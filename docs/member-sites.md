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
| ~~the signal that should replace the Thursday schedule~~ | **Settled 2026-09-24**: a signed intermediate, published on change. See *"Intermediates are the deliverable"* below |

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

## Intermediates are the deliverable

Autumn's call, 2026-09-24, settling the last row of the table above. Recorded
close to verbatim, because the reasoning is the part that has to survive.

> We're going to use our intermediates system to deliver what the content
> should be, in order to save an outside builder exactly that trouble. It'll be
> signed by us.

An **intermediate** is the fourth thing the library engine already claims to
hold — *"intermediate artifacts we use to build sites and video"* (README,
*Library*). This decides that member sites are delivered as intermediates
rather than composed here at build time.

### The symmetry is the argument

> Station Node is hosting us, so they're building us, but we're giving them
> those pre-bakes. And we're doing the pre-bakes because we're in the same
> position. We go to build our sites, and some of these modules are
> multi-tenant, but they might be ejected. We might only get access on a
> rotating basis. We're gonna cook intermediates so that we have those.

FCPM sits on both sides of the same arrangement at once. Station-node hosts
FCPM and builds it; FCPM hosts members and builds them. Handing a pre-bake
upward is the same act as expecting one downward, and neither side has to trust
the other's toolchain to do it.

**The reason is loss of access, and that is what makes it more than a
convenience.** A module that is multi-tenant today may be ejected tomorrow;
access may be granted on rotation. A build that reaches for its inputs at build
time fails in exactly those moments. **A pre-bake survives the loss of the
thing that produced it** — which is why this is cooked in advance rather than
resolved on demand, and why it is worth the storage.

> The media node is going to get a chance to register as many sites as it deems
> first class, and it can build all of them exactly in the way that Station Node
> is building for us.

So *first class* becomes a thing a host decides about a site, rather than a
property the site asserts about itself.

### An intermediate may be a folder

> If the intermediate has a folder to represent complex things, then we're
> still fine.

Stated because it is the thing that would otherwise be assumed away. An
intermediate is not constrained to one file. A site that needs a directory —
assets, several data files, a tree — publishes a directory, and nothing
downstream has to flatten it to fit a format decision nobody made on purpose.

### What it is source for

Not only Jekyll. FCPM is building toward **a source distribution for a markdown
browser**, so an intermediate is read by more than one kind of consumer, and
that is the reason it carries content rather than rendered output. A
pre-rendered site would serve one consumer and strand the rest.

### Where identity comes from

Membership is `you` — the control point at `FCCN-ANTIBODY/you.anecdote.channel`,
whose own `residency.yml` declares an `instance` label holding *"which site this
deployment is: its origin, which is also the RP ID every passkey minted here is
bound to, permanently."*

That is what lets a member identify with something well enough to modify their
own project, and it is why members become subdomains under it. **Its subdomain
root is deployed for member repositories, not for member sites** — the
repository is the thing a person owns and edits; the site is an output. Nothing
of this is leveraged on the media node yet, and it is the direction rather than
the state.

### What this does not change

**`/feed.xml` is still the inbound contract.** A member's feed is what FCPM
reads, and the property that matters is that *someone else is allowed to read
it*. An intermediate travels the other way — FCPM to a builder — and is signed
by us. Two directions, two artifacts; neither should be made to do the other's
job.

**Signing has a precedent and one prerequisite.** `site/bin/mint-claim.py`
already signs with a private key and verifies in the browser against the public
half in `site/_data/identity.yml`. The shape exists. But `identity.yml` carries
`keys: []` — no signing key has ever been minted — so there is a key ceremony
first, and where that private key lives is a decision rather than a value.

### What it settles, and what it unblocks

- **The Thursday schedule.** A signed intermediate published when the content
  changes *is* the signal that was wanted and deliberately not designed. It has
  the property a cron cannot have: it moves on change and never otherwise, the
  same reason [`KIOSK.md`](KIOSK.md) uses a digest rather than a timestamp.
- **The generated tier's one undecided point.** A generated site has no
  repository and therefore no gitlink, so it could be neither `tenant` nor
  `listed`. An intermediate does not need a repository in order to exist, so the
  question stops being asked. `site/_shows/` holds 1 and `site/_podcasts/` holds
  8 — nine sites, with no member having to do anything.
- **`submodules: recursive` in `publish-member-sites.yml`.** It is there to pull
  tenant repositories at build time. If tenants are delivered as intermediates,
  the recursion is not needed — which also retires the private-submodule problem
  recorded in `.gitmodules` against `.contact-sheets-engine`, with no token and
  no scrub.

---

## How an update reaches us, and who owns it on the way

Autumn, 2026-09-24, in the same conversation as the section above. This is the
transport half of that decision and the custody model underneath it.

