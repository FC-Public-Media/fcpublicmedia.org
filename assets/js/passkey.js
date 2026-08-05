// Creating a passkey and getting the public half out of it.
//
// VOCABULARY, because it took a while to get straight
// ---------------------------------------------------
//   passkey        a WebAuthn credential. The private half never leaves the
//                  phone's secure hardware, and iCloud Keychain / Google
//                  Password Manager sync and back it up. That is why it
//                  survives the browser clearing site storage, which a key we
//                  generated ourselves would not.
//   credential ID  an opaque handle for one passkey. Stored next to the
//                  public key.
//   relying party  the domain the passkey belongs to. A passkey made here
//                  works on this domain and nowhere else — which is why the
//                  editing UI has to live on our domain rather than on the
//                  member's published site.
//   user handle    an opaque per-person ID baked into the credential, so a
//                  browser can offer the right passkey without anyone typing
//                  a username.
//
// WHAT THIS FILE DOES NOT DO
// --------------------------
// It does not authenticate anybody. Registration below generates its own
// challenge, which is fine here because the thing being trusted is the signed
// link that got the visitor to this page, not the ceremony.
//
// When the authentication side gets built, its challenge MUST come from the
// broker. A self-generated challenge there would let anyone replay a captured
// assertion. Do not copy the pattern below into that flow.

const B64 = {
  encode(bytes) {
    let binary = '';
    for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  },
};

export const supported = () =>
  Boolean(window.PublicKeyCredential && navigator.credentials?.create);

// The user handle is the only thing a sign-in gives back about who signed in
// — not the email, not the display name, just these bytes. So whatever a later
// page needs to know has to be *in* here.
//
// This was originally a SHA-256 of "email|repo", which was unreadable by
// design and therefore useless: /upload/ needs to know which member site the
// passkey belongs to, and a hash cannot be turned back into one. So the site
// is carried in the clear and the person is carried as a short digest:
//
//     v1|owner/repository|a1b2c3d4
//
// The digest keeps two people on the same site from colliding. That matters
// more than it looks: an authenticator treats a repeated user handle as the
// same account and REPLACES the existing credential, so a shared handle would
// mean the second person to register silently evicted the first.
//
// Nothing secret is in here. It names a public repository, and it is stored on
// the visitor's own device where it may show up in their password manager —
// which is arguably a feature, since it says what the passkey is for.
const HANDLE_VERSION = 'v1';
const HANDLE_LIMIT = 64; // WebAuthn's ceiling for user.id

async function shortDigest(value) {
  const bytes = new Uint8Array(
    await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
  );
  return Array.from(bytes.slice(0, 4), (b) => b.toString(16).padStart(2, '0')).join('');
}

async function encodeHandle(email, repo) {
  const handle = `${HANDLE_VERSION}|${repo}|${await shortDigest(email)}`;
  const bytes = new TextEncoder().encode(handle);
  if (bytes.length > HANDLE_LIMIT) return null;
  return bytes;
}

/**
 * Read a handle back. Returns { repo, person } or null.
 *
 * Never throws on rubbish: the bytes come from an authenticator and could be
 * from an older format, a different site, or nothing we recognise.
 */
export function decodeHandle(bytes) {
  if (!bytes) return null;
  let text;
  try {
    text = new TextDecoder().decode(bytes);
  } catch (error) {
    return null;
  }

  const parts = text.split('|');
  if (parts.length !== 3 || parts[0] !== HANDLE_VERSION) return null;
  if (parts[1].split('/').length !== 2) return null;

  return { repo: parts[1], person: parts[2] };
}

/**
 * Run the registration ceremony and return the record to hand over.
 *
 * Resolves to { ok: true, device } or { ok: false, reason, detail }. Never
 * throws: someone dismissing the system passkey sheet is an ordinary thing to
 * do, not an exception.
 */
export async function createPasskey({ email, repo, label, rpId, issuer }) {
  if (!supported()) return { ok: false, reason: 'unsupported' };

  const handle = await encodeHandle(email, repo);
  if (!handle) return { ok: false, reason: 'repo-too-long' };

  const challenge = crypto.getRandomValues(new Uint8Array(32));

  // rp.id is omitted unless configured. Left out, the browser uses the
  // origin's own domain, which is right in development and on a preview
  // deployment; setting it to a domain the page is not served from throws a
  // SecurityError rather than failing softly.
  const rp = { name: issuer || 'Fort Collins Public Media' };
  if (rpId) rp.id = rpId;

  let credential;
  try {
    credential = await navigator.credentials.create({
      publicKey: {
        challenge,
        rp,
        user: {
          id: handle,
          name: email,
          displayName: label || email,
        },
        // ES256 first, RS256 as a fallback for authenticators that want it.
        pubKeyCredParams: [
          { type: 'public-key', alg: -7 },
          { type: 'public-key', alg: -257 },
        ],
        authenticatorSelection: {
          // Discoverable, so signing in later needs nothing typed and we do
          // not have to ship a list of credential IDs to the sign-in page.
          residentKey: 'required',
          userVerification: 'preferred',
        },
        // We are not checking which hardware made this, so asking for proof of
        // it would only add a privacy prompt on some platforms for nothing.
        attestation: 'none',
        timeout: 120000,
      },
    });
  } catch (error) {
    const reason = error?.name === 'NotAllowedError' ? 'cancelled' : 'failed';
    return { ok: false, reason, detail: error?.message || String(error) };
  }

  if (!credential) return { ok: false, reason: 'cancelled' };

  const response = credential.response;

  // getPublicKey() hands back SPKI DER directly. The alternative is decoding
  // COSE out of the attestation object by hand, which is a lot of code to
  // maintain for browsers that are now several years old.
  const spki = response.getPublicKey?.();
  if (!spki) {
    return { ok: false, reason: 'no-public-key' };
  }

  return {
    ok: true,
    device: {
      credential_id: B64.encode(credential.rawId),
      // SPKI, so crypto.subtle.importKey('spki', …) reads it as-is later.
      public_key: B64.encode(spki),
      algorithm: response.getPublicKeyAlgorithm?.() ?? null,
      transports: response.getTransports?.() ?? [],
      label: (label || '').trim() || 'Unnamed device',
      added: new Date().toISOString(),
    },
  };
}

