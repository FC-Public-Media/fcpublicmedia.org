# The broker

A small Cloudflare Worker that hands out challenges and checks the signatures
made over them.

Everything else on this site is honest about proving nothing. `/authorize/`
makes a passkey and shows you the record to email us. `/settings/` signs in
with that passkey and then hands you your own edited file to send over, because
the sign-in happened entirely in the visitor's browser, against a challenge the
visitor's browser generated, checked by code the visitor controls. Useful for
wayfinding. Not evidence.

This is where it becomes evidence.

## What it does today

| | |
|---|---|
| `POST /challenge` | Declare what you want to do. Get a challenge bound to it. |
| `POST /verify` | Send the assertion. Find out whether it checks out. Changes nothing. |
| `POST /write` | Same checks, then write the file. |
| `POST /bind` | Put a new passkey on a site's list. |
| `POST /device` | Approve or revoke a listed device. |
| `POST /upload` | Sign permission to put a file in storage. |

`/verify` answers with `performed: false`, out loud, so nothing downstream can
mistake a verification for a save. All five run the same `authorize()` first
and none of them re-implements a step of it, which is why each one after the
first was a small addition rather than a second system.

### Asking for a challenge

```json
POST /challenge
{
  "action": "settings.write",
  "repo": "fcpublicmedia/janes-show",
  "path": "_data/site.yml",
  "sha": "e1b4…",
  "content_hash": "9J8k…"
}
```

```json
{ "ok": true, "challenge": "T3Vy…", "expires_in": 300, "intent": { … } }
```

The actions are listed in `src/intent.js`, with what each one has to declare.
`verify` declares nothing extra and is how a page asks "is this device
registered for this site, and may it publish?"

### Answering it

```json
POST /verify
{
  "assertion": {
    "credential_id":      "…",
    "authenticator_data": "…",
    "client_data_json":   "…",
    "signature":          "…"
  },
  "content": "name: Jane Live\n"
}
```

Base64url throughout. `assets/js/passkey.js` produces exactly this shape from
`navigator.credentials.get()`, so no page has to know the field names.

The challenge is not sent as a field. It is read out of the signed client data,
which is the only copy that cannot be swapped.

`POST /write` takes the same body and, if everything checks out, writes the
file. In `branch` mode that means a branch named after the content hash and a
pull request, so the repository's own checks see a settings file before it goes
live — a member editing raw YAML can produce something that does not parse, and
the difference between catching that and not is a message versus a dead site.

Two answers are worth reading carefully:

- `409 conflict` — the blob SHA no longer matches, so somebody changed the file
  while this member was editing. Their text is still in the textarea; the page
  offers a reload.
- `200` with `repeated: true` — the bytes were already there. A double tap, or
  a retry of a request whose answer never arrived. Reported as a repeat rather
  than a fresh save, because telling that member it failed is how you end up
  with two of everything.

## The three things that make it worth having

**The challenge is bound to an intent.** A challenge that is only a nonce turns
a verified assertion into a bearer token — whoever holds it can spend it on
anything, because the signature says nothing about what was agreed to. Here the
page declares the action first and gets a challenge for that; when the assertion
comes back, the request has to match what was declared, content hash included.
The member's device signed for one specific edit. `src/intent.js`.

**The repository comes from the challenge.** Never from the request body. The
device list is looked up in the repo the challenge was issued for, so a
signature made for one site cannot be redirected at another. The body's copy is
compared afterwards and a mismatch is a 409.

**Listed is not allowed.** Being in `.auth/devices.json` means a device exists.
Whether it may change the site is `may_publish` on the record, absent by
default. That separation is what makes a forwardable enrollment link safe — see
`_data/authorize.yml`.

## Enrolment: `/bind` and `/device`

The rule these two encode is the one in DESIGN-NOTES: **enrolment and authority
are different things.** A claim link can be forwarded, and that is survivable
only because forwarding it gets somebody *listed* and nothing more.

**`/bind`** puts a passkey on a site's list. It is the odd endpoint out,
because the device doing the signing is the one being added and so cannot be
looked up. Three things have to hold:

1. The challenge was issued for this credential ID and this public key.
2. A signature over it verifies **against that public key** — proof the asker
   holds the private half of what they want recorded, rather than a key they
   copied out of somebody's public device list.
3. A current claim, signed by us, **naming this repository**.

The claim is the enrolment authority. What arrives is a listed device that may
not publish — *unless it is the first*, in which case there is nobody to
approve it and nobody to protect it from, so it is trusted. That is "first
device free", and `enroll.js` reads it as "is there anybody who could approve?"
rather than "is the list empty", because a site whose only devices are
listed-but-not-allowed still has nobody who could say yes.

