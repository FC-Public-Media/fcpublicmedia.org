// What a signature is for.
//
// WHY A CHALLENGE IS NOT JUST A NONCE HERE
// ----------------------------------------
// The obvious broker issues a random challenge, checks the assertion, and then
// does whatever the request asks for. That makes a verified assertion a bearer
// token: whoever holds it can spend it on any action, because the signature
// says nothing about what was being agreed to.
//
// So a challenge is issued FOR something. The page declares the action first —
// this file, this SHA, content hashing to this — and gets a challenge bound to
// that declaration. When the assertion comes back, the request has to match
// what was declared, byte for byte. The member's device signed a challenge
// that means one specific edit and nothing else.
//
// The cost is one extra round trip before the passkey prompt. It buys the
// difference between "this person is authorized" and "this person authorized
// THIS", and only the second one is worth having.

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

  // Set an owner and the broker will not touch anything outside it. Without
  // this the repo is just a string from the page, and the only thing stopping
  // a request naming somebody else's repository is that the lookup would fail
  // — which is true today and stops being true the moment a token is added.
  if (owner && parts[0].toLowerCase() !== owner.toLowerCase()) {
    return `This broker only handles repositories under ${owner}.`;
  }
  return null;
}

// Paths the broker refuses to write no matter who asks.
//
// .github/ is the one that matters: a workflow file runs with the
// repository's secrets, so permission to write one is permission to use every
// credential the repository holds. An editor for a tagline must never be a
// route to that.
//
// .auth/ is the device list. It is the broker's own bookkeeping and changing
// it is how you would add yourself; it has its own flow, with its own rules.
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

/**
 * Every action the broker knows, and what has to be declared to ask for one.
 *
 * Add an action here and it becomes requestable. Nothing else in this file
 * needs to change — which is the point, so that adding one is a decision made
 * in one visible place rather than a branch buried in a handler.
 */
export const ACTIONS = {
  // Prove a device is bound to a site. Writes nothing. This is what a page
  // uses to find out whether to show an editor at all.
  verify: {
    declare: [],
    userVerification: false,
  },

  // Replace one file in the member's own repository with content the page
  // declared the hash of. `sha` is the blob SHA the page read; sending it back
  // is what makes GitHub refuse the write if somebody else edited in between.
  'settings.write': {
    declare: ['path', 'sha', 'content_hash'],
    userVerification: true,
  },

  // Put a new passkey on the site's list. The signature answering this one
  // comes from the NEW device — it is proof that whoever is asking holds the
  // key they are asking us to record, and nothing more. Authority to enrol is
  // the claim, checked separately.
  //
  // Deliberately survivable when the claim link was forwarded: being listed
  // does nothing on its own. See enroll.js.
  'device.add': {
    declare: ['credential_id', 'public_key'],
    userVerification: true,
    // Not signed by a device on the list, because it is not on the list yet.
    unlisted: true,
  },

  // Let a listed device publish, or stop it. Signed by an existing device that
  // may already publish — the owner approving a co-producer's phone from their
  // own phone, with staff nowhere in it.
  'device.allow': {
    declare: ['credential_id'],
    userVerification: true,
  },
  'device.revoke': {
    declare: ['credential_id'],
    userVerification: true,
  },

  // Permission to put one file in object storage.
  //
  // Note what is NOT declared: a content hash. The broker never sees these
  // bytes — they go straight from the browser to R2 — and hashing six
  // gigabytes before starting would roughly double the wait to protect
  // something we could not check anyway. What the signature binds to is the
  // grant: this member, this site, this object, this size. See r2.js.
  'upload.grant': {
    declare: ['filename', 'size'],
    userVerification: true,
  },
};

/**
 * Turn a request body into an intent, or say why not.
 *
 * Returns { ok: true, intent } or { ok: false, detail }. Everything here came
 * from a page and none of it is trusted, including the shape.
 */
export function readIntent(body, { owner = '', maxUpload = 0 } = {}) {
  const action = ACTIONS[body?.action];
  if (!action) return { ok: false, detail: 'That is not something this broker does.' };

  const repoProblem = checkRepo(body.repo, owner);
  if (repoProblem) return { ok: false, detail: repoProblem };

  const intent = { action: body.action, repo: body.repo };

  for (const field of action.declare) {
    const value = body[field];

    if (field === 'sha') {
      // Empty means "there is no file there yet", which is a legitimate first
      // write. Anything else has to look like a blob SHA.
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
      // Only ever used to build a slug, never as a path — but a name carrying
      // separators or a leading dot is a sign of something other than a file
      // being picked, and refusing it costs nothing.
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

    // These end up in a JSON file in somebody's repository, so the shape is
    // checked here rather than trusted to survive a round trip. base64url and
    // nothing else — a credential ID is 16 to 32 bytes and an SPKI key is a
    // few hundred, so anything longer is not what it says it is.
    if (field === 'credential_id' || field === 'public_key') {
      if (!/^[A-Za-z0-9_-]{16,1024}$/.test(value)) {
        return { ok: false, detail: `${field} is not a value this broker recognises.` };
      }
    }

    intent[field] = value;
  }

  return { ok: true, intent };
}

/**
 * Does the finished request do what the challenge was issued for?
 *
 * Called after the signature checks out. Every declared field has to be
 * present and identical — a request that changed its mind between asking for
 * the challenge and using it did not get that challenge signed for this.
 */
export async function matchesIntent(intent, body) {
  const action = ACTIONS[intent.action];
  if (!action) return { ok: false, detail: 'That intent is no longer supported.' };

  if (body?.repo !== undefined && body.repo !== intent.repo) {
    return { ok: false, detail: 'This asks about a different site than the challenge was for.' };
  }

  for (const field of action.declare) {
    if (field === 'content_hash') {
      // The page declared a hash; here is where the actual bytes turn up. If
      // they hash to something else, the device signed for different content.
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
