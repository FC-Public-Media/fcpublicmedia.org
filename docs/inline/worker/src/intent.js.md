# `worker/src/intent.js`

Moved out of the file. Unreviewed.

## 1

Above `const HASH_ALGORITHM = 'SHA-256';`

What a signature is for.

WHY A CHALLENGE IS NOT JUST A NONCE HERE
----------------------------------------
The obvious broker issues a random challenge, checks the assertion, and then
does whatever the request asks for. That makes a verified assertion a bearer
token: whoever holds it can spend it on any action, because the signature
says nothing about what was being agreed to.

So a challenge is issued FOR something. The page declares the action first —
this file, this SHA, content hashing to this — and gets a challenge bound to
that declaration. When the assertion comes back, the request has to match
what was declared, byte for byte. The member's device signed a challenge
that means one specific edit and nothing else.

The cost is one extra round trip before the passkey prompt. It buys the
difference between "this person is authorized" and "this person authorized
THIS", and only the second one is worth having.

## 2

Above `if (owner && parts[0].toLowerCase() !== owner.toLowerCase()) {`

Set an owner and the broker will not touch anything outside it. Without
this the repo is just a string from the page, and the only thing stopping
a request naming somebody else's repository is that the lookup would fail
— which is true today and stops being true the moment a token is added.

## 3

Above `const FORBIDDEN_PREFIXES = ['.github/', '.auth/'];`

Paths the broker refuses to write no matter who asks.

.github/ is the one that matters: a workflow file runs with the
repository's secrets, so permission to write one is permission to use every
credential the repository holds. An editor for a tagline must never be a
route to that.

.auth/ is the device list. It is the broker's own bookkeeping and changing
it is how you would add yourself; it has its own flow, with its own rules.

## 4

Above `export const ACTIONS = {`

Every action the broker knows, and what has to be declared to ask for one.

Add an action here and it becomes requestable. Nothing else in this file
needs to change — which is the point, so that adding one is a decision made
in one visible place rather than a branch buried in a handler.

## 5

Above `verify: {`

Prove a device is bound to a site. Writes nothing. This is what a page
uses to find out whether to show an editor at all.

## 6

Above `'settings.write': {`

Replace one file in the member's own repository with content the page
declared the hash of. `sha` is the blob SHA the page read; sending it back
is what makes GitHub refuse the write if somebody else edited in between.

## 7

Above `'device.add': {`

Put a new passkey on the site's list. The signature answering this one
comes from the NEW device — it is proof that whoever is asking holds the
key they are asking us to record, and nothing more. Authority to enrol is
the claim, checked separately.

Deliberately survivable when the claim link was forwarded: being listed
does nothing on its own. See enroll.js.

## 8

Above `'device.allow': {`

Let a listed device publish, or stop it. Signed by an existing device that
may already publish — the owner approving a co-producer's phone from their
own phone, with staff nowhere in it.

## 9

Above `'upload.grant': {`

Permission to put one file in object storage.

Note what is NOT declared: a content hash. The broker never sees these
bytes — they go straight from the browser to R2 — and hashing six
gigabytes before starting would roughly double the wait to protect
something we could not check anyway. What the signature binds to is the
grant: this member, this site, this object, this size. See r2.js.

## 10

Above `export function readIntent(body, { owner = '', maxUpload = 0 } = {}) {`

Turn a request body into an intent, or say why not.

Returns { ok: true, intent } or { ok: false, detail }. Everything here came
from a page and none of it is trusted, including the shape.

## 11

Above `if (value !== '' && !/^[0-9a-f]{40}$/.test(String(value ?? ''))) {`

Empty means "there is no file there yet", which is a legitimate first
write. Anything else has to look like a blob SHA.

## 12

Above `if (typeof value !== 'string' || !value || value.length > 200) {`

Only ever used to build a slug, never as a path — but a name carrying
separators or a leading dot is a sign of something other than a file
being picked, and refusing it costs nothing.

## 13

Above `if (field === 'credential_id' || field === 'public_key') {`

These end up in a JSON file in somebody's repository, so the shape is
checked here rather than trusted to survive a round trip. base64url and
nothing else — a credential ID is 16 to 32 bytes and an SPKI key is a
few hundred, so anything longer is not what it says it is.

## 14

Above `export async function matchesIntent(intent, body) {`

Does the finished request do what the challenge was issued for?

Called after the signature checks out. Every declared field has to be
present and identical — a request that changed its mind between asking for
the challenge and using it did not get that challenge signed for this.

## 15

Above `if (typeof body?.content !== 'string') {`

The page declared a hash; here is where the actual bytes turn up. If
they hash to something else, the device signed for different content.
