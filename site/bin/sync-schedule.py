#!/usr/bin/env python3
"""Pull the broadcast schedule into site/_data/airings.json.

    python3 site/bin/sync-schedule.py
    python3 site/bin/sync-schedule.py --days 90

Airings per show id, joined with site/_data/cablecast.json by the pages.
See docs/programming.md.
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
# site/bin/ is inside the Jekyll source; SITE is the build root.
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(SITE, "_data", "airings.json")
CATALOG = os.path.join(SITE, "_data", "cablecast.json")

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
    """Month-sized ranges covering the period, oldest first: a year in one query times out."""
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
            # Deleted slots did not air, and filler is not programming.
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
    """Report titles on more than one catalog record. Reported only: a person decides what merges."""
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

    # Nothing read: keep the existing file rather than erase the airing data.
    if errors and not shows:
        print("No schedule could be read; leaving the existing data alone.", file=sys.stderr)
        return 1

    payload = {
        "_note": (
            "Generated by site/bin/sync-schedule.py from Cablecast's public "
            "schedule API. Airings per show over the window below; join on "
            "the show id in site/_data/cablecast.json. Filler and deleted slots "
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
