# Asks — credentials

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
