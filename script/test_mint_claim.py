#!/usr/bin/env python3
"""Tests for mint-claim.py.

The part worth testing is the DER-to-raw signature conversion. Everything else
is openssl doing its job, but that conversion is hand-written, and getting it
wrong produces a token that looks perfectly fine and fails to verify in a
browser — the exact failure that is miserable to diagnose from a phone.

    python3 script/test_mint_claim.py

Run alongside the browser-side check in tests/claims.spec.js, which verifies
the same tokens through WebCrypto itself.
"""

import base64
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

# The script has a hyphen in its name, so it cannot be imported normally.
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mint_claim", HERE / "mint-claim.py")
mint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mint)


class DerToRaw(unittest.TestCase):
    def test_pads_short_integers_to_32_bytes(self):
        # r = 0x01, s = 0x02: minimally encoded by openssl, fixed-width here.
        der = bytes([0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02])
        raw = mint.der_to_raw(der)

        self.assertEqual(len(raw), 64)
        self.assertEqual(raw[:32], b"\x00" * 31 + b"\x01")
        self.assertEqual(raw[32:], b"\x00" * 31 + b"\x02")

    def test_strips_the_sign_byte_openssl_adds(self):
        # A 32-byte value whose top bit is set gets a leading zero in DER, so
        # the INTEGER is 33 bytes. Keeping that byte would push r into 33 bytes
        # and shift s by one — a signature that verifies nowhere.
        value = b"\xff" + b"\x11" * 31
        der = bytes([0x30, 0x46, 0x02, 0x21, 0x00]) + value + bytes([0x02, 0x21, 0x00]) + value
        raw = mint.der_to_raw(der)

        self.assertEqual(len(raw), 64)
        self.assertEqual(raw[:32], value)
        self.assertEqual(raw[32:], value)

    def test_rejects_a_non_sequence(self):
        with self.assertRaises(mint.MintError):
            mint.der_to_raw(b"\x02\x01\x01\x00\x00\x00\x00\x00")

    def test_rejects_trailing_bytes(self):
        der = bytes([0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02]) + b"\x00"
        with self.assertRaises(mint.MintError):
            mint.der_to_raw(der)

    def test_rejects_an_oversized_integer(self):
        value = b"\x11" * 33
        der = bytes([0x30, 0x46, 0x02, 0x21]) + value + bytes([0x02, 0x01, 0x01])
        with self.assertRaises(mint.MintError):
            mint.der_to_raw(der)


class Base64Url(unittest.TestCase):
    def test_round_trips_every_padding_length(self):
        for size in range(1, 8):
            raw = bytes(range(size))
            self.assertEqual(mint.unb64u(mint.b64u(raw)), raw)

    def test_has_no_padding_or_url_unsafe_characters(self):
        # 0xfb 0xff encodes to characters that differ between the two alphabets.
        text = mint.b64u(b"\xfb\xff\xfe")
        self.assertNotIn("=", text)
        self.assertNotIn("+", text)
        self.assertNotIn("/", text)


class WithKey(unittest.TestCase):
    """Tests that need a real signing key."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.key = os.path.join(cls.tmp.name, "test-key.pem")
        cls.block = mint.new_key(cls.key)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_public_block_is_two_32_byte_coordinates(self):
        for axis in ("x", "y"):
            self.assertEqual(len(mint.unb64u(self.block[axis])), 32)

    def test_private_key_is_not_world_readable(self):
        self.assertEqual(os.stat(self.key).st_mode & 0o077, 0)

    def test_refuses_to_overwrite_an_existing_key(self):
        # Overwriting silently would invalidate every claim already mailed out.
        with self.assertRaises(mint.MintError):
            mint.new_key(self.key)

    def test_claim_carries_the_address_and_an_expiry(self):
        token, payload = mint.build_claim(self.key, "Someone@Example.com", 30, "k1")

        self.assertEqual(payload["email"], "someone@example.com")
        self.assertEqual(payload["exp"] - payload["iat"], 30 * 86400)
        self.assertEqual(payload["kid"], "k1")

        version, body, signature = token.split(".")
        self.assertEqual(version, "v1")
        self.assertEqual(json.loads(mint.unb64u(body)), payload)
        self.assertEqual(len(mint.unb64u(signature)), 64)

    def test_rejects_something_that_is_not_an_address(self):
        for bad in ("nobody", "@example.com", "someone@", ""):
            with self.assertRaises(mint.MintError):
                mint.build_claim(self.key, bad, 30, "k1")

    def test_signature_verifies_against_the_published_key(self):
        """The full round trip, checked with openssl rather than our own code.

        Signing and verifying with the same hand-written helper would pass
        happily while producing something no browser accepts, so this rebuilds
        the DER form independently and asks openssl.
        """
        token, _ = mint.build_claim(self.key, "someone@example.com", 30, "k1")
        version, body, signature = token.split(".")
        raw = mint.unb64u(signature)

        der = _raw_to_der(raw)
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as handle:
            handle.write(der)
            sig_path = handle.name

        try:
            pub = os.path.join(self.tmp.name, "pub.pem")
            with open(pub, "wb") as out:
                out.write(mint.openssl(["ec", "-in", self.key, "-pubout"]))

            result = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", pub, "-signature", sig_path],
                input=f"{version}.{body}".encode(),
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            os.unlink(sig_path)

    def test_a_tampered_payload_stops_verifying(self):
        token, _ = mint.build_claim(self.key, "someone@example.com", 30, "k1")
        version, body, signature = token.split(".")

        forged = mint.b64u(
            json.dumps(
                {"email": "someoneelse@example.com", "iat": 0, "exp": 9999999999, "kid": "k1"},
                separators=(",", ":"),
                sort_keys=True,
            ).encode()
        )

        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as handle:
            handle.write(_raw_to_der(mint.unb64u(signature)))
            sig_path = handle.name

        try:
            pub = os.path.join(self.tmp.name, "pub2.pem")
            with open(pub, "wb") as out:
                out.write(mint.openssl(["ec", "-in", self.key, "-pubout"]))

            result = subprocess.run(
                ["openssl", "dgst", "-sha256", "-verify", pub, "-signature", sig_path],
                input=f"{version}.{forged}".encode(),
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
        finally:
            os.unlink(sig_path)


def _raw_to_der(raw):
    """The inverse of der_to_raw, written separately so the test is a check."""

    def encode(value):
        trimmed = value.lstrip(b"\x00") or b"\x00"
        if trimmed[0] & 0x80:
            trimmed = b"\x00" + trimmed
        return bytes([0x02, len(trimmed)]) + trimmed

    body = encode(raw[:32]) + encode(raw[32:])
    return bytes([0x30, len(body)]) + body


if __name__ == "__main__":
    unittest.main(verbosity=2)