**`/device`** flips `may_publish`, or revokes. It goes through the same
`authorize()` as everything else, so the signer must be listed, proven, and
already allowed — the owner approving a co-producer's phone from their own
phone, with staff nowhere in it.

Two refusals worth knowing:

- **A device cannot approve itself.** Falls out of `authorize()` rather than
  being a special case: an unapproved device fails the `may_publish` check
  before the action is even read.
- **The last device that can publish cannot be revoked.** Doing it would leave
  a site nobody can change, and the way back is staff editing the file by hand.

Device writes are always direct, never on a branch — a grant sitting in an
unmerged pull request grants nothing.

`CLAIM_KEYS` is the public half of the claim signing keys, the same list as
`_data/identity.yml`. `src/index.js` imports the browser's own
`assets/js/claims.js` to check them rather than keeping a second copy, so the
two cannot drift; a test imports it under Node to catch the day somebody adds a
`window` reference to that file.

## Uploads: `/upload`

A finished episode is measured in gigabytes. The broker never sees any of it —
it signs URLs, the browser sends the file straight to R2, and the only thing
crossing this Worker is a few hundred bytes of JSON. Proxying would pay for the
bandwidth twice, hold the transfer open for its whole length, and turn a
resumable upload into one long request that fails whole.

**What the signature binds to here is different, on purpose.** `/write` binds
to a hash of the exact content. This cannot: hashing six gigabytes in a browser
means reading the whole file before the upload starts, roughly doubling the
wait, to protect bytes the broker never sees anyway. So an upload signature
binds to the **grant** — this member, this site, this object key, this size,
for this window.

What that costs is worth stating rather than glossing: somebody holding the URL
can put different bytes at that key. Somebody holding the URL is the member
whose device just signed for it. The exposure is a member overwriting their own
pending upload, which is a retry, not a threat.

**Where it lands is decided at challenge time**, before anybody signs, and the
prefix comes from the repository the challenge is for — so one member cannot
aim an upload into another's space, and the page does not get a say.

### Multipart

A single PUT tops out at 5 GiB. Above 4 GiB the upload is split and every part
is presigned up front, so the browser does parts → complete on its own without
coming back.

The ordering matters and is easy to get wrong: **a part URL carries `uploadId`
in its query string, and the query string is inside the signature.** There is
no signing against a placeholder and substituting the real id afterwards — that
produces URLs that are well-formed and refused. So the broker starts the
multipart upload itself first, by presigning the create call and then fetching
that URL. A presigned URL works for whoever holds it, including us, which means
this file needs one way of signing rather than two.

### SigV4

`src/sigv4.js`. Every step is exact — a query parameter sorted wrong, a path
encoded twice, a header with a stray space — and each mistake produces a
signature that is perfectly well-formed and rejected, with the service replying
only that it does not match.

So the test is a **known-answer test against the worked example in AWS's own
documentation**, signature and all. A round trip against ourselves would prove
the file agrees with itself, which was never in doubt.

The one that bit during writing: `new URL()` has already percent-encoded the
path, so running an encoder over the result turns `%20` into `%2520`. The
canonical request and the returned URL are now built from the same string, so
they cannot disagree.

## The device list

Read from the member's own repository, public, at `.auth/devices.json`:

```json
{
  "version": 1,
  "devices": [
    {
      "credential_id": "…base64url…",
      "public_key":    "…base64url SPKI…",
      "algorithm":     -7,
      "label":         "Jane's phone",
      "added":         "2026-01-14T18:22:04.117Z",
      "may_publish":   true
    }
  ]
}
```

Public keys are the half meant to be published. Anyone can read who may edit a
site; nobody can become them. A record with `"revoked": true` is skipped.

It is read **through the authenticated API whenever the broker has a
credential**, falling back to raw.githubusercontent only for a broker set up to
verify but not to write. That is not tidiness: raw serves this with cache
headers measured in minutes, so a revoked device would keep working — and,
less obviously, an owner who had just bound their own phone could not approve
anybody until the cache caught up, which would read as the feature simply not
working.

## Configuration

In `wrangler.jsonc`. The Worker refuses to answer at all, with a message naming
the variable, if any of these is missing — a broker that quietly compares every
passkey against the hash of an empty string looks like "passkeys are broken" for
a day.

