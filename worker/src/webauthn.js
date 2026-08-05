// Checking a WebAuthn assertion.
//
// This is the only file in the broker that decides whether a signature is
// genuine, and it is written so it can run anywhere with WebCrypto — no
// Workers APIs, no bindings, no network. That is deliberate: the tests drive
// it under plain Node with a real key and a real signature, which is the only
// way to find out whether the parsing below is right.
//
// WHAT AN ASSERTION ACTUALLY PROVES
// ---------------------------------
// The authenticator signs exactly two things joined together:
//
//     authenticatorData || SHA-256(clientDataJSON)
//
// Everything else the browser hands back — the credential ID, the user handle
// — travels ALONGSIDE the signature and is not covered by it. So none of it
// can be believed on its own. What makes this safe is that the credential ID
// is used to look up a public key that was recorded earlier, and the signature
// then has to verify under that key. A lie about the credential ID produces a
// lookup that fails or a key that does not verify. It is never trusted.
//
// The challenge is inside clientDataJSON, so it IS covered. That is what makes
// a captured assertion useless the second time: the challenge was issued by us,
// once, for one thing.
//
// THE PART MOST LIKELY TO BE QUIETLY WRONG
// ----------------------------------------
// WebAuthn's ES256 signatures are DER-encoded — a SEQUENCE of two INTEGERs.
// WebCrypto's verify() wants the raw 64 bytes, r followed by s, each padded to
// exactly 32. Converting between them means stripping the leading zero DER
// adds to keep an integer positive, and re-padding short values back out. Get
// it slightly wrong and roughly one signature in every hundred and thirty
// fails while the rest pass, which reads as "flaky authenticator" for months.
//
// script/mint-claim.py has the same seam in the other direction.

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

/**
 * DER SEQUENCE(INTEGER r, INTEGER s) into the raw r||s WebCrypto wants.
 *
 * Throws rather than returning something plausible. A signature that will not
 * parse is not a signature, and treating it as one that merely fails to verify
 * would hide a real bug behind a routine-looking rejection.
 */
export function derToRawSignature(der, size = P256_SCALAR) {
  const bytes = new Uint8Array(der);
  let at = 0;

  const byte = () => {
    if (at >= bytes.length) throw new Error('signature ended early');
    return bytes[at++];
  };

  if (byte() !== 0x30) throw new Error('signature is not a DER sequence');

  // Short form only. A P-256 signature is around seventy bytes, so a length
  // needing the long form means this is not what it claims to be.
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

    // DER prefixes a zero byte when the top bit is set, so the integer stays
    // positive. That byte is encoding, not value.
    while (value.length > 1 && value[0] === 0) value = value.subarray(1);
    if (value.length > size) throw new Error('signature member is too large');

    // And a scalar that happened to be small is short. Left-pad it back out;
    // WebCrypto wants a fixed width, not the minimal encoding.
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

/**
 * Some authenticators hand back the raw form already, in spite of the spec.
 *
 * A raw P-256 signature is exactly 64 bytes; DER encoding two full-width
 * scalars takes 70. DER only gets down to 64 if six bytes of leading zeros
 * turn up across r and s together, which is a one-in-2^48 accident, so
 * treating a 64-byte signature as raw is safe in the way that matters: it can
 * make a valid signature fail, never an invalid one pass.
 */
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

/**
 * Load a recorded public key.
 *
 * The algorithm is stored with the device — getPublicKeyAlgorithm() gives it
 * to us at registration — but records written before that was captured may not
 * have it, so an absent value means try the two we ask for, in the order we
 * ask for them.
 */
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

/**
 * Verify one assertion against one recorded device.
 *
 * `assertion` carries the base64url values the browser produced:
 *   { credential_id, authenticator_data, client_data_json, signature }
 *
 * `device` is the record from .auth/devices.json:
 *   { credential_id, public_key (SPKI), algorithm }
 *
 * `expected` is what we required before it was made:
 *   { challenge (base64url, as issued), origins: [...], rpId,
 *     requireUserVerification }
 *
 * Returns { ok: true, flags } or { ok: false, reason, detail }. Never throws
 * on bad input — every field here came off the wire and can be anything.
 */
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

  // A registration ceremony signs the same shape. Without this check an
  // assertion could be swapped for a creation and the difference would not
  // show up anywhere else.
  if (clientData.type !== 'webauthn.get') {
    return no('wrong-ceremony', `The client data says ${clientData.type}.`);
  }

  if (!sameString(clientData.challenge, expected.challenge)) {
    return no('challenge', 'That is not the challenge we issued.');
  }

  // The origin is the browser's word for which site asked, and the browser is
  // the one party here that cannot be talked out of telling the truth about
  // it. This is what stops a page on another domain from collecting
  // assertions and posting them to us.
  if (!expected.origins.includes(clientData.origin)) {
    return no('origin', `The ceremony happened at ${clientData.origin}.`);
  }

  // Set when the ceremony ran inside a cross-origin frame. Nothing we build
  // does that, so it means someone else framed us.
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