### Two channels, and the difference is deliberate

**FCPM talks to station-node over the LAN.** **FCPM's members talk over QR
channels.** That is a design split, not a stage of rollout — the two sides of
this organisation have different reach and are not being made to pretend
otherwise.

A QR channel means the update has to survive being **serialized to bytes** and
carried across a gap with no network on it.

### The serialization is a tar of a file structure

> We've decided at this point we're just going to tar a file structure, which
> then contains bytes of things.

Chosen because it is the boring answer that already works: a directory survives
the trip intact, nothing has to be flattened, and *"if the intermediate has a
folder to represent complex things, then we're still fine"* holds on this side
too.

### The checks are publishable, and that is the point

> It just works like a form that they can commit to, using controlled hooks as
> checks for us to import — or at least observe, to know the rules. You don't
> even have to install them if you understand what's going to be rejected or
> not. And it's a state machine. It is like a living little state machine.

**The rules are legible whether or not you run them.** A member who installs
the hooks gets told early; a member who merely reads them knows what will be
rejected and can comply by hand. That is the same property `REDIRECTS.md` has —
a check rather than a claim — applied to somebody else's working copy.

Calling it a state machine is the load-bearing part: a submission is *in* a
state, the hooks say which transitions are legal, and both sides can compute
the answer independently.

### Members submit with git, signed by the passkey we already know

> They're committing on a little branch and we're going to pull it in and say,
> okay, great, and merge that into our thing. It looks signed by their passkey.
> We know what their passkey is.

So the submission is a branch, the merge is the approval, and provenance comes
from the passkey enrolled at `/authorize/` rather than from a second identity
system. The broker in `worker/` already issues and verifies assertions; this is
another consumer of it, not a new mechanism.

### Custody: we hold it, they own it

This is the part that is a commitment rather than an implementation detail.

> We're going to carve out dedicated space for them to manage that over time,
> and it will be a repository, and they will have full custody over it, even
> though we're holding it. They are free to back it up any number of ways from
> that point, because we gave them a git client in their phone. They could take
> control of their thing at any time, and that is the hallmark of what I'm doing
> here.

**Holding is not owning.** A member can walk with the whole history at any
moment, and nothing has to be negotiated for that to work — it is a clone. This
is what `member-sites.md` already means by *ejecting should cost them nothing
but a decision*, made concrete.

> And if they only ever wanted to publish their intermediates for us as an
> artifact, so that they could keep a private repository — completely safe.

**A member may keep their repository private and send only the intermediate.**
The artifact is the contract, so the source never has to be visible to us at
all. That is the strongest version of the intermediates decision, and it is
available to anybody who wants it.

### GitHub is a relay, not the system

> FCPM's member updates are going to come back to it through GitHub, because
> that is one of our relays. When someone edits the bytes, they need to submit
> it back, and right now the only way for that to go anywhere meaningful is to
> go to an address that the cloud is offering — unless someone has the changes
> in their phone and they can generate the diff and show it to the computer.

Named as **one relay among possible others**, which is the reason to write it
down: today GitHub is the address the cloud offers, and the design does not
depend on it staying that way. The phone-to-camera path is sketched, not
designed, and is recorded only so nobody assumes the cloud is load-bearing.

### FCPM is not the publisher of its own site, and should know it

> All of that is what's travelling the LAN to the station node for now. Later,
> FCPM can probably take over its deploy so that it doesn't need to be on the
> same LAN. This is an important process for it to know that — hey, I'm not the
> publisher of my own stuff. I rely on someone else.

Worth stating plainly because it is easy to drift out of. The arrangement with
station-node is guest hosting and [`KIOSK.md`](KIOSK.md) already calls it
*"temporary by design"*. Knowing we are not our own publisher is what keeps the
artifacts portable enough for that to stay true.

### What station-node's trade service is for

> What I hope it really means is that Station Node is running a trade service
> that publishes the intermediates. That's its goal: publish the intermediates.

And the acceptance range is wide on purpose:

> If your intermediate happens to be raw source, or it happens to be fully
> cooked HTML, it falls inside parameters.

**Both ends of that range are valid input.** A consumer does not get to require
one shape.

### Degrading gracefully is a promise, not a fallback

> And when it doesn't, we want to promise that it degrades gracefully. So we're
> fine showing the raw Liquid. We can probably mark it up a little, but we want
> it to be clearly not interpreted.

The rule for anything outside parameters: **render it as itself, visibly
uninterpreted.** Showing raw Liquid is an acceptable outcome; showing something
that *looks* rendered but is not is the failure. Light markup is fine as long as
it makes the uninterpreted state more obvious rather than less.

This is the same discipline as `unwitnessed` on the depot — a surface must not
present a thing it could not confirm as though it had been confirmed.

---

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
