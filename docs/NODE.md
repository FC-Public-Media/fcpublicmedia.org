# This repository is a node

Written 2026-09-17, when the website moved into `site/`.

Everything below is about *shape*. Nothing here mounts an engine, adds a
submodule, or moves a pin — each of those is its own pull request by whoever
owns it, and that has been the node seat's rule since it was seated.

Three companions, and the division between them is worth knowing before you
pick one. **This file is the repository**: what is at the root, what is in
`site/`, and what `site/_data` can reach. [`STATION.md`](STATION.md) is **the
station**: the machines, the crews, the public-repository rule, and which
engines arrive in what order. [`TENANCY.md`](TENANCY.md) is **the tenancy**:
other people's sites published from here, and it is where *What a second site in
the cluster would need*, below, is now carried forward. [`DESIGN-NOTES.md`](DESIGN-NOTES.md)
is **the services** the other three exist to make possible.

---

## What was decided

**2026-09-16 — the site is the node.** Not a sibling repository holding the
site as a holding. Her words:

> i do think the site is the node because itll build with its resources handy
> in jekyll data. The -node paradigm gives us site clusters that share a build
> root context

**2026-09-17 — the website scoots into a prefix, and the prefix is `site/`.**
Her words:

> I don't wanna change the build system per se, but I need to scoot it into a
> suitable prefix. And I think just the word site is gonna be fine, because
> what we're doing next to it is carving out ways for this thing to act more
> like station node.

These two are the same decision, a day apart, and it is worth saying why they
are not in tension. *The site is the node* settles **which repository** — this
one, rather than a sibling with this one inside it. It does not say the website
must own the top of that repository. What the second decision does is free the
root to be the node's floor, so that the things the node grows — the services,
the library, the engines — sit beside the website instead of being crowded in
among its pages.

**station-node is laid out exactly this way**, and it is the prototype this
repository is being shaped after: its root holds `bin/`, `docs/`, `library/`,
`machine/`, `state/` and the `.<subdomain>-engine` mounts, and its own web
surface is one directory called `site/`.

### And FCPM chooses its own holdings

Also 2026-09-17, and it needs recording because the node seat's G1 and G4 both
assume otherwise until told:

> FCPM does not need to take cues from station-node about what to keep in its
> library per se. It is definitely up to us what we are bringing over.

The prototype is borrowed from for its **shape**. What goes in the library is
FCPM's own decision, made against what public media here can actually offer.
The seat's job is still to say where each borrowing came from — a borrowing
without a source is a guess — but "station-node holds it" is not by itself an
argument that FCPM should.

### Why a node at all, and not just a website

> All we're really doing here is showing everyone how to be self-sufficient
> with more than just a website.

That is the whole motivation, and it is worth keeping at the top of this file
because it is the thing that makes the reorganisation worth its cost. A public
media organisation that can hand a member a website is useful. One that can
hand them the *services underneath* a website — identity, uploads, a schedule,
a way to be found — is doing something nobody else in this town is positioned
to do. The node is the container for that second thing.

---

## What is at the root, and what is in `site/`

```
README.md            the repository's front page.
AGENTS.md            standing orders. At the root because that is where they are looked for.
advocate.yml         the seat declarations.
site/                THE WEBSITE, and the build root. Jekyll runs from in here.
  _config.yml        the site's config. No `source:`; the source is this folder.
  Gemfile            one gem. Jekyll.
  .ruby-version      the only Ruby pin. Cloudflare reads it from here.
  wrangler.jsonc     host config. `assets.directory` is `_site`, beside it.
  bin/               build tooling and the syncs. Excluded from the build.
  tests/             browser tests. Excluded from the build.
docs/                everything written down. Outside `source:`, so unpublishable.
kiosk/               what a studio screen says. Content only, no renderer. See KIOSK.md.
instruments/         each studio screen and what it shows. Draft. See its README.
machines/            one profile per host this can plausibly run on. See its README.
worker/              the broker. Its own Cloudflare Worker. Deployed separately.
site-template/       what a member's own repository holds. Data only, no markup.
member-site-core/    what FCPM supplies to a member site at build time.
```

The rule is short: **`site/` is what the public gets. The root is everything
else.** `worker/` was already a service sitting beside the site rather than
inside it, which is part of why this move was cheap — the repository had half of
this shape before anybody named it. `api/` was the other half and is gone; see
`identity.md`.

### Why `bin/` and `tests/` are *inside* `site/`

