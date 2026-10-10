# `site/tests/settings.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Editing a member site's settings.

The claim this page makes is that editing raw text preserves the comments
that document the settings, where a form would strip them. That claim is
worth testing, because it is the entire reason the page is a textarea and
the pull to "just make it a form" will be constant.

GitHub is stubbed rather than called. The tests are about what the page
does with a response, and hitting a rate-limited public API from CI to
learn that would be both slow and flaky.

## 2

Above `const SETTINGS = # Everything a member can change about their site.`

A settings file shaped like the real one: mostly commentary, with the
values scattered through it. If an editor cannot round-trip this, it cannot
round-trip the thing members actually have.

## 3

Above `async function withBroker(page, { write } = {}) {`

Point the page at a broker, and stand in for it.

The signature cannot be checked here — there is no private key on this side
of the virtual authenticator — but the thing worth checking can be: that the
page signed the challenge THIS stub issued rather than one of its own. That
is the entire difference between the broker mattering and not.

Returns the record of what the page asked for and what it sent back.

## 4

Above `const clientData = JSON.parse(`

Read the challenge back out of the signed client data, which is the
only copy the page could not have swapped.

## 5

Above `async function signedIn(page, options) {`

Sign in and, unless a load failure is being tested, wait for the editor to
actually hold the file.

Without that wait this races: inputValue() on a not-yet-populated textarea
returns an empty string rather than waiting, so a test that reads the file
and edits it would fill in nothing and then be told nothing had changed.
It passed in isolation and failed under parallel load, which is the worst
way for a test to be wrong.

## 6

Above `await signedIn(page, { status: 403 });`

Unauthenticated requests are capped per address and a shared network
can exhaust it. "Try again later" is the actual fix here, so saying it
plainly is not a brush-off.

## 7

Above `await signedIn(page);`

The whole argument for a textarea over a form. Those comments are the
only documentation a member has for what these settings do.

## 8

Above `await signedIn(page);`

A form would round-trip through a parser and strip all of these on the
first save. This is the regression that would be invisible until a
member needed the documentation and it had gone.

## 9

Above `await signedIn(page);`

Deleting one on purpose is legitimate; deleting one by pasting over the
top is not, and only the member can tell which happened.

## 10

Above `const seen = await withBroker(page);`

The whole point of the broker. A page that generates its own challenge
proves nothing to anybody, and the difference is invisible from the
outside — both flows show the same prompt and both succeed.

## 11

Above `const seen = await withBroker(page);`

The binding only works if the hash declared before the prompt describes
the bytes sent after it. Nothing else in the system notices if these
two drift apart — the broker would simply start refusing every save.

## 12

Above `await expect(page.locator('[data-state="manual"]')).toBeVisible();`

The edit survives as something the member can send us by hand. This is
the state the page was in before the broker existed, which is exactly
why it is worth keeping.
