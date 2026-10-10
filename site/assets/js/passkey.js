// see docs/inline/site/assets/js/passkey.js.md#1

const B64 = {
  encode(bytes) {
    let binary = '';
    for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  },
};

export const supported = () =>
  Boolean(window.PublicKeyCredential && navigator.credentials?.create);

// see docs/inline/site/assets/js/passkey.js.md#2
const HANDLE_VERSION = 'v1';
const HANDLE_LIMIT = 64; // WebAuthn's ceiling for user.id

async function shortDigest(value) {
  const bytes = new Uint8Array(
    await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  );
  return Array.from(bytes.slice(0, 4), (b) => b.toString(16).padStart(2, '0')).join('');
}

async function encodeHandle(email, repo) {
  const handle = `${HANDLE_VERSION}|${repo}|${await shortDigest(email)}`;
  const bytes = new TextEncoder().encode(handle);
  if (bytes.length > HANDLE_LIMIT) return null;
  return bytes;
}

// see docs/inline/site/assets/js/passkey.js.md#3
export function decodeHandle(bytes) {
  if (!bytes) return null;
  let text;
  try {
    text = new TextDecoder().decode(bytes);
  } catch (error) {
    return null;
  }

  const parts = text.split('|');
  if (parts.length !== 3 || parts[0] !== HANDLE_VERSION) return null;
  if (parts[1].split('/').length !== 2) return null;

  return { repo: parts[1], person: parts[2] };
}

// see docs/inline/site/assets/js/passkey.js.md#4
export async function createPasskey({ email, repo, label, rpId, issuer }) {
  if (!supported()) return { ok: false, reason: 'unsupported' };

  const handle = await encodeHandle(email, repo);
  if (!handle) return { ok: false, reason: 'repo-too-long' };

  const challenge = crypto.getRandomValues(new Uint8Array(32));

  // see docs/inline/site/assets/js/passkey.js.md#5
  const rp = { name: issuer || 'Fort Collins Public Media' };
  if (rpId) rp.id = rpId;

  let credential;
  try {
    credential = await navigator.credentials.create({
      publicKey: {
        challenge,
        rp,
        user: {
          id: handle,
          name: email,
          displayName: label || email,
        },
        // ES256 first, RS256 as a fallback for authenticators that want it.
        pubKeyCredParams: [
          { type: 'public-key', alg: -7 },
          { type: 'public-key', alg: -257 },
        ],
        authenticatorSelection: {
          // see docs/inline/site/assets/js/passkey.js.md#6
          residentKey: 'required',
          userVerification: 'preferred',
        },
        // see docs/inline/site/assets/js/passkey.js.md#7
        attestation: 'none',
        timeout: 120000,
      },
    });
  } catch (error) {
    const reason = error?.name === 'NotAllowedError' ? 'cancelled' : 'failed';
    return { ok: false, reason, detail: error?.message || String(error) };
  }

  if (!credential) return { ok: false, reason: 'cancelled' };

  const response = credential.response;

  // see docs/inline/site/assets/js/passkey.js.md#8
  const spki = response.getPublicKey?.();
  if (!spki) {
    return { ok: false, reason: 'no-public-key' };
  }

  return {
    ok: true,
    device: {
      credential_id: B64.encode(credential.rawId),
      // SPKI, so crypto.subtle.importKey('spki', …) reads it as-is later.
      public_key: B64.encode(spki),
      algorithm: response.getPublicKeyAlgorithm?.() ?? null,
      transports: response.getTransports?.() ?? [],
      label: (label || '').trim() || 'Unnamed device',
      added: new Date().toISOString(),
    },
  };
}

// see docs/inline/site/assets/js/passkey.js.md#9
async function requestChallenge(brokerUrl, intent) {
  let response;
  try {
    // see docs/inline/site/assets/js/passkey.js.md#10
    response = await fetch(`${brokerUrl.replace(/\/+$/, '')}/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intent),
    });
  } catch (error) {
    return { ok: false, detail: 'We could not reach the server.' };
  }

  const body = await response.json().catch(() => ({}));
  if (!response.ok || !body.challenge) {
    return { ok: false, detail: body.detail || `The server said no (HTTP ${response.status}).` };
  }
  return { ok: true, challenge: body.challenge, intent: body.intent };
}

// see docs/inline/site/assets/js/passkey.js.md#11
export async function signIn({ rpId, brokerUrl, intent, credentialId } = {}) {
  if (!window.PublicKeyCredential || !navigator.credentials?.get) {
    return { ok: false, reason: 'unsupported' };
  }

  let challenge = null;
  if (brokerUrl) {
    if (!intent) throw new Error('signIn with a broker needs an intent to bind the challenge to');
    const issued = await requestChallenge(brokerUrl, intent);
    if (!issued.ok) return { ok: false, reason: 'no-challenge', detail: issued.detail };
    challenge = issued.challenge;
  }

  const request = {
    challenge: challenge
      ? Uint8Array.from(atob(challenge.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0))
      : crypto.getRandomValues(new Uint8Array(32)),
    // see docs/inline/site/assets/js/passkey.js.md#12
    userVerification: brokerUrl ? 'required' : 'preferred',
    timeout: 120000,
    // see docs/inline/site/assets/js/passkey.js.md#13
  };
  if (rpId) request.rpId = rpId;

  // see docs/inline/site/assets/js/passkey.js.md#14
  if (credentialId) {
    request.allowCredentials = [
      {
        type: 'public-key',
        id: Uint8Array.from(
          atob(credentialId.replace(/-/g, '+').replace(/_/g, '/')),
          (c) => c.charCodeAt(0)
        ),
      },
    ];
  }

  let assertion;
  try {
    assertion = await navigator.credentials.get({ publicKey: request });
  } catch (error) {
    const reason = error?.name === 'NotAllowedError' ? 'cancelled' : 'failed';
    return { ok: false, reason, detail: error?.message || String(error) };
  }

  if (!assertion) return { ok: false, reason: 'cancelled' };

  const handle = decodeHandle(assertion.response?.userHandle);
  if (!handle) {
    // see docs/inline/site/assets/js/passkey.js.md#15
    return { ok: false, reason: 'unreadable' };
  }

  return {
    ok: true,
    repo: handle.repo,
    person: handle.person,
    credentialId: B64.encode(assertion.rawId),
    verified: Boolean(brokerUrl),
    // see docs/inline/site/assets/js/passkey.js.md#16
    assertion: {
      credential_id: B64.encode(assertion.rawId),
      authenticator_data: B64.encode(assertion.response.authenticatorData),
      client_data_json: B64.encode(assertion.response.clientDataJSON),
      signature: B64.encode(assertion.response.signature),
    },
  };
}
