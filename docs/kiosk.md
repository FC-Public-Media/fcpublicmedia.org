# Kiosk and studio screens

A kiosk is a screen in the studio. This repository owns what it says (`machines/kiosk/welcome/`) and the dim
every studio screen shares (`brand/idle/`). The kiosk's door draws the pages.

## Content

| file | |
|---|---|
| `welcome/content.yml` | hand-written: the room, the greeting, the panels' wording |
| `welcome/welcome.yml` | generated, committed, canonical |
| `welcome/welcome.js` | generated, committed: the same content as `window.FCPM_KIOSK`, for `file://` pages |
| `bin/build-kiosk.py` | joins `content.yml` to `site/_data/` and writes both artifacts |

```sh
python3 bin/build-kiosk.py           # write both
python3 bin/build-kiosk.py --check   # fail if either is stale (CI runs this)
python3 bin/build-kiosk.py --print   # write nothing, show both
python3 bin/test_build_kiosk.py
```

Edit `content.yml` (or the facts in `site/_data/`), regenerate, commit all three. The root
reads down into `site/_data/`; nothing in `site/` reads `welcome/`.

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

`takeover: false` in `content.yml` makes it an ordinary panel. The kiosk's door copies
`pickSession` out of `classes.js` on every page it draws: on the wall the card takes the stage
under the check-in header; on the desk it takes the check-in words. `?at=<ISO time>` on either
page pretends it is then. `classes: sample` in `machines/kiosk/node.yml` invents three
sessions, marked as samples.

## Hosts

`site/_data/hosts.yml` is who is on: the welcome screen's footer (on now, next), the room pages,
the host wizard's one-tap names and, with classes, the awake windows (`hosts()` in `door.py`).
Each person's day keys are their standing shift, `[from, to]`, local and 24-hour. A day key is a
letter (`M T W R F S U`), a three-letter name (`Mon`…`Sun`, any case) or a range of either
(`Sun-M`); a shift that starts and ends at the same time is none. `scheduled: false` keeps a
person off the schedule but among the host picks. Names show as their first word. The top-level
`days` is the studio's hours, which the site's footer prints; the kiosk does not read it.

`supports` tags people with activities (`node.yml` `facilities` and `stations`); a station with nothing booked this week lists up to three who can help, at their next
shift. `orientation`, or no tags, helps with anything.

## Dim

Every page on a studio screen falls to the same dim, in any orientation.

| | owes | never |
|---|---|---|
| the door (`awake_windows()` in `door.py`) | the awake windows for the next week | a verdict on whether a screen is awake now |
| `brand/idle/dim.js`, `dim.css` | the verdict from the page's own clock, and the dim | an idle timer |
| the page | nothing (`page()` inlines both); it may hold the screen awake | its own rule for "awake" |

