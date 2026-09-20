# Member sites

<!--
Was `site-template/README.md` until 2026-09-18. It moved because READMEs are
now written for the audience that reads them, and this one is for the crew:
nothing in it is addressed to a member. Her words:

  "that read me would never land in a real site templated thing"

`site-template/` therefore has no README. The one that belongs to a member is
hers to write, and is deliberately absent rather than stubbed — a placeholder
that ships to every member site is the thing somebody always forgets to delete.

The framing below is also SUPERSEDED in one place. "Discoverability at a local
level" is not the problem a member site solves; burnout for want of a tool or
an answer at the moment it was needed is. See docs/TENANCY.md, "The problem is
burnout, and it is not discoverability." The rest of this file stands.
-->

**A member site is a scaffold, not an example.** Nothing in `site-template/` is
a real member's site. It exists so the shape is decided in one place, reviewed
like anything else, and copied rather than reinvented the first time somebody
needs one.

**It is two directories, not one.** `site-template/` is what a member's own
repository holds; `member-site-core/` is what FCPM supplies at build time. See
*The split* at the end of this file.

## The problem it exists to solve

Members already publish. They upload to YouTube and Spotify and the work is
genuinely there — the assertion "our members are making things" is true and
measurable.

What is missing is **discoverability at a local level**. A Fort Collins
resident cannot find a Fort Collins producer through YouTube's recommendations,
and a producer with four hundred subscribers has no way to be found by the
people who live twenty minutes away.

So a member site is not a replacement for those platforms. It is a **local
index over them**, with one property those platforms do not offer: a feed that
someone else is allowed to read.

## What it produces

One file matters more than all the pages: `/feed.xml`.

That feed is what FCPM reads (`site/bin/sync-feeds.py` in the main repository),
and it is the whole contract. Everything else on the site is for humans; the
feed is for us. A member who never looks at their own site still gets listed
on ours as long as the feed keeps working.

## Publishing states

Repositories we host are **public**, so this is not a secrecy mechanism — it is
a scheduling one.

| `status` | On the site | In the feed | Meaning |
|---|---|---|---|
| `draft` | no | no | Being worked on. Visible to anyone reading the repo, which is fine — a repo is not a stage. |
| `scheduled` | yes, marked | yes, dated forward | Finished and waiting for a drop day. |
| `released` | yes | yes | Out. |

`scheduled` is the interesting one. It puts a **future date** in the feed on
purpose, so FCPM can see what is coming and slot it into a drop day without
anyone sending an email about it. Scheduling is something people already do by
hand here; this is the same act, written down where a machine can read it.

**If a member needs genuine pre-release secrecy**, that is what ejecting is
for: they take ownership, make the repository private, and carry on. A GitHub
App installed on their repository can keep reading the feed afterwards, so
they keep submitting to us passively without giving up control. Ejecting
should cost them nothing but a decision.

## Large artifacts do not go in git

Members finish a program as one large file, and they often keep versions of it.
Putting that in a repository is a bad trade — git is poor at large binaries,
and nobody wants their working files versioned by accident.

So `artifact.url` is a **pointer**, not a payload. Put the finished file
wherever you already put it, and link it. The generated feed carries that link
as an `<enclosure>`, which is exactly what enclosures are for, and it is how
the file ever reaches FCPM.

A feed entry says *a program exists*. The enclosure says *where the actual file
is*. Both are needed; neither is sufficient.

## Where this stands, 2026-09-19

Written at a reboot, for whoever arrives next. The machinery is finished and has
no users, and those two facts look the same from outside.

**Built and running.** `sites.yml` is the list. `bin/build-sites.py` composes,
builds each site independently, publishes tenants into `site/member-sites/` and
prunes anyone delisted. 44 tests.
`.github/workflows/publish-member-sites.yml` runs it Thursdays and on demand,
and commits — Cloudflare's git build publishes from the commit, so there is
still exactly one thing that puts bytes on the internet.

**Zero tenants.** `sites.yml` holds `site` and `site-template` and nothing else,
so every green check above is green over an empty set. Nothing is broken; there
is simply nobody listed.

### The next commit

**The generated tier.** A show with its own repository gets a `tenant` site;
every other show gets one anyway, built from the show data this repository
already holds plus `member-site-core/`. See
[`TENANCY.md`](TENANCY.md), *"Every show gets a site, and most of them are
virtual"*.

It is the highest-value thing available because of the arithmetic: `site/_shows/`
holds **1** and `site/_podcasts/` holds **8**, so the first run produces nine
sites where there are now none — with no member having to do anything.

**Its one undecided point**, and it should be decided before it is built: a
generated site has no repository and therefore no gitlink, so it is neither
`tenant` nor `listed`. Either `sites.yml` grows a role whose source is a
collection entry rather than a directory, or generation synthesises entries
before the manifest is read.

The rule that holds either way: **a generated site must never be confusable with
`scaffold`.** The template must never reach the public; a generated site must
always reach it.

### Decisions being held for the operator

Not gaps. These were reserved deliberately and an agent should not settle them:

| | |
|---|---|
| the wildcard rewrite | `run_worker_first` on the site Worker, which costs the public site its *"no main, no runtime, nothing to execute"* property, versus a second Worker on `*.fcpublicmedia.org/*`. Both written up in [`deploying.md`](deploying.md) |
| a better name for `member-site-core/` | reserved by her; the name in the tree is provisional. `TENANCY.md` argues the journal engine's word for it is *engine* |
| the audience-facing README for `site-template/` | **deliberately absent, not stubbed.** Her voice |
| collapsing `_shows` and `_podcasts` | recorded in `TENANCY.md`; it moves live URLs, so it is a `REDIRECTS.md` question as much as a data one |
| the signal that should replace the Thursday schedule | wanted, not designed. Nothing anticipates its shape on purpose |

