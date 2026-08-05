// Building real assertions to test against.
//
// Nothing here is a mock of the verification. The tests generate an actual
// P-256 key, assemble actual authenticator data, and produce an actual ECDSA
// signature — because the failures worth catching in this code are failures of
// byte layout, and a mock would agree with whatever the code already does.
//
// rawToDer below is written from the DER rules rather than by inverting
// derToRawSignature. Two implementations of the same encoding, arrived at
// separately, is what makes the round trip a check instead of a mirror.

export const b64u = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/** Raw r||s into DER SEQUENCE(INTEGER, INTEGER). */
export function rawToDer(raw) {
  const half = raw.length / 2;

  const integer = (scalar) => {
    let start = 0;
    while (start < scalar.length - 1 && scalar[start] === 0) start += 1;
    let value = Array.from(scalar.subarray(start));
    // Top bit set would read as negative, so DER prefixes a zero.
    if (value[0] & 0x80) value = [0, ...value];
    return [0x02, value.length, ...value];
  };

  const body = [...integer(raw.subarray(0, half)), ...integer(raw.subarray(half))];
  return Uint8Array.from([0x30, body.length, ...body]);
}

const sha256 = async (bytes) => new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
const utf8 = (text) => new TextEncoder().encode(text);

/** A passkey: the private half stays here, the record is what a repo holds. */
export async function makeCredential({ label = 'Test phone', mayPublish = true } = {}) {
  const pair = await crypto.subtle.generateKey(
    { name: 'ECDSA', namedCurve: 'P-256' },
    true,
    ['sign', 'verify']
  );
  const spki = new Uint8Array(await crypto.subtle.exportKey('spki', pair.publicKey));
  const credentialId = b64u(crypto.getRandomValues(new Uint8Array(16)));

  return {
    pair,
    credentialId,
    record: {
      credential_id: credentialId,
      public_key: b64u(spki),
      algorithm: -7,
      label,
      added: '2026-01-01T00:00:00.000Z',
      may_publish: mayPublish,
    },
  };
}

export const FLAG_USER_PRESENT = 0x01;
export const FLAG_USER_VERIFIED = 0x04;

/** What a browser hands back from navigator.credentials.get(). */
export async function makeAssertion(credential, options) {
  const {
    challenge,
    origin,
    rpId,
    type = 'webauthn.get',
    flags = FLAG_USER_PRESENT | FLAG_USER_VERIFIED,
    counter = 7,
    crossOrigin = false,
    rawSignature = false,
  } = options;

  const authenticatorData = new Uint8Array(37);
  authenticatorData.set(await sha256(utf8(rpId)), 0);
  authenticatorData[32] = flags;
  new DataView(authenticatorData.buffer).setUint32(33, counter);

  const clientDataBytes = utf8(JSON.stringify({ type, challenge, origin, crossOrigin }));

  const signed = new Uint8Array(authenticatorData.length + 32);
  signed.set(authenticatorData, 0);
  signed.set(await sha256(clientDataBytes), authenticatorData.length);

  const raw = new Uint8Array(
    await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, credential.pair.privateKey, signed)
  );

  return {
    credential_id: credential.credentialId,
    authenticator_data: b64u(authenticatorData),
    client_data_json: b64u(clientDataBytes),
    signature: b64u(rawSignature ? raw : rawToDer(raw)),
  };
}

/* ------------------------------------------------------------------- doubles */

/** KV, minus the network and the eventual consistency. */
export function memoryKV() {
  const entries = new Map();
  return {
    entries,
    async put(key, value) {
      entries.set(key, value);
    },
    async get(key) {
      return entries.has(key) ? entries.get(key) : null;
    },
    async delete(key) {
      entries.delete(key);
    },
  };
}

/**
 * GitHub, enough of it.
 *
 * Both hosts, because the broker uses one fetch for both: raw.githubusercontent
 * for the device list and the API for the write. Stateful rather than
 * canned — the interesting questions are "does a retry land in the same place"
 * and "does a stale SHA get refused", and neither can be asked of a fake that
 * answers the same thing every time.
 *
 * `byRepo` maps a repository to its .auth/devices.json. `undefined` is a 404
 * (no list) and `null` is a 500 (GitHub having a bad minute).
 */
