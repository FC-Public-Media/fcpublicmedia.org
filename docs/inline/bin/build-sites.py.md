# `bin/build-sites.py`

Moved out of the file. Unreviewed.

## 1

Above `import argparse`

python3 bin/build-sites.py                 build everything buildable
    python3 bin/build-sites.py --list           show the manifest, build nothing
    python3 bin/build-sites.py --only site      build one
    python3 bin/build-sites.py --strict         a tenant failure is fatal too

This is the member-site factory. `site/` is a self-contained Jekyll project, so
there is no longer a "the site" to special-case — it is one entry in sites.yml
like any other.

A member's site is NOT self-contained, and deliberately so: `site-template/`
holds two data files, and `member-site-core/` holds the config and the markup.
They are composed at build time. See `compose()`, and docs/member-sites.md for
where the line is drawn and why.

WHY ONE TOOLCHAIN FOR ALL OF THEM
---------------------------------
Every build runs `bundle exec` from `site/`, which owns the Gemfile and the
lockfile, and points Jekyll at the site with `--source`.

**Measured, 2026-09-18: with an explicit `--source`, Jekyll reads
`<source>/_config.yml` — not one in the working directory.** Building
`site-template/` this way produces a page titled "Your Show", which is the
template's own config and not FCPM's. That one fact is what makes a managed
multi-site build possible at all.

It is also the principle the whole tenancy rests on, arriving as an
implementation detail: **the defaults live in the host, not in the tenant.** A
member's repository needs no Gemfile, no lockfile and no Ruby pin to be built
here, because the host brought all three. GitHub Pages works the same way and
it is the reason "almost no config" is achievable rather than aspirational.

(The prune question this used to defer is settled: the template is pruned to
data, and ejecting means composing the core into the member's repository as a
commit rather than leaving it behind. That is option 1 from docs/TENANCY.md,
"What the pruner is actually blocked on", chosen by her on 2026-09-18.)

WHY A FAILURE DOES NOT STOP THE RUN
-----------------------------------
Her words, on cadence:

  "we promise a cadence that we can meet instead of real time, which is the
   crux of it all."

A promise of Thursday that is kept is worth more than a promise of instantly
that is kept most of the time. But "building kinda all at once" puts one broken
tenant in the same run as every healthy one, so **every site is built
independently and the run continues past a failure.** One member's typo must
not make everybody else miss the day.

That is also why the exit code is not simply "did everything build":

  - `site` and `scaffold` are ours. Failing is our bug and exits non-zero.
  - `tenant` failures are reported, and do not affect the exit code, because
    they are not a defect in this repository. `--strict` overrides that when
    you want the harsher reading.

WHAT THIS DOES NOT DO
---------------------
**It does not deploy.** Publishing a tenant needs a Cloudflare account per
site, and which account a site lands in is a decision that has been made in
prose and not in configuration — the default is her `anecdote.channel`
constellation, and a member who buys a domain moves to FCPM's own account. See
docs/TENANCY.md, "Where the sites get served". Building is the half that is
fully decided, so it is the half that is built.

It also does not fetch or hydrate anything. A `tenant` whose directory is not
on disk reports `absent` and is skipped: an unhydrated gitlink is the normal
resting state of the list, not a fault.

## 2

Above `TOOLCHAIN = REPO / "site"`

The directory whose bundle every build borrows. It owns Gemfile,
Gemfile.lock and .ruby-version, so every site is built on one known
toolchain rather than on whatever each happened to pin.

## 3

Above `COMPOSED = {"scaffold", "tenant"}`

Roles whose source is only half a site: the other half is `core` from
sites.yml, staged underneath it at build time. `site` is ours and whole.

## 4

Above `DELIVERIES = {"source", "intermediate"}`

