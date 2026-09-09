# Seat · payments

`advocate/payments` · last spoke **2026-09-09** · 1 session(s) · 9 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Payments — opening position

**Seated 2026-09-09.** This is a seating, not a report: there is no range behind
it, because a baseline does not exist until somebody records one. What follows is
where this site stands today against the two goals in `advocate.yml`, read from
the repository at `2d9fdd5`.

I speak for the treasurer, and for whoever holds that job after them.

## The one sentence

**Fort Collins Public Media cannot take money through its own website.** The only
working payment surface is Booqable, and Booqable takes rental money through
Booqable's own Stripe connection, not through anything this repository controls.
Everything else — memberships, class registration, donations, program submission
— still hands the visitor to Wix.

That was already written down in `ADVOCATE.md`. What I can add today is that it
is worse than the data files alone suggest, and the reason is in the pipeline
rather than in the content.

## What I found that was not already on the page

The broker — `worker/`, the piece that would actually create a Stripe Checkout
Session — **has never been deployed.** Its workflow has fired exactly once, on
2026-08-17, and in that run both the `Deploy` step and the `Give it the Stripe
key` step were *skipped*. They are gated on `CLOUDFLARE_API_TOKEN`, and the
repository has no Actions secrets at all: the API reports `total_count: 0`.

So there are three independent stops between here and a member paying dues, and
each of them is sufficient on its own:

1. `_data/payments.yml` has `publishable_key: ""` and `live: false`.
2. The restricted key that the broker would charge with was never pushed to
   Cloudflare, because the workflow that pushes it has never run its own steps.
3. `_data/providers.yml` has no URL for membership, tickets, donations or
   submission — so the pages render the "not wired up yet" placeholder, which is
   the correct behaviour and is also the whole story.

I want to be careful about one thing: an *organization*-level secret would not
appear in the repository list, and I am not permitted to read the organization's
secrets (the API returned 403). So the honest claim is that **no repository
secret exists**, and that the one broker run we have on record behaved exactly as
it would with no token. I am not asserting the org has none; I am asserting
nothing has deployed.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every entry in `_data/providers.yml` is either live or has a named person and a reason it is not. | **Not met, and half-met in an interesting way.** All five entries carry a *reason* — the notes are unusually good, naming candidate providers and what blocks each. None carries a **named person.** Five of five are `placeholder` or `pending`. |
| **G2** | A trustee can answer "how does FCPM get paid online" from one page, without opening a data file. | **Not met.** There is no such page. The answer today lives across `payments.yml`, `providers.yml`, `membership.yml` and a workflow file, and it takes reading all four to learn that the answer is "we can't." |

Neither goal is `unmeasured`. Both are measurable from the checkout and both are
measured above.

## What is genuinely in good shape

I am not here to be gloomy about work that was done carefully, and this was.

`_data/payments.yml` is the best-documented file in this repository. It explains
the three kinds of Stripe key and which of them may exist in git; it keeps prices
in `_data/membership.yml` so that a price change is a commit and a diff rather
than a silent dashboard edit; and it writes down the difference between paying up
front and subscribing in language a member could actually read. The renewal terms
are drafted. The refusal to sell class drop-ins while their prices are `TODO` is
the right refusal.

**None of that is the blocker.** The thinking is finished and the switch is off.
That distinction matters for how this gets reported to a board: this is not a
project that needs designing, it is a project that needs four decisions and a
token.

## What would make us stop

PEG funding is being wound down. Every year this stays as it is, the gap between
what this organisation could collect and what it does collect gets wider, and the
site keeps sending people to a Wix account FCPM is trying to leave. The failure
mode is not an outage. It is a slow one: nobody ever notices the membership that
was never bought.

## Next session

Monthly. **Due 2026-10-09.** I will read the range since `2d9fdd5` and I will
check first whether `providers.yml` gained a person's name against any entry —
that is the cheapest of my two goals to move, it needs no money and no vendor
decision, and it is the one I would most like to report differently next time.

## Complaints

### Complaints — payments

The treasurer's voice, carried. Everything here is `source: simulated` on this
first pass: I am speaking the constituency written into my seat, not relaying
anything a real trustee said to me. When a real one says any of it out loud, the
entry gets upgraded to `relayed` and that is a promotion worth making.

Everything opens at `draft`. A draft is not a claim and nothing is owed for
leaving it there.

## P1 · We agreed to sell memberships online months ago, and I still can't say when

`status: draft` · `source: simulated` · `first said: 2026-09-09`

The membership tiers are priced. The renewal terms are written. The refund and
notice rules are written. And a person who wants to join still cannot give us
money without being handed to Wix. I do not know what the remaining step is or
who owns it, and I cannot tell from the site whether it is a week away or a year.

What I would want to be able to answer at a meeting: *is anything waiting on the
board, or is it all waiting on one person with a Cloudflare login?*

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

`status: draft` · `source: simulated` · `first said: 2026-09-09`

The broker in `worker/` has one workflow run to its name, on 2026-08-17, and in
that run it deployed nothing — the deploy steps were skipped for want of
`CLOUDFLARE_API_TOKEN`, and this repository has no Actions secrets.

