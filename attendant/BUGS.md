# Bugs found by following recipes

A step that failed because the page does not offer what the recipe says it
does. See [`README.md`](README.md) for what goes here and what does not.

Each entry: the recipe and step, what the page did, why it matters to a
person, where in the code, and whether it was **seen** (followed on the real
page) or only **read** (found by reading the code the page is built from).
A *read* bug is confirmed or struck the first time the recipe is followed.

Fixed bugs are deleted; the history keeps them.

---

## The wall's frame is always called "Module"

- **Recipe:** [`wall.md`](wall.md), step 2
- **Status:** read, 2026-09-26. Not seen yet.
- **What the page does:** the shell's frame is `<iframe title=Module>`, and
  `show()` changes its `src` but never its title.
- **Why it matters:** someone using a screen reader, or an attendant, hears
  "Module" whichever module is up. The only way to know which one it is, is
  to find the lit button.
- **Where:** `machines/kiosk-1/door.py`, `wall_files()` (the `<iframe>`) and
  `WALL_JS` (`show()`).

## The wall's modules reload every minute with no way to stop it

- **Recipe:** [`wall.md`](wall.md), step 5
- **Status:** read, 2026-09-26. Not seen yet.
- **What the page does:** every module page carries
  `<meta http-equiv="refresh" content="60">` (`every:` in the wall block),
  and the shell reloads every ten times that.
- **Why it matters:** a reload moves the reading position back to the top.
  For someone listening to the depot list, or an attendant partway through
  reading it, the page is gone every minute (WCAG 2.2.1, *Timing Adjustable*).
  For a screen read from across the room it is the right beat, so the fix is
  probably to pause while someone is using it, not to remove the refresh.
- **Where:** `machines/kiosk-1/door.py`, `wall_files()`.
