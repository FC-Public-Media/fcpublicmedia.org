#!/usr/bin/env python3
"""Nothing that lives in the site but is not the site reaches the public.

`bin/` and `site/tests/` are inside `site/` on purpose — the syncs write `_data/`,
the browser tests drive the built pages, and both belong in the context they
serve. Neither is content. `_config.yml` excludes them, and this asserts that
the exclusion actually worked rather than trusting that somebody remembered it.

WHY A TEST AND NOT A CAREFUL HABIT. The old `exclude:` list named eleven
documents one by one, and three of them still reached a public URL — not
because anybody was careless, but because a list you have to extend is a list
that will eventually be one entry short. The current list is two directories
and needs no extending. This check is what makes that claim checkable: rename a
directory, add a third one, upgrade Jekyll into different exclude semantics,
and the build says so instead of the internet finding out.

    python3 site/bin/test_nothing_internal_is_published.py

Skips when there is no `_site`, the same bargain `test_no_secrets.py` makes: a
check that cannot run says so rather than passing.
"""

import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parent.parent
REPO = SOURCE.parent
SITE = REPO / "_site"

# Directories under `site/` that are excluded from the build.
INTERNAL = ["bin", "tests"]

# Endings that would betray one of them even if the directory itself were
# flattened or renamed on the way out.
NEVER_PUBLISHED = (".py", ".spec.js", "package-lock.json", "playwright.config.js")


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
        """The whole verbatim-copy class, as one assertion.

        Jekyll renders a page with front matter to `index.html`. A `.md` file in
        `_site` therefore cannot be a page — it is a source file that was copied
        verbatim, which is how MANIFEST.md, REDIRECTS.md and RESERVE-DESIGN.md
        each reached a public URL, and how `site/README.md` did on 2026-09-17.

        This is deliberately not a list of filenames. It does not need updating
        when somebody adds a document, which is the property the old `exclude:`
        list did not have.
        """
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
        # A guard that cannot fail proves nothing. The suffix list has to
        # actually match the things it is guarding.
        for sample in ("sync-feeds.py", "smoke.spec.js", "playwright.config.js"):
            self.assertTrue(
                sample.endswith(NEVER_PUBLISHED),
                f"{sample} is in the site but would not be caught",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
