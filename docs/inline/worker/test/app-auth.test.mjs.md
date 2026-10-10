# `worker/test/app-auth.test.mjs`

Moved out of the file. Unreviewed.

## 1

Above `import { strict as assert } from 'node:assert';`

Being a GitHub App.

The JWT is signed with a real RSA key and verified against its public half,
because a broker that assembled the claims wrongly would look exactly like
one that got them right — until the first real request, at which point the
only symptom is "401 Bad credentials" and no indication of which field.

## 2

Above `const { save } = await setUp({`

What GitHub's download button hands you. WebCrypto's own error is
"Invalid keyData", which tells nobody anything.

## 3

Above `const { save } = await setUp();`

An installation may span every member site. What comes out of it here
never does.

## 4

Above `const { hub, save } = await setUp({ installed: [] });`

The same answer as "this site was revoked", which is the point of
revoking by uninstalling.

## 5

Above `const { save } = await setUp({ token: 'ghp_leftover' });`

A token left behind from an afternoon of trying this out must not quietly
remain the thing in use.
