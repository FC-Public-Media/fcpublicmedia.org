# `site/bin/test_nothing_internal_is_published.py`

Moved out of the file. Unreviewed.

## 1

Above `import pathlib`

Nothing that lives in the site but is not the site reaches the public.

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

## 2

Above `NEVER_PUBLISHED = (`

Endings that would betray one of them even if the directory itself were
flattened or renamed on the way out.

## 3

Above `"wrangler.jsonc",`

Apparatus that moved INTO the source when the build root became `site/`.
`wrangler.jsonc` reached the output the first time it was built here,
which is the whole argument for this file existing.

## 4

Above `leaked = sorted(`

The whole verbatim-copy class, as one assertion.

Jekyll renders a page with front matter to `index.html`. A `.md` file in
`_site` therefore cannot be a page — it is a source file that was copied
verbatim, which is how MANIFEST.md, REDIRECTS.md and RESERVE-DESIGN.md
each reached a public URL, and how `site/README.md` did on 2026-09-17.

This is deliberately not a list of filenames. It does not need updating
when somebody adds a document, which is the property the old `exclude:`
list did not have.

## 5

Above `for sample in (`

A guard that cannot fail proves nothing. The suffix list has to
actually match the things it is guarding.
