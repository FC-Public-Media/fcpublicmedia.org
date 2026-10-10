# `worker/src/index.js`

Moved out of the file. Unreviewed.

## 1

Above `import { appCredential, patCredential } from './app-auth.js';`

The broker.

A small service that does the things a static site cannot do for itself:
hand out challenges, and decide whether a signature over one is genuine.

WHAT IT IS FOR
--------------
Everything on the site up to now has been honest about proving nothing.
/authorize/ makes a passkey and shows you the record. /settings/ signs in
with that passkey and then hands you your own edited file to email us,
because the sign-in happened entirely in the visitor's browser, using a
challenge the visitor's browser generated, checked by code the visitor
controls. It is wayfinding. It is not evidence.

This is where it becomes evidence. The challenge comes from here, is bound
to one specific thing being asked for, and is spent once. The signature is
checked here, against a public key recorded in the member's repository, by
code the visitor cannot reach.

WHAT IT DELIBERATELY DOES NOT HOLD
----------------------------------
No password, no session, no user table. The only durable state is a set of
challenges that expire in five minutes. Who may do what lives in each
member's own repository, in public, where they can read it.

ONE VERIFICATION, FIVE THINGS DONE WITH IT
------------------------------------------
/verify reports, /write commits, /bind and /device change who may act, and
/upload signs permission to put bytes somewhere. All five run the same
authorize() first and none of them re-implements a step of it, which is why
each new one was a small addition rather than a second system.

## 2

Above `import { verifyClaim } from '../../site/assets/js/claims.js';`

The claim verifier the BROWSER uses, imported rather than copied.

It is pure WebCrypto with no DOM at the top level, so it runs here
unmodified — and one implementation cannot drift from the other, which for a
signature check is worth more than the tidiness of a self-contained worker
directory. site/tests/claims.spec.js drives the same file from a browser, and
enrol.test.mjs imports it here to catch the day somebody adds a `window`.

## 3

Above `function corsHeaders(request, origins) {`

CORS, restricted to the origins the site is actually served from.

A wildcard would work and would also let any page anywhere ask this broker
for a challenge. The challenge would be useless to them — the assertion has
to come from a passkey bound to our domain, and the origin inside the signed
client data is checked — but there is no reason to answer at all.

## 4

Above `function readConfig(env, now = () => Date.now()) {`

Read the settings, or say precisely what is missing.

A broker with no RP ID configured would compare every passkey against the
hash of an empty string and reject all of them; a broker with no origins
would reject every ceremony. Both are safe failures, and both look like
"passkeys are broken" for a day. Refusing to start with a message naming the
variable is cheaper than that.

## 5

Above `writeMode: env.WRITE_MODE === 'direct' ? 'direct' : 'branch',`

Where a write lands. Read here rather than sent by the page, because
"commit straight to the live branch" is not a member's decision to make.

## 6

Above `claimKeys: readClaimKeys(env.CLAIM_KEYS),`

The public halves of the claim signing keys, same list as
site/_data/identity.yml. Public by nature — they verify, they do not sign —
so they are config rather than a secret.

## 7

Above `storage:`

Nothing here is optional: an endpoint with no bucket, or keys with no
endpoint, is a half-configured broker that would fail at the moment
somebody had already chosen a file.

## 8

Above `stripe: (env.PUBLIC_STRIPE_API_KEY || env.STRIPE_KEY || '').trim() || null,`

The Stripe key. A RESTRICTED key — rk_live_… — with permission to write
Checkout Sessions and nothing else, which is what Stripe now recommends
over sk_ for exactly this reason: if this worker is ever compromised,
the key it holds cannot issue refunds, read the customer list, or move
the balance. Booqable holds its own separate credential for the rental
side, so neither system can act as the other.

WHAT "PUBLIC" MEANS IN PUBLIC_STRIPE_API_KEY.

Not "safe to publish". It names WHO CAUSES THIS KEY TO BE USED, which
is the more useful question. /checkout takes no passkey and
authenticates nobody — a stranger on the internet makes this key act,
every time. So it is restricted to exactly what a stranger may cause:
writing a Checkout Session, and nothing else. No refunds, no customer
list, no balance.

The name is a standing instruction to whoever scopes the next one. A
credential named PUBLIC_ is one the public can trigger, so its
permissions must stay inside what the public may do — if this endpoint
ever needs to read a customer or issue a credit, that is a signal to
stop and use a different key, not to widen this one.

The value is still a secret and must never be rendered into a page,
logged, or returned in a response. site/_data/payments.yml holds the
genuinely publishable pk_ key, and site/bin/test_no_secrets.py fails the
build if anything shaped like a secret key reaches the built site.

