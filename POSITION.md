# Credentials — position

**Session 2026-09-10.** Range `2d9fdd5..e63fc7b`, ten merged pull requests. Seated
2026-09-09 at `2d9fdd5`; this is the first real range behind that seating.

I speak for the person who inherits the accounts without inheriting the context.

## The one sentence

**A tenth credential entered the system in this range, and my own constitution's
inventory does not know about it yet — while also still counting one that isn't
real.** Nobody rotated anything and nothing lapsed; what moved is the shape of
what there is to track.

## What moved, that my seat notices

### A new credential: `CLOUDFLARE_PAGES_TOKEN`

PR #59 ("deploy-the-site-from-actions", merged 2026-09-09) added a second
deploy path: GitHub Actions can now build and publish the site itself with
`wrangler deploy`, as a deliberately-unarmed spare for the Cloudflare git
connection that has broken once already. It needs its own organization secret,
**`CLOUDFLARE_PAGES_TOKEN`** — account-scoped, *Edit Cloudflare Workers*
template — kept separate from the existing `CLOUDFLARE_API_TOKEN` so that
revoking or rotating one never takes the broker down with it. Two repository
*variables* ride alongside it, `CLOUDFLARE_PAGES_PROJECT` and
`CLOUDFLARE_ACCOUNT_ID` — not credentials, no secret value, I note them only
for completeness.

The workflow itself no-ops cleanly if the secret is unset (`if: env.CF_TOKEN
!= ''`, with a step that writes plainly to the job summary that nothing was
published and why) — so I cannot tell from the repository alone whether this
secret exists yet or is still a documented gap. I could not check the
organization's or repository's secret list this session; the command needed
approval that this environment did not grant. That is a gap in this report,
not a finding — see "What I could not see."

Either way, this is now a name my inventory has to hold, and **`ADVOCATE.md`'s
table does not have a row for it.** The table was not touched anywhere in this
range. See C5.

### A correction to my own inventory: the Stripe row was never two credentials

Not new to this range, but new to me this session, found while chasing the
Cloudflare token through the same files. `ADVOCATE.md`'s inventory (line
100–101) lists `STRIPE_KEY` and `PUBLIC_STRIPE_API_KEY` as two separate
credentials, one described as the "publishable half." My own opening
`POSITION.md` copied that framing forward on 2026-09-09 without checking it.

It is wrong, and the codebase already knows it is wrong: `worker/src/index.js`
reads `PUBLIC_STRIPE_API_KEY` first and falls back to `STRIPE_KEY` — one value,
two names, the second kept only so a secret already set by hand keeps working.
Both hold the same **restricted secret key** (`rk_live_…`). Neither is
publishable. The actual publishable key is a different, genuinely-public value
that lives in `_data/payments.yml` and is not a credential in this seat's sense
at all — it is meant to be world-readable.

`script/test_no_secrets.py` and `script/reprice-subscriptions.py` both carry
comments warning against exactly this misreading — "somebody will eventually
read that name, believe it, and put the value in a template." My constitution's
own table is that somebody. I am not able to fix `ADVOCATE.md` — it is not my
file to write — so this is a complaint (C5) and, together with the missing
Cloudflare row, the honest count below.

### Unchanged: the Slack invite

Nothing touched `_data/community.yml`'s "where we talk" section in this range —
the events-calendar additions elsewhere in the same file are new content, not a
new invite. Blame on the link is still `a30f919`, 2026-08-28. It still expires
**no later than 2026-09-27**, which is now **seventeen days** from this
session rather than eighteen. Not expired. Nobody regenerated it, and nobody
needed to yet.

## Everything else: earliest possible age, and no later evidence

| Credential | Reference first appears | Later evidence of rotation |
| --- | --- | --- |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | 2026-07-31 | none |
| `GITHUB_APP_ID` / `GITHUB_APP_KEY` | 2026-08-05 | none |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | 2026-08-05 | none |
| `CLOUDFLARE_API_TOKEN` | 2026-08-17 | none |
| `STRIPE_KEY` / `PUBLIC_STRIPE_API_KEY` (one credential, two names) | 2026-08-17 | none |
| **`CLOUDFLARE_PAGES_TOKEN`** | **2026-09-09** (this range, PR #59) | none — and unknown whether it exists yet |
| Claim signing private key | not yet — `_data/identity.yml` still has `keys: []` | n/a |

Nothing here is overdue. The oldest reference is six weeks old; the newest is
one day old. I am not reporting neglect — I am reporting that the list itself
needs an edit, which is a smaller and more honest thing to say.

## What I could not see, and will not try to

I attempted to list this repository's Actions secrets and variables by name
only, the way the seating session listed the (empty) repository secret set.
The command required an approval this environment did not grant this round, so
I do not know whether `CLOUDFLARE_PAGES_TOKEN` has been created. I did not
retry past the refusal, and I did not attempt to read, print or copy any
secret value — nothing here required one.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every credential in the `ADVOCATE.md` inventory has a rotation date or a named person who knows one. | **Not met.** Still 0 with either — unchanged from seating. But the inventory itself needs a row added (`CLOUDFLARE_PAGES_TOKEN`) and a row corrected (Stripe is one credential, not two) before "every credential" is even the right list to be measuring against. |
| **G2** | The Slack invite on the community page is not expired, or is recorded as expired with an owner. | **Met today.** Seventeen days left, still no owner recorded for regenerating it. Unchanged in substance from the seating session — see A2. |

## What would make us stop

Unchanged from seating: a token that quietly expires does not announce itself,
the site just stops updating, and the person who notices is whoever eventually
wonders why their change never appeared. This range added a second such token
rather than removing the risk — a deliberate spare, which is the right design,
but it is one more name that needs an owner and a rotation date exactly like
the rest.

## Next session

Cadence is quarterly; the prior session named 2026-12-09 as due. This session
ran sooner than that because a work order fired for a real range, not because
my cadence changed — I am not treating that as mine to question. I would look
next at whether `CLOUDFLARE_PAGES_TOKEN` has actually been created (if I can
get the secret-list check approved), and whether the claim signing key list is
still empty.
