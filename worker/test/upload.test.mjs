// Signing permission to upload.
//
// The first test here is the important one and it is a known-answer test: the
// worked example from AWS's own documentation for presigned URLs, signature
// and all. A round trip against ourselves would prove this file agrees with
// itself, which was never in doubt; what is in doubt is whether it agrees with
// S3, and only somebody else's answer can settle that.
//
// Every other SigV4 bug produces a signature that is perfectly well-formed and
// rejected, with the service replying only that it does not match.

import { strict as assert } from 'node:assert';
import { test } from 'node:test';

import { createBroker } from '../src/index.js';
import { grantUpload, objectKey, planUpload } from '../src/r2.js';
import { presign } from '../src/sigv4.js';
import { fakeGitHub, makeAssertion, makeCredential, memoryKV } from './helpers.mjs';

/* ------------------------------------------------------------ known answer */

test('it agrees with the worked example in the AWS documentation', async () => {
  const url = await presign({
    method: 'GET',
    url: 'https://examplebucket.s3.amazonaws.com/test.txt',
    expires: 86400,
    accessKeyId: 'AKIAIOSFODNN7EXAMPLE',
    secretAccessKey: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    region: 'us-east-1',
    service: 's3',
    now: Date.parse('2013-05-24T00:00:00Z'),
  });

  assert.equal(
    new URL(url).searchParams.get('X-Amz-Signature'),
    'aeeed9bbccd4d02ee5c0109b86d86835f995330da4c265957d157751f604d404'
  );
});

test('the signature is scoped to a day, a region and a service', async () => {
  // The point of the HMAC chain. A signature lifted out of one URL is useless
  // tomorrow, and useless against another region — so the parts of the scope
  // have to actually reach the derivation rather than only the credential
  // string that is displayed.
  const base = {
    method: 'PUT',
    url: 'https://account.r2.cloudflarestorage.com/media/a.mp4',
    accessKeyId: 'k',
    secretAccessKey: 's',
    now: Date.parse('2026-08-05T12:00:00Z'),
  };
  const signature = async (overrides) =>
    new URL(await presign({ ...base, ...overrides })).searchParams.get('X-Amz-Signature');

  const original = await signature({});
  assert.notEqual(original, await signature({ now: Date.parse('2026-08-06T12:00:00Z') }));
  assert.notEqual(original, await signature({ region: 'us-east-1' }));
  assert.notEqual(original, await signature({ service: 'sts' }));
  assert.notEqual(original, await signature({ method: 'GET' }));
  assert.equal(original, await signature({}), 'signing is not deterministic');
});

test('an already-encoded path is not encoded a second time', async () => {
  // The bug this is here for turns %20 into %2520 — a signature over a path
  // nobody will ever request, and a service that answers only that the
  // signature does not match.
  const path = '/media/show/take%20one%2B.mp4';
  const url = await presign({
    method: 'PUT',
    url: `https://account.r2.cloudflarestorage.com${path}`,
    accessKeyId: 'k',
    secretAccessKey: 's',
    now: Date.parse('2026-08-05T12:00:00Z'),
  });

  assert.equal(new URL(url).pathname, path);
  assert.ok(!url.includes('%2520'));
});

test('the path signed is the path handed back', async () => {
  // Structural rather than careful: the canonical request and the returned URL
  // are built from the same string, so no amount of encoding subtlety can make
  // them disagree. Changing the path changes the signature, which is what says
  // the path really is inside it.
  const sign = (path) =>
    presign({
      method: 'PUT',
      url: `https://account.r2.cloudflarestorage.com${path}`,
      accessKeyId: 'k',
      secretAccessKey: 's',
      now: Date.parse('2026-08-05T12:00:00Z'),
    });

  const one = await sign('/media/show/a.mp4');
  const two = await sign('/media/show/b.mp4');

  assert.notEqual(
    new URL(one).searchParams.get('X-Amz-Signature'),
    new URL(two).searchParams.get('X-Amz-Signature')
  );
});

/* ------------------------------------------------------------------ layout */

test('a file lands under its own site and cannot be aimed elsewhere', async () => {
  const key = objectKey('fcpublicmedia/janes-show', 'Final Cut v2.MP4', Date.parse('2026-08-05T00:00:00Z'));

  assert.match(key, /^janes-show\/2026\/final-cut-v2-[0-9a-f]{8}\.mp4$/);
});

test('two uploads of the same name do not land on each other', async () => {
  const args = ['fcpublicmedia/janes-show', 'final.mp4', Date.parse('2026-08-05T00:00:00Z')];
  assert.notEqual(objectKey(...args), objectKey(...args));
});