Staff-run work does NOT use this key. site/bin/reprice-subscriptions.py
lists and updates subscriptions, which is far outside what a stranger
may cause, so it reads its own credential.

STRIPE_KEY is still read as a fallback so a Cloudflare secret set under
the obvious name keeps working.

Absent from `missing` deliberately. A broker that refused to hand out
challenges because nobody had set up payments yet would take the
passkey work offline for a configuration step unrelated to it; /checkout
reports this, and only /checkout.

## 9

Above `uploadTtl: Number(env.UPLOAD_TTL || 21600),`

Long enough for a big file on a slow line to finish, since the signature
has to outlive the whole transfer rather than just the request.

## 10

Above `function readClaimKeys(value) {`

Parse CLAIM_KEYS, and treat a broken value as no keys at all.

Refusing every enrolment with "not configured" is the right failure for a
malformed list. Verifying against a half-parsed one is not.

## 11

Above `async function handleChallenge(request, { config, challenges }) {`

Issue a challenge for one declared action.

Nothing is authenticated here on purpose. Handing out a random number that
expires in five minutes costs nothing and reveals nothing — the only thing
it can be used for is a signature by a passkey we already recorded.

## 12

Above `if (intent.intent.action === 'upload.grant') {`

Where an upload will land is decided HERE and stored with the challenge,
so it is settled before anybody signs and cannot be renegotiated after.
The prefix comes from the repository the challenge is for, which is what
stops one member writing into another's space.

## 13

Above `intent: intent.intent,`

Echoed so a page can show what it is about to ask someone to approve,
and so a mismatch is visible rather than mysterious.

## 14

Above `async function authorize(request, { config, challenges, devices }) {`

Everything that has to be true before anything happens.

The order below is the whole design in miniature:

  1. Spend the challenge. Gone whatever happens next.
  2. Find the recorded key, in the repository the CHALLENGE named — never
     the one the request names. The request's copy is checked against it
     afterwards, but it is not what the lookup is done with.
  3. Verify the signature.
  4. Only then, check the request does what the challenge was issued for.
  5. And that the device is allowed to do it, which is a different question
     from whether it is registered.

Returns { ok: true, body, intent, device } or { ok: false, response }. Every
endpoint that does anything goes through here first, and none of them may
re-implement a step of it — a second copy of this order is a second chance
to get it subtly wrong.

## 15

Above `let presented;`

The challenge is read out of the signed client data rather than taken as
a separate field, so there is no way to present one challenge and answer
a different one.

## 16

Above `if (ACTIONS[intent.action]?.unlisted) {`

device.add is signed by a device that is not on the list yet, so none of
what follows can be done for it. /bind handles that case with its own
rules; nothing else may, and a challenge for it presented here is spent
and refused rather than quietly reinterpreted.

## 17

Above `return refuse({ credential: 500, unreachable: 503 }[found.reason] || 403, {`

Three different kinds of "no": our setup, their outage, and an actual
refusal. Only the last one is about the person asking.

## 18

Above `if (intent.action !== 'verify' && !mayPublish(found.device)) {`

Listed and proven, but that is not permission. An action that changes the
site needs the record to say so; `verify` does not, which is what makes it
useful for telling somebody they are bound but not yet allowed.

## 19

Above `performed: false,`

Said out loud, because a page that treats a verification as a save would
tell somebody their edit went through when nothing has been written.

## 20

Above `async function handleWrite(request, deps) {`

Check an assertion and then do what it was for.

Every meaningful decision has already been made by the time this runs. What
is left is the write itself and the vocabulary for reporting how it went —
which is the shape the remaining two jobs should take too.

## 21

Above `const message = Update ${intent.path} from ${describe(device).label};`

Names the device rather than the person: the device record is the only
thing we actually know, and a commit message that guessed at a name would
be inventing it.

## 22

Above `const status = { conflict: 409, credential: 500 }[written.reason] || 502;`

Three different things, and they are not the member's fault in the same
way. A conflict is the SHA doing its job — somebody changed the file
while they were editing, and the page keeps their text and offers a
reload. A credential failure is our setup, including "the App is not
installed here", which is what a revoked site looks like from in here.

## 23

Above `repeated: written.repeated === true,`

True when the bytes were already there — a double tap, or a retry of a
request whose answer never arrived. Nothing changed this time, and the
page can say so instead of implying a second save.

## 24

Above `async function handleUpload(request, deps) {`

Hand back permission to put one file in storage.

