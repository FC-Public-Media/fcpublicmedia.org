// Verifying an email claim in the browser.
//
// A claim is minted by script/mint-claim.py and arrives as a link:
//
//     /check-in/#claim=v1.<payload>.<signature>
//
// The payload is JSON — an address, when it was issued, when it lapses, and
// which key signed it. The signature is ECDSA P-256 over "v1.<payload>",
// checked here against the public keys published in _data/identity.yml.
//
// WHAT THE CHECK IS FOR
// ---------------------
// Not security. Someone determined to lie to this page can edit it; it is
// their browser. The check is here so a person whose link was mangled by an
// email client finds out immediately instead of believing they are verified.
//
// The security lives in the token, which is kept whole. Anything that later
// wants to trust the address — staff, a form, a Worker — re-verifies the
// signature itself rather than believing a flag someone else's device set.

const VERSION = 'v1';

function decodeBase64Url(text) {
  const padded = text.replace(/-/g, '+').replace(/_/g, '/');
  const binary = atob(padded + '='.repeat((4 - (padded.length % 4)) % 4));
  return Uint8Array.from(binary, (c) => c.charCodeAt(0));
}

/** Import one published key into something WebCrypto will verify against. */
function importKey({ x, y }) {
  return crypto.subtle.importKey(
    'jwk',
    { kty: 'EC', crv: 'P-256', x, y, ext: true },
    { name: 'ECDSA', namedCurve: 'P-256' },
    false,
    ['verify']
  );
}

/**
 * Check a token against the configured keys.
 *
 * Resolves to the payload when the signature holds and the claim is current,
 * or to a reason it did not. Never throws and never rejects: a malformed
 * string arriving from a URL is an ordinary event, not an exception.
 */
export async function verifyClaim(token, keys, now = Date.now()) {
  if (typeof token !== 'string') return { ok: false, reason: 'missing' };

  const parts = token.split('.');
  if (parts.length !== 3 || parts[0] !== VERSION) {
    return { ok: false, reason: 'malformed' };
  }

  const [version, body, signature] = parts;

  let payload;
  let signatureBytes;
  try {
    payload = JSON.parse(new TextDecoder().decode(decodeBase64Url(body)));
    signatureBytes = decodeBase64Url(signature);
  } catch (error) {
    return { ok: false, reason: 'malformed' };
  }

  if (!payload?.email || !payload?.exp) return { ok: false, reason: 'malformed' };

  if (!crypto?.subtle) return { ok: false, reason: 'unsupported' };

  // A key id narrows which key to try, but is a hint rather than a rule — a
  // claim minted before a rotation still verifies against whichever published
  // key actually signed it.
  const ordered = payload.kid
    ? [...keys].sort((a, b) => (b.id === payload.kid) - (a.id === payload.kid))
    : keys;

  const signed = new TextEncoder().encode(`${version}.${body}`);

  let verified = false;
  for (const key of ordered) {
    try {
      const imported = await importKey(key);
      // eslint-disable-next-line no-await-in-loop
      if (await crypto.subtle.verify(
        { name: 'ECDSA', hash: 'SHA-256' },
        imported,
        signatureBytes,
        signed
      )) {
        verified = true;
        break;
      }
    } catch (error) {
      // A key we cannot import is a configuration problem, not this visitor's
      // problem. Try the rest.
    }
  }

  if (!verified) return { ok: false, reason: 'signature' };

  // Expiry is checked after the signature, so an expired-but-genuine claim can
  // be reported as expired rather than as a forgery. The two need different
  // advice: one means "ask us for a new link", the other means "something is
  // wrong with this link".
  if (payload.exp * 1000 <= now) {
    return { ok: false, reason: 'expired', payload };
  }

  return { ok: true, payload };
}

/** Pull a claim out of the URL fragment, if one is there. */
export function claimFromLocation(location = window.location) {
  const hash = (location.hash || '').replace(/^#/, '');
  if (!hash) return null;
  return new URLSearchParams(hash).get('claim');
}

/**
 * Remove the claim from the address bar once it has been dealt with.
 *
 * It is already stored; leaving it visible invites someone to share the URL,
 * which would hand their address to whoever they sent it to.
 */
export function clearClaimFromLocation() {
  const { pathname, search } = window.location;
  window.history.replaceState(null, '', pathname + search);
}
