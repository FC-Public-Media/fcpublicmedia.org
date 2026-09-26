# Class mode on the rolling TV: a brief for its own pass

Status: **a demo.** `class.html`, written beside the wall from
`class-sample/` (`class:` in the `wall:` block of `machines/kiosk-1/node.yml`)
and never in the wall's turn. `?light` shows the light version. This is
Autumn's brief from 2026-09-26, and then the shape she gave the demo the
same day. It is its own pass because "the footer and the top, they're all
going to want to be a little different."

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

## The shape of the demo (Autumn, 2026-09-26)

- **Header, a quarter of the screen**, in the darker slate (`--ink`), with the
  wall's slanted bottom edge. The check-in code on the yellow clock square
  ("our QR is hiding a clock inside of it"), then the class's name and its
  hours in place of "Check in" and the motto. No timer. The digital time is
  printed on the slant, where the wall's timer runs.
- **Content, the dark slate (`--slate`) or white.** Dark by default, light with
  `?light`. Only the content gets these two, so they stay reserved for the
  material.
- **Footer: the presenter's name, then the noun** for the kind of material
  (HANDOUTS), in place of FCPM and the module. Material is organised by nouns,
  meaning kinds of material, not slides. It can still be used like slides:
  numbered files keep working.
- **Sections as slanted tabs**, stacked along the -8 degree line, with no pill
  padding. The one that's up is signal yellow. The last one used is signal at
  30%, so the way back is easy to see. The rest are the dark slate. A section
  is a button named by its title. There's no rotation: a tab stays up until
  someone moves it.

**Still open:** which class and presenter the page shows (today, from
`class.yml`; later, from the calendar and the class's own folder), and more
than one kind of material in a class (the demo shows the first).
