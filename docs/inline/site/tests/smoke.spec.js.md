# `site/tests/smoke.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Smoke tests: does every page load without anything visibly broken?

These run against local output by default and need no network. They are the
ones that should stay green all the time.

The point of these is to surface failures that are invisible in normal use —
especially on a phone, where there is no console to look at.

## 2

Above `function watch(page) {`

Attach listeners before navigating and return the collected problems.
Third-party failures are kept separate: an outage at Cablecast is not the
same event as a link we got wrong, and conflating them makes the suite
flaky enough that people stop trusting it.

## 3

Above `const source = message.location()?.url || '';`

Console messages from inside an embedded iframe surface on the parent
page's console, so a third-party player's internal errors would
otherwise fail an assertion about our own code.

The concrete case: headless Chromium ships without the codecs for HLS,
so the Cablecast player reliably logs
"VIDEOJS: ERROR: (CODE:4 MEDIA_ERR_SRC_NOT_SUPPORTED)" on any runner
that can reach the network. That is a property of the test browser, not
a broken embed — whether the player actually mounts is asserted in
embeds.spec.js, where it belongs.

## 4

Above `test('no page shows its own markup as text', async ({ page }) => {`

Markup that leaked onto the page as words.

Liquid's whitespace-trimming comment tags eat the newlines either side of
themselves. Put one between a Markdown heading and a block of HTML and
kramdown receives them as ONE line — it reads the whole thing as heading
text and escapes the tag. `By category<ul class="rows rows-tight">` appeared
on /watch/ that way and no test noticed, because to every check we had it
was simply a heading with an unusual name.

Only headings and prose are looked at. Several pages legitimately show
markup — /settings/ and /authorize/ display YAML and JSON in <pre> — and a
check that read the whole document would have to be turned off for them,
which is how a guard stops guarding.

## 5

Above `if (problems.thirdPartyFailures.length) {`

Third-party trouble is recorded on the test rather than asserted on,
so it shows up in the report without turning the run red because
someone else's server had a bad minute.

## 6

Above `await expect(page).toHaveTitle(/^[^\s—|-].*[^\s—|-]$/);`

Not just "has a title" — a title must not begin or end with a
separator. The homepage rendered as " — Fort Collins Public Media"
because an empty string is truthy in Liquid, and a bare /\S/ check
was happy with it.

## 7

Above `const headings = page.locator('h1');`

At most one, not exactly one. Pages under site/_layouts/page.html carry no
h1: the masthead prints the menu word instead, which costs no height.
Accessibility will want a heading here eventually — that is a known,
deliberate debt, not an oversight. Pages that do have one (the
homepage, a show, a podcast, the 404) must still have exactly one.

## 8

Above `const blankLinks = await page.$$eval('a', (links) =>`

Every link needs something clickable in it. This is what catches
data problems like a catalog record with no title rendering as an
invisible link.

## 9

Above `const overflow = await page.evaluate(() => {`

The classic mobile bug: something a few pixels too wide makes the
whole page pan, and it is easy to miss unless you look for it.

## 10

Above `const filter = page.locator('#archive-filter');`

The filter box is hidden until its script runs, so its visibility is
itself the assertion that the script loaded.

## 11

Above `test.describe('hosted forms', () => {`

---------------------------------------------------------------------------
The two pages that frame a hosted form. Nothing is configured yet, so what
matters is that the unconfigured state is visible rather than a blank space,
and that the page never leaves someone with no way forward.

## 12

Above `await expect(notice).toContainText('Anyone can respond');`

The instruction that stops someone shipping a form that breaks on
iPhones has to survive edits to this page.

## 13

Above `const onward = await page.$$eval('main a[href^="/"]', (as) => as.length);`

An unconfigured form page must not be a dead end. Two specific things
rather than a link count, which would only measure how chatty the
copy happens to be: somewhere else on the site to go, and a way to
reach a human.

## 14

Above `test.describe('archive airing history', () => {`

---------------------------------------------------------------------------
Airing history on the archive.

Cablecast records every run, so this is a join rather than something the
site tracks. What is worth testing is the part that is easy to get quietly
wrong: the join itself (a Liquid lookup that returns nothing rather than
complaining when the key type is off), and the sort, which has to flatten
the category grouping to be useful at all.

## 15

Above `await page.goto('/watch/archive/');`

The Liquid join indexes a JSON object by a stringified id. Get that
wrong and every row silently reads "not aired this year" — a page that
looks fine and is entirely wrong.

## 16

Above `await page.goto('/watch/archive/');`

A program nobody has run in two years is interesting regardless of the
heading it happens to sit under, so sorting cannot stay inside groups.

## 17

Above `await page.goto('/watch/archive/');`

The rows are moved between lists, so "back" has to be a real restore
rather than an approximation — losing one would lose a program.
