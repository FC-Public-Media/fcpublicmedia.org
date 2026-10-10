// see docs/inline/site/tests/authorize.spec.js.md#1

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

// `site/tests/` is inside the Jekyll source, so one level up is the site.
const SITE_DIR = path.resolve(__dirname, '..');
const SCRIPT = path.join(SITE_DIR, 'bin', 'mint-claim.py');

let workdir;
let keyPath;
let publicKey;

function mint(args) {
  return execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();
}

function parseKeyBlock(output) {
  const grab = (field) => output.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
  return { id: grab('id'), x: grab('x'), y: grab('y') };
}

const tokenFrom = (url) => url.split('#claim=')[1];

test.beforeAll(() => {
  workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-authorize-'));
  keyPath = path.join(workdir, 'key.pem');
  publicKey = parseKeyBlock(mint(['--new-key', keyPath]));
});

test.afterAll(() => fs.rmSync(workdir, { recursive: true, force: true }));

/** Serve /authorize/ with a signing key configured, as a live site would. */
async function withKey(page) {
  await page.route('**/authorize/', async (route) => {
    const response = await route.fetch();
    const body = (await response.text()).replace(
      '"keys": []',
      `"keys": [${JSON.stringify(publicKey)}]`
    );
    await route.fulfill({ response, body });
  });
}

// see docs/inline/site/tests/authorize.spec.js.md#2
async function virtualAuthenticator(page) {
  const session = await page.context().newCDPSession(page);
  await session.send('WebAuthn.enable');
  const { authenticatorId } = await session.send('WebAuthn.addVirtualAuthenticator', {
    options: {
      protocol: 'ctap2',
      transport: 'internal',
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true,
    },
  });
  return { session, authenticatorId };
}

const linkFor = (email, repo, days = '2') =>
  tokenFrom(mint(['--key', keyPath, '--email', email, '--repo', repo, '--days', days]));

test.describe('arriving at /authorize/', () => {
  test('with no link at all, explains itself', async ({ page }) => {
    // The most likely wrong turn: someone finds the page in a search result.
    await page.goto('/authorize/');

    await expect(page.locator('[data-state="no-link"]')).toBeVisible();
    await expect(page.locator('main')).toContainText('link we emailed you');
  });

  test('a valid link names the site and the address', async ({ page }) => {
    await withKey(page);
    const token = linkFor('member@example.com', 'fcpublicmedia/janes-show');

    await page.goto(`/authorize/#claim=${token}`);

    await expect(page.locator('[data-state="ready"]')).toBeVisible();
    await expect(page.locator('#ready-site')).toHaveText('janes-show');
    await expect(page.locator('#ready-email')).toHaveText('member@example.com');
  });

  test('the token is taken out of the address bar', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#3
    await withKey(page);
    const token = linkFor('member@example.com', 'fcpublicmedia/janes-show');

    await page.goto(`/authorize/#claim=${token}`);
    await expect(page.locator('[data-state="ready"]')).toBeVisible();

    expect(page.url()).not.toContain('claim=');
  });

  test('a check-in claim is refused rather than half-honoured', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#4
    await withKey(page);
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'member@example.com']));

    await page.goto(`/authorize/#claim=${token}`);

    await expect(page.locator('[data-state="bad-link"]')).toBeVisible();
    await expect(page.locator('#bad-link-detail')).toContainText("doesn't name a site");
  });

  test('a link signed by another key is refused', async ({ page }) => {
    await withKey(page);
    const otherPath = path.join(workdir, 'other.pem');
    if (!fs.existsSync(otherPath)) mint(['--new-key', otherPath]);
    const token = tokenFrom(
      mint(['--key', otherPath, '--email', 'attacker@example.com', '--repo', 'a/b'])
    );

    await page.goto(`/authorize/#claim=${token}`);

    await expect(page.locator('[data-state="bad-link"]')).toBeVisible();
  });

  test('the repository cannot be re-aimed by editing the link', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#5
    await withKey(page);
    const token = linkFor('member@example.com', 'fcpublicmedia/janes-show');
    const [version, body, signature] = token.split('.');

    const payload = JSON.parse(Buffer.from(body, 'base64url').toString());
    const forged = Buffer.from(
      JSON.stringify({ ...payload, repo: 'fcpublicmedia/someone-else' })
    ).toString('base64url');

    await page.goto(`/authorize/#claim=${version}.${forged}.${signature}`);

    await expect(page.locator('[data-state="bad-link"]')).toBeVisible();
    await expect(page.locator('main')).not.toContainText('someone-else');
  });

  test('an expired link says so plainly', async ({ page }) => {
    await withKey(page);
    const token = linkFor('member@example.com', 'fcpublicmedia/janes-show', '-1');

    await page.goto(`/authorize/#claim=${token}`);

    await expect(page.locator('#bad-link-detail')).toContainText('expired');
  });
});

