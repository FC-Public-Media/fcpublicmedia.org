# kiosk-screen

Keeps a studio page on a screen this host finds plugged in: kiosk-1's screen keeping (`door.py`
`launch_screen`, `screens`) for a host that does not run the door. Today: the rolling TV
(`instruments/roller-tv/`), from editing bay 1. Screens and dim: [`docs/kiosk.md`](../../docs/kiosk.md).

`screen.ps1 keep <instrument>` is one pass; bay 1's pool runs it every minute
(`machines/editing-bay-1/code/bin/pool.ps1`, with `FCPM_BY=pool`). A pass:

1. **Finds the screen** by the instrument's `match: product` EDID code (`VIZ1006`), never by display number. None, or more than one: nothing is shown, and our browser is closed wherever Windows moved it.
2. **Picks the page**: the wall kiosk-1 writes to `\\10.209.1.1\DIGISTATION\.wall\` if its SMB port answers, else the wall `render.py` renders here every pass from this checkout's `door.py` under uv. Class mode's `class.html` instead while asked for.
3. **Plays it**: unless our Edge is already fullscreen there on that page, closes it and launches Edge `--kiosk --edge-kiosk-type=fullscreen` with its own profile, on the monitor's rect in physical pixels.

Ours is the Edge whose command line names `%LOCALAPPDATA%\<profile>\troves\kiosk-screen\<instrument>\profile`; it is closed by WM_CLOSE, then by process id, never by name. No other screen: the TV is the building's.

Verbs: `fcpm screen` (`status`: attached, our browser, the page, the last log lines), `off` (closed until `on`), `on`, `reset` (close and start again), `class` (class mode, `instruments/README.md`; `class light` for light), `wall` (back), `toggle` (whichever of the two is not showing).

State in `%LOCALAPPDATA%\editing-bay-1\troves\kiosk-screen\roller-tv\`: `wall\`, `profile\`, `off`, `page`, `kept-pool` and `kept-hand` (heartbeats), `input.js` (this computer's last input), `screen.log`.

**Waking.** A touch anywhere on this computer ends the dim at once, for an hour from the last touch, as on kiosk-1's panels. The page is a file with no door to ask, so `screen.ps1 watch` (started by `keep` beside our Edge, one at a time) writes `input.js` within 0.2 s of any input, and the page, launched with `?input=` naming it, reads it twice a second. The watcher ends with our Edge, when held off, or when `screen.ps1` changes; the next pass starts it again.

The local render has no depot listing, so its **Files** is empty until the depot answers. **Studio** shows `machines/kiosk-1/bookings.sample.yml` (pills say *Sample*) while `node.yml` says `bookings: sample`.
