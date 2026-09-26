# Bugs found by following recipes

A step that failed because the page does not offer what the recipe says it
does. See [`README.md`](README.md) for what goes here and what does not.

Each entry: the recipe and step, what the page did, why it matters to a
person, where in the code, and whether it was **seen** (followed on the real
page) or only **read** (found by reading the code the page is built from).
A *read* bug is confirmed or struck the first time the recipe is followed.

Fixed bugs are deleted; the history keeps them.

---

## Hold is renamed every second while it holds

- **Recipe:** [`wall.md`](wall.md), step 5
- **Status:** seen, 2026-09-26, on roller-tv, at `e8d44d1` (#138).
- **What the page does:** a pressed Hold writes its countdown into the
  button's own text, so the button's accessible name becomes "Held 2:57",
  then "Held 2:56", and so on. `aria-pressed` is right throughout.
- **Why it matters:** anything that finds the button by its name, whether a
  voice command ("click Hold"), an attendant, or a screen reader user's list
  of buttons, cannot find Hold to let go early, and finds a new name each
  second if it looks again. A screen reader resting on the button may read
  each change.
- **Where:** `machines/kiosk-1/door.py`, the wall shell's `label()`.
  Probably fixed by keeping the button's text "Hold" and putting the
  countdown beside it (in the "Showing" line, say), not in a live region.
  Not tried.

The three earlier wall bugs were fixed by #138 and are in this file's
history.
