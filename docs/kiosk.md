# Kiosk and studio screens

A kiosk is a screen in the studio. This repository owns what it says (`kiosk/`) and the dim
every studio screen shares (`brand/idle/`). kiosk-1's door draws the pages.

## Content

| file | |
|---|---|
| `kiosk/content.yml` | hand-written: the room, the greeting, the panels' wording |
| `kiosk/welcome.yml` | generated, committed, canonical |
| `kiosk/welcome.js` | generated, committed: the same content as `window.FCPM_KIOSK`, for `file://` pages |
| `kiosk/rota.yml` | hand-written: who is on, by default ([Rota](#rota)) |
| `bin/build-kiosk.py` | joins `content.yml` to `site/_data/` and writes both artifacts |

```sh
python3 bin/build-kiosk.py           # write both
python3 bin/build-kiosk.py --check   # fail if either is stale (CI runs this)
python3 bin/build-kiosk.py --print   # write nothing, show both
python3 bin/test_build_kiosk.py
```

Edit `content.yml` (or the facts in `site/_data/`), regenerate, commit all three. The root
reads down into `site/_data/`; nothing in `site/` reads `kiosk/`.

The artifact never contains:

- **the Wi-Fi password, or a QR encoding it.** `wifi-qr.svg` is gitignored; the generator
  refuses to name it, and refuses any `password:`, `passphrase:`, `secret:` or `psk:` key, in
  YAML or JSON. The printed poster at `/wifi/poster/` is how the password reaches a guest.
- **a host, port or address for itself.** `encodes:` is the one URL: where the check-in QR
  points, shown as text character for character as the printed poster shows it.
- **a timestamp.** `--check` answers whether it is current.

An SSID with `confirmed: false` in `site/_data/wifi.yml` refuses to build.

## Panels

```yaml
- panel: Checking in     # the heading
  say: …                 # the short answer
  note: …                # a smaller line (optional)
  qr: {image, encodes, alt}   # generated, never hand-written
```

In `content.yml` a panel is either `from: <source>` (facts from `site/_data/`; `say` and
`note` still override) or a literal `say:` / `note:`. Sources: `wifi`, `checkin`, `classes`.
An unknown `from:` is an error.

- **Guest Wi-Fi** names the SSID and takes its note from `content.yml` only: the poster's note
  tells a guest to scan a code the kiosk does not have.
- **Checking in** carries `site/assets/img/check-in-qr.svg`. A kiosk browser never opens
  `/check-in/`: that page keeps name, reason and email in `localStorage` (`fcpm.profile`,
  `fcpm.checkins`), so a shared browser would prefill one guest's details for the next.
  The guest scans the code with their own phone.

## Revision

`revision:` is the first field: twelve hex characters of SHA-256 over the YAML body. It
changes when the content changes and never otherwise. A renderer polls it and reloads when it
differs. `welcome.js` carries the same revision, copied, not recomputed.

## Transport

A `file://` page has an opaque origin: `fetch` and XHR of `welcome.yml` fail. A
`<script src="welcome.js?t=N">` works repeatedly, so a panel injects it with a cache-buster,
reads `window.FCPM_KIOSK`, and drops the tag. `welcome.js` is one assignment: no logic, no
fetch. Read `welcome.yml` when you can.

## The class on now

| | owes | never |
|---|---|---|
| `site/bin/sync-calendar.py` | `site/_data/calendar.json`, committed periodically | a live pipe to the screens |
| `bin/build-kiosk.py` | the `classes` panel: the schedule and the two windows | a verdict on what is on now |
| a renderer | the verdict, from its own clock, with `pickSession` | a second rule for "now" |

The schedule is `calendar.json` when it has sessions, else `site/_data/classes.yml`, as the
website does (`site/_includes/class-config.html`). Each session carries `title`, `starts`,
`ends`, `room`, `summary`, and may carry `cancelled: true` (kept in the file, off every screen).
Every time carries its UTC offset or the build refuses; sessions sort by instant. Nothing about
people is copied, whatever the file holds. `leadMinutes` (90) and `lateMinutes` (45) come from
`classes.yml`.

The panel is exactly the config `pickSession` in `site/assets/js/classes.js` takes. Import it
or copy it byte for byte.

| phase | the screen |
|---|---|
| `soon` | takes over: *Starting soon*, title, room, start time |
| `late` | takes over: *Happening now*, title, room, *until* the end, *join until* start + `lateMinutes`, with the check-in code |
| `now` | takes over: *Happening now*, title, room, *until* the end |
| none | the next session, one line |

`takeover: false` in `content.yml` makes it an ordinary panel. kiosk-1's door copies
`pickSession` out of `classes.js` on every page it draws: on the wall the card takes the stage
under the check-in header; on the desk it takes the check-in words. `?at=<ISO time>` on either
page pretends it is then. `classes: sample` in `machines/kiosk-1/node.yml` invents three
sessions, marked as samples.

## Rota

`kiosk/rota.yml` is the standing host rotation: the welcome screen's footer (on now, next) and,
with classes, the awake windows. Times are local, 24-hour; `days` takes `mon`…`sun`; `role`
shows beside the name. `crew:` tags people with activities (`site/_data/facilities.yml`, or
`node.yml` stations); a station with nothing booked this week lists up to three who can help,
at their next shift. No tags means a host, who helps with anything.

## Dim

Every page on a studio screen falls to the same dim, in any orientation.

| | owes | never |
|---|---|---|
| the door (`awake_windows()` in `door.py`) | the awake windows for the next week | a verdict on whether a screen is awake now |
| `brand/idle/dim.js`, `dim.css` | the verdict from the page's own clock, and the dim | an idle timer |
| the page | nothing (`page()` inlines both); it may hold the screen awake | its own rule for "awake" |

**Awake windows.** Each rota shift and each class (by `pickSession`'s sessions), from 60
minutes before it starts to its end, merged, for 7 days, plus the camera's lights window. Not
bookings: a booking is always inside host hours. Delivered three ways: baked into every page,
in the `awake` field of `/kiosk/now` (60 s) and `/depot/now` (10 s), and baked into the wall's
files (rewritten every 60 s). No list, an empty list, or past its last end: awake.

**Dim, drawn.** Pure black over the page, the page at 10%, and over it the three squares: the
lit one walking the column, a split clock (hour hand top, seconds middle, minute hand bottom),
and the column gliding at a calm speed and bouncing off the edges, against burn-in. Fade in
over 30 s, wake in under a second. Reduced motion: no fade, no glide, the middle square lit,
and the column moves once an hour. The page dims, not the backlight: kiosk-1 has no DDC/CI
tooling and no administrator.

**Waking.** A touch, click, key, wheel or real pointer movement wakes the screen for an hour,
and each one restarts the hour. The first touch on a dim screen only wakes: the layer swallows
it. On kiosk-1 the door reports the computer's last input (`/input`), so input anywhere wakes
every panel. A page holds the screen awake with `<html class="fcpm-awake">`: the wall while
held or during a class takeover, the desk during a takeover or while the camera is up. A
check-in does not wake it; it happens on the visitor's phone. `?at=HH:MM` or `?at=<ISO>`,
`?awake` and `?dim` on the top page's URL show either state.

| contract | |
|---|---|
| `window.FCPM_AWAKE` | `[[startMs, endMs], ...]`, epoch ms, merged; baked into `<head>` before any body script |
| `window.fcpmAwake(list)` | fresh windows from the kiosk and depot pages; replaces the list, fires `fcpm:awake` |
| `<html class="fcpm-awake">` | awake whatever the schedule |
| `window.FCPMDim` | `isDim()` (the wall asks every frame and stops its turn), `tally(el)` (draws the mark; the idle screen uses it), `wake()` |
| `window !== window.top` | `dim.js` does nothing, so a module's iframe draws no second layer |

While dim the wall's turn is paused, and its ten-minute shell reload waits for the turn to
resume. Screen supervision still relaunches a stuck panel, which works out dim again.

**Monitors.** A monitor attached but off is not an emergency. kiosk-1's panels never sleep
(*Never* on AC); both are DisplayPort, so one switched off drops out of Windows, and the door
relaunches its window in place when it returns. Editing bay 1 sleeps its displays after 2 hours
idle. The roller's Vizio is on an HDMI-to-DisplayPort adapter; suspect the long blue-cored HDMI
cables first.

## kiosk-screen trove

[`troves/kiosk-screen/`](../troves/kiosk-screen/README.md) keeps a studio page on a screen a
host finds plugged in, by EDID product code, for a host that does not run the door. Editing bay
1's pool runs `screen.ps1 keep roller-tv` every minute: the depot's copy of the wall if the
share answers, else a wall rendered locally from `door.py` `wall_files()`.

## kiosk-1's door

`machines/kiosk-1/door.py` on `[::]:8080` serves the welcome screen (`/kiosk/`: the check-in
code, the studio map, Wi-Fi codes built in memory from Credential Manager, the host footer),
the depot, the cameras, the turn and the idle screen, and writes the wall (no Wi-Fi codes) to
`\\10.209.1.1\DIGISTATION\.wall\` for the rolling TV. Every page reloads when `/revision` moves.
Layout: `machines/kiosk-1/node.yml`; the rest: [`PROFILE.md`](../machines/kiosk-1/PROFILE.md).
