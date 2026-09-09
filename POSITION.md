# Payments — opening position

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
