// Writing to a member's repository.
//
// The credential comes from app-auth.js, one repository at a time, and this
// file never sees where it came from. That is the point of the seam: the
// question "what is allowed to write here" is answered in one place, by an App
// installation, and not by whatever each call site happens to pass.
//
// WHY THE DEFAULT IS A BRANCH AND NOT THE MAIN LINE
// -------------------------------------------------
// A member editing their settings file can produce YAML that does not parse.
// Committed straight to the default branch that takes their site down until
// somebody notices. On a branch, the repository's own checks run first and the
// merge only happens if it builds — so the worst case is an open pull request
// and a message, instead of a broken site and a phone call.
//
// _data/settings.yml has the same argument written for the person reading it.

import { contentHash as hashOf } from './intent.js';

const API = 'https://api.github.com';

/** Base64 for the Contents API, going through UTF-8 rather than charCodes. */
function toBase64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

/** The API wraps its base64 at sixty columns, so the whitespace has to go. */
function fromBase64(value) {
  const binary = atob(String(value).replace(/\s/g, ''));
  return new TextDecoder().decode(Uint8Array.from(binary, (c) => c.charCodeAt(0)));
}

/** A short, stable branch name. The same edit retried lands on the same one. */
const branchFor = (hash) => `settings/${hash.replace(/[^A-Za-z0-9]/g, '').slice(0, 12)}`;

