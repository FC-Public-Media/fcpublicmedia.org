# Complaints — payments

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
