# `site/tests/embeds.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Tests for things hosted by someone else: the Cablecast player, show pages,
and thumbnails.

These need network access and will fail if Cablecast is down, which is why
they are separated from smoke.spec.js. Skip them with:

    npx playwright test --grep-invert @external

Why these exist at all: Cablecast's viewer is a single-page app. Requesting
a show that does not exist still returns HTTP 200 and a full HTML shell —
verified with /internetchannel/show/999999. So checking status codes proves
nothing about whether a link works. The only way to know is to render the
page and look for the player.

## 2

Above `await expect(page.locator('video')).toBeAttached({ timeout: 30_000 });`

The player is injected by the SPA, so wait for the element rather than
trusting the response.

## 3

Above `const content = page.frameLocator('iframe[src*="watch-live-embed"]');`

Confirm the iframe actually produced a document rather than a blocked
or errored frame.

## 4

Above `const sample = [hrefs[0], hrefs[Math.floor(hrefs.length / 2)], hrefs[hrefs.length - 1]];`

A sample, not all 1,060 — enough to catch a wrong URL shape, which is
the failure mode that matters. A per-show data problem is Cablecast's
to fix, not this site's.

## 5

Above `await expect(`

The SPA renders something show-shaped: a heading or a player. If the
URL pattern were wrong we would get the shell and nothing else.

## 6

Above `if (response.status() >= 400 && ![403, 405, 429].includes(response.status())) {`

403 and 429 are what social networks return to automated clients;
they mean "we saw you", not "this link is wrong".
