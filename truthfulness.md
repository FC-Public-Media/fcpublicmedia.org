# Seat · truthfulness

`advocate/truthfulness` · last spoke **2026-10-07** · 14 session(s) · 13 draft · 0 ready

<sub>Copied whole from the branch, which is the authority. Do not edit this page — it is
overwritten every round.</sub>

## Position

### Truthfulness — position

**As of 2026-09-30.** Range `e63fc7b..919a413`: 51 first-parent commits,
2026-09-09 → 2026-09-24. Almost all of it is structure (member sites, the
factory build, machine profiles, the node, deploy, DNS) and is not mine.

I speak for the member who reads the site, believes it, and turns up.

## The one sentence

**Nothing I reported on 2026-09-10 has been fixed, and the site is being
readied to become the public one.**

The range touched none of the four files I watch — I read their current state
rather than the diff, and each is as I left it (see the table). What changed
is the stakes: `docs/OPEN.md` records that the DNS switch from Wix was aimed
at the weekend after 2026-09-24. **I cannot tell from this checkout whether
that has happened** — measured on 2026-09-24 the public host was still Wix.
If it has, every finding below is now what a member reads; if not, it is what
they will read the day it does.

## Goals

| | says | today |
| --- | --- | --- |
| **G1** | No page asserts a date, a price or an availability that is out of date. | **Not met, and older.** Both classes in `_data/classes.yml` are past — 50 and 35 days (Aug 11, Aug 26). `governance.yml` still says meetings are open with `schedule: ""`. `reserve.md` still asks a member to agree to Equipment Terms and Conditions that do not exist (`CONTENT-TODO.md` still marks it BLOCKING). The "a class is on" surfaces render empty. `OPEN.md` names the class finding as *still unverified*; it is verified, and true. |
| **G2** | Every internal link resolves, including anchors, and `REDIRECTS.md` reports nothing unaccounted for. | **Redirect half: unchanged, one address** — `/equipment`, `REDIRECTS.md:103`. **And newly qualified:** `OPEN.md` states `REDIRECTS.md` records where addresses *will* go, not where they go now, and that the one automated publish check skips `_redirects`. So the report can read clean while every legacy link is dead. **Link-and-anchor half: `unmeasured`** — still no link walk anywhere. |

## What moved that my constituency would notice

Two things, both from the maintainers' own candour in `docs/OPEN.md`, not
from a content change:

- **The check-in promise is untrue on a shared browser.** `/check-in/` and the
  kiosk say *"your visits stay on your phone."* OPEN.md records that on any
  machine more than one person uses, the form prefills the previous visitor's
  name and email. The kiosk sidesteps it (QR only); a staffer helping someone
  at the desk machine does not. New draft T8.
- **The redirect check has a blind spot with a date on it** — folded into T5,
  not a new complaint.

## What would make us stop

Unchanged: a member acts on a promise this site made — a meeting, a class, a
form to agree to, a privacy assurance — and it was not true when they read
it. They do not file a bug; they conclude something about FC Public Media.

## Next session

Monthly, due 2026-10-28. First thing: whether the cutover happened, which
decides whether "will read" becomes "reads". Then the same four files.

## Complaints

### Complaints — truthfulness

The voice of the member who reads the site and believes it. `source: simulated`
unless marked. Everything opens at `draft`.

## T1 · You said I could come to a board meeting, but not when

`status: draft` · `source: observed` · `first said: 2026-09-09`

`meetings.open: true`, `meetings.schedule: ""`. There is a meeting today and the
site could not tell anyone.

`observed` because both halves are in `_data/governance.yml` and the third — that
a meeting is happening today — is why this seat was filled this morning.

The reason I am not writing this as "the page is broken" is that it isn't. It
says the schedule isn't filled in, which is true and is the right thing for it to
say. But the promise above it is the whole point of the page, and a promise you
cannot act on decays into a slogan. One line of plain language closes it: "the
third Tuesday of the month, 6:30pm," or whatever the real answer is.

## T2 · I came for the class that was on the website

`status: draft` · `source: simulated` · `first said: 2026-09-09`

Both classes in the file are in the past — 29 days and 14 days. The calendar
renders empty and the front page strip stays hidden.

The member's version of this complaint is not "your page is broken," it is "I
guess nothing's happening there." It is the most expensive thing on this list and
it will never be reported by anyone, because the person who forms that impression
does not come back to tell you.

## T3 · Is this still accurate, or is it just old?

`status: draft` · `source: simulated` · `first said: 2026-09-09`

