// Signing a URL somebody else will use.
//
// R2 speaks the S3 API, and the S3 API's answer to "let this browser upload
// six gigabytes without the bytes passing through us" is a presigned URL: a
// normal PUT whose authority is carried in the query string, good for one
// method, one object, and a few minutes.
//
// The alternative is proxying, and it is worse in every direction. A Worker in
// the data path pays for the bandwidth twice, holds the whole transfer open,
// and turns a resumable upload into one long request that fails whole. This
// signs a URL and gets out of the way.
//
// SIGV4 IN ONE PARAGRAPH
// ----------------------
// Build a canonical description of the request, hash it, wrap the hash in a
// string that also names the day and the scope, and HMAC that with a key
// derived from the secret by chaining HMACs over date, region, service and a
// terminator. The chain is what makes a leaked signature useless tomorrow and
// useless in another region.
//
// Every step is exact. A query parameter sorted wrong, a path segment encoded
// twice, a header with a stray space — each produces a signature that is
// perfectly well-formed and rejected, with S3 replying only that it does not
// match. That is why the test here is a known-answer test against the example
// in AWS's own documentation rather than a round trip against ourselves: a
// round trip proves this file agrees with itself, which is not in doubt.

const ALGORITHM = 'AWS4-HMAC-SHA256';

// The payload is not signed. It cannot be — nobody has hashed the six
// gigabytes, and requiring it would mean reading the file twice before the
// upload even starts. What the signature covers is the grant: this method,
// this object, this window.
const UNSIGNED = 'UNSIGNED-PAYLOAD';

const utf8 = (text) => new TextEncoder().encode(text);

const hex = (bytes) =>
  Array.from(new Uint8Array(bytes), (byte) => byte.toString(16).padStart(2, '0')).join('');

const sha256 = async (input) =>
  hex(await crypto.subtle.digest('SHA-256', typeof input === 'string' ? utf8(input) : input));

async function hmac(key, message) {
  const imported = await crypto.subtle.importKey(
    'raw',
    typeof key === 'string' ? utf8(key) : key,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  return new Uint8Array(await crypto.subtle.sign('HMAC', imported, utf8(message)));
}

/**
 * RFC 3986, which is not what encodeURIComponent does.
 *
 * The difference is exactly four characters — ! ' ( ) * — which
 * encodeURIComponent leaves alone and S3 expects encoded. A filename with a
 * bracket in it would sign fine and be refused, and the error would say
 * nothing about brackets.
 */
const encode = (value) =>
  encodeURIComponent(value).replace(
    /[!'()*]/g,
    (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`
  );

/**
 * The path is used exactly as it already is, and NOT encoded again.
 *
 * `new URL()` has already percent-encoded anything that needed it, so running
 * an encoder over the result turns %20 into %2520 — a signature over a path
 * nobody will ever request. S3's own rule is the same: for this service the
 * canonical URI is the encoded path as it stands, not the path encoded twice.
 *
 * The safety here is structural rather than careful: the same string goes into
 * the canonical request and into the URL handed back, so the two cannot
 * disagree. Callers encode their own segments before building the URL —
 * r2.js does, and object keys are slugified down to [a-z0-9-] anyway.
 */
const canonicalPath = (path) => path || '/';

/** Sorted by encoded key, then by encoded value. */
function canonicalQuery(params) {
  return Object.entries(params)
    .map(([key, value]) => [encode(key), encode(value)])
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0))
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
}

/** 20130524T000000Z, and the 20130524 the scope wants. */
function stamp(now) {
  const iso = new Date(now).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  return { long: iso, short: iso.slice(0, 8) };
}

/**
 * Presign one request.
 *
 * `url` is the whole thing including any query the operation needs — the
 * multipart calls carry `?uploads`, `?partNumber=3&uploadId=…` and so on, and
 * those have to be inside the signature rather than appended afterwards.
 *
 * Returns the URL with the six X-Amz-* parameters added. Anyone holding it can
 * make that exact request until it expires, which is the point.
 */
export async function presign({
  method,
  url,
  expires = 900,
  accessKeyId,
  secretAccessKey,
  region = 'auto',
  service = 's3',
  now = Date.now(),
  headers = {},
}) {
  const target = new URL(url);
  const { long, short } = stamp(now);
  const scope = `${short}/${region}/${service}/aws4_request`;

  // host is always signed. Anything else the caller names is signed too, and
  // has to be sent by whoever uses the URL or the signature will not match.
  const signedHeaders = { host: target.host, ...headers };
  const headerNames = Object.keys(signedHeaders)
    .map((name) => name.toLowerCase())
    .sort();
  const canonicalHeaders = headerNames
    .map((name) => `${name}:${String(signedHeaders[name] ?? signedHeaders[name.toLowerCase()]).trim()}\n`)
    .join('');

  const query = {};
  for (const [key, value] of target.searchParams) query[key] = value;
  Object.assign(query, {
    'X-Amz-Algorithm': ALGORITHM,
    'X-Amz-Credential': `${accessKeyId}/${scope}`,
    'X-Amz-Date': long,
    'X-Amz-Expires': String(expires),
    'X-Amz-SignedHeaders': headerNames.join(';'),
  });

  const canonicalRequest = [
    method,
    canonicalPath(target.pathname),
    canonicalQuery(query),
    canonicalHeaders,
    headerNames.join(';'),
    UNSIGNED,
  ].join('\n');

  const stringToSign = [ALGORITHM, long, scope, await sha256(canonicalRequest)].join('\n');

  // The chain. Each step narrows what the resulting key can sign for, which is
  // why a signature cannot be replayed into another day or another region.
  let key = await hmac(`AWS4${secretAccessKey}`, short);
  key = await hmac(key, region);
  key = await hmac(key, service);
  key = await hmac(key, 'aws4_request');

  const imported = await crypto.subtle.importKey(
    'raw',
    key,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const signature = hex(await crypto.subtle.sign('HMAC', imported, utf8(stringToSign)));

  return `${target.origin}${canonicalPath(target.pathname)}?${canonicalQuery(query)}&X-Amz-Signature=${signature}`;
}
