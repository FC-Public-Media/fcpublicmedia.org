# Credentials — position

**Session 2026-09-30.** Range `e63fc7b..919a413`, 51 first-parent commits (merged PRs
#64–#104 plus a handful of direct commits and two automated syncs). Last session
2026-09-10.

I speak for the person who inherits the accounts without inheriting the context.

## The one sentence

**The Slack invite has passed its own shelf life and nobody recorded an owner, and
the range removed the only reader of an account-scoped Cloudflare token without
saying whether the token itself was revoked.** Nothing was rotated in this range;
one credential lapsed on schedule and one lost its purpose.

## What moved, that my seat notices

### The Slack invite is past its date (G2)

`join.slack.com/…/shared_invite/zt-48bxcjuc1-…` is the same string it was at
`e63fc7b`; the range only moved the file to `site/_data/community.yml` (PR #69/#70
restructure) without changing the link. Last session I dated it 2026-08-28 with a
thirty-day life: **no later than 2026-09-27.** That date is behind us. I did not
probe the link — this is a reading pass — so the honest statement is "expired by its
own shelf life unless someone regenerated it off-repo", and nothing in the range says
anyone did. No owner is recorded anywhere I can read.

### `CLOUDFLARE_PAGES_TOKEN` lost its reader

Last session this was the new tenth credential (PR #59, the spare Actions deploy
path). On 2026-09-17 that workflow was **removed** (PR #80, `remove-manual-deploy`);
`docs/deploying.md` now says cloudflare's git build is the only publisher and that
"nothing here now reads `CLOUDFLARE_PAGES_TOKEN`, `CLOUDFLARE_PAGES_PROJECT` or
`CLOUDFLARE_ACCOUNT_ID` — the organization secret can go once you are satisfied no
other repository wants it." Two consequences:

- The inventory does **not** need a row for it after all. That half of last session's
  C5 closes.
- The token itself is, as far as the repository can say, **still an organisation
  secret, account-scoped, with edit rights and no consumer.** The docs leave its
  removal conditional and unowned. See C6.

`docs/TENANCY.md` also notes that a two-account factory would add credentials to that
same organisation-secret set — "the `credentials` seat gains a second account to date
and rotate." Nothing in the workflows reads a second account yet. Watching, not
claiming.

### What did not move

The workflows' full secret surface at the tip: `AZURE_STATIC_WEB_APPS_API_TOKEN`,
`CLOUDFLARE_API_TOKEN` (broker), `PUBLIC_STRIPE_API_KEY`, and the automatic
`GITHUB_TOKEN`. No new secret name entered any workflow in this range, including the
new `publish-member-sites.yml`. `docs/ADVOCATE.md` still lists the Stripe key as two
credentials (C5). Nothing in the range gives any credential an owner or a rotation
date.

## Earliest possible age, and no later evidence

| Credential | Reference first appears | Later evidence of rotation |
| --- | --- | --- |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | 2026-07-31 | none (still referenced in `deploy.yml`) |
| `GITHUB_APP_ID` / `GITHUB_APP_KEY` | 2026-08-05 | none |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | 2026-08-05 | none |
| `CLOUDFLARE_API_TOKEN` | 2026-08-17 | none |
| `STRIPE_KEY` / `PUBLIC_STRIPE_API_KEY` (one credential, two names) | 2026-08-17 | none |
| `CLOUDFLARE_PAGES_TOKEN` | 2026-09-09 | none — reader removed 2026-09-17, revocation unrecorded |
| Claim signing private key | not verified this session | unmeasured |

The oldest reference is now about nine weeks. Nothing is overdue by a stated rule —
none of these has one — which is the finding, not a comfort.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every credential in the `ADVOCATE.md` inventory has a rotation date or a named person who knows one. | **Not met.** 0 of the inventory carries either. Unchanged since seating. |
| **G2** | The Slack invite is not expired, or is recorded as expired with an owner. | **Not met.** Past its shelf life by the file's own comment; no owner recorded. It was *met* last session with seventeen days to spare, which is the movement. |

## What I could not see

Actions and organisation secret lists (needed approval no earlier session had, and I
did not seek a workaround); whether the Slack link currently resolves; whether the
claim signing key list is still empty (I did not re-read `identity.yml` at the tip).
Reported as unmeasured, not estimated. No secret value was read, printed or copied,
and none was needed.

## What would make us stop

Unchanged. A token that lapses does not announce itself; the site just stops
updating. This range added the mirror case: a token that *should* have ended but has
no recorded end.

## Next session

Cadence is quarterly (due ~2026-12-30 from now). Look next at: whether anyone owns
the Slack link; whether `CLOUDFLARE_PAGES_TOKEN` is recorded as revoked; whether the
factory (`sites.yml`) introduced a second Cloudflare account credential.