/**
 * Ask the broker for a challenge to sign, bound to one specific thing.
 *
 * The intent goes up before the passkey prompt does, so what comes back is
 * good for that and nothing else. See worker/src/intent.js for why the
 * challenge is not just a nonce.
 *
 * Resolves to { ok: true, challenge, intent } or { ok: false, detail }.
 */
async function requestChallenge(brokerUrl, intent) {
  let response;
  try {
    // brokerUrl is a base — the worker answers /challenge and /verify under
    // it — so this joins rather than replacing any path it carries.
    response = await fetch(`${brokerUrl.replace(/\/+$/, '')}/challenge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(intent),
    });
  } catch (error) {
    return { ok: false, detail: 'We could not reach the server.' };
  }

  const body = await response.json().catch(() => ({}));
  if (!response.ok || !body.challenge) {
    return { ok: false, detail: body.detail || `The server said no (HTTP ${response.status}).` };
  }
  return { ok: true, challenge: body.challenge, intent: body.intent };
}

/**
 * Sign in with an existing passkey, and find out which member site it is for.
 *
 * WHAT THIS PROVES, AND TO WHOM
 * -----------------------------
 * With no broker configured, the challenge is generated right here. To the
 * person holding the device that is still worth something — it says they hold
 * a passkey this site issued, and which site it belongs to, which is enough to
 * show them the right form. To us it proves NOTHING: a captured assertion
 * could be replayed, and the code doing the checking is code the visitor
 * controls. `verified` comes back false to say so, and nothing is written
 * anywhere as a result.
 *
 * With a broker, the challenge comes from there, bound to `intent`, and the
 * assertion goes back for the broker to check against the public key recorded
 * in the member's repository. `verified` is true and the result carries the
 * broker's answer rather than this page's guess.
 *
 * The two paths use the same ceremony. Do not let the first one's success be
 * read as evidence about the second.
 *
 * Resolves to { ok: true, repo, person, credentialId, verified, assertion }
 * or { ok: false, reason, detail }.
 */
export async function signIn({ rpId, brokerUrl, intent } = {}) {
  if (!window.PublicKeyCredential || !navigator.credentials?.get) {
    return { ok: false, reason: 'unsupported' };
  }

  let challenge = null;
  if (brokerUrl) {
    if (!intent) throw new Error('signIn with a broker needs an intent to bind the challenge to');
    const issued = await requestChallenge(brokerUrl, intent);
    if (!issued.ok) return { ok: false, reason: 'no-challenge', detail: issued.detail };
    challenge = issued.challenge;
  }

  const request = {
    challenge: challenge
      ? Uint8Array.from(atob(challenge.replace(/-/g, '+').replace(/_/g, '/')), (c) => c.charCodeAt(0))
      : crypto.getRandomValues(new Uint8Array(32)),
    // The broker requires verification for anything that changes a site, so
    // asking for it here means the prompt happens once rather than the write
    // being refused after the fact.
    userVerification: brokerUrl ? 'required' : 'preferred',
    timeout: 120000,
    // No allowCredentials, deliberately. The passkeys are discoverable, so the
    // browser offers whatever it holds for this domain and nobody has to type
    // a username — which also means this page ships no list of who exists.
  };
  if (rpId) request.rpId = rpId;

  let assertion;
  try {
    assertion = await navigator.credentials.get({ publicKey: request });
  } catch (error) {
    const reason = error?.name === 'NotAllowedError' ? 'cancelled' : 'failed';
    return { ok: false, reason, detail: error?.message || String(error) };
  }

  if (!assertion) return { ok: false, reason: 'cancelled' };

  const handle = decodeHandle(assertion.response?.userHandle);
  if (!handle) {
    // A real passkey for this domain that carries nothing we can read. Most
    // likely registered before the handle format changed.
    return { ok: false, reason: 'unreadable' };
  }

  return {
    ok: true,
    repo: handle.repo,
    person: handle.person,
    credentialId: B64.encode(assertion.rawId),
    verified: Boolean(brokerUrl),
    // What the broker needs to check the signature itself. Kept in the shape
    // its endpoints take, so no page has to know the field names.
    assertion: {
      credential_id: B64.encode(assertion.rawId),
      authenticator_data: B64.encode(assertion.response.authenticatorData),
      client_data_json: B64.encode(assertion.response.clientDataJSON),
      signature: B64.encode(assertion.response.signature),
    },
  };
}
