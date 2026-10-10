# `site/_data/classes.yml`

Moved out of the file. Unreviewed.

## 1

Above `# How early the homepage starts advertising a session, and how long after the`

Class sessions.

Two gears turn here, and they are deliberately separate:

  Gear 1 — the build. This file is baked into the page. Eventually it will be
           generated from the Microsoft 365 calendar by a script, the same
           way _data/cablecast.json is generated. Until then it is edited by
           hand.

  Gear 2 — the browser. assets/js/classmode.js looks at the wall clock and
           decides whether a class is happening *right now*. No request, no
           API, no key. A page built last night knows about tonight's class
           because the times came along with it.

The cost of that split is staleness: a class added this morning is not on the
site until the next build. The weekly sync already rebuilds; if classes are
added at short notice, move that to daily.

TIMES MUST CARRY AN OFFSET. "2026-08-11T18:00:00-06:00", not
"2026-08-11 18:00". Colorado is -06:00 in summer and -07:00 in winter, and a
time without an offset is read as the visitor's own zone — which is wrong for
anyone travelling, and silently wrong, which is worse.

## 2

Above `lead_minutes: 90`

How early the homepage starts advertising a session, and how long after the
start someone is still told they can join.

## 3

Above `photo:`

A photograph for the top of /classes/.

Bryan's whole note on that page was that it wants a picture of people
teaching classes — not the room, not the gear. A class is people showing
other people how to do something, and a photo of an empty studio says the
opposite of what the page is selling.

Left empty the page is type only, the same arrangement as `hero_image` in
_data/org.yml: it reads as intentional rather than broken, so there is no
rush and nothing to disable when the file does not exist yet.

`alt` is not optional when `src` is set. This is a photo of identifiable
people doing a specific thing, which is exactly the case where a decorative
empty alt is wrong — describe who is doing what.

## 4

Above `caption: ""`

Optional. A caption earns its place by saying something the picture does
not — which class, or when. Leave it off rather than restating the alt.

## 5

Above `dropin:`

Drop-in pricing for someone who turns up without having signed up.

This is not a ticketing system: people who signed up already paid through
whatever the registration flow is. This is the walk-in case.

TODO — every figure below is a placeholder. Confirm with the board before
this is shown to anyone.
