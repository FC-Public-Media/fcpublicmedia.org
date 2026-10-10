# `worker/test/broker.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

The broker end to end: routing, challenges, device lookup, and what each
failure tells the page.

Driven through Request and Response rather than by calling the handlers, so
the statuses and the CORS headers are covered too. A 500 that should have
been a 403 is a real bug — the page shows a different thing for each.

## 2

Above `const service = broker({});`

The escalation this exists to stop: a workflow runs with the
repository's secrets, so writing one is using all of them.

## 3

Above `const credential = await makeCredential();`

A page that treats "GitHub had a bad minute" as "your device is not
authorized" sends somebody off to register a passkey they already have.

## 4

Above `const proof = await challengeFor(service, { action: 'verify', repo: REPO });`

It can still prove it exists, which is what tells the member the
difference between "we have never seen this phone" and "wait for us".

## 5

Above `const jane = await makeCredential();`

Both repositories are real and both devices are registered on their own
site. The question is whether naming the other one in the request body
can move the lookup — it must not, or a member of one site could spend
their own signature against another.