Because that is the context they serve. `bin/` writes `_data/`; `tests/` drives
the built pages. Neither is content, and both are excluded — the only two
`exclude:` entries there are, and the only two there should ever be.

**That is not the old document list coming back.** That list named eleven files
one at a time, and the failure mode was the twelfth. These are directories:
adding a script or a spec needs no edit, so there is nothing to forget. And
`site/bin/test_nothing_internal_is_published.py` fails the build if either
directory reaches `_site`, which is what makes the claim checkable rather than
merely careful.

**Documents are different and go outside `source:`** — the root or `docs/` —
where the build cannot see them at all.

### One thing the move fixed on its way past

`_config.yml` used to carry an `exclude:` list of eleven internal documents,
because **a `.md` file with no front matter is copied verbatim to a public URL**.
MANIFEST.md, REDIRECTS.md and RESERVE-DESIGN.md had each been published that way
and had to be taken back. REVIEW-NOTES.md is the one that mattered: unratified
board feedback, quoted verbatim, one guessable URL from anyone who tried.

That list is gone, and nothing replaced it. Internal documents are at the root,
outside `source:`, so Jekyll does not see them. The failure mode was *forgetting
to add a file to a list*, and there is no longer a list to forget.

**A new internal document goes at the root.** Do not move one into `site/`, and
do not restore the exclude list to make that safe — it was never reliably safe,
which is the whole reason it is gone.

---

## The mechanism is one dashboard field

```
Cloudflare → Path / root directory → site
```

That is the entire change to how this site builds, and it replaces an earlier
arrangement worth understanding because the reasoning survived the change.

**Until 2026-09-18 the config stayed at the repository root with `source: site`
in it.** Jekyll looks for `_config.yml` in the directory it is run from, before
it has read any `source:` setting, so a config inside the source directory has
to be named on the command line — in CI, at the host, and by hand. Keeping it at
the root meant the move into `site/` cost nothing: same build command, same
working directory, same output, **and nobody had to open the dashboard.**

**What changed is that there is now a reason to pay that price.** The repository
root is being given to the station — the front door, and whatever engine ends up
providing it — and a root that is also a Jekyll build root cannot be given to
anything else. So the site stopped borrowing the root:

| | |
|---|---|
| Build command | `bundle exec jekyll build`, unchanged |
| Working directory | **`site/`**, set by the dashboard field and by `working-directory:` in CI |
| Config | **`site/_config.yml`**, with no `source:` — the source is where the config lives |
| Moved with it | `Gemfile`, `.ruby-version`, `wrangler.jsonc`, each read relative to the build root |
| Output | **`site/_site`**. The dashboard's output field stays `_site` because it is relative to the root directory |
| The published bytes | **identical.** Every file byte-for-byte, modulo the `?v=<build time>` cache-busting token |

That last row is how both moves were checked: the tree before and the tree after
were built and compared file by file. Nothing the public fetches is different.

**That token is the build clock, not a file time**, and the distinction was
written down wrongly here until 2026-09-24. Five templates carry
`?v={{ site.time | date: '%s' }}` — `site.css` and four scripts — so **every
HTML file in `_site` changes on every build, whether or not anything was
edited.** An mtime would have been stable across a no-op rebuild; this is not.
Harmless while a host builds and serves in one step, and not harmless if a build
output is ever committed: the diff is the whole tree every time. See
[`OPEN.md`](OPEN.md).

**`.ruby-version` is the one that would have failed quietly** if it had been left
behind. Cloudflare's image reads it from the root directory setting, so the host
would have moved to their default Ruby with nothing in CI noticing.

---

## What `site/_data` may reach into — and what it may not

This is the part the 2026-09-16 decision got slightly wrong, and a later reader
should have the correction rather than the claim.

The reasoning recorded on G2 was that if the site *is* the node, every holding
sits inside the build root and is **"reachable from `_data`, for free, with no
copying step."** That is not quite how Jekyll works, and it would not have been
true even with the site at the top.

**Jekyll's data directory cannot leave the source tree.** `data_dir` is resolved
through `Jekyll.sanitized_path`, which refuses to escape `source:`. There is no
configuration that points `_data` at a sibling directory. A build root always has
a boundary; moving the boundary does not remove it.

**A symlink crosses it, and that is a trap rather than a mechanism.** Measured in
this repository on 2026-09-17: a symlinked directory inside `site/_data/` *is*
read by an ordinary `jekyll build`, and is *silently ignored* under `jekyll
build --safe` — no warning, no error, the data is simply empty and the page
renders blank. Anything that depends on it would work everywhere until the day
something built in safe mode, and then fail without saying so.

