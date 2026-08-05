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

/** raw.githubusercontent, holding whatever the test says each repo holds. */
export function fakeRaw(byRepo) {
  return async (url) => {
    const match = String(url).match(
      /^https:\/\/raw\.githubusercontent\.com\/([^/]+\/[^/]+)\/HEAD\/(.+)$/
    );
    const body = match && byRepo[match[1]];
    if (body === undefined) return new Response('Not Found', { status: 404 });
    if (body === null) return new Response('Server Error', { status: 500 });
    return new Response(typeof body === 'string' ? body : JSON.stringify(body), { status: 200 });
  };
}
