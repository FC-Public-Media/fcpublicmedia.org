# `site/bin/sync-schedule.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

Cablecast already records every airing, keyed to the same show IDs that are
already in site/_data/cablecast.json. So rerun history is not something to build —
it is a join. This script does the pulling and the counting; the archive page
does the join.

    python3 site/bin/sync-schedule.py
    python3 site/bin/sync-schedule.py --days 90

WHAT IT IS FOR
--------------
Not "when is this on next" — the forward window is nearly empty, because
scheduling here happens close in. It is for the other direction: how often has
each program run, when did it last run, and *what has not run at all*.

That last question is the interesting one. A three-month sample found 137
distinct programs airing out of 1,060 in the catalogue, with the top rotation
running about twice a day. A station with a thousand programs airing a
hundred of them has a discovery problem inside its own library, and this file
is what makes that visible rather than suspected.

ON PRIVACY
----------
There is none to protect. Cablecast serves this to anyone who asks, with no
key, and it is a broadcast schedule — the least secret thing the station owns.
It belongs on the public archive page, not behind a login.

ON THE WINDOW
-------------
A year by default, fetched a month at a time because a single year-long query
times out. Widen it and the run gets slower; narrow it and "last aired" stops
being able to say "not in the last year", which is the answer that matters
most.

## 2

Above `SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`

`site/bin/` is inside the Jekyll source, so a path here is relative to the
site rather than to the repository. SITE is the build root; REPO is the node.

## 3

Above `start = now - dt.timedelta(days=days)`

Month-sized ranges covering the period, oldest first.

A single year-long query times out on their end — the whole range is
thousands of items — so it is chunked. Months rather than weeks because
the request count is what costs, not the response size.

## 4

Above `if item.get("deleted") or item.get("filler"):`

Deleted slots did not happen. Filler is real airtime but it is
not programming, and counting it would make the rotation look
healthier than it is.

## 5

Above `try:`

Report titles that appear on more than one catalogue record.

Two kinds of thing look identical here and only a human can tell them
apart. "Democracy Now" on 249 records is a daily series whose episodes
were never given individual titles — correct, if unhelpful. The same
program uploaded twice is a genuine duplicate, and it splits that
program's airing history across two records, so "last aired" is wrong
for exactly the shows that air most.

Reported rather than fixed. Merging records is a decision for whoever
owns the Cablecast catalogue, and guessing from a title would eventually
merge two things that only share a name.

## 6

Above `if errors and not shows:`

Every window failing means the API changed or is down, and writing an
empty file over a good one would erase the archive's airing data.
