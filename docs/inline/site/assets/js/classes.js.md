# `site/assets/js/classes.js`

Moved out of the file. Unreviewed.

## 1

Above `export function readConfig(elementId = 'class-config') {`

Shared class-window logic.

Two pages ask the same question — "is a class happening right now?" — and
they must never disagree. The homepage uses it to decorate the check-in
panel; the check-in page uses it to preload itself for a class arrival.

So the answer lives here, once, and both import it. The QR on the door
carries no class information at all: it is a permanent link to /check-in/,
and the page works out the rest. Nothing to reprint, nothing to rotate,
nothing that can be stale in someone's pocket.

Windows:

  soon   the leadMinutes before the start — visible on the way in
  late   the first lateMinutes after it starts — still worth walking in
  now    running, past the point of joining late

`late` is a sub-case of the class being on, not a separate phase of the
day; both mean "the class is happening".

## 2

Above `export const sessionKey = (session) => ${session.starts}|${session.title};`

Stable identity for a session, so an RSVP can be matched back to it without
depending on array order or on a field the calendar may not provide.

## 3

Above `export function watch(render, intervalMs = 60000) {`

Re-evaluate on a timer, but only while the tab is visible. Both callers want
exactly this, and both would otherwise get it slightly wrong.
