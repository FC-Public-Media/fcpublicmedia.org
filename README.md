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

## Check-in

`/check-in/` is a QR destination. Someone scans the poster, taps once, and the
visit is recorded — in their own browser's storage, on their own device.

- The device identifier is a random UUID made on first visit. Not derived from
  the device or the person, never transmitted, deleted by "Forget this device".
- History is capped, exportable to a JSON file, and re-importable — importing
  merges rather than replaces, so restoring a backup never drops newer visits.
- A test asserts that checking in makes **no network request**. If a future
  change starts posting somewhere, the suite fails.

Print the poster at `/check-in/poster/`. The QR is a committed SVG; regenerate
it only if the URL changes:

```
pip install qrcode
python3 script/make-qr.py
```

The generated code was decoded back to `https://www.fcpublicmedia.org/check-in/`
to confirm it is correct — a printed poster with a wrong URL is worse than no
poster.

### This does not replace the paper log

Two things follow from there being no server, and neither is a bug in the page:

**FCPM receives nothing.** A log on a visitor's phone cannot be counted,
reported to the City, or put in a grant application. The export button lets a
visitor hand their history over, but that is a favour, not a reporting system.
The stated goal was simplifying check-in *reporting* — device-local storage
serves the visitor, not the organization.

**Browsers delete this.** Safari removes script-writable storage after about
seven days without a visit unless the site is on the Home Screen, and clearing
browsing data clears it. For a log people touch monthly, losing it is the
normal outcome, not an edge case. The page says so plainly rather than
implying a permanence it cannot deliver.

So run it alongside the paper log until check-ins have somewhere to go.

### What "somewhere to go" would take

On Cloudflare, a Worker with a D1 or KV binding — roughly thirty lines, and the
free tier covers this volume many times over. The page would POST the same
record it stores locally, and the device-local history keeps working as the
visitor's own copy.

That is a small piece of work. It is listed here rather than built because it
turns a static site into one holding a record of who was in the building and
when, and that is a decision for the board: retention period, who can read it,
what happens on a subpoena, and whether it needs a privacy notice.

### Identity

`_data/checkin.yml` sets `identity.mode`:

- **`none`** (current) — check-ins are recorded without an email, and the page
  says so.
- **`access`** — put Cloudflare Access in front of `/check-in/` and the page
  reads the verified identity from `/cdn-cgi/access/get-identity`.

`access` is what matches the original ask: the visitor picks their own provider
— Google, Microsoft, GitHub, or a one-time emailed PIN — Cloudflare verifies
it, and the page gets a real email address without this site holding a secret
or running any OAuth code. Changing provider later is a dashboard setting, not
a code change, and someone can use a different email next time without anything
breaking.

It is off because enabling it is a Zero Trust dashboard change; switching the
config before the route is actually protected would show everyone an error.
When the route is not behind Access the identity request 404s and the page
falls back to an anonymous check-in, so both states are safe.

Note that Access authenticates the visitor to *Cloudflare*, and the page then
reads that identity client-side. It does not by itself give FCPM a server-side
record — that still needs the Worker above.

## Tests

Browser smoke tests, run with Playwright against a real Chromium in both a
desktop and a phone viewport.

```
bundle exec jekyll build
cd tests && npm ci && npx playwright install chromium
npx playwright test
```

They exist because the failures that matter here are the ones you cannot see:
a JavaScript error on a phone, an embed that silently does not mount, a link
that looks fine and 404s. Each page is checked for:

- HTTP status, a title, exactly one `<h1>`
- No uncaught JavaScript errors and no console errors
- No failed same-origin requests
- Every internal link resolving — this is not a crawl of the whole site, it is
  every link on every listed page, fetched
- No link with an invisible label (blank text, no image, no `aria-label`)
- No horizontal scrolling, which is the classic phone bug

Plus the mobile menu opening and closing, and the archive filter actually
filtering.

They caught two real bugs the first time they ran: all 38 category links on
`/watch/` pointed at `/watch-archive-news`-style paths that 404ed, because
`slugify` had been chained after `append` and slugified the path along with
the name; and the archive scrolled sideways on a phone because Cablecast
titles are often one long underscore-joined token with nowhere to break.

