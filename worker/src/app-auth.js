// see docs/inline/worker/src/app-auth.js.md#1

const API = 'https://api.github.com';

// see docs/inline/worker/src/app-auth.js.md#2
const JWT_LIFETIME = 540;
const SKEW = 60;

// Re-mint a minute early rather than discovering expiry mid-write.
const EARLY = 60_000;

// see docs/inline/worker/src/app-auth.js.md#3
const PERMISSIONS = { contents: 'write', pull_requests: 'write' };

const utf8 = (text) => new TextEncoder().encode(text);

const b64u = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

// see docs/inline/worker/src/app-auth.js.md#4
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
    // see docs/inline/worker/src/app-auth.js.md#5
    iat: seconds - SKEW,
    exp: seconds + JWT_LIFETIME,
    iss: appId,
  };

  const signed = `${b64u(utf8(JSON.stringify(header)))}.${b64u(utf8(JSON.stringify(payload)))}`;
  const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, utf8(signed));
  return `${signed}.${b64u(signature)}`;
}

// see docs/inline/worker/src/app-auth.js.md#6
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
      // see docs/inline/worker/src/app-auth.js.md#7
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

// see docs/inline/worker/src/app-auth.js.md#8
export const patCredential = (token) => async () =>
  token ? { ok: true, token } : { ok: false, detail: 'GITHUB_TOKEN is not set.' };
