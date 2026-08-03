// Email claims, checked across the seam.
//
// script/mint-claim.py signs with openssl. assets/js/claims.js verifies with
// WebCrypto. Those are two different implementations of the same standard,
// joined by a hand-written DER conversion, and the failure mode is a token
// that looks perfect and verifies nowhere.
//
// So these tests mint real tokens with the real script and verify them in a
// real browser. Nothing is stubbed in the middle, because the middle is the
// part that can be wrong.

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
let otherKey;

/** Run the minting script and return its stdout. */
function mint(args) {
  return execFileSync('python3', [SCRIPT, ...args], { encoding: 'utf8' }).trim();
}

/** Parse the YAML block --new-key prints into the object the page consumes. */
function parseKeyBlock(output) {
  const grab = (field) => output.match(new RegExp(`${field}:\\s*"([^"]+)"`))[1];
  return { id: grab('id'), x: grab('x'), y: grab('y') };
}

/** The token out of the URL the script prints. */
function tokenFrom(url) {
  return url.split('#claim=')[1];
}

test.beforeAll(() => {
  workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'fcpm-claims-'));

  keyPath = path.join(workdir, 'key.pem');
  publicKey = parseKeyBlock(mint(['--new-key', keyPath]));

  // A second, unrelated key: the thing a forged claim would be signed with.
  const otherPath = path.join(workdir, 'other.pem');
  otherKey = parseKeyBlock(mint(['--new-key', otherPath]));
  otherKey.path = otherPath;
});

test.afterAll(() => {
  fs.rmSync(workdir, { recursive: true, force: true });
});

/** Verify a token through the page's own module, in the page's own browser. */
async function verify(page, token, keys, now) {
  await page.goto('/check-in/');
  return page.evaluate(
    async ({ token, keys, now }) => {
      const module = await import('/assets/js/claims.js');
      return module.verifyClaim(token, keys, now ?? Date.now());
    },
    { token, keys, now }
  );
}

test.describe('claim verification', () => {
  test('a freshly minted claim verifies', async ({ page }) => {
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));

    const result = await verify(page, token, [publicKey]);

    expect(result.ok).toBe(true);
    expect(result.payload.email).toBe('someone@example.com');
  });

  test('the address is lower-cased at minting, not at reading', async ({ page }) => {
    // Two people typing the same address differently must not become two
    // records. Normalising once, at the source, is what makes the token itself
    // the canonical form.
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'Someone@Example.COM']));

    const result = await verify(page, token, [publicKey]);

    expect(result.payload.email).toBe('someone@example.com');
  });

  test('a claim signed by another key is rejected', async ({ page }) => {
    const token = tokenFrom(
      mint(['--key', otherKey.path, '--email', 'someone@example.com'])
    );

    const result = await verify(page, token, [publicKey]);

    expect(result.ok).toBe(false);
    expect(result.reason).toBe('signature');
  });

  test('an altered address is rejected', async ({ page }) => {
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));
    const [version, body, signature] = token.split('.');

    // Re-encode the payload with a different address, keeping the signature.
    const forged = Buffer.from(
      JSON.stringify({
        ...JSON.parse(Buffer.from(body, 'base64url').toString()),
        email: 'attacker@example.com',
      })
    ).toString('base64url');

    const result = await verify(page, `${version}.${forged}.${signature}`, [publicKey]);

    expect(result.ok).toBe(false);
    expect(result.reason).toBe('signature');
  });

  test('an expired claim is reported as expired, not as a forgery', async ({ page }) => {
    // The distinction is the whole reason expiry is checked after the
    // signature: one means "ask for a new link", the other means "something is
    // wrong". Telling someone their genuine link was tampered with sends them
    // to the wrong place.
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com', '--days', '1']));

    const result = await verify(page, token, [publicKey], Date.now() + 2 * 86400 * 1000);

    expect(result.ok).toBe(false);
    expect(result.reason).toBe('expired');
    expect(result.payload.email).toBe('someone@example.com');
  });

  test('a claim still verifies after a key rotation adds a newer key', async ({ page }) => {
    // Links already sitting in inboxes have to keep working, which is the only
    // reason the config holds a list instead of a key.
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));

    const result = await verify(page, token, [otherKey, publicKey]);

    expect(result.ok).toBe(true);
  });

  test('garbage is refused without throwing', async ({ page }) => {
    for (const bad of ['', 'nonsense', 'v1.only-two', 'v2.a.b', 'v1.!!!.###']) {
      const result = await verify(page, bad, [publicKey]);
      expect(result.ok, `${bad} was accepted`).toBe(false);
    }
  });

  test('no configured keys means nothing verifies', async ({ page }) => {
    // The shipped state. A site with no keys must reject rather than wave
    // things through.
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));

    const result = await verify(page, token, []);

    expect(result.ok).toBe(false);
  });
});

