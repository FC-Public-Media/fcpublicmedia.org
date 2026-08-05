// Editing a member site's settings.
//
// The claim this page makes is that editing raw text preserves the comments
// that document the settings, where a form would strip them. That claim is
// worth testing, because it is the entire reason the page is a textarea and
// the pull to "just make it a form" will be constant.
//
// GitHub is stubbed rather than called. The tests are about what the page
// does with a response, and hitting a rate-limited public API from CI to
// learn that would be both slow and flaky.

const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const SCRIPT = path.join(REPO, 'script', 'mint-claim.py');
const SITE = 'fcpublicmedia/janes-show';

// A settings file shaped like the real one: mostly commentary, with the
// values scattered through it. If an editor cannot round-trip this, it cannot
// round-trip the thing members actually have.
const SETTINGS = `# Everything a member can change about their site.
#
# WHY ONE FILE
# ------------
# This is the file an editing UI writes to.

name: Your Show
tagline: One line about what you make.

# Shown so people can tell a Fort Collins producer from a stranger.
producer: Your Name
location: Fort Collins, CO

# Leave anything blank and it is skipped rather than rendered empty.
email: ""
`;

let workdir;
let keyPath;
let publicKey;

const mint = (args) => execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();

function parseKeyBlock(output) {
  const grab = (field) => output.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
  return { id: grab('id'), x: grab('x'), y: grab('y') };
}

test.beforeAll(() => {
  workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-settings-'));
  keyPath = path.join(workdir, 'key.pem');
  publicKey = parseKeyBlock(mint(['--new-key', keyPath]));
});

test.afterAll(() => fs.rmSync(workdir, { recursive: true, force: true }));

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
}

/** Stand in for the member's repository. */
async function stubGitHub(page, { status = 200, body = SETTINGS } = {}) {
  await page.route('https://api.github.com/repos/**/contents/**', async (route) => {
    if (status !== 200) {
      await route.fulfill({ status, contentType: 'application/json', body: '{}' });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        path: '_data/site.yml',
        sha: 'abc123def456',
        encoding: 'base64',
        content: Buffer.from(body, 'utf8').toString('base64'),
      }),
    });
  });
}

const BROKER = 'https://broker.test';

const b64u = (buffer) => buffer.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const hashOf = (text) => b64u(crypto.createHash('sha256').update(text, 'utf8').digest());

/**
 * Point the page at a broker, and stand in for it.
 *
 * The signature cannot be checked here — there is no private key on this side
 * of the virtual authenticator — but the thing worth checking can be: that the
 * page signed the challenge THIS stub issued rather than one of its own. That
 * is the entire difference between the broker mattering and not.
 *
 * Returns the record of what the page asked for and what it sent back.
 */