The same authorization as everything else, and then a set of signed URLs.
The bytes never come here — the broker is not a proxy at any size, which is
the only way six gigabytes is a sensible thing to ask of it.

## 25

Above `const DEVICES = '.auth/devices.json';`

The broker chooses this path. It is never sent by a page, and intent.js
refuses it as a settings target, so there is no route by which somebody
edits the list of who may edit.

## 26

Above `async function readDevices(repositories, repo) {`

Read the device list for writing.

Authenticated, so it is current — the cached raw.githubusercontent copy that
devices.js reads is fine for "does this key check out" and is not fine as
the first half of a read-modify-write.

## 27

Above `async function handleBind(request, { config, challenges, repositories }) {`

Put a new passkey on a site's list.

The odd one out, because the device signing is the one being added and so is
not on the list to be looked up. Three things have to hold:

  1. The challenge was issued for this credential and this public key.
  2. A signature over it verifies against THAT PUBLIC KEY — proof the asker
     holds the private half of the thing they want recorded, rather than
     somebody else's key they copied off a public device list.
  3. A current claim, signed by us, naming this repository.

The claim is the enrolment authority and can be forwarded. That is fine and
intended: what arrives is a listed device that may not publish, unless it is
the first, in which case there is nobody to approve it and nobody to protect
it from. See enroll.js.

## 28

Above `const proved = await verifyAssertion({`

Against the key in the INTENT, not one looked up anywhere. This is the
only place in the broker that verifies against a key it was handed, and it
is sound because the only thing it establishes is possession — the right
to be recorded comes from the claim below.

## 29

Above `if (claim.payload.repo !== intent.repo) {`

The claim names the site it enrols for. Without this check any claim would
enrol against any site, which is the whole grant.

## 30

Above `may_publish: added.granted,`

The one thing the page has to say out loud. "You're set up" and "ask
whoever runs this site to approve your phone" are different messages.

## 31

Above `async function handleDevice(request, deps) {`

Approve or revoke a device, signed by one that may already publish.

Goes through authorize() unchanged: the signer has to be listed, proven, and
allowed. That is exactly the check this needs, which is why there is no
second copy of it here.

## 32

Above `if (change.already) {`

Already in the asked-for state. Nothing to write, and reporting a failure
for something that is already true would send somebody looking for a
problem that is not there.

## 33

Above `async function handleCheckout(request, { config, fetchImpl }) {`

Start a checkout.

THE ONE ENDPOINT HERE THAT DOES NOT AUTHENTICATE ANYBODY
-------------------------------------------------------
Every other route runs authorize() first, because every other route changes
something of ours — a file, a device list, permission to write bytes. This
one takes money from a stranger, which is a thing strangers are supposed to
be able to do. Requiring a passkey to join would mean you had to be a member
to become one.

So the protection is not "who are you". It is that there is nothing here
worth attacking: the caller picks from a fixed list, the amount comes from
our side of the wire, and the worst a hostile caller achieves is a Stripe
page nobody pays. No card details pass through this worker at any point —
Stripe hosts the form, which is the entire reason to use Checkout rather
than build one.

## 34

Above `'Idempotency-Key': crypto.randomUUID(),`

Stripe replays a repeated key rather than charging twice. The window
is 24 hours, so this is scoped to the visit rather than to the item:
somebody who genuinely buys two memberships an hour apart must get two
sessions, and somebody whose phone retried the same tap must not.

## 35

Above `console.error('stripe', response.status, payload?.error?.message || '');`

Stripe's message names the parameter and is written for a developer, so
it goes to the log and not to the visitor. What a visitor can act on is
that it did not work and it was not their fault.

## 36

Above `export function createBroker(env, { fetchImpl, now } = {}) {`

Build the worker. Dependencies are injectable so the tests can run the whole
thing — routing, CORS, statuses and all — without KV or GitHub.

## 37

Above `const credential = env.GITHUB_APP_ID`

Absent from readConfig's `missing` on purpose: /challenge and /verify work
without any of this, and a broker that refuses to prove anything because
it cannot write is worse than one that can do the half it is set up for.
/write reports it, and only /write.

The App wins whenever both are configured, so a personal token left behind
from an afternoon of trying this out cannot quietly remain the thing in
use. See app-auth.js for why that ordering is not arbitrary.

## 38

Above `const devices = deviceList({`

Read the device list through the API when there is a credential for it.
The cached raw copy is minutes behind, which would mean a revoked device
still working and — the one that would read as the feature being broken —
an owner who just bound their own phone unable to approve anybody yet.
