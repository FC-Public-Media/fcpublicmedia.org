// see docs/inline/site/tests/devices.spec.js.md#1

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

// `site/tests/` is inside the Jekyll source, so one level up is the site.
const SITE_DIR = path.resolve(__dirname, '..');
const SCRIPT = path.join(SITE_DIR, 'bin', 'mint-claim.py');
const SITE = 'fcpublicmedia/janes-show';
const BROKER = 'https://broker.test';

let workdir;
let keyPath;
let publicKey;

const mint = (args) => execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();

test.beforeAll(() => {
  workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-devices-'));
  keyPath = path.join(workdir, 'key.pem');
  const out = mint(['--new-key', keyPath]);
  const grab = (field) => out.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
  publicKey = { id: grab('id'), x: grab('x'), y: grab('y') };
});

test.afterAll(() => fs.rmSync(workdir, { recursive: true, force: true }));

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
}

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// see docs/inline/site/tests/devices.spec.js.md#2
async function signedIn(page, { devices, broker = null, decision } = {}) {
  const seen = { challenges: [], calls: [] };

  await page.route('**/authorize/', async (route) => {
    const response = await route.fetch();
    const body = (await response.text()).replace('"keys": []', `"keys": [${JSON.stringify(publicKey)}]`);
    await route.fulfill({ response, body });
  });

  await page.route('**/devices/', async (route) => {
    const response = await route.fetch();
    let body = await response.text();
    if (broker) body = body.replace('"brokerUrl": ""', `"brokerUrl": "${broker}"`);
    await route.fulfill({ response, body });
  });

  await page.route('https://raw.githubusercontent.com/**', async (route) => {
    if (devices === null) {
      await route.fulfill({ status: 404, body: 'Not Found' });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ version: 1, devices }),
    });
  });

  if (broker) {
    await page.route(`${broker}/**`, async (route) => {
      const request = route.request();
      if (request.method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers: CORS });
        return;
      }
      const body = request.postDataJSON();
      const json = (status, payload) =>
        route.fulfill({
          status,
          headers: { ...CORS, 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

      if (request.url().endsWith('/challenge')) {
        const challenge = crypto.randomBytes(32).toString('base64url');
        seen.challenges.push({ intent: body, challenge });
        await json(200, { ok: true, challenge, expires_in: 300, intent: body });
        return;
      }

      seen.calls.push(body);
      const answer = decision || { status: 200, payload: { ok: true, performed: true } };
      await json(answer.status, answer.payload);
    });
  }

  await virtualAuthenticator(page);

  const token = mint(['--key', keyPath, '--email', 'jane@example.com', '--repo', SITE, '--days', '2'])
    .split('#claim=')[1];
  await page.goto(`/authorize/#claim=${token}`);
  await expect(page.locator('[data-state="ready"]')).toBeVisible();
  await page.locator('#create-passkey').click();
  await expect(page.locator('[data-state="manual"]')).toBeVisible();

  await page.goto('/devices/');
  await page.locator('#sign-in').click();

  return seen;
}

const owner = (extra = {}) => ({
  credential_id: 'owner-credential-aaaaaaaa',
  public_key: 'k',
  label: "Jane's phone",
  added: '2026-01-14T18:22:04.117Z',
  may_publish: true,
  ...extra,
});

const waiting = (extra = {}) => ({
  credential_id: 'waiting-credential-bbbbbbbb',
  public_key: 'k',
  label: "Raj's phone",
  added: '2026-08-01T10:00:00.000Z',
  may_publish: false,
  ...extra,
});

test.describe('arriving', () => {
  test('asks you to sign in rather than showing a list', async ({ page }) => {
    await page.goto('/devices/');

    await expect(page.locator('[data-state="signed-out"]')).toBeVisible();
    await expect(page.locator('[data-state="listing"]')).toBeHidden();
  });

  test('no failure state is a dead end', async ({ page }) => {
    await page.goto('/devices/');

    for (const state of ['unsupported', 'sign-in-failed', 'load-failed']) {
      const panel = page.locator(`[data-state="${state}"]`);
      await expect(panel, `no ${state} panel`).toHaveCount(1);
      const ways = await panel.evaluate(
        (node) => node.querySelectorAll('[data-action], a[href], button').length
      );
      expect(ways, `${state} offers nothing to do next`).toBeGreaterThan(0);
    }
  });
});

