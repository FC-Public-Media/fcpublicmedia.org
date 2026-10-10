# `worker/test/webauthn.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

The verification, checked against real signatures.

Half of these are about the signature encoding and half are about the things
a signature does not say. Both halves matter: a bug in the first makes
genuine members fail at random, and a bug in the second makes the whole
thing decorative.

## 2

Above `const raw = new Uint8Array(64);`

r is 1, which DER encodes in a single byte. Handed to WebCrypto unpadded
it would be read as the first byte of a 32-byte number and verify
against nothing. This is the failure that shows up in roughly one
signature in a hundred and thirty and gets blamed on the phone.

## 3

Above `const credential = await makeCredential();`

ECDSA picks a fresh nonce every time, so the encoded length of r and s
varies. One run proves nothing about the padding; fifty walks into the
short-scalar case often enough to matter.

## 4

Above `assertion.credential_id = credential.credentialId;`

The impostor claims to be the registered credential. Only the recorded
public key gets a say in whether that is true.
