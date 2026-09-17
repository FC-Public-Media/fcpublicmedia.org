<!--
Split out of the root README on 2026-09-17, unchanged apart from paths.

The README was 68 KB and had become the only place a lot of this was written
down, which made it both the first thing a visitor saw and the last place
anybody wanted to edit. Nothing here was rewritten in the move; if something
reads as out of date, it was out of date before it moved, and saying so is
welcome.
-->

# Programming and the catalog

Cablecast, what goes on the schedule, and what the homepage features.

## The Cablecast catalog

The station's Cablecast instance has a public API that needs no key and sends
`Access-Control-Allow-Origin: *`. It holds **1,486 programs** going back to
2011, 740 of them watchable online, 1,462 with thumbnails, across 36
categories and 80 producers. That is the archive, and it was already there.

`site/bin/sync-cablecast.py` pulls it into `site/_data/cablecast.json` (standard
library only, nothing to install):

```
python3 site/bin/sync-cablecast.py
```

`.github/workflows/sync-cablecast.yml` runs it weekly and commits the result
if anything changed.

Snapshotting at build time rather than fetching in the browser means the
archive is real HTML — indexable, findable with ⌘F, and still there if
Cablecast is down. The one thing that *is* live is the "on now" strip
(`site/assets/js/onair.js`), which reads the schedule directly because a weekly
snapshot cannot tell you what is playing right now. It removes itself if the
request fails.

The script's one judgement call is `LOCAL_PREFIXES` — which categories count
as locally produced. This matters: the raw "most recent" list is dominated by
Free Speech TV and Paltrocast, which buries the work Fort Collins people
actually made, so the site features local production separately.

## Class mode

The homepage knows when a class is running and rearranges itself around it.
Two gears, deliberately separate:

**The build** bakes `site/_data/classes.yml` into the page as inline JSON. Session
titles, times, rooms, and drop-in prices come along with the HTML.

**The browser** reads the wall clock and decides. No request, no API, no key —
`site/assets/js/classmode.js` is arithmetic on numbers already in memory. A page
built last night knows about tonight's class. It re-checks each minute while
the tab is visible, so a page left open switches on by itself when the class
starts and off again when it ends.

Three windows: `soon` (the `lead_minutes` before), `now`, and `late` (the first
`late_minutes`, when someone walking in is still worth inviting). Outside all
three the block stays hidden and the ordinary check-in card is untouched.

### One QR, two pages, one answer

`site/assets/js/classes.js` holds the window logic. The homepage and the check-in
page both import it and run it over the same baked-in schedule, so they cannot
disagree about whether a class is on.

That has a consequence worth stating plainly, because it removes work:

**The QR carries no class information.** It is a permanent link to
`/check-in/`. There is no per-class code to generate, print, swap on the door,
or take down afterwards. The page works out on arrival that a class is
running — which is also the only place that decision can be correct, since a
link shared two hours ago would still be claiming a class is on.

The homepage's job shrinks to decorating the panel that already holds the QR
and the link. It does not encode anything.

Same reasoning for a class held elsewhere: what would change is the venue
coordinates the page checks against, not the code on the door. The QR is the
door; the location is the fact.

### On the check-in page

When a class window is open, the check-in page:

- shows the class, with the same wording as the homepage
- preselects `Class` as the reason — but **only if the visitor has not chosen
  something else**, so a page open since before the class does not have its
  answer overwritten
- changes the button to "I'm here for the class"
- before the start, offers "I'm planning to come"

That last one is recorded **on the device only**, and the page says so. There
is nowhere to send it yet. It becomes a real RSVP the day the Worker exists,
and the wording changes then — until it does, telling someone we received
their RSVP would be a lie.

Because the intent, the name, and the reason are all the same stored profile,
someone who noted intent on the way in is already set up to check in when they
arrive. No second form.

The cost of the split is staleness — a class added this morning is not on the
site until the next build. The weekly sync already rebuilds; if classes get
added at short notice, move that job to daily. Eventually `classes.yml` should
be generated from the Microsoft 365 calendar the same way `cablecast.json` is
generated from Cablecast, at which point the gear on this side does not change
at all.

**Times must carry an offset** — `2026-08-11T18:00:00-06:00`, never a bare
local time. A time without an offset is read as the *visitor's* zone, which is
wrong for anyone travelling and silently wrong, which is worse. The template
normalises through `date_to_xmlschema` so what reaches the browser is always
unambiguous.