| | |
|---|---|
| `RP_ID` | The domain the passkeys belong to. Must equal `rp_id` in `_data/authorize.yml`. |
| `ORIGINS` | Comma-separated origins, exact. Used for CORS *and* checked against the origin inside the signature — two different checks. |
| `OWNER` | Repositories outside this owner are refused. |
| `CHALLENGE_TTL` | Seconds. Default 300. |
| `WRITE_MODE` | `branch` (default) or `direct`. Not the page's decision to make. |
| `CLAIM_KEYS` | Claim signing public keys as JSON, same as `_data/identity.yml`. `/bind` only. |
| `R2_ENDPOINT` | `https://<account id>.r2.cloudflarestorage.com`. |
| `R2_BUCKET` | Bucket name. |
| `R2_MAX_BYTES` | Largest file accepted. `0` is no cap, which is not a decision. |
| `UPLOAD_TTL` | Seconds a signed upload URL lives. Default six hours. |
| `CHALLENGES` | KV namespace binding. `npx wrangler kv namespace create CHALLENGES`. |

Plus the App's two secrets, below.

### The credential

The passkeys mean no *member* holds a credential. They do not mean nothing
does — GitHub only accepts GitHub credentials, so something has to hold one to
write. The question is only what, how scoped, and how revocable.

It is a **GitHub App**, and its secrets are set with `wrangler secret put`
rather than living in the config:

```sh
npx wrangler secret put GITHUB_APP_ID
npx wrangler secret put GITHUB_APP_KEY
```

A personal access token belongs to a person. It outlives their interest in the
project and dies with their account, so the day somebody leaves the board is
the day member sites stop saving — and nobody will connect those two events. An
App belongs to the organization. The rest follows:

- What is stored is a **private key that signs requests for tokens**. It is not
  itself a token, so it cannot be replayed against the API.
- Tokens last an hour, are minted per write, and are **narrowed at the moment
  of minting to one repository and two permissions**. An installation covering
  forty member sites still produces a credential good for one of them.
- **Revoking a site is uninstalling the App from it.** No list to edit and no
  way to forget.
- **Workflows is not among the permissions**, so GitHub refuses a write to
  `.github/` no matter what this code does. `intent.js` refuses it too. That is
  what makes "two locks" true rather than a claim.

Permissions when creating the App: Contents (write), Pull requests (write),
Metadata (read). Nothing else. `src/app-auth.js` has the setup, including the
one `openssl` command GitHub's key format needs — it hands out PKCS#1 and
WebCrypto reads only PKCS#8, and the error for getting that wrong is
`Invalid keyData`, so the broker checks for it and says which command to run.

`GITHUB_TOKEN` is still read as a stopgap for trying this out before an App
exists. The App wins whenever both are set, so a token left behind from an
afternoon of experimenting cannot quietly remain the thing in use.

`/challenge` and `/verify` work without any of it. A broker that refused to
prove anything because it could not write would be worse than one doing the
half it is set up for, so only `/write` complains.

## Running it

```sh
cd worker
npm test          # node --test, no dependencies, no network
npx wrangler dev
npx wrangler deploy
```

The tests need nothing installed. They generate a real P-256 key, assemble real
authenticator data, and produce a real ECDSA signature, because the bugs worth
catching here are bugs of byte layout and a mock would agree with whatever the
code already does.

### The part most likely to be quietly wrong

WebAuthn's ES256 signatures are DER — a SEQUENCE of two INTEGERs. WebCrypto's
`verify()` wants the raw 64 bytes, r then s, each padded to exactly 32.
Converting means stripping the leading zero DER adds to keep an integer
positive, and padding a short scalar back out. Get it slightly wrong and about
one signature in a hundred and thirty fails while the rest pass, which reads as
a flaky authenticator for months.

`test/helpers.mjs` writes the encoder from the DER rules rather than by
inverting the decoder, so the round trip is a check and not a mirror, and the
suite signs fifty times because one signature proves nothing about the padding.

`script/mint-claim.py` has the same seam in the other direction.

## What is not built

- **Any page that uses `/bind`, `/device` or `/upload`.** The endpoints are
  here and tested; `/authorize/` and `/upload/` still hand the member their own
  record to send over.
- **Rate limiting.** `/challenge` is unauthenticated by design — handing out a
  random number that expires in five minutes reveals nothing — but it is still
  a free endpoint.
- **Strictly single-use challenges.** `take()` reads and then deletes, and KV
  is eventually consistent between those. The window allows a replay of the
  *same* intent, never a different one. `src/challenges.js` works through why
  that is survivable and what to do (a Durable Object) when it stops being.
