#!/usr/bin/env python3
"""Mint a signed email claim, and generate the key that signs them.

A claim is a short token saying "Fort Collins Public Media asserts that this
address was mailed a link on this date". It is signed with a private key held
by whoever runs this script, and verified in the browser against the public
half published in _data/identity.yml.

    Generate a signing key (once):

        python3 script/mint-claim.py --new-key claim-key.pem

    Mint a claim and get a link to email:

        python3 script/mint-claim.py --email someone@example.com

Sending is deliberately not automated. At this size, pasting a link into an
Outlook message is a smaller and more reliable thing than a mail API, a sender
domain, and a set of credentials that can expire on a weekend. Automate it when
the volume justifies it, not before.

WHY OPENSSL RATHER THAN A PYTHON LIBRARY
----------------------------------------
Nothing else in script/ needs anything installed, and that is worth keeping:
the person who runs this in two years should not have to resolve a dependency
first. openssl is already on macOS, on Linux, and on the GitHub Actions
runners. The only part written by hand is the conversion from openssl's DER
signature to the raw r||s pair WebCrypto expects, which is small, fixed, and
covered by tests.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time

CURVE = "prime256v1"  # P-256, the curve WebCrypto implements everywhere
VERSION = "v1"

# A P-256 SubjectPublicKeyInfo is a fixed size, and the point is the tail of
# it. Asserting the length is cheaper and harder to get wrong than walking the
# structure, and a mismatch means something other than a P-256 key was handed
# in — which should stop the run, not be worked around.
SPKI_LEN = 91
POINT_LEN = 65


class MintError(Exception):
    """Anything that should stop the run with a readable message."""


# --------------------------------------------------------------------- base64


def b64u(raw):
    """URL-safe base64 without padding, the encoding used across the token."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def unb64u(text):
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


# ------------------------------------------------------------------------ DER


def der_to_raw(der):
    """Convert an ECDSA DER signature to the 64-byte r||s WebCrypto wants.

    openssl emits SEQUENCE { INTEGER r, INTEGER s }, where each integer is
    big-endian, minimally encoded, and carries a leading zero byte when its top
    bit would otherwise read as negative. WebCrypto wants both values as fixed
    32-byte fields. So: strip the padding openssl added, then re-pad to a fixed
    width. The two paddings are for different reasons and are not the same
    bytes.
    """
    if len(der) < 8 or der[0] != 0x30:
        raise MintError("signature is not a DER SEQUENCE")

    # Length may be short form (one byte) or long form (a count, then bytes).
    length = der[1]
    index = 2 if not length & 0x80 else 2 + (length & 0x7F)

    values = []
    for _ in range(2):
        if index >= len(der) or der[index] != 0x02:
            raise MintError("signature is missing an INTEGER")
        size = der[index + 1]
        if size & 0x80:
            raise MintError("signature INTEGER uses long-form length")

        value = der[index + 2 : index + 2 + size].lstrip(b"\x00")
        if len(value) > 32:
            raise MintError("signature INTEGER is too large for P-256")

        values.append(value.rjust(32, b"\x00"))
        index += 2 + size

    if index != len(der):
        raise MintError("trailing bytes after the DER signature")

    return values[0] + values[1]


def spki_to_point(der):
    """Pull the uncompressed (x, y) point out of a P-256 public key."""
    if len(der) != SPKI_LEN:
        raise MintError(
            f"expected a {SPKI_LEN}-byte P-256 public key, got {len(der)} bytes"
        )

    point = der[-POINT_LEN:]
    if point[0] != 0x04:
        raise MintError("public key point is not in uncompressed form")

    return point[1:33], point[33:65]


# -------------------------------------------------------------------- openssl


def openssl(args, stdin=None):
    try:
        result = subprocess.run(
            ["openssl", *args], input=stdin, capture_output=True, check=False
        )
    except FileNotFoundError:
        raise MintError("openssl was not found on PATH")

    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise MintError(f"openssl {args[0]} failed: {detail}")

    return result.stdout


def new_key(path):
    """Write a new private key and return the public block to publish."""
    if os.path.exists(path):
        raise MintError(
            f"{path} already exists. Refusing to overwrite a signing key — "
            "every claim it signed would stop verifying."
        )

    pem = openssl(["ecparam", "-name", CURVE, "-genkey", "-noout"])

    # Owner-only from the moment it exists, rather than written wide and fixed
    # afterwards.
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(handle, "wb") as out:
        out.write(pem)

    return public_block(path)