### Two things that are true and unreported by any tool

**`.advocate-engine` is pinned 5 commits behind its `origin/main`** (pin
`4635cfc1`). A clean `git status` will never say so — a superproject is clean
when the gitlink matches what was committed, which is a statement about the
commit and not about the world. Advancing it is its own pull request by whoever
owns it.

**The live site is served from a personal Cloudflare account.**
`new.fcpublicmedia.org` is a CNAME to `fcpm.autumn-e2c.workers.dev`. It works and
will keep working; it is recorded in [`deploying.md`](deploying.md) because
nothing in the repository said so until somebody ran `dig`.

## The split

Drawn 2026-09-18, because the line between what a member owns and what we
supply had been a table in prose and a single directory on disk.

```
site-template/          WHAT A MEMBER'S REPOSITORY HOLDS
  _data/site.yml        Settings. One file, and the only one an editing UI
                        would ever write to.
  _data/programs.yml    The programs. One entry per thing you make.
  .gitignore            Keeps finished video out of git.

member-site-core/       WHAT FCPM SUPPLIES AT BUILD TIME
  _config.yml           Managed. A member never edits it.
  _layouts/default.html Markup.
  assets/css/site.css   The whole visual design.
  index.html            The public page, driven entirely by _data.
  feed.xml              Generated. The contract with FCPM.
  Gemfile               Jekyll. The member does not need one — see below.
```

**A member's repository is two YAML files and a `.gitignore`.** That is the
whole of it, and it is the answer to *"if we can get things done with just a
configuration."*

**Nothing in `site-template/` is markup.** A member who wants different markup
is a member who should eject and own it, which is what the collision rule below
detects.

### Why the member needs no Gemfile

Measured 2026-09-18: with an explicit `--source`, Jekyll reads
`<source>/_config.yml` rather than one in the working directory. So one
toolchain — one Ruby, one Gemfile, one lockfile, all at the host — builds every
site. `member-site-core/Gemfile` exists for the composed build and for a member
who ejects, not for a member who is hosted.

The principle is GitHub Pages': **the defaults live in the host, not the
tenant.**

### Publishing, and what delisting does

`bin/build-sites.py --publish` copies each built tenant into
`site/member-sites/<name>/` and commits nothing itself. **The cadence commits**:
`.github/workflows/publish-member-sites.yml`, Thursday morning and on demand,
the same bargain the `_data` syncs make.

**It does not deploy.** It writes into `site/` and commits; Cloudflare's git
build sees the commit and publishes, exactly as it does for any other change to
`site/`. There is still one thing that puts bytes on the internet, which is the
property the manual deploy workflow was deleted to restore.

The schedule is a placeholder for a signal that does not exist yet. When it
does, it becomes another entry under `on:` and nothing else in that file
changes.

**A site is published as its `name`, not its path.** The name is the public
address: the subdomain label and the folder. The path is where we happen to
check their repository out. Keeping them separate means moving a checkout
cannot silently change somebody's address.

**Removing an entry from `sites.yml` takes the site down.** `--publish` prunes
published directories that are no longer listed, and that is the whole point of
it: otherwise *"delisting is the whole withdrawal"* is a thing we say rather
than a thing we do, and a published tree that only grows would keep serving
somebody who asked us to stop.

Three guards on that, because a recursive delete driven by a config file wants
them:

- only **direct subdirectories** of the publish root are considered, so a
  listing page or a `.gitkeep` at the root survives;
- the root must resolve **inside the repository**, checked on the shape of the
  path before anything is read from disk;
- **`--only` prunes nothing at all.** A single-site run sees one entry, so
  every other site would look unlisted — which would take every member's site
  down at once, and is the worst bug available here.

**A tenant that failed to build keeps what it published last time.** The
cadence promises that new work appears, not that old work vanishes the first
morning somebody's data file will not parse.

`site/_data/member_sites.json` is the list, written as data rather than as a
page so FCPM's own site can render it with a Liquid loop. **It carries no
timestamp** — a payload that records when it ran differs every run and commits
a file every week to say it looked. The commit is the timestamp.

### Composition, and the collision that means "eject"

`bin/build-sites.py` stages `member-site-core/` and then the member's own files
on top. **If a member's file would overwrite one of ours, that is not an error
to resolve — it is the eject signal**, and the builder reports it rather than
silently discarding their work.

It is the same fact `git merge upstream/main --ff-only` failing used to carry,
detected at build time instead of at update time, and it fails the same way: in
favour of the member having taken the site somewhere of their own.

## Ejecting

The line between what upstream owns and what the member owns is by directory,
so a member site can be updated from the template without stepping on
anybody's work:

| Upstream owns | Member owns |
|---|---|
| `_layouts/` `_includes/` `assets/` `.github/` | `_config.yml` `_data/` any content pages |

Updates come in with `git merge upstream/main --ff-only`, which **fails loudly**
rather than merging when a member has edited the left column. That failure is
the eject signal: they have taken the site somewhere of their own and should
stop taking updates. That is a feature, and it should be an easy, unembarrassing
thing to do.

Note there are no forks anywhere in this. A plain `upstream` remote
fast-forwards exactly the same way, works on private repositories, and
transfers cleanly.
