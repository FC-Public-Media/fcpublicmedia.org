# `site/tests/playwright.config.js`

Moved out of the file. Unreviewed.

## 1

Above `const { defineConfig, devices } = require('@playwright/test');`

Playwright configuration for the smoke tests.

Two ways to run:

  npm test                 build _site first, serve it locally, test that
  npm run test:live        test the deployed site instead

The local server is Python's http.server because it needs no dependency and
serves directory index files, which is all Jekyll output requires. It does
not do custom 404 pages or redirects — those are host behavior, so the
tests that cover them only run against a real deployment.

## 2

Above `workers: process.env.CI ? '100%' : undefined,`

Playwright defaults to half the machine's cores, which on a standard
GitHub runner is two of four — so a suite marked fullyParallel spent most
of its time not being parallel. Locally, `undefined` keeps the default:
saturating a laptop that is also running an editor is not a kindness.

## 3

Above `reporter: process.env.CI`

The html reporter is what the failure artifact in CI is made of — without
it the upload step finds nothing to upload, which is the situation you
least want when a test only fails on the runner.

## 4

Above `baseURL: BASE_URL || http://localhost:${LOCAL_PORT},`

localhost rather than 127.0.0.1, and not interchangeably: WebAuthn
requires the origin to have a valid *domain*, and an IP literal is not
one. Passkey creation on 127.0.0.1 fails with "This is an invalid
domain" while working fine in production, which is the worst kind of
environment-only difference. localhost is special-cased by the spec.

## 5

Above `trace: 'retain-on-failure',`

On failure, keep enough to diagnose without re-running — which is the
whole point when the thing that broke only breaks on a phone.

## 6

Above `video: 'on-first-retry',`

`on-first-retry`, NOT `retain-on-failure`, and the difference is the
whole reason this run got slow.

`retain-on-failure` does not mean "record when it fails" — it cannot,
because nothing knows a test will fail until it has. It records EVERY
test, start to finish, and deletes the file when the test passes. The
cost is paid on the ninety-nine that pass, for the one that does not.

`retries: 1` is already set below, so a failing test runs a second time
and that is the run worth watching anyway. Recording only there keeps
the diagnosis and stops paying for it on every green run.

## 7

Above `command: python3 -m http.server ${LOCAL_PORT} --directory ../_site,`

Bound to all interfaces rather than 127.0.0.1 so it answers on
localhost whether that resolves to IPv4 or IPv6 — which differs
between a laptop and a CI runner.
