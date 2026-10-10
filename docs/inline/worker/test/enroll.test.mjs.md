# `worker/test/enroll.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

Binding devices, and approving them.

The rule under test is the one in DESIGN-NOTES: enrolment and authority are
different things. A claim link can be forwarded, and that is survivable only
because forwarding it gets somebody LISTED and nothing more. If that ever
stops being true, the whole reason staff can leave the loop goes with it.

The claims here are minted by site/bin/mint-claim.py — the real script, run as
a subprocess — rather than assembled by the test. The broker's claim
checking is worth nothing if it agrees with a fixture instead of with the
thing that actually issues links.

## 2

Above `const listed = [{ credential_id: 'a'.repeat(20), public_key: 'k', may_publish: false }];`

A site whose only devices are listed-but-not-allowed has nobody who could
approve anything, so the next to arrive is still the first that matters.

## 3

Above `const only = [{ credential_id: 'a'.repeat(20), may_publish: true }];`

Doing it would leave a site nobody can change, and the way back is staff
editing the file by hand. Refusing is kinder than allowing.

## 4

Above `const jane = await makeCredential();`

The link is the same link. Forwarding it is expected. What it buys is a
device that cannot change anything until somebody says so.

## 5

Above `const jane = await makeCredential();`

Device lists are public, so anybody can read a key out of one. Binding it
needs the private half, which is the point of signing the challenge with
the key being registered.

## 6

Above `const claims = await import('../../site/assets/js/claims.js');`

index.js imports site/assets/js/claims.js rather than keeping a second copy.
The day somebody adds a top-level `window` to that file, this fails here
instead of in production.
