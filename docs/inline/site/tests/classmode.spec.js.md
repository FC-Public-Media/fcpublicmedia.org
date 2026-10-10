# `site/tests/classmode.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Class mode is entirely a function of the wall clock, so the clock is mocked.
Without that these tests would only pass in August 2026 between six and
eight in the evening, which is not a test.

Session times come from site/_data/classes.yml. Podcasting 101 runs
2026-08-11 18:00–20:00 in Denver, which is 2026-08-12 00:00–02:00 UTC.
lead_minutes is 90, late_minutes is 45.

## 2

Above `await expect(page.locator('.hero-qr img')).toBeVisible();`

The QR is unconditional. It is the same code for a class and for a bay,
so a day with no class on it is still a day someone walks in and scans.

## 3

Above `await visitAt(page, at(20));`

The whole reason class mode moved out of a band further down the page.
Someone standing in the doorway holding a phone should not scroll to
learn that the thing they walked in for is running — so this asserts
the position, not just the presence. On a phone the card is ordered
above the headline for the same reason.

## 4

Above `const qr = await page.locator('a.hero-qr').boundingBox();`

And the code goes with it. On a phone the class displaces the headline
rather than the QR — someone who came for the class still has to be
able to check in without scrolling.

## 5

Above `const join = page.locator('[data-class-join]');`

Deliberately a bare link. The check-in page reaches the same conclusion
from the same data, so putting the class in the URL would create a
second place for the answer to live — and a link that could be shared
hours later still claiming a class is on. It also means the QR on the
door never has to be reprinted for a class.

## 6

Above `const requests = [];`

Scoped to the main frame rather than to a list of third-party hosts.

The Cablecast player iframe pulls in its own dependencies — video.js
from a CDN, and a Stripe pricing script — on hosts nobody here chose or
can predict. Those belong to the embed's frame, not ours. Filtering by
frame captures the real distinction: what *this page* asked for. A
maintained host list would have to be updated every time a vendor adds
a dependency, and would go quietly wrong when it wasn't.

## 7

Above `if (request.isNavigationRequest()) return;`

The page's own document is not a fetch. Said as "is this the
navigation?" rather than by matching the test server's hostname,
which was how this previously broke when the host changed.

## 8

Above `if (isThirdParty(url)) return;`

The on-air strip legitimately calls Cablecast from this frame. That is
a different feature; the frame check alone would flag it.
