# `brand/idle/dim.css`

Moved out of the file. Unreviewed.

## 1

Above `/* --- The mark: three squares in a column, with a rule behind them --------`

 dim.css -- the studio screens' dim layer and the mark it carries.
Read with dim.js; docs/SCREENS-DIM.md has the why. door.py's page() inlines
both into every screen page, and the idle screen links them.

The brand values are the stylesheet's (site/assets/css/site.css :root),
with fallbacks, because this also runs on pages that define none.

## 2

Above `.fcpm-tally {`

 --- The mark: three squares in a column, with a rule behind them --------

The idle screen's, lifted out so there is one. Each square carries part of
a clock: the top an hour hand, the middle a seconds tick walking its rim,
the bottom a minute hand. The lit square walks down and back up the column
on a 4 s beat.

## 3

Above `rotate: -8deg;`

 NEGATIVE: counterclockwise, the same -8deg as the icon and the wordmark.
brand/idle/index.html used to say why at length; the lean the other way
reads as rolling forward.

## 4

Above `#fcpm-dim {`

 --- The layer -----------------------------------------------------------

Pure black over the page, the page showing through at 10%. It is only
there while dim: awake, it is hidden and takes no clicks. Dim, it takes
every click and touch, so the first one wakes the screen and presses
nothing underneath. Slow in, quick out.
