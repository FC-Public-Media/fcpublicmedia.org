# `site/tests/theme.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Which colours, and who decides.

TWO RULES THIS FILE EXISTS TO HOLD.

1. LIGHT IS THE DEFAULT, including for a visitor whose system is dark. That
   is a deliberate reversal — the site used to follow the system — and it is
   exactly the kind of thing somebody "helpfully" restores later on the
   assumption that following the system is always correct. It is not correct
   here: the dark scheme reads as drab and most visitors were being handed
   the weaker of the two without being asked.

2. THE SETTING IS A TOGGLE, not a palette picker. Follow the system, or do
   not. There is deliberately no explicit "dark", because it differs from
   "follow" only for somebody whose system is light but who wants a dark
   site anyway — a small group who mostly own a dark system already.

## 2

Above `await expect(page.locator('[data-theme-input]')).not.toBeChecked();`

And the control says so, rather than showing an unset state on a page
that plainly has a colour.

## 3

Above `await page.goto('/watch/');`

Across a navigation, and without a flash — the head sets the attribute
before anything paints, which is why that script is inline rather than
in theme.js.

## 4

Above `const context = await browser.newContext({ colorScheme: 'dark' });`

The way back matters: without it, somebody on a dark machine who tried
the toggle would have no route to the default.

## 5

Above `const context = await browser.newContext({ colorScheme: 'light' });`

On a machine already set to light, matching the system means light, so
pressing this would change nothing. A control that visibly does nothing
reads as broken and leaves the visitor wondering what they missed, so it
is simply not there.

## 6

Above `const context = await browser.newContext({ colorScheme: 'light' });`

The light-laptop-at-noon case. The control shows up once it means
something, and the page does NOT change on its own — nobody asked for
dark, and deciding for them is the thing this whole setting avoids.

## 7

Above `const context = await browser.newContext({ colorScheme: 'dark' });`

The three-way this replaced could store `dark`. Anything that is not an
explicit `light` counts as following, which is the closest surviving
intent for somebody who had chosen dark.

## 8

Above `const context = await browser.newContext({ colorScheme: 'dark' });`

Reading localStorage THROWS when storage is blocked rather than
returning null, and blocking it is a real setting real people turn on.

## 9

Above `await page.locator('[data-theme-input]').check();`

The toggle still works for the life of the page. It forgets on the next
navigation, which is a smaller loss than being nagged about it.
