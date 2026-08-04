#!/usr/bin/env python3
"""Pull the broadcast schedule into _data/airings.json.

Cablecast already records every airing, keyed to the same show IDs that are
already in _data/cablecast.json. So rerun history is not something to build —
it is a join. This script does the pulling and the counting; the archive page
does the join.

    python3 script/sync-schedule.py
    python3 script/sync-schedule.py --days 90

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
"""

import argparse
import collections
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(ROOT, "_data", "airings.json")
CATALOG = os.path.join(ROOT, "_data", "cablecast.json")

TIMEOUT = 120
ATTEMPTS = 3
BACKOFF = 3


def fetch(path, sleeper=time.sleep):
    """GET with retries. A year of history is a lot of requests to get right."""
    last = None
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(
                BASE + path, headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.load(response)
        except Exception as error:  # noqa: BLE001 — retried, then reported
            last = error
            if attempt < ATTEMPTS - 1:
                sleeper(BACKOFF * (2**attempt))
    raise last


def windows(days, now):
    """Month-sized ranges covering the period, oldest first.

    A single year-long query times out on their end — the whole range is
    thousands of items — so it is chunked. Months rather than weeks because
    the request count is what costs, not the response size.
    """
    start = now - dt.timedelta(days=days)
    spans = []
    while start < now:
        end = min(start + dt.timedelta(days=30), now)
        spans.append((start.date().isoformat(), end.date().isoformat()))
        start = end
    return spans


def collect(days, now, fetcher=fetch, channel=1):
    """Airings per show. Returns (shows, totals, errors)."""
    counts = collections.Counter()
    first = {}
    last = {}
    slots = 0
    errors = []

    for start, end in windows(days, now):
        path = (
            f"/scheduleitems?channel={channel}"
            f"&start={start}&end={end}&page_size=5000"
        )
        try:
            payload = fetcher(path)
        except Exception as error:  # noqa: BLE001
            errors.append({"window": f"{start}..{end}", "error": str(error)})
            print(f"  {start}..{end}: {error}", file=sys.stderr)
            continue

        items = payload.get("scheduleItems") or []
        kept = 0
        for item in items:
            # Deleted slots did not happen. Filler is real airtime but it is
            # not programming, and counting it would make the rotation look
            # healthier than it is.
            if item.get("deleted") or item.get("filler"):
                continue
            show = item.get("show")
            when = (item.get("runDateTime") or "")[:10]
            if not show or not when:
                continue

            counts[show] += 1
            kept += 1
            if show not in first or when < first[show]:
                first[show] = when
            if show not in last or when > last[show]:
                last[show] = when

        slots += kept
        print(f"  {start}..{end}: {kept}", file=sys.stderr)

    shows = {
        str(show): {"airings": n, "first": first[show], "last": last[show]}
        for show, n in counts.items()
    }
    return shows, {"slots": slots, "distinct": len(shows)}, errors


def report_shared_titles():
    """Report titles that appear on more than one catalogue record.

    Two kinds of thing look identical here and only a human can tell them
    apart. "Democracy Now" on 249 records is a daily series whose episodes
    were never given individual titles — correct, if unhelpful. The same
    program uploaded twice is a genuine duplicate, and it splits that
    program's airing history across two records, so "last aired" is wrong
    for exactly the shows that air most.

    Reported rather than fixed. Merging records is a decision for whoever
    owns the Cablecast catalogue, and guessing from a title would eventually
    merge two things that only share a name.
    """
    try:
        with open(CATALOG, encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, ValueError):
        return

    titles = collections.Counter(
        (show.get("title") or "").strip().lower()
        for show in catalog.get("shows", [])
        if (show.get("title") or "").strip()
    )
    repeated = {title: n for title, n in titles.items() if n > 1}
    if repeated:
        print(
            f"\n{len(repeated)} title(s) sit on more than one catalogue "
            "record. Some are series with untitled episodes; some are the "
            "same program entered twice, and those have their airing history "
            "split in two. Worth a look:",
            file=sys.stderr,
        )
        for title, n in sorted(repeated.items(), key=lambda kv: -kv[1])[:5]:
            print(f"  {n}x  {title[:60]}", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--days", type=int, default=365, help="how far back to look")
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--out", default=OUTPUT)
    parser.add_argument("--now", help="override the clock, for tests. ISO 8601.")
    args = parser.parse_args(argv)

    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)

    print(f"Reading {args.days} days of schedule...", file=sys.stderr)
    shows, totals, errors = collect(args.days, now, channel=args.channel)

    # Every window failing means the API changed or is down, and writing an
    # empty file over a good one would erase the archive's airing data.
    if errors and not shows:
        print("No schedule could be read; leaving the existing data alone.", file=sys.stderr)
        return 1

    payload = {
        "_note": (
            "Generated by script/sync-schedule.py from Cablecast's public "
            "schedule API. Airings per show over the window below; join on "
            "the show id in _data/cablecast.json. Filler and deleted slots "
            "are not counted."
        ),
        "generated": now.isoformat(),
        "window_days": args.days,
        "since": (now - dt.timedelta(days=args.days)).date().isoformat(),
        "channel": args.channel,
        "totals": totals,
        "errors": errors,
        "shows": shows,
    }

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True)
        handle.write("\n")

    print(
        f"\n{totals['slots']:,} airings of {totals['distinct']} distinct "
        f"programs over {args.days} days.",
        file=sys.stderr,
    )
    report_shared_titles()
    return 0


if __name__ == "__main__":
    sys.exit(main())