test.describe('making the passkey', () => {
  test('produces a device record with a usable public key', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#6
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#device-name').fill("Jane's phone");
    await page.locator('#create-passkey').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const record = JSON.parse(await page.locator('#device-record').innerText());
    expect(record.credential_id).toBeTruthy();
    expect(record.label).toBe("Jane's phone");
    expect(record.added).toMatch(/^\d{4}-\d{2}-\d{2}T/);

    const importable = await page.evaluate(async (b64) => {
      const bytes = Uint8Array.from(
        atob(b64.replace(/-/g, '+').replace(/_/g, '/')),
        (c) => c.charCodeAt(0)
      );
      try {
        await crypto.subtle.importKey(
          'spki',
          bytes,
          { name: 'ECDSA', namedCurve: 'P-256' },
          true,
          ['verify']
        );
        return true;
      } catch (error) {
        return String(error);
      }
    }, record.public_key);

    expect(importable, 'the stored public key is not importable').toBe(true);
  });

  test('the record carries no email address', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#7
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();
    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const record = await page.locator('#device-record').innerText();
    expect(record).not.toContain('member@example.com');
  });

  test('an unnamed device still gets a label', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#8
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();
    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const record = JSON.parse(await page.locator('#device-record').innerText());
    expect(record.label.trim().length).toBeGreaterThan(0);
  });

  test('two devices on one site produce two distinct records', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#9
    await withKey(page);
    await virtualAuthenticator(page);

    const ids = [];
    for (const [email, label] of [
      ['member@example.com', 'phone'],
      ['second@example.com', 'laptop'],
    ]) {
      // see docs/inline/site/tests/authorize.spec.js.md#10
      await page.goto('/authorize/');
      await page.goto(`/authorize/#claim=${linkFor(email, 'fcpublicmedia/janes-show')}`);
      await expect(page.locator('[data-state="ready"]')).toBeVisible();
      await page.locator('#device-name').fill(label);
      await page.locator('#create-passkey').click();
      await expect(page.locator('[data-state="manual"]')).toBeVisible();
      ids.push(JSON.parse(await page.locator('#device-record').innerText()).credential_id);
    }

    expect(ids[0]).not.toBe(ids[1]);
  });

  test('a browser without passkeys is told so, not left waiting', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#11
    await withKey(page);
    await page.addInitScript(() => {
      delete window.PublicKeyCredential;
    });

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();

    await expect(page.locator('[data-state="unsupported"]')).toBeVisible();
    await expect(page.locator('[data-state="manual"]')).toBeHidden();
    await expect(page.locator('[data-state="done"]')).toBeHidden();
  });

  test('no failure state is a dead end', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#12
    await page.goto('/authorize/');

    for (const state of ['cancelled', 'error', 'unsupported', 'bad-link', 'no-link']) {
      const panel = page.locator(`[data-state="${state}"]`);
      await expect(panel, `no ${state} panel`).toHaveCount(1);

      const ways = await panel.evaluate(
        (node) =>
          node.querySelectorAll('[data-action="retry"], a[href], button').length
      );
      expect(ways, `${state} offers nothing to do next`).toBeGreaterThan(0);
    }
  });
});

test.describe('a second link in the same tab', () => {
  test('re-reads it instead of showing the first one still', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#13
    await withKey(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await expect(page.locator('#ready-site')).toHaveText('janes-show');

    await page.evaluate((token) => {
      window.location.hash = `claim=${token}`;
    }, linkFor('member@example.com', 'fcpublicmedia/other-show'));

    await expect(page.locator('#ready-site')).toHaveText('other-show');
  });
});

test.describe('without a broker configured', () => {
  test('shows the record to hand over rather than pretending it was sent', async ({ page }) => {
    // see docs/inline/site/tests/authorize.spec.js.md#14
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    await expect(page.locator('[data-state="done"]')).toBeHidden();
    await expect(page.locator('#email-record')).toHaveAttribute('href', /^mailto:/);
  });
});
