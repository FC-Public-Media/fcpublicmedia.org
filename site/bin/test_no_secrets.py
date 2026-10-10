#!/usr/bin/env python3
"""see docs/inline/site/bin/test_no_secrets.py.md#1"""

import pathlib
import re
import subprocess
import sys
import unittest

# see docs/inline/site/bin/test_no_secrets.py.md#2
SOURCE = pathlib.Path(__file__).resolve().parent.parent
REPO = SOURCE.parent
SITE = SOURCE / "_site"   # the build root is `site/`, so the output is inside it

# see docs/inline/site/bin/test_no_secrets.py.md#3
SECRET = re.compile(r"\b(?:rk|sk)_(?:live|test|org)_[A-Za-z0-9]{8,}")

# see docs/inline/site/bin/test_no_secrets.py.md#4

# see docs/inline/site/bin/test_no_secrets.py.md#5
WIFI_KEY = re.compile(r"WIFI:" + r"[^\n]{0,300}?;" + r"P:[^;\n]+;")

# see docs/inline/site/bin/test_no_secrets.py.md#6
WIFI_QR = "site/assets/img/wifi-qr.svg"


def tracked_files():
    """see docs/inline/site/bin/test_no_secrets.py.md#7"""
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    )
    return [REPO / name for name in result.stdout.splitlines() if name]


def hits(paths):
    found = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # a font or an image cannot hold a key we would ever read
        for match in SECRET.findall(text):
            found.append(f"{path.relative_to(REPO)}: {match[:12]}…")
    return found


class NothingSecretIsPublished(unittest.TestCase):
    def test_the_built_site_carries_no_secret_key(self):
        if not SITE.exists():
            self.skipTest("no _site — run `bundle exec jekyll build` first")

        found = hits(SITE.rglob("*"))
        self.assertEqual(
            found,
            [],
            "A Stripe secret key is in the built site. Rotate it in the Stripe "
            "dashboard before anything else — it is compromised the moment "
            "this deploys:\n" + "\n".join(found),
        )

    def test_no_tracked_file_carries_a_secret_key(self):
        found = hits(tracked_files())
        self.assertEqual(
            found,
            [],
            "A Stripe secret key is committed. It is burned as soon as it is "
            "pushed — rotate it, do not merely delete the line:\n" + "\n".join(found),
        )

    def test_the_publishable_key_field_is_actually_a_publishable_key(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#8
        payments = (SOURCE / "_data" / "payments.yml").read_text(encoding="utf-8")
        declared = re.search(r"publishable_key:\s*[\"']?([^\"'\s]*)", payments)
        value = declared.group(1) if declared else ""

        if value:
            self.assertTrue(
                value.startswith("pk_"),
                f"publishable_key is {value[:8]}… — that is not a publishable key. "
                "Only pk_ belongs in a file that is rendered into public pages.",
            )

    def test_the_check_catches_a_key_when_there_is_one(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#9
        for shape in (
            "rk_live_" + "A1b2C3d4E5f6",
            "sk_test_" + "51H8xQ2zzzzzzz",
            "sk_org_" + "9kLmNoPqRsTu",
        ):
            self.assertTrue(SECRET.search(shape), f"{shape[:10]}… was not caught")

    def test_no_tracked_file_carries_a_wifi_password(self):
        found = []
        for path in tracked_files():
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if WIFI_KEY.search(text):
                found.append(str(path.relative_to(REPO)))

        self.assertEqual(
            found,
            [],
            "A Wi-Fi join payload with a password in it is committed. Change the "
            "password on the router — it is public now, and deleting the line "
            "does not remove it from git history:\n" + "\n".join(found),
        )

    def test_the_built_site_does_not_carry_the_wifi_code(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#10
        if not SITE.exists():
            self.skipTest("no _site — run `bundle exec jekyll build` first")

        stray = SITE / "assets" / "img" / "wifi-qr.svg"
        self.assertFalse(
            stray.exists(),
            "The guest Wi-Fi code is in _site. That is fine for printing the "
            "poster and NOT fine to deploy — a manual `wrangler deploy` "
            "publishes it. Before deploying:\n"
            "    rm site/assets/img/wifi-qr.svg && bundle exec jekyll build",
        )

    def test_the_generated_wifi_code_is_not_tracked(self):
        tracked = {str(path.relative_to(REPO)) for path in tracked_files()}
        self.assertNotIn(
            WIFI_QR,
            tracked,
            f"{WIFI_QR} is committed. The password is readable from it with any "
            "phone. Remove it, change the password, and see the header of "
            "site/_data/wifi.yml for why it is generated locally instead.",
        )

    def test_the_wifi_data_file_declares_no_password(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#11
        config = SOURCE / "_data" / "wifi.yml"
        if not config.exists():
            self.skipTest("no site/_data/wifi.yml")

        declared = [
            line
            for line in config.read_text(encoding="utf-8").splitlines()
            if re.match(r"\s*(password|passphrase|psk|key)\s*:\s*\S", line)
        ]
        self.assertEqual(
            declared,
            [],
            "site/_data/wifi.yml declares a password. It is rendered into a public "
            "site from a public repository; the generator takes the password "
            "from the environment for this reason:\n" + "\n".join(declared),
        )

    def test_the_wifi_check_catches_a_payload_when_there_is_one(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#12
        scheme = "WIFI:"
        for shape in (
            f"{scheme}T:WPA;S:FC Public WiFi;P:correcthorse;;",
            f"{scheme}S:Guest;T:WPA;P:hunter2;H:true;;",
            f'{scheme}T:WPA;S:Cafe\\;Guest;P:p@ss\\,word;;',
        ):
            self.assertTrue(WIFI_KEY.search(shape), f"{shape[:14]}… was not caught")

    def test_this_file_does_not_trip_its_own_wifi_check(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#13
        self.assertIsNone(
            WIFI_KEY.search(pathlib.Path(__file__).read_text(encoding="utf-8")),
            "test_no_secrets.py contains a complete WIFI: payload. Build the "
            "examples from parts instead of weakening the pattern.",
        )

    def test_wifi_prose_and_open_networks_are_not_mistaken_for_a_password(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#14
        for benign in (
            "the WIFI: scheme puts the password in a P: field",
            "WIFI:T:nopass;S:FC Public WiFi;;",
            "a WIFI: payload is not encryption",
        ):
            self.assertIsNone(WIFI_KEY.search(benign), f"{benign!r} was treated as a password")

    def test_prose_about_keys_is_not_mistaken_for_one(self):
        # see docs/inline/site/bin/test_no_secrets.py.md#15
        for prose in ("rk_live_…", "use the rk_ key", "sk_live_ keys are dangerous", "`pk_live_…`"):
            self.assertIsNone(SECRET.search(prose), f"{prose!r} was treated as a key")


if __name__ == "__main__":
    unittest.main()
