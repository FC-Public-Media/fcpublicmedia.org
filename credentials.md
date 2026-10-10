# Seat · credentials

`advocate/credentials` · last spoke **2026-10-10** · 20 session(s) · 8 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Credentials — position

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

## Complaints

### Complaints — credentials

The voice of whoever inherits the accounts. `source` is marked per entry: `simulated`
is me speaking my constituency and is not testimony.

## C1 · The Slack link on our own front-facing page is now an error

`status: open` · `source: observed` · `first said: 2026-09-09` · `moved: draft → open 2026-09-30`

Committed 2026-08-28 with a thirty-day life; the file's comment says so. The string
is unchanged at the tip, so by its own shelf life it lapsed on or before 2026-09-27.
I have not probed it; I do not need to, because the date is in the history.

It ripened because the thing predicted last time happened: the page still renders,
so nothing looks wrong from inside, and nobody owns regenerating it. The shape is a
monthly chore with no owner, not a one-off mistake.

## C2 · I don't know who has that login

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Every credential the inventory names lacks a person against it. The range added a
dozen docs about how the site is built and where it deploys; none names who holds the
accounts. Board terms are about a year. Nine lines would prevent it.

## C3 · Was that one of ours or Wix's?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Unchanged, kept vague on purpose. The range added a DNS inventory and a redirect
blind-spot record, which help the vendors seat more than mine. Still unsure whether
this is mine.

## C4 · A key I cannot see is a key I cannot report on

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Unchanged. The unobservability is the safety; the complaint is only that nobody has
written down who *can* see them.

## C5 · Our own inventory counts one Stripe credential as two

`status: open` · `source: observed` · `first said: 2026-09-10` · `moved: draft → open 2026-09-30`

**Half closed.** The missing-row half — `CLOUDFLARE_PAGES_TOKEN` — is closed: the
workflow that read it was removed on 2026-09-17, so the inventory correctly has no
row for something nothing reads. (What that leaves behind is C6.)

The remaining half stands at the tip: `docs/ADVOCATE.md` still lists `STRIPE_KEY` and
`PUBLIC_STRIPE_API_KEY` as two credentials, the second described as the "publishable
half". The worker reads one and falls back to the other; both hold the same restricted
secret key. The codebase carries comments warning against this reading, and the table
still makes it. `docs/ADVOCATE.md` was substantially rewritten in this range and the
row survived.

## C6 · A powerful token nobody uses, and nobody has to remove

`status: draft` · `source: observed` · `first said: 2026-09-30`

The spare deploy workflow is gone, and `deploying.md` says the organisation secret
"can go once you are satisfied no other repository in the org wants it." That is a
condition with no owner and no date. An account-scoped token with edit rights, read by
nothing in this repository, is a live credential whose absence would be noticed by
nobody — which is the exact reverse of the failure I usually watch for, and just as
invisible.

Kept as a draft: I cannot see the organisation's secret list, so I do not know whether
it has already been deleted. The complaint is that the repository cannot tell me.

---

**Tally of movement:** C1 draft → open; C5 draft → open and half closed; C6 new.
Nothing withdrawn.

## Asks

### Asks — credentials

Shapes, not instructions. I hold no `writes:` grant; none of these is a pull request.

## A1 · A rotation owner for each credential in the inventory

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** somebody inheriting these accounts can tell, from the repository, who
would know how to rotate each one — without any secret value becoming visible to
anyone who could not already see it.

A name is enough; a date is better. It must not require moving anything into the
repository, and if any proposed answer does, it is the wrong answer.

## A2 · Something that notices the Slack invite before a member does

`status: open` · `target: FCPM board / whoever maintains the workflows` · `first said: 2026-09-09` · `moved: draft → open 2026-09-30`

**Shape:** a link with a thirty-day life on a public page cannot reach its expiry
without a person having been told first.

Last session I said my quarterly cadence made me structurally unable to catch this,
and that this ask existed for that reason. The link has now lapsed without any
notice in the range. Not specified: scheduled workflow, calendar reminder, runbook
line, or a longer-lived invite. Any satisfies the shape.

## A3 · A decision recorded about whether these credentials exist yet

`status: draft` · `target: whoever holds the Cloudflare and Azure accounts` · `first said: 2026-09-09`

**Shape:** a reader can tell "this credential exists and is stored out of sight"
from "this credential was never created."

Narrowed this session: `CLOUDFLARE_PAGES_TOKEN` is no longer part of it (see A5).
What remains is the Azure token, still referenced by `deploy.yml` while
`deploying.md` names Cloudflare as the only publisher — a reader cannot tell whether
that reference is live, dormant or vestigial. That overlaps the vendors seat's
deploy-twice decision; I record only the credential side.

## A4 · An inventory that moves when the credentials do

`status: draft` · `target: FCPM board / whoever maintains ADVOCATE.md` · `first said: 2026-09-10`

**Shape:** when a pull request adds, removes, or renames a secret this site depends
on, the inventory that names it changes in the same pull request.

This range removed a credential's only reader and the inventory was rewritten in the
same range without either counting it or correcting the Stripe row (C5). Not
specified: PR template item, or a script diffing `secrets.` references against the
table.

## A5 · A recorded end for a credential whose reader was removed

`status: draft` · `target: whoever holds the Cloudflare organisation` · `first said: 2026-09-30`

**Shape:** when the last thing that reads a credential is deleted, the credential is
recorded as either revoked (with a date) or kept (with a reason and an owner) — so a
reader can tell "unused and gone" from "unused and still live."

Instance: `CLOUDFLARE_PAGES_TOKEN`; see C6. Not specified who acts or how.

## Last session note — 2026-10-10

### 2026-10-10

Subject unchanged at `919a413`. Nothing merged since the last session; nothing to say.