def public_block(key_path):
    """The YAML fragment for _data/identity.yml describing this key."""
    der = openssl(["ec", "-in", key_path, "-pubout", "-outform", "DER"])
    x, y = spki_to_point(der)

    return {
        "id": time.strftime("%Y-%m"),
        "x": b64u(x),
        "y": b64u(y),
    }


def sign(key_path, message):
    der = openssl(["dgst", "-sha256", "-sign", key_path], stdin=message)
    return der_to_raw(der)


# ---------------------------------------------------------------------- claim


def build_claim(key_path, email, days, key_id, now=None, repo=None):
    """Return the signed token for an address.

    The signature covers the version and the payload together, so a token
    cannot be replayed under a different format later.

    With `repo`, the claim also names a member site, and the link points at
    /authorize/ instead of /check-in/. The repository travels inside the
    signature rather than as a separate URL parameter, so a forwarded link
    cannot be edited to bind a device to somebody else's site.
    """
    email = email.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise MintError(f"{email!r} does not look like an email address")

    issued = int(now if now is not None else time.time())
    payload = {
        "email": email,
        "iat": issued,
        "exp": issued + days * 86400,
        "kid": key_id,
    }

    if repo:
        if repo.count("/") != 1 or repo.startswith("/") or repo.endswith("/"):
            raise MintError(f"{repo!r} should look like owner/repository")
        payload["repo"] = repo

    # Separators pinned so the bytes signed here are the bytes verified there.
    body = b64u(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{VERSION}.{body}".encode("ascii")

    return f"{VERSION}.{body}.{b64u(sign(key_path, signing_input))}", payload


# ----------------------------------------------------------------------- main


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--new-key", metavar="PATH", help="generate a signing key")
    parser.add_argument("--email", help="address to mint a claim for")
    parser.add_argument(
        "--key",
        default=os.environ.get("FCPM_CLAIM_KEY", "claim-key.pem"),
        help="signing key (default: $FCPM_CLAIM_KEY or claim-key.pem)",
    )
    parser.add_argument("--days", type=int, default=120, help="how long it stays valid")
    parser.add_argument(
        "--repo",
        help="owner/repository of a member site; makes this a device-binding link",
    )
    parser.add_argument(
        "--key-id",
        default=None,
        help="key id recorded in the claim; defaults to the current year-month",
    )
    parser.add_argument(
        "--site",
        default="https://www.fcpublicmedia.org",
        help="site the link points at",
    )
    args = parser.parse_args(argv)

    if args.new_key:
        block = new_key(args.new_key)
        print(f"Private key written to {args.new_key} — keep it out of git.\n")
        print("Paste this into the `keys:` list in _data/identity.yml:\n")
        print(f'  - id: "{block["id"]}"')
        print(f'    x: "{block["x"]}"')
        print(f'    y: "{block["y"]}"')
        return 0

    if not args.email:
        parser.error("give --email ADDRESS, or --new-key PATH to start")

    if not os.path.exists(args.key):
        raise MintError(
            f"no signing key at {args.key}. Generate one with --new-key, or "
            "point --key at the existing one."
        )

    key_id = args.key_id or public_block(args.key)["id"]
    token, payload = build_claim(
        args.key, args.email, args.days, key_id, repo=args.repo
    )

    # A claim naming a repository is for binding a device to a member site; a
    # bare one confirms an address. Same signature, same key, different door.
    path = "/authorize/" if args.repo else "/check-in/"

    # The token rides in the fragment, which browsers do not send to servers.
    # It never appears in an access log, ours or Cloudflare's.
    print(f"{args.site}{path}#claim={token}")
    print(file=sys.stderr)
    print(f"  for      {payload['email']}", file=sys.stderr)
    if args.repo:
        print(f"  site     {payload['repo']}", file=sys.stderr)
        print("  NOTE     anyone who opens this link can bind a device.",
              file=sys.stderr)
        print("           Keep --days short for these.", file=sys.stderr)
    print(f"  expires  {time.strftime('%Y-%m-%d', time.localtime(payload['exp']))}",
          file=sys.stderr)
    print(f"  key      {key_id}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MintError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
