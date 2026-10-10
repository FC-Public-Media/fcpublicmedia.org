// see docs/inline/worker/src/webauthn.js.md#1

/* --------------------------------------------------------------------- bytes */

export function fromBase64Url(value) {
  const padded = String(value).replace(/-/g, '+').replace(/_/g, '/');
  const binary = atob(padded + '='.repeat((4 - (padded.length % 4)) % 4));
  return Uint8Array.from(binary, (c) => c.charCodeAt(0));
}

export function toBase64Url(bytes) {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

const sha256 = async (bytes) =>
  new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));

const utf8 = (text) => new TextEncoder().encode(text);

/** Same length, same bytes, without leaking where the first difference was. */
function sameBytes(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i += 1) diff |= a[i] ^ b[i];
  return diff === 0;
}

/** The string form of the above, for values that arrive already encoded. */
function sameString(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  return sameBytes(utf8(a), utf8(b));
}

/* ------------------------------------------------------------------ signature */

const P256_SCALAR = 32;

// see docs/inline/worker/src/webauthn.js.md#2
export function derToRawSignature(der, size = P256_SCALAR) {
  const bytes = new Uint8Array(der);
  let at = 0;

  const byte = () => {
    if (at >= bytes.length) throw new Error('signature ended early');
    return bytes[at++];
  };

  if (byte() !== 0x30) throw new Error('signature is not a DER sequence');

  // see docs/inline/worker/src/webauthn.js.md#3
  const length = byte();
  if (length & 0x80) throw new Error('signature length is not short-form DER');
  // Covers both a truncated signature and one with something appended.
  if (at + length !== bytes.length) {
    throw new Error('signature is not the length it declares');
  }

  const scalar = () => {
    if (byte() !== 0x02) throw new Error('signature member is not an integer');
    const size_ = byte();
    if (size_ & 0x80) throw new Error('signature member is absurdly long');
    if (at + size_ > bytes.length) throw new Error('signature member overruns');

    let value = bytes.subarray(at, at + size_);
    at += size_;

    // see docs/inline/worker/src/webauthn.js.md#4
    while (value.length > 1 && value[0] === 0) value = value.subarray(1);
    if (value.length > size) throw new Error('signature member is too large');

    // see docs/inline/worker/src/webauthn.js.md#5
    const padded = new Uint8Array(size);
    padded.set(value, size - value.length);
    return padded;
  };

  const r = scalar();
  const s = scalar();
  if (at !== bytes.length) throw new Error('signature has trailing members');

  const raw = new Uint8Array(size * 2);
  raw.set(r, 0);
  raw.set(s, size);
  return raw;
}

// see docs/inline/worker/src/webauthn.js.md#6
function normalizeEcdsaSignature(signature) {
  if (signature.length === P256_SCALAR * 2) return signature;
  return derToRawSignature(signature);
}

/* ------------------------------------------------------------------ the check */

const ALG_ES256 = -7;
const ALG_RS256 = -257;

const IMPORTS = {
  [ALG_ES256]: {
    key: { name: 'ECDSA', namedCurve: 'P-256' },
    verify: { name: 'ECDSA', hash: 'SHA-256' },
    signature: normalizeEcdsaSignature,
  },
  [ALG_RS256]: {
    key: { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    verify: { name: 'RSASSA-PKCS1-v1_5' },
    signature: (signature) => signature,
  },
};

// see docs/inline/worker/src/webauthn.js.md#7
async function importPublicKey(spki, algorithm) {
  const candidates = algorithm == null ? [ALG_ES256, ALG_RS256] : [algorithm];

  for (const alg of candidates) {
    const shape = IMPORTS[alg];
    if (!shape) continue;
    try {
      const key = await crypto.subtle.importKey('spki', spki, shape.key, false, ['verify']);
      return { key, shape };
    } catch (error) {
      // Wrong guess. Only meaningful when there was another to try.
    }
  }
  return null;
}

// Flags live in one byte after the RP ID hash.
const FLAG_USER_PRESENT = 0x01;
const FLAG_USER_VERIFIED = 0x04;
const AUTH_DATA_MINIMUM = 37; // 32 hash + 1 flags + 4 counter

const no = (reason, detail) => ({ ok: false, reason, detail });

// see docs/inline/worker/src/webauthn.js.md#8
export async function verifyAssertion({ assertion, device, expected }) {
  let authenticatorData;
  let clientDataBytes;
  let signature;
  let publicKey;
  try {
    authenticatorData = fromBase64Url(assertion.authenticator_data);
    clientDataBytes = fromBase64Url(assertion.client_data_json);
    signature = fromBase64Url(assertion.signature);
    publicKey = fromBase64Url(device.public_key);
  } catch (error) {
    return no('malformed', 'A field was not base64url.');
  }

  /* ------------------------------------------------------------ client data */

  let clientData;
  try {
    clientData = JSON.parse(new TextDecoder().decode(clientDataBytes));
  } catch (error) {
    return no('malformed', 'The client data was not JSON.');
  }

  // see docs/inline/worker/src/webauthn.js.md#9
  if (clientData.type !== 'webauthn.get') {
    return no('wrong-ceremony', `The client data says ${clientData.type}.`);
  }

  if (!sameString(clientData.challenge, expected.challenge)) {
    return no('challenge', 'That is not the challenge we issued.');
  }

  // see docs/inline/worker/src/webauthn.js.md#10
  if (!expected.origins.includes(clientData.origin)) {
    return no('origin', `The ceremony happened at ${clientData.origin}.`);
  }

  // see docs/inline/worker/src/webauthn.js.md#11
  if (clientData.crossOrigin === true) {
    return no('cross-origin', 'The ceremony ran inside another site.');
  }

  /* --------------------------------------------------- authenticator data */

  if (authenticatorData.length < AUTH_DATA_MINIMUM) {
    return no('malformed', 'The authenticator data is too short to be real.');
  }

  const rpIdHash = authenticatorData.subarray(0, 32);
  if (!sameBytes(rpIdHash, await sha256(utf8(expected.rpId)))) {
    return no('rp-id', 'The passkey belongs to a different domain.');
  }

  const flags = authenticatorData[32];
  if (!(flags & FLAG_USER_PRESENT)) {
    return no('user-present', 'Nobody was at the device.');
  }
  if (expected.requireUserVerification && !(flags & FLAG_USER_VERIFIED)) {
    return no('user-verification', 'The device did not check who was holding it.');
  }

  /* ------------------------------------------------------------- signature */

  const imported = await importPublicKey(publicKey, device.algorithm ?? null);
  if (!imported) {
    return no('public-key', 'The recorded public key could not be read.');
  }

  let normalized;
  try {
    normalized = imported.shape.signature(signature);
  } catch (error) {
    return no('signature-encoding', error.message);
  }

  const signed = new Uint8Array(authenticatorData.length + 32);
  signed.set(authenticatorData, 0);
  signed.set(await sha256(clientDataBytes), authenticatorData.length);

  const valid = await crypto.subtle.verify(
    imported.shape.verify,
    imported.key,
    normalized,
    signed
  );
  if (!valid) return no('signature', 'The signature does not match the recorded key.');

  return {
    ok: true,
    flags: {
      userPresent: Boolean(flags & FLAG_USER_PRESENT),
      userVerified: Boolean(flags & FLAG_USER_VERIFIED),
    },
  };
}
