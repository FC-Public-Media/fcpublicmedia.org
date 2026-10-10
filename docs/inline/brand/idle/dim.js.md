# `brand/idle/dim.js`

Moved out of the file. Unreviewed.

## 1

Above `(function () {`

 dim.js -- every studio screen falls to dim when nobody is meant to be here.

docs/SCREENS-DIM.md is the plan. In short:

AWAKE comes from the door. window.FCPM_AWAKE is [[startMs, endMs], ...]:
host shifts and classes, each from an hour before, for a week ahead.
page() bakes it in; the kiosk and depot pages hand in fresh ones through
window.fcpmAwake(), which fires `fcpm:awake`. This file only compares the
page's own clock with that list. It never guesses a schedule, and it has no
idle timer.

AWAKE ANYWAY:
- <html class="fcpm-awake">, set by a page that must not dim (the wall
while held, or a class taking a screen over);
- an hour after any touch, click, key or real pointer movement, and
each one starts the hour again. Nobody should watch a room's screen
dim on them because the schedule didn't know they were there;
- no list, an empty list, or past the list's last end. A screen that
doesn't know fails awake.

DIM is pure black over the page, the page at 10%, and the three squares:
a split clock (hour hand at the top, a seconds tick in the middle, minute
hand at the bottom), the lit square walking the column, the column gliding
slowly across the black and bouncing off the edges, against burn-in.
The first touch on a dim screen only wakes it.

PROOFS, on the top page's URL: ?at=HH:MM or ?at=<ISO time> pretends it is
then (as the wall and class mode do), ?awake and ?dim pin either state.

window.FCPMDim = { isDim(), tally(el), wake() }. The wall asks isDim() every
frame and stops turning while it is true. tally() draws the mark into any
element; the idle screen uses it. wake() is a touch from elsewhere.

Only the top window runs it. The wall's modules are pages in iframes that
carry this file too, and there must be one layer, the shell's.

No build step, no network, ES5-ish: it has to run inlined into a page
read over file:// on a panel that has been off for a month.

## 2

Above `var skew = 0, at = q.get('at');`

?at=: HH:MM today, or anything Date can read. The clock then runs on
from there.

## 3

Above `function walk(t) {`

Down the column and back up, never wrapping: a level meter, not a
progress bar. Reduced motion keeps it on the middle square.

## 4

Above `var x = 0, y = 0, vx = 1, vy = 1, last = 0, movedHour = -1;`

A disc on a frictionless table: a straight line at a calm, constant
speed, bouncing off the edges. About a minute to cross a portrait panel.
Reduced motion: no glide; it moves to a new place once an hour instead.

## 5

Above `var waking = 0;`

Waking keeps the layer catching for a moment after it starts to go, so
the rest of the touch that woke it (the click a tap ends in) lands on
the layer and not on a button that has just appeared under it.

## 6

Above `var px = null, py = null;`

A pointer that hasn't moved is not a person: browsers send a mousemove
when the page changes under a resting cursor, and the layer appearing is
exactly that. Count only real movement.

## 7

Above `function wake() { wokeUntil = now() + HOUR; judge(); }`

wake(): what a touch does, without a touch: the hour starts again and the
screen wakes. For input seen somewhere else, such as kiosk-1's door
reading Windows' last input so a mouse on one panel wakes both (#178).
Nothing was pressed, so nothing needs swallowing.
