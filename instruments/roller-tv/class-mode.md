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

- **Header, a quarter of the screen**, in the lighter slate (`--slate`), with
  the wall's slanted bottom edge. The check-in code on the yellow clock square
  ("our QR is hiding a clock inside of it"), then the class's name. No timer.
- **On the slant, above the edge:** the presenter's name at the left, in a
  serif so it reads apart from everything else. The class's hours at the
  right, written short: "6–8 PM", with minutes only when they aren't :00
  ("6:30–8 PM"). The name is a name ("Doug"): short. A long one is the
  exception, and should be the person's real name.
- **Under the edge at the right, tucked toward the corner: a pill for each
  hour** of the class, like beads on the slant, acting as an overline for
  the time. The hour you're in is lit, and the ones before it stay lit but
  dimmer. Outside the class's hours nothing is bright: the floor is visibly
  given back. The pills are a fixed size, anchored at the right, so a five-hour
  seminar reaches further toward the middle, not off the screen. The point is
  progress without rushing.
- **The time of day** sits under the pills: small, regular weight, dim, for
  the edge of the eye.
- **Colours for the pills and the time:** on white, ink for the current hour,
  slate for past hours. On the dark
  content, two whites stand in for ink and slate: the bright paper for now,
  and a dim white for past hours, which is also the time's colour. Hours
  not yet reached aren't drawn at all, though their places are kept, so
  nothing shifts. No yellow: it's too much accent here.
- **Content, the dark slate (`--ink`) or white.** Dark by default, light with
  `?light`. If it has to scroll, it runs under the header: the slanted edge
  covers it, hiding its top-left corner, and the scrollbar starts at the
  slant. The header, the pills and the time stay put. There's no plan for
  scrolling on the TV, but someone with a mouse at the bay might try it.
- **Footer, the lighter slate, holding only the sections**, as strips the
  full height of the footer, flush against each other with no gaps. Each is
  a tab turned -90 degrees, so its name reads bottom to top. Then it's skewed
  so its bottom pulls left: its top and bottom stay level with the screen,
  and only its sides lean. The name follows the lean, turned rather than
  sheared. Names only, no
  numbers. Fifteen fit across. The one that's up is signal yellow. The last
  one used is signal at 30%, so the way back is easy to see. The rest are the
  dark slate, told apart by a hairline. There's no yellow text in the footer.
  A section is a button named by its title. There's no rotation.
- **The footer's corner: CLASS**, as the wall's bar says FCPM, over a 2×2 of
  round keys that look pressable: Dark and Light, then previous and next.
  **Nothing flickers on repeated presses:** Dark and Light are two keys, not
  a toggle, so pressing one again does nothing. The arrows stop at the first
  and last section, never wrapping around, and take at most one step per
  quarter second however fast they're pressed. The arrow shapes are
  placeholders.
- **Material is organised by nouns** (the folders, such as `Handouts`),
  meaning kinds of material, not slides. It can still be used like slides:
  numbered files keep working. The noun isn't shown yet.

**Proofs:** `?at=HH:MM` on the page pretends it's that time today, to see the
pills mid-class.

**Still open:** grading the lit hour as a blend from unlit to lit through the
hour (Autumn is open to it, and it isn't built). Also still open: which class and presenter the page shows (today, from
`class.yml`; later, from the calendar and the class's own folder), and more
than one kind of material in a class (the demo shows the first).