**So the way a node holding reaches the site is that something writes it into
`site/_data/`** — and this repository has been doing exactly that, five times
over, since before it was a node:

(`bin/build-kiosk.py` is the first traffic in the opposite direction: a root
concern *reading* `site/_data/` to produce `kiosk/welcome.yml`. Same rule, other
end — the root reaches down freely, and nothing in `site/` knows `kiosk/` is
there. See [`KIOSK.md`](KIOSK.md).)

| what | from | into |
|---|---|---|
| `site/bin/sync-cablecast.py` | the Cablecast catalog | `site/_data/cablecast.json` |
| `site/bin/sync-schedule.py` | the broadcast schedule | `site/_data/airings.json` |
| `site/bin/sync-calendar.py` | the class calendar | `site/_data/calendar.json` |
| `site/bin/sync-feeds.py` | member program feeds | `site/_data/member_programs.json` |
| `site/bin/sync-nonprofits.py` | the nonprofit registry | `site/assets/nonprofits.json` |

Each runs in CI, commits its output, and the commit is the record. A holding at
the root is the *easiest possible* case of that pattern: no network, no API key,
no rate limit — a file read at a relative path in the same working tree, by a
script that already knows where both ends are.

**That is what being one repository actually buys**, and it is worth more than
the version that was claimed for it. The alternative — the node in a sibling
repository — would make every one of those five syncs a cross-repository
problem, with a submodule pin or a checkout step and a way to be stale. Here
there is nothing to keep in sync, because there is nothing to sync *from*.

So the honest rule:

- **`site/_data` reads what is inside `site/`.** Nothing else, ever.
- **The root reaches down into `site/`**, freely — scripts write into
  `site/_data/`, and `worker/src/index.js` imports `site/assets/js/claims.js` so
  the browser's claim verifier and the broker's cannot drift apart.
- **`site/` never reaches up.** A page that needs something from the root needs a
  script to have put it in `_data` first.
- **Do not symlink across the boundary.** It works, and then one day it does not,
  and it will not tell you.

---

## What a second site in the cluster would need

The unit she named is a **site cluster sharing one build root context**, and
member-site provisioning is the reason it matters — the goal is for that to be
"the library admits a holding", not "somebody sets up a deployment".

Nothing below is built. It is what the next person would run into, written down
while the shape is fresh.

**1. A second `source:` cannot live in the same `_config.yml`.** One config, one
source. A second site is a second config — `_config.member.yml` with
`source: sites/<name>`, built with `-c`. The root stays the working directory for
all of them, which is the part that makes them a cluster rather than two
repositories in a trenchcoat.

**2. `_site` is one directory and would need to become several.** `-d
_site/<name>`, or a destination per config. `wrangler.jsonc` names exactly one
`assets.directory`, so a second site is a second Worker config and a second
deploy — which is correct, because it is a second site with its own domain, not
a subdirectory of this one.

**3. `site-template/` is already the scaffold**, already a complete Jekyll site
of its own, and already checked on every push by `site/bin/check-template.py` —
which builds it and reads its feed back with this repository's own reader,
because that feed is the entire contract between a member site and FCPM. The
factory has a working part before it has a factory.

**4. The shared thing should be `_includes`, not copied files.** This is the one
worth deciding early. Two sites that each got a copy of the header will have two
different headers within a year. Jekyll has no cross-source include path, so a
shared layer is either a symlink (see above — no), a build step that stages it,
or a theme gem. The repository has spent its whole life refusing plugins and
theme gems on purpose; a staging step in `site/bin/` is the option that matches
how everything else here already works.

**5. Naming.** The prefix is `site`, singular, chosen deliberately. If a cluster
arrives, member sites go under something else — `sites/<name>/` — rather than
renaming this one. `site/` is *this* site, and every path in the documentation,
the scripts and the workflows now says so.

---

## What is not here yet

- **No `library/`.** FCPM's library is G4's question and it is waiting on a
  paragraph from Autumn about what the board actually decided. Escalation `9605`
  is open for exactly that, and nothing else is blocked by it.
- **No engines but one.** `.advocate-engine` is mounted. Nothing else is, and
  mounting is out of scope for the node seat by construction.
- **No services described as services yet.** `worker/` is a service in fact;
  G3 asks for proofing to be *described* as one, including what it refuses to
  capture. That is prose nobody has written.

The seat's goals are in [`advocate.yml`](../advocate.yml) under `node`, and the
constitution they answer to is §6 of [`ADVOCATE.md`](ADVOCATE.md).