HOW A HOST DEPLOYS A SITE: the one switch every host reads. docs/deploying.md,
"The switch".

  source        the host runs its own ordinary build in `path` (for `site`,
                Cloudflare's `bundle exec jekyll build` with root `site`).
                The fallback that always works, and it needs nothing from us.
  intermediate  the host builds nothing. It serves what we pre-baked in
                _intermediates/<domain>/, a root with its own wrangler.jsonc.
                docs/INTERMEDIATES.md.

A host's ROOT DIRECTORY is where this switch actually takes effect, because a
Cloudflare dashboard cannot read this file. So each kind of delivery is its
own self-describing root, and `--deploy-root DOMAIN` prints which one to set.

## 5

Above `self.name = name or path.rstrip("/").split("/")[-1]`

The name is the PUBLIC ADDRESS — the subdomain label and the folder a
site is published into. It defaults to the last path segment, but it
is separate from the path on purpose: where a repository is checked
out is our business and the address is the member's, and moving one
must not silently change the other.

## 6

Above `collisions = []`

Stage `core`, then `site` on top of it, into `dest`.

Returns the list of paths the site carries that core also provides.

THAT LIST IS THE EJECT SIGNAL, not an error to resolve. A member whose
repository contains a layout has taken the markup somewhere of their own,
and the one thing this must never do is quietly prefer ours and build a
site that is not the one they wrote. It is the same fact that
`git merge upstream/main --ff-only` failing used to carry, noticed at build
time instead of at update time.

Core is copied first so that `dest` is a complete site even when the member
supplies almost nothing, which is the normal case: two data files.

## 7

Above `root = (repo / publish_root).resolve()`

Remove published sites that are no longer in the list.

**This is what makes delisting real.** Removing an entry from sites.yml has
to take the site off the internet, or "delisting is the whole withdrawal"
is a thing we say rather than a thing we do. A published tree that only
ever grows would keep serving somebody who asked us to stop.

Only direct subdirectories of the publish root are considered, and only
inside it — files at the root (an index, a .gitkeep) are left alone.

## 8

Above `if root != repo.resolve() and repo.resolve() not in root.parents:`

The containment check comes FIRST, before asking whether the directory
exists. Checking existence first meant a path that escaped the
repository and happened not to exist returned quietly instead of
refusing — so the guard passed precisely when it had least information.
A recursive delete should refuse on the shape of the path, not on what
is currently on disk.

## 9

Above `target = repo / "site" / "_data" / "member_sites.json"`

The list of published sites, as data.

Written as JSON into `site/_data/` like the five syncs, so FCPM's own pages
can render the listing with a Liquid loop. Deliberately NOT an HTML index:
what that page says, and in whose voice, is not this script's business.

## 10

Above `payload = {`

NO TIMESTAMP. sync-feeds.py learned this one already: a payload carrying
the time it was generated differs on every run, so the cadence commits a
file every week to record that it looked. The commit is the timestamp.
Without one, this file changes only when the list of sites changes.

## 11

Above `repo = repo or REPO`

Build one site. Returns (status, detail).

status is one of: built, failed, diverged, absent, skipped.

A composed site (`scaffold`, `tenant`) is staged into a temporary
directory: `core` first, then the site's own files on top. Its `_site` is
still written beside the site's source, so the output lands where a deploy
would look for it and the staging area is disposable.

## 12

Above `if entry.required:`

For a tenant this is an unhydrated gitlink and entirely expected. For
one of ours it means somebody moved a directory without editing
sites.yml, which main() treats as fatal.

## 13

Above `return "failed", (result.stdout or "") + (result.stderr or "")`

Liquid errors land on stdout, not stderr, and are the whole
reason anybody reads this output — so keep both.

## 14

Above `return "failed", "build reported success but produced no index.html"`

A zero exit with no index is worse than a failure: deploying it
replaces a working site with an empty one and reports success.

## 15

Above `if status in ("failed", "diverged"):`

Does this outcome mean the run failed?

A tenant that did not build is not our defect — that is the whole point of
building each site independently. `--strict` reads it the other way.

## 16

Above `published = [e.name for e, s, _ in outcomes if e.publishes and s == "built"]`

Only what built. A tenant that failed keeps whatever it published
last time rather than being taken down for a typo — the cadence is a
promise about new work appearing, not about old work vanishing.

## 17

Above `keep = {e.name for e, _, _ in outcomes if e.publishes}`

Kept, rather than pruned: everything that built now, plus anything
still listed as a tenant whose build did not succeed this run.

## 18

Above `removed = [] if args.only else prune(keep, REPO, publish_root)`

A single-site run prunes nothing. Its `outcomes` is one entry, so
every other published site would look unlisted and be taken down —
which is the worst possible bug in this script and the reason it is
spelled out rather than guarded by a condition somewhere.
