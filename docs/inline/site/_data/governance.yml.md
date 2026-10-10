# `site/_data/governance.yml`

Moved out of the file. Unreviewed.

## 1

Above `meetings:`

How the board runs, and what a member of the public can turn up to.

The point of this file is one sentence on the page it feeds: our board
meetings are open, and you can come to one. Everything else here is in
service of making that sentence usable — when, where, and what happens if
you walk in.

A NOTE ON WHAT WE ARE NOT
-------------------------
FCPM is a 501(c)(3) nonprofit, not a public body. Colorado's Open Meetings
Law covers state and local government, and does not apply here. So none of
this is a legal obligation being met — it is a choice the board made, which
is a better thing to say and the only accurate one. Nothing on the page
should imply a statute is being complied with.

MINUTES
-------
Minutes are a record, not a publication. Linking a folder for anyone curious
enough to look is a different act from putting decisions on the front page,
and this file keeps the two apart on purpose. Leave `minutes.url` empty and
the page offers to send them on request instead, which is a perfectly good
answer and needs nothing set up.

## 2

Above `open: true`

Is the public welcome? If this is ever false, the page changes entirely
rather than going quiet — a board that has closed its meetings should say
so plainly rather than let an old invitation sit there.

## 3

Above `schedule: ""`

Plain language, not a cron expression. "The third Tuesday of the month,
6:30pm" is what someone needs to decide whether they can make it.

## 4

Above `location: ""`

Where the meeting happens. Left empty, the page falls back to the studio
address in _data/org.yml, which is the usual answer.

## 5

Above `what_to_expect: ""`

Anything a first-time attendee would otherwise have to ask: whether to
tell someone in advance, whether there is a public comment period, whether
it is worth bringing anything.

## 6

Above `recorded: false`

Meetings are not recorded. Said out loud because a visitor who assumes
otherwise may speak differently, and because it explains why the minutes
are the only record there is.

## 7

Above `upcoming: []`

Optional. Specific dates, for when the schedule alone is not enough — a
special meeting, or an annual meeting that breaks the pattern. These also
appear in the merged list on /community/, so a neighbour who never visits
this page still sees them.

TIMES MUST CARRY AN OFFSET — "2026-09-15T18:30:00-06:00", not
"2026-09-15 18:30". Same rule as _data/classes.yml and _data/community.yml,
and for the same reason: a time without one is read as the visitor's own
zone, which is silently wrong for anyone travelling.

## 8

Above `minutes:`

- starts: "2026-09-15T18:30:00-06:00"
  note: Annual meeting — board elections.

## 9

Above `url: ""`

A link to wherever minutes live: a shared folder, a Drive link, anything
that opens. Empty is fine and is the shipped state — the page then offers
to send them on request, using the address below.

## 10

Above `note: >-`

What the link is, in the visitor's terms. Sets expectations before they
click something that turns out to be a folder of PDFs.

## 11

Above `request_email: ""`

Who to ask when there is no link. Falls back to the general address in
_data/org.yml when empty.

## 12

Above `documents: []`

Documents a nonprofit is commonly asked for. Each needs a name and a url;
entries without a url are skipped entirely rather than rendered as a dead
link, so it is safe to list what you intend to publish before it exists.

## 13

- name: Bylaws
  url: /assets/docs/bylaws.pdf
- name: Form 990 (2025)
  url: https://…
