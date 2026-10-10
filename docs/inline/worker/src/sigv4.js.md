# `worker/src/sigv4.js`

Moved out of the file. Unreviewed.

## 1

Above `const ALGORITHM = 'AWS4-HMAC-SHA256';`

Signing a URL somebody else will use.

R2 speaks the S3 API, and the S3 API's answer to "let this browser upload
six gigabytes without the bytes passing through us" is a presigned URL: a
normal PUT whose authority is carried in the query string, good for one
method, one object, and a few minutes.

The alternative is proxying, and it is worse in every direction. A Worker in
the data path pays for the bandwidth twice, holds the whole transfer open,
and turns a resumable upload into one long request that fails whole. This
signs a URL and gets out of the way.

SIGV4 IN ONE PARAGRAPH
----------------------
Build a canonical description of the request, hash it, wrap the hash in a
string that also names the day and the scope, and HMAC that with a key
derived from the secret by chaining HMACs over date, region, service and a
terminator. The chain is what makes a leaked signature useless tomorrow and
useless in another region.

Every step is exact. A query parameter sorted wrong, a path segment encoded
twice, a header with a stray space — each produces a signature that is
perfectly well-formed and rejected, with S3 replying only that it does not
match. That is why the test here is a known-answer test against the example
in AWS's own documentation rather than a round trip against ourselves: a
round trip proves this file agrees with itself, which is not in doubt.

## 2

Above `const UNSIGNED = 'UNSIGNED-PAYLOAD';`

The payload is not signed. It cannot be — nobody has hashed the six
gigabytes, and requiring it would mean reading the file twice before the
upload even starts. What the signature covers is the grant: this method,
this object, this window.

## 3

Above `const encode = (value) =>`

RFC 3986, which is not what encodeURIComponent does.

The difference is exactly four characters — ! ' ( ) * — which
encodeURIComponent leaves alone and S3 expects encoded. A filename with a
bracket in it would sign fine and be refused, and the error would say
nothing about brackets.

## 4

Above `const canonicalPath = (path) => path || '/';`

The path is used exactly as it already is, and NOT encoded again.

`new URL()` has already percent-encoded anything that needed it, so running
an encoder over the result turns %20 into %2520 — a signature over a path
nobody will ever request. S3's own rule is the same: for this service the
canonical URI is the encoded path as it stands, not the path encoded twice.

The safety here is structural rather than careful: the same string goes into
the canonical request and into the URL handed back, so the two cannot
disagree. Callers encode their own segments before building the URL —
r2.js does, and object keys are slugified down to [a-z0-9-] anyway.

## 5

Above `export async function presign({`

Presign one request.

`url` is the whole thing including any query the operation needs — the
multipart calls carry `?uploads`, `?partNumber=3&uploadId=…` and so on, and
those have to be inside the signature rather than appended afterwards.

Returns the URL with the six X-Amz-* parameters added. Anyone holding it can
make that exact request until it expires, which is the point.

## 6

Above `const signedHeaders = { host: target.host, ...headers };`

host is always signed. Anything else the caller names is signed too, and
has to be sent by whoever uses the URL or the signature will not match.

## 7

Above `let key = await hmac(AWS4${secretAccessKey}, short);`

The chain. Each step narrows what the resulting key can sign for, which is
why a signature cannot be replayed into another day or another region.
