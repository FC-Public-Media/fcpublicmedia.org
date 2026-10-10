# `site/tests/meet.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

The community page.

Its job is to answer "when can I turn up" and "where is everyone" without
making a visitor know which data file a thing lives in. Three sources merge
into one list, so the tests below are mostly about that merge behaving —
chronological, forward-looking, and not lying when it is empty.

## 2

Above `function classSessions() {`

Class sessions as the build sees them, with when they start.

The start time is read as well as the title, and that is the whole point of
this helper. The page shows only what has not happened yet — deliberately,
and there is a test below for it — so a version of this that returned every
title asserted that history is on display, and passed only until the first
session went by. It did exactly that: "Podcasting 101" was on a Tuesday and
this went red on the Wednesday, in CI, on a change about colours.

## 3

Above `const notice = (message) => test.info().annotations.push({ type: 'stale-content', description: messa`

An empty calendar is a REAL STATE, not a broken one, and the page says so
deliberately — see the "Nothing on the calendar right now" branch in site/meet.md.

These tests used to assert there was always something upcoming, so that a
stale site/_data/classes.yml went red. The intention was good and the effect was
not: every session went into the past, and the suite sat red for eighteen
hours over a content problem while real regressions — class mode being dead
on the homepage, two 404s in the internal links — hid in the same wall of
failures. That is the same argument the workflow already makes for the
@external tests: a suite that goes red for reasons outside the change is a
suite people stop reading.

So staleness is ANNOTATED rather than asserted. It shows up on the run,
where someone can act on it, without gating a deploy. What is asserted is
behaviour: whatever the data says, the page renders it correctly.

## 4

Above `await expect(page.locator('main')).toContainText('Nothing on the calendar right now');`

The empty state has to be the written one, not an empty list. A heading
with nothing under it reads as abandoned; this reads as quiet.

## 5

Above `await page.goto('/meet/');`

The merge exists so a class is listed here by virtue of being a class.
If this breaks, the fix people reach for is to copy the session into
community.yml, and then the two quietly disagree forever.

## 6

Above `await page.goto('/meet/');`

The sort key is epoch seconds rather than the ISO string, because two
events either side of a DST change carry different offsets.

## 7

Above `await page.goto('/meet/');`

A calendar full of last spring is worse than an empty one — it reads as
abandoned rather than quiet.

## 8

Above `await page.goto('/meet/');`

Merging sources means losing the context a single-purpose page would
have given for free, so each row has to carry it.

## 9

Above `await page.goto('/meet/');`

A malformed offset in a data file renders as "Invalid Date" rather than
failing the build, which is exactly the kind of thing nobody notices.

## 10

Above `await page.goto('/meet/');`

The chat platform is unsettled — Slack today, possibly Teams. Naming one
without a working link invites "where is it, then?", which is the one
question this section exists to prevent. Entries with no URL are meant
to be skipped entirely, and this is what proves it.

## 11

Above `await page.goto('/meet/');`

The shipped state, and the one that has to do the work: nobody has sent
a feed yet, so the section's whole job is to ask for one. An empty
heading with nothing under it would ask for nothing.

## 12

Above `await page.goto('/meet/');`

Feed content is third-party. If items are present, none of them may
introduce a script, an event handler, or a non-http link — the two
halves of the defence are stripping in sync-feeds.py and | escape in
the template, and this checks the result rather than either half.

## 13

Above `await page.goto('/meet/');`

A member site marks a program `scheduled` with a future drop date, and
that date rides into the feed as its pubDate. Before the split, those
arrived here announcing something as published on the day it was still
being finished.

## 14

Above `await page.goto('/meet/');`

A feed entry carries where the finished file lives. That is for us — a
page announcing something is coming has no business publishing the path
to an unreleased master.

## 15

Above `await page.goto('/meet/');`

Plenty of feeds are sloppy about dates, and guessing that undated means
upcoming would put a whole back catalogue under "coming up".

## 16

Above `await page.goto('/meet/');`

The page should not just describe a community; it should be possible to
act from it. Membership, classes, and the open board meeting are the
three that cost a newcomer the least.
