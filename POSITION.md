# Payments — position

**As of 2026-09-10**, reading the range `2d9fdd5..e63fc7b` (10 first-parent
commits, one board meeting's worth of merges). I speak for the treasurer, and
for whoever holds that job after them.

## The one sentence

**Fort Collins Public Media still cannot take money through its own website,**
except Booqable equipment rental, which runs on Booqable's own Stripe
connection and not on anything in this repository. That has not changed since
seating. What changed this range is that the gap between "the machinery is
finished" and "the switch is off" is now written down in one place, by name,
for the first time.

## What moved

A new file, `PAYMENTS-CHECKLIST.md`, landed in this range (PR #60) and was
corrected in it (PR #63). It is a runbook, not a design document, and it does
what none of the data files do: it separates *values only an account holder
can paste* (§1) from *decisions only the board can make* (§2), and it dates
itself — 2026-09-09.

It also found something I had not: **`worker/wrangler.jsonc` declared a KV
namespace binding with an empty id, and Wrangler refuses to run any command at
all against a config with an empty-string id.** That is a stronger failure
than the one I reported at seating — it would have blocked the *fix* to the
Cloudflare-token blocker, not just the deploy. The same range corrects it
(PR #63): the placeholder binding is removed until a real namespace exists,
with the exact command to create one left as a comment. This is the one piece
of technical debt that closed itself within a single range, and I am naming it
because a fix that ships before I ever had to ask for it is worth recording as
that, not folded silently into "still blocked."

Separately, `.github/workflows/deploy.yml` now deploys the *site* from Actions
under its own Cloudflare token, `CLOUDFLARE_PAGES_TOKEN`, distinct from the
broker's `CLOUDFLARE_API_TOKEN`. The comment in that file says why in words I
would have wanted said: "a token that only publishes the site cannot also
redeploy the thing that takes money." I did not ask for this and it does not
move either of my goals, but it protects the thing my goals depend on, so I am
noting it rather than staying silent about it.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | Every entry in `_data/providers.yml` is either live or has a named person and a reason it is not. | **Not met. Unchanged.** Still five of five `placeholder`/`pending`. Still no named person against any entry — checked directly against the file at `e63fc7b`. |
| **G2** | A trustee can answer "how does FCPM get paid online" from one page, without opening a data file. | **Not met, but closer than last session.** `PAYMENTS-CHECKLIST.md` is the first document that answers this question from one page, in prose, without requiring a data file to be opened. It is not yet what this goal asks for, though: it is a runbook addressed to whoever executes the checklist, and its own closing section says to delete it once everything on it is struck — so it will not be there to answer the question once payments go live. A trustee's page needs to survive the switch being flipped; this one is designed not to. |

## What is genuinely in good shape

Restated briefly because it is still true and still the majority of the
picture: the broker is written and tested (119 tests), prices generate from
`_data/` with CI enforcing agreement, repricing existing subscribers is
scripted, and the nonprofit half-rate cannot be self-claimed. None of that
needed this session's attention because none of it moved and none of it is
wrong. `PAYMENTS-CHECKLIST.md` restates this well and I have nothing to add to
it.

## What would make us stop

Unchanged from seating: PEG funding is being wound down, and every month this
stays as it is widens the gap between what FCPM could collect online and what
it does. The failure mode is still not an outage — it is a membership nobody
ever gets asked to buy because the page that would ask does not exist yet.

## Next session

Monthly. **Due 2026-10-09.** I will check, in order: whether `providers.yml`
gained a name (G1, cheapest to move); whether either of the two board-only
blockers in `PAYMENTS-CHECKLIST.md` §2 (class drop-in prices, tier summaries)
got a number; and whether `PAYMENTS-CHECKLIST.md` itself is still there,
unstruck, past its usefulness window, or gone because the switch flipped.
