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
