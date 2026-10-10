# `site/tests/contrast.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Text you can actually read.

WHY THIS EXISTS
---------------
site/bin/test_tokens.py checks the stylesheet's source for the one rule that
matters most — yellow is never a text colour. It cannot check the cascade,
and the cascade is where this went wrong.

When the masthead became a dark band it got `color: var(--masthead-ink)`,
and `.site-head a { color: inherit }` under it. But `.site-nav a` further
down the file said `color: var(--ink)`, at the same specificity and later,
so it won. --ink is the dark colour. The navigation shipped as #121417 text
on a #121417 band: present, focusable, announced correctly by a screen
reader, and invisible.

Nothing caught it. The smoke tests look for links with no accessible label,
which these had; the token test reads source, which looked fine in both
places separately. Only the computed result was wrong.

So this asks the browser. It walks the text that carries meaning, reads the
colour actually painted and the background actually behind it, and does the
arithmetic WCAG does.

## 2

Above `async function sample(page, selector) {`

Read the painted colour of each element, and what is behind it.

The background walk is the awkward part: an element usually has no
background of its own, so the colour behind it belongs to some ancestor.
Walking up until something is not transparent is what a person sees, and it
is the only way to catch a light rule sitting on a dark band.

## 3

Above `const parse = (value) => {`

Chromium reports anything touched by color-mix as
`color(srgb 0.95 0.94 0.91)` — the same colour on a 0–1 scale
rather than 0–255. Reading those as channel values makes every
light colour look almost black and invents failures, which is
exactly what it did the first time this ran.

## 4

Above `const CHECKED = [`

The chrome that appears on every page, plus a couple of pages whose own
content carries the colours most likely to be got wrong.

## 5

Above `for (const [path, name] of [['/', 'home'], ['/watch/', 'watch'], ['/membership/', 'membership']]) {`

A few pages rather than all of them. The header is one include, so a
regression is site-wide by construction and the twenty-sixth page
proves nothing the first did not — while clicking a toggle on every
one of them is slow and finds ways to be flaky.

## 6

Above `const toggle = page.locator('.nav-toggle');`

On a phone the menu is behind a toggle, so its links are hidden and
the sampler skips them — correctly, since a colour nobody is looking
at cannot be unreadable. Open it, because the links inside are
exactly the ones that shipped invisible.
