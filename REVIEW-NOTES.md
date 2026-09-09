# Review notes — what people have said about the site

**Feedback arrives here undecided.** It is a record of what people said, kept
close to verbatim, so that it is in front of us while we work instead of
sitting in an inbox. Nothing is authoritative on arrival; Autumn rules on it.

So read every entry as *"this was said"* until it carries an outcome. A round
that has been ruled on says so at its head, and a note that has shipped is
struck through with a pointer to where it went. **Struck through means it is in
the site — the page is the authority then, not this file.** Round 1 is ruled
on. **Round 2 is not** — its machinery is built but nothing it asks for is
visible yet, and the difference matters. Anything still open is collected at
the foot of each round.

The value of the file is the second column of every table: **where the note
lands in the repo.** Feedback arrives as prose about a page; work happens in a
particular file. Doing that translation once, while the note is fresh, is most
of what this file is for.

Each round gets its own section, newest at the bottom, so the history of what
was asked for stays legible even after it is superseded. Bryan called round 2
his *"last notes"*, so his pass over the staged site is complete — but this
file is for whoever reviews next, not for him specifically, and it should not
be closed off.

---

## Round 1 — Bryan, board president, 4 September 2026

> **Ruled on by Autumn, 9 September 2026. Most of this has shipped.** She read
> the round and answered: *"his wording is ideal"*, the events calendar goes on
> /meet/ rather than the homepage, and — as a standing order now in
> [CLAUDE.md](CLAUDE.md) — his plainer rendering of our copy is to be treated
> as authoritative, because ours is over-written. Entries below carry their
> outcome. What is still open is collected at the foot of the file.

Two annotated PDFs, printed from the staged site: `Home Page.pdf` and
`Reserve Page.pdf`. His convention, stated at the top of each: *"Bryan's
comments/suggestions are in italicized and in red."* Highlighting in yellow
marks the passage he is talking about, not a change.

He is [`hosts.yml`](_data/hosts.yml)'s Bryan — board president and the booker —
and the same person the facilities copy came from in August, which is why the
[`facilities.yml`](_data/facilities.yml) summaries come back highlighted rather
than rewritten. He is reading his own words.

His overall verdict on the home page, verbatim: *"After this I think the rest
of the home page looks great!"*

### Home page

| What he said | Where it lands |
|---|---|
| ~~Suggestion: replace the tagline **"PUBLIC MEDIA is made of You."** with **"You are PUBLIC MEDIA"**~~ **Shipped.** | `tagline:` in the front matter of `index.html`. |
| ~~*"I'd like a mission statement before scrolling down to the Watch Page. Maybe in front of a photo of the studio."*~~ **Shipped, without the photo** — there isn't one yet, and a band styled around a missing image reads as broken. Type only, same call the hero makes. | `index.html`, between the on-air bar and the Watch section. |
| ~~His proposed mission statement: *"Fort Collins Public Media offers the equipment, training, and artistic space for Northern Coloradans to craft their visions into reality."*~~ **Shipped**, verbatim. | `org.mission` in `_data/org.yml`. Still to be rendered on `/about/` when that page has the rest of its content. |
| *"After the Mission Statement I think it'd be beneficial to have an Events Calendar"* — listing **Classes**, **Meetups**, and **Video Events** *("E.G. Comic Con")* | See the note below. This is the one that is not small. |

**Answered: it goes on /meet/, not the homepage.** Autumn's call, and it turned
out to need no new machinery at all — `meet.md` already merges three sources
into one chronological list, and `_data/community.yml` already had a `kind`
field the template rendered but the documentation never mentioned. Classes come
from `classes.yml`, board meetings from `governance.yml`, and meetups and video
events go in `community.yml` as `kind: Meetup` and `kind: Video event`. Both
are now documented there with worked examples, Comic Con included.

The homepage deliberately does **not** get the list. Her reasoning: showing the
class that is *running right now* has earned its place for check-in and
visibility, but a whole calendar is a reason to visit /meet/ rather than a
reason to lengthen the front page.

What is left is not engineering — somebody has to actually enter the events,
which is a standing job rather than a one-off.

The mission statement and the studio photo are the same errand as the About
page and the `hero_image` slot, both of which have been waiting on exactly this
content. That part is an unblock, not a request.

### Reserve page — the intro

His suggested replacement for the opening paragraph:

> *"At any tier of FC Public Media Membership you can reserve both the video
> and podcast studios, edit with the full Adobe Creative Suite, and check out
> production equipment"*

Shorter and better, and it names Adobe, which the current sentence buries. Two
things it changes that are worth noticing before it is pasted in:

- **It stops saying you reserve the editing bay.** "Edit with the full Adobe
  Creative Suite" reads as a facility you walk up to. The bay is a bookable
  space with two stations and it is on the same calendar as the studios.
- **"Check out production equipment"** sits oddly beside the rest of the page,
  which says equipment is *"arranged by email rather than through the booking
  calendar"* and against CONTENT-TODO's account that members describe the job
  and staff pull the gear. His phrasing implies self-serve. It may just be
  loose wording; it may be how he intends it to work. Worth one question.

