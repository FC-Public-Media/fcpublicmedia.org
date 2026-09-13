#!/usr/bin/env python3
"""Nothing secret-shaped may reach the built site, or the repository.

WHY THIS IS NOT PARANOIA
------------------------
The restricted Stripe key is named PUBLIC_STRIPE_API_KEY, where "public" names
who causes it to be used — /checkout authenticates nobody, so a stranger makes
that key act — and therefore how tightly it is scoped. It is a good name and
it is about blast radius, not visibility.

It is also a name somebody will one day read quickly, take to mean "safe to
expose", and put in a template. That is a reasonable misreading of a name that
is doing something subtler than usual, and no amount of comment prevents it.
So the guarantee is mechanical rather than documentary: whatever anybody
believed, a secret key does not reach the built site.

It is deliberately mechanical and looks at OUTPUT rather than at intent. It
does not care how a key got there: interpolated by Liquid, pasted into a data
file, hardcoded in a script, committed to a config. If a string shaped like a
Stripe secret is in _site or in the tracked source, the build fails.

WHAT COUNTS AS SECRET-SHAPED
----------------------------
    rk_live_…  rk_test_…   restricted
    sk_live_…  sk_test_…   secret
    sk_org_…               organization

`pk_live_` and `pk_test_` are absent from that list on purpose. Publishable
keys are meant to be in the page — refusing them would make this check
something people switch off, and a check people switch off protects nothing.

THE GUEST WI-FI PASSWORD IS THE SAME PROBLEM WEARING A COSTUME
--------------------------------------------------------------
A Wi-Fi QR code encodes the password as plain text. A QR is not encryption,
it is a font — `assets/img/wifi-qr.svg` committed here would publish the
guest password to anyone who points a phone at a public repository, and it
would not look like publishing a password while you did it. That is exactly
the misreading this file exists to make impossible, so the same mechanical
treatment applies: the generated code is gitignored, and these tests fail if
it, or a `WIFI:` payload, or a password field in `_data/wifi.yml`, is ever
tracked.

The poster is meant for the lobby, where everyone reading it is already in
the building. Publishing it to fcpublicmedia.org is a different decision and
FCPM has not made it. See the header of `_data/wifi.yml`.
"""

import pathlib
import re
import subprocess
import sys
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SITE = REPO / "_site"

# The underscore after the prefix matters: it is what separates a real key
# from prose about one. This very file says "rk_live_…" with an ellipsis
# rather than a plausible suffix so that it does not match itself.
SECRET = re.compile(r"\b(?:rk|sk)_(?:live|test|org)_[A-Za-z0-9]{8,}")

# Booqable access tokens and Cloudflare/R2 credentials would be just as bad,
# but they have no distinctive prefix to match on. The Stripe shapes are the
# ones that can be caught mechanically, and catching those is worth doing
# even though it is not everything.

# A Wi-Fi join payload, but only one carrying a key: `P:` with something in
# it. `WIFI:T:nopass;S:Guest;;` is an open network and discloses nothing, and
# prose about the format — which _data/wifi.yml and wifi/poster.md are full of
# — has no payload in it at all.
# Assembled rather than written out for the same reason the shapes above use
# an ellipsis: spelled in one piece, the pattern's own source is a payload and
# this file fails its own check. test_this_file_does_not_trip_its_own_wifi_check
# is what keeps that honest.
WIFI_KEY = re.compile(r"WIFI:" + r"[^\n]{0,300}?;" + r"P:[^;\n]+;")

# The generated code. Gitignored; this asserts that the gitignore is doing its
# job, because a `git add -f` or a rewritten ignore file is silent otherwise.
WIFI_QR = "assets/img/wifi-qr.svg"


