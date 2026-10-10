# `site/bin/mint-claim.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

A claim is a short token saying "Fort Collins Public Media asserts that this
address was mailed a link on this date". It is signed with a private key held
by whoever runs this script, and verified in the browser against the public
half published in site/_data/identity.yml.

    Generate a signing key (once):

        python3 site/bin/mint-claim.py --new-key claim-key.pem

    Mint a claim and get a link to email:

        python3 site/bin/mint-claim.py --email someone@example.com

Sending is deliberately not automated. At this size, pasting a link into an
Outlook message is a smaller and more reliable thing than a mail API, a sender
domain, and a set of credentials that can expire on a weekend. Automate it when
the volume justifies it, not before.

WHY OPENSSL RATHER THAN A PYTHON LIBRARY
----------------------------------------
Nothing else in site/bin/ needs anything installed, and that is worth keeping:
the person who runs this in two years should not have to resolve a dependency
first. openssl is already on macOS, on Linux, and on the GitHub Actions
runners. The only part written by hand is the conversion from openssl's DER
signature to the raw r||s pair WebCrypto expects, which is small, fixed, and
covered by tests.

## 2

Above `SPKI_LEN = 91`

A P-256 SubjectPublicKeyInfo is a fixed size, and the point is the tail of
it. Asserting the length is cheaper and harder to get wrong than walking the
structure, and a mismatch means something other than a P-256 key was handed
in — which should stop the run, not be worked around.

## 3

Above `if len(der) < 8 or der[0] != 0x30:`

Convert an ECDSA DER signature to the 64-byte r||s WebCrypto wants.

openssl emits SEQUENCE { INTEGER r, INTEGER s }, where each integer is
big-endian, minimally encoded, and carries a leading zero byte when its top
bit would otherwise read as negative. WebCrypto wants both values as fixed
32-byte fields. So: strip the padding openssl added, then re-pad to a fixed
width. The two paddings are for different reasons and are not the same
bytes.

## 4

Above `handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)`

Owner-only from the moment it exists, rather than written wide and fixed
afterwards.

## 5

Above `email = email.strip().lower()`

Return the signed token for an address.

The signature covers the version and the payload together, so a token
cannot be replayed under a different format later.

With `repo`, the claim also names a member site, and the link points at
/authorize/ instead of /check-in/. The repository travels inside the
signature rather than as a separate URL parameter, so a forwarded link
cannot be edited to bind a device to somebody else's site.

## 6

Above `path = "/authorize/" if args.repo else "/check-in/"`

A claim naming a repository is for binding a device to a member site; a
bare one confirms an address. Same signature, same key, different door.

## 7

Above `print(f"{args.site}{path}#claim={token}")`

The token rides in the fragment, which browsers do not send to servers.
It never appears in an access log, ours or Cloudflare's.
