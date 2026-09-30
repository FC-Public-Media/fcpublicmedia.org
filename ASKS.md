# Asks — credentials

Shapes, not instructions. I hold no `writes:` grant; none of these is a pull request.

## A1 · A rotation owner for each credential in the inventory

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** somebody inheriting these accounts can tell, from the repository, who
would know how to rotate each one — without any secret value becoming visible to
anyone who could not already see it.

A name is enough; a date is better. It must not require moving anything into the
repository, and if any proposed answer does, it is the wrong answer.

## A2 · Something that notices the Slack invite before a member does

`status: open` · `target: FCPM board / whoever maintains the workflows` · `first said: 2026-09-09` · `moved: draft → open 2026-09-30`

**Shape:** a link with a thirty-day life on a public page cannot reach its expiry
without a person having been told first.

Last session I said my quarterly cadence made me structurally unable to catch this,
and that this ask existed for that reason. The link has now lapsed without any
notice in the range. Not specified: scheduled workflow, calendar reminder, runbook
line, or a longer-lived invite. Any satisfies the shape.

## A3 · A decision recorded about whether these credentials exist yet

`status: draft` · `target: whoever holds the Cloudflare and Azure accounts` · `first said: 2026-09-09`

**Shape:** a reader can tell "this credential exists and is stored out of sight"
from "this credential was never created."

Narrowed this session: `CLOUDFLARE_PAGES_TOKEN` is no longer part of it (see A5).
What remains is the Azure token, still referenced by `deploy.yml` while
`deploying.md` names Cloudflare as the only publisher — a reader cannot tell whether
that reference is live, dormant or vestigial. That overlaps the vendors seat's
deploy-twice decision; I record only the credential side.

## A4 · An inventory that moves when the credentials do

`status: draft` · `target: FCPM board / whoever maintains ADVOCATE.md` · `first said: 2026-09-10`

**Shape:** when a pull request adds, removes, or renames a secret this site depends
on, the inventory that names it changes in the same pull request.

This range removed a credential's only reader and the inventory was rewritten in the
same range without either counting it or correcting the Stripe row (C5). Not
specified: PR template item, or a script diffing `secrets.` references against the
table.

## A5 · A recorded end for a credential whose reader was removed

`status: draft` · `target: whoever holds the Cloudflare organisation` · `first said: 2026-09-30`

**Shape:** when the last thing that reads a credential is deleted, the credential is
recorded as either revoked (with a date) or kept (with a reason and an owner) — so a
reader can tell "unused and gone" from "unused and still live."

Instance: `CLOUDFLARE_PAGES_TOKEN`; see C6. Not specified who acts or how.
