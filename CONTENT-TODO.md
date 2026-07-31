# Content still needed

Every `TODO` in the repository, in one place.

Most of these exist because the content is rendered client-side by a Wix app on
the current site — it isn't in the HTML that gets served, so it couldn't be
read programmatically. Those items need a human to copy them over, and they are
also a decent argument for the migration: content that a script can't read is
content Google reads poorly too.

## Blocked — content is inside a Wix widget

| Page | What's missing |
|---|---|
| `/donate` | Entire page. Suggested amounts, recurring options, the case for support, and which processor is in use. |
| `/bulletin-board` | Entire page. Unknown what's posted or how it's submitted. |
| `_podcasts/*` (all 8) | Descriptions, hosts, player embeds, subscribe links. |
| `/equipment` | The inventory. Published as a photo gallery. |
| `/policies/non-discrimination` | The statement text. Copy verbatim, don't paraphrase. |
| `/submit` | The full legal agreement text. |
| `/teach` | The instructor application questions. |

## Needs a decision, not a copy-paste

- **Membership term.** The current page says both "January 1 – December 31" and
  "expires one year from the sign-up date." Pick one.
- **Membership tier benefits.** Benefits are described in one shared paragraph;
  what actually differs between Sponsor, Student, Creator, and Producer isn't
  stated anywhere.
- **Class listings.** The only content on the site with a schedule. Needs to
  come from the ticketing provider or a `_data/classes.yml` file — not
  hand-maintained in `classes.md`.
- **Bulletin board mechanism.** Data file the maintainers edit, or a submission
  form with approval. Depends on volume.
- **Nonprofit production pricing.** Currently unpublished. Publish or don't.
- **Equipment terms and conditions.** Host as a page or keep as a PDF.
- **Programming schedule.** Link out to Cablecast or embed it.

## Never existed and probably should

- **An about page.** The current site has none, which is unusual for a
  nonprofit asking for donations.
- **Board and staff roster.** Board members host studio sessions, so the public
  has a reason to know who they are.
- **Financials.** EIN, Form 990, annual report.
- **Facility descriptions.** The booking pages list durations but not what's
  actually in each room.

## Assets

- A real logo. The current wordmark uses a plain block as a placeholder mark.
- Photography of the space, the gear, and people using both.
- Webfonts, if desired. Swap the two `--font-*` lines at the top of
  `assets/css/site.css`; everything scales off them.
