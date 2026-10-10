# `bin/test_build_kiosk.py`

Moved out of the file. Unreviewed.

## 1

Above `import importlib.util`

Tests for the kiosk artifact builder.

    python3 bin/test_build_kiosk.py

The assertions worth having here are about the two things that make this
artifact safe to hand to a machine nobody in this repository controls:

**It carries no secret.** The guest Wi-Fi password must not reach a committed
file in a public repository, and the gitignored QR that encodes it must not be
referenced either. Both are checked against a hostile case — the password
present in the sources *and* in the environment — because the guard that only
runs on the happy path is the guard that is not there.

**It stays inert and portable.** No template syntax, no address for itself, no
timestamp. Those are what let station-node render it today and an FCPM machine
render it later with the file unchanged. Each is cheap to break by accident and
silent when broken, which is exactly what a test is for.

Plus a regression test for a bug that shipped in the first draft and was caught
only by generating the file and reading it: the Wi-Fi panel inheriting the
printed poster's "point your camera at the code" wording onto a screen that has
no code on it.

## 2

Above `src = {`

Minimal but realistic sources, with the password present in the input.

The Wi-Fi password is deliberately threaded into the source dict even
though no real data file holds one. If a future edit starts copying
unknown keys through into the artifact, these tests are what notices.

## 3

Above `body = "\n".join(`

The serving address belongs to whoever serves it, not to the file.

This is the property that makes the eventual handover free: when FCPM
stands up its own node, the artifact does not change — only the
renderer. A hostname baked in here is what would break that.

## 4

Above `body = "\n".join(`

A self-stamping file churns every run and stops meaning anything.

A class's `starts:` and `ends:` are dates and are content: the schedule
a screen reads its clock against. They are the only dates allowed.

## 5

Above `def test_present_and_looks_like_a_digest(self):`

The field that lets an update bounce a screen.

A kiosk on a wall has nobody to press refresh, so the page polls this and
reloads when it differs from what it rendered with. That only works if the
field has both halves of the property: it must change when the content
changes, and it must NOT change when it hasn't. A timestamp has the first
and not the second, which is why this is a digest.

## 6

Above `def setUp(self):`

The second artifact, and why it is transport rather than a second truth.

The panel opens `brand/idle/index.html` from a clone as a local file.
Measured in Chrome 2026-09-24: a `file://` page cannot `fetch` a sibling —
opaque origin, `TypeError: Failed to fetch`, and no header can permit it —
but a `<script src>` with a cache-buster works and works repeatedly. So the
YAML is unreadable by the one consumer this artifact has.

The risk that comes with a second copy is that the two disagree. These
tests are what makes that not happen.

## 7

Above `src = sources()`

Regression: the poster has a code on it and the kiosk does not.

`wifi.poster.note` says "point your camera at the code". On a screen
with no code that reads as a broken kiosk, and the guest cannot tell
that from a missing feature. Shipped in the first draft; caught by
generating the file and reading it.

## 8

Above `def test_check_mode_passes_against_the_tree(self):`

The drift guard. This is the test that earns the generator its keep.

`kiosk/welcome.yml` is committed so a consumer needs no build step, which
means it can be stale, which means something has to say so. A stale kiosk
names a network to a guest standing in front of it.
