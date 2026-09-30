# Complaints — credentials

The voice of whoever inherits the accounts. `source` is marked per entry: `simulated`
is me speaking my constituency and is not testimony.

## C1 · The Slack link on our own front-facing page is now an error

`status: open` · `source: observed` · `first said: 2026-09-09` · `moved: draft → open 2026-09-30`

Committed 2026-08-28 with a thirty-day life; the file's comment says so. The string
is unchanged at the tip, so by its own shelf life it lapsed on or before 2026-09-27.
I have not probed it; I do not need to, because the date is in the history.

It ripened because the thing predicted last time happened: the page still renders,
so nothing looks wrong from inside, and nobody owns regenerating it. The shape is a
monthly chore with no owner, not a one-off mistake.

## C2 · I don't know who has that login

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Every credential the inventory names lacks a person against it. The range added a
dozen docs about how the site is built and where it deploys; none names who holds the
accounts. Board terms are about a year. Nine lines would prevent it.

## C3 · Was that one of ours or Wix's?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Unchanged, kept vague on purpose. The range added a DNS inventory and a redirect
blind-spot record, which help the vendors seat more than mine. Still unsure whether
this is mine.

## C4 · A key I cannot see is a key I cannot report on

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Unchanged. The unobservability is the safety; the complaint is only that nobody has
written down who *can* see them.

## C5 · Our own inventory counts one Stripe credential as two

`status: open` · `source: observed` · `first said: 2026-09-10` · `moved: draft → open 2026-09-30`

**Half closed.** The missing-row half — `CLOUDFLARE_PAGES_TOKEN` — is closed: the
workflow that read it was removed on 2026-09-17, so the inventory correctly has no
row for something nothing reads. (What that leaves behind is C6.)

The remaining half stands at the tip: `docs/ADVOCATE.md` still lists `STRIPE_KEY` and
`PUBLIC_STRIPE_API_KEY` as two credentials, the second described as the "publishable
half". The worker reads one and falls back to the other; both hold the same restricted
secret key. The codebase carries comments warning against this reading, and the table
still makes it. `docs/ADVOCATE.md` was substantially rewritten in this range and the
row survived.

## C6 · A powerful token nobody uses, and nobody has to remove

`status: draft` · `source: observed` · `first said: 2026-09-30`

The spare deploy workflow is gone, and `deploying.md` says the organisation secret
"can go once you are satisfied no other repository in the org wants it." That is a
condition with no owner and no date. An account-scoped token with edit rights, read by
nothing in this repository, is a live credential whose absence would be noticed by
nobody — which is the exact reverse of the failure I usually watch for, and just as
invisible.

Kept as a draft: I cannot see the organisation's secret list, so I do not know whether
it has already been deleted. The complaint is that the repository cannot tell me.

---

**Tally of movement:** C1 draft → open; C5 draft → open and half closed; C6 new.
Nothing withdrawn.