async function withBroker(page, { write } = {}) {
  const seen = { challenges: [], writes: [] };

  await page.route('**/settings/', async (route) => {
    const response = await route.fetch();
    const body = (await response.text()).replace('"brokerUrl": ""', `"brokerUrl": "${BROKER}"`);
    await route.fulfill({ response, body });
  });

  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  await page.route(`${BROKER}/**`, async (route) => {
    const request = route.request();
    if (request.method() === 'OPTIONS') {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }

    const body = request.postDataJSON();
    const json = (status, payload) =>
      route.fulfill({
        status,
        headers: { ...cors, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

    if (request.url().endsWith('/challenge')) {
      const challenge = b64u(crypto.randomBytes(32));
      seen.challenges.push({ intent: body, challenge });
      await json(200, { ok: true, challenge, expires_in: 300, intent: body });
      return;
    }

    // Read the challenge back out of the signed client data, which is the
    // only copy the page could not have swapped.
    const clientData = JSON.parse(
      Buffer.from(body.assertion.client_data_json, 'base64url').toString('utf8')
    );
    seen.writes.push({ body, clientData });

    const answer = write || { status: 200, payload: { ok: true, performed: true, mode: 'branch', url: 'https://github.com/x/y/pull/3', repeated: false } };
    await json(answer.status, answer.payload);
  });

  return seen;
}

/**
 * Sign in and, unless a load failure is being tested, wait for the editor to
 * actually hold the file.
 *
 * Without that wait this races: inputValue() on a not-yet-populated textarea
 * returns an empty string rather than waiting, so a test that reads the file
 * and edits it would fill in nothing and then be told nothing had changed.
 * It passed in isolation and failed under parallel load, which is the worst
 * way for a test to be wrong.
 */
async function signedIn(page, options) {
  await withKey(page);
  await virtualAuthenticator(page);
  await stubGitHub(page, options);

  const token = mint(['--key', keyPath, '--email', 'jane@example.com', '--repo', SITE, '--days', '2'])
    .split('#claim=')[1];
  await page.goto(`/authorize/#claim=${token}`);
  await expect(page.locator('[data-state="ready"]')).toBeVisible();
  await page.locator('#create-passkey').click();
  await expect(page.locator('[data-state="manual"]')).toBeVisible();

  await page.goto('/settings/');
  await page.locator('#sign-in').click();

  if (!options || !options.status || options.status === 200) {
    await expect(page.locator('[data-state="editing"]')).toBeVisible();
    await expect(page.locator('#settings-text')).not.toHaveValue('');
  }
}

test.describe('arriving at /settings/', () => {
  test('asks you to sign in rather than showing an editor', async ({ page }) => {
    await page.goto('/settings/');

    await expect(page.locator('[data-state="signed-out"]')).toBeVisible();
    await expect(page.locator('[data-state="editing"]')).toBeHidden();
  });

  test('no failure state is a dead end', async ({ page }) => {
    await page.goto('/settings/');

    for (const state of ['unsupported', 'sign-in-failed', 'load-failed']) {
      const panel = page.locator(`[data-state="${state}"]`);
      await expect(panel, `no ${state} panel`).toHaveCount(1);
      const ways = await panel.evaluate(
        (node) => node.querySelectorAll('[data-action], a[href], button').length
      );
      expect(ways, `${state} offers nothing to do next`).toBeGreaterThan(0);
    }
  });

  test('a rate-limited GitHub says what to do about it', async ({ page }) => {
    // Unauthenticated requests are capped per address and a shared network
    // can exhaust it. "Try again later" is the actual fix here, so saying it
    // plainly is not a brush-off.
    await signedIn(page, { status: 403 });

    await expect(page.locator('[data-state="load-failed"]')).toBeVisible();
    await expect(page.locator('#load-detail')).toContainText('rate-limiting');
  });

  test('a missing settings file explains itself', async ({ page }) => {
    await signedIn(page, { status: 404 });

    await expect(page.locator('#load-detail')).toContainText("isn't in your site yet");
  });
});

test.describe('editing', () => {
  test('loads the file whole, comments and all', async ({ page }) => {
    // The whole argument for a textarea over a form. Those comments are the
    // only documentation a member has for what these settings do.
    await signedIn(page);

    await expect(page.locator('[data-state="editing"]')).toBeVisible();
    const text = await page.locator('#settings-text').inputValue();

    expect(text).toBe(SETTINGS);
    expect(text).toContain('# WHY ONE FILE');
    expect(text).toContain('# Leave anything blank');
  });

  test('an edit keeps every comment that was there', async ({ page }) => {
    // A form would round-trip through a parser and strip all of these on the
    // first save. This is the regression that would be invisible until a
    // member needed the documentation and it had gone.
    await signedIn(page);

    const text = await page.locator('#settings-text').inputValue();
    await page.locator('#settings-text').fill(text.replace('Your Show', 'Jane Live'));
    await page.locator('#settings-save').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    const saved = await page.locator('#settings-output').innerText();

    for (const comment of SETTINGS.split('\n').filter((line) => line.startsWith('#'))) {
      expect(saved, `lost: ${comment}`).toContain(comment);
    }
    expect(saved).toContain('name: Jane Live');
  });

  test('refuses to save a tab', async ({ page }) => {
    // Invalid YAML, and an editor that inserted one leaves no visible trace.
    await signedIn(page);

    await page.locator('#settings-text').fill('name: A Show\n\tbroken: true\n');

    await expect(page.locator('#settings-checks')).toContainText('tab');
    await page.locator('#settings-save').click();
    await expect(page.locator('[data-state="manual"]')).toBeHidden();
  });

  test('warns when a setting has disappeared but does not block it', async ({ page }) => {
    // Deleting one on purpose is legitimate; deleting one by pasting over the
    // top is not, and only the member can tell which happened.
    await signedIn(page);

    await page.locator('#settings-text').fill('name: A Show\n');

    await expect(page.locator('#settings-checks')).toContainText('No longer in the file');
    await page.locator('#settings-save').click();
    await expect(page.locator('[data-state="manual"]')).toBeVisible();
  });

  test('saying nothing changed is not the same as saving', async ({ page }) => {
    await signedIn(page);

    await page.locator('#settings-save').click();

    await expect(page.locator('#settings-status')).toContainText('Nothing has changed');
    await expect(page.locator('[data-state="manual"]')).toBeHidden();
  });

  test('undo puts the original back', async ({ page }) => {
    await signedIn(page);

    await page.locator('#settings-text').fill('name: Wrecked\n');
    await page.locator('#settings-revert').click();

    expect(await page.locator('#settings-text').inputValue()).toBe(SETTINGS);
  });

  test('with no broker it hands the file over rather than pretending', async ({ page }) => {
    await signedIn(page);

    await page.locator('#settings-text').fill(SETTINGS.replace('Your Name', 'Jane Doe'));
    await page.locator('#settings-save').click();

    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    await expect(page.locator('[data-state="saved"]')).toBeHidden();
    await expect(page.locator('#email-settings')).toHaveAttribute('href', /^mailto:/);
  });
});

test.describe('saving through the broker', () => {
  const edited = SETTINGS.replace('Your Show', 'Jane Live');

  test('it signs the challenge the broker issued, not one of its own', async ({ page }) => {
    // The whole point of the broker. A page that generates its own challenge
    // proves nothing to anybody, and the difference is invisible from the
    // outside — both flows show the same prompt and both succeed.
    const seen = await withBroker(page);
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();
    await expect(page.locator('[data-state="saved"]')).toBeVisible();

    expect(seen.challenges).toHaveLength(1);
    expect(seen.writes).toHaveLength(1);
    expect(seen.writes[0].clientData.challenge).toBe(seen.challenges[0].challenge);
    expect(seen.writes[0].clientData.type).toBe('webauthn.get');
  });

  test('what it declares up front is what it sends back', async ({ page }) => {
    // The binding only works if the hash declared before the prompt describes
    // the bytes sent after it. Nothing else in the system notices if these
    // two drift apart — the broker would simply start refusing every save.
    const seen = await withBroker(page);
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();
    await expect(page.locator('[data-state="saved"]')).toBeVisible();

    const { intent } = seen.challenges[0];
    expect(intent.action).toBe('settings.write');
    expect(intent.repo).toBe(SITE);
    expect(intent.sha).toBe('abc123def456');
    expect(intent.content_hash).toBe(hashOf(edited));
    expect(seen.writes[0].body.content).toBe(edited);
  });

  test('a save that goes through offers a look at it', async ({ page }) => {
    await withBroker(page);
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();

    await expect(page.locator('[data-state="saved"]')).toBeVisible();
    await expect(page.locator('#saved-link')).toHaveAttribute('href', /\/pull\/3$/);
    await expect(page.locator('#saved-detail')).toContainText('being checked');
  });

  test('an already-saved edit says so rather than claiming a second save', async ({ page }) => {
    await withBroker(page, {
      write: { status: 200, payload: { ok: true, performed: true, mode: 'branch', url: '', repeated: true } },
    });
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();

    await expect(page.locator('#saved-detail')).toContainText('already saved');
    await expect(page.locator('#saved-link')).toBeHidden();
  });

  test('a conflict keeps their text and says where the other version is', async ({ page }) => {
    await withBroker(page, {
      write: { status: 409, payload: { ok: false, reason: 'conflict', detail: 'The file changed.' } },
    });
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();

    await expect(page.locator('#settings-status')).toContainText('Somebody else changed');
    await expect(page.locator('[data-state="saved"]')).toBeHidden();
    // Losing the edit here would be the whole cost of the conflict.
    expect(await page.locator('#settings-text').inputValue()).toBe(edited);
  });

  test('a device that may not publish is told that, not that it failed', async ({ page }) => {
    await withBroker(page, {
      write: {
        status: 403,
        payload: { ok: false, reason: 'not-allowed', detail: 'Registered but not allowed.' },
      },
    });
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();

    await expect(page.locator('#settings-status')).toContainText('not yet allowed');
  });

  test('a broker that is down falls back to handing the file over', async ({ page }) => {
    await withBroker(page, {
      write: { status: 500, payload: { ok: false, detail: 'Everything is on fire.' } },
    });
    await signedIn(page);

    await page.locator('#settings-text').fill(edited);
    await page.locator('#settings-save').click();

    // The edit survives as something the member can send us by hand. This is
    // the state the page was in before the broker existed, which is exactly
    // why it is worth keeping.
    await expect(page.locator('[data-state="manual"]')).toBeVisible();
    await expect(page.locator('#settings-output')).toContainText('Jane Live');
    await expect(page.locator('#email-settings')).toHaveAttribute('href', /^mailto:/);
  });
});
