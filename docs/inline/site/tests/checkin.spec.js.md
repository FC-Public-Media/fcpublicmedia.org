# `site/tests/checkin.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

The check-in page is the one part of this site with real client-side state
and real conditional behaviour, so it gets real tests.

Geolocation is mocked through Playwright's context permissions and
setGeolocation, which is the only way to exercise "you are not here yet"
without standing in a car park.

## 2

Above `const NEARBY = { latitude: 40.5892, longitude: -105.0768 };`

Old Town Square, roughly 700m away — outside the 200m radius, close enough
to be a realistic "on my way" position.

## 3

Above `await expect(page.locator('#device-label')).not.toHaveValue('');`

Whatever kind of device the test runs as, it gets a word for it, and
that word is kept as the phone's name.

## 4

Above `const outbound = [];`

The promise of this page is that the visit stays on the device. If a
future change starts posting somewhere, this fails.

## 5

Above `const link = page.locator('a.hero-qr');`

The QR *is* the check-in affordance on the homepage now — the code for
whoever is being shown the phone, the link for whoever is holding it.
There is no separate card with a button beside it, because that was the
same errand offered twice.

## 6

Above `const box = await link.boundingBox();`

In the hero, so it is above the fold rather than scrolled to. That is
the point of it being there and worth failing over.

## 7

Above `const CLASS_START = Date.parse('2026-08-12T00:00:00Z');`

---------------------------------------------------------------------------
The check-in page runs the same class logic the homepage does, from the same
data. The QR on the door is a permanent link here; everything about a class
is worked out on arrival rather than encoded in what someone scanned.

## 8

Above `await page.clock.fastForward('02:20:00');`

The class window opens while they are still on the page. fastForward
rather than setFixedTime: the latter moves the clock but never fires
the interval, so nothing would re-render and the test would be
asserting against a page that never updated.
