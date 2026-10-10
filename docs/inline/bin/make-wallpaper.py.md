# `bin/make-wallpaper.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

python3 bin/make-wallpaper.py

Writes SVG and PNG into brand/wallpaper/ at the studio's own resolution, plus
a landscape set for anything that is not a rotated panel. The PNGs are
committed, because the machine that needs them is a studio workstation and not
a thing that runs a build.

Why a generator and not five hand-drawn files
---------------------------------------------
The monitor count and the resolution are both still moving. Every measurement
below is a fraction of the canvas, so a new panel is a command-line argument
rather than a redraw:

    python3 bin/make-wallpaper.py --size 2160x3840 --design plate

The whole brand is a square, a rule and two lines of type. That is small
enough to describe in arithmetic, and arithmetic is the thing that stays
correct when the canvas changes.

THE TILT IS NEGATIVE. This is the one rule that is not a preference.
A square leaning counterclockwise reads as a clipboard clip lifting at the top
edge. The same square leaning the other way reads as rolling forward, which is
what the O in the Roblox wordmark does, and there are already copies of our
mark in the wild making that mistake. See site/assets/img/icon-inverted.svg, which
exists to correct exactly this. bin/test_make_wallpaper.py fails the build
if the sign ever flips.

Rendering needs rsvg-convert (`brew install librsvg`). Without it the script
still writes the SVGs and says so — the SVG is the source, the PNG is a
convenience for an operating system that will not set a vector as a wallpaper.

## 2

Above `INK = "#121417"  # the dark field, and the masthead band`

The brand sheet, lifted from :root in site/assets/css/site.css. Kept as a literal
copy rather than parsed out of the CSS: a wallpaper is a file somebody
downloaded months ago, and it cannot follow a token change anyway. When the
palette moves, re-run this.

## 3

Above `caps = size * 0.52`

Fort Collins / PUBLIC MEDIA, the two-line lockup from the masthead.

Georgia and Helvetica rather than Source Serif 4 and Archivo. The real
faces are self-hosted woff2, which fontconfig does not read, so asking for
them here would silently fall back to something arbitrary on whichever
machine ran the render. These two are the documented metric-match
fallbacks in the stylesheet and they are on every Mac, so the substitution
is a decision rather than an accident.

## 4

Above `nudge = track / 2 if anchor == "middle" else 0`

A letter-spaced run carries the extra space after its final glyph too,
so a centred line sits half a step left of where it looks like it should.

## 5

Above `m = min(w, h)`

One mark, one rule, one lockup. The default, and the quiet one.

The composition sits low. Desktop icons stack down the left from the top
corner, so the top 40% is left deliberately empty — the wallpaper gets out
of the way of the thing the desktop is actually for, and the bottom stays
clear of a taskbar.

## 6

Above `m = min(w, h)`

Three marks in a column, one of them lit. One file per monitor.

The studio runs three portrait panels, and three identical backgrounds
read as a tiling accident rather than as a set. So the lit square walks
down the column: --lit 1 on the left panel, 2 in the middle, 3 on the
right. Each one still reads as a deliberate mark standing alone, which
matters, because the monitors get rearranged.

Unlit marks are filled slate rather than outlined. Rules and blocks do the
structural work in this brand; an outline is a third thing it does not own.

## 7

Above `m = min(w, h)`

The masthead, and then nothing. The light one.

For the panel by the door that spends its day showing check-in or the
guest network — a dark field there is a lamp pointed at the room, and the
content that lands on it is dark type on paper anyway. The band keeps the
one rule the palette cannot bend: the plate only ever sits on ink.

## 8

Above `sizes = args.size or [(1050, 1680), (1680, 1050)]`

1050x1680 is a 1680x1050 panel rotated into portrait, which is how all
three in the studio are mounted. The landscape size is the same pixels
the other way up, for a panel that has not been turned yet.