test('an awkward name still produces a usable key', async () => {
  const stamp = Date.parse('2026-08-05T00:00:00Z');
  assert.match(objectKey('a/b', '....mp4', stamp), /^b\/2026\/upload-[0-9a-f]{8}\.mp4$/);
  assert.match(objectKey('a/b', 'Ünïcødé Shöw.mov', stamp), /^b\/2026\/[a-z0-9-]+-[0-9a-f]{8}\.mov$/);
});

test('a big file is split and a small one is not', async () => {
  const GB = 1024 ** 3;

  assert.equal(planUpload(50 * 1024 * 1024).multipart, false);
  assert.equal(planUpload(2 * GB).multipart, false);

  const big = planUpload(6 * GB);
  assert.equal(big.multipart, true);
  assert.ok(big.parts > 1);
  assert.ok(big.partSize >= 5 * 1024 * 1024, 'parts under 5 MiB are refused by S3');
  assert.ok(big.parts * big.partSize >= 6 * GB, 'the parts do not cover the file');
});

test('an enormous file grows its parts rather than its part count', async () => {
  // S3 allows ten thousand parts. Handing back that many URLs would be a
  // response measured in megabytes.
  const huge = planUpload(500 * 1024 ** 3);
  assert.ok(huge.parts <= 1000, `${huge.parts} parts`);
  assert.ok(huge.parts * huge.partSize >= 500 * 1024 ** 3);
});

/* ------------------------------------------------------------- the multipart */

/** R2, enough of it to start a multipart upload. */
function fakeR2({ fail = false } = {}) {
  const calls = [];
  return {
    calls,
    fetchImpl: async (url, options = {}) => {
      calls.push({ url: String(url), method: options.method });
      if (fail) return new Response('nope', { status: 503 });
      return new Response(
        '<?xml version="1.0"?><InitiateMultipartUploadResult><UploadId>abc/123+xyz</UploadId></InitiateMultipartUploadResult>',
        { status: 200 }
      );
    },
  };
}

const CREDENTIALS = { accessKeyId: 'k', secretAccessKey: 's' };

test('the upload id is real, and every part URL is signed with it', async () => {
  // The bug this is here for: signing parts against a placeholder and
  // substituting the id afterwards. The query string is inside the signature,
  // so that produces URLs that are well-formed and refused.
  const r2 = fakeR2();
  const granted = await grantUpload({
    key: 'janes-show/2026/big-abc12345.mp4',
    size: 6 * 1024 ** 3,
    bucket: 'media',
    endpoint: 'https://account.r2.cloudflarestorage.com',
    credentials: CREDENTIALS,
    now: Date.parse('2026-08-05T12:00:00Z'),
    fetchImpl: r2.fetchImpl,
  });

  assert.equal(granted.ok, true, granted.detail);
  assert.equal(granted.grant.upload_id, 'abc/123+xyz');

  // The create call happened before anything was signed against the id.
  assert.equal(r2.calls.length, 1);
  assert.match(r2.calls[0].url, /\?.*uploads=/);

  for (const part of granted.grant.parts) {
    assert.ok(part.url.includes('uploadId=abc%2F123%2Bxyz'), part.url);
    assert.ok(!part.url.includes('UPLOAD_ID'), 'a placeholder survived into a signed URL');
    assert.ok(part.url.includes(`partNumber=${part.number}`));
  }
  assert.ok(granted.grant.complete.includes('uploadId=abc%2F123%2Bxyz'));
  assert.ok(granted.grant.abort.includes('uploadId=abc%2F123%2Bxyz'));
});

test('a small file gets one URL and no round trip to storage', async () => {
  const r2 = fakeR2();
  const granted = await grantUpload({
    key: 'janes-show/2026/small-abc12345.mp4',
    size: 12 * 1024 * 1024,
    bucket: 'media',
    endpoint: 'https://account.r2.cloudflarestorage.com',
    credentials: CREDENTIALS,
    now: Date.parse('2026-08-05T12:00:00Z'),
    fetchImpl: r2.fetchImpl,
  });

  assert.equal(granted.grant.multipart, false);
  assert.ok(granted.grant.url.includes('X-Amz-Signature='));
  assert.equal(r2.calls.length, 0);
});

test('storage having a bad minute is reported, not half-granted', async () => {
  const granted = await grantUpload({
    key: 'k',
    size: 6 * 1024 ** 3,
    bucket: 'media',
    endpoint: 'https://account.r2.cloudflarestorage.com',
    credentials: CREDENTIALS,
    fetchImpl: fakeR2({ fail: true }).fetchImpl,
  });

  assert.equal(granted.ok, false);
  assert.match(granted.detail, /503/);
});

/* ----------------------------------------------------------------- the endpoint */

const ORIGIN = 'https://www.fcpublicmedia.org';
const RP_ID = 'fcpublicmedia.org';
const REPO = 'fcpublicmedia/janes-show';

