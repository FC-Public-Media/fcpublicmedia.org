# `instruments/roller-tv/show.yml`

Moved out of the file. Unreviewed.

## 1

Above `version: 1`

show.yml — what the rolling TV shows. This is the page, treated as config.
See docs/instruments/README.md.

DRAFT. Nothing reads it yet. Today the TV's page is the wall, which the
media node's door builds from the `wall:` block in
machines/kiosk-1/node.yml. This is what that block would read from once it
is moved here. The fields below say what is wanted, and name the gap where
the wall does not do it yet.

## 2

Above `route: wall`

ONE ROUTE. The screen opens one address and never navigates away from it.
The shell changes what it shows by itself.

## 3

Above `modules:`

MODULES are the door's pages (door.py WALL_PAGES). They are named here, not
copied: any screen that shows `studio` shows the same one.

## 4

Above `layout:`

HOW THEY ARE SHOWN. Nobody is standing at this screen to press a button, so
the main area moves through the modules on its own, under a fixed check-in
header. No thumbnails (Autumn, 2026-09-26): one module fills the area, and
the bar names what is showing. A class soon or on takes the area over and
does not rotate. Built in door.py (the wall), where `rotate:` in node.yml's
wall block is `every` below.

## 5

Above `controls: small`

SCALE. This screen gets a pointer at most, so the controls are small
(door.py WALL_CSS, 1.35vh type) and the room goes to the content.

## 6

Above `animated: true`

Motion is allowed. This is a screen in a window, read from across a room:
some movement is what tells somebody it is live and not a frozen page.
Nothing may flash.

## 7

The data is refreshed on the wall's own beat (`every:` in node.yml's wall
block, 60 s), not here.
