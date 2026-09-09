# Complaints — payments

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
