# `worker/src/app-auth.js`

Moved out of the file. Unreviewed.

## 1

Above `const API = 'https://api.github.com';`

Being a GitHub App rather than a person.

WHY NOT A PERSONAL ACCESS TOKEN
-------------------------------
A token belongs to whoever made it. It outlives their interest in the
project and dies with their account, so the day somebody leaves the board is
the day member sites stop saving — and nobody will connect those two events.
An App belongs to the organization.

The rest follows from that:

  * The stored secret is a private key that signs requests for tokens. It is
    never itself a token, so it cannot be replayed against the API.
  * The tokens it mints last an hour and are minted per write.
  * Each one is narrowed at the moment of minting to ONE repository and two
    permissions. An installation covering forty member sites still produces
    a credential good for one of them.
  * Revoking a site is uninstalling the App from it. No list to edit, and no
    way to forget.
  * Workflows are not among the permissions granted, so the API refuses a
    write to .github/ regardless of what this code does. intent.js refuses
    it too. Two locks, which is what that README claim needs to be true.

site/_data/authorize.yml said "a GitHub App installation token" from the start.
This is that.

SETUP
-----
  1. Create an App under the organization. Permissions: Contents (write),
     Pull requests (write), Metadata (read). Nothing else — especially not
     Workflows, Secrets, or Administration.
  2. Install it on the member repositories.
  3. Generate a private key. GitHub hands back PKCS#1, which WebCrypto
     cannot read, so convert it once:

       openssl pkcs8 -topk8 -nocrypt -in app.private-key.pem -out app.pkcs8.pem

  4. npx wrangler secret put GITHUB_APP_KEY   < paste app.pkcs8.pem
     npx wrangler secret put GITHUB_APP_ID    < the numeric App ID

## 2

Above `const JWT_LIFETIME = 540;`

GitHub rejects a JWT claiming more than ten minutes. Nine leaves room for
the clock skew allowance below without ever crossing the ceiling.

## 3

Above `const PERMISSIONS = { contents: 'write', pull_requests: 'write' };`

Everything the broker is allowed to do, restated at the moment of minting.
The installation may hold more; a token from here never does.

## 4

Above `async function importPrivateKey(pem) {`

Read the App's private key.

The PKCS#1 case gets its own message on purpose. GitHub's download button
produces exactly that format, WebCrypto's error for it is "Invalid keyData",
and the fix is one command that nobody guesses.

## 5

Above `iat: seconds - SKEW,`

Back-dated, because GitHub rejects a JWT issued in its future and our
clock is not their clock.

## 6

Above `export function appCredential({ appId, privateKey, fetchImpl = fetch, api = API, now = () => Date.no`

A credential source: hand it a repository, get a token good for that one.

Resolves to { ok: true, token } or { ok: false, detail }. Never throws — a
misconfigured App is something the page has to tell somebody about, not a
stack trace.

CACHING, AND WHERE IT DELIBERATELY IS NOT
-----------------------------------------
Tokens are held in memory, in the isolate, and nowhere else. Not KV. A
write credential at rest in a store that outlives the request is a worse
thing to have than the handful of extra API calls avoiding it costs. The
cache dying with the isolate is the correct lifetime.

## 7

Above `body: { repositories: [repo.split('/')[1]], permissions: PERMISSIONS },`

Narrowed here, every time. An installation spanning every member site
still yields a token that can only touch this one.

## 8

Above `export const patCredential = (token) => async () =>`

A personal access token, wrapped to look the same.

A stopgap for trying the broker out before an App exists, and the reason
index.js prefers the App whenever both are configured. Everything in the
comment at the top of this file is an argument against leaving it here.
