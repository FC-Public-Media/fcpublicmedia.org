// see docs/inline/site/tests/upload.spec.js.md#1

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

// `site/tests/` is inside the Jekyll source, so one level up is the site.
const SITE_DIR = path.resolve(__dirname, '..');
const SCRIPT = path.join(SITE_DIR, 'bin', 'mint-claim.py');
const SITE = 'fcpublicmedia/janes-show';

// see docs/inline/site/tests/upload.spec.js.md#2
const PARSE_ENTRY = `
import sys, json, yaml
try:
    doc = yaml.safe_load("programs:\\n" + sys.stdin.read())
    print(json.dumps(doc["programs"][0]))
except Exception as error:
    print(json.dumps({"error": f"{type(error).__name__}: {error}"}))
`;

let workdir;
let keyPath;
let publicKey;

const mint = (args) => execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();

function parseKeyBlock(output) {
  const grab = (field) => output.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
  return { id: grab('id'), x: grab('x'), y: grab('y') };
}

const claimFor = (email, repo) =>
  mint(['--key', keyPath, '--email', email, '--repo', repo, '--days', '2'])
    .split('#claim=')[1];

test.beforeAll(() => {
  workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-upload-'));
  keyPath = path.join(workdir, 'key.pem');
  publicKey = parseKeyBlock(mint(['--new-key', keyPath]));
});

test.afterAll(() => fs.rmSync(workdir, { recursive: true, force: true }));

/** Serve /authorize/ with a signing key configured. */
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

async function virtualAuthenticator(page) {
  const session = await page.context().newCDPSession(page);
  await session.send('WebAuthn.enable');
  await session.send('WebAuthn.addVirtualAuthenticator', {
    options: {
      protocol: 'ctap2',
      transport: 'internal',
      hasResidentKey: true,
      hasUserVerification: true,
      isUserVerified: true,
      automaticPresenceSimulation: true,
    },
  });
  return session;
}

/** Register a passkey for a site, so /upload/ has something to sign in with. */
async function register(page, email, repo) {
  await page.goto(`/authorize/#claim=${claimFor(email, repo)}`);
  await expect(page.locator('[data-state="ready"]')).toBeVisible();
  await page.locator('#create-passkey').click();
  await expect(page.locator('[data-state="manual"]')).toBeVisible();
}

test.describe('arriving at /upload/', () => {
  test('asks you to sign in rather than showing a form', async ({ page }) => {
    await page.goto('/upload/');

    await expect(page.locator('[data-state="signed-out"]')).toBeVisible();
    await expect(page.locator('[data-state="ready"]')).toBeHidden();
  });

  test('a browser without passkeys is told so, not left waiting', async ({ page }) => {
    await page.addInitScript(() => {
      delete window.PublicKeyCredential;
    });
    await page.goto('/upload/');
    await page.locator('#sign-in').click();

    await expect(page.locator('[data-state="unsupported"]')).toBeVisible();
  });

  test('no failure state is a dead end', async ({ page }) => {
    await page.goto('/upload/');

    for (const state of ['unsupported', 'sign-in-failed']) {
      const panel = page.locator(`[data-state="${state}"]`);
      await expect(panel, `no ${state} panel`).toHaveCount(1);
      const ways = await panel.evaluate(
        (node) => node.querySelectorAll('[data-action="retry"], a[href], button').length
      );
      expect(ways, `${state} offers nothing to do next`).toBeGreaterThan(0);
    }
  });
});

test.describe('signing in with a registered passkey', () => {
  test('finds out which site the passkey belongs to', async ({ page }) => {
    // see docs/inline/site/tests/upload.spec.js.md#3
    await withKey(page);
    await virtualAuthenticator(page);
    await register(page, 'jane@example.com', SITE);

    await page.goto('/upload/');
    await page.locator('#sign-in').click();

    await expect(page.locator('[data-state="ready"]')).toBeVisible();
    await expect(page.locator('#ready-site')).toHaveText('janes-show');
  });

  test('two people on one site get separate credentials', async ({ page }) => {
    // see docs/inline/site/tests/upload.spec.js.md#4
    await withKey(page);
    await virtualAuthenticator(page);

    await register(page, 'jane@example.com', SITE);
    const first = JSON.parse(await page.locator('#device-record').innerText());

    await page.goto('/authorize/');
    await register(page, 'sam@example.com', SITE);
    const second = JSON.parse(await page.locator('#device-record').innerText());

    expect(second.credential_id).not.toBe(first.credential_id);
  });

  // see docs/inline/site/tests/upload.spec.js.md#5
});

test.describe('describing an episode', () => {
  async function signedIn(page) {
    await withKey(page);
    await virtualAuthenticator(page);
    await register(page, 'jane@example.com', SITE);
    await page.goto('/upload/');
    await page.locator('#sign-in').click();
    await expect(page.locator('[data-state="ready"]')).toBeVisible();
  }

  test('writes the drop time with Colorado\'s offset, not the browser\'s', async ({ page }) => {
    // see docs/inline/site/tests/upload.spec.js.md#6
    await signedIn(page);

    await page.locator('#ep-date').fill('2026-08-14');
    await page.locator('#ep-time').fill('18:00');

    // Mountain Daylight Time in August.
    await expect(page.locator('#ep-iso')).toHaveText('2026-08-14T18:00:00-06:00');
  });

  test('uses the winter offset for a winter date', async ({ page }) => {
    // see docs/inline/site/tests/upload.spec.js.md#7
    await signedIn(page);

    await page.locator('#ep-date').fill('2026-12-14');
    await page.locator('#ep-time').fill('18:00');

    await expect(page.locator('#ep-iso')).toHaveText('2026-12-14T18:00:00-07:00');
  });

  test('refuses a submission with no title', async ({ page }) => {
    await signedIn(page);

    await page.locator('#ep-submit').click();

    await expect(page.locator('#ep-error')).toContainText('title');
    await expect(page.locator('[data-state="manual"]')).toBeHidden();
  });

  test('produces an entry the site template would accept', async ({ page }) => {
    await signedIn(page);

    await page.locator('#ep-title').fill('Episode Nine');
    await page.locator('#ep-summary').fill('What it is about.');
    await page.locator('#ep-date').fill('2026-08-14');
    await page.locator('#ep-time').fill('18:00');
    await page.locator('#ep-runtime').fill('24:10');
    await page.locator('#ep-path').fill('/Programs/2026/ep9.mov');
    await page.locator('#ep-submit').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();

    const yaml = await page.locator('#entry-yaml').innerText();

    // see docs/inline/site/tests/upload.spec.js.md#8
    const parsed = JSON.parse(
      execFileSync('python3', ['-c', PARSE_ENTRY], { input: yaml, encoding: 'utf8' })
    );

    expect(parsed.error, parsed.error).toBeUndefined();
    expect(parsed.title).toBe('Episode Nine');
    expect(parsed.status).toBe('scheduled');
    expect(parsed.drop).toBe('2026-08-14T18:00:00-06:00');
    expect(parsed.runtime).toBe('24:10');
    expect(parsed.summary.trim()).toBe('What it is about.');
    expect(parsed.artifact.url).toBe('/Programs/2026/ep9.mov');
  });

  test('says plainly that the file is not uploaded from here', async ({ page }) => {
    // see docs/inline/site/tests/upload.spec.js.md#9
    await signedIn(page);

    await expect(page.locator('[data-no-destination]')).toBeVisible();
    await expect(page.locator('[data-no-destination]')).toContainText("can't take the file");
  });
});
