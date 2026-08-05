// The verification, checked against real signatures.
//
// Half of these are about the signature encoding and half are about the things
// a signature does not say. Both halves matter: a bug in the first makes
// genuine members fail at random, and a bug in the second makes the whole
// thing decorative.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { derToRawSignature, verifyAssertion } from '../src/webauthn.js';
import {
  FLAG_USER_PRESENT,
  b64u,
  makeAssertion,
  makeCredential,
  rawToDer,
} from './helpers.mjs';

const RP_ID = 'fcpublicmedia.org';
const ORIGIN = 'https://www.fcpublicmedia.org';
const CHALLENGE = b64u(crypto.getRandomValues(new Uint8Array(32)));

const expected = (overrides = {}) => ({
  challenge: CHALLENGE,
  origins: [ORIGIN],
  rpId: RP_ID,
  requireUserVerification: false,
  ...overrides,
});

const check = (assertion, credential, overrides) =>
  verifyAssertion({ assertion, device: credential.record, expected: expected(overrides) });

/* ------------------------------------------------------------- the encoding */

test('DER round-trips back to the raw form it came from', () => {
  for (let i = 0; i < 200; i += 1) {
    const raw = crypto.getRandomValues(new Uint8Array(64));
    assert.deepEqual(derToRawSignature(rawToDer(raw)), raw);
  }
});

test('a scalar with the top bit set survives the padding byte DER adds', () => {
  const raw = new Uint8Array(64).fill(0x11);
  raw[0] = 0xff; // r reads as negative, so DER prefixes a zero
  raw[32] = 0xff; // and so does s
  assert.deepEqual(derToRawSignature(rawToDer(raw)), raw);
});

test('a short scalar is padded back out to its full width', () => {
  // r is 1, which DER encodes in a single byte. Handed to WebCrypto unpadded
  // it would be read as the first byte of a 32-byte number and verify
  // against nothing. This is the failure that shows up in roughly one
  // signature in a hundred and thirty and gets blamed on the phone.
  const raw = new Uint8Array(64);
  raw[31] = 1;
  raw.set(crypto.getRandomValues(new Uint8Array(32)), 32);

  const der = rawToDer(raw);
  assert.equal(der[3], 1, 'the test fixture should encode r in one byte');
  assert.deepEqual(derToRawSignature(der), raw);
});

test('a mangled signature is rejected rather than silently interpreted', () => {
  const der = rawToDer(crypto.getRandomValues(new Uint8Array(64)));

  assert.throws(() => derToRawSignature(Uint8Array.from([0x31, ...der.subarray(1)])), /sequence/);
  assert.throws(() => derToRawSignature(Uint8Array.from([...der, 0x00])), /length/);
  assert.throws(() => derToRawSignature(der.subarray(0, 8)), /length/);
  assert.throws(() => derToRawSignature(new Uint8Array(0)), /ended early/);
});

/* --------------------------------------------------------------- the happy path */

test('a genuine assertion verifies', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
  });

  const result = await check(assertion, credential);
  assert.equal(result.ok, true, result.detail);
  assert.equal(result.flags.userVerified, true);
});

test('fifty signatures in a row all verify', async () => {
  // ECDSA picks a fresh nonce every time, so the encoded length of r and s
  // varies. One run proves nothing about the padding; fifty walks into the
  // short-scalar case often enough to matter.
  const credential = await makeCredential();

  for (let i = 0; i < 50; i += 1) {
    const assertion = await makeAssertion(credential, {
      challenge: CHALLENGE,
      origin: ORIGIN,
      rpId: RP_ID,
      counter: i,
    });
    const result = await check(assertion, credential);
    assert.equal(result.ok, true, `signature ${i}: ${result.reason} ${result.detail}`);
  }
});

test('an authenticator that skips DER and sends the raw form still works', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
    rawSignature: true,
  });

  assert.equal((await check(assertion, credential)).ok, true);
});

/* ------------------------------------------------------------- the rejections */

test('a signature from another key does not verify', async () => {
  const credential = await makeCredential();
  const impostor = await makeCredential();

  const assertion = await makeAssertion(impostor, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
  });
  // The impostor claims to be the registered credential. Only the recorded
  // public key gets a say in whether that is true.
  assertion.credential_id = credential.credentialId;

  const result = await check(assertion, credential);
  assert.equal(result.ok, false);
  assert.equal(result.reason, 'signature');
});

test('one flipped bit in the authenticator data is enough', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
  });

  // The sign counter, which is inside the signed bytes and nowhere else.
  const bytes = Uint8Array.from(atob(assertion.authenticator_data.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0));
  bytes[36] ^= 0x01;
  assertion.authenticator_data = b64u(bytes);

  assert.equal((await check(assertion, credential)).reason, 'signature');
});

test('an assertion for a different challenge is refused', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: b64u(crypto.getRandomValues(new Uint8Array(32))),
    origin: ORIGIN,
    rpId: RP_ID,
  });

  assert.equal((await check(assertion, credential)).reason, 'challenge');
});

test('a ceremony that happened on another site is refused', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: 'https://fcpublicmedia.org.example.net',
    rpId: RP_ID,
  });

  const result = await check(assertion, credential);
  assert.equal(result.reason, 'origin');
});

test('a passkey for another domain is refused', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: 'example.net',
  });

  assert.equal((await check(assertion, credential)).reason, 'rp-id');
});

test('a registration cannot stand in for a sign-in', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
    type: 'webauthn.create',
  });

  assert.equal((await check(assertion, credential)).reason, 'wrong-ceremony');
});

test('a ceremony inside somebody else’s frame is refused', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
    crossOrigin: true,
  });

  assert.equal((await check(assertion, credential)).reason, 'cross-origin');
});

test('nobody at the device is refused', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
    flags: 0x00,
  });

  assert.equal((await check(assertion, credential)).reason, 'user-present');
});

test('user verification is required only when it was asked for', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
    flags: FLAG_USER_PRESENT, // present, but not verified
  });

  assert.equal((await check(assertion, credential)).ok, true);
  assert.equal(
    (await check(assertion, credential, { requireUserVerification: true })).reason,
    'user-verification'
  );
  assert.equal((await check(assertion, credential)).flags.userVerified, false);
});

test('truncated authenticator data is malformed, not merely unverifiable', async () => {
  const credential = await makeCredential();
  const assertion = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
  });
  assertion.authenticator_data = b64u(new Uint8Array(20));

  assert.equal((await check(assertion, credential)).reason, 'malformed');
});

test('rubbish in any field is refused without throwing', async () => {
  const credential = await makeCredential();
  const good = await makeAssertion(credential, {
    challenge: CHALLENGE,
    origin: ORIGIN,
    rpId: RP_ID,
  });

  for (const field of ['authenticator_data', 'client_data_json', 'signature']) {
    const result = await check({ ...good, [field]: 'not base64url at all !!!' }, credential);
    assert.equal(result.ok, false, `${field} was accepted`);
  }

  const noKey = await verifyAssertion({
    assertion: good,
    device: { ...credential.record, public_key: b64u(new Uint8Array(8)) },
    expected: expected(),
  });
  assert.equal(noKey.reason, 'public-key');
});
