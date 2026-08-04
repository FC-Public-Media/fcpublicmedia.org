// Binding a device to a member site.
//
// The passkey ceremony runs against a CDP virtual authenticator, so these are
// real WebAuthn calls producing a real credential — not a stub. That matters
// because the part most likely to be wrong is getting the public key back out
// in a form something else can verify, and a mock would happily return
// whatever shape the test expected.

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const SCRIPT = path.join(REPO, 'script', 'mint-claim.py');

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

/**
 * Attach a virtual authenticator so credentials.create() resolves.
 *
 * Chromium only, which is what this suite runs.
 */
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
    // It is a capability — anyone who opens it can bind a device — so it must
    // not survive in a URL someone might paste into a group chat.
    await withKey(page);
    const token = linkFor('member@example.com', 'fcpublicmedia/janes-show');

    await page.goto(`/authorize/#claim=${token}`);
    await expect(page.locator('[data-state="ready"]')).toBeVisible();

    expect(page.url()).not.toContain('claim=');
  });

  test('a check-in claim is refused rather than half-honoured', async ({ page }) => {
    // A claim with no repository proves an email but names no site. Running
    // the ceremony anyway would leave someone holding a passkey that
    // authorizes nothing.
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
    // The whole reason the repo travels inside the signature: the link is
    // meant to be forwarded, and a forwarded link must not be editable into
    // one that binds a device to somebody else's site.
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
    // The assertion that matters: the public key comes back as SPKI that
    // WebCrypto will import. If this passes, whatever verifies a signature
    // later can read the same bytes.
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
    // It goes into a repository that may be public, and a second person on
    // the same site should not have their address published by being added
    // to it. The claim already proved the address; the passkey carries it
    // forward without restating it.
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();
    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const record = await page.locator('#device-record').innerText();
    expect(record).not.toContain('member@example.com');
  });

  test('an unnamed device still gets a label', async ({ page }) => {
    // Blank names in a list everyone else can see are how you end up unable
    // to tell which device to revoke.
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();
    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const record = JSON.parse(await page.locator('#device-record').innerText());
    expect(record.label.trim().length).toBeGreaterThan(0);
  });

  test('two devices on one site produce two distinct records', async ({ page }) => {
    // The multi-device and two-people cases are the same code path, and both
    // have to yield separate credentials rather than replacing each other.
    await withKey(page);
    await virtualAuthenticator(page);

    const ids = [];
    for (const [email, label] of [
      ['member@example.com', 'phone'],
      ['second@example.com', 'laptop'],
    ]) {
      // A full load between the two. Going straight from one claim URL to the
      // next would change only the fragment, which the page now handles via
      // hashchange — but that is a different code path and is not what is
      // under test here.
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
    // The one ceremony failure that can be triggered honestly here. A
    // user-dismissed system sheet cannot: headless Chromium with no
    // authenticator hangs rather than rejecting, so a test for it would be
    // testing the harness. The dead-end property that case shares is covered
    // structurally below.
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
    // Whichever way the ceremony fails, the person holding the phone needs
    // something to do next. Asserted over the markup rather than by driving
    // each failure, because some of them cannot be driven from here.
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
    // Only the fragment changes, which is not a navigation. Without a
    // hashchange listener the page sits there naming the wrong site, which is
    // the worst possible way to be wrong on this particular page.
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
    // The shipped state. The passkey is real; only the delivery is manual,
    // and for the first few member sites that is a genuine workflow.
    await withKey(page);
    await virtualAuthenticator(page);

    await page.goto(`/authorize/#claim=${linkFor('member@example.com', 'fcpublicmedia/janes-show')}`);
    await page.locator('#create-passkey').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    await expect(page.locator('[data-state="done"]')).toBeHidden();
    await expect(page.locator('#email-record')).toHaveAttribute('href', /^mailto:/);
  });
});
