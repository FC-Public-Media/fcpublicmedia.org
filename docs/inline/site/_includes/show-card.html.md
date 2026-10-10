# `site/_includes/show-card.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign s = include.show -%}`

One program from the Cablecast catalog.
Usage: {% include show-card.html show=item %}

## 2

Above `{%- assign shown_date = include.aired | default: s.date -%}`

`aired` is optional. Pass it and the card shows when the programme last went
out instead of its catalogue date — which is what a strip headed "recently on
the channel" is actually claiming. Without it the card is unchanged, so the
archive and the show pages carry on showing the catalogue date they mean.

The two are not close. A programme that aired last week can carry a catalogue
date of 2021, and a card that says "recently" over "2021-12-28" reads as a
bug.