test.describe('the two lists', () => {
  test('a device waiting for approval is separated out, not buried', async ({ page }) => {
    // A single list sorted by status hides the only row anybody came to act on.
    await signedIn(page, { devices: [owner(), waiting()] });

    await expect(page.locator('[data-state="listing"]')).toBeVisible();
    await expect(page.locator('#waiting-section')).toBeVisible();
    await expect(page.locator('#waiting-list li')).toHaveCount(1);
    await expect(page.locator('#waiting-list')).toContainText("Raj's phone");
    await expect(page.locator('#allowed-list')).toContainText("Jane's phone");
  });

  test('nothing waiting means no section asking to be looked at', async ({ page }) => {
    await signedIn(page, { devices: [owner()] });

    await expect(page.locator('#waiting-section')).toBeHidden();
    await expect(page.locator('#allowed-list li')).toHaveCount(1);
  });

  test('a revoked device is gone from both lists', async ({ page }) => {
    await signedIn(page, { devices: [owner(), waiting({ revoked: true })] });

    await expect(page.locator('#waiting-section')).toBeHidden();
    await expect(page.locator('#allowed-list li')).toHaveCount(1);
  });
});

test.describe('what cannot be done', () => {
  test('the only device that can publish has no Remove button at all', async ({ page }) => {
    // see docs/inline/site/tests/devices.spec.js.md#3
    await signedIn(page, { devices: [owner()] });

    await expect(page.locator('#allowed-list button')).toHaveCount(0);
    await expect(page.locator('#allowed-note')).toContainText('cannot be removed');
  });

  test('once a second device is approved, removing becomes possible', async ({ page }) => {
    await signedIn(page, { devices: [owner(), waiting({ may_publish: true })] });

    await expect(page.locator('#allowed-list li')).toHaveCount(2);
    await expect(page.locator('#allowed-list button')).toHaveCount(2);
  });

  test('a device that may not publish is told that, not that it failed', async ({ page }) => {
    // see docs/inline/site/tests/devices.spec.js.md#4
    await signedIn(page, {
      devices: [owner(), waiting()],
      broker: BROKER,
      decision: {
        status: 403,
        payload: { ok: false, reason: 'not-allowed', detail: 'Registered but not allowed.' },
      },
    });

    await page.locator('#waiting-list button', { hasText: 'Approve' }).click();

    await expect(page.locator('#devices-status')).toContainText('not allowed to change the site yet');
  });
});

test.describe('approving', () => {
  test('asks the broker for a challenge bound to that one device', async ({ page }) => {
    // see docs/inline/site/tests/devices.spec.js.md#5
    const seen = await signedIn(page, {
      devices: [owner(), waiting()],
      broker: BROKER,
    });

    await page.locator('#waiting-list button', { hasText: 'Approve' }).click();
    await expect(page.locator('#devices-status')).toContainText('Done');

    expect(seen.challenges).toHaveLength(1);
    expect(seen.challenges[0].intent).toMatchObject({
      action: 'device.allow',
      repo: SITE,
      credential_id: 'waiting-credential-bbbbbbbb',
    });
  });

  test('removing asks for a revoke, not an approve', async ({ page }) => {
    const seen = await signedIn(page, {
      devices: [owner(), waiting({ may_publish: true })],
      broker: BROKER,
    });

    await page.locator('#allowed-list li', { hasText: "Raj's phone" }).getByText('Remove').click();

    expect(seen.challenges[0].intent.action).toBe('device.revoke');
    expect(seen.challenges[0].intent.credential_id).toBe('waiting-credential-bbbbbbbb');
  });

  test('the signature answers the challenge the broker issued', async ({ page }) => {
    const seen = await signedIn(page, {
      devices: [owner(), waiting()],
      broker: BROKER,
    });

    await page.locator('#waiting-list button', { hasText: 'Approve' }).click();
    await expect(page.locator('#devices-status')).toContainText('Done');

    const clientData = JSON.parse(
      Buffer.from(seen.calls[0].assertion.client_data_json, 'base64url').toString('utf8')
    );
    expect(clientData.challenge).toBe(seen.challenges[0].challenge);
    expect(clientData.type).toBe('webauthn.get');
  });

  test('with no broker it asks us instead of pretending', async ({ page }) => {
    await signedIn(page, { devices: [owner(), waiting()] });

    await page.locator('#waiting-list button', { hasText: 'Approve' }).click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    await expect(page.locator('#manual-detail')).toContainText('approve');
    await expect(page.locator('#email-change')).toHaveAttribute('href', /^mailto:/);
  });
});
