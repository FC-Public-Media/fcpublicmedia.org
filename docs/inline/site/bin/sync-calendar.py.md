# `site/bin/sync-calendar.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

python3 site/bin/sync-calendar.py --ics "https://outlook.office365.com/....ics"
    python3 site/bin/sync-calendar.py --ics "$FCPM_CALENDAR_ICS" --weeks 8

WHY BUILD TIME
--------------
The schedule changes a few times a month and is identical for everybody. Having
each visitor's browser ask Microsoft for it would be the same answer fetched
thousands of times, would put a key or a public endpoint in the client, and
would leave the page blank whenever Microsoft is slow. Fetching it once per
build and shipping the answer as part of the page is faster, cheaper, private,
and works offline. Same reasoning as site/bin/sync-cablecast.py.

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

## 2

Above `WINDOWS_ZONES = {`

Outlook frequently writes Windows zone names into TZID rather than IANA
identifiers, and zoneinfo has never heard of "Mountain Standard Time". These
are the ones a Colorado organisation plausibly encounters; anything else is
refused rather than guessed at, because being silently an hour out twice a
year is worse than a visible error. The full mapping lives in CLDR's
windowsZones.xml if this ever needs extending.

## 3

Above `try:`

Return (datetime, is_all_day) or (None, False) if it can't be read.

Handles the three forms published calendars actually emit: UTC with a
trailing Z, a date-only value for all-day events, and a local time with a
TZID parameter.

Never raises. One malformed event in a feed should be reported and skipped,
not take down the whole sync — a calendar is other people's data and will
eventually contain something unexpected.

## 4

Above `upcoming = [`

Keep anything not yet finished, out to the horizon. A class that started
an hour ago is exactly what the homepage needs to know about.
