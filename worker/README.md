# Broker

`fcpm-broker`, a Cloudflare Worker apart from the site's assets-only one. It verifies passkey
signatures over challenges it issued, writes to member repositories as a GitHub App, signs upload URLs
and starts Stripe checkouts. No user table: see [`docs/identity.md`](../docs/identity.md) and
[`docs/payments.md`](../docs/payments.md).

## Routes

All `POST` with JSON (`OPTIONS` answers CORS for `ORIGINS` only).

| Route | Does | Needs |
|---|---|---|
| `/challenge` | Issues a challenge bound to a declared intent, good once for `CHALLENGE_TTL` | Nothing |
| `/verify` | Checks an assertion; answers `performed: false` | Assertion |
| `/write` | Checks, then writes one file (`settings.write`) | Assertion, App |
| `/bind` | Adds a passkey to a site's list (`device.add`) | Claim + new-key signature, App, `CLAIM_KEYS` |
| `/device` | Approves or revokes a listed device | Assertion from a publishing device, App |
| `/upload` | Returns presigned R2 URLs for one file (`upload.grant`) | Assertion, R2 |
| `/checkout` | `{ sku, recurring, success_path, cancel_path, reference, email }` → `{ ok, url, id }` | `PUBLIC_STRIPE_API_KEY`; else 503 |

`/checkout` prices the SKU from `src/prices.js` (unknown: 400) and returns only to paths on the first
of `ORIGINS` (defaults `/thanks/` and `/membership/`). No card data passes through the broker.

Every route but `/challenge`, `/bind` and `/checkout` runs `authorize()` in `src/index.js`, in this
order: spend the challenge (read from the signed client data); find the device in the repository the
**challenge** named; verify the signature (`src/webauthn.js`); check the request matches the declared
intent (`matchesIntent`); require `may_publish` for anything but `verify`.

Intents are declared in `src/intent.js` `ACTIONS`; adding an action there makes it requestable.

| Action | Declares | User verification |
|---|---|---|
| `verify` | — | No |
| `settings.write` | `path`, `sha` (blob SHA or empty), `content_hash` (SHA-256, base64url) | Yes |
| `device.add` | `credential_id`, `public_key` | Yes |
| `device.allow`, `device.revoke` | `credential_id` | Yes |
| `upload.grant` | `filename`, `size` | Yes |

Every challenge names a `repo` under `OWNER`. Paths under `.github/` and `.auth/` are never written.

## Answers

`409 conflict`: the blob SHA moved under the member. `200` with `repeated: true`: the bytes were
already there (a retry). `403` carries a `reason` (`challenge`, `unknown-device`, `not-allowed`,
`signature`, `claim`…). `500` names missing configuration; `502`/`503` mean GitHub or R2 failed.

## Writes and uploads

- `WRITE_MODE=branch` commits to `settings/<hash>` and opens a pull request, so the member repository's
  checks run first; `direct` commits to the default branch. Device-list writes are always direct.
- `/bind`: the first device on a site with no publisher arrives with `may_publish: true`; later ones
  wait for `/device`. The last publisher cannot be revoked.
- `/upload` binds the grant (repo, object key, size), not the bytes, which go straight to R2. Keys are
  `<site>/<year>/<slug>-<random>.<ext>`, chosen at challenge time. Above 4 GiB the broker starts a
  multipart upload and presigns every part (64 MiB default, at most 1000), `complete` and `abort`.
- The bucket needs CORS allowing PUT, POST and DELETE from `ORIGINS` and exposing `ETag`, and a
  lifecycle rule aborting incomplete multipart uploads.

## Configuration

Vars in `wrangler.jsonc`: `RP_ID` (registrable domain; equals `rp_id` in `site/_data/authorize.yml`),
`ORIGINS` (exact, comma-separated; CORS and the signed origin), `OWNER`, `CHALLENGE_TTL` (300),
`WRITE_MODE` (`branch`), `CLAIM_KEYS` (JSON public keys, same as `site/_data/identity.yml`),
`R2_ENDPOINT`, `R2_BUCKET`, `R2_MAX_BYTES` (`0` = no cap), `UPLOAD_TTL` (21600). The broker refuses
every request until `RP_ID`, `ORIGINS` and the `CHALLENGES` KV binding exist.

The `CHALLENGES` namespace id is committed. Never set it to `""`: wrangler then refuses every command,
including the `kv namespace create` that makes one. To replace it, delete the block first.

Secrets, set with `npx wrangler secret put <NAME>`: `GITHUB_APP_ID`, `GITHUB_APP_KEY`,
`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (one bucket, object read and write), `PUBLIC_STRIPE_API_KEY`
(`STRIPE_KEY` is a fallback). `GITHUB_TOKEN` works as a stopgap; the App wins when both are set.

### GitHub App

Create it under the organization with Contents (write), Pull requests (write), Metadata (read), and
never Workflows, so GitHub itself refuses writes to `.github/`. Install it on member repositories;
uninstalling revokes a site. Each token is minted per repository with those two permissions and held
only in isolate memory. GitHub's key download is PKCS#1, which WebCrypto cannot read; convert it once:
`openssl pkcs8 -topk8 -nocrypt -in app.private-key.pem -out app.pkcs8.pem`. With a credential,
device lists are read through the API; without one, from raw.githubusercontent, which caches for minutes.

## Run

In `worker/`: `npm test` (`node --test`, no dependencies, no network), `npx wrangler dev`,
`npx wrangler deploy`. The tests sign with real P-256 and RSA keys, encode DER independently of the
decoder, and check SigV4 against AWS's published example. `.github/workflows/broker.yml` runs them on
every push to `main` touching `worker/`, then deploys and sets `PUBLIC_STRIPE_API_KEY` once
`CLOUDFLARE_API_TOKEN` exists (Cloudflare → My Profile → API Tokens → *Edit Cloudflare Workers*).
