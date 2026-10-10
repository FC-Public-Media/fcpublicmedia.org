# `site/tests/upload.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Submitting an episode.

The test that matters here spans two pages: a passkey registered at
/authorize/ has to be signable-in at /upload/, and the site it belongs to
has to come back out. That is a real virtual-authenticator credential
crossing between them, because the whole mechanism is the user handle
surviving the round trip and nothing short of running it proves that.

## 2

Above `const PARSE_ENTRY = `

Parses the page's output the way the member site's build would, and reports
the failure rather than raising, so a malformed entry produces a readable
assertion instead of a stack trace from a subprocess.

## 3

Above `await withKey(page);`

The round trip. The user handle is the only thing an assertion returns
about who signed in, so the site has to survive inside it — a hash, as
this originally was, comes back unreadable and the page cannot tell
whose site to submit to.

## 4

Above `await withKey(page);`

An authenticator treats a repeated user handle as the same account and
REPLACES the credential, so a handle without a per-person part would
mean the second person silently evicted the first.

## 5

Above `});`

A cancelled sign-in is not tested behaviourally, for the same reason it
is not on /authorize/: headless Chromium with no authenticator HANGS on
credentials.get() rather than rejecting, so the test would be measuring
the harness. The property that matters — that every failure state offers
a way onward — is asserted structurally above.

## 6

Above `await signedIn(page);`

A producer submitting from another zone must not schedule their own
episode hours out. Everything on this site follows the same rule.

## 7

Above `await signedIn(page);`

The offset is not a constant, and hardcoding one would be wrong for
half the year — silently, since the timestamp still parses.

## 8

Above `const parsed = JSON.parse(`

Not a substring check. The output is pasted into a real programs.yml,
so what matters is that it PARSES and comes out the right shape —
indentation, quoting and the folded summary all have to survive, and
none of that is visible in a `toContain`.

## 9

Above `await signedIn(page);`

There is no destination configured, and pretending otherwise would
leave someone believing they had sent a file they had not.
