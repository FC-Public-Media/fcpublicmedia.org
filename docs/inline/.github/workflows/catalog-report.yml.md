# `.github/workflows/catalog-report.yml`

Moved out of the file. Unreviewed.

## 1

Above `on:`

Once a month, line the Cablecast catalog up against itself and say what looks
wrong. Nothing it finds can be fixed here — the records live in Cablecast,
and the next sync picks up whatever gets changed there.

WHY MONTHLY WHEN WE RELEASE WEEKLY
----------------------------------
Because it should almost always say nothing. These are data-entry mistakes in
a fifteen-year-old catalog: a typo, a miscredit, one record entered twice.
They arrive at the rate somebody makes them, which is not weekly, and a
report that turns up every seven days carrying the same list is a report
nobody opens by March.

QUIET MEANS QUIET
-----------------
One issue, reused. Findings update it; no findings closes it. A month with
nothing wrong produces no notification at all — not an issue saying "all
clear", which is the same noise in a friendlier voice.

The first run will not be quiet, and that is the point of building it: there
is a backlog nobody could see until the archive was grouped by show.

## 2

Above `- cron: "0 16 12 * *"`

The 12th, a few days after the show proposals, so a month's worth of
catalog housekeeping arrives together rather than scattered.

## 3

Above `- name: Put it in the run summary`

Visible whether or not an issue gets opened, so a run that found
nothing still leaves a record of having looked.

## 4

Above `gh issue comment "$existing" --body \`

Everything that was reported has been dealt with. Say so where
the work was tracked, then get out of the way.

## 5

Above `gh issue edit "$existing" --body-file /tmp/report.md`

Edited rather than commented on. A monthly comment thread on a
list that has not changed is how an issue becomes unreadable.