### Reserve page — the floor plan and photography

| What he said | Where it lands |
|---|---|
| ~~*"I like having the floorplan on the page. However I don't think it needs to be at the top... The floor plan might be better at the bottom as extra information"*~~ **Shipped.** The video/slideshow half is not — it waits on footage. | `reserve.md`. The `.reserve-intro` wrapper went with it: it was a two-column grid that existed only to stand the plan beside the intro, and left to itself it would have reserved 17rem for nothing. |
| *"I'd like a picture for every option/offering. I can take and send you the pictures. There may also be some old ones on Wix."* **Accepted — Autumn is taking him up on it**, and pulling what she can from Google Drive besides. Old Wix pictures are a **read**, which is all we ever do to Wix; see CLAUDE.md. | Not built yet, on purpose: an `image:` key with no images behind it is a schema nobody can fill. New `image:` per entry in `_data/facilities.yml` plus markup in `rows-spaces`, the day the photographs land. |

**He is offering to shoot the photography, and Autumn has accepted.** She is
also pulling what she can out of Google Drive, where the material exists but is
scattered. That is the single biggest unblock in the file. CONTENT-TODO's Assets section asks for *"photography of
the space, the gear, and people using both"*, and it is the dependency under
the hero photo, the per-facility pictures, and the video/slideshow he wants
where the floor plan is now. Taking him up on it is worth doing before the
layout work, not after — the design of that section depends on what the
pictures actually look like.

The video/slideshow itself has no home yet. It is a new component, and it needs
to be decided whether it is a real video or a set of stills, because those are
different builds.

### Reserve page — equipment

**The email is changing, on a date.** He has created `equipment@fcpublicmedia.org`
in Microsoft 365:

> *"On Nov 1, 2026 I'll officially switch equipment requests to this email.
> I'll make an announcement in the October Newsletter so people are aware. In
> the meantime we can still use the fcpmequipment@gmail.com email."*

So `org.equipment_email` stays `fcpmequipment@gmail.com` until **1 November
2026** and becomes `equipment@fcpublicmedia.org` on it. One line in
`_data/org.yml`, on a date that is easy to sail past. It should be somebody's
diary entry and not just a line in this file.

His suggested replacement for the "please help us by knowing in advance" list:

> *"In your email please include: 1. Your contact information. 2. What
> equipment you will need or are looking for. 3. The dates of your
> production."*

followed by a new paragraph:

> *"All equipment requests must be submitted at least one week in advance. All
> users must provide a valid credit card for late fees and incidentals. Any
> User of FC Public Media equipment must agree to FC Public Media's Equipment
> Terms and Conditions."*

**Both went in as written.** They travel together: his numbered list drops the
credit card and his paragraph picks it up, so the requirement is stated once
rather than twice. Two things about that are worth keeping in view.

- **The credit card changed meaning, and that is now live copy.** The page used
  to say *"a credit card for a temporary charge as collateral"* — a hold. It
  now says *"a valid credit card for late fees and incidentals"* — a card kept
  on file to be charged against. Autumn ruled his wording ideal, so this is
  decided rather than open, but it is a **policy** difference and not a
  rephrasing. Somebody should confirm that is how equipment checkout actually
  works in practice, because the page now promises it.
- **It cites a document that does not exist. This one is still open.**
  *"FC Public Media's Equipment Terms and Conditions"* has no page and no PDF.
  CONTENT-TODO already carried "host as a page or keep as a PDF" as an open
  decision; the sentence shipping promotes it to **blocking**, because copy
  that names an agreement and cannot link to it is worse than copy that never
  mentioned one. It is deliberately unlinked rather than linked to a 404.

### Not commented on

Worth recording, because silence on a staged page is weak evidence of assent
and it is useful to know what he did look at. The **"Check availability — not
wired up yet"** placeholder for Booqable appears in his printout and he did not
remark on it, so the `booking` entry in `_data/providers.yml` stays `pending`
on the same terms as before. Everything below the equipment section on the
reserve page, and everything below the hero on the home page, he passed over.

---

## Still open after round 1

Ruled on 9 September 2026. What survives, in order of how much it matters.

1. **Equipment Terms and Conditions must now exist.** The reserve page names
   the document in shipped copy and cannot link to it. Page under `policies/`
   or a PDF — either is fine, neither has been chosen. **This is the one that
   should not sit.**
2. **Does equipment checkout work the way the page now says it does?** Two
   things to confirm against practice rather than against each other: the card
   is now described as being held for *late fees and incidentals* rather than
   as a hold, and Bryan's *"check out production equipment"* reads more
   self-serve than `_data/facilities.yml`'s *"arranged by email"*. Both are
   defensible; neither has been checked with the people who run it.
3. **Video or slideshow of the spaces**, in the slot the floor plan vacated.
   Different builds, and both wait on footage that does not exist yet.
