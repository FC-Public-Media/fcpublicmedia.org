# `site/assets/js/claims.js`

Moved out of the file. Unreviewed.

## 1

Above `const VERSION = 'v1';`

Verifying an email claim in the browser.

A claim is minted by site/bin/mint-claim.py and arrives as a link:

    /check-in/#claim=v1.<payload>.<signature>

The payload is JSON — an address, when it was issued, when it lapses, and
which key signed it. The signature is ECDSA P-256 over "v1.<payload>",
checked here against the public keys published in _data/identity.yml.

WHAT THE CHECK IS FOR
---------------------
Not security. Someone determined to lie to this page can edit it; it is
their browser. The check is here so a person whose link was mangled by an
email client finds out immediately instead of believing they are verified.

The security lives in the token, which is kept whole. Anything that later
wants to trust the address — staff, a form, a Worker — re-verifies the
signature itself rather than believing a flag someone else's device set.

## 2

Above `export async function verifyClaim(token, keys, now = Date.now()) {`

Check a token against the configured keys.

Resolves to the payload when the signature holds and the claim is current,
or to a reason it did not. Never throws and never rejects: a malformed
string arriving from a URL is an ordinary event, not an exception.

## 3

Above `const ordered = payload.kid`

A key id narrows which key to try, but is a hint rather than a rule — a
claim minted before a rotation still verifies against whichever published
key actually signed it.

## 4

Above `}`

A key we cannot import is a configuration problem, not this visitor's
problem. Try the rest.

## 5

Above `if (payload.exp * 1000 <= now) {`

Expiry is checked after the signature, so an expired-but-genuine claim can
be reported as expired rather than as a forgery. The two need different
advice: one means "ask us for a new link", the other means "something is
wrong with this link".

## 6

Above `export function clearClaimFromLocation() {`

Remove the claim from the address bar once it has been dealt with.

It is already stored; leaving it visible invites someone to share the URL,
which would hand their address to whoever they sent it to.