### Where the schedule comes from

`site/_includes/class-config.html` picks a source, in this order:

1. **`site/_data/calendar.json`** — written by `site/bin/sync-calendar.py` from the
   Microsoft 365 calendar. Used whenever it has anything in it.
2. **`site/_data/classes.yml`** — hand-maintained. The fallback, and what the site
   uses today.

Switching is a matter of configuring a source and running the sync. No
template change, and `site/assets/js/classes.js` never learns where the data came
from.

```
python3 site/bin/sync-calendar.py --ics "$FCPM_CALENDAR_ICS" --weeks 12
python3 site/bin/test_sync_calendar.py     # 17 tests, no dependencies
```

**Why at build time.** The schedule changes a few times a month and is the
same for everybody. Every visitor's browser asking Microsoft for it would be
the same answer fetched thousands of times, would put a key or a public
endpoint in the client, and would leave the page blank whenever Microsoft is
slow. Fetching once per build is faster, cheaper, private, and works offline.
Same reasoning as the Cablecast sync.

### Two ways into the calendar

**A published ICS link** is what the script implements, and it is the one to
start with. In Outlook on the web: Settings → Calendar → Shared calendars →
Publish a calendar. **No app registration, no admin consent, no client secret,
nothing that expires.**

The trade is that the link works for anyone who has it. That is fine for a
class schedule and wrong for anything else — so publish a dedicated *Public
Programming* calendar rather than someone's own.

**Microsoft Graph** is needed for anything not public: room free/busy,
reservation details, a hidden nonce on a booking. Three things to know:

- Use **`calendarView`**, not `/events`. `/events` returns the recurrence
  *master*; `calendarView` expands a series into real occurrences across a date
  window, which is the shape a website wants.
- From GitHub Actions, authenticate with **workload identity federation**
  rather than a client secret. GitHub's OIDC token is exchanged for a Graph
  token, so there is no stored secret and nothing to rotate — Entra client
  secrets expire within 24 months otherwise.
- **`Calendars.Read` as an application permission grants read access to every
  mailbox in the tenant.** Scope it with an Application Access Policy
  (`New-ApplicationAccessPolicy`) pointed at a mail-enabled security group
  containing only the calendars in question. This is the sharp edge.

### Recurring events

Published ICS describes a repeating event once, with an `RRULE`, rather than
listing occurrences. Expanding those correctly — with exceptions, moved
instances, and daylight saving — is real work and not worth hand-rolling.

**The script does not.** It reports them and skips them, loudly. If FCPM starts
running recurring classes, that is the moment to move to Graph `calendarView`,
which expands them server-side.

The parser is deliberately strict about time zones for the same reason. Outlook
writes Windows zone names (`Mountain Standard Time`) that `zoneinfo` has never
heard of; the common US ones are mapped, and anything unrecognised is refused
rather than guessed at. Being silently an hour out twice a year is worse than a
visible error.

### Drop-in pricing

Shown as one plain line, not a gate. Someone who balks at the drop-in rate is
exactly the person for whom membership is the better deal, so the membership
link sits beside the price rather than behind it, and "other classes" is
offered next to "I'm here for the class". A person who came for one class and
leaves having browsed three and considered joining is a better outcome than a
completed drop-in payment.

This is not ticketing. People who signed up already paid through registration;
this is only the walk-in case.

**Every price in `site/_data/classes.yml` is a placeholder.** Nothing renders the
price block until real figures replace them.

### What is not built

Tier-aware pricing — showing someone their own rate rather than the public one
— needs the device to know the member's tier, which needs identity, which
needs Access or a Worker. The payment hand-off itself is blocked on the same
provider decision as everything else in `site/_data/providers.yml`.

## Featuring things on the homepage

`site/_data/featured.yml` is the whole content management system. It is a list.
Add an entry to put something on the front page; it removes itself when `ends`
passes. Four archetypes — `class`, `event`, `show`, `notice` — which is what
the actual pattern of announcements looks like.

Expiry is evaluated at build time, which is why the weekly workflow rebuilds
even when nothing changed. Otherwise a class that happened on Tuesday would
still be advertised on Friday.

If nothing is currently in its date window, the section renders nothing and
the page closes up around it. An empty `featured.yml` is a valid state.
