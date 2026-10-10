# `site/_includes/clock-hands.html`

Moved out of the file. Unreviewed.

## 1

Above `<svg class="clock" viewBox="0 0 100 100" aria-hidden="true" style="position:absolute;inset:0;width:1`

 Clock hands: drop this inside any mark (the tilted signal square) and it
tells the time, leaning with the mark. It draws on top of whatever else
the mark holds, the check-in QR included: the code is error-correction H
and the hands cover about 3% of it, well clear of the finder corners.
The mark has to be positioned (relative or absolute). Plain HTML, no
Liquid (keep it that way, or door.py breaks), so the site includes it
and door.py reads the same file through clock_hands(). Hide .ticks
where they'd crowd a code.

## 2

Above `<g class="hh" stroke-linecap="square">`

 Each hand is drawn twice: a signal halo, then ink, so it reads as a
hand even where it crosses the code's dark modules.
