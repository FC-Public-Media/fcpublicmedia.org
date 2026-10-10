# `bin/test_make_wallpaper.py`

Moved out of the file. Unreviewed.

## 1

Above `import math`

What the wallpaper generator is not allowed to get wrong.

Two of these are real rules and the rest are arithmetic.

The real ones:

1. THE TILT IS NEGATIVE. A square leaning counterclockwise reads as a
   clipboard clip lifting at its top edge. Leaning the other way it reads as
   rolling forward, which is the O in the Roblox wordmark. There are already
   copies of our mark in the wild leaning the wrong way —
   site/assets/img/icon-inverted.svg exists to say so. A wallpaper is worse than a
   favicon here, because it is a file somebody downloads once and then looks
   at every day for a year without ever opening this repository again.

2. YELLOW IS A SURFACE, NEVER A COLOUR. The same rule site/bin/test_tokens.py
   enforces on the stylesheet, enforced again on the thing the stylesheet does
   not reach. Yellow type is 1.4:1 on paper: not a near miss, invisible.
   The band design is where this would go wrong, because it is the one with a
   light field.

The arithmetic ones are here because every measurement is a fraction of a
canvas that is expected to change — a new panel is a command-line argument,
and the failure mode of a bad fraction is a mark half off the screen at one
size and fine at the one the author happened to test.

## 2

Above `SIZES = [(1050, 1680), (1680, 1050), (1000, 1000), (2160, 3840), (320, 480)]`

Portrait as mounted, landscape as shipped, a square, a 4K panel, and one
absurdly small — the fractions should not care.

## 3

Above `w, h = 1050, 1680`

band is the only design with a paper field. The plate reaches
11.7:1 on ink and 1.4:1 on paper, so where the mark sits is the whole
design, not a placement preference.

## 4

Above `for name in wp.DESIGNS:`

A rotated square is wider than its side. cos+sin of the tilt is the
factor, and forgetting it is how a mark ends up clipped at one size.

## 5

Above `for name in wp.DESIGNS:`

No design may leave the default transparent ground showing — a
wallpaper with an alpha channel renders as whatever the desktop's own
background colour happens to be, which is nobody's decision.

## 6

Above `rendered = {`

The point of the tally set is that three monitors do not look like
a tiling accident. If the renders ever come out identical the set has
silently become one wallpaper printed three times.
