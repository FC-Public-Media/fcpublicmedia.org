# `site/tests/claims.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Email claims, checked across the seam.

site/bin/mint-claim.py signs with openssl. site/assets/js/claims.js verifies with
WebCrypto. Those are two different implementations of the same standard,
joined by a hand-written DER conversion, and the failure mode is a token
that looks perfect and verifies nowhere.

So these tests mint real tokens with the real script and verify them in a
real browser. Nothing is stubbed in the middle, because the middle is the
part that can be wrong.

## 2

Above `const token = tokenFrom(mint(['--key', keyPath, '--email', 'Someone@Example.COM']));`

Two people typing the same address differently must not become two
records. Normalising once, at the source, is what makes the token itself
the canonical form.

## 3

Above `const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com', '--days', '1']));`

The distinction is the whole reason expiry is checked after the
signature: one means "ask for a new link", the other means "something is
wrong". Telling someone their genuine link was tampered with sends them
to the wrong place.

## 4

Above `const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));`

Links already sitting in inboxes have to keep working, which is the only
reason the config holds a list instead of a key.

## 5

Above `const token = tokenFrom(mint(['--key', keyPath, '--email', 'someone@example.com']));`

The shipped state. A site with no keys must reject rather than wave
things through.

## 6

Above `await withKey(page);`

It is stored by now, and a URL still carrying it is one someone might
paste into a group chat, handing their address to everyone in it.

## 7

Above `await expect(page.locator('#profile-email')).toBeVisible();`

Still able to type an address by hand — a broken link must not be a
dead end.

## 8

Above `await page.goto('/check-in/');`

No keys are configured on the shipped site, so this is the state
everyone is actually in. It must not read as an error.

## 9

Above `await page.clock.setFixedTime(new Date('2026-08-03T18:00:00Z'));`

The distinction has to survive into the history, or the record claims
more than it knows.
