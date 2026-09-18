<!--
Split out of the root README on 2026-09-17, unchanged apart from paths.

The README was 68 KB and had become the only place a lot of this was written
down, which made it both the first thing a visitor saw and the last place
anybody wanted to edit. Nothing here was rewritten in the move; if something
reads as out of date, it was out of date before it moved, and saying so is
welcome.
-->

# Running it

How to get the site building on your machine, and what the tree contains.

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
cd site
bundle install
bundle exec jekyll serve
```

**From `site/`, not the repository root.** That directory is the build root —
Cloudflare's own "Path / root directory" setting says `site` — and everything
the build reads lives in it: `_config.yml`, `Gemfile`, `.ruby-version`,
`wrangler.jsonc`. Run from the root and Jekyll finds no config, takes the root
as its source, and produces nonsense. See [`deploying.md`](deploying.md).

Then open <http://localhost:4000>. Edits rebuild automatically. There is no npm,
no bundler, no CSS preprocessor, and no plugins.

### Ruby

The version is **3.2.2**, and `site/.ruby-version` is the only file that says so.

It used to be written down twice — `.ruby-version` for CI, `.tool-versions` for
asdf — with a CI step whose whole job was checking the two agreed. That is gone
as of 2026-09-17, and `.tool-versions` with it. Two reasons:

- **Cloudflare's build image reads `.ruby-version`** (or a `RUBY_VERSION` build
  variable) and nothing else. It never read `.tool-versions`, so that file was
  never protecting the build that publishes the site.
- **Its presence is a known hazard on Cloudflare.** The builder detects
  `.tool-versions` undocumentedly and can fail the whole build with
  `error occurred while installing tools or dependencies`, with no way to turn
  the behaviour off. See `deploying.md`.

With [asdf](https://asdf-vm.com/) installed, asdf does *not* read
`.ruby-version` by default — it needs one line, once, per machine:

```
echo 'legacy_version_file = yes' >> ~/.asdfrc
asdf plugin add ruby
asdf install 3.2.2
```

**If you skip that, nothing silently goes wrong.** The `Gemfile` carries
`ruby ">= 3.2"` — a floor, not a second pin — so the wrong Ruby announces
itself in one line:

```
Your Ruby version is 2.6.10, but your Gemfile specified >= 3.2
```

which is the whole reason the floor is there. If your Ruby is the one macOS
ships (`/usr/bin/ruby`, 2.6.x), nothing here will work — Jekyll 4 needs 3.x.

**A trap worth knowing about**, because it cost an afternoon: `LDFLAGS` and
`CPPFLAGS` exported globally from a shell profile are inherited by every
`./configure`, including the one that builds Ruby. If they point at a Homebrew
package that has since been removed — `openssl@1.1` is the usual culprit — the
build dies at `checking whether LDFLAGS is valid... no` and the error names
your profile not at all. Set such flags per-command, never as a login export.

**3.2.2 reached end of life** and no longer gets security updates. Moving to a
supported 3.3 or 3.4 is now a **one-line change in one file**, which is what
collapsing the pin bought — but it still changes the Ruby that builds the
deployed site, so it wants doing deliberately rather than in passing. Note that
Cloudflare's own default is already 3.4.4, so the gap is only as wide as
`.ruby-version` says it is.

## How it's laid out

**The website is `site/`. Everything else at the root is the rest of the node** —
the services, the tooling, the documents. [`NODE.md`](NODE.md) says why, and
what the root is allowed to become; [`STATION.md`](STATION.md) says what the
station around it is for.

```
_config.yml                Site settings. ~40 lines, all commented.
                           Stays at the root; `source: site` points it down.
site/                      EVERYTHING THE PUBLIC GETS. Jekyll sees only this.
  *.md                     One file per page. Filename becomes the URL.
  _data/                   Content that repeats or changes. Plain YAML.
    org.yml                Address, email, phone, socials.
    nav.yml                Header and footer menus.
    providers.yml          The five transactions. See below.
    membership.yml         Tiers and prices.
    facilities.yml         Spaces that can be booked.
    equipment.yml          What kinds of gear we have (not an inventory).
    watch.yml              Channels and carriage.
    board.yml              Board and staff roster.
  _layouts/                Three of them: default, page, podcast.
  _includes/               Four: head, header, footer, transaction.
  _podcasts/               One file per show. Shares the podcast layout.
  assets/css/site.css      The entire visual design. One file.
  assets/js/nav.js         Ten lines. The mobile menu. That's all the JS.
  staticwebapp.config.json Routing, redirects, auth rules.
  bin/                     Build tooling and the syncs. Excluded, never published.
  tests/                   Browser tests. Excluded, never published.
worker/                    The broker. Its own Worker. See [identity.md](identity.md).
site-template/             The scaffold a member site is cut from.
docs/                      This directory. Everything written down.
```

`bin/` and `tests/` sit inside `site/` because that is the context they serve —
the syncs write `_data/`, the browser tests drive the built pages. They are the
only two `exclude:` entries in `_config.yml`, and
`site/bin/test_nothing_internal_is_published.py` fails the build if either ever
reaches the output.

That's the whole thing. Nine template files and a stylesheet.

### Adding a page

Create `something.md` in `site/`:

```markdown
---
title: Something
lede: One sentence under the heading.
---

Write in Markdown.
```

It's live at `/something/`. Add it to `site/_data/nav.yml` if it belongs in a menu.

### Adding a podcast

Copy any file in `site/_podcasts/` and edit the front matter. It appears on
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
