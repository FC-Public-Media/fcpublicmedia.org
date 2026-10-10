# `site/tests/membership.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Membership: the rules, and finding your own nonprofit.

The feedback behind this page is that the pricing is hard to understand —
and it is the rules that are hard, not the amounts. So the first tests here
are about whether the rules are actually stated, which is the kind of thing
that quietly rots when somebody rearranges a page.

The rest are about the lookup, whose whole job is to stop being a gate. Most
of what can go wrong with it — no matches, a failed download, no JavaScript
— has to leave somebody a way through, because plenty of real organizations
are legitimately not on the IRS list.

## 2

Above `await page.goto('/membership/');`

The old site said both "January 1 – December 31" and "one year from
sign-up". This is the one that is true, and saying it is the whole point
of the section.

## 3

Above `await page.goto('/membership/');`

Both were real rules people remember. Leaving them unstated is how
somebody ends up arguing about a half-year price at the front desk.

## 4

Above `await page.goto('/membership/');`

"Some of our people know that nonprofits pay half" is the failure being
fixed: a discount only the informed got.

## 5

Above `await withList(page);`

Nobody types the first two words of an organization's name. They type
the two they remember.

## 6

Above `await withList(page);`

The list is Larimer County 501(c)(3)s. A new organization, a chapter, or
one under a fiscal sponsor is legitimately absent, and being told "no"
would be the lookup doing harm.

## 7

Above `const context = await browser.newContext({ javaScriptEnabled: false });`

A search box that does nothing when typed into is worse than no search
box. The contact route is plain HTML and survives.

## 8

Above `const response = await page.request.get('/assets/nonprofits.json');`

Against the committed file rather than a stub: the sync script and this
page agree on a format, and nothing else would notice them diverging.