I raise this as its own item rather than folding it into P1 because it fails
differently. P1 is a decision nobody has made. This is a decision that *was*
made — the code exists, the tests exist, the workflow exists — that then quietly
did not happen. Nothing went red. The workflow reports success every time,
because "skipped because no token" is exactly the behaviour it was designed to
have, and that design is correct and is also why nobody noticed for three weeks.

## P5 · There is nowhere to send someone who asks how we get paid

`status: draft` · `source: simulated` · `first said: 2026-09-09`

This is G2 restated as a feeling, and I am keeping it separate because it will
outlive the others. Even after memberships are live, the answer to "how does FCPM
take money online" will still be spread across four files. A trustee should be
able to open one page. Today I would have to explain it from memory, and my
memory rotates off the board.

---

**Nothing closed this session.** That is expected on a seating and it is the last
time it will be a good excuse. Next session I intend to close one before adding
any.

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

## A2 · A recorded answer to "is the broker meant to be deployed yet?"

`status: draft` · `target: whoever holds the Cloudflare account` · `first said: 2026-09-09`

**Shape:** an operator who does not hold the token can tell, from the repository,
whether the undeployed broker is *waiting* or *abandoned*.

Right now those two states look identical: a green workflow that skipped its own
deploy. I am not asking for the token to be created — that may well be premature,
and it is not mine to decide. I am asking that the answer be written down, so the
next person to look does not have to reconstruct it from a run log.

## A3 · One page that says how FCPM takes money

`status: draft` · `target: FCPM board / whoever writes site copy` · `first said: 2026-09-09`

**Shape:** a trustee who does not read code can answer "how do we get paid
online, and what is switched on today" from a single page, and that page is wrong
in an obvious way if it goes stale.

The last clause is the part I care about. A hand-written summary that nobody
updates would be worse than the data files, because it would be confidently
wrong instead of merely scattered. Generated from `providers.yml` and
`payments.yml` would satisfy this; hand-maintained would not.

## A4 · Two numbers for class drop-ins

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** the walk-in price and the member price exist as approved figures, so
the generator stops refusing.

Explicitly **not** my decision and I will not suggest a figure. My out-of-scope
says so and it is right: a plausible guess at a price is worse than a blank,
because a blank is obviously unfinished and a guess is not.

## Last session note — 2026-09-09

### 2026-09-09 — seating

**Range:** none. This is the first session; the pin was set at `2d9fdd5` and a
baseline does not exist until it is recorded. Reporting the tip commit as "what
moved" would have been a lie about it, so I read the repository as it stands
instead.

**Constitution read:** `ADVOCATE.md`, and my sub-constitution
`#3-whether-we-can-still-be-paid`. It was written 2026-09-02 and it is accurate.
Nothing in it needed correcting.

## What I read

`_data/providers.yml`, `_data/payments.yml`, `_data/membership.yml`,
`_data/classes.yml` (pricing block only), `.github/workflows/broker.yml`, the
file listing of `worker/`, and the run history of the broker workflow.

## What is new, versus what the constitution already said

The constitution already said nothing but Booqable can take money. It did not
say — because it could not have known without looking at the forge — that **the
broker has never been deployed.** One run, 2026-08-17, deploy steps skipped, no
Actions secrets on the repository. That is the finding of this session and it is
in `POSITION.md` and as complaint P4.

## A note on how I got that

The run history and the secret *list* are not in the checkout. I read the
repository's own CI, not a sibling repository, and I never read a secret value —
only whether names exist and when steps ran. I think that is inside my scope and
I am flagging it rather than burying it, because the method tells me to read this
checkout and I read one thing beside it. If a future reader disagrees, the rest
of this session stands without it: `live: false` and an empty publishable key
were enough on their own.

## Tally

Complaints: **5 draft**, 0 open, 0 ready. Asks: **4 draft**. Nothing closed —
expected on a seating, and not an excuse I get to use twice.

## What I deliberately did not say

- **I did not suggest a price**, for drop-ins or anything else. Out of scope and
  the reason is good.
- **I did not recommend a payment provider.** `providers.yml` names Zeffy,
  Givebutter and an M365-backed form as candidates; I have no view I am entitled
  to.
- **I did not ask anyone to create `CLOUDFLARE_API_TOKEN`.** It may be correct
  that it does not exist yet. I asked for the answer to be recorded, not for the
  answer to be yes.
- **I did not comment on the quality of the worker code.** The tests own that.
- **I did not fold P4 into P1** even though they have the same victim, because
  one is an undecided decision and the other is a decided one that did not
  happen, and a board would act on them differently.

## Timeline, recorded because it will not be obvious later

I was seated **2026-09-09**, the day of a board meeting. **This council was not
ready for that meeting** and nobody pretended otherwise — the seats were being
filled the same morning. The intent is to be in step for the **October** meeting,
which is the first one this seat will have a real range to report against.

My cadence is **monthly**. Next session **2026-10-09**.

## What I would look at next

Whether `providers.yml` gained a name. It is the cheapest goal I hold and the one
whose movement would tell me most about whether this seat is being read.

