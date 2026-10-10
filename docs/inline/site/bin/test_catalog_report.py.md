# `site/bin/test_catalog_report.py`

Moved out of the file. Unreviewed.

## 1

Above `import datetime`

Tests for the catalog report.

The failure that matters here is not missing something. It is crying wolf: a
report that lists two hundred false positives every month gets ignored, and
then the month it says something true it gets ignored too.

So most of these are about what the report REFUSES to say.

## 2

Above `catalog = [item(n, "Brick Wall") for n in range(10)]`

"Brickwall" against twenty-nine "Brick Wall" — found in the real
catalog and easy to miss by eye.

## 3

Above `catalog = [item(1, "River Walk"), item(2, "River Talk")]`

Neither is established, so there is no reason to think one is a
mistyping of the other rather than two different programmes.

## 4

Above `catalog = [item(n, "Shared Show", producer="One") for n in range(5)]`

A show that genuinely changed hands, or has co-producers. Half and
half is not somebody's mistake.

## 5

Above `catalog = [item(1, "Thing", producer="A"), item(2, "Thing", producer="B")]`

Three episodes with three credits is not enough to call any of them
the odd one out.

## 6

Above `catalog = [item(n, "Democracy Now", seconds=3542) for n in range(140)]`

THE false positive this check exists to avoid. A hundred and forty
episodes of an hour-long news programme are all 3542 seconds, and
reporting them would bury everything else.

## 7

Above `catalog = [item(n, f"Old Thing {n}", watchable=False, date="2023-05-01") for n in range(20)]`

Twenty of ours are unwatchable and none is newer than 2024. Listing
them monthly would mean this report was never quiet, which is the
one thing it has to be.

## 8

Above `catalog = [item(n, "Brick Wall", producer="Jorie") for n in range(28)]`

Whoever reads this has to open it in Cablecast to fix it, and
copying an ID out of a code block is a worse morning.

## 9

Above `self.assertIsInstance(total, int)`

Not an assertion about the count — it should go down as things get
fixed, and up when somebody fat-fingers a title. This is here so a
change that throws on real data fails in CI rather than in a
scheduled run nobody is watching.

## 10

Above `self.assertLess(total, 60, "the report is too long to be read")`

And the thing this was built to avoid: a report so long nobody reads
it. If it ever gets here, a check needs scoping rather than the
threshold being raised.