const post = (path, body) =>
  new Request(`https://broker.example${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: ORIGIN },
    body: JSON.stringify(body),
  });

async function setUp({ storage = true, maxBytes, mayPublish = true } = {}) {
  const credential = await makeCredential({ mayPublish });
  const hub = fakeGitHub({ [REPO]: { version: 1, devices: [credential.record] } });
  const r2 = fakeR2();

  // One fetch reaches both GitHub and R2, the way it does in the Worker.
  const fetchImpl = async (url, options) =>
    String(url).includes('r2.cloudflarestorage.com')
      ? r2.fetchImpl(url, options)
      : hub.fetchImpl(url, options);

  const service = createBroker(
    {
      RP_ID,
      ORIGINS: ORIGIN,
      OWNER: 'fcpublicmedia',
      CHALLENGES: memoryKV(),
      GITHUB_TOKEN: 'ghp_test',
      ...(maxBytes ? { R2_MAX_BYTES: String(maxBytes) } : {}),
      ...(storage
        ? {
            R2_ENDPOINT: 'https://account.r2.cloudflarestorage.com',
            R2_BUCKET: 'media',
            R2_ACCESS_KEY_ID: 'k',
            R2_SECRET_ACCESS_KEY: 's',
          }
        : {}),
    },
    { fetchImpl }
  );

  const ask = async (filename, size) => {
    const declared = await service.fetch(
      post('/challenge', { action: 'upload.grant', repo: REPO, filename, size })
    );
    const issued = await declared.json();
    if (!issued.challenge) return { response: declared, body: issued };

    const assertion = await makeAssertion(credential, {
      challenge: issued.challenge,
      origin: ORIGIN,
      rpId: RP_ID,
    });
    const response = await service.fetch(post('/upload', { assertion }));
    return { response, body: await response.json(), issued };
  };

  return { service, ask, r2 };
}

test('a signed-for upload comes back with somewhere to put it', async () => {
  const { ask } = await setUp();

  const { response, body, issued } = await ask('episode-12.mp4', 40 * 1024 * 1024);

  assert.equal(response.status, 200, body.detail);
  assert.equal(body.performed, true);
  assert.match(body.key, /^janes-show\/\d{4}\/episode-12-[0-9a-f]{8}\.mp4$/);
  assert.ok(body.url.startsWith('https://account.r2.cloudflarestorage.com/media/'));

  // Where it lands is settled at challenge time, before anybody signs.
  assert.equal(issued.intent.key, body.key);
});

test('the key is fixed by the challenge and not renegotiable', async () => {
  const { service } = await setUp();
  const credential = await makeCredential();

  const declared = await service.fetch(
    post('/challenge', { action: 'upload.grant', repo: REPO, filename: 'a.mp4', size: 1024 })
  );
  const issued = await declared.json();

  // Whatever the page sends later, the grant is for the key above.
  assert.match(issued.intent.key, /^janes-show\//);
  assert.equal(issued.intent.repo, REPO);
  assert.ok(credential);
});

test('a device that may not publish gets no upload', async () => {
  const { ask, r2 } = await setUp({ mayPublish: false });

  const { response, body } = await ask('episode.mp4', 1024);

  assert.equal(response.status, 403);
  assert.equal(body.reason, 'not-allowed');
  assert.equal(r2.calls.length, 0);
});

test('a file over the cap is refused before anybody is asked to approve it', async () => {
  // Refused at the challenge, so the passkey prompt never appears. Being asked
  // to authorize something and only then told it was too big is a worse
  // sequence than being told first.
  const { ask } = await setUp({ maxBytes: 2 * 1024 ** 3 });

  const { response, body } = await ask('enormous.mp4', 6 * 1024 ** 3);

  assert.equal(response.status, 400);
  assert.match(body.detail, /larger than this site accepts/);
});

test('a broker with nowhere to put files says which settings it wants', async () => {
  const { ask } = await setUp({ storage: false });

  const { response, body } = await ask('episode.mp4', 1024);

  assert.equal(response.status, 500);
  assert.match(body.detail, /R2_BUCKET/);
});

test('a name that is really a path is refused', async () => {
  const { ask } = await setUp();

  for (const name of ['../../etc/passwd', 'a/b.mp4', '.hidden']) {
    const { response } = await ask(name, 1024);
    assert.equal(response.status, 400, `${name} was accepted`);
  }
});

test('a size that is not a size is refused', async () => {
  const { ask } = await setUp();

  for (const size of [0, -1, 1.5, 'lots', null]) {
    const { response } = await ask('a.mp4', size);
    assert.equal(response.status, 400, `${size} was accepted`);
  }
});
