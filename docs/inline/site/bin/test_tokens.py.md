# `site/bin/test_tokens.py`

Moved out of the file. Unreviewed.

## 1

Above `import pathlib`

The contrast rules the palette cannot enforce on its own.

The brand sheet states the constraint plainly: yellow on ink passes at 11.7:1,
ink on yellow passes, and yellow on paper FAILS. The first two are pleasant
facts. The third is the one that needs guarding, because it fails in a
particular way — a rule reading `color: var(--signal)` looks entirely
reasonable to whoever writes it, renders as pale yellow on cream, and is
invisible to everybody who is not the author looking at their own screen.

There were nine of those in this file before the palette changed. They were
fine when the signal colour was red and became unreadable the moment it
became yellow, which is exactly the kind of breakage a token swap is supposed
to be safe from and is not.

So the rule is mechanical: yellow is a surface. It may be a background, a
border, an outline, a mark. It is never `color:`.

## 2

Above `text = CSS.read_text(encoding="utf-8")`

The palette as declared, for whichever block is asked for.

Sliced rather than scanned whole. Every token is declared twice — once in
:root and again under the dark scheme — and a dict built from the whole
file keeps whichever came last, which silently pairs the light yellow
against the dark ink and reports 1.3:1. The test failed for that reason
before this did the slicing, which is a good argument for the slicing.

## 3

Above `marker = ':root[data-theme="dark"]'`

Sliced at the SELECTOR, not at "prefers-color-scheme: dark". The dark
palette is chosen by attribute now so that a visitor can override it —
a media query cannot be overridden, which is why "follow my system" was
impossible before. The old marker still appears in this file, but only
inside the comment explaining that, so slicing on it would have kept
working by luck and broken the day somebody reworded a comment.

## 4

Above `offenders = []`

`border-color` and `background-color` are fine and common, so the
lookbehind is doing real work here rather than being decorative.

## 5

Above `palette = tokens()`

The reason --record-ink exists. The brand red is 4.1:1 on paper,
which fails AA for the small bold labels that need it most — an
on-air badge is the last text you want people squinting at.

## 6

Above `palette = tokens()`

It is the one surface that does not invert with the colour scheme,
so it has to stand up on its own in both.

## 7

Above `palette = tokens("dark")`

Dark mode redefines these, and a palette that passes in one scheme
and fails in the other is the half nobody checks.

## 8

Above `self.assertGreaterEqual(contrast(palette["--signal"], palette["--paper"]), 4.5)`

Here yellow finally IS safe as text, which is the point of it
surviving the inversion unchanged.

## 9

Above `include = CSS.parent.parent.parent / "_includes" / "countdown.html"`

A spinner with no name is a silence, and somebody waiting deserves
to be told that is what they are doing.