**Awake windows.** Each host shift and each class (by `pickSession`'s sessions), from 60
minutes before it starts to its end, merged, for 7 days, plus the camera's lights window. Not
bookings: a booking is always inside host hours. Delivered three ways: baked into every page,
in the `awake` field of `/kiosk/now` (60 s) and `/depot/now` (10 s), and baked into the wall's
files (rewritten every 60 s). No list, an empty list, or past its last end: awake.

**Dim, drawn.** Pure black over the page, the page at 10%, and over it the three squares: the
lit one walking the column, a split clock (hour hand top, seconds middle, minute hand bottom),
and the column gliding at a calm speed and bouncing off the edges, against burn-in. Fade in
over 30 s, wake in under a second. Reduced motion: no fade, no glide, the middle square lit,
and the column moves once an hour. The page dims, not the backlight: the kiosk has no DDC/CI
tooling and no administrator.

**Waking.** One mark per computer is the lock (Autumn, 2026-10-13): `awake` in the door's state
folder. Present and under an hour old, every clock is off; missing, every clock is on. Any input on
the computer writes it: Windows' last input, X's idle clock on a Linux desktop, or a page's own touch,
key, wheel or real pointer movement (POST `/input`). It is written at once when missing, and at most
once a minute while fresh. The first look that finds it an hour old removes it, so every screen dims
together. Pages ask `/input` twice a second and take its answer whole. The first touch on a dim screen
only wakes: the layer swallows it. The roller, read over `file://`, reads `input.js`, kept by the
kiosk-screen trove's watcher. A page holds the screen awake with
`<html class="fcpm-awake">`: the wall while held or during a class takeover, the desk during a takeover or while the camera is up. A
check-in does not wake it; it happens on the visitor's phone. `?at=HH:MM` or `?at=<ISO>`,
`?awake` and `?dim` on the top page's URL show either state.

| contract | |
|---|---|
| `window.FCPM_AWAKE` | `[[startMs, endMs], ...]`, epoch ms, merged; baked into `<head>` before any body script |
| `window.fcpmAwake(list)` | fresh windows from the kiosk and depot pages; replaces the list, fires `fcpm:awake` |
| `<html class="fcpm-awake">` | awake whatever the schedule |
| `window.FCPMDim` | `isDim()` (the wall asks every frame and stops its turn), `tally(el)` (draws the mark; the idle screen uses it), `wake([at])` (the hour runs from `at`, never shortened) |
| `window !== window.top` | `dim.js` does nothing, so a module's iframe draws no second layer |

While dim the wall's turn is paused, and its ten-minute shell reload waits for the turn to
resume. Screen supervision still relaunches a stuck panel, which works out dim again.

**Monitors.** A monitor attached but off is not an emergency. The kiosk's panels never sleep
(*Never* on AC); both are DisplayPort, so one switched off drops out of Windows, and the door
relaunches its window in place when it returns. Editing bay 1 sleeps its displays after 2 hours
idle. The roller's Vizio is on an HDMI-to-DisplayPort adapter; suspect the long blue-cored HDMI
cables first.

## kiosk-screen trove

[`troves/kiosk-screen/`](../troves/kiosk-screen/README.md) keeps a studio page on a screen a
host finds plugged in, by EDID product code, for a host that does not run the door. Editing bay
1's pool runs `screen.ps1 keep roller-tv` every minute: the depot's copy of the wall if the
share answers, else a wall rendered locally from `door.py` `wall_files()`.

## The kiosk's door

`machines/kiosk/door.py` on `[::]:8080` serves the welcome screen (`/kiosk/`: the check-in
code, the studio map, Wi-Fi codes built in memory from Credential Manager, the host footer),
the depot, the cameras, the turn and the idle screen, and writes the wall (no Wi-Fi codes) to
`\\10.209.1.1\DIGISTATION\.wall\` for the rolling TV. Every page reloads when `/revision` moves.
Layout: `machines/kiosk/node.yml`; the rest: [`PROFILE.md`](../machines/kiosk/PROFILE.md).

## Rooms

A room's hallway door is a tablet in a holder showing `/room/<room>/` from the door, any shape, landscape
first (an iPad Air 2 at the podcast studio, on `digitization.local`). `machines/kiosk/rooms/<room>.yml` is
the room: its title, two sentences for somebody passing, the code (the site, not check-in), its name in the
classes list, and its gear (`id`, `name`, `say`, `count`, `trove`, `usually`). The page never dims: the
tablet is put away when nobody is in. It shows who is hosting (the last host reply, while its `until`
holds), else who is at the desk or next (hosts.yml), this room's next classes, and the gear lit as the last
reply left it, or as `usually:` says while no reply has spoken. The small `Staff` link opens the wizard.

## Replies

A wizard is a page that helps one person form one reply, and only that: the form's checks exist to make
the shape, never to refuse. `fcpm.reply/v0` names the wizard (`wizard:kiosk+lights`, `wizard:kiosk+host`)
and the wizard's commit (`at`, the form's version), and carries `issued`, a `nonce` and `sig: null`. The
reply travels in a bottle: a signed transfer (the scanner trove's composer; Ed25519, the phone's own key,
its fingerprint the pseudonym), poured as AC1 fountain frames at 48 bytes a frame, so every bottle is a
video from the first byte and a dented, shuffled or lossy catch heals; or the same bytes set down over the
LAN (`POST /drop`). Either way it is kept first, as the file it arrived as, and read on the door's next pass
(`replies.py take`, every 20 s): applied to the room's state, or held with the reason (`held/`,
`log.ndjson`). Nothing is refused at the door and nothing is applied on arrival. Held: not JSON, a payload
whose hash does not match, an unknown wizard or room, `issued` more than a day from now, a nonce seen
before, an `until` already passed. The signature is read by the composer under Node (`verify-bottle.mjs`);
without Node the payload's hash is still checked and the reply applies as `unverified`. For `kiosk+host`,
unsigned and unknown-key replies apply too: being on the studio's network is the staff's authority for
this. `trust` is recorded (`friend`, `signed`, `unsigned`, `unverified`), and `replies.py trust
<fingerprint> <name>` names a phone. The eyes' path (`troves/scanner` `page.py` handing a catch to
`replies.drop_frames`) is not wired yet; the reader is.

### wizard:kiosk+host

`/host/?room=<room>` on a staff phone: your name (hosts.yml's people as one-tap picks, remembered on the
phone), Hosting or Left, until (23:59 by default), and what is in the room.

```json
{"schema": "fcpm.reply/v0", "wizard": "wizard:kiosk+host", "at": "64b194e", "room": "podcast",
 "hosting": true, "host": "Autumn", "until": "2026-10-17T23:59:00-06:00",
 "present": ["rodecaster", "mics", "headphones", "camera-6k"],
 "issued": "2026-10-17T14:02:11-06:00", "nonce": "…", "sig": null}
```

`hosting: false` is leaving. `present` is the whole list each time; gear the room does not list is
ignored and noted in the verdict. The public check-in's pass offers *Hosting a room? Check in as
staff*: the wizard on the board's LAN name (`_data/lan.yml`, at the root), the typed name carried in `?name=`.
