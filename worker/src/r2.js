// Handing out permission to upload, without touching the bytes.
//
// A finished episode is measured in gigabytes. The broker never sees any of
// it: it signs URLs, the browser sends the file straight to R2, and the only
// thing that crosses this Worker is a few hundred bytes of JSON.
//
// WHAT THE SIGNATURE BINDS TO HERE, AND WHY IT IS DIFFERENT
// ---------------------------------------------------------
// /write binds a signature to a hash of the exact content. This cannot, and
// the reason is worth stating rather than glossing: hashing six gigabytes in a
// browser means reading the whole file before the upload starts, roughly
// doubling the time on a slow laptop, to protect bytes the broker never sees
// anyway.
//
// So an upload signature binds to the GRANT — this member, this site, this
// object key, this size, for the next fifteen minutes — and not to the
// content. What that costs is precise: somebody holding the URL can put
// different bytes at that key. Somebody holding the URL is the member whose
// device just signed for it. The exposure is a member overwriting their own
// pending upload, which is not a threat, it is a retry.
//
// MULTIPART, BECAUSE ONE PUT IS NOT ENOUGH
// ----------------------------------------
// A single PUT tops out at 5 GiB, which is under what a finished episode can
// be. Above the threshold the upload is split, every part is presigned up
// front, and the browser does create → parts → complete on its own. The broker
// signs and steps out; it is not a proxy at any size.
//
// Two things about that the bucket has to be configured for, because they are
// not code:
//
//   * CORS on the bucket must allow PUT and POST from our origins, and must
//     expose the ETag header — the browser has to read each part's ETag to
//     complete the upload, and a cross-origin response hides it otherwise.
//   * A lifecycle rule to abort incomplete multipart uploads. A member who
//     closes the tab halfway leaves parts behind, and parts are billed.

import { presign } from './sigv4.js';

// S3 and R2 both refuse a part under 5 MiB, except the last one.
const MIN_PART = 5 * 1024 * 1024;

// What a part is by default. Big enough that a long upload is not thousands of
// requests, small enough that losing one is not a disaster on a bad line.
const DEFAULT_PART = 64 * 1024 * 1024;

// Above this, split it. Comfortably under the 5 GiB single-PUT ceiling, so the
// boundary is never the thing that fails.
const SINGLE_LIMIT = 4 * 1024 * 1024 * 1024;

// S3 allows ten thousand parts. A thousand keeps the response a sensible size
// while still covering a 64 GB file at the default part size.
const MAX_PARTS = 1000;

/**
 * Where a file goes.
 *
 * Prefixed with the repository the CHALLENGE named, so one member cannot write
 * into another's space — the prefix is not something the page gets to choose.
 * The random suffix is there so two uploads of "final.mp4" in the same year do
 * not land on each other.
 */
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

  // Grow the part rather than the count when a file is big enough that the
  // default would blow past the cap.
  const chosen = Math.max(partSize, MIN_PART, Math.ceil(size / MAX_PARTS));
  return { multipart: true, parts: Math.ceil(size / chosen), partSize: chosen };
}

/**
 * Sign everything the browser will need, in one go.
 *
 * THE UPLOAD ID HAS TO EXIST BEFORE THE PARTS CAN BE SIGNED
 * ---------------------------------------------------------
 * A part URL carries `uploadId=…` in its query string, and the query string is
 * inside the signature. So there is no signing parts against a placeholder and
 * substituting the real id later — that produces a URL whose signature does
 * not match, and R2 will say only that it does not match.
 *
 * The broker therefore starts the multipart upload itself, here, before
 * signing anything else. It does that by presigning the create call and then
 * fetching that URL — a presigned URL works for whoever holds it, including
 * us, which means this file needs exactly one way of signing rather than two.
 * One round trip to R2 inside this request, and then the browser has
 * everything and never comes back.
 *
 * Resolves to { ok: true, grant } or { ok: false, detail }.
 */
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

  // One well-known element out of a small XML document. Workers have no XML
  // parser, and adding one to read a single field would be a dependency for
  // something a regular expression answers exactly.
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
      // Signed and handed over so a member who closes the tab can be tidied up
      // after. The bucket needs a lifecycle rule for the ones who just vanish,
      // because abandoned parts are billed.
      abort: await sign('DELETE', `${base}?uploadId=${id}`),
    },
  };
}
