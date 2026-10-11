# Programming

## Cablecast

The Cablecast API (`https://reflect-fcpublicmedia.cablecast.tv/cablecastapi/v1`) needs no key and
allows any origin. The site snapshots it at build time into plain, indexable HTML. The one live call
is the "on now" strip (`site/assets/js/onair.js`), which stays hidden if the request fails.

## Sync jobs

| script in `site/bin/` | reads | writes | run by |
|---|---|---|---|
| `sync-cablecast.py` | Cablecast catalog | `site/_data/cablecast.json` | `sync-cablecast.yml`, Mondays 13:00 UTC |
| `sync-schedule.py` | Cablecast schedule, 365 days | `site/_data/airings.json` | the same job |
| `sync-feeds.py` | `site/_data/feeds.yml` | `site/_data/member_programs.json` | `sync-feeds.yml`, daily and on `feeds.yml` push |
| `sync-calendar.py` | a published ICS calendar | `site/_data/calendar.json` | by hand |
| `propose-shows.py` | `cablecast.json`, `site/_shows/` | `site/_shows/<slug>.md` | `propose-shows.yml`, monthly |

Standard-library Python except `sync-feeds.py` (PyYAML). Jobs commit only a changed file; when
nothing changed, `sync-cablecast.yml` dispatches `deploy.yml` so expired features drop off.

- **cablecast.json**: titled programs, newest first; untitled records are only counted
  (`untitled_omitted`); programs without a VOD stay as `watchable: false`. `local` marks categories
  in `LOCAL_PREFIXES` or `LOCAL_EXTRA`, the one judgement call: syndication dominates the raw list,
  so `recent_local` sits beside `recent` (24 each).
- **airings.json**: airings and first and last date, keyed by show id as a string, without filler or
  deleted slots; if nothing can be read, the old file stays. The run lists titles on several catalog records
  (untitled series, or duplicates splitting airing history) for the catalog's owner to merge.

## Feeds and podcasts

`site/_data/feeds.yml` lists member feeds under `sources:` (`name`, `url`, `kind`: podcast, video or
writing, optional `owner`), with `per_source` (6), `total` (24) and `months` (18). Any RSS 2.0 or
Atom feed works. Items show on `/meet/` under "made by members".

- Feed text is untrusted: the script strips markup (entities decoded first), drops non-http(s)
  links and caps lengths, and `site/meet.md` escapes every field again. Keep both halves.
- Each feed is retried five times, 404 included (YouTube sends spurious ones). A feed that still
  fails keeps its last items, unmarked. The job fails only if every feed failed and none was kept.
- The file is rewritten only when items change. `enclosure` is the media file, `image` a thumbnail.

Podcasts are `site/_podcasts/<name>.md` at `/podcasts/<name>/`: `title`, `lede`, `hosts`, `explicit`,
`partner`, `embed` (the host's player) and `listen` links, empty ones skipped.

## Shows

A show is `site/_shows/<slug>.md` at `/watch/<slug>/`: `title`, `slug`, `kind`, `match.prefixes`,
`match.producers`, `producer`, `local`, and optionally `proposed`, `catalog_first`/`catalog_last`
(Cablecast record dates, not airings), `repository` (its own repository) and `pipeline`
(per-episode steps, see [troves/pools/README.md](../troves/pools/README.md)). Its episodes are
`cablecast.json` filtered by title prefix, case and punctuation ignored; there are no episode pages.

Cablecast titles are episode titles, so a person names each show. `propose-shows.py` groups
unclaimed titles by first word, names a group by the longest word prefix 80% of it shares (less
`ep`, `part`…), and needs 3 episodes; `propose-shows.yml` opens one pull request each, up to `limit`
(5) a run. Fix `title` or close it; delete `proposed: true`, which flags the page, once checked.

## Class mode

`site/_includes/class-config.html`, in `site/index.html` and `site/check-in.md`, bakes the schedule
in as JSON: `site/_data/calendar.json` if it has sessions, else `site/_data/classes.yml`.
`pickSession` (`site/assets/js/classes.js`) checks it against the clock, without a request, every
minute while the page is visible. Windows: `soon` (`lead_minutes`, 90, before the start), `late`
(the first `late_minutes`, 45), `now` (the rest).

- Homepage (`classmode.js`): the class panel appears; its drop-in price stays hidden while `TODO`.
- Check-in (`checkin.js`): a class banner; the reason is `Class` unless the URL's `?reason=` names
  another listed reason; the button reads "I'm here for the class". Before the start, "I'm planning
  to come" stores the session in `fcpm.rsvp`, on the device only.
- The QR on the door always links to `/check-in/`; the page works out the class on arrival.

`classes.yml` also holds `photo` (top of `/classes/`, never shown without `alt`), `dropin` and
`sessions` (`title`, `starts`, `ends`, `room`, `summary`, `signup`). Times carry an offset
(`2026-08-11T18:00:00-06:00`); a bare time is read in the visitor's zone. A new class appears at
the next build. On the roller TV: [instruments/README.md](../instruments/README.md#class-mode-on-the-roller-tv).

## Calendar

`python3 site/bin/sync-calendar.py --ics "$FCPM_CALENDAR_ICS" --weeks 12` reads a calendar published
from Outlook on the web (Settings, Calendar, Shared calendars, Publish a calendar); anyone with the
link can read it, so publish a dedicated public programming calendar. It keeps events not yet ended,
skips and lists repeating events (`RRULE`), and refuses time zones it cannot map.

## Homepage

- The check-in panel with its QR and the class panel, then the on-air strip.
- `site/_data/featured.yml`: entries (`kind`: class, event, show or notice; `title`, `blurb`, `when`,
  `url`, `cta`, `starts`, `ends`) shown between `starts` and `ends` as of the build. The first is
  the large card; an empty list renders nothing.
- The live stream, the carriage list (`site/_data/watch.yml`), the latest eight airings, one per producer.
