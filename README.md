# fcpublicmedia.org

A static site for Fort Collins Public Media. Built with Jekyll, deployed to
Azure Static Web Apps.

This is a proposal-stage scaffold. The structure is real and it builds; a lot
of the content is marked `TODO` because it lives inside Wix widgets on the
current site and can't be read from outside. See [CONTENT-TODO.md](CONTENT-TODO.md).

---

## The idea

The current site is on Wix. Almost all of it is static — prose, images, a few
embeds. The parts that genuinely aren't static come down to five transactions:
class tickets, membership dues, donations, studio booking, and program
submissions. None of those require a site builder. They require a payment
processor and a calendar.

So: publish the static part as static files, and treat the five transactions as
explicit, swappable integrations rather than as a reason to rent a platform.

## Running it

```
bundle install
bundle exec jekyll serve
```

Then open <http://localhost:4000>. Edits rebuild automatically. There is no npm,
no bundler, no CSS preprocessor, and no plugins.

## How it's laid out

```
_config.yml              Site settings. ~40 lines, all commented.
_data/                   Content that repeats or changes. Plain YAML.
  org.yml                Address, email, phone, socials.
  nav.yml                Header and footer menus.
  providers.yml          The five transactions. See below.
  membership.yml         Tiers and prices.
  facilities.yml         Bookable spaces.
  equipment.yml          Gear inventory.
  watch.yml              Channels and carriage.
  board.yml              Board and staff roster.
_layouts/                Three of them: default, page, podcast.
_includes/               Four: head, header, footer, transaction.
_podcasts/               One file per show. Shares the podcast layout.
assets/css/site.css      The entire visual design. One file.
assets/js/nav.js         Ten lines. The mobile menu. That's all the JS.
*.md                     One file per page. Filename becomes the URL.
api/                     The small server-side piece. See "Members" below.
staticwebapp.config.json Routing, redirects, auth rules.
```

That's the whole thing. Nine template files and a stylesheet.

### Adding a page

Create `something.md` in the root:

```markdown
---
title: Something
lede: One sentence under the heading.
---

Write in Markdown.
```

It's live at `/something/`. Add it to `_data/nav.yml` if it belongs in a menu.

### Adding a podcast

Copy any file in `_podcasts/` and edit the front matter. It appears on
`/podcasts/` automatically and gets its own page.

### Why so little Jekyll

Deliberately. Jekyll is here to loop over data files and stamp out a header —
not to be learned. Anyone who can edit YAML and Markdown can maintain this
site, and anyone who can write HTML and CSS can restyle it. If a future need
argues for a plugin, check first whether a `_data` file and a ten-line Liquid
loop would do it. On a site this size, it usually will.

No React. Nothing to compile. Not knowing a framework should never be the
reason someone doesn't contribute.

---

## The five transactions

Everything on this site that isn't a static file goes through
`_data/providers.yml` and `_includes/transaction.html`. That's on purpose:
switching a vendor is a one-line edit, and it's impossible to lose track of how
many paid integrations the organization has.

| Key | What it is | Now |
|---|---|---|
| `tickets` | Class registration | Wix Events |
| `membership` | Dues | Wix Pricing Plans |
| `donate` | Donations | Wix Donations |
| `booking` | Studio and bay reservations | Bookable — staying |
| `submit` | Program submissions | Wix form + Dropbox |

An entry with an empty `url` renders as a visible "not wired up yet" block
rather than a dead button, so nothing ships silently broken.

Booking stays on Bookable. Microsoft 365 calendar integration is being built
separately; when it lands, only the `booking` entry changes.

---

## Members and sign-in

The current site has no real accounts, and it doesn't need them. What it needs
is a way to tell whether the person asking to book a studio has paid.

Azure Static Web Apps does this without a user table:

1. A visitor clicks sign in and authenticates against **Entra ID**. FCPM never
   stores a password and never has one to leak.
2. SWA calls **`api/GetRoles`** once, with the visitor's email.
3. That function looks up whether the email has paid dues and hasn't expired,
   and returns `["member"]` or `[]`.
4. `staticwebapp.config.json` gates `/members/*` on that role.

The membership record itself is the only thing FCPM stores: an email address
and a paid-through date. The natural home is a **SharePoint list in the
existing Microsoft 365 tenant**, read through Microsoft Graph — no new vendor,
no new bill, and board members can see and edit it without touching code.

The write side is the payment redirect: a member pays, the provider sends them
back or fires a webhook, and that records the dues. Signing in by itself never
grants membership.

`api/src/functions/GetRoles.js` is a working stub with the lookup left as a TODO.

## Forms

A static site can't accept a form post. Two options, both fine:

- **A function in `/api`** that relays the submission to `info@fcpublicmedia.org`
  through Microsoft Graph. No third party, no per-submission cost, and the mail
  is already in the tenant.
- **A hosted form service** for the ones with real complexity — the program
  submission form has ranked scheduling preferences, a file upload, and a legal
  agreement, and is not worth hand-building.

## Deploying

`.github/workflows/deploy.yml` builds with Jekyll and deploys to Azure Static
Web Apps on every push to `main`. Pull requests get their own preview URL,
which means the board can look at a change before it goes live — something Wix
has never offered.

One secret is required: `AZURE_STATIC_WEB_APPS_API_TOKEN`, from the Static Web
App resource in the Azure portal.

The free tier covers the static hosting, the managed functions, the auth, and a
custom domain with a certificate.

### Why Azure and not GitHub Pages

Normally GitHub Pages plus Cloudflare would be the answer. Here the
organization already has Microsoft 365, and Azure Static Web Apps bundles
static hosting, Entra sign-in, and a small serverless API into one free
resource. That combination is what makes members-only pages possible without
running a server or adding a vendor. The site is still just static files — if
Azure ever stops being the right host, `_site/` deploys anywhere.

---

## Known issues on the current site

Carried over as a to-do list, since each is a one-line fix here:

- Footer copyright reads 2025
- The instructor page slug is misspelled: `/innstructor-application`
- Donate is not linked from the site navigation
- Two abandoned store sitemaps from 2022 are still published
- Membership term is stated two contradictory ways (calendar year vs. rolling
  year from signup)
- Several pages load slowly because of Wix widgets, including one that displays
  the weather
- The equipment inventory is published as images, so it isn't searchable or
  indexable