test.describe('redeeming a claim on the page', () => {
  /** Serve the check-in page with a key configured, as a live site would. */
  async function withKey(page) {
    await page.route('**/check-in/', async (route) => {
      const response = await route.fetch();
      const body = (await response.text()).replace(
        '"keys": []',
        `"keys": [${JSON.stringify(publicKey)}]`
      );
      await route.fulfill({ response, body });
    });
  }

  test('opening a claim link confirms the address', async ({ page }) => {
    await withKey(page);
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'member@example.com']));

    await page.goto(`/check-in/#claim=${token}`);

    await expect(page.locator('[data-claim="verified"]')).toBeVisible();
    await expect(page.locator('#claim-email')).toHaveText('member@example.com');
    await expect(page.locator('[data-claim="none"]')).toBeHidden();
  });

  test('the token is taken out of the address bar', async ({ page }) => {
    // It is stored by now, and a URL still carrying it is one someone might
    // paste into a group chat, handing their address to everyone in it.
    await withKey(page);
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'member@example.com']));

    await page.goto(`/check-in/#claim=${token}`);
    await expect(page.locator('[data-claim="verified"]')).toBeVisible();

    expect(page.url()).not.toContain('claim=');
  });

  test('the confirmation survives a reload', async ({ page }) => {
    await withKey(page);
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'member@example.com']));

    await page.goto(`/check-in/#claim=${token}`);
    await expect(page.locator('#claim-email')).toHaveText('member@example.com');

    await page.goto('/check-in/');
    await expect(page.locator('#claim-email')).toHaveText('member@example.com');
  });

  test('a bad link says so and leaves the page usable', async ({ page }) => {
    await withKey(page);

    await page.goto('/check-in/#claim=v1.bogus.bogus');

    await expect(page.locator('#claim-status')).toBeVisible();
    // Still able to type an address by hand — a broken link must not be a
    // dead end.
    await expect(page.locator('#profile-email')).toBeVisible();
  });

  test('an expired link says to ask for a new one', async ({ page }) => {
    await withKey(page);
    const token = tokenFrom(
      mint(['--key', keyPath, '--email', 'member@example.com', '--days', '-1'])
    );

    await page.goto(`/check-in/#claim=${token}`);

    await expect(page.locator('#claim-status')).toContainText('expired');
    await expect(page.locator('[data-claim="none"]')).toBeVisible();
  });

  test('removing it returns the page to the typed-address state', async ({ page }) => {
    await withKey(page);
    const token = tokenFrom(mint(['--key', keyPath, '--email', 'member@example.com']));

    await page.goto(`/check-in/#claim=${token}`);
    await expect(page.locator('[data-claim="verified"]')).toBeVisible();

    page.on('dialog', (dialog) => dialog.accept());
    await page.locator('#claim-forget').click();

    await expect(page.locator('[data-claim="none"]')).toBeVisible();
    await expect(page.locator('[data-claim="verified"]')).toBeHidden();
  });
});

test.describe('email without a claim', () => {
  test('the typed-address field is what a visitor sees by default', async ({ page }) => {
    // No keys are configured on the shipped site, so this is the state
    // everyone is actually in. It must not read as an error.
    await page.goto('/check-in/');

    await expect(page.locator('[data-claim="none"]')).toBeVisible();
    await expect(page.locator('[data-claim="verified"]')).toBeHidden();
    await expect(page.locator('#claim-status')).toBeHidden();
  });

  test('a typed address is remembered on this device', async ({ page }) => {
    await page.goto('/check-in/');
    await page.locator('#profile-email').fill('typed@example.com');

    await page.goto('/check-in/');

    await expect(page.locator('#profile-email')).toHaveValue('typed@example.com');
  });

  test('a typed address is recorded, and recorded as unconfirmed', async ({ page }) => {
    // The distinction has to survive into the history, or the record claims
    // more than it knows.
    await page.clock.setFixedTime(new Date('2026-08-03T18:00:00Z'));
    await page.context().grantPermissions(['geolocation']);
    await page.context().setGeolocation({ latitude: 40.5849119, longitude: -105.0735292 });

    await page.goto('/check-in/');
    await page.locator('#profile-email').fill('typed@example.com');
    await page.locator('[data-state="idle"] [data-action="check-in"]').click();

    await expect(page.locator('[data-state="done"]')).toBeVisible();
    await expect(page.locator('#done-detail')).toContainText("haven't confirmed");
    await expect(page.locator('#checkin-history li')).toContainText('unconfirmed');
  });
});
