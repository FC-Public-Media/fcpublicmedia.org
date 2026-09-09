# Review notes — what people have said about the site

**Nothing in this file is decided.** It is a record of feedback as it arrived,
kept close to verbatim, so that it is in front of us while we work instead of
sitting in an inbox. Autumn has to digest it before any of it becomes a change.

Read it as *"this was said"*, never as *"this is the plan."* When something
here does become the plan, it moves — into the page, into `_data/`, or into
[CONTENT-TODO.md](CONTENT-TODO.md) as a decision that has actually been made —
and the entry here gets struck through with a pointer to where it went.

The value of the file is the second column of every table: **where the note
lands in the repo.** Feedback arrives as prose about a page; work happens in a
particular file. Doing that translation once, while the note is fresh, is most
of what this file is for.

More rounds are expected. Each gets its own section, newest at the bottom, so
the history of what was asked for stays legible even after it is superseded.

---

## Round 1 — Bryan, board president, 4 September 2026

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
| Suggestion: replace the tagline **"PUBLIC MEDIA is made of You."** with **"You are PUBLIC MEDIA"** | `tagline:` in the front matter of `index.html`. One line. |
| *"I'd like a mission statement before scrolling down to the Watch Page. Maybe in front of a photo of the studio."* | New block in `index.html` between the hero and Watch; the photo is `org.hero_image`, currently `""`. |
| His proposed mission statement: *"Fort Collins Public Media offers the equipment, training, and artistic space for Northern Coloradans to craft their visions into reality."* | Wants a home in `_data/org.yml` if it is going to appear in more than one place — and it will, because `/about` needs it too. |
| *"After the Mission Statement I think it'd be beneficial to have an Events Calendar"* — listing **Classes**, **Meetups**, and **Video Events** *("E.G. Comic Con")* | See the note below. This is the one that is not small. |

**The events calendar is a scope change, not a section.** MANIFEST §7 defers a
*live class schedule* — class times, currently typed into `_data/classes.yml`,
eventually read from the Microsoft 365 calendar. Bryan is asking for something
wider: meetups and outside video events like Comic Con are not classes, they
are not in `classes.yml`, and nobody is currently maintaining a list of them
anywhere. Before this can be built somebody has to say **where the events come
from**. Deciding that is the work; rendering them is an afternoon.

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
| *"I like having the floorplan on the page. However I don't think it needs to be at the top. I think a video/slideshow of the space will be a better selling point. The floor plan might be better at the bottom as extra information"* | `reserve.md` — the `<figure class="floor-plan">` moves out of `.reserve-intro` to the foot of the page. The captioning logic and `plan_label` come with it unchanged. |
| *"I'd like a picture for every option/offering. I can take and send you the pictures. There may also be some old ones on Wix."* | New `image:` key per entry in `_data/facilities.yml`, and markup for it in the `rows-spaces` list. |

**He is offering to shoot the photography.** That is the single biggest
unblock in the file. CONTENT-TODO's Assets section asks for *"photography of
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

Two things in there are policy, not copy, and are the reason this section
should not be pasted in without an answer:

- **The credit card changes meaning.** The page currently says *"a credit card
  for a temporary charge as collateral"* — a hold. His paragraph says *"a
  valid credit card for late fees and incidentals"* — a card kept on file to
  be charged against. Those are different arrangements and the second is the
  one people ask questions about. Which is it?
- **It cites a document that does not exist.** *"FC Public Media's Equipment
  Terms and Conditions"* has no page and no PDF on the site. CONTENT-TODO
  already carries "host as a page or keep as a PDF" as an open decision; this
  sentence promotes it to blocking, because copy that names an agreement and
  then does not link to it is worse than copy that never mentioned one.

Note also that his numbered list drops the credit card from the list and moves
it into the paragraph. If both go in as written, the requirement is stated once
rather than twice — which is probably the intent, but it means the two edits
travel together.

### Not commented on

Worth recording, because silence on a staged page is weak evidence of assent
and it is useful to know what he did look at. The **"Check availability — not
wired up yet"** placeholder for Booqable appears in his printout and he did not
remark on it, so the `booking` entry in `_data/providers.yml` stays `pending`
on the same terms as before. Everything below the equipment section on the
reserve page, and everything below the hero on the home page, he passed over.

---

## What is actually blocked on Autumn

Pulled out of the above so it is not buried in prose. None of these are
copy edits; each changes what the site claims.

1. **Equipment: hold, or card on file for fees?** The two phrasings describe
   different arrangements.
2. **Equipment Terms and Conditions** — the new copy names it. It needs to
   exist, or the sentence needs to change.
3. **Where do calendar events come from?** Classes are in `_data/classes.yml`.
   Meetups and outside video events are nowhere.
4. **Is equipment checkout self-serve or staff-picked?** His intro rewrite
   implies the first; the rest of the site says the second.
5. **Video or slideshow** for the space, in the slot the floor plan vacates.

## What can be done as soon as somebody says yes

Small, self-contained, no decision underneath them:

- Tagline → "You are PUBLIC MEDIA" (`index.html` front matter).
- Mission statement into `_data/org.yml`, rendered on the home page and `/about`.
- Floor plan moves to the foot of `reserve.md`.
- `image:` key on `_data/facilities.yml` entries, once photographs exist.
- `org.equipment_email` → `equipment@fcpublicmedia.org`, **on 1 November 2026**.
