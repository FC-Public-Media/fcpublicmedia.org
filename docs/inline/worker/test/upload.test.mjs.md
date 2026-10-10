# `worker/test/upload.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

Signing permission to upload.

The first test here is the important one and it is a known-answer test: the
worked example from AWS's own documentation for presigned URLs, signature
and all. A round trip against ourselves would prove this file agrees with
itself, which was never in doubt; what is in doubt is whether it agrees with
S3, and only somebody else's answer can settle that.

Every other SigV4 bug produces a signature that is perfectly well-formed and
rejected, with the service replying only that it does not match.

## 2

Above `const base = {`

The point of the HMAC chain. A signature lifted out of one URL is useless
tomorrow, and useless against another region — so the parts of the scope
have to actually reach the derivation rather than only the credential
string that is displayed.

## 3

Above `const path = '/media/show/take%20one%2B.mp4';`

The bug this is here for turns %20 into %2520 — a signature over a path
nobody will ever request, and a service that answers only that the
signature does not match.

## 4

Above `const sign = (path) =>`

Structural rather than careful: the canonical request and the returned URL
are built from the same string, so no amount of encoding subtlety can make
them disagree. Changing the path changes the signature, which is what says
the path really is inside it.

## 5

Above `const huge = planUpload(500 * 1024 ** 3);`

S3 allows ten thousand parts. Handing back that many URLs would be a
response measured in megabytes.

## 6

Above `const r2 = fakeR2();`

The bug this is here for: signing parts against a placeholder and
substituting the id afterwards. The query string is inside the signature,
so that produces URLs that are well-formed and refused.

## 7

Above `const { ask } = await setUp({ maxBytes: 2 * 1024 ** 3 });`

Refused at the challenge, so the passkey prompt never appears. Being asked
to authorize something and only then told it was too big is a worse
sequence than being told first.
