# `site/index.html`

Moved out of the file. Unreviewed.

## 1

Above `{%- assign c = site.data.community -%}`

The top of this page is the page. Everything that matters — who we are,
where to find us, how to check in, and what is happening right now — sits
above the fold and nothing below it is required reading.

What is deliberately NOT here: a grid of tiles for Equipment / Studios /
Classes / Submit, and a second copy of the community list. Those were the
menu rendered twice, once as a menu and once as a section, which is two
places to maintain and two places to disagree. If it is in the header, the
header is where it lives.

The channel buttons are the exception that proves it. Slack, YouTube,
Instagram, the newsletter, the studio itself — none of those are in the
menu, so listing them here is the only listing they get. Text, not icons.

The hero photo is a background *behind* a solid panel, not underneath the
text. Set org.hero_image and it appears. Empty is a perfectly good state.

## 2

Above `{%- assign hero_image = site.data.org.hero_image | default: '' -%}`

Liquid treats "" as true — only nil and false are falsy — so `if hero_image`
matched an empty string and the hero rendered as a photo hero with
background-image: url(''): extra padding, an inset panel, and no photo. The
comparison has to be explicit.

## 3

Above `<div class="hero-actions hero-channels">`

Where to find us. First entry is the studio itself, which is why the
QR sits directly under it — the two are the same errand.

## 4

Above `<a class="checkin-card-qr hero-qr" href="{{ '/check-in/' | relative_url }}">`

A grid child rather than part of the panel, so a phone can order it
directly under a running class. It is the same code either way — for a
class, for a bay, for someone who just walked in — which is why it says
"check in" and nothing more specific.

## 5

Above `<aside class="hero-class" data-class-slot hidden>`

A class in progress. Hidden until assets/js/classmode.js says otherwise,
from data baked in at build time with no request made. It belongs up
here rather than in a section further down: someone standing in the
doorway holding a phone should not have to scroll to find out that the
thing they walked in for is running.

## 6

Above `{%- assign mission = site.data.org.mission | default: '' | strip_newlines | strip -%}`

THE MISSION STATEMENT, BEFORE YOU REACH THE CHANNEL.

Asked for by the board president in his September 2026 review: a mission
statement before scrolling down to the Watch section, "maybe in front of a
photo of the studio". The words are his and are kept verbatim — see
CLAUDE.md on why his phrasing is not ours to improve.

The photo half is deliberately not built. There is no photograph of the
studio in this repository yet, and a band styled around an image it does not
have reads as broken rather than restrained. Type only is the same call the
hero already makes about org.hero_image, and it is a perfectly good state.
When the photography arrives this is where it goes.

Renders nothing at all if org.mission is empty, so the page closes up around
it rather than leaving a gap.

## 7

Above `{% if cc.total %}<a class="btn" href="{{ '/watch/archive/' | relative_url }}">Browse all {{ cc.total`

One button, one destination. There is no "all ways to watch" link beside
it because Watch is in the header, and there is no grid of recent
programs because the archive is the place programs are listed.

## 8

Above `{%- assign air = site.data.airings -%}`

WHAT ACTUALLY WENT OUT, not what was recently catalogued.

_data/airings.json is the station's own broadcast log — every slot Cablecast
ran over the last year, filler excluded — so `last` is a real airing date.
cablecast.json's `date` is a catalog date and several dozen records share
one, which would have rendered as eight programmes all claiming the same
day.

The join and the stringify are the ones watch/archive.md already uses: the
id has to be a string before it will index the JSON object, and Liquid
returns nothing rather than complaining when it does not match.

Sorting is the delimited-string idiom, because Liquid cannot sort objects
by a key it has to look up. ISO dates sort lexicographically, so a plain
string sort is a date sort here.

AND THEN ONE PER PRODUCER, WHICH IS THE PART THAT MATTERS.

The date alone does not discriminate: the channel runs most of its
catalogue on a loop, so the entire top forty shares a single last-aired
date. Sorting by it and taking eight does not give you the eight most
recent things, it gives you eight arbitrary rows from a tie — and whoever
has the most programmes in the catalogue wins the whole strip. Sorted
naively this was six consecutive episodes of one serial, then fourteen of
the top sixteen from a single producer.

So the strip is deduplicated by producer. Same honest claim — all of these
did air recently — and eight different people instead of one. Anything
with no producer recorded is allowed through, since there is nothing to
collide on.

The delimiters around each name matter: `contains` on a bare concatenation
would match any producer whose name is a substring of another's.

## 9

Above `{%- assign aired_on = parts[0] -%}`

Both pulled into their own variables because Jekyll's include tag
takes plain variables or quoted strings only — `aired=parts[0]` is
a parse error, not a lookup.

## 10

Above `{%- assign duplicate = false -%}`

An explicit flag, not `seen contains stamp == false`. Liquid has
no parentheses and no boolean negation of a `contains`, so that
expression parses as something else entirely and quietly lets
duplicates through — which it did, twice, from one producer.
