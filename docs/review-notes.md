# Review notes

**Unratified board feedback: a record of what was said, not of what was decided. Never publish it.**

Each note is quoted verbatim and names the file it lands in. A struck note has shipped, and the
page is then the authority. The board's wording is authoritative over ours ([AGENTS.md](../AGENTS.md)).

## Round 1: board president, home and reserve pages

Two annotated PDFs of the staged site, `Home Page.pdf` and `Reserve Page.pdf`. Ruled on: his wording
is ideal, and the events calendar goes on `/meet/`, not the homepage.

| Note | Lands in |
|---|---|
| ~~Suggestion: replace the tagline **"PUBLIC MEDIA is made of You."** with **"You are PUBLIC MEDIA"**~~ | `tagline:` in `site/index.html` |
| ~~*"I'd like a mission statement before scrolling down to the Watch Page. Maybe in front of a photo of the studio."*~~ Shipped without the photo, which waits on photography | `site/index.html`, between the on-air bar and Watch |
| ~~*"Fort Collins Public Media offers the equipment, training, and artistic space for Northern Coloradans to craft their visions into reality."*~~ | `org.mission` in `site/_data/org.yml`; `/about/` does not render it yet |
| *"After the Mission Statement I think it'd be beneficial to have an Events Calendar"*: Classes, Meetups, Video Events *("E.G. Comic Con")* | `/meet/` "What's on": `site/_data/community.yml` events with `kind: Meetup` or `kind: Video event`. Built; no entries yet |
| *"After this I think the rest of the home page looks great!"* | none |
| ~~*"At any tier of FC Public Media Membership you can reserve both the video and podcast studios, edit with the full Adobe Creative Suite, and check out production equipment"*~~ | intro of `site/reserve.md` |
| ~~*"I like having the floorplan on the page. However I don't think it needs to be at the top... The floor plan might be better at the bottom as extra information"*~~ The video or slideshow half waits on footage | `site/reserve.md` |
| *"I'd like a picture for every option/offering. I can take and send you the pictures. There may also be some old ones on Wix."* Accepted | `image:` per entry in `site/_data/facilities.yml`, rendered in `rows-spaces`, once photos exist |
| *"On Nov 1, 2026 I'll officially switch equipment requests to this email. I'll make an announcement in the October Newsletter so people are aware. In the meantime we can still use the fcpmequipment@gmail.com email."* | `org.equipment_email` in `site/_data/org.yml` becomes `equipment@fcpublicmedia.org` on 2026-11-01 |
| ~~*"In your email please include: 1. Your contact information. 2. What equipment you will need or are looking for. 3. The dates of your production."*~~ | Equipment section of `site/reserve.md` |
| ~~*"All equipment requests must be submitted at least one week in advance. All users must provide a valid credit card for late fees and incidentals. Any User of FC Public Media equipment must agree to FC Public Media's Equipment Terms and Conditions."*~~ | Equipment section of `site/reserve.md`; the Terms are named but unlinked, since no such document exists |

Not commented on: the "Check availability — not wired up yet" Booqable placeholder, everything
below the equipment section of the reserve page, and everything below the home page hero.

## Round 2: board president, meet and learn pages

A plain email, his last notes on the staged site. Not ruled on. The fields exist, but nothing
shows until content is supplied.

| Note | Lands in |
|---|---|
| *"I'd like to see office hours posted on the page."* | through the next note |
| *"If we have a board directors section, we can post each board member's office hours in their mini-bios."* | `office_hours` per person in `site/_data/board.yml`, shown in the roster card on `/meet/` (The board, Who's on it) |
| *"Only note, picture on the page of people teaching classes."* | `photo.src` and `photo.alt` in `site/_data/classes.yml`, at the top of `/classes/`. It renders only with `alt` |

What is still open from both rounds is in [OPEN.md](OPEN.md).
