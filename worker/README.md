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

`/verify` answers with `performed: false`, out loud, so nothing downstream can
mistake a verification for a save. Presigning an upload to R2 and co-signing a
second device are each the same verification plus one action, which is why
`/write` was a small file and not a second system.

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

Removing a device is not instant — raw.githubusercontent serves this with cache
headers measured in minutes. Fine for "take my old phone off"; not fine for
"this was stolen an hour ago", and when that needs answering the read moves
behind an authenticated API call. `src/devices.js` says so at the point it
matters.

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
| `CHALLENGES` | KV namespace binding. `npx wrangler kv namespace create CHALLENGES`. |

`GITHUB_TOKEN` is a secret, set with `npx wrangler secret put GITHUB_TOKEN`
rather than in the config. It is the only secret in the system — every other
credential is a passkey on somebody's own phone — so it is the one thing whose
loss is not confined to one person. Fine-grained, **Contents: write** and
**Pull requests: write**, on the member repositories and nothing else. Not
Actions, not Workflows, not Secrets, not Administration. The path checks in
`intent.js` refuse `.github/` for the same reason; a token that *cannot* write
a workflow makes that a second lock rather than the only one.

`/challenge` and `/verify` work without it. A broker that refused to prove
anything because it could not write would be worse than one doing the half it
is set up for, so only `/write` complains.

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

- **The presigned upload to R2**, and **co-signing a second device**. Both are
  the same verification plus one action.
- **Rate limiting.** `/challenge` is unauthenticated by design — handing out a
  random number that expires in five minutes reveals nothing — but it is still
  a free endpoint.
- **Strictly single-use challenges.** `take()` reads and then deletes, and KV
  is eventually consistent between those. The window allows a replay of the
  *same* intent, never a different one. `src/challenges.js` works through why
  that is survivable and what to do (a Durable Object) when it stops being.
