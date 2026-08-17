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

    def test_prose_about_keys_is_not_mistaken_for_one(self):
        # The README and several data files discuss rk_live_ and sk_live_ at
        # length. If those tripped it, the check would be turned off within a
        # week, which is the failure mode worth designing against.
        for prose in ("rk_live_…", "use the rk_ key", "sk_live_ keys are dangerous", "`pk_live_…`"):
            self.assertIsNone(SECRET.search(prose), f"{prose!r} was treated as a key")


if __name__ == "__main__":
    unittest.main()
