# Content still needed

Every `TODO` in the repository, in one place.

Most of these exist because the content is rendered client-side by a Wix app on
the current site — it isn't in the HTML that gets served, so it couldn't be
read programmatically. Those items need a human to copy them over, and they are
also a decent argument for the migration: content that a script can't read is
content Google reads poorly too.

Some of what follows now has feedback attached to it. That feedback lives in
[REVIEW-NOTES.md](REVIEW-NOTES.md) and is **not decided** — it is what was
said, not what we are doing. Items below carry a pointer where a note applies.
This file stays the list of what is still needed; nothing moves out of it
until somebody has actually chosen.

## Blocked — content is inside a Wix widget

| Page | What's missing |
|---|---|
| `/donate` | Entire page. Suggested amounts, recurring options, the case for support, and which processor is in use. |
| `/bulletin-board` | Entire page. Unknown what's posted or how it's submitted. |
| `_podcasts/*` (all 8) | Descriptions, hosts, player embeds, subscribe links. |
| `/policies/non-discrimination` | The statement text. Copy verbatim, don't paraphrase. |
| `/submit` | The full legal agreement text. |
| `/teach` | The instructor application questions. |

## Equipment

Not a migration item. The inventory lives in Booqable, which is the system of
record, and members never pick items themselves — they describe the job and
staff pull the gear. So the site needs a category-level summary, not a
catalogue.

What's needed is four one-line descriptions in `_data/equipment.yml`
("camcorders, mirrorless bodies, and a cinema camera"), written by someone who
knows the kit. Ten minutes, not a data-entry project.

## Needs a decision, not a copy-paste

- **Membership term.** The current page says both "January 1 – December 31" and
  "expires one year from the sign-up date." Pick one.
- **Membership tier benefits.** Benefits are described in one shared paragraph;
  what actually differs between Sponsor, Student, Creator, and Producer isn't
  stated anywhere.
- **Class listings.** The only content on the site with a schedule. Needs to
  come from the ticketing provider or a `_data/classes.yml` file — not
  hand-maintained in `classes.md`. The wider *events* calendar Bryan asked for
  is **settled and built**: it lives on `/meet/`, which already merges classes,
  board meetings and `_data/community.yml`. Meetups and video events go in the
  last of those with a `kind`. What is missing is entries, not code.
- **Bulletin board mechanism.** Data file the maintainers edit, or a submission
  form with approval. Depends on volume.
- **Nonprofit production pricing.** Currently unpublished. Publish or don't.
- **Equipment terms and conditions. BLOCKING.** Host as a page or keep as a
  PDF. The reserve page now says in shipped copy that users "must agree to FC
  Public Media's Equipment Terms and Conditions" — the sentence went in with
  the rest of Bryan's wording, and there is nothing to link it to. It is
  deliberately unlinked rather than pointed at a 404. See REVIEW-NOTES.
- **Programming schedule.** Link out to Cablecast or embed it.

## Never existed and probably should

- **An about page.** The current site has none, which is unusual for a
  nonprofit asking for donations. **The mission statement is no longer
  missing** — Bryan's wording is in `org.mission` and renders on the homepage;
  `/about/` should pull the same value rather than a second copy. What that
  page still needs is the history and the roster.
- **Board and staff roster.** Board members host studio sessions, so the public
  has a reason to know who they are.
- **Financials.** EIN, Form 990, annual report.
- **Facility descriptions.** The booking pages list durations but not what's
  actually in each room.

## Cablecast data hygiene

Now that the catalog is exposed on the site, its gaps are visible:

- **461 of 1,486 programs have no category.** They fall into "Uncategorized"
  on the archive page. Some are certainly local work that is currently
  impossible to find.
- **746 programs have no VOD**, so they are listed but not watchable. Worth
  knowing whether that is deliberate (rights) or just un-encoded.
- **No program has captions.** `hasCaptions` is false across the board, and
  Cablecast has a captioning service configured.
- **Titles carry filename debris** — `Midnight_Limited_1940_2026-07-14_11_59_43`,
  `DISCLOSURE - Resized for FC Public Media`. These are what the public sees.
- **`LOCAL_PREFIXES` in `script/sync-cablecast.py`** is my guess at which
  categories are locally produced. Someone who knows the programming should
  confirm it.

Fixing any of these happens in Cablecast, not in this repository, and shows up
on the site at the next weekly sync.

## Assets

- A real logo. The current wordmark uses a plain block as a placeholder mark.
- Photography of the space, the gear, and people using both. **In progress:**
  Bryan is shooting new ones and Autumn is pulling what exists out of Google
  Drive. Older pictures may still be on the Wix site, which we **read and never
  write** — see CLAUDE.md. This is the dependency under a photo behind the
  homepage mission band, a picture per facility, and whatever goes at the top
  of the reserve page now the floor plan has moved down. All three are small
  and all three wait on files. See REVIEW-NOTES.
- Webfonts, if desired. Swap the two `--font-*` lines at the top of
  `assets/css/site.css`; everything scales off them.
