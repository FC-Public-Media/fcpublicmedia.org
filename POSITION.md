# Truthfulness — position

**As of 2026-09-10.** Second session. Range: `2d9fdd5..e63fc7b`, ten merged
pull requests, 2026-09-09.

I speak for the member who reads the site, believes it, and turns up.

## The one sentence

**The reserve page now asks a member to agree to a document that does not
exist, and the people who wrote the sentence said so in writing before it
shipped.**

PR #56 put *"Any User of FC Public Media equipment must agree to FC Public
Media's Equipment Terms and Conditions"* on `reserve.md`. No such page or PDF
exists anywhere in this repository. This is not something I found that the
maintainers missed — `REVIEW-NOTES.md`, merged in the same range, already
calls it *"the one that should not sit,"* and `CONTENT-TODO.md` marks it
**BLOCKING**. The gap here is not attention. It is that the sentence went
live in the same commit that flagged it as not ready to.

Full account in `COMPLAINTS.md` T7.

## What moved, against my goals

Ten PRs merged. Most of what's in them is outside my constituency entirely —
deploy pipeline (#59, #62), Ruby toolchain (#57), test speed (#61), the
payments checklist and KV bootstrap (#60, #63) are the payments seat's
concern, not mine. Two touched what I watch:

- **#56 (bryans-wording)** — the board president's copy review landing on
  `index.html`, `reserve.md`, `_data/community.yml`, `_data/org.yml`. This is
  where T7 came from. It also added a real events calendar (`community.yml`
  `events:`, still `[]` — nobody has entered anything yet) and a verbatim
  mission statement, neither of which asserts anything stale or false.
- **#58 (bryans-meet-and-learn-notes)** — added `office_hours` and `photo` to
  `_data/board.yml` and rendered them on `/meet/`. The roster itself is still
  `[]`; nothing here changes G1 or G2. One thing outside every seat, flagged
  and not claimed: the new `person.photo` render in `meet.md` hardcodes
  `alt=""` on what would be a photograph of a named, identifiable board
  member, with none of the guard `classes.md`'s own photo field has (alt
  required whenever src is set). Nobody holds accessibility as a seat. I am
  raising a hand, not opening a complaint.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | No page asserts a date, a price or an availability that is out of date. | **Not met, and worse by one.** The two stale findings from last session are unchanged: `governance.yml`'s meeting schedule is still `""` while `meetings.open: true`, and both classes in `classes.yml` are a day further into the past (30 and 15 days now) than they were at last count. New this session: `reserve.md` now asserts an obligation — an agreement a member must make — that has no referent at all. That is a different failure mode than "stale": it was never true, not even on the day it shipped. |
| **G2** | Every internal link resolves, including anchors, and `REDIRECTS.md` reports nothing unaccounted for. | **Unchanged.** `REDIRECTS.md` still reports one unaccounted address, `/equipment`. The link-and-anchor half stays `unmeasured` — nothing in this range added a link check, and T7 is not a broken link at all (it's deliberately unlinked prose), so even a link checker built tomorrow would not have caught it. |

## T1–T6, checked against this range

None closed. I looked before adding T7, as the method asks:

- `_data/governance.yml` is byte-identical to the last session's baseline —
  T1 stands.
- The two class dates in `_data/classes.yml` are untouched — T2 stands, one
  day worse.
- `classmode.js`'s TODO guard is untouched — T4 stands, same shape.
- `REDIRECTS.md` still names `/equipment` unaccounted for — T5 stands.
- No link-checking machinery appeared in this range — T6 stands.
- T3 (no page signals its own freshness) is the general form of T2 and has
  no single line to check; it stands by inheritance.

## Something worth recording about how this range was built

Last session's note was that the site kept handling things honestly before I
had to say so. This range is the opposite instance of the same discipline,
and it is worth being precise about which: **the maintainers' own review
caught this exact problem, on the record, before I did — and shipped it
anyway.** That is not dishonesty. `REVIEW-NOTES.md` is unusually candid about
its own gaps; nothing here was hidden. But a defect that is named in the same
commit that ships it is a different thing from a defect nobody has looked at,
and my seat exists for the member reading the page today, who cannot see
`REVIEW-NOTES.md` and has only the sentence on `reserve.md` to go on. The
gap between "we know" and "it's fixed" is exactly the gap this seat watches,
regardless of how well-documented the gap is on the inside.

## What would make us stop

Unchanged from last session in kind, widened by one instance: a member reads
a promise on this site — a meeting they can attend, a class that's on, a
form they can agree to — and acts on it or is stopped by it, and in each
case the promise was not true when they read it. They don't file a bug. They
conclude something about FC Public Media that isn't warranted, and the site
is what told them so.

## Next session

Monthly. **Due 2026-10-09.** I will re-check `_data/classes.yml` for a
future date, `_data/governance.yml`'s schedule field, and whether T7 has a
document to point to — that last one is the cheapest and most urgent of the
three, since the site's own maintainers already ranked it first.
