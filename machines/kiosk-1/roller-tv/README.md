# The roller TV

The kiosk's third screen: the rolling TV in the control-room opening, showing the wall the kiosk's
door writes. Editing bay 1 drives it ([`troves/kiosk-screen/`](../../../troves/kiosk-screen/README.md))
because the bay is the machine with a cable or a cast to it; the screen, its page and class mode are
the kiosk's. The building owns the TV and other people work at the bays, so a driver finds its screen
every time, plays it in Edge kiosk mode with a `--user-data-dir` of its own (`launch_screen` in
[`../door.py`](../door.py)), and touches nothing it did not create. Without its own profile, Edge
hands the page to whatever window is open. `screen.ps1` reads `instrument.yml` here; `screens:` and
`wall:` in [`../node.yml`](../node.yml) drive the kiosk's own panels.

## Matching

1. A page follows its panel: match on EDID manufacturer and product code, never display number, port or serial.
2. Two connected panels of one model: their order on the Windows desktop decides.
3. An unknown panel takes whichever page has no screen, among panels the host has set aside.
4. Swapping two pages is one action, never a config edit.

## Files

`instrument.yml` (match, orientation, input, placement, how it is played) and `show.yml` (the page as
config: one route, the door modules it names, layout, scale). Only the Windows way is written.

| screen | folder | where | show |
|---|---|---|---|
| roller TV | `roller-tv/` | control-room opening, rolling stand; driven by editing bay 1 | the wall |
| Dell P2213 (`DEL`, `DELF043`) | none | the kiosk, portrait | check-in, `/kiosk/` |
| Dell P2210 (`DEL`, `DEL404D`) | none | the kiosk, portrait | files, `/depot/` |

## Class mode

A demo: `door.py` writes `class.html` beside the wall from the folder named by `class:` in node.yml's
`wall:` block (`class-sample/` here), never in the wall's turn; `fcpm screen class` puts it up.
It shows a teacher's supporting materials during the class, not their presentation.

- A class is a folder: `class.yml` (`title`, `presenter`, `starts`, `ends`) and a folder per kind of material (`Handouts`), one Markdown or text file per section in name order, shown as given. A real class's folder may be a private submodule.
- Header: the check-in code, the class name, presenter and hours on the slant, a pill per hour of the class (current lit, past dimmer), and the time of day.
- Footer: the sections as slanted vertical tabs, the current one yellow, the last used at 30%; keys Dark, Light, previous, next. Arrows stop at the ends and step at most every 250 ms. Nothing rotates.
- `?light` gives white content; `?at=HH:MM` pretends it is that time today.