def tracked_files():
    """What git actually has, rather than what is lying around.

    Scanning the working tree would trip over _site, node_modules, and any
    key somebody has sensibly kept OUT of version control in a scratch file.
    The question is what would be published, and git answers that.
    """
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
        # The specific mistake the naming invites: someone reads
        # PUBLIC_STRIPE_API_KEY, believes it, and pastes the restricted key
        # into the field that gets rendered into every page.
        payments = (REPO / "_data" / "payments.yml").read_text(encoding="utf-8")
        declared = re.search(r"publishable_key:\s*[\"']?([^\"'\s]*)", payments)
        value = declared.group(1) if declared else ""

        if value:
            self.assertTrue(
                value.startswith("pk_"),
                f"publishable_key is {value[:8]}… — that is not a publishable key. "
                "Only pk_ belongs in a file that is rendered into public pages.",
            )

    def test_the_check_catches_a_key_when_there_is_one(self):
        # A scanner that never matches passes every time and proves nothing.
        # These are not real keys; they are the shape of one.
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
        # Not the same guarantee as the tracked-file check, and this is the
        # one that catches the realistic accident. CI builds from a clean
        # checkout and so can never have the code — but README, "Deploying to
        # Cloudflare", documents `npx wrangler deploy` from a local checkout
        # as the fallback when Actions is unavailable, and it publishes
        # whatever `_site` happens to contain. Somebody who generated the
        # poster an hour earlier would ship the password without touching a
        # file that git can see.
        if not SITE.exists():
            self.skipTest("no _site — run `bundle exec jekyll build` first")

        stray = SITE / "assets" / "img" / "wifi-qr.svg"
        self.assertFalse(
            stray.exists(),
            "The guest Wi-Fi code is in _site. That is fine for printing the "
            "poster and NOT fine to deploy — a manual `wrangler deploy` "
            "publishes it. Before deploying:\n"
            "    rm assets/img/wifi-qr.svg && bundle exec jekyll build",
        )

    def test_the_generated_wifi_code_is_not_tracked(self):
        tracked = {str(path.relative_to(REPO)) for path in tracked_files()}
        self.assertNotIn(
            WIFI_QR,
            tracked,
            f"{WIFI_QR} is committed. The password is readable from it with any "
            "phone. Remove it, change the password, and see the header of "
            "_data/wifi.yml for why it is generated locally instead.",
        )

    def test_the_wifi_data_file_declares_no_password(self):
        # The specific mistake the file invites: somebody finds a config with
        # an SSID in it, reasonably expects the password next to it, and adds
        # the field the generator deliberately does not read.
        config = REPO / "_data" / "wifi.yml"
        if not config.exists():
            self.skipTest("no _data/wifi.yml")

        declared = [
            line
            for line in config.read_text(encoding="utf-8").splitlines()
            if re.match(r"\s*(password|passphrase|psk|key)\s*:\s*\S", line)
        ]
        self.assertEqual(
            declared,
            [],
            "_data/wifi.yml declares a password. It is rendered into a public "
            "site from a public repository; the generator takes the password "
            "from the environment for this reason:\n" + "\n".join(declared),
        )

    def test_the_wifi_check_catches_a_payload_when_there_is_one(self):
        # A scanner that never matches passes every time and proves nothing.
        #
        # The scheme is assembled from a name rather than written out, for the
        # same reason the Stripe shapes above use an ellipsis: a file that
        # contains a complete example payload fails its own check, and the
        # obvious fix for that is to weaken the pattern.
        scheme = "WIFI:"
        for shape in (
            f"{scheme}T:WPA;S:FC Public WiFi;P:correcthorse;;",
            f"{scheme}S:Guest;T:WPA;P:hunter2;H:true;;",
            f'{scheme}T:WPA;S:Cafe\\;Guest;P:p@ss\\,word;;',
        ):
            self.assertTrue(WIFI_KEY.search(shape), f"{shape[:14]}… was not caught")

    def test_this_file_does_not_trip_its_own_wifi_check(self):
        # Not redundant with the tracked-file sweep: this file is the one most
        # likely to acquire a literal payload, and the sweep's failure message
        # would read as a real leak when it was a test fixture.
        self.assertIsNone(
            WIFI_KEY.search(pathlib.Path(__file__).read_text(encoding="utf-8")),
            "test_no_secrets.py contains a complete WIFI: payload. Build the "
            "examples from parts instead of weakening the pattern.",
        )

    def test_wifi_prose_and_open_networks_are_not_mistaken_for_a_password(self):
        # This file, _data/wifi.yml and wifi/poster.md all discuss the format
        # at length, and an open network has nothing to disclose. If any of
        # those tripped it, the check would be switched off within a week.
        for benign in (
            "the WIFI: scheme puts the password in a P: field",
            "WIFI:T:nopass;S:FC Public WiFi;;",
            "a WIFI: payload is not encryption",
        ):
            self.assertIsNone(WIFI_KEY.search(benign), f"{benign!r} was treated as a password")

    def test_prose_about_keys_is_not_mistaken_for_one(self):
        # The README and several data files discuss rk_live_ and sk_live_ at
        # length. If those tripped it, the check would be turned off within a
        # week, which is the failure mode worth designing against.
        for prose in ("rk_live_…", "use the rk_ key", "sk_live_ keys are dangerous", "`pk_live_…`"):
            self.assertIsNone(SECRET.search(prose), f"{prose!r} was treated as a key")


if __name__ == "__main__":
    unittest.main()
