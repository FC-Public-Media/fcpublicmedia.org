# `site/tests/authorize.spec.js`

Moved out of the file. Unreviewed.

## 1

Above `const { test, expect } = require('@playwright/test');`

Binding a device to a member site.

The passkey ceremony runs against a CDP virtual authenticator, so these are
real WebAuthn calls producing a real credential — not a stub. That matters
because the part most likely to be wrong is getting the public key back out
in a form something else can verify, and a mock would happily return
whatever shape the test expected.

## 2

Above `async function virtualAuthenticator(page) {`

Attach a virtual authenticator so credentials.create() resolves.

Chromium only, which is what this suite runs.

## 3

Above `await withKey(page);`

It is a capability — anyone who opens it can bind a device — so it must
not survive in a URL someone might paste into a group chat.

## 4

Above `await withKey(page);`

A claim with no repository proves an email but names no site. Running
the ceremony anyway would leave someone holding a passkey that
authorizes nothing.

## 5

Above `await withKey(page);`

The whole reason the repo travels inside the signature: the link is
meant to be forwarded, and a forwarded link must not be editable into
one that binds a device to somebody else's site.

## 6

Above `await withKey(page);`

The assertion that matters: the public key comes back as SPKI that
WebCrypto will import. If this passes, whatever verifies a signature
later can read the same bytes.

## 7

Above `await withKey(page);`

It goes into a repository that may be public, and a second person on
the same site should not have their address published by being added
to it. The claim already proved the address; the passkey carries it
forward without restating it.

## 8

Above `await withKey(page);`

Blank names in a list everyone else can see are how you end up unable
to tell which device to revoke.

## 9

Above `await withKey(page);`

The multi-device and two-people cases are the same code path, and both
have to yield separate credentials rather than replacing each other.

## 10

Above `await page.goto('/authorize/');`

A full load between the two. Going straight from one claim URL to the
next would change only the fragment, which the page now handles via
hashchange — but that is a different code path and is not what is
under test here.

## 11

Above `await withKey(page);`

The one ceremony failure that can be triggered honestly here. A
user-dismissed system sheet cannot: headless Chromium with no
authenticator hangs rather than rejecting, so a test for it would be
testing the harness. The dead-end property that case shares is covered
structurally below.

## 12

Above `await page.goto('/authorize/');`

Whichever way the ceremony fails, the person holding the phone needs
something to do next. Asserted over the markup rather than by driving
each failure, because some of them cannot be driven from here.

## 13

Above `await withKey(page);`

Only the fragment changes, which is not a navigation. Without a
hashchange listener the page sits there naming the wrong site, which is
the worst possible way to be wrong on this particular page.

## 14

Above `await withKey(page);`

The shipped state. The passkey is real; only the delivery is manual,
and for the first few member sites that is a genuine workflow.
