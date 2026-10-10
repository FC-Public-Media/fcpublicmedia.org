// see docs/inline/site/assets/js/claims.js.md#1

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

// see docs/inline/site/assets/js/claims.js.md#2
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

  // see docs/inline/site/assets/js/claims.js.md#3
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
      // see docs/inline/site/assets/js/claims.js.md#4
    }
  }

  if (!verified) return { ok: false, reason: 'signature' };

  // see docs/inline/site/assets/js/claims.js.md#5
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

// see docs/inline/site/assets/js/claims.js.md#6
export function clearClaimFromLocation() {
  const { pathname, search } = window.location;
  window.history.replaceState(null, '', pathname + search);
}