export function fakeGitHub(byRepo = {}, { blobs = {}, defaultBranch = 'main' } = {}) {
  // Files are per branch, because that is what makes a retry different from a
  // conflict: the second attempt writes to a branch that already holds the
  // first attempt's bytes, and a fake that tracked one copy per repository
  // could not tell the two apart. `blobs` seeds the default branch.
  const files = new Map(); // "repo#branch/path" -> { sha, content }
  for (const [key, sha] of Object.entries(blobs)) {
    const parts = key.split('/');
    const repo = parts.slice(0, 2).join('/');
    const path = parts.slice(2).join('/');
    files.set(`${repo}#${defaultBranch}/${path}`, { sha, content: 'whatever was there before\n' });
  }

  const refs = new Set();
  const pulls = [];
  const written = [];
  const calls = [];

  const json = (body, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

  const base64 = (text) => {
    let binary = '';
    for (const byte of new TextEncoder().encode(text)) binary += String.fromCharCode(byte);
    return btoa(binary);
  };

  const fetchImpl = async (input, options = {}) => {
    const url = String(input);
    const method = options.method || 'GET';
    const body = options.body ? JSON.parse(options.body) : null;
    calls.push({ url, method, body });

    const raw = url.match(/^https:\/\/raw\.githubusercontent\.com\/([^/]+\/[^/]+)\/HEAD\/(.+)$/);
    if (raw) {
      const held = byRepo[raw[1]];
      if (held === undefined) return new Response('Not Found', { status: 404 });
      if (held === null) return new Response('Server Error', { status: 500 });
      return new Response(typeof held === 'string' ? held : JSON.stringify(held), { status: 200 });
    }

    const api = url.match(/^https:\/\/api\.github\.com\/repos\/([^/]+\/[^/?]+)(.*)$/);
    if (!api) return new Response('Not Found', { status: 404 });
    const [, repo, rest] = api;

    if (method === 'GET' && rest === '') return json({ default_branch: defaultBranch });

    if (method === 'GET' && rest.startsWith('/git/ref/heads/')) {
      return json({ object: { sha: 'f'.repeat(40) } });
    }

    if (method === 'POST' && rest === '/git/refs') {
      const name = body.ref.replace('refs/heads/', '');
      if (refs.has(`${repo}#${name}`)) return json({ message: 'Reference already exists' }, 422);
      refs.add(`${repo}#${name}`);
      // A new branch starts as a copy of the one it was cut from.
      for (const [key, held] of [...files]) {
        if (key.startsWith(`${repo}#${defaultBranch}/`)) {
          files.set(key.replace(`#${defaultBranch}/`, `#${name}/`), { ...held });
        }
      }
      return json({ ref: body.ref }, 201);
    }

    if (rest.startsWith('/contents/')) {
      const [target, query] = rest.slice('/contents/'.length).split('?');
      const path = decodeURI(target);

      if (method === 'GET') {
        const ref = new URLSearchParams(query || '').get('ref') || defaultBranch;
        const held = files.get(`${repo}#${ref}/${path}`);
        if (!held) return json({ message: 'Not Found' }, 404);
        return json({ sha: held.sha, encoding: 'base64', content: base64(held.content) });
      }

      const branch = body.branch || defaultBranch;
      const key = `${repo}#${branch}/${path}`;
      // The SHA is the whole point: a write carrying a stale one is refused
      // rather than allowed to discard somebody else's change.
      if ((files.get(key)?.sha || '') !== (body.sha || '')) {
        return json({ message: 'does not match' }, 409);
      }

      const content = new TextDecoder().decode(
        Uint8Array.from(atob(body.content), (c) => c.charCodeAt(0))
      );
      files.set(key, { sha: `${written.length}`.padStart(40, '0'), content });
      written.push({ repo, path, branch, message: body.message, content });
      return json({ commit: { html_url: `https://github.com/${repo}/commit/abc123` } });
    }

    if (method === 'POST' && rest === '/pulls') {
      if (pulls.some((pull) => pull.repo === repo && pull.head === body.head)) {
        return json({ message: 'A pull request already exists' }, 422);
      }
      const pull = {
        repo,
        head: body.head,
        base: body.base,
        title: body.title,
        html_url: `https://github.com/${repo}/pull/${pulls.length + 1}`,
      };
      pulls.push(pull);
      return json(pull, 201);
    }

    if (method === 'GET' && rest.startsWith('/pulls?')) {
      const head = decodeURIComponent(new URLSearchParams(rest.slice(rest.indexOf('?'))).get('head') || '');
      const branch = head.split(':')[1];
      return json(pulls.filter((pull) => pull.repo === repo && pull.head === branch));
    }

    return new Response('Not Found', { status: 404 });
  };

  return { fetchImpl, written, pulls, refs, calls };
}

/** The device-list half on its own, for tests that never write. */
export const fakeRaw = (byRepo) => fakeGitHub(byRepo).fetchImpl;
