# Seat · credentials

`advocate/credentials` · last spoke **2026-09-11** · 3 session(s) · 9 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Credentials — position

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

## Complaints

### Complaints — credentials

The voice of whoever inherits the accounts. All `source: simulated` on this first
pass except where marked `observed` — I am speaking the constituency my seat was
written for, not relaying testimony. Everything opens at `draft`.

## C1 · The Slack link on our own front-facing page is about to become an error

`status: draft` · `source: observed` · `first said: 2026-09-09`

Committed 2026-08-28, thirty-day shelf life, so it dies on or before 2026-09-27.
Nothing regenerates it and nobody owns regenerating it.

This is `observed`, not simulated: the date is in the git history and the shelf
life is in a comment beside the line. I am not imagining the complaint, I am
reading it.

What makes it worth a board's attention is the shape rather than the size. It is
thirty days of life, generated by hand, on the primary channel of a community
page — which means it is not a thing that gets fixed once. It is a chore that
recurs monthly forever, and it currently belongs to nobody, and the failure is
invisible from the inside because the page still renders.

## C2 · I don't know who has that login

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Nine credentials are named in `ADVOCATE.md`. Not one of them has a person against
it. I can find out when each was first *mentioned* here, which tells me roughly
how old the account is, and nothing about who could get into it.

Board terms are about a year. This is the complaint that turns into a genuine
emergency exactly once, at the worst possible moment, and it costs nine lines to
prevent.

## C3 · Was that one of ours or Wix's?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

The site is mid-migration off Wix. Some things the organisation pays for belong
to the new stack, some to the old, and the redirect map in `_data/redirects.yml`
describes an address space FCPM is leaving. When somebody eventually cancels the
Wix account, I do not currently have a way to tell them what breaks.

Vague on purpose and kept as a draft on purpose. I am not sure yet whether this
is mine or the vendors seat's — it touches both — and half-formed is the honest
state of it. I would rather record it badly now than discover in December that
nobody wrote it down.

## C4 · A key I cannot see is a key I cannot report on

`status: draft` · `source: simulated` · `first said: 2026-09-09`

This repository has zero Actions secrets, and the organization's secrets are
closed to me — correctly. So for eight of my nine credentials I cannot say
whether they exist, let alone when they were rotated.

I want to be careful here, because there is a bad version of this complaint that
ends with "so move them somewhere I can see." That would be the single worst
outcome this seat could cause, my out-of-scope says so, and I agree with it. The
unobservability *is* the safety.

The complaint is not that I cannot see them. It is that **nobody has written down
who can**, and that person is the entire control.

## C5 · Our own inventory has a phantom entry and a missing one

`status: draft` · `source: observed` · `first said: 2026-09-10`

`ADVOCATE.md`'s credential table lists `STRIPE_KEY` and `PUBLIC_STRIPE_API_KEY`
as two separate credentials. They are one: the worker reads the second and
falls back to the first, and both hold the same restricted secret key. Neither
is the "publishable half" the table calls it — the real publishable key isn't
a credential at all, it's meant to be public and lives in a data file. The
codebase already carries comments warning people away from exactly this
misreading. My own table did not listen to its own codebase.

Meanwhile a real, new credential — `CLOUDFLARE_PAGES_TOKEN`, added this range
so Actions can deploy the site as a spare to Cloudflare's git connection — has
no row at all.

Both halves of this complaint are the same shape: the list I check credentials
against is not itself being kept current, and I found that out by reading the
code rather than by the list telling me. I cannot fix `ADVOCATE.md` myself —
it isn't mine to write — so this sits as a complaint until whoever maintains
it does.

---

**Nothing closed this session.** All four prior complaints are still live and
none has ripened past `draft` — the range gave them company (C5) rather than
resolution. C1's number moved (eighteen days to seventeen) but its status
didn't.

## Asks

### Asks — credentials

Shapes, not instructions. I hold no `writes:` grant; none of these is a pull
request.

## A1 · A rotation owner for each credential in the inventory

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** somebody inheriting these accounts can tell, from the repository, who
would know how to rotate each one — without any secret value becoming visible to
anyone who could not already see it.

Nine rows. A name is enough; a date would be better. It must not require moving
anything into the repository, and if any proposed answer does, it is the wrong
answer.

## A2 · Something that notices the Slack invite before a member does

`status: draft` · `target: FCPM board / whoever maintains the workflows` · `first said: 2026-09-09`

**Shape:** a link with a thirty-day life on a public page cannot reach its expiry
without a person having been told first.

I am naming this one carefully. My cadence is quarterly and the link expires in
under three weeks, so **I am structurally unable to be the thing that catches
it** — this session is the only warning I get to give before it lapses, and my
next visit is December. That is not a complaint about my cadence, which a person
set deliberately. It is the reason this ask exists at all: the check belongs
somewhere that runs more often than I do.

Deliberately not specified: whether that is a scheduled workflow, a calendar
reminder, a line in a runbook, or a longer-lived invite link. Any of those would
satisfy the shape, and choosing between them is not mine.

## A3 · A decision recorded about whether these credentials exist yet

`status: draft` · `target: whoever holds the Cloudflare and Azure accounts` · `first said: 2026-09-09`

**Shape:** a reader can tell the difference between "this credential exists and
is stored correctly out of sight" and "this credential was never created."

Today those look identical from here — both are a name in a workflow file and
nothing else. It changes what the honest report is, and it changes whether the
site is deploying at all, so it is not a bookkeeping question.

This one overlaps with an ask the payments seat is holding. I am recording it
from my side rather than deferring, because the answer matters to me for a
different reason: an unrotated key and an uncreated key need very different
follow-ups, and I cannot pick one without knowing which I have.

## A4 · An inventory that moves when the credentials do

`status: draft` · `target: FCPM board / whoever maintains ADVOCATE.md` · `first said: 2026-09-10`

**Shape:** when a pull request adds, removes, or renames a secret this site
depends on, the inventory that names it changes in the same pull request —
not discovered later by an advocate reading the workflow files by hand.

This range added a real credential (`CLOUDFLARE_PAGES_TOKEN`) with no row for
it, on top of an inventory that already miscounted an existing one (Stripe's
secret was listed as two credentials; it is one — see C5). Neither mistake was
dangerous by itself, but a list that drifts from what the workflows actually
reference is a list nobody can safely stop double-checking, which defeats the
point of keeping one.

Deliberately not specified: whether that is a checklist item on the PR
template, a script that greps workflow files for `secrets.` and diffs the
result against the table, or something else. Any of those satisfy the shape.

## Last session note — 2026-09-11

### 2026-09-11

Subject unchanged at `e63fc7b`. Nothing merged since the last session; nothing to say.

