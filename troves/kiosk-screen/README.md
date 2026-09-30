# kiosk-screen

**If you have a screen that shows a studio page, this is how it is kept on.**
The first is the rolling TV (`../../instruments/roller-tv/`), driven by editing
bay 1. It is kiosk-1's screen keeping (`door.py`, `launch_screen` and
`screens`), lifted out for a host that does not run the door.

Status: on the roller since 2026-09-27, from a local render.

## What it does

`screen.ps1 keep <instrument>` makes one pass, and bay 1's pool task runs it
every minute as `keep -By pool` (`machines/editing-bay-1/code/bin/pool.ps1`, `pass`). Nothing
runs between passes except Edge itself.

1. **Find the screen.** Ask Windows for the monitor whose EDID product code is
   the instrument's `match: product` (`VIZ1006`), and never go by display
   number. If there is none, or more than one, nothing is shown. If Windows
   piled our browser onto another monitor when the TV went, it is closed.
2. **Pick the page.** The wall kiosk-1 writes to the depot
   (`\\10.209.1.1\DIGISTATION\.wall\`) if its SMB port answers. Otherwise it
   uses the wall rendered on this host by `render.py`, which calls this
   checkout's `door.py` `wall_files()` under uv. The render is redone every
   pass, and the wall reloads itself every ten minutes.
3. **Play it.** If our browser is not already fullscreen on that monitor
   showing that page, close it and launch Edge with `--kiosk`,
   `--edge-kiosk-type=fullscreen` and a profile of its own, placed on the
   monitor's rect in physical pixels.

## Never

- **Nobody's browser.** Ours is the Edge whose command line names our profile
  folder, `%LOCALAPPDATA%\<profile>\troves\kiosk-screen\<instrument>\profile`.
  It is closed by asking its windows (WM_CLOSE), then by its process ids.
  Never by name (`machines/editing-bay-1/GRANTS`).
- **No other screen.** The TV is the building's, lent to the studio
  (`instrument.yml`). When it is gone, the page goes too.
- **Nothing a person is using.** `fcpm screen off` holds until `fcpm screen on`.

## Verbs

| | |
|---|---|
| `fcpm screen` / `status` | is the TV attached, is our browser on it, what it shows, the last few log lines |
| `fcpm screen off` | close it and keep it closed, pass after pass |
| `fcpm screen on` | keep it again, starting now |
| `fcpm screen reset` | close it and start it again |
| `fcpm screen class` | class mode instead of the wall (`class.html`, `../../instruments/roller-tv/class-mode.md`), held pass after pass. `class light` for the light version |
| `fcpm screen wall` | back to the wall |

Under `%LOCALAPPDATA%\editing-bay-1\troves\kiosk-screen\roller-tv\`: `wall\`
(the local render), `profile\` (Edge's), `off` (present while off), `page` (present while class mode is asked for),
`screen.log` (what changed, one line each time).

## What the local render cannot show

Bay 1 has no Microsoft 365 key and no route to the depot. The **Studio** module
falls back to `machines/kiosk-1/bookings.sample.yml`, and its pills say
*Sample*. **Files** is empty. Both clear up once the depot answers, because the
depot's copy is written by kiosk-1.
