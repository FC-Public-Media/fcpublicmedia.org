# Site

fcpublicmedia.org is a static Jekyll site built from `site/` and uploaded to one Cloudflare Pages project,
`fcpm-new`, at `fcpublicmedia.org` ([Deploy](#deploy)); the photocopy of the old Wix site is at `wix.fcpublicmedia.org`. Its five transactions (tickets, dues, donations,
booking, submissions) are hand-offs to other services ([payments.md](payments.md#transactions)).

## Layout

`site/` is what the public gets, and it is the build root. The repository root is everything else.

| `site/` | |
|---|---|
| `_config.yml`, `Gemfile`, `.ruby-version` | build config, read relative to the build root |
| `*.md`, `index.html`, `404.html` | one file per page; the filename is the URL |
| `_layouts/` | `default`, `page`, `pass` (`/check-in/`, `/lights/`) |
| `_includes/` | `head`, `header`, `footer`, `show-card` and smaller parts |
| `you/` | the member's own pages. `/check-in/`, `/authorize/` and `/lights/` keep their old URLs by `permalink` (a printed QR, an issued claim link, the kiosk camera); the rest are `/you/:name/` |
| `_data/`, `assets/` | [data files](#data-files); `css/site.css` (the whole design), `js/`, `fonts/`, `img/` |
| `member-sites/` | built member sites, by `bin/build-sites.py --publish` ([members.md](members.md)); `bin/deploy-site` runs it |
| `bin/`, `tests/` | tooling, syncs and Python tests; Playwright tests. Both excluded from the build |
| `_redirects`, `_headers`, `robots.txt`, `sitemap.xml` | generated for hosts |

| Root | |
|---|---|
| `AGENTS.md`, `README.md`, `docs/` | standing orders, front page, everything written down |
| `sites.yml`, `site-template/`, `member-site-core/` | the site list and member sites ([members.md](members.md#sitesyml)) |
| `bin/` | `build-sites.py`, `build-kiosk.py`, `make-wallpaper.py` and their tests |
| `brand/` | the brand; the studio screens are the kiosk's ([kiosk.md](kiosk.md)) |
| `machines/`, `troves/`, `attendant/` | the station ([station.md](station.md)) |
| `advocate.yml`, `tell.yml`, `atlas.yml`, `keys/`, `_data/`, `.<name>-engine/` | seats, directory, submodules |

- `site/_data` reads only what is inside `site/`; Jekyll's `data_dir` cannot leave the source.
- The root reaches down: syncs write `site/_data/` and `bin/build-kiosk.py` reads it. `site/` never reaches up.
- The site-worker is its own repository ([FC-Public-Media/site-worker](https://github.com/FC-Public-Media/site-worker));
  its `src/claims.js` is a copy of `site/assets/js/claims.js`: change both.
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
Add it to `site/_data/nav.yml` to put it in a menu.

There are no collections. `_podcasts/` and `_shows/` left `site/` (2026-10-25): everything the site
lists has to come from Cablecast first, and a purposeful listing is for the outer repository to
build into `site/`. So `site.podcasts` and `site.shows` are nil — a `sort` or `concat` on either is
a build error, which is how `sitemap.xml` and `watch.md` broke when they went.

- `page`, the default layout, prints no `<h1>` and no lede; pages start at `<h2>`.
- `sitemap: false` keeps a page out of `/sitemap.xml`, which lists every URL ending in `/`.
- Liquid: `""` is truthy, so compare with `!= ""`; a line starting `2004.` becomes a list;
  `include` takes plain variables only; `contains` cannot be negated.

## Data files

| `site/_data/` | Holds |
|---|---|
| `org.yml` | name, founding year, emails, phone, address, `legal`, `mission`, `hero_image`, `social` |
| `nav.yml` | `primary` (header), `cta` (Donate); `label` with `items` makes a group. `elsewhere` is no menu: it names pages nothing links, so the header can still say which one you are on |
| `featured.yml` | homepage cards: `kind`, `title`, `blurb`, `when`, `url`, `cta`, `starts`, `ends`; first is largest |
| `community.yml` | `/meet/` `events` and `channels` (`primary: true` leads) |
| `governance.yml` | board `meetings`, `minutes`, `documents` |
| `board.yml` | roster: `name`, `role`, optional `office_hours`, `bio`, `photo` |
| `facilities.yml` | bookable spaces; Video and Podcast Studio are coupled, so booking one blocks both |
| `redirects.yml`, `wifi.yml`, `settings.yml` | [redirects](#redirects-and-headers); the guest network, never its password; [members.md](members.md) |

Other data files name their doc in their first line.

- Every time carries a UTC offset, `"2026-09-15T18:30:00-06:00"`, or a browser reads it as local.
- Entries with no `url` (channels, socials, documents) are skipped.
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
| `assets/js/archive-filter.js` | filter and sort on the archive, now part of `/watch/` (the menu has no script: it stays on the bar at every width) |
| `assets/js/onair.js` | "On now" and "Next at" from Cablecast's API, on pages with `data-onair`; removed on failure |
| `assets/js/lights.js` | `/lights/`: the lights reply code for the kiosk camera ([kiosk.md](kiosk.md)) |
| `assets/js/qr-*.mjs` | vendored from anecdote.channel, unchanged; `machines/kiosk/door.py` serves them, so never move them |
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
npm run test:live                                # against https://fcpublicmedia.org
```

- `playwright.config.js` serves `../_site` on `localhost:4567` (WebAuthn rejects an IP), desktop and
  Pixel 5. `BASE_URL` targets a deployed site; redirects, 404s and trailing slashes exist only there.
- Every page in `pages.js` must load with a title, at most one `<h1>`, no console errors, no failed
  same-origin request, resolving internal links, labelled links and no sideways scroll.
- `@external` (`embeds.spec.js`) renders Cablecast pages: its viewer answers 200 for missing shows.
- `.github/workflows/smoke.yml`, on every push and pull request: build, Python tests, the site-worker's
  `npm test`, Playwright. `@external` runs only on the Tuesday schedule or by hand, allowed to fail.

## Deploy

Deploying is one thing: `bin/deploy-site`. In a throwaway copy of HEAD it refreshes the site's data
([the sync jobs](programming.md#sync-jobs) and member sites), runs `jekyll build` in `site/` and uploads `_site` to
the Cloudflare Pages project `fcpm-new` on FCPM's org Cloudflare account, as its production (branch
`main`). That project is a static bucket: direct upload, no git connection, no build on Cloudflare's
side, no Functions. It serves `fcpm-new.pages.dev`, `fcpublicmedia.org` and `new.fcpublicmedia.org`.

- It runs where the keychain is (digitization), with the `cloudflare` group (`machines/digitization/keys.yml`).
  `bin/deploy-site --build` refreshes, builds and checks without uploading, and keeps the copy.
- The refreshed data goes up with the build, not into git: the committed `cablecast.json`,
  `airings.json` and `nonprofits.json` are what the LAN build and the tests
  use, and they age until someone commits a refresh. A refresh that fails keeps the committed copy.
- A push to GitHub deploys nothing. No GitHub Actions workflow deploys the site, and no other host
  serves it.
- Pages reads `_redirects` and `_headers` from `_site`. Nothing in `site/` names the host or runs code.
  The one piece of running code is the [site-worker](https://github.com/FC-Public-Media/site-worker),
  deployed on its own; the site knows it only by `site/_data/site_worker.yml` `url`.
- The LAN has the site from `machines/static` (`site-build`, served by nginx), through a cloud outage.
- `deliver:` in `sites.yml` is `source` (this build) or `intermediate`
  ([station.md](station.md#intermediates)); `python3 bin/build-sites.py --deploy-root
  fcpublicmedia.org` prints the root directory.

## Domain and DNS

Network Solutions is the registrar (expires 2027-06-19). `clientTransferProhibited` blocks moving the
domain to another registrar, not changing its nameservers. Since 2026-10-24 the nameservers are
Cloudflare's (`ganz` and `tiffany.ns.cloudflare.com`), so the zone lives in FCPM's org Cloudflare account
beside the Pages projects and the site-worker. Wix's old nameservers still answer from a stale copy;
nothing asks them.

| Name | Serves |
|---|---|
| `@` | this site (Pages `fcpm-new`), its canonical address (`url` in `site/_config.yml`) |
| `www` | a 301 to the same path on `@`, by a Single Redirect rule in the zone |
| `wix` | the Wix photocopy (Pages `fcpm-wix`), for good |
| `new` | this site too, for codes printed before the cutover; later the beta, beside a preview worker |
| `cloud` | the site-worker, once `bin/provision.mjs` attaches it (no record yet) |

The web names are proxied. Mail and Microsoft 365 came across whole, checked 2026-10-28:

| Name | Type | Value |
|---|---|---|
| `@` | MX 10; TXT | `fcpublicmedia-org.mail.protection.outlook.com`; `v=spf1 include:spf.protection.outlook.com -all`, `ms15993575` |
| `autodiscover`, `lyncdiscover`, `sip` | CNAME | `autodiscover.outlook.com`, `webdir.online.lync.com`, `sipdir.online.lync.com` |
| `enterpriseregistration`, `enterpriseenrollment` | CNAME | `enterpriseregistration.windows.net`, `enterpriseenrollment.manage.microsoft.com` |
| `_sipfederationtls._tcp`, `_sip._tls` | SRV | `100 1 5061 sipfed.online.lync.com`, `100 1 443 sipdir.online.lync.com` |

No wildcard, CAA, `_dmarc` or DKIM. The SPF ends in `-all`: mail from anywhere else is refused.

### Redirects

Two layers, each doing what the other can't. The zone's Single Redirect rule sends `www` to `@`: it sees
hostnames and runs before Pages. Old paths (Wix's, and ours that moved) are `_redirects`, built from
`site/_data/redirects.yml`: paths only, matched exactly, so `/membership` and `/membership/` are two
entries. A Pages custom domain that isn't Active answers Cloudflare's 522; a hostname is only safe to
point at a project once the project lists it as Active.

### The cutover (2026-10-28)

1. Done: `@` serves `fcpm-new`, `www` redirects to it, `wix` keeps the photocopy.
2. Deploy this site with `site/_data/checkin.yml` naming `@` (the QR, the poster and the kiosk follow).
   A code printed for `new` keeps working.
3. `keys run cloudflare -- node bin/provision.mjs` in the site-worker checkout attaches `cloud`; then
   `site/_data/site_worker.yml` `url` becomes `https://cloud.fcpublicmedia.org` and the site deploys again.
4. Switch off the Wix forms; drain the site-worker; retire the `instructor` tank once its drain is empty.

## Redirects and headers

- `site/_data/redirects.yml` generates `_redirects`, all 301. Add entries; never remove one. A
  `from` is either a live Wix URL or one of ours that moved.
- `_config.yml` lists `_redirects` and `_headers` under `include:` despite the underscore.
- `_headers`: `nosniff` and `strict-origin-when-cross-origin`; `/assets/*` caches for an hour. No HSTS.
- The unused Wix store (`/product-page/i-m-a-product*`, `/category/all-products`) is left to 404.
- `site/bin/redirect-report.py` writes `docs/REDIRECTS.md` and exits 1 on any Wix URL with no
  redirect, page or decision.

## Never published

- Internal documents live at the root and in `docs/`, outside the build. Never put one in `site/`:
  a `.md` with no front matter is copied verbatim to a public URL.
- `_config.yml` excludes exactly `bin`, `tests` and `README.md`.
- `site/bin/test_site_runs_no_code.py` fails if `site/` tracks host config or server code (`wrangler.*`,
  `staticwebapp.config.json`, `_worker.js`, `functions/`).
- `site/bin/test_nothing_internal_is_published.py` fails if `_site` holds `bin/`, `tests/`, a `.py`,
  `.spec.js`, `playwright.config.js`, `package-lock.json`, `wrangler.jsonc`, `Gemfile`, `_config.yml`
  or any `.md`.
- `site/bin/test_no_secrets.py` fails on a Stripe secret shape in `_site` or git, a non-`pk_`
  `publishable_key`, a Wi-Fi payload with a password, or a tracked or built `wifi-qr.svg`.
- The Wi-Fi QR holds the guest password in readable form: made locally, gitignored, printed for
  the lobby. Delete it and rebuild before publishing `_site` by hand.
- [review-notes.md](review-notes.md) holds unratified board feedback and stays in `docs/`.
