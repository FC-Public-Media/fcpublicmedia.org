#!/usr/bin/env python3
"""Pull calendar events into _data/calendar.json at build time.

    python3 script/sync-calendar.py --ics "https://outlook.office365.com/....ics"
    python3 script/sync-calendar.py --ics "$FCPM_CALENDAR_ICS" --weeks 8

WHY BUILD TIME
--------------
The schedule changes a few times a month and is identical for everybody. Having
each visitor's browser ask Microsoft for it would be the same answer fetched
thousands of times, would put a key or a public endpoint in the client, and
would leave the page blank whenever Microsoft is slow. Fetching it once per
build and shipping the answer as part of the page is faster, cheaper, private,
and works offline. Same reasoning as script/sync-cablecast.py.

TWO WAYS IN, AND THEY SUIT DIFFERENT DATA
-----------------------------------------
1. **Published ICS** — what this script implements. In Outlook on the web:
   Settings > Calendar > Shared calendars > Publish a calendar. Publish a
   calendar that holds only what is meant to be public, take the ICS link, and
   hand it to this script.

   No app registration, no admin consent, no client secret, nothing that
   expires. The trade is that the link is public to anyone who has it — which
   is fine for a class schedule, and not fine for anything else. Publish a
   dedicated "Public Programming" calendar rather than someone's own.

2. **Microsoft Graph** — needed for anything not public: room free/busy,
   reservation details, the hidden nonce on a booking. Use `calendarView`
   rather than `/events`: `/events` returns the recurrence master, while
   `calendarView` expands a recurring series into real occurrences across a
   date window, which is the shape a website wants.

   From GitHub Actions, authenticate with **workload identity federation**
   rather than a client secret — GitHub's OIDC token is exchanged for a Graph
   token, so there is no secret stored and nothing to rotate. Entra client
   secrets expire within 24 months and would otherwise become a calendar
   reminder nobody keeps.

   If Graph app-only is used, note that `Calendars.Read` as an *application*
   permission grants read access to **every mailbox in the tenant**. Scope it
   with an Application Access Policy (`New-ApplicationAccessPolicy`) pointed at
   a mail-enabled security group holding just the calendars in question. This
   is the sharp edge; it is easy to grant far more than intended.

RECURRENCE
----------
Published ICS describes a repeating event once, with an RRULE, rather than
listing each occurrence. Expanding those correctly — with exceptions, moved
instances and daylight saving — is a genuine piece of work and not something
to hand-roll. This script does not: it reports them and skips them, loudly,
rather than quietly getting them wrong.

If FCPM starts running recurring classes, that is the moment to move to Graph
`calendarView`, which does the expansion server-side and hands back real
occurrences.

Standard library only.
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "_data", "calendar.json")

# Outlook frequently writes Windows zone names into TZID rather than IANA
# identifiers, and zoneinfo has never heard of "Mountain Standard Time". These
# are the ones a Colorado organisation plausibly encounters; anything else is
# refused rather than guessed at, because being silently an hour out twice a
# year is worse than a visible error. The full mapping lives in CLDR's
# windowsZones.xml if this ever needs extending.
WINDOWS_ZONES = {
    "Mountain Standard Time": "America/Denver",
    "US Mountain Standard Time": "America/Phoenix",
    "Central Standard Time": "America/Chicago",
    "Eastern Standard Time": "America/New_York",
    "Pacific Standard Time": "America/Los_Angeles",
    "Alaskan Standard Time": "America/Anchorage",
    "Hawaiian Standard Time": "Pacific/Honolulu",
    "UTC": "UTC",
    "GMT Standard Time": "Europe/London",
}


# --------------------------------------------------------------------- ical

def unfold(text):
    """ICS wraps long lines by starting the continuation with a space or tab."""
    return re.sub(r"\r?\n[ \t]", "", text)


def unescape(value):
    return (
        value.replace("\\n", "\n")
        .replace("\\N", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def parse_when(value, params):
    """Return (datetime, is_all_day) or (None, False) if it can't be read.

    Handles the three forms published calendars actually emit: UTC with a
    trailing Z, a date-only value for all-day events, and a local time with a
    TZID parameter.

    Never raises. One malformed event in a feed should be reported and skipped,
    not take down the whole sync — a calendar is other people's data and will
    eventually contain something unexpected.
    """
    try:
        return _parse_when(value, params)
    except Exception:
        return None, False


def _parse_when(value, params):
    value = value.strip()

    # All-day: VALUE=DATE, 20260811
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return dt.datetime.strptime(value, "%Y%m%d").replace(tzinfo=dt.timezone.utc), True

    if value.endswith("Z"):
        stamp = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        return stamp.replace(tzinfo=dt.timezone.utc), False

    naive = dt.datetime.strptime(value, "%Y%m%dT%H%M%S")

    tzid = params.get("TZID", "").strip('"')
    if tzid:
        from zoneinfo import ZoneInfo

        for candidate in (tzid, WINDOWS_ZONES.get(tzid)):
            if not candidate:
                continue
            try:
                return naive.replace(tzinfo=ZoneInfo(candidate)), False
            except Exception:
                continue
        return None, False

    return None, False


def parse_ics(text):
    """Pull VEVENTs out of an ICS document. Returns (events, skipped)."""
    events, skipped = [], []

    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfold(text), re.S):
        fields, params = {}, {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            head, _, value = line.partition(":")
            name, *rest = head.split(";")
            name = name.upper()
            fields[name] = value
            params[name] = dict(
                p.split("=", 1) for p in rest if "=" in p
            )

        title = unescape(fields.get("SUMMARY", ""))

        if "RRULE" in fields:
            skipped.append(title or "(untitled)")
            continue
        if not title or "DTSTART" not in fields:
            continue

        starts, all_day = parse_when(fields["DTSTART"], params.get("DTSTART", {}))
        if starts is None:
            skipped.append(f"{title} (unreadable start time)")
            continue

        ends, _ = parse_when(fields.get("DTEND", ""), params.get("DTEND", {}))
        if ends is None:
            ends = starts + dt.timedelta(days=1 if all_day else 2)

        events.append(
            {
                "uid": fields.get("UID", "").strip(),
                "title": title,
                "starts": starts.astimezone(dt.timezone.utc).isoformat(),
                "ends": ends.astimezone(dt.timezone.utc).isoformat(),
                "all_day": all_day,
                "room": unescape(fields.get("LOCATION", "")),
                "summary": unescape(fields.get("DESCRIPTION", "")),
            }
        )

    events.sort(key=lambda e: e["starts"])
    return events, skipped


# --------------------------------------------------------------------- main

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "fcpm-site/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "ignore")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ics", help="Published calendar URL (or set FCPM_CALENDAR_ICS)")
    parser.add_argument("--weeks", type=int, default=12,
                        help="How far ahead to keep. Default 12.")
    parser.add_argument("--now", help="Override the clock, for tests. ISO 8601.")
    parser.add_argument("--file", help="Read a local .ics instead of fetching.")
    args = parser.parse_args()

    source = args.file or args.ics or os.environ.get("FCPM_CALENDAR_ICS")
    if not source:
        raise SystemExit(
            "No calendar source. Pass --ics <url>, --file <path>, or set "
            "FCPM_CALENDAR_ICS.\n"
            "Until one exists, _data/classes.yml is edited by hand and the site "
            "uses that."
        )

    text = open(source).read() if args.file else fetch(source)
    events, skipped = parse_ics(text)

    now = dt.datetime.fromisoformat(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=dt.timezone.utc)
    horizon = now + dt.timedelta(weeks=args.weeks)

    # Keep anything not yet finished, out to the horizon. A class that started
    # an hour ago is exactly what the homepage needs to know about.
    upcoming = [
        e for e in events
        if dt.datetime.fromisoformat(e["ends"]) >= now
        and dt.datetime.fromisoformat(e["starts"]) <= horizon
    ]

    data = {
        "sessions": upcoming,
        "window_weeks": args.weeks,
        "skipped_recurring": skipped,
    }

    with open(OUT, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")

    print(f"Wrote {os.path.normpath(OUT)}")
    print(f"  {len(events)} events in the feed, {len(upcoming)} within {args.weeks} weeks")

    if skipped:
        print(f"\n  SKIPPED {len(skipped)} repeating or unreadable events:")
        for s in skipped:
            print(f"    - {s}")
        print("  Repeating events need Graph calendarView. See the note at the")
        print("  top of this script.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
