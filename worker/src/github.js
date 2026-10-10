// Reading and writing a member repository through the Contents API. See worker/README.md.

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
    /** { ok: true, content, sha } (null and '' when absent) or { ok: false, reason, detail }. */
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

    /** Write `content` against the blob `sha` the page read ('' = new file); { ok, mode, url }. */
    async writeFile({ repo, path, content, sha, contentHash, message, mode = 'branch' }) {
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

      // A rejected SHA is either a real conflict or this same edit landed already; the bytes decide.
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
      // 422: the content-named branch exists, so it holds this same edit (a retry).
      if (!created.ok && created.status !== 422) {
        return { ok: false, reason: 'github', detail: `Could not open a branch (${created.status}).` };
      }

      // Forked from the default branch, so the member's SHA still applies unless this is a retry.
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

      // 422 again on a retry: find the pull request already open.
      if (pull.status === 422) {
        const owner = repo.split('/')[0];
        const open = await call(
          `/repos/${repo}/pulls?state=open&head=${encodeURIComponent(`${owner}:${branch}`)}`
        );
        const existing = Array.isArray(open.payload) ? open.payload[0] : null;
        if (existing) return { ok: true, mode, url: existing.html_url, repeated };
      }

      // The file is written; only the pull request is missing.
      return {
        ok: true,
        mode,
        url: '',
        detail: 'Your change is saved on a branch, but we could not open a request for it.',
      };
    },
  };
}
