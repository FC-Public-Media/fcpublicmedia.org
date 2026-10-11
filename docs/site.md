# Site

fcpublicmedia.org is a static Jekyll site built from `site/`, served at `new.fcpublicmedia.org`
while the apex still serves the old Wix site. Its five transactions (tickets, dues, donations,
booking, submissions) are hand-offs in `site/_data/providers.yml` ([payments.md](payments.md#transactions)).

## Layout

`site/` is what the public gets, and it is the build root. The repository root is everything else.

| `site/` | |
|---|---|
| `_config.yml`, `Gemfile`, `.ruby-version`, `wrangler.jsonc` | build config, read relative to the build root |
| `*.md`, `index.html`, `404.html` | one file per page; the filename is the URL |
| `_layouts/` | `default`, `page`, `pass` (`/check-in/`, `/lights/`), `podcast`, `show` |
| `_includes/` | `head`, `header`, `footer`, `transaction`, `show-card`, `featured` and smaller parts |
| `_podcasts/`, `_shows/` | collections at `/podcasts/:name/` and `/watch/:name/` |
| `_data/`, `assets/` | [data files](#data-files); `css/site.css` (the whole design), `js/`, `fonts/`, `img/` |
| `member-sites/` | built member sites, committed by the publish workflow ([members.md](members.md)) |
| `bin/`, `tests/` | tooling, syncs and Python tests; Playwright tests. Both excluded from the build |
| `_redirects`, `_headers`, `staticwebapp.config.json`, `robots.txt`, `sitemap.xml` | generated for hosts |

| Root | |
|---|---|
| `AGENTS.md`, `README.md`, `docs/` | standing orders, front page, everything written down |
| `sites.yml`, `site-template/`, `member-site-core/` | the site list and member sites ([members.md](members.md#sitesyml)) |
| `worker/` | the broker, its own Worker ([worker/README.md](../worker/README.md)) |
| `bin/` | `build-sites.py`, `build-kiosk.py`, `make-wallpaper.py` and their tests |
| `kiosk/`, `instruments/`, `brand/` | studio screens ([kiosk.md](kiosk.md)) and the brand |
| `machines/`, `troves/`, `crews/`, `attendant/` | the station ([station.md](station.md)) |
| `advocate.yml`, `tell.yml`, `atlas.yml`, `keys/`, `_data/`, `.<name>-engine/` | seats, directory, submodules |

- `site/_data` reads only what is inside `site/`; Jekyll's `data_dir` cannot leave the source.
- The root reaches down: syncs write `site/_data/`, `bin/build-kiosk.py` reads it, and
  `worker/src/index.js` imports `site/assets/js/claims.js`. `site/` never reaches up.
- No symlinks across the boundary: `jekyll build --safe` silently reads them as empty.

## Build and run

```
cd site
bundle install
bundle exec jekyll serve      # http://localhost:4000, rebuilds on save
```

Always from `site/`: from the root Jekyll finds no config and builds the wrong tree. No npm, no
CSS preprocessor, no theme gem, no plugins; try a `_data` file and a Liquid loop first.

- `site/.ruby-version` (3.2.2) is the only Ruby pin; Cloudflare and `ruby/setup-ruby` read it. The
  `Gemfile` floor `ruby ">= 3.2"` makes the macOS system Ruby 2.6 fail at once.
- No `.tool-versions` ([AGENTS.md](../AGENTS.md)): Cloudflare's builder detects it and can fail with
  `error occurred while installing tools or dependencies`.
- asdf reads `.ruby-version` only with `legacy_version_file = yes` in `~/.asdfrc`.
- A Ruby compile failing at `checking whether LDFLAGS is valid... no` means a profile exports
  `LDFLAGS`/`CPPFLAGS` for a removed Homebrew package. Set them per command.
- `Gemfile.lock` is not committed; one resolved on another platform breaks hosted installs.
- `site.css` and the scripts load with `?v=<build time>`: a deploy busts caches, and every HTML
  file changes on every build.

## Pages

Create `site/something.md` with front matter (`title:` at least); it is live at `/something/`.
Add it to `site/_data/nav.yml` to put it in a menu. A podcast: copy a file in `site/_podcasts/`.

- `page`, the default layout, prints no `<h1>` and no lede; pages start at `<h2>`.
- `sitemap: false` keeps a page out of `/sitemap.xml`, which lists every URL ending in `/`.
- Liquid: `""` is truthy, so compare with `!= ""`; a line starting `2004.` becomes a list;
  `include` takes plain variables only; `contains` cannot be negated.

## Data files

| `site/_data/` | Holds |
|---|---|
| `org.yml` | name, founding year, emails, phone, address, `legal`, `mission`, `hero_image`, `social` |
| `nav.yml` | `primary` (header), `cta` (Donate), `footer`; `label` with `items` makes a group |
| `featured.yml` | homepage cards: `kind`, `title`, `blurb`, `when`, `url`, `cta`, `starts`, `ends`; first is largest |
| `community.yml` | `/meet/` `events` and `channels` (`primary: true` leads) |
| `governance.yml` | board `meetings`, `minutes`, `documents` |
| `board.yml` | roster: `name`, `role`, optional `office_hours`, `bio`, `photo` |
| `facilities.yml` | bookable spaces; Video and Podcast Studio are coupled, so booking one blocks both |
| `redirects.yml`, `wifi.yml`, `settings.yml` | [redirects](#redirects-and-headers); the guest network, never its password; [members.md](members.md) |

Other data files name their doc in their first line.

- Every time carries a UTC offset, `"2026-09-15T18:30:00-06:00"`, or a browser reads it as local.
- Entries with no `url` (channels, socials, documents) are skipped.
- `/meet/` "What's on" merges `classes.yml` sessions, `governance.yml` meetings and
  `community.yml` events (`kind` is a free label, default "Event"). Past items drop out.
- `featured.yml` items drop off only when the site rebuilds.
- `org.mission` and the `facilities.yml` summaries are the board's wording: never rewrite them.

## Design tokens

`site/assets/css/site.css`; `site/bin/test_tokens.py` and `site/tests/contrast.spec.js` check contrast.

- `--ink`, `--ink-soft`, `--slate`, `--paper`, `--paper-alt`, `--rule`, `--signal` (yellow plate),
  `--signal-ink`, `--record`, `--record-ink`, `--masthead`, `--masthead-ink`, `--masthead-soft`, `--accent`.
- Yellow is a surface, never text on paper (1.4:1; 11.7:1 on ink). `--record` (red) is a fill;
  red text uses `--record-ink`. The masthead is dark in both schemes.
- Light is the default. `assets/js/theme.js` runs the footer checkbox (localStorage `theme`: `light`
  or `system`) and sets `data-theme="dark"` on `<html>`; `_includes/head.html` applies it before paint.
- Self-hosted Archivo (`--font-body`) and Source Serif 4 (`--font-display`); the brand tilt is -8deg.

## Scripts

| | |
|---|---|
| `assets/js/nav.js`, `archive-filter.js` | mobile menu; filter and sort on `/watch/archive/` |
| `assets/js/onair.js` | "On now" and "Next at" from Cablecast's API, on pages with `data-onair`; removed on failure |
| `assets/js/lights.js` | `/lights/`: the lights reply code for the kiosk camera ([kiosk.md](kiosk.md)) |
| `assets/js/qr-*.mjs` | vendored from anecdote.channel, unchanged; `machines/kiosk-1/door.py` serves them, so never move them |
| `bin/make-qr.py` | writes the committed `check-in-qr.svg` from `_data/checkin.yml`; needs `pip install qrcode` |
| `bin/make-wifi-qr.py` | writes the uncommitted `wifi-qr.svg`; password from `FCPM_WIFI_PASSWORD` or a prompt |
| `bin/redirect-report.py` | checks the live Wix sitemaps against `redirects.yml` and `_site` |
| `bin/catalog-report.py` | Cablecast records that look wrong; `catalog-report.yml` keeps one issue, monthly on the 12th |
| `bin/check-template.py` | builds `site-template/` on `member-site-core/` and reads its feed back |

## Tests

```
cd site && bundle exec jekyll build
cd tests && npm ci && npx playwright install chromium
npx playwright test --grep-invert @external      # what CI gates on
npx playwright test --grep @external             # third-party health
npm run test:live                                # against https://www.fcpublicmedia.org
```

- `playwright.config.js` serves `../_site` on `localhost:4567` (WebAuthn rejects an IP), desktop and
  Pixel 5. `BASE_URL` targets a deployed site; redirects, 404s and trailing slashes exist only there.
- Every page in `pages.js` must load with a title, at most one `<h1>`, no console errors, no failed
  same-origin request, resolving internal links, labelled links and no sideways scroll.
- `@external` (`embeds.spec.js`) renders Cablecast pages: its viewer answers 200 for missing shows.
- `.github/workflows/smoke.yml`, on every push and pull request: build, Python tests, the broker's
  `npm test`, Playwright. `@external` runs only on the Tuesday schedule or by hand, allowed to fail.

## Deploy

Cloudflare's git build is the only thing that publishes the site:

| Setting | Value |
|---|---|
| Build command | `bundle exec jekyll build` |
| Deploy command | `npx wrangler deploy` |
| Non-production branch deploy command | `npx wrangler versions upload` (per-branch preview URL) |
| Path / root directory | `site` |
| Build output directory | `_site` (relative to the root directory) |
| Build watch paths | `site` |

- At any other root directory the build finds no config and publishes a wrong site while
  reporting success. `worker/` holds the broker's Worker config, not the site's.
- `site/wrangler.jsonc` is static assets only. Without it `wrangler deploy` auto-configures and
  fails. Never `wrangler pages deploy`: it creates a second site.
- Member-site publishing commits into `site/member-sites/`, so it triggers a deploy.
- Do not add `submodules: true` to the checkout in `deploy.yml`; nothing in `_site` needs one.
- The fallback is this table on FCPM's own Cloudflare account; it needs no machine of ours.
- `deliver:` in `sites.yml` is `source` (this build) or `intermediate`
  ([station.md](station.md#intermediates)); `python3 bin/build-sites.py --deploy-root
  www.fcpublicmedia.org` prints the root directory. Change the dashboard field in the same act.
- The broker deploys from `.github/workflows/broker.yml` with `CLOUDFLARE_API_TOKEN`.

| Build failure | Cause |
|---|---|
| `Could not locate Gemfile`; "Detected the following tools" names Ruby | root directory is not `site` |
| the same, with that line empty | an empty checkout; check the GitHub App's access |
| repository reported as damaged | delete and recreate the Cloudflare project |
| `error occurred while installing tools or dependencies` | a `.tool-versions` file |

A failed build leaves the last good deployment serving.

**Azure.** `.github/workflows/deploy.yml` builds every push and pull request to `main`; it deploys,
with PR previews, only if `AZURE_STATIC_WEB_APPS_API_TOKEN` is set, and it is not.

## Domain and DNS

Network Solutions is the registrar (expires 2027-06-19, `clientTransferProhibited`); nameservers
change there, with no transfer. Wix's `ns4.wixdns.net` and `ns5.wixdns.net` serve the zone:

| Name | Type | Value |
|---|---|---|
| `@` | A | `185.230.63.171`, `185.230.63.107`, `185.230.63.186` |
| `www`; `new` | CNAME | `cdn3.wixdns.net`; `fcpm.autumn-e2c.workers.dev` (a personal account, not FCPM's) |
| `@` | MX 10; TXT | `fcpublicmedia-org.mail.protection.outlook.com`; `v=spf1 include:spf.protection.outlook.com -all`, `ms15993575` |
| `autodiscover`, `lyncdiscover`, `sip` | CNAME | `autodiscover.outlook.com`, `webdir.online.lync.com`, `sipdir.online.lync.com` |
| `enterpriseregistration`, `enterpriseenrollment` | CNAME | `enterpriseregistration.windows.net`, `enterpriseenrollment.manage.microsoft.com` |
| `_sipfederationtls._tcp`, `_sip._tls` | SRV | `100 1 5061 sipfed.online.lync.com`, `100 1 443 sipdir.online.lync.com` |

No wildcard, CAA, `_dmarc` or DKIM. A zone moved to Cloudflare must carry every row, re-read
first: mail is on Microsoft 365 and the SPF ends in `-all`. A and CNAME rows stay DNS-only, since
proxying Wix takes the apex down. A Workers Custom Domain needs zone and Worker in one account.

## Redirects and headers

- `site/_data/redirects.yml` generates `_redirects` (Cloudflare) and the routes of
  `staticwebapp.config.json` (Azure), all 301. Add entries; never remove one.
- `_config.yml` lists `_redirects` and `_headers` under `include:` despite the underscore.
- `_headers`: `nosniff` and `strict-origin-when-cross-origin`; `/assets/*` caches for an hour.
  Azure's config also sends HSTS.
- The unused Wix store (`/product-page/i-m-a-product*`, `/category/all-products`) is left to 404.
- `site/bin/redirect-report.py` writes `docs/REDIRECTS.md` and exits 1 on any Wix URL with no
  redirect, page or decision.

## Never published

- Internal documents live at the root and in `docs/`, outside the build. Never put one in `site/`:
  a `.md` with no front matter is copied verbatim to a public URL.
- `_config.yml` excludes exactly `bin`, `tests`, `wrangler.jsonc` and `README.md`.
- `site/bin/test_nothing_internal_is_published.py` fails if `_site` holds `bin/`, `tests/`, a `.py`,
  `.spec.js`, `playwright.config.js`, `package-lock.json`, `wrangler.jsonc`, `Gemfile`, `_config.yml`
  or any `.md`.
- `site/bin/test_no_secrets.py` fails on a Stripe secret shape in `_site` or git, a non-`pk_`
  `publishable_key`, a Wi-Fi payload with a password, or a tracked or built `wifi-qr.svg`.
- The Wi-Fi QR holds the guest password in readable form: made locally, gitignored, printed for
  the lobby. Delete it and rebuild before any local `wrangler deploy`.
- [review-notes.md](review-notes.md) holds unratified board feedback and stays in `docs/`.
