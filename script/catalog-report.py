#!/usr/bin/env python3
"""Look for things wrong in the Cablecast catalog that only a person can fix.

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
"""

import argparse
import collections
import datetime
import difflib
import json
import pathlib
import re
import sys

DEFAULT_CATALOG = "_data/cablecast.json"

# How alike two titles have to be before one looks like a typo of the other.
# 0.90 finds "democrracy now" and "brickwall"; loosening it starts pairing
# genuinely different episodes of the same series.
TYPO_RATIO = 0.90

# A title has to be this common before a near-miss of it counts as a typo
# rather than as two rare things that happen to look alike.
TYPO_ESTABLISHED = 5

# Above this, a repeated title is a series and its episodes will naturally
# share runtimes — 140 episodes of a daily hour-long news programme are all
# 3542 seconds. Below it, an exact repeat is probably one record entered twice.
DUPLICATE_CEILING = 3

# How recent a local production has to be before it not being watchable is a
# task rather than a fact about the archive.
RECENT_DAYS = 365


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()



# --------------------------------------------------------------- actionable


def typos(items):
    """A rare title one small edit away from an established one."""
    counts = collections.Counter(normalize(i["title"]) for i in items)
    established = [t for t, n in counts.items() if n >= TYPO_ESTABLISHED]

    found = []
    for title, n in counts.items():
        if n > 2:
            continue
        for other in established:
            if abs(len(title) - len(other)) > 2:
                continue
            ratio = difflib.SequenceMatcher(None, title, other).ratio()
            if TYPO_RATIO <= ratio < 1.0:
                actual = next(i for i in items if normalize(i["title"]) == title)
                found.append(
                    {
                        "id": actual["id"],
                        "title": actual["title"],
                        "looks_like": next(
                            i["title"] for i in items if normalize(i["title"]) == other
                        ),
                        "count": counts[other],
                    }
                )
                break
    return found


