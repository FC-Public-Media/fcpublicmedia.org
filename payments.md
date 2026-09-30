# Seat · payments

`advocate/payments` · last spoke **2026-09-30** · 11 session(s) · 7 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Payments — position

**As of 2026-09-30**, reading `e63fc7b..919a413` (51 first-parent commits,
2026-09-09 → 2026-09-24). I speak for the treasurer, and whoever holds that job
after them.

## The one sentence

**Fort Collins Public Media still cannot take money through its own website** —
unchanged since seating — **and a DNS cutover aimed at the weekend of
2026-09-26 would retire the Wix pages that were the only place a donation, dues
payment or class ticket could have been taken, in favour of pages that say
"not wired up yet."** Whether that flip happened, I cannot measure from here.

## What moved, for this constituency

The range is large (site moved into `site/`, member sites, machine profiles,
kiosk, tenancy, registrar and DNS records) and almost none of it is money. I
checked the payment surfaces by history: `docs/PAYMENTS-CHECKLIST.md`,
`payments.yml`, `providers.yml`, `membership.yml`, `classes.yml` and `worker/`
changed in this range only by **path moves and one wrangler fix already
recorded** — no value pasted, no name added, no price decided, no page built.
The checklist still describes the world accurately; it is 21 days old and every
open row is still open.

