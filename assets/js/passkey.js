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

/**
 * A stable, opaque identifier for one person on one site.
 *
 * Deterministic so that a second device for the same person groups with the
 * first rather than looking like a stranger. Derived rather than stored,
 * because there is nowhere to store it.
 *
 * It is a hash of an email address, and email addresses are guessable, so
 * treat this as pseudonymous rather than anonymous — it does not put the
 * address in the file, but it would not defeat someone checking a hunch.
 */
async function userHandle(email, repo) {
  const material = new TextEncoder().encode(`${email}|${repo}`);
  return new Uint8Array(await crypto.subtle.digest('SHA-256', material));
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
          id: await userHandle(email, repo),
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