export function github({ credential, fetchImpl = fetch, api = API }) {
  async function callWith(token, path, { method = 'GET', body } = {}) {
    const response = await fetchImpl(`${api}${path}`, {
      method,
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28',
        // GitHub rejects requests without one.
        'User-Agent': 'fcpm-broker',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });

    const payload = await response.json().catch(() => ({}));
    return { status: response.status, ok: response.ok, payload };
  }

  return {
    /**
     * Read a file, authenticated.
     *
     * Not raw.githubusercontent: that is served with cache headers measured in
     * minutes, and this read is the first half of a read-modify-write. Getting
     * a stale device list here would mean writing back a list with somebody
     * else's change removed from it.
     *
     * Returns { ok: true, content, sha } — with `content: null` and `sha: ''`
     * when there is no file yet, which is an ordinary first enrolment — or
     * { ok: false, reason, detail }.
     */
    async readFile({ repo, path }) {
      const issued = await credential(repo);
      if (!issued.ok) return { ok: false, reason: 'credential', detail: issued.detail };

      const found = await callWith(issued.token, `/repos/${repo}/contents/${encodeURI(path)}`);
      if (found.status === 404) return { ok: true, content: null, sha: '' };
      if (!found.ok) {
        return { ok: false, reason: 'github', detail: `GitHub returned ${found.status}.` };
      }
      if (typeof found.payload?.content !== 'string') {
        return { ok: false, reason: 'github', detail: `${path} is not a file.` };
      }

      return { ok: true, content: fromBase64(found.payload.content), sha: found.payload.sha };
    },

    /**
     * Put `content` at `path`, and return where it can be looked at.
     *
     * `sha` is the blob SHA the page read before editing. Sending it back is
     * what makes GitHub refuse the write if somebody changed the file in
     * between, rather than silently discarding their change. An empty string
     * means the file did not exist, which is a legitimate first write.
     *
     * Returns { ok: true, mode, url } or { ok: false, reason, detail }.
     */
    async writeFile({ repo, path, content, sha, contentHash, message, mode = 'branch' }) {
      // One token, minted for this repository and this write. If the App is
      // not installed here, that is the answer — and it is the same answer as
      // "this site was revoked", which is the point of revoking that way.
      const issued = await credential(repo);
      if (!issued.ok) return { ok: false, reason: 'credential', detail: issued.detail };
      const call = (path_, options) => callWith(issued.token, path_, options);

      const put = (branch) =>
        call(`/repos/${repo}/contents/${encodeURI(path)}`, {
          method: 'PUT',
          body: {
            message,
            content: toBase64(content),
            ...(sha ? { sha } : {}),
            ...(branch ? { branch } : {}),
          },
        });

      /**
       * A rejected SHA has two meanings and they need opposite answers.
       *
       * Somebody else changed the file: refuse, and tell the member so they
       * can go and look. This edit already landed — a double tap, or a retry
       * of a request whose answer never arrived: say it worked, because it
       * did. Telling that member it failed is how you end up with two.
       *
       * Only the bytes can tell them apart, so go and read them.
       */
      const alreadyThere = async (branch) => {
        const query = branch ? `?ref=${encodeURIComponent(branch)}` : '';
        const existing = await call(`/repos/${repo}/contents/${encodeURI(path)}${query}`);
        if (!existing.ok || !existing.payload?.content) return false;
        try {
          return (await hashOf(fromBase64(existing.payload.content))) === contentHash;
        } catch (error) {
          return false;
        }
      };

      const conflicted = (status) => status === 409 || status === 422;

      if (mode === 'direct') {
        const written = await put(null);
        if (conflicted(written.status)) {
          if (await alreadyThere(null)) return { ok: true, mode, url: '', repeated: true };
          return { ok: false, reason: 'conflict', detail: 'The file changed while you were editing.' };
        }
        if (!written.ok) {
          return { ok: false, reason: 'github', detail: `GitHub returned ${written.status}.` };
        }
        return { ok: true, mode, url: written.payload?.commit?.html_url || '' };
      }

      /* ------------------------------------------------------ branch mode */

      const repository = await call(`/repos/${repo}`);
      if (!repository.ok) {
        return { ok: false, reason: 'github', detail: `GitHub returned ${repository.status}.` };
      }
      const base = repository.payload.default_branch;

      const head = await call(`/repos/${repo}/git/ref/heads/${encodeURIComponent(base)}`);
      if (!head.ok) {
        return { ok: false, reason: 'github', detail: `Could not read ${base}.` };
      }

      const branch = branchFor(contentHash);
      const created = await call(`/repos/${repo}/git/refs`, {
        method: 'POST',
        body: { ref: `refs/heads/${branch}`, sha: head.payload.object.sha },
      });
      // 422 is "already exists", which is what a retry of the same edit looks
      // like. The branch name is derived from the content, so the one sitting
      // there is this edit and not somebody else's.
      if (!created.ok && created.status !== 422) {
        return { ok: false, reason: 'github', detail: `Could not open a branch (${created.status}).` };
      }

      // The branch was forked from the default one, so the SHA the member read
      // is still the right SHA here — unless this edit is already on it, which
      // is exactly what a retry looks like.
      let repeated = false;
      const written = await put(branch);
      if (conflicted(written.status)) {
        if (!(await alreadyThere(branch))) {
          return { ok: false, reason: 'conflict', detail: 'The file changed while you were editing.' };
        }
        repeated = true;
      } else if (!written.ok) {
        return { ok: false, reason: 'github', detail: `GitHub returned ${written.status}.` };
      }

      const pull = await call(`/repos/${repo}/pulls`, {
        method: 'POST',
        body: { title: message, head: branch, base, body: message },
      });
      if (pull.ok) return { ok: true, mode, url: pull.payload.html_url, repeated };

      // Also 422 when one is already open for this branch — the same retry
      // case as above. Find it rather than reporting a failure for something
      // that has already happened.
      if (pull.status === 422) {
        const owner = repo.split('/')[0];
        const open = await call(
          `/repos/${repo}/pulls?state=open&head=${encodeURIComponent(`${owner}:${branch}`)}`
        );
        const existing = Array.isArray(open.payload) ? open.payload[0] : null;
        if (existing) return { ok: true, mode, url: existing.html_url, repeated };
      }

      // The file IS written; only the pull request is missing. Saying so beats
      // reporting a failure the member would respond to by editing again.
      return {
        ok: true,
        mode,
        url: '',
        detail: 'Your change is saved on a branch, but we could not open a request for it.',
      };
    },
  };
}
