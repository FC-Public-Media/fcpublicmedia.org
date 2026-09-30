# Payments — position

**As of 2026-09-30**, reading `e63fc7b..919a413` (51 first-parent commits,
2026-09-09 → 2026-09-24). I speak for the treasurer, and whoever holds that job
after them.

## The one sentence

**Fort Collins Public Media still cannot take money through its own website** —
unchanged since seating — **and a DNS cutover aimed at the weekend of
2026-09-26 would retire the Wix pages that were the only place a donation, dues
payment or class ticket could have been taken, in favour of pages that say
"not wired up yet."** Whether that flip happened, I cannot measure from here.

## What moved, for this constituency

The range is large (site moved into `site/`, member sites, machine profiles,
kiosk, tenancy, registrar and DNS records) and almost none of it is money. I
checked the payment surfaces by history: `docs/PAYMENTS-CHECKLIST.md`,
`payments.yml`, `providers.yml`, `membership.yml`, `classes.yml` and `worker/`
changed in this range only by **path moves and one wrangler fix already
recorded** — no value pasted, no name added, no price decided, no page built.
The checklist still describes the world accurately; it is 21 days old and every
open row is still open.

What does bear on payments is **the cutover** (`docs/OPEN.md`, relayed
2026-09-24: DNS "aimed at the coming weekend", "as much readiness work as
possible" first). The readiness work written down there is redirects and
publisher checks. None of it mentions the three entries in `providers.yml` that
say "Currently Wix": `tickets` (Wix Events), `membership` (Wix Pricing Plans),
`donate` (Wix Donations). Each has `url: ""` and `status: placeholder`;
`transaction.html` renders an empty url as a visible "not wired up yet" block.
So on the new origin `/donate/`, `/register/` and `/membership/` have nothing
to hand a visitor to. `REDIRECTS.md` keeps `/donate` and `/membership` at the
"same address" — the addresses survive; what sat behind them does not.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every entry in `providers.yml` is live or has a named person and a reason. | **Not met. Unchanged.** Five entries, all `placeholder`/`pending`, zero named people (read at subject `919a413`). |
| **G2** | A trustee can answer "how does FCPM get paid online" from one page, without a data file. | **Not met, and the answer just got harder.** The one page that answers it is a runbook scheduled for deletion and says nothing about the Wix paths the cutover retires. |

Measured vs. not: whether the DNS flip has happened — **unmeasured** (last
measurement in-repo, 2026-09-24: still Wix). Whether the Wix donation, dues and
events tools were actually live and collecting — **unmeasured**; the repo only
says "currently Wix", and Wix is read-only to every agent here.

## In good shape (restated once)

Broker written and tested, prices generated from `site/_data/` with CI
enforcement, repricing scripted, nonprofit half-rate not self-claimable.
Untouched this range, still true.

## What would make us stop

Same as seating, plus one sharper way: **the website switching over while the
old money path is switched off and the new one does not exist.** The failure is
not an outage; it is a donor who lands on a placeholder on the day the
organisation was most visible.

## Next session

Monthly; due **2026-10-30**. In order: (1) has the flip happened and what do
`/donate/` and `/membership/` show — this is the most time-sensitive; (2) does
any `providers.yml` entry have a url or a name (G1); (3) board-only rows in the
checklist §2; (4) is the checklist still there.
