# `kiosk/welcome.js`

Moved out of the file. Unreviewed.

## 1

Above `window.FCPM_KIOSK = {`

GENERATED FILE — do not edit. The YAML beside it is canonical.

  python3 bin/build-kiosk.py

WHY THIS FILE EXISTS, AND IT IS NOT A PREFERENCE
-----------------------------------------------
The panel opens `brand/idle/index.html` as a local file, from a clone, with
no server behind it. Measured in Chrome 2026-09-24:

  file:// + fetch('welcome.yml')        -> TypeError: Failed to fetch
  file:// + <script src="welcome.js">   -> works, repeatedly, with a
                                          cache-buster on the src

A `file://` page has an opaque origin, so fetch and XHR are both refused
and no header can permit it. That makes the YAML unreadable by the one
consumer this artifact has — which is why the same content is emitted a
second time as an assignment a script tag can carry.

This is TRANSPORT, not a second source of truth. It is generated from the
same `kiosk/content.yml` in the same run and carries the SAME `revision`,
copied rather than recomputed, so the two cannot disagree about what they
describe. Read `welcome.yml` if you have a choice; read this if you are a
browser looking at a file path.

One assignment and nothing else. No logic, no fetch, no side effects.