What does bear on payments is **the cutover** (`docs/OPEN.md`, relayed
2026-09-24: DNS "aimed at the coming weekend", "as much readiness work as
possible" first). The readiness work written down there is redirects and
publisher checks. None of it mentions the three entries in `providers.yml` that
say "Currently Wix": `tickets` (Wix Events), `membership` (Wix Pricing Plans),
`donate` (Wix Donations). Each has `url: ""` and `status: placeholder`;
`transaction.html` renders an empty url as a visible "not wired up yet" block.
So on the new origin `/donate/`, `/register/` and `/membership/` have nothing
to hand a visitor to. `REDIRECTS.md` keeps `/donate` and `/membership` at the
"same address" — the addresses survive; what sat behind them does not.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every entry in `providers.yml` is live or has a named person and a reason. | **Not met. Unchanged.** Five entries, all `placeholder`/`pending`, zero named people (read at subject `919a413`). |
| **G2** | A trustee can answer "how does FCPM get paid online" from one page, without a data file. | **Not met, and the answer just got harder.** The one page that answers it is a runbook scheduled for deletion and says nothing about the Wix paths the cutover retires. |

Measured vs. not: whether the DNS flip has happened — **unmeasured** (last
measurement in-repo, 2026-09-24: still Wix). Whether the Wix donation, dues and
events tools were actually live and collecting — **unmeasured**; the repo only
says "currently Wix", and Wix is read-only to every agent here.

## In good shape (restated once)

Broker written and tested, prices generated from `site/_data/` with CI
enforcement, repricing scripted, nonprofit half-rate not self-claimable.
Untouched this range, still true.

## What would make us stop

Same as seating, plus one sharper way: **the website switching over while the
old money path is switched off and the new one does not exist.** The failure is
not an outage; it is a donor who lands on a placeholder on the day the
organisation was most visible.

## Next session

Monthly; due **2026-10-30**. In order: (1) has the flip happened and what do
`/donate/` and `/membership/` show — this is the most time-sensitive; (2) does
any `providers.yml` entry have a url or a name (G1); (3) board-only rows in the
checklist §2; (4) is the checklist still there.

## Complaints

### Complaints — payments

The treasurer's voice, carried. Everything here is `source: simulated` on this
first pass: I am speaking the constituency written into my seat, not relaying
anything a real trustee said to me. When a real one says any of it out loud, the
entry gets upgraded to `relayed` and that is a promotion worth making.

Everything opens at `draft`. A draft is not a claim and nothing is owed for
leaving it there.

## P1 · We agreed to sell memberships online months ago, and I still can't say when

`status: open` · `source: simulated` · `first said: 2026-09-09` · `ripened: 2026-09-10`

The membership tiers are priced. The renewal terms are written. The refund and
notice rules are written. And a person who wants to join still cannot give us
money without being handed to Wix.

I moved this from `draft` to `open` this session because the question I asked
at seating now has a precise answer, in `PAYMENTS-CHECKLIST.md`: it is *both* —
five account-holder values and five board decisions, itemized separately, none
of them done. I no longer have to guess whether it is one person or one
meeting; the checklist names both queues.

## P2 · Somebody asked how to pay for a class and I sent them an email address

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Class drop-in prices are `TODO` in `_data/classes.yml`, so the site correctly
refuses to show a number. I agree with the refusal — a made-up price is worse
than no price. But the consequence lands on whoever picks up the phone, and it
lands every time, and nobody is counting it.

Two figures would close this: the public drop-in price and the member price. It
is a board decision and it is a small one.

## P3 · Every one of these has a reason and none of them has a person

`status: draft` · `source: simulated` · `first said: 2026-09-09`

`_data/providers.yml` explains itself well — I can read why tickets are still on
Wix and what the candidates are. What I cannot read is who is *doing* it. A
reason without a person is a description of a situation, not a plan, and when the
board turns over the reason survives and the intention does not.

This is the complaint I most expect to close first, because closing it costs
nothing but a name.

## P4 · The thing that would take the money has never been switched on

`status: open` · `source: simulated` · `first said: 2026-09-09` · `ripened: 2026-09-10`

Still true: the broker is not deployed. What changed this range is that it is
worse in one specific way I had not found, and better in the way that matters —
`worker/wrangler.jsonc` declared a KV binding with an empty id, and Wrangler
refuses to run *any* command against a config shaped like that. It would have
silently blocked the fix to the token problem, not just the deploy itself. The
same range removed the placeholder binding rather than leaving it to surprise
whoever tries next.

I am moving this to `open` rather than closing it, because the broker is still
not deployed — the missing namespace and the missing
`CLOUDFLARE_API_TOKEN` are both still open items in `PAYMENTS-CHECKLIST.md`
§1. What closed is the trap; the underlying fact this complaint is about has
not.

## P5 · There is nowhere to send someone who asks how we get paid

`status: open` · `source: simulated` · `first said: 2026-09-09` · `ripened: 2026-09-10`

This is G2 restated as a feeling, and I am keeping it separate because it will
outlive the others. `PAYMENTS-CHECKLIST.md` is the closest thing to an answer
this repository has produced, and I want to give it credit rather than move
past it — but its own last section says to delete it once every item on it is
struck. It is built to disappear exactly when memberships go live, which is
the moment this complaint stops being about "is it written down" and starts
being about "is it still true." Nothing durable exists yet for that moment.

I am ripening this to `open` because I can now point at a real artifact and
say precisely what it is not, instead of only describing an absence.

---

**One ask closed this session** — see `ASKS.md`, A2. That is the first thing
this seat has retired since seating, and the method asks me to keep the
outcome rather than the tally alone: it closed because somebody wrote the
answer down, in the repository, in the form I asked for. That is the cheapest
kind of close there is, and I would like more of them to look like this one.

---

## P6 · The website is about to change over and I don't know what happens to the donate button

`status: draft` · `source: observed` · `first said: 2026-09-30`

Observed from `docs/OPEN.md` and `providers.yml`, not from anyone's mouth: the
DNS switch was aimed at the weekend after 2026-09-24, and the readiness notes
cover redirects and publishing but not money. Today's Wix pages for donations,
dues and class tickets are the old way of being paid; the new site's versions
of those pages render "not wired up yet." As the treasurer I would ask: on
Monday, where does someone who wants to give us forty dollars go?

I do not know whether Wix's tools were live, or whether the flip happened.
Kept at `draft` because both are unmeasured. It ripens to `open` the moment
either is measured and the answer is bad.

---

*2026-09-30 session:* P1–P5 unchanged in status. Payment files changed in the
range by path only, so nothing moved them. No complaint closed: nothing in the
range answered one, and I will not close one to make the tally move.

## Asks

### Asks — payments

Requests, in shapes rather than instructions. Triage is a human's; I hold these
until somebody promotes them somewhere real, and then I cite where and stop
holding them.

I have no `writes:` grant, so none of these is a pull request. They are all
"somebody should decide."

## A1 · A person's name against each entry in `providers.yml`

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** every dynamic surface on this site can name the human who would know
its current state, without anybody having to open a data file to find out that
nobody does.

Five entries. It does not require deciding a vendor, setting a price, or spending
anything, and it is the only one of my asks that a single meeting could finish.

## A2 · A recorded answer to "is the broker meant to be deployed yet?" — `answered`

`status: answered` · `target: whoever holds the Cloudflare account` · `first said: 2026-09-09` · `answered: 2026-09-10`

**Shape asked for:** an operator who does not hold the token can tell, from the
repository, whether the undeployed broker is *waiting* or *abandoned*.

**What happened:** `PAYMENTS-CHECKLIST.md` (merged this range, PR #60, then
corrected in PR #63) records exactly this — a numbered list of what blocks
deployment, none of it a decision, each with what it blocks. It even found a
sharper version of the question I asked: one of the blockers was a config
error that would have looked identical to "waiting," and it got named and
fixed in the same range. I am not asking for anything further here; the thing
this ask wanted now exists in the repository and I have cited it.

## A3 · One page that says how FCPM takes money

`status: draft` · `target: FCPM board / whoever writes site copy` · `first said: 2026-09-09`

**Shape:** a trustee who does not read code can answer "how do we get paid
online, and what is switched on today" from a single page, and that page is wrong
in an obvious way if it goes stale.

The last clause is the part I care about. A hand-written summary that nobody
updates would be worse than the data files, because it would be confidently
wrong instead of merely scattered. Generated from `providers.yml` and
`payments.yml` would satisfy this; hand-maintained would not.

**Not satisfied by `PAYMENTS-CHECKLIST.md`**, new this range. It is the
closest thing produced so far, and it is hand-maintained on purpose — it is a
runbook meant to be struck down to nothing and then deleted, not a standing
page. This ask is for the page that exists *after* that runbook is gone.

## A4 · Two numbers for class drop-ins

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** the walk-in price and the member price exist as approved figures, so
the generator stops refusing.

Explicitly **not** my decision and I will not suggest a figure. My out-of-scope
says so and it is right: a plausible guess at a price is worse than a blank,
because a blank is obviously unfinished and a guess is not.

## A5 · Someone who knows whether the old money paths survive the flip

`status: draft` · `target: whoever runs the cutover / FCPM board` · `first said: 2026-09-30`

**Shape:** whoever decides the day `www` moves can say, before it moves,
whether the Wix donation, dues and ticket tools keep working, are deliberately
turned off, or are already dead — and a visitor who lands on `/donate/` that
day is handed somewhere real or told plainly.

Not a request to pick a provider or build anything; that is the board's and out
of this seat. It is a request for a recorded answer, like A2 was.
*Candidate advisory:* a moving external deadline is what the method says may
warrant an issue. I have not posted one (outside this session's reach) and
leave that to a human.

## Last session note — 2026-09-30

### 2026-09-30

**Range:** `e63fc7b..919a413` — 51 first-parent commits, 2026-09-09 → 2026-09-24.
(An auto-written line dated today said nothing had merged; it contradicted the
work order's range and is replaced by this note.)

**Read:** PENDING.md, METHOD.md, my seat, `docs/PAYMENTS-CHECKLIST.md`,
`providers.yml`, `transaction.html`, `donate.md`, `register.md`, `docs/OPEN.md`
(cutover), `REDIRECTS.md` donate/membership rows, and the history of every
payment file across the range. The constitution anchor is in `docs/ADVOCATE.md`;
I did not check whether it changed in the range, only that it is there.

**Changed:** `POSITION.md` rewritten. `COMPLAINTS.md`: P6 added (draft).
`ASKS.md`: A5 added (draft).

**Tally:** complaints — open 3 (P1, P4, P5), draft 3 (P2, P3, P6). Asks — draft 4
(A1, A3, A4, A5), answered 1 (A2).

**Thin on purpose:** 51 commits, one thing this constituency notices — the
cutover. Payment files moved by path only; no value, name, price or page landed.

**Did not say:** that the flip happened (unmeasured); that Wix's tools were live
(unmeasured, Wix is read-only here); any provider, price or fix; anything about
member sites, kiosk, machine profiles or tenancy.

**Outside every seat (hand raised):** nobody owns the post-cutover absence test
for `_redirects` described in `docs/OPEN.md`.

**Next look:** flip status and what `/donate/` renders, before anything else.

Station grant reported TRUANT/unledgered at session start; work proceeded.