def miscredits(items):
    """One episode of a series credited to somebody the rest of it is not.

    Found the real one: 28 episodes of Brick Wall by Jorie Kramer and a
    twenty-ninth credited to Free Speech TV, who distribute a daily news
    programme and did not make a local music show.
    """
    groups = collections.defaultdict(list)
    for item in items:
        groups[normalize(item["title"])].append(item)

    found = []
    for title, group in groups.items():
        if len(group) < 4:
            continue
        counts = collections.Counter((i.get("producer") or "").strip() for i in group)
        winner, majority = counts.most_common(1)[0]
        if not winner:
            continue

        for producer, n in counts.items():
            if producer == winner or n > max(1, len(group) // 10):
                continue
            for item in group:
                if (item.get("producer") or "").strip() == producer:
                    found.append(
                        {
                            "id": item["id"],
                            "title": item["title"],
                            "credited": producer or "(nobody)",
                            "expected": winner,
                            "majority": majority,
                        }
                    )
    return found


def mixed_local(items):
    """The same series marked as ours in some records and not in others."""
    groups = collections.defaultdict(list)
    for item in items:
        groups[normalize(item["title"])].append(item)

    found = []
    for title, group in groups.items():
        flags = {bool(i.get("local")) for i in group}
        if len(flags) < 2:
            continue
        odd = [i for i in group if not i.get("local")]
        usual = len(group) - len(odd)
        if len(odd) <= usual:
            for item in odd:
                found.append({"id": item["id"], "title": item["title"], "others": usual})
    return found


def duplicates(items):
    """The same record twice: one title, one producer, one runtime.

    Scoped to titles that are not a series, because a daily programme's
    episodes legitimately share a runtime — without the ceiling this reports
    two hundred false positives and nothing else.
    """
    counts = collections.Counter(normalize(i["title"]) for i in items)
    seen = collections.defaultdict(list)

    for item in items:
        title = normalize(item["title"])
        if counts[title] > DUPLICATE_CEILING or not item.get("seconds"):
            continue
        seen[(title, (item.get("producer") or "").strip(), item["seconds"])].append(item)

    return [
        {
            "title": group[0]["title"],
            "ids": [i["id"] for i in group],
            "seconds": group[0]["seconds"],
        }
        for group in seen.values()
        if len(group) > 1
    ]


def unwatchable_local(items, today=None):
    """Something we made recently that nobody can watch.

    Syndicated material is often unavailable online for rights reasons, and
    that is expected. Our own production not being watchable is either a
    missing file or a setting somebody meant to change.

    RECENT ONLY, and the catalog is why. Twenty of our own productions are
    unwatchable and not one is newer than 2024 — those are history, and
    listing them every month would mean this report was never quiet again.
    Something from this year is a mistake somebody can still act on. The
    standing counts carry the full number.
    """
    horizon = ((today or datetime.date.today()) - datetime.timedelta(days=RECENT_DAYS)).isoformat()

    return [
        {"id": i["id"], "title": i["title"], "producer": i.get("producer") or ""}
        for i in items
        if i.get("local") and not i.get("watchable") and (i.get("date") or "") >= horizon
    ]


# ----------------------------------------------------------------- standing


def standing(items):
    """Counts, not tasks. Context for whoever is reading, and nothing more."""
    return {
        "records": len(items),
        "no producer": sum(1 for i in items if not (i.get("producer") or "").strip()),
        "no thumbnail": sum(1 for i in items if not (i.get("thumb") or "").strip()),
        "no runtime": sum(1 for i in items if not i.get("seconds")),
        "not watchable": sum(1 for i in items if not i.get("watchable")),
        "ours and not watchable": sum(
            1 for i in items if i.get("local") and not i.get("watchable")
        ),
    }


# ------------------------------------------------------------------- report


CHECKS = [
    ("Titles that look like typos", typos, "typo"),
    ("Episodes credited to the wrong producer", miscredits, "miscredit"),
    ("Series marked as ours inconsistently", mixed_local, "mixed"),
    ("Records that appear to be duplicates", duplicates, "duplicate"),
    ("Ours, recent, and not watchable", unwatchable_local, "unwatchable"),
]


def show(kind, finding):
    link = "https://reflect-fcpublicmedia.cablecast.tv/internetchannel/show/"

    if kind == "typo":
        return (
            f"- [`{finding['id']}`]({link}{finding['id']}) **{finding['title']}** — "
            f"probably meant to be *{finding['looks_like']}*, which {finding['count']} "
            f"other records use."
        )
    if kind == "miscredit":
        return (
            f"- [`{finding['id']}`]({link}{finding['id']}) **{finding['title']}** — "
            f"credited to *{finding['credited']}*, but the other {finding['majority']} "
            f"episodes are *{finding['expected']}*."
        )
    if kind == "mixed":
        return (
            f"- [`{finding['id']}`]({link}{finding['id']}) **{finding['title']}** — "
            f"not marked local, but {finding['others']} others with this title are."
        )
    if kind == "duplicate":
        ids = ", ".join(f"[`{i}`]({link}{i})" for i in finding["ids"])
        return f"- **{finding['title']}** — {ids}, all {finding['seconds']}s."
    return (
        f"- [`{finding['id']}`]({link}{finding['id']}) **{finding['title']}**"
        + (f" — {finding['producer']}" if finding["producer"] else "")
    )


def build(items):
    sections = []
    total = 0
    for heading, check, kind in CHECKS:
        found = check(items)
        total += len(found)
        if found:
            sections.append((heading, [show(kind, f) for f in found]))

    lines = []
    if total:
        lines.append(
            "Lining the catalog up against itself found things that look wrong. "
            "None of these can be fixed here — the records live in Cablecast, and "
            "the next sync picks up whatever you change there."
        )
        lines.append("")
        for heading, rows in sections:
            lines.append(f"### {heading}")
            lines.append("")
            lines.extend(rows)
            lines.append("")
    else:
        lines.append("Nothing looks wrong this month. Nothing to do.")
        lines.append("")

    lines.append("### Standing counts")
    lines.append("")
    lines.append("Facts about a fifteen-year-old catalog rather than tasks.")
    lines.append("")
    for label, value in standing(items).items():
        lines.append(f"- {value} {label}")

    return total, "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--out", help="write the report here as well as to stdout")
    parser.add_argument(
        "--count-only",
        action="store_true",
        help="print just the number of actionable findings",
    )
    args = parser.parse_args(argv)

    items = json.loads(pathlib.Path(args.catalog).read_text(encoding="utf-8"))["shows"]
    total, report = build(items)

    if args.count_only:
        print(total)
        return 0

    if args.out:
        pathlib.Path(args.out).write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