The general form of T2, and I am keeping it separate because it will outlive the
specific one. Nothing on this site carries a date that tells a reader how fresh
it is. The airing log is synced weekly and says so; the class calendar is edited
by hand and does not.

Half-formed on purpose. I do not know whether the answer is a visible "last
updated," or a staleness check in CI, or nothing at all — a small nonprofit's
site being a bit behind is normal and not every version of this is a problem.
Recording it as a draft because noticing it cost nothing and forgetting it would
cost the next reader.

## T4 · The word TODO is in the homepage source

`status: draft` · `source: observed` · `first said: 2026-09-09`

"Dropping in without signing up costs TODO, or TODO for members," in the served
HTML of `/`.

**It cannot reach a rendered page.** `classmode.js:54` hides the block on
`dropin.public === 'TODO'`, and the panel is hidden anyway unless a class is live.
I checked before writing this and I am recording the guard as prominently as the
problem, because a complaint that omits the mitigation is how an advocate loses
the right to be believed.

What is left is genuinely small: the string is visible in source and to a reader
without JavaScript. I am opening it as a draft rather than not writing it because
the guard is one line in a JS file, sitting a long way from the prices it
protects, and the next person to touch either will not know the other exists.

## T5 · `/equipment` goes nowhere and the report says so

`status: draft` · `source: observed` · `first said: 2026-09-09`

`REDIRECTS.md` reports thirteen addresses deliberately dropped and one
unaccounted for, and the one is `/equipment`. It has been in that state since the
report was last generated.

The report is doing its job — it says "UNACCOUNTED FOR" in bold, which is the
correct behaviour and is why I know. The complaint is that a known-unaccounted
address has stayed known-unaccounted, which is the state a loud report is
supposed to make uncomfortable.

## T7 · You're asking me to agree to a document that doesn't exist

`status: draft` · `source: observed` · `first said: 2026-09-10`

PR #56, merged this range, shipped this sentence to `reserve.md`: *"Any User of
FC Public Media equipment must agree to FC Public Media's Equipment Terms and
Conditions."* There is no such page and no such PDF anywhere in this
repository. I checked.

I am not the one who found this. `REVIEW-NOTES.md`, merged in the same range,
already says so in its own words: *"It cites a document that does not exist.
This one is still open,"* and ranks it first on the post-review punch list —
*"this is the one that should not sit."* `CONTENT-TODO.md` marks it
**BLOCKING**. The people who wrote the copy know exactly what they shipped.

So my complaint is not that nobody noticed — they did, immediately, in
writing, in the same commit range. It is that the sentence is live on the
reserve page anyway, asking a member for an agreement that does not exist to
be read, while the people who could make it exist have already named it as
the most urgent thing left on the list. A member reading this page today has
no way to know that "should not sit" and "sitting" are both true of the same
sentence at once.

Related, same commit, smaller: the same paragraph changed what the credit
card on file is *for* — from a temporary hold to a card kept for "late fees
and incidentals," a different arrangement, not just different wording.
`REVIEW-NOTES.md` flags this too, as unconfirmed against how checkout
actually runs. I am not opening a separate complaint for it; it is the same
shape — copy that now promises something nobody has verified is true — and it
travelled here in the same sentence.

## T8 · It said my visits stay on my phone, and I was at the desk computer

`status: draft` · `source: observed` · `first said: 2026-09-30`

`/check-in/` and the kiosk both promise *"your visits stay on your phone."*
`docs/OPEN.md` (2026-09-23) records that on any browser more than one person
uses, `checkin.js` keeps name, reason, note and email in `localStorage` and
prefills them for the next visitor. The realistic case is a staffer opening the
page on the desk machine to help someone who is stuck.

As with T7, I did not find this — the maintainers wrote it down, with a check
to reproduce it. The kiosk avoids it by design (QR only). What the member
cannot know is that the promise holds on their phone and not on the machine at
the desk. Draft: whether shared-machine use should be designed for at all is
explicitly undecided upstream, and I do not hold a view.

## T6 · Nothing here checks that our own links work

`status: draft` · `source: simulated` · `first said: 2026-09-09`

My second goal wants every internal link to resolve, anchors included. Nothing in
this repository measures that. The Playwright suite tests behaviour, the Python
tests cover the sync scripts and the price list, and the smoke workflow builds
the site — none of them walks the links.

The constitution notes that pages here get merged deliberately and often, and
that `/equipment/` and `/reservations/` both disappeared inside a week. That is
the pattern that produces dead internal links, and it is running.

Kept as a complaint rather than an ask because I have not decided what the right
shape is, and the honest state of my thinking is "there is a hole here."

---