4. **Somebody has to enter the events.** The calendar works and is documented;
   `community.yml` currently holds `events: []`.

## Round 2 — Bryan, board president, 9 September 2026

> **Not ruled on.** Both notes have had their *machinery* built, because both
> were unbuildable-into-nothing otherwise — but neither is visible on the site
> yet, and both wait on content rather than on code. Read the outcomes below as
> "the site can now accept this", not "the site now does this".

Plain email this time rather than annotated PDFs, and he calls it **"last notes
from bryan"** — so with Home, Reserve, Meet and Learn covered, his pass over
the staged site is complete. It is also by far the shortest round, which is
worth reading as a result rather than as a lull.

### Meet page

| What he said | Where it lands |
|---|---|
| *"I'd like to see office hours posted on the page."* | Nowhere on its own — see the sub-note, which is how he wants it done. |
| *"If we have a board directors section, we can post each board member's office hours in their mini-bios."* | **Machinery shipped.** `office_hours` per person in `_data/board.yml`, rendered inside the roster card on `/meet/`. |

We do have a board directors section, so his conditional resolves: it is
"Who's on it", the last part of **The board** on `/meet/`. It used to be a page
of its own.

**This renders nothing today, and that is the finding.** `_data/board.yml` is
an empty list — it has been since it was written — so a field for each board
member's hours produces exactly zero board members' hours. The president has
now asked for something on the site that cannot appear until the roster is
filled in, which quietly promotes **"Board and staff roster"** in
[CONTENT-TODO.md](CONTENT-TODO.md) from *never existed and probably should* to
*a named person is waiting on it*.

Two smaller things fell out of building it:

- **`photo` was documented and never rendered.** `_data/board.yml` has offered
  a `photo` field since the file was written; `meet.md` ignored it. An optional
  field that silently does nothing is worse than no field at all, because the
  first person to set one concludes the site is broken rather than that the
  template is. It renders now.
- **There is deliberately no studio-wide office-hours setting.** He tied the
  hours to people, and a second org-level field would be a second place to look
  and a second thing to contradict. If the studio ever keeps hours belonging to
  nobody in particular, `address.note` in `_data/org.yml` already says *"Open
  by appointment"* and is where that would go.

### Learn page

| What he said | Where it lands |
|---|---|
| *"Only note, picture on the page of people teaching classes."* | **Machinery shipped, waiting on a file.** `photo:` in `_data/classes.yml`, rendered at the top of `/classes/`. |

*"Only note"* is doing real work in that sentence: everything else on the page
passed, including the standing admission that class listings have no home yet.

**One reading was chosen and it should be checked.** *"People teaching
classes"* can mean a single photograph of instruction happening, or a portrait
of each instructor beside their class. The first is what was built — one photo
at the top of the page — because it is cheap, it needs one file rather than a
roster of instructors the site does not model, and it is trivially replaced by
the second if that is what he meant. `_data/classes.yml` sessions carry no
`instructor` field at all today, so the per-instructor reading is a genuinely
larger piece of work and not one to start on a guess.

Also settled while building it: **`alt` is required, not optional.** A `src`
with an empty `alt` is not rendered. These are photographs of identifiable
people doing a specific thing, which is the exact case where a decorative empty
`alt` is the wrong answer, and a guard is more reliable than a note.

## Still open after round 2

1. **The board roster.** Names and roles at minimum, and Bryan's office hours
   with them. Nothing he asked for on `/meet/` appears until this exists.
2. **A photograph of a class in progress.** Same dependency as everything under
   *Waiting on photographs* below, and now with a specific brief: people
   teaching, not the room and not the gear.
3. **Which reading of the Learn photo he meant** — one picture of instruction,
   or one per instructor. Answerable in a sentence by asking him.

## Waiting on photographs

Not blocked on a decision — blocked on files. Autumn is pulling from Google
Drive and Bryan is shooting new ones. Five things unlock the moment they land,
and all five are small:

- The homepage mission band takes a photo behind it, the way `org.hero_image`
  already can.
- `image:` per entry in `_data/facilities.yml`, rendered in `rows-spaces`.
- Whatever goes at the top of the reserve page where the plan used to be.
- **A class in progress**, for the top of `/classes/` — `photo.src` and
  `photo.alt` in `_data/classes.yml`. Round 2, and the one with a brief
  attached: *people teaching*, not an empty studio.
- **Headshots for the board roster**, `photo` per person in `_data/board.yml`.
  Not asked for, but the field renders now and the roster has to be written
  either way.

Two of these are now things a named person has asked to see, which is a
different kind of waiting from the other three.

Old pictures may also be on the Wix site. **Retrieving them is a read**, which
is the only thing we ever do to Wix — see [CLAUDE.md](CLAUDE.md).

## Diarised

- **1 November 2026** — `org.equipment_email` becomes
  `equipment@fcpublicmedia.org`. It is `fcpmequipment@gmail.com` until then and
  Bryan announces the change in the October newsletter. One line in
  `_data/org.yml`, and nothing in this repository will remind anyone.
