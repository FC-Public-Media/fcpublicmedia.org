# `site/tests/meet-board.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

The board — a section of /meet/, not a page.

It stopped being its own page because it is one of the ways you meet this
place, not a destination beside it. Its one job is unchanged: make "you can
come to a board meeting" actionable. The tests below are about that, plus
the three states it ships in — no schedule, no roster, no minutes link —
which are what everyone will see until someone fills them in, and which
must not read as a broken page.

## 2

Above `await page.goto('/meet/');`

FCPM is a 501(c)(3), not a public body. Colorado's Open Meetings Law
covers state and local government and does not reach a nonprofit board,
so language implying statutory compliance would be a misstatement — and
an easy one to introduce while editing copy that sounds civic.

## 3

Above `await page.goto('/meet/');`

Someone who assumes a recording exists may speak differently in the
room, and it is why the minutes are the only record.

## 4

Above `await page.goto('/meet/');`

With no folder linked — the shipped state — the page must still route
someone somewhere rather than mentioning minutes and stopping.

## 5

Above `await page.goto('/meet/');`

An invitation with no date is not an invitation. This is the state the
page ships in, so the gap has to be loud enough that someone closes it.

## 6

Above `await page.goto('/meet/');`

The previous version of this rendered one card per placeholder, so a
live page displayed "TODO" three times.

## 7

Above `await page.goto('/meet/');`

A heading with no list under it reads as neglect and invites the exact
question it was meant to answer.

## 8

Above `await page.goto('/about/');`

Merging it into /meet/ must not strand the board content — someone
looking for governance will still start at /about/, and the link has to
land on the section rather than on a page that no longer exists.

## 9

Above `await expect(page.locator('.site-nav a[href="/meet/"]')).toHaveCount(1);`

In the header now, not the footer. Meet is a section of the site, and
the board is a heading inside it.

## 10

Above `await page.goto('/meet/');`

Three places link to #the-board. An anchor is silently broken in a way
a 404 is not — the page loads, it just does not go anywhere.