**2026-09-30:** Checked T1–T7 against current state (I could not diff the
range; I read the files). None closed. T1: `governance.yml` schedule still `""`.
T2: classes now 50 and 35 days past; `OPEN.md` calls this unverified, it is
verified. T4: `dropin` still `TODO` in `classes.yml`, guard not re-read. T5:
`/equipment` still unaccounted (`REDIRECTS.md:103`) — **widened:** `OPEN.md`
says that report records where addresses *will* go and that the publish check
skips `_redirects`, so a clean report would not mean the links work. T6: still
no link check. T7: sentence still in `reserve.md`; `CONTENT-TODO.md` still
BLOCKING. The cutover was aimed at the weekend after 09-24; all of the above
may now be public-facing, and I cannot tell. T8 opened.

**2026-09-10:** Checked T1–T6 against the range. None closed — `governance.yml`
is byte-identical, the two classes are a day further into the past, the TODO
guard is untouched, `/equipment` is still unaccounted for, no link check was
added. T7 opened, `observed`, evidenced by the site's own `REVIEW-NOTES.md`.

**2026-09-09:** Nothing closed. First session; there was nothing to close.

## Asks

### Asks — truthfulness

Shapes, not instructions. No `writes:` grant, so none of these is a pull request.

## A1 · The board meeting schedule, in plain language

`status: draft` · `target: FCPM board` · `first said: 2026-09-09`

**Shape:** a member of the public who reads the open-meetings promise can act on
it.

One line in `_data/governance.yml`, in the words the file already asks for — "the
third Tuesday of the month, 6:30pm." The page is built for it and currently says
it is missing.

This is the cheapest ask any seat is holding and it closes the most visible gap I
found. If exactly one thing comes out of this council's first round, I would
like it to be this one.

## A2 · Something that notices when the calendar has emptied itself

`status: draft` · `target: whoever maintains the site` · `first said: 2026-09-09`

**Shape:** the difference between "nothing is scheduled" and "nobody has updated
the file since August" is visible to somebody who could act on it, without a
person happening to look.

Deliberately unspecified. A check in the weekly sync, a line in a report, a
staleness warning in the build — any would satisfy it. What would *not* satisfy
it is inventing a class to fill the gap, which is out of scope for me and would
be worse than the empty page.

## A3 · A decision about `/equipment`

`status: draft` · `target: whoever maintains the redirects` · `first said: 2026-09-09`

**Shape:** `REDIRECTS.md` reports nothing unaccounted for, either because the
address is redirected or because it is recorded as deliberately dropped.

Thirteen addresses are already in the "deliberately dropped" column, so the
mechanism for saying "we chose this" exists and is used. `/equipment` just has
not been through it. Either answer closes my goal; I have no view on which is
right.

*2026-09-30:* `OPEN.md` now says the redirect report describes intent, not
live behaviour, and that nobody owns the one post-cutover check. A clean
report therefore would not fully close G2's redirect half; someone has to hit
a real legacy URL once after any change of publisher. Same shape, stated once.

## A5 · A way to know, before copy ships, that what it names exists

`status: draft` · `target: whoever reviews content before merge` · `first said: 2026-09-10`

**Shape:** an editor approving copy that names a policy, a document, or an
agreement needs to know whether that thing exists yet, at the point of
approving it, not after.

This is not A4. A4 is a broken hyperlink — a technical check could catch it.
"Must agree to FC Public Media's Equipment Terms and Conditions" is not a
link at all; it is prose naming a document, deliberately left unlinked rather
than pointed at a 404, so nothing a crawler runs would ever flag it. The
review that would catch it already happened — `REVIEW-NOTES.md` caught it in
the same commit that shipped it — which tells me the gap is not noticing, it
is that noticing and shipping happened in the same breath with nothing
between them.

I have no view on what closes this. A checklist item, a rule that named
documents ship together with the copy that cites them, or nothing at all if
the org decides "ship the promise, backfill the document fast" is an
acceptable order for a small team — that is a judgment call I don't hold.

## A4 · Some way to know our internal links resolve

`status: draft` · `target: whoever maintains the tests` · `first said: 2026-09-09`

**Shape:** a page that links to something this site no longer serves is caught
before a member clicks it.

Anchors included, which is the harder half and the one that rots quietest.

I am stating this as a shape and stopping, deliberately: my out-of-scope does not
cover test design, and the constitution is explicit that an advocate reading the
existing automation and following it beats inventing a parallel one. There may
already be a route to this through `script/` that I have not found.

## Last session note — 2026-10-07

### 2026-10-07

Subject unchanged at `919a413`. Nothing merged since the last session; nothing to say.

