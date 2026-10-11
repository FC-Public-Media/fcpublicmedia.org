// Presigned R2 upload grants, single PUT or multipart; the bytes never pass through the broker.
// Bucket CORS and lifecycle requirements: worker/README.md#writes-and-uploads.

import { presign } from './sigv4.js';

// S3 and R2 both refuse a part under 5 MiB, except the last one.
const MIN_PART = 5 * 1024 * 1024;

const DEFAULT_PART = 64 * 1024 * 1024;

// Under the 5 GiB single-PUT ceiling with room to spare.
const SINGLE_LIMIT = 4 * 1024 * 1024 * 1024;

// S3 allows 10,000; 1,000 keeps the response small and still covers 64 GB at the default part.
const MAX_PARTS = 1000;

/** <site>/<year>/<slug>-<random>.<ext>, the site taken from the challenge's repo. */
export function objectKey(repo, filename, now) {
  const site = repo.split('/')[1];
  const year = new Date(now).getUTCFullYear();

  const dot = filename.lastIndexOf('.');
  const stem = dot > 0 ? filename.slice(0, dot) : filename;
  const extension = dot > 0 ? filename.slice(dot + 1).toLowerCase().replace(/[^a-z0-9]/g, '') : '';

  const slug =
    stem
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'upload';

  const suffix = Array.from(crypto.getRandomValues(new Uint8Array(4)), (b) =>
    b.toString(16).padStart(2, '0')
  ).join('');

  return `${site}/${year}/${slug}-${suffix}${extension ? `.${extension}` : ''}`;
}

/** One PUT, or how many parts of what size. */
export function planUpload(size, { partSize = DEFAULT_PART } = {}) {
  if (size <= SINGLE_LIMIT) return { multipart: false, parts: 1, partSize: size };

  // Past the part cap, grow the part rather than the count.
  const chosen = Math.max(partSize, MIN_PART, Math.ceil(size / MAX_PARTS));
  return { multipart: true, parts: Math.ceil(size / chosen), partSize: chosen };
}

/** Sign everything the browser needs; multipart starts first, as uploadId is signed into each part. */
export async function grantUpload({
  key,
  size,
  bucket,
  endpoint,
  credentials,
  expires = 900,
  now = Date.now(),
  fetchImpl = fetch,
}) {
  const base = `${endpoint.replace(/\/+$/, '')}/${bucket}/${key.split('/').map(encodeURIComponent).join('/')}`;
  const sign = (method, url) => presign({ method, url, expires, now, ...credentials });

  const plan = planUpload(size);

  if (!plan.multipart) {
    return {
      ok: true,
      grant: { key, multipart: false, expires_in: expires, url: await sign('PUT', base) },
    };
  }

  let started;
  try {
    started = await fetchImpl(await sign('POST', `${base}?uploads=`), { method: 'POST' });
  } catch (error) {
    return { ok: false, detail: 'The storage service could not be reached.' };
  }
  if (!started.ok) {
    return { ok: false, detail: `The storage service returned ${started.status}.` };
  }

  // Workers have no XML parser; one element needs none.
  const uploadId = (await started.text()).match(/<UploadId>([^<]+)<\/UploadId>/)?.[1];
  if (!uploadId) {
    return { ok: false, detail: 'The storage service did not return an upload id.' };
  }

  const id = encodeURIComponent(uploadId);
  const parts = [];
  for (let number = 1; number <= plan.parts; number += 1) {
    // eslint-disable-next-line no-await-in-loop
    parts.push({ number, url: await sign('PUT', `${base}?partNumber=${number}&uploadId=${id}`) });
  }

  return {
    ok: true,
    grant: {
      key,
      multipart: true,
      expires_in: expires,
      upload_id: uploadId,
      part_size: plan.partSize,
      parts_expected: plan.parts,
      parts,
      complete: await sign('POST', `${base}?uploadId=${id}`),
      abort: await sign('DELETE', `${base}?uploadId=${id}`),
    },
  };
}
