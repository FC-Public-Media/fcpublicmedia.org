# `site/bin/test_mint_claim.py`

Moved out of the file. Unreviewed.

## 1

Above `import base64`

Tests for mint-claim.py.

The part worth testing is the DER-to-raw signature conversion. Everything else
is openssl doing its job, but that conversion is hand-written, and getting it
wrong produces a token that looks perfectly fine and fails to verify in a
browser — the exact failure that is miserable to diagnose from a phone.

    python3 site/bin/test_mint_claim.py

Run alongside the browser-side check in site/tests/claims.spec.js, which verifies
the same tokens through WebCrypto itself.

## 2

Above `value = b"\xff" + b"\x11" * 31`

A 32-byte value whose top bit is set gets a leading zero in DER, so
the INTEGER is 33 bytes. Keeping that byte would push r into 33 bytes
and shift s by one — a signature that verifies nowhere.

## 3

Above `token, _ = mint.build_claim(self.key, "someone@example.com", 30, "k1")`

The full round trip, checked with openssl rather than our own code.

Signing and verifying with the same hand-written helper would pass
happily while producing something no browser accepts, so this rebuilds
the DER form independently and asks openssl.
