# Instruments

Every screen that shows a studio page is an instrument: hardware played through gear, in
station-node's sense, here an output rather than a source. It can be taken away (the building owns
the roller TV; other people work at the bays), so a driver finds its screen every time, plays it in
Edge kiosk mode with a `--user-data-dir` of its own (`launch_screen` in `machines/kiosk-1/door.py`),
and touches nothing it did not create. Without its own profile, Edge hands the page to whatever
window is open. Nothing reads this directory yet: `screens:` and `wall:` in `machines/kiosk-1/node.yml` drive the screens.

## Matching

1. A page follows its panel: match on EDID manufacturer and product code, never display number, port or serial.
2. Two connected panels of one model: their order on the Windows desktop decides.
3. An unknown panel takes whichever page has no screen, among panels the host has set aside.
4. Swapping two pages is one action, never a config edit.

## Files

Each screen has a folder: `instrument.yml` (match, orientation, input, placement, how it is played)
and `show.yml` (the page as config: one route, the door modules it names, layout, scale). A role
(kiosk, roller-TV driver, digitization main view) says which show goes on which instrument; the
host's profile in `machines/` says how. Only the Windows way is written.

| instrument | folder | where | show |
|---|---|---|---|
| roller TV | `roller-tv/` | control-room opening, rolling stand; driven by editing bay 1 (`troves/kiosk-screen/`) | the wall |
| kiosk-1 Dell P2213 (`DEL`, `DELF043`) | none | media node, portrait | check-in, `/kiosk/` |
| kiosk-1 Dell P2210 (`DEL`, `DEL404D`) | none | media node, portrait | files, `/depot/` |

## Class mode on the roller TV

A demo: `door.py` writes `class.html` beside the wall from the folder named by `class:` in node.yml's
`wall:` block (`roller-tv/class-sample/`), never in the wall's turn; `fcpm screen class` puts it up.
It shows a teacher's supporting materials during the class, not their presentation.

- A class is a folder: `class.yml` (`title`, `presenter`, `starts`, `ends`) and a folder per kind of material (`Handouts`), one Markdown or text file per section in name order, shown as given. A real class's folder may be a private submodule.
- Header: the check-in code, the class name, presenter and hours on the slant, a pill per hour of the class (current lit, past dimmer), and the time of day.
- Footer: the sections as slanted vertical tabs, the current one yellow, the last used at 30%; keys Dark, Light, previous, next. Arrows stop at the ends and step at most every 250 ms. Nothing rotates.
- `?light` gives white content; `?at=HH:MM` pretends it is that time today.
