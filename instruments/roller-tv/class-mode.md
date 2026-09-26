# Class mode on the rolling TV: a brief for its own pass

Status: **not designed and not built.** This is Autumn's brief from
2026-09-26, recorded so the next pass starts from her words and not from a
guess. She asked for it to be its own pass, because "the footer and the top,
they're all going to want to be a little different."

## What it is for

While a class is in session, the roller can show **the teacher's supporting
materials**: resource pages that the teacher gave the studio ahead of time.

- **It's supporting media, not the presentation.** "This is not their
  presentation device, but it can be a supporting media thing." It's not a
  slide deck, "although we could think about it."
- **Sections the teacher moves between.** A teacher can have several
  resource pages, and "switch it depending on which chapter of their
  presentation they're on."
- **No rotation.** The wall's timer and turning do not apply. The screen
  shows what the class is on until someone moves it.
- **Normally out of the rotation.** A class page is not one of the wall's
  modules, "unless we're on like maybe a debug."

## Where the materials come from

- **Pre-built, and seldom rebuilt.** "We could pre-build this and save it in
  our materials so that Bay One can see it. And it wouldn't need to update
  that frequently." A class's pages are prepared once, stored with the
  studio's materials where the bay that drives the roller can read them, and
  refreshed only when the teacher sends something new.
- **As given, not processed.** Teachers hand over files, ideally Markdown or
  plain text. "I'm trying not to process it, though." Show what they gave,
  with as little conversion as possible.
- **The structure is public; the materials don't have to be.** "It doesn't
  necessarily need to be public, and so we might submodule it from somewhere
  else, but if we build the structure for showing such a thing, that's
  pretty good." So this repository gets the shape (how a class's sections
  are laid out, and the page that shows them). A class's own materials can
  live in a private repository, mounted as a submodule, the way `enhance`
  is mounted at `.enhance-engine`. Build the showing, and test it against
  sample materials.

## The navigation, and why the bar has to change

- **Section buttons like the wall's, but red.** They look like the wall's
  bottom navigation, but in the on-air red (`--record`), "because it's
  like in session."
- **The pills don't scale.** Today's pills are too wide: "there's no way
  we're going to get anyone else's custom sections in there." A section
  name the teacher chose could fill the whole width on its own. The class
  bar needs a different way to show many sections, or long names.
- **The header and footer change too.** In class mode, the check-in header
  and the FCPM bar are expected to differ from the wall's. This is the part
  that makes it a separate pass.

## Later: an admin or teacher view

With an admin mode, someone could see more: a teacher section to navigate
into. That depends on the bar and footer working well first, so it's
deferred.

## What exists to build on

- **Class detection:** `pickSession` (`site/assets/js/classes.js`), which the
  door already uses to take the wall over when a class is soon, late or on
  (`docs/KIOSK.md`, "The class on now"). Class mode is where that takeover
  could lead.
- **Drawing it:** the wall shell in `machines/kiosk-1/door.py`. It is written
  to `DIGISTATION\.wall` and shown on the roller by editing bay 1 (see
  `show.yml` and `instrument.yml` here).
- **Checking it:** `attendant/wall.md`, the attendant recipe. Class mode will
  need its own steps, and its buttons must be findable by role and name like
  the wall's.
