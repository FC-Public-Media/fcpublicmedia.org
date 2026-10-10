#!/usr/bin/env python3
"""see docs/inline/site/bin/test_nothing_internal_is_published.py.md#1"""

import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parent.parent
REPO = SOURCE.parent
SITE = SOURCE / "_site"   # the build root is `site/`, so the output is inside it

# Directories under `site/` that are excluded from the build.
INTERNAL = ["bin", "tests"]

# see docs/inline/site/bin/test_nothing_internal_is_published.py.md#2
NEVER_PUBLISHED = (
    ".py",
    ".spec.js",
    "package-lock.json",
    "playwright.config.js",
    # see docs/inline/site/bin/test_nothing_internal_is_published.py.md#3
    "wrangler.jsonc",
    "Gemfile",
    "Gemfile.lock",
    "_config.yml",
)


class NothingInternalIsPublished(unittest.TestCase):
    def setUp(self):
        if not SITE.is_dir():
            self.skipTest("no _site — run `bundle exec jekyll build` first")

    def test_the_excluded_directories_are_not_in_the_output(self):
        for name in INTERNAL:
            self.assertFalse(
                (SITE / name).exists(),
                f"_site/{name}/ exists. `site/{name}/` is excluded in _config.yml "
                "and something stopped honouring it.",
            )

    def test_no_file_that_could_only_be_internal_was_published(self):
        leaked = [
            str(path.relative_to(SITE))
            for path in SITE.rglob("*")
            if path.is_file() and path.name.endswith(NEVER_PUBLISHED)
        ]
        self.assertEqual(
            leaked,
            [],
            "Files that can only have come from `site/bin/` or `site/tests/` are "
            "in the built site:\n" + "\n".join(leaked),
        )

    def test_no_markdown_survived_into_the_output(self):
        """see docs/inline/site/bin/test_nothing_internal_is_published.py.md#4"""
        leaked = sorted(
            str(path.relative_to(SITE)) for path in SITE.rglob("*.md") if path.is_file()
        )
        self.assertEqual(
            leaked,
            [],
            "Markdown was copied verbatim into the built site. A `.md` with no "
            "front matter is published at its own URL — these are readable by "
            "anyone who guesses the path:\n" + "\n".join(leaked),
        )

    def test_the_check_would_notice(self):
        # see docs/inline/site/bin/test_nothing_internal_is_published.py.md#5
        for sample in (
            "sync-feeds.py",
            "smoke.spec.js",
            "playwright.config.js",
            "wrangler.jsonc",
            "Gemfile",
            "_config.yml",
        ):
            self.assertTrue(
                sample.endswith(NEVER_PUBLISHED),
                f"{sample} is in the site but would not be caught",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
