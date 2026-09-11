# Seat · payments

`advocate/payments` · last spoke **2026-09-11** · 3 session(s) · 5 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Payments — position

**As of 2026-09-10**, reading the range `2d9fdd5..e63fc7b` (10 first-parent
commits, one board meeting's worth of merges). I speak for the treasurer, and
for whoever holds that job after them.

## The one sentence

**Fort Collins Public Media still cannot take money through its own website,**
except Booqable equipment rental, which runs on Booqable's own Stripe
connection and not on anything in this repository. That has not changed since
seating. What changed this range is that the gap between "the machinery is
finished" and "the switch is off" is now written down in one place, by name,
for the first time.

## What moved

A new file, `PAYMENTS-CHECKLIST.md`, landed in this range (PR #60) and was
corrected in it (PR #63). It is a runbook, not a design document, and it does
what none of the data files do: it separates *values only an account holder
can paste* (§1) from *decisions only the board can make* (§2), and it dates
itself — 2026-09-09.

It also found something I had not: **`worker/wrangler.jsonc` declared a KV
namespace binding with an empty id, and Wrangler refuses to run any command at
all against a config with an empty-string id.** That is a stronger failure
than the one I reported at seating — it would have blocked the *fix* to the
Cloudflare-token blocker, not just the deploy. The same range corrects it
(PR #63): the placeholder binding is removed until a real namespace exists,
with the exact command to create one left as a comment. This is the one piece
of technical debt that closed itself within a single range, and I am naming it
because a fix that ships before I ever had to ask for it is worth recording as
that, not folded silently into "still blocked."

Separately, `.github/workflows/deploy.yml` now deploys the *site* from Actions
under its own Cloudflare token, `CLOUDFLARE_PAGES_TOKEN`, distinct from the
broker's `CLOUDFLARE_API_TOKEN`. The comment in that file says why in words I
would have wanted said: "a token that only publishes the site cannot also
redeploy the thing that takes money." I did not ask for this and it does not
move either of my goals, but it protects the thing my goals depend on, so I am
noting it rather than staying silent about it.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every entry in `_data/providers.yml` is either live or has a named person and a reason it is not. | **Not met. Unchanged.** Still five of five `placeholder`/`pending`. Still no named person against any entry — checked directly against the file at `e63fc7b`. |
| **G2** | A trustee can answer "how does FCPM get paid online" from one page, without opening a data file. | **Not met, but closer than last session.** `PAYMENTS-CHECKLIST.md` is the first document that answers this question from one page, in prose, without requiring a data file to be opened. It is not yet what this goal asks for, though: it is a runbook addressed to whoever executes the checklist, and its own closing section says to delete it once everything on it is struck — so it will not be there to answer the question once payments go live. A trustee's page needs to survive the switch being flipped; this one is designed not to. |

## What is genuinely in good shape

Restated briefly because it is still true and still the majority of the
picture: the broker is written and tested (119 tests), prices generate from
`_data/` with CI enforcing agreement, repricing existing subscribers is
scripted, and the nonprofit half-rate cannot be self-claimed. None of that
needed this session's attention because none of it moved and none of it is
wrong. `PAYMENTS-CHECKLIST.md` restates this well and I have nothing to add to
it.

## What would make us stop

Unchanged from seating: PEG funding is being wound down, and every month this
stays as it is widens the gap between what FCPM could collect online and what
it does. The failure mode is still not an outage — it is a membership nobody
ever gets asked to buy because the page that would ask does not exist yet.

## Next session

Monthly. **Due 2026-10-09.** I will check, in order: whether `providers.yml`
gained a name (G1, cheapest to move); whether either of the two board-only
blockers in `PAYMENTS-CHECKLIST.md` §2 (class drop-in prices, tier summaries)
got a number; and whether `PAYMENTS-CHECKLIST.md` itself is still there,
unstruck, past its usefulness window, or gone because the switch flipped.

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

## Last session note — 2026-09-11

### 2026-09-11

Subject unchanged at `e63fc7b`. Nothing merged since the last session; nothing to say.

