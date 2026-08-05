// Being a GitHub App rather than a person.
//
// WHY NOT A PERSONAL ACCESS TOKEN
// -------------------------------
// A token belongs to whoever made it. It outlives their interest in the
// project and dies with their account, so the day somebody leaves the board is
// the day member sites stop saving — and nobody will connect those two events.
// An App belongs to the organization.
//
// The rest follows from that:
//
//   * The stored secret is a private key that signs requests for tokens. It is
//     never itself a token, so it cannot be replayed against the API.
//   * The tokens it mints last an hour and are minted per write.
//   * Each one is narrowed at the moment of minting to ONE repository and two
//     permissions. An installation covering forty member sites still produces
//     a credential good for one of them.
//   * Revoking a site is uninstalling the App from it. No list to edit, and no
//     way to forget.
//   * Workflows are not among the permissions granted, so the API refuses a
//     write to .github/ regardless of what this code does. intent.js refuses
//     it too. Two locks, which is what that README claim needs to be true.
//
// _data/authorize.yml said "a GitHub App installation token" from the start.
// This is that.
//
// SETUP
// -----
//   1. Create an App under the organization. Permissions: Contents (write),
//      Pull requests (write), Metadata (read). Nothing else — especially not
//      Workflows, Secrets, or Administration.
//   2. Install it on the member repositories.
//   3. Generate a private key. GitHub hands back PKCS#1, which WebCrypto
//      cannot read, so convert it once:
//
//        openssl pkcs8 -topk8 -nocrypt -in app.private-key.pem -out app.pkcs8.pem
//
//   4. npx wrangler secret put GITHUB_APP_KEY   < paste app.pkcs8.pem
//      npx wrangler secret put GITHUB_APP_ID    < the numeric App ID

const API = 'https://api.github.com';

// GitHub rejects a JWT claiming more than ten minutes. Nine leaves room for
// the clock skew allowance below without ever crossing the ceiling.
const JWT_LIFETIME = 540;
const SKEW = 60;

// Re-mint a minute early rather than discovering expiry mid-write.
const EARLY = 60_000;

// Everything the broker is allowed to do, restated at the moment of minting.
// The installation may hold more; a token from here never does.
const PERMISSIONS = { contents: 'write', pull_requests: 'write' };

const utf8 = (text) => new TextEncoder().encode(text);

const b64u = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/**
 * Read the App's private key.
 *
 * The PKCS#1 case gets its own message on purpose. GitHub's download button
 * produces exactly that format, WebCrypto's error for it is "Invalid keyData",
 * and the fix is one command that nobody guesses.
 */
async function importPrivateKey(pem) {
  const text = String(pem || '').trim();
  if (!text) throw new Error('no private key');

  if (/BEGIN RSA PRIVATE KEY/.test(text)) {
    throw new Error(
      'the private key is in PKCS#1, which is what GitHub hands you and what ' +
      'WebCrypto cannot read. Convert it once: openssl pkcs8 -topk8 -nocrypt ' +
      '-in app.private-key.pem -out app.pkcs8.pem'
    );
  }
  if (!/BEGIN PRIVATE KEY/.test(text)) {
    throw new Error('the private key does not look like a PEM file');
  }

  const der = Uint8Array.from(
    atob(text.replace(/-----[^-]*-----/g, '').replace(/\s/g, '')),
    (c) => c.charCodeAt(0)
  );

  return crypto.subtle.importKey(
    'pkcs8',
    der,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  );
}

/** A short-lived assertion that we are the App. Not a token; buys tokens. */
async function appJwt(appId, key, now) {
  const seconds = Math.floor(now / 1000);
  const header = { alg: 'RS256', typ: 'JWT' };
  const payload = {
    // Back-dated, because GitHub rejects a JWT issued in its future and our
    // clock is not their clock.
    iat: seconds - SKEW,
    exp: seconds + JWT_LIFETIME,
    iss: appId,
  };

  const signed = `${b64u(utf8(JSON.stringify(header)))}.${b64u(utf8(JSON.stringify(payload)))}`;
  const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, utf8(signed));
  return `${signed}.${b64u(signature)}`;
}

/**
 * A credential source: hand it a repository, get a token good for that one.
 *
 * Resolves to { ok: true, token } or { ok: false, detail }. Never throws — a
 * misconfigured App is something the page has to tell somebody about, not a
 * stack trace.
 *
 * CACHING, AND WHERE IT DELIBERATELY IS NOT
 * -----------------------------------------
 * Tokens are held in memory, in the isolate, and nowhere else. Not KV. A
 * write credential at rest in a store that outlives the request is a worse
 * thing to have than the handful of extra API calls avoiding it costs. The
 * cache dying with the isolate is the correct lifetime.
 */
export function appCredential({ appId, privateKey, fetchImpl = fetch, api = API, now = () => Date.now() }) {
  let key = null;
  let keyProblem = null;
  const installations = new Map(); // repo -> installation id
  const tokens = new Map(); // repo -> { token, expires }

  async function loadKey() {
    if (key || keyProblem) return;
    try {
      key = await importPrivateKey(privateKey);
    } catch (error) {
      keyProblem = error.message;
    }
  }

  async function asApp(path, options = {}) {
    const jwt = await appJwt(appId, key, now());
    const response = await fetchImpl(`${api}${path}`, {
      method: options.method || 'GET',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${jwt}`,
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'fcpm-broker',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      },
      ...(options.body ? { body: JSON.stringify(options.body) } : {}),
    });
    return { status: response.status, ok: response.ok, payload: await response.json().catch(() => ({})) };
  }

  return async function tokenFor(repo) {
    if (!appId) return { ok: false, detail: 'GITHUB_APP_ID is not set.' };

    await loadKey();
    if (keyProblem) return { ok: false, detail: `GITHUB_APP_KEY: ${keyProblem}.` };

    const held = tokens.get(repo);
    if (held && held.expires - EARLY > now()) return { ok: true, token: held.token };

    let installation = installations.get(repo);
    if (!installation) {
      const found = await asApp(`/repos/${repo}/installation`);
      if (found.status === 404) {
        return {
          ok: false,
          detail: `the app is not installed on ${repo}. Installing it is how a site is granted, and uninstalling is how it is revoked.`,
        };
      }
      if (!found.ok) {
        return { ok: false, detail: `GitHub returned ${found.status} looking up the installation.` };
      }
      installation = found.payload.id;
      installations.set(repo, installation);
    }

    const minted = await asApp(`/app/installations/${installation}/access_tokens`, {
      method: 'POST',
      // Narrowed here, every time. An installation spanning every member site
      // still yields a token that can only touch this one.
      body: { repositories: [repo.split('/')[1]], permissions: PERMISSIONS },
    });
    if (!minted.ok || !minted.payload?.token) {
      return { ok: false, detail: `GitHub returned ${minted.status} minting a token.` };
    }

    tokens.set(repo, {
      token: minted.payload.token,
      expires: Date.parse(minted.payload.expires_at) || now() + 3_600_000,
    });
    return { ok: true, token: minted.payload.token };
  };
}

/**
 * A personal access token, wrapped to look the same.
 *
 * A stopgap for trying the broker out before an App exists, and the reason
 * index.js prefers the App whenever both are configured. Everything in the
 * comment at the top of this file is an argument against leaving it here.
 */
export const patCredential = (token) => async () =>
  token ? { ok: true, token } : { ok: false, detail: 'GITHUB_TOKEN is not set.' };
