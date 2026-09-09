# Asks — payments

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
