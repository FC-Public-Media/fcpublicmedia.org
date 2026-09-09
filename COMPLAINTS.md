# Complaints — truthfulness

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

**Nothing closed this session.** First session; there was nothing to close.