### Tests marked @external

`embeds.spec.js` checks the Cablecast player, show links, thumbnails, and
outbound links. These need network and depend on someone else's servers, so
they are excluded from the pull request run:

```
npx playwright test --grep-invert @external   # what CI runs
npx playwright test --grep @external          # third-party health
```

The external ones run on a weekly schedule with `continue-on-error`, because
a suite that goes red when a third party has a bad afternoon is a suite people
stop reading.

**Why these are browser tests rather than link checks:** Cablecast's viewer is
a single-page app. `/internetchannel/show/999999` returns HTTP 200 with a full
HTML shell for a show that does not exist. A status check proves nothing; you
have to render the page and look for the player.

### Testing the deployed site

```
cd tests && BASE_URL=https://www.fcpublicmedia.org npx playwright test
```

Worth doing after a deploy, because redirects, custom 404s, and trailing-slash
handling are host behavior and do not exist in the local preview server.

## The Cablecast catalog

The station's Cablecast instance has a public API that needs no key and sends
`Access-Control-Allow-Origin: *`. It holds **1,486 programs** going back to
2011, 740 of them watchable online, 1,462 with thumbnails, across 36
categories and 80 producers. That is the archive, and it was already there.

`script/sync-cablecast.py` pulls it into `_data/cablecast.json` (standard
library only, nothing to install):

```
python3 script/sync-cablecast.py
```

`.github/workflows/sync-cablecast.yml` runs it weekly and commits the result
if anything changed.

Snapshotting at build time rather than fetching in the browser means the
archive is real HTML — indexable, findable with ⌘F, and still there if
Cablecast is down. The one thing that *is* live is the "on now" strip
(`assets/js/onair.js`), which reads the schedule directly because a weekly
snapshot cannot tell you what is playing right now. It removes itself if the
request fails.

The script's one judgement call is `LOCAL_PREFIXES` — which categories count
as locally produced. This matters: the raw "most recent" list is dominated by
Free Speech TV and Paltrocast, which buries the work Fort Collins people
actually made, so the site features local production separately.

## Featuring things on the homepage

`_data/featured.yml` is the whole content management system. It is a list.
Add an entry to put something on the front page; it removes itself when `ends`
passes. Four archetypes — `class`, `event`, `show`, `notice` — which is what
the actual pattern of announcements looks like.

Expiry is evaluated at build time, which is why the weekly workflow rebuilds
even when nothing changed. Otherwise a class that happened on Tuesday would
still be advertised on Friday.

If nothing is currently in its date window, the section renders nothing and
the page closes up around it. An empty `featured.yml` is a valid state.

## Booking on a subdomain

Booking is expected to end up hosted elsewhere — likely Microsoft-built and
Microsoft-hosted, on something like `book.fcpublicmedia.org`. The concern is
that it should feel like part of this organization, not like scheduling a
video call with a stranger.

Three things carry most of that, in order of effect per unit of work:

1. **Same domain, not a redirect to a vendor URL.** A subdomain of
   `fcpublicmedia.org` reads as first-party; `outlook.office365.com/...` does
   not. This is most of the perceived difference and it costs one DNS record.
2. **Arrive and leave inside the site.** Link out from `/reservations/` with
   context already given — who can book, what the spaces are, what happens
   after — so the external page only has to collect a time. Send people back
   to a page here on completion.
3. **Carry the tokens across.** The palette, type scale, and spacing all live
   in the `:root` block of `assets/css/site.css`. Where the booking host
   allows custom CSS or a logo and color, copy those values rather than
   re-picking them by eye.

What not to spend effort on: recreating this site's header on the booking
host. Partial imitation reads worse than an honest, clean handoff.

Set `booking.subdomain` in `_data/providers.yml` once the host is chosen.

## Forms

A static site can't accept a form post. Two options, both fine:

- **A function in `/api`** that relays the submission to `info@fcpublicmedia.org`
  through Microsoft Graph. No third party, no per-submission cost, and the mail
  is already in the tenant.
