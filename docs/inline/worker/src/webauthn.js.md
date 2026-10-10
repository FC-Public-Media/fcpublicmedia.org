# `worker/src/webauthn.js`

Moved out of the file. Unreviewed.

## 1

Above `/* --------------------------------------------------------------------- bytes */`

Checking a WebAuthn assertion.

This is the only file in the broker that decides whether a signature is
genuine, and it is written so it can run anywhere with WebCrypto — no
Workers APIs, no bindings, no network. That is deliberate: the tests drive
it under plain Node with a real key and a real signature, which is the only
way to find out whether the parsing below is right.

WHAT AN ASSERTION ACTUALLY PROVES
---------------------------------
The authenticator signs exactly two things joined together:

    authenticatorData || SHA-256(clientDataJSON)

Everything else the browser hands back — the credential ID, the user handle
— travels ALONGSIDE the signature and is not covered by it. So none of it
can be believed on its own. What makes this safe is that the credential ID
is used to look up a public key that was recorded earlier, and the signature
then has to verify under that key. A lie about the credential ID produces a
lookup that fails or a key that does not verify. It is never trusted.

The challenge is inside clientDataJSON, so it IS covered. That is what makes
a captured assertion useless the second time: the challenge was issued by us,
once, for one thing.

THE PART MOST LIKELY TO BE QUIETLY WRONG
----------------------------------------
WebAuthn's ES256 signatures are DER-encoded — a SEQUENCE of two INTEGERs.
WebCrypto's verify() wants the raw 64 bytes, r followed by s, each padded to
exactly 32. Converting between them means stripping the leading zero DER
adds to keep an integer positive, and re-padding short values back out. Get
it slightly wrong and roughly one signature in every hundred and thirty
fails while the rest pass, which reads as "flaky authenticator" for months.

site/bin/mint-claim.py has the same seam in the other direction.

## 2

Above `export function derToRawSignature(der, size = P256_SCALAR) {`

DER SEQUENCE(INTEGER r, INTEGER s) into the raw r||s WebCrypto wants.

Throws rather than returning something plausible. A signature that will not
parse is not a signature, and treating it as one that merely fails to verify
would hide a real bug behind a routine-looking rejection.

## 3

Above `const length = byte();`

Short form only. A P-256 signature is around seventy bytes, so a length
needing the long form means this is not what it claims to be.

## 4

Above `while (value.length > 1 && value[0] === 0) value = value.subarray(1);`

DER prefixes a zero byte when the top bit is set, so the integer stays
positive. That byte is encoding, not value.

## 5

Above `const padded = new Uint8Array(size);`

And a scalar that happened to be small is short. Left-pad it back out;
WebCrypto wants a fixed width, not the minimal encoding.

## 6

Above `function normalizeEcdsaSignature(signature) {`

Some authenticators hand back the raw form already, in spite of the spec.

A raw P-256 signature is exactly 64 bytes; DER encoding two full-width
scalars takes 70. DER only gets down to 64 if six bytes of leading zeros
turn up across r and s together, which is a one-in-2^48 accident, so
treating a 64-byte signature as raw is safe in the way that matters: it can
make a valid signature fail, never an invalid one pass.

## 7

Above `async function importPublicKey(spki, algorithm) {`

Load a recorded public key.

The algorithm is stored with the device — getPublicKeyAlgorithm() gives it
to us at registration — but records written before that was captured may not
have it, so an absent value means try the two we ask for, in the order we
ask for them.

## 8

Above `export async function verifyAssertion({ assertion, device, expected }) {`

Verify one assertion against one recorded device.

`assertion` carries the base64url values the browser produced:
  { credential_id, authenticator_data, client_data_json, signature }

`device` is the record from .auth/devices.json:
  { credential_id, public_key (SPKI), algorithm }

`expected` is what we required before it was made:
  { challenge (base64url, as issued), origins: [...], rpId,
    requireUserVerification }

Returns { ok: true, flags } or { ok: false, reason, detail }. Never throws
on bad input — every field here came off the wire and can be anything.

## 9

Above `if (clientData.type !== 'webauthn.get') {`

A registration ceremony signs the same shape. Without this check an
assertion could be swapped for a creation and the difference would not
show up anywhere else.

## 10

Above `if (!expected.origins.includes(clientData.origin)) {`

The origin is the browser's word for which site asked, and the browser is
the one party here that cannot be talked out of telling the truth about
it. This is what stops a page on another domain from collecting
assertions and posting them to us.

## 11

Above `if (clientData.crossOrigin === true) {`

Set when the ceremony ran inside a cross-origin frame. Nothing we build
does that, so it means someone else framed us.
