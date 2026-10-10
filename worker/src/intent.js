// see docs/inline/worker/src/intent.js.md#1

const HASH_ALGORITHM = 'SHA-256';

const toBase64Url = (bytes) => {
  let binary = '';
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/** The hash a page declares up front and the broker recomputes at the end. */
export async function contentHash(text) {
  const bytes = new TextEncoder().encode(String(text));
  return toBase64Url(await crypto.subtle.digest(HASH_ALGORITHM, bytes));
}

/* --------------------------------------------------------------------- names */

const SEGMENT = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

function checkRepo(value, owner) {
  if (typeof value !== 'string') return 'A repository is required.';

  const parts = value.split('/');
  if (parts.length !== 2) return 'A repository looks like owner/name.';
  if (!parts.every((part) => SEGMENT.test(part) && part !== '.' && part !== '..')) {
    return 'That is not a repository name.';
  }

  // see docs/inline/worker/src/intent.js.md#2
  if (owner && parts[0].toLowerCase() !== owner.toLowerCase()) {
    return `This broker only handles repositories under ${owner}.`;
  }
  return null;
}

// see docs/inline/worker/src/intent.js.md#3
const FORBIDDEN_PREFIXES = ['.github/', '.auth/'];

function checkPath(value) {
  if (typeof value !== 'string' || !value) return 'A path is required.';
  if (value.startsWith('/') || value.includes('\\')) return 'That is not a path in a repository.';

  const segments = value.split('/');
  if (segments.some((part) => part === '' || part === '.' || part === '..')) {
    return 'That path does not go anywhere.';
  }
  if (FORBIDDEN_PREFIXES.some((prefix) => value.startsWith(prefix))) {
    return `${value} is not a file this broker will write.`;
  }
  return null;
}

/* ------------------------------------------------------------------- actions */

// see docs/inline/worker/src/intent.js.md#4
export const ACTIONS = {
  // see docs/inline/worker/src/intent.js.md#5
  verify: {
    declare: [],
    userVerification: false,
  },

  // see docs/inline/worker/src/intent.js.md#6
  'settings.write': {
    declare: ['path', 'sha', 'content_hash'],
    userVerification: true,
  },

  // see docs/inline/worker/src/intent.js.md#7
  'device.add': {
    declare: ['credential_id', 'public_key'],
    userVerification: true,
    // Not signed by a device on the list, because it is not on the list yet.
    unlisted: true,
  },

  // see docs/inline/worker/src/intent.js.md#8
  'device.allow': {
    declare: ['credential_id'],
    userVerification: true,
  },
  'device.revoke': {
    declare: ['credential_id'],
    userVerification: true,
  },

  // see docs/inline/worker/src/intent.js.md#9
  'upload.grant': {
    declare: ['filename', 'size'],
    userVerification: true,
  },
};

// see docs/inline/worker/src/intent.js.md#10
export function readIntent(body, { owner = '', maxUpload = 0 } = {}) {
  const action = ACTIONS[body?.action];
  if (!action) return { ok: false, detail: 'That is not something this broker does.' };

  const repoProblem = checkRepo(body.repo, owner);
  if (repoProblem) return { ok: false, detail: repoProblem };

  const intent = { action: body.action, repo: body.repo };

  for (const field of action.declare) {
    const value = body[field];

    if (field === 'sha') {
      // see docs/inline/worker/src/intent.js.md#11
      if (value !== '' && !/^[0-9a-f]{40}$/.test(String(value ?? ''))) {
        return { ok: false, detail: 'That is not a blob SHA.' };
      }
      intent.sha = String(value);
      continue;
    }

    if (field === 'path') {
      const problem = checkPath(value);
      if (problem) return { ok: false, detail: problem };
      intent.path = value;
      continue;
    }

    if (field === 'filename') {
      // see docs/inline/worker/src/intent.js.md#12
      if (typeof value !== 'string' || !value || value.length > 200) {
        return { ok: false, detail: 'That is not a file name.' };
      }
      if (/[/\\]/.test(value) || value.startsWith('.')) {
        return { ok: false, detail: 'That is not a file name.' };
      }
      intent.filename = value;
      continue;
    }

    if (field === 'size') {
      const bytes = Number(value);
      if (!Number.isSafeInteger(bytes) || bytes <= 0) {
        return { ok: false, detail: 'That is not a size.' };
      }
      if (maxUpload && bytes > maxUpload) {
        return {
          ok: false,
          detail: `That file is larger than this site accepts (${Math.floor(maxUpload / 1e9)} GB).`,
        };
      }
      intent.size = bytes;
      continue;
    }

    if (typeof value !== 'string' || !value) {
      return { ok: false, detail: `${field} is missing.` };
    }

    // see docs/inline/worker/src/intent.js.md#13
    if (field === 'credential_id' || field === 'public_key') {
      if (!/^[A-Za-z0-9_-]{16,1024}$/.test(value)) {
        return { ok: false, detail: `${field} is not a value this broker recognises.` };
      }
    }

    intent[field] = value;
  }

  return { ok: true, intent };
}

// see docs/inline/worker/src/intent.js.md#14
export async function matchesIntent(intent, body) {
  const action = ACTIONS[intent.action];
  if (!action) return { ok: false, detail: 'That intent is no longer supported.' };

  if (body?.repo !== undefined && body.repo !== intent.repo) {
    return { ok: false, detail: 'This asks about a different site than the challenge was for.' };
  }

  for (const field of action.declare) {
    if (field === 'content_hash') {
      // see docs/inline/worker/src/intent.js.md#15
      if (typeof body?.content !== 'string') {
        return { ok: false, detail: 'The content is missing.' };
      }
      if ((await contentHash(body.content)) !== intent.content_hash) {
        return { ok: false, detail: 'The content is not what was signed for.' };
      }
      continue;
    }

    if (body?.[field] !== undefined && body[field] !== intent[field]) {
      return { ok: false, detail: `${field} is not what the challenge was issued for.` };
    }
  }

  return { ok: true };
}
