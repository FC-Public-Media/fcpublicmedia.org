// AWS SigV4 presigned URLs for R2's S3 API. Tested against AWS's own worked example.

const ALGORITHM = 'AWS4-HMAC-SHA256';

// The payload is never hashed; the signature covers method, object and window.
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

/** RFC 3986: encodeURIComponent plus ! ' ( ) *, which S3 expects encoded. */
const encode = (value) =>
  encodeURIComponent(value).replace(
    /[!'()*]/g,
    (c) => `%${c.charCodeAt(0).toString(16).toUpperCase()}`
  );

/** new URL() already encoded the path; encoding again turns %20 into %2520. Callers encode segments. */
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

/** Presign one request; the operation query in `url` (?uploads, ?partNumber=…) is signed too. */
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

  // host is always signed; any other header named here must be sent by whoever uses the URL.
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

  // Key derivation over date, region, service: no replay into another day or region.
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