- **A hosted form service** for the ones with real complexity — the program
  submission form has ranked scheduling preferences, a file upload, and a legal
  agreement, and is not worth hand-building.

## Deploying to Cloudflare

This is the fastest path to a real URL on a real domain, and it is what the
demo runs on.

Cloudflare now creates new projects as **Workers** rather than Pages, and the
two behave differently at deploy time. This repository is set up for the
Workers flow, which is what you get by default today.

Point the Cloudflare GitHub app at this repository and set:

| Setting | Value |
|---|---|
| Build command | `bundle exec jekyll build` |
| Deploy command | `npx wrangler deploy` |
| Build output directory | `_site` |
| Root directory | `/` (leave it alone) |

Everything else is in `wrangler.jsonc`, which is committed.

### Why wrangler.jsonc has to be committed

`wrangler deploy` looks for a config file. If it does not find one it runs
auto-configuration: it inspects the repository, decides what kind of project
this is, and **re-runs the build command through npx**. For a Ruby project
that produces `npx bundle exec jekyll build`, which fails with:

```
npm error could not determine executable to run
```

The Jekyll build has already succeeded at that point. The failure is wrangler
guessing, not the build. Committing `wrangler.jsonc` skips the guess.

### Notes

- **`bundle exec` is deliberate.** Cloudflare finds the `Gemfile` and runs
  `bundle install` on its own, so plain `jekyll build` also works. Prefixing
  with `bundle exec` guarantees the bundled Jekyll rather than whatever
  happens to be on `PATH`.
- **`_site` appears twice** — in the dashboard and in `wrangler.jsonc` under
  `assets.directory`. Both need it. It is Jekyll's default and is not
  overridden in `_config.yml`.
- **`.ruby-version` pins Ruby 3.2.2**, the default in Cloudflare's build
  image, and CI reads the same file. Without it the builder can fall back to
  a Ruby too old for Jekyll 4. Do not delete it.
- **Leave the root directory as `/`.** The `api/` folder is Azure Functions
  source, not a second site, and `_config.yml` excludes it from the output.
  There is one buildable component here, at the root.
- **`Gemfile.lock` is intentionally not committed.** A lock file resolved on a
  different platform is a common cause of `bundle install` failures on hosted
  builders. Jekyll is the only direct dependency.

### If you are on classic Pages instead

Same build command and output directory, no deploy command, and
`wrangler.jsonc` is ignored. Both flows serve `_redirects` and `_headers`
from the output, so the redirect handling below applies either way.

### Redirects and headers

Cloudflare Pages reads `_redirects` and `_headers` from the root of the
published output. Azure reads `staticwebapp.config.json`. **All three are
generated from `_data/redirects.yml`** at build time, so the hosts cannot
drift apart — add a redirect once and both get it.

The 20 legacy Wix URLs therefore keep working on either host, which matters:
those are the links currently indexed by Google and sitting in other people's
bookmarks.

## Deploying to Azure Static Web Apps

`.github/workflows/deploy.yml` builds with Jekyll and deploys to Azure Static
Web Apps on every push to `main`. Pull requests get their own preview URL,
which means the board can look at a change before it goes live — something Wix
has never offered.

One secret is required: `AZURE_STATIC_WEB_APPS_API_TOKEN`, from the Static Web
App resource in the Azure portal.

The free tier covers the static hosting, the managed functions, the auth, and a
custom domain with a certificate.

### Cloudflare or Azure?

Both, for now, and that is not indecision.

**Cloudflare Pages** is the demo host: it attaches to the domain in minutes
and needs no Azure setup. It serves static files, which is all this site
currently is.

**Azure Static Web Apps** is where this goes if members-only pages are
wanted, because it bundles static hosting, Entra ID sign-in, and a small
serverless API into one free resource inside the Microsoft 365 tenant the
organization already has. Cloudflare Pages can do auth and functions too, but
not with Entra sitting right there.

Nothing about the site favours one over the other — that is the point of it
being static files. `_site/` deploys anywhere, both hosts build from the same
command, and the redirect list feeds both. Switching later is a DNS change,
not a rewrite.

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
