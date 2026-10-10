# `site/bin/catalog-report.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

WHY THIS EXISTS
---------------
Grouping the archive by show made two errors visible that nobody would have
found by looking: one item titled "Brick Wall" credited to Free Speech TV when
the other twenty-eight are Jorie Kramer's, and an episode titled "Democrracy
Now". Neither is a bug in this repository. Both are records in Cablecast that
say something untrue, and both are invisible until you line the catalog up
against itself.

So: line it up once a month and say what looks wrong.

THE THING THAT DECIDES WHETHER THIS IS USEFUL
---------------------------------------------
It has to be quiet. A report that arrives every month carrying the same fifty
items with no producer is a report nobody reads by March, and then the one
month it says something new is the month it gets ignored.

So findings are split in two:

  * ACTIONABLE — small, specific, and fixable. A typo, a miscredit, a
    duplicated record. These open an issue.
  * STANDING — chronic counts. Fifty items with no producer is a data quality
    fact about a fifteen-year-old catalog, not a task. These ride along for
    context and never trigger anything on their own.

When the actionable list is empty the report says so and the workflow closes
the issue. Most months should be empty.

NOT A LINTER FOR OUR CODE
-------------------------
Everything here is about someone else's data. Nothing it reports can be fixed
by editing this repository — the fixes happen in Cablecast, and the next sync
picks them up. That is why it is a report and not a test.

## 2

Above `TYPO_RATIO = 0.90`

How alike two titles have to be before one looks like a typo of the other.
0.90 finds "democrracy now" and "brickwall"; loosening it starts pairing
genuinely different episodes of the same series.

## 3

Above `TYPO_ESTABLISHED = 5`

A title has to be this common before a near-miss of it counts as a typo
rather than as two rare things that happen to look alike.

## 4

Above `DUPLICATE_CEILING = 3`

Above this, a repeated title is a series and its episodes will naturally
share runtimes — 140 episodes of a daily hour-long news programme are all
3542 seconds. Below it, an exact repeat is probably one record entered twice.

## 5

Above `RECENT_DAYS = 365`

How recent a local production has to be before it not being watchable is a
task rather than a fact about the archive.

## 6

Above `groups = collections.defaultdict(list)`

One episode of a series credited to somebody the rest of it is not.

Found the real one: 28 episodes of Brick Wall by Jorie Kramer and a
twenty-ninth credited to Free Speech TV, who distribute a daily news
programme and did not make a local music show.

## 7

Above `counts = collections.Counter(normalize(i["title"]) for i in items)`

The same record twice: one title, one producer, one runtime.

Scoped to titles that are not a series, because a daily programme's
episodes legitimately share a runtime — without the ceiling this reports
two hundred false positives and nothing else.

## 8

Above `horizon = ((today or datetime.date.today()) - datetime.timedelta(days=RECENT_DAYS)).isoformat()`

Something we made recently that nobody can watch.

Syndicated material is often unavailable online for rights reasons, and
that is expected. Our own production not being watchable is either a
missing file or a setting somebody meant to change.

RECENT ONLY, and the catalog is why. Twenty of our own productions are
unwatchable and not one is newer than 2024 — those are history, and
listing them every month would mean this report was never quiet again.
Something from this year is a mistake somebody can still act on. The
standing counts carry the full number.
