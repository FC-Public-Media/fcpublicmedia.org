# The multi-tenant turn

Written 2026-09-17 from **three** spoken briefings by Autumn, the same day as
[`STATION.md`](STATION.md) and [`NODE.md`](NODE.md) and continuous with them.
**Every quotation is dictated speech**, lightly de-garbled where speech-to-text
mangled a proper noun (`Jecal` → Jekyll, `Cloudflare Flair pages` → Cloudflare
Pages) and not otherwise.

| | |
|---|---|
| **The multi-tenant turn** | the frame. The central thing deliberately unnamed. |
| **The factory, and what it is for** | `site-template/`, and most of what the first briefing asked. **Supersedes the first in two places** and says so where it does. |
| **Where the sites get served** | the hosting offer, and whose Cloudflare account a tenant lands in. |

Read in order. Each one narrows the last.

**Almost nothing here is built.** This file exists so that the next session
starts from what has already been said and measured rather than from scratch,
and so that what she has already decided is not re-litigated.

The three documents divide like this. `NODE.md` is **the repository** — what is
at the root and what is in `site/`. `STATION.md` is **the station** — the
machines, the crews, the public-repository rule. This file is **the tenancy** —
who else's sites live here, and what it costs them to be here.

---

## The frame: this is the product, not the plumbing

> This is the nonprofit product, and we are gonna start offering services in
> our community.

That sentence changes the reading of the other two documents. Up to now the
node has been described as *how FCPM keeps its own house* — its engines, its
library, its machines. This says the node is also **what FCPM sells**, in the
nonprofit sense of sells: the thing it offers the community and is funded to
offer.

It is the same motivation `NODE.md` already records, arriving with a customer
attached:

> All we're really doing here is showing everyone how to be self-sufficient
> with more than just a website.

So a design question here is not only *does this work* but *can somebody who is
not us use it*. Those have different answers, and until today only the first
one was being asked.

---

## station-node is the prototype for the shape, and NOT for the role

This is the sharpest correction in the briefing and the one a later reader most
needs, because `STATION.md` can be read as *copy station-node* and this says
plainly that it must not be.

The prototype's own posture, and it is deliberate:

> Station node has a very independent mission to observe itself. It thinks of
> itself as the stranger there at the studio, and that is correct. That's what
> I wanted to feel.

**The stranger is a designed feeling, not an accident to be corrected.**
station-node is Autumn's personal machine standing in someone else's building,
and its independence is the point of it.

And then the limit:

> station node is running on my personal equipment at the studio that FCPM has.
> And so when I prototype things there and use remote workstations and get
> grants to do work tasks on other computers in the studio, those are workflows
> I intend to bring here.

> they're not all gonna look the same. most of them will look the same, but
> they're not all gonna be performing the same roles as station node.

Read those together and the rule falls out:

- **The workflows travel.** Remote workstations, and grant-funded work farmed
  out to other machines in the studio, are named as things to bring over.
- **The mechanisms mostly travel.** *"most of them will look the same"* — so
  the default when copying is to keep the shape, and a divergence should say
  why it diverged.
- **The role does not travel.** A tenant of FCPM is not a stranger in the
  building. It is there by invitation, hosted on purpose, and its reason to
  exist is FCPM's mission rather than its own independent one.

That last point is a genuine design constraint and not a philosophical
flourish. Almost everything station-node does to *observe itself* — the
posture, the watch, the compulsive log — is the behaviour of a party that owes
its findings to nobody. A tenant's equivalents are owed to FCPM *and* to the
tenant, which is a different contract and will produce different code in at
least these places: what gets logged, who may read the log, and what happens
when the tenant leaves.

**Open, and hers:** which of the observation machinery is a tenant entitled to
turn off. It is not answered by *"most of them will look the same."*

---

## The root empties out, and keeps its name

> Right now, we're keeping the repository site name just fine.

The repository stays `fcpublicmedia.org` even as it stops being mostly a
website. Recorded because it will look wrong to somebody later and be right
anyway — and because `STATION.md` already notes the public face is not pinned
to its address (*"It won't matter if we change domain names"*), so the
repository name and the site's domain are now two independently movable things.

> We've moved what we had into a site folder, but we're gonna move more. So
> we're gonna feel mostly empty here. We're gonna have a site folder. We're
> gonna have something that we're gonna talk about. And then there might be
> very basic configuration.

Three slots at the root, then:

| slot | status |
|---|---|
| `site/` | **done.** The move landed 2026-09-17. |
| the tenancy thing | **unnamed.** This is the talk. |
| very basic configuration | **implied, small on purpose.** *"there might be"* is doing real work — it is not certain anything is owed here at all. |

**"Mostly empty" is a target, and the root has moved toward it since this was
written.** When this paragraph was drafted the root held eleven markdown
documents, `api/`, `worker/`, `script/`, `tests/`, `site-template/`, a Gemfile
and four config files. Since then `api/` has been deleted, `script/` and
`tests/` have become `site/bin/` and `site/tests/`, and the documents have moved
into `docs/`. Then on 2026-09-18 the build root became `site/`, and the config,
the Gemfile, the Ruby pin and `wrangler.jsonc` went in with it. What is left at
the root is `AGENTS.md`, `README.md`, `advocate.yml`, and the directories.

*"We're gonna move more"* still stands. Nobody should read the present shape as
settled, in either direction.

---

## The standard is GitHub Pages, and it is a high one

> We're gonna make it feel like with almost no config, you can publish Jekyll
> sites. We're gonna act like GitHub in that way. If you publish to their pages
> product.

> this is because what we're gonna talk about is a multi tenant system.

Naming Pages as the benchmark is more useful than *"easy"* would have been,
because Pages made a specific choice that can be copied or refused:

**Pages puts the defaults in the host, not in the tenant.** A repository with
one `index.md` and no `_config.yml` publishes. Jekyll still needs a full
configuration to run — Pages supplies it, merges the tenant's partial one over
the top, and pins the gem versions itself. The tenant writes only its
divergences.

That is the mechanism *"almost no config"* is asking for, and it is the exact
inverse of what this repository does today, where `_config.yml` is a
hand-written 90-line document full of reasoning.

**Pages is the benchmark for config minimalism ONLY.** The second briefing
settled the build cadence and settled it the other way: Pages builds on push,
FCPM promises a day. See *The crux: a promised cadence, not real time*. Taking
Pages as the model for latency as well would put a per-tenant build trigger into
a system deliberately designed without one.

### What that costs here, measured rather than guessed

From `NODE.md`, which worked this out before there was a reason to:

1. **One `_config.yml`, one `source:`.** A second site is a second config file,
   built with `-c`. So *"almost no config"* is not a claim about Jekyll; it is a
   requirement that **something at the root writes each tenant's config**. That
   generator is the first real piece of the tenancy system, and its input is
   whatever the tenant does declare.
2. **`_site` is one directory.** It becomes several — a destination per tenant —
   and `wrangler.jsonc` names exactly one `assets.directory`, so a tenant with
   its own domain is a second Worker config and a second deploy.
3. **Shared markup must be staged, not symlinked.** Jekyll has no cross-source
   include path. Measured in this repository: a symlinked `_data` directory is
   read by a normal build and **silently ignored** under `--safe`. A staging
   step in `site/bin/` is the option that matches how everything else here works.
4. **`sites/<name>/` is already the reserved name** if tenants live in this
   repository. `site/` is deliberately singular and every path in the docs,
   scripts and workflows now says so.

#### Items 1 and 2 above are superseded, and it got easier

The build root moved into `site/` on 2026-09-18, which made that directory a
**self-contained Jekyll project** — its own `_config.yml`, `Gemfile`,
`.ruby-version` and `wrangler.jsonc`, all read relative to the directory the
build runs in. The list above was written when one config at the repository
root had to serve everything, and two of its four costs simply stopped
existing:

- **A second site does not need a second `-c`.** It is a sibling directory with
  its own config, built exactly the way `site/` is. `site/` stopped being *the*
  site and became *a* site.
- **`_site` is already several.** Each site writes its own, and `wrangler.jsonc`
  is already per-site, which was item 2's requirement rather than its problem.

**And one measurement makes the managed build cheap.** With an explicit
`--source`, Jekyll reads `<source>/_config.yml` rather than one in the working
directory — verified 2026-09-18 by building `site-template/` from `site/`'s
bundle and getting a page titled *"Your Show"*. So **one toolchain builds every
site**: one Ruby, one Gemfile, one lockfile, at the host.

That is the *"defaults live in the host, not in the tenant"* principle turning
up as plumbing. A member's repository needs no Gemfile, no lockfile and no Ruby
pin in order to be built here. `bin/build-sites.py` does this, and
[`sites.yml`](../sites.yml) is the canonical list it reads.

**The generator from item 1 is still wanted** — *"almost no config"* means
something writes a tenant's `_config.yml` from whatever little the tenant
declares. What changed is that it is now only that, rather than also a solution
to a build-plumbing problem.

### And half of it is already built

`site-template/` is a complete Jekyll site, cut as a scaffold rather than an
example, and `site/bin/check-template.py` builds it on every push and reads its
feed back **with this repository's own reader** — because `/feed.xml` is the
entire contract between a member site and FCPM.

More importantly it has already drawn the line a tenancy needs most:

| Upstream owns | Tenant owns |
|---|---|
| `_layouts/` `_includes/` `assets/` `.github/` | `_config.yml` `_data/` content pages |

Updates arrive as `git merge upstream/main --ff-only`, which **fails loudly**
when a tenant has edited the left column — and that failure is the eject
signal, treated as a feature. *"Ejecting should cost them nothing but a
decision."*

**A tenancy that cannot be left is not a service, it is a lock-in**, and this
repository decided that before it had a tenant. Whatever gets built should not
undo it.

---

## What the public-repository rule does to a tenancy

`STATION.md` fixes the constraint: only the encrypted-by-specification path gets
implemented here, because this repository is public and *"if our public rules
hold, there's no risk to checking it out anywhere."*

For tenants that sharpens into something worth stating plainly, because it will
surprise somebody: **hosted tenant repositories are public, so publishing state
is scheduling and never secrecy.** `site-template/README.md` already says so —
`draft` is *"being worked on,"* visible to anyone reading the repo, *"which is
fine — a repo is not a stage."* A tenant who needs genuine pre-release secrecy
ejects, goes private, and keeps submitting a feed.

This is the part most likely to be mis-sold when the product is described to a
board or a member. Say it first, not in the FAQ.

---

## The questions the talk had to answer

Kept as asked, because what was open at the time is part of the record. **Four
of the five were answered within the hour** — see *Which of the questions above
are now answered* at the end of this file.

1. **Is a tenant's site in this repository, or its own?** The two halves of the
   existing design disagree, and both are defensible. *"Site clusters that
   share a build root context"* means `sites/<name>/` here. The template's
   eject story — `upstream` remote, ff-only merge, going private — assumes the
   tenant's own repository, and **GitHub Pages, the named benchmark, does not
   keep your site in GitHub's repo.** It is also possible both are wanted: in-repo
   for FCPM's own surfaces, own-repo for members. That answer decides whether
   the unnamed root folder holds *sites* or a *registry of sites*.

2. **Is "tenant" a site, or a member of the node?** The briefing put remote
   workstations and grant-funded work on other studio machines in the same
   breath as multi-tenancy. Those are machine and crew concerns, not Jekyll
   ones. If a tenant is a party that can hold *a site, a workstation session,
   and a grant*, then tenancy is an identity system that the site publishing
   hangs off — a much larger thing than a build directory, and it would want
   naming accordingly.

3. **What may a tenant switch off?** Per above: the observation machinery is
   station-node's by right and a tenant's by negotiation.

4. **Does the second slot at the root hold tenants, or the machinery?** *"We're
   gonna have something that we're gonna talk about"* is one folder. If tenants
   live in their own repositories, that folder is small and is mostly a
   registry and a generator; if they live here, it is the bulk of the
   repository. The name should follow from question 1, not precede it.

5. **Which of the eleven root documents survive the emptying?** Asked because
   *"we're gonna move more"* was said about code, and the documents are the part
   a new reader meets first.

---

# The factory, and what it is for

Second briefing, 2026-09-17, a few hours after the first. The subject moved onto
`site-template/`, and it arrived with a person waiting on it:

> We have the site template, and it is the focus of what we're talking about
> next. I have someone pruning it, because it's too complicated, but telling
> them to finish that job hinges on what we're gonna talk about.

**So this half of the document has a deadline attached to it that the first half
did not.** The pruning decision is downstream of everything below, and the
section *What the pruner is actually blocked on* names the one question that has
to be answered before that work can finish.

---

## The problem is burnout, and it is not discoverability

This supersedes the framing in `site-template/README.md`, and the difference
matters enough to state before anything else.

The template's README says the problem is **local discoverability** — that a
Fort Collins resident cannot find a Fort Collins producer through YouTube's
recommendations. That is true, and it is not what she said the site is for:

> we know that we have members signing up, and they wanna make a show. And
> they're probably only gonna upload it to YouTube or Spotify. That is what most
> people end up doing if they publish anything at all for that matter.

> If we are looking to solve something, it is the following. When a member comes
> in and has a passionate idea, they can still burn out by not getting the
> support or not having answers or tools that they need when they need it. Our
> mission is to be there when they need it and give them that stuff, but joining
> us doesn't mean that they won't get discouraged. So this still happens.

**The thing being solved is a member losing momentum for want of an answer, a
tool, or support, at the moment they needed it.** Not obscurity. A member who
burns out was not failed by a search ranking.

Two consequences, and they are both load-bearing:

1. **An index does not answer burnout.** A site that is only a local index over
   YouTube is a fine thing and it does not address the stated problem at all. So
   the template cannot be evaluated by *does it make them findable* — it has to
   be evaluated by *does a member who is flagging find something to attach to*.
2. **Discoverability is downstream and explicitly parked.** Her words: *"We can
   separately make a aggregator site out of them, so I'm not worried."* The
   aggregator is a later, separate build, and it is not a constraint on the
   factory. Nothing in the template needs to be designed around it.

The answer to burnout turns up later in the same briefing, in the services
section, and the two halves join there. Read *The hook is the product* below
before deciding this section is only philosophy.

---

## A project is a repository, and a member may hold several

> I think what we can do is allow members to have multiple properties that might
> be shows that they run. And the way that the dividing line would fall on those
> is separate websites if they want those.

> But **a project is a repository here.**

The tenancy unit is the **project**, not the member. A member is a party who may
hold several, and the dividing line between them is *a separate website, if they
want one* — which means one member with three shows is three repositories if
they ask for that, and one if they do not. The member decides where the line
falls, not us.

---

## ANSWERED: a tenant's site is its own repository, mounted here as a submodule

This is the first briefing's question 1, and it is settled. **`sites/<name>/`
does not happen.** `NODE.md` reserved that name for the case where tenants live
in this repository; that reservation is now spent, and the reasoning it was
based on — *"site clusters that share a build root context"* — is satisfied a
different way.

> when I make websites for people, what I'm talking about is adding their new Git
> repository as a submodule inside of our trade area.

> these are submodules that we might hydrate in something to build them, but
> they don't all have to be there. But **it is a canonical list, and it is backed
> in by the repository.**

> The site template is trying to add a new managed repository to its collection,
> and it would be in the library section.

Three properties, and all three are already how the node's library behaves:

| she said | the library already does this |
|---|---|
| *"we might hydrate in something to build them"* | the library **fills nothing eagerly** — a holding is a reference until a session asks for it by name |
| *"they don't all have to be there"* | an unfilled gitlink is the normal resting state, not a broken checkout |
| *"a canonical list, backed in by the repository"* | the gitlink **is** the list; it is version-controlled, reviewable, and cannot drift from what is committed |

**That is a finding worth more than it looks.** The hydrate-on-demand behaviour
that a site factory needs is not new work — it is the library engine's existing
rule, and it is the concrete reason the library engine is the right mount for
this rather than a bespoke registry. Note also the standing hazard from
`~/.claude/CLAUDE.md`: **a submodule never says it is stale.** A canonical list
of tenant pins will report a clean tree while every pin is months old, so the
factory needs an explicit staleness report from day one. Nothing else will say
it.

### The library is the second slot at the root

This also answers the first briefing's question 4. The unnamed *"something that
we're gonna talk about"* is **`library/`** — she placed the submodules in *"the
library section"* and said *"We can keep them in our station like library."*
There is no third folder.

> We have a plan to take the library engine like it appears in station node and
> bring it here. **We're not gonna have their library, though. We're gonna have
> our own.** And some of it is just project scratch space for the other things
> we're gonna do.

Consistent with `STATION.md`: the library arrives here **mounted as branches
rather than a folder on `main`**, and FCPM starts that way rather than migrating
to it.

### Which categories things land in

The first concrete assignment anyone has made of the library's reserved category
words for FCPM:

> this site generator is making products that fall in the **trade** category,
> but the content itself is **media**, which means that it is set loose on
> purpose for people to find.

> the websites we're launching for them are trade entity websites. They're not
> necessarily selling anything, but they're not, like, specifically doing
> broadcasting yet. Like, broadcasting is something that they go accomplish, and
> they're embedding it in this site.

So: **the site is a trade object; what plays on it is media.** A site is not
broadcasting — broadcasting is something the member goes and accomplishes, and
the site is where it gets embedded afterwards.

**This does not close escalation `9605`**, which asks for the board's own
decisions about what public media offers under the reserved categories. It does
mean two of the categories now have a worked example from her side, which is
more than G4 had this morning.

---

## One mechanism, three populations

The cleanest simplification in the briefing, and it should be built this way
rather than discovered later:

> shows that are ejected simply just have to be submodules by us. Still pointing
> to it.

> talking about those ejected items is identical to talking about any individual
> product who never wanted to start with us at all. But they are affiliated. They
> wanna be on the list. We're not publishing their site, but they are
> enumerated. That is also okay.

| population | in the list | do we build it |
|---|---|---|
| **managed** | yes | yes |
| **ejected** — took the site somewhere of their own | yes | no |
| **affiliated** — never wanted a site from us at all | yes | no |

**There is one list and one kind of entry.** The difference between the three is
a single flag: *do we build this one*. Anything that models them as three
registries, or ejection as a departure rather than a flag change, is more
complicated than what was asked for and will be wrong about the third case —
which has no ejection event to key off, because it never started here.

She also floated extending the pattern, and flagged it as speculative herself:

> We might find reasons to use this pattern just to make more specific types of
> pointers like alumni projects that are not running anymore, so we get them out
> of the way. There's probably better ways to handle it than that, but you can
> imagine.

Recorded, not designed.

---

## We own nothing, and delisting is the whole withdrawal

She corrected herself mid-sentence here, and the correction is the point:

> Staying in here, I think just means listing amongst our properties — which I
> said that a little strong. It's not really our properties at all. **In fact, we
> own nothing.**

> the media that we produce, we're trying to showcase it. It's just that they
> absolutely have the right to not have us blob about them doing their marketing
> or anti marketing as they might see it. **They have the right to ask us to not
> do anything at all.** And so that just means removing it from our list here.

So the withdrawal path is **one removal from one list**, and it has to be
complete. That is a promise about behaviour, which makes it checkable, and it is
worth checking now rather than on the day somebody asks.

### Measured: what removal from the list does today, and what it leaves

The existing member-feed pipeline is the closest thing to this that is actually
running. `site/_data/feeds.yml` is the list; `site/bin/sync-feeds.py` reads it
daily and commits `site/_data/member_programs.json`.

- **Removing an entry from `feeds.yml` does drop their items.** Carry-forward is
  keyed per source and only runs for sources still in the config, so a removed
  source contributes nothing and carries nothing. Verified by reading
  `collect()` — it iterates the configured sources, and the carry branch is
  inside that loop.
- **It takes up to a day.** The sync is on a `0 12 * * *` cron. The `push`
  trigger is scoped to `site/_data/feeds.yml`, so editing the list *does* kick a
  run immediately — which means the honest answer is "within minutes if someone
  commits the removal, otherwise by tomorrow morning."
- **Carry-forward is the trap, and only in one direction.** It exists so a
  member's work does not vanish when their host has a bad morning. But a member
  who withdraws by *taking their own feed down* rather than telling us looks
  exactly like a transient outage, and their items are deliberately kept. That
  is the safety feature working as designed and producing the wrong outcome.
  **Withdrawal has to be an act on our list, not on their server** — and we
  should say so to members, because the intuitive move is the one that does not
  work.
- **Git history keeps it regardless.** The committed JSON is in every clone
  forever. That is not fixable and should not be sold as fixable; it should be
  said plainly up front.

### Going private

> If they take their thing private, we can unhook. If they take it private, but
> they want us to stay in, we can arrange that. We'll get to that part.

Deferred by her. Recorded because a submodule pointing at a private repository
does not clone for anyone else, so *unhook* is the default that happens whether
or not it is chosen. The template README already names the mechanism for the
other case — a GitHub App on their repository keeps reading the feed after they
go private.

---

## The crux: a promised cadence, not real time

> When I deploy the sites, they can individually deploy with workflows, but I
> don't need them to have all of that by default. It could be the managed
> workflow situation, more managed code.

> I don't want to create a situation where these sites break frequently, and
> therefore the build pipelines are just, like, hundreds of reds. No one is gonna
> know what to do in that case.

> we need to understand that when we build, probably a managed build, and so
> we're building kinda all at once. That's not ideal, but for the stuff that
> we're managing, it's exactly what you would expect from someone in our
> position — in the world where updates come slow, and you just have to be
> patient, and so it's fine.

> And so **we promise a cadence that we can meet instead of real time, which is
> the crux of it all.** We wanna be able to say, hey, we can do it like weekly.
> Or just let people pick their day. It could be every day, but you have to pick
> one.

### This corrects the first briefing, and the correction is easy to miss

The first briefing named **GitHub Pages** as the benchmark. Pages builds **on
push**. FCPM promises **a day**. Those are opposite answers to the same
question, and conflating them would put a per-tenant build trigger into a system
that was explicitly designed not to have one.

**Pages is the benchmark for config minimalism only** — defaults in the host,
divergences in the tenant. It is emphatically *not* the benchmark for latency.
`TENANCY.md` now says so in both halves on purpose.

### What a cadence buys, stated plainly

- **One red badge, in one place, owned by us.** This is the reason she gave, and
  it is the right one. N tenant workflows produce N failing badges on N
  repositories belonging to N people who cannot fix them and will not look.
- **A promise that can be kept.** *"Updates come slow, and you just have to be
  patient"* is not an apology — a small organisation that promises Thursday and
  delivers Thursday is more trustworthy than one that promises instant and
  delivers most of the time.
- **A tenant repository needs no `.github/` at all.** That falls straight out,
  and it is most of the pruning license.

### The hazard the phrase "all at once" carries

*"We're building kinda all at once"* means one broken tenant is in the same run
as every healthy one. **Per-tenant isolation inside the batch is not optional**
— a tenant whose `programs.yml` will not parse must fail alone, publish nothing
new, and leave the other sites' output untouched and published. A batch that
goes red as a unit converts one member's typo into an outage for everybody, and
it would do it on the promised day, which is the worst possible timing.

Also worth flagging as a question rather than a finding: *"let people pick
their day"* is per-tenant, and *"building kinda all at once"* is one house
cadence. Both are reasonable and they are not the same system.

---

## What the pruner is actually blocked on

This is the section to read first if you are the person pruning
`site-template/`. The template is ten files today:

```
_config.yml  _data/site.yml  _data/programs.yml  feed.xml  index.html
_layouts/default.html  assets/css/site.css  Gemfile  .gitignore  README.md
```

Given a **managed, centrally-run build on a promised cadence**, most of that
does not need to be in a member's repository at all:

| file | after this briefing |
|---|---|
| `.github/` | **not needed.** There is none today; do not add one. FCPM builds. |
| `_config.yml` | **generated.** First briefing: something at the root writes each tenant's config. Not the member's file to maintain. |
| `Gemfile` | **only for local preview.** No longer load-bearing for publishing. |
| `_layouts/`, `assets/css/` | **stageable.** A central build can inject upstream-owned markup at build time; it does not have to live in the tenant repo. |
| `feed.xml` | **generated by whoever builds.** While managed, that is us. |
| `_data/site.yml`, `_data/programs.yml` | **the actual tenant surface.** Keep. |

Follow that all the way down and a managed tenant repository is **two YAML files
and any content pages** — which is almost exactly her other wish, *"if we can
get things done with just a configuration."*

### And here is the conflict nobody has resolved

**The prune and the eject story pull directly against each other.**

`site-template/README.md` promises *"Ejecting should cost them nothing but a
decision."* That promise is currently kept by the member's repository already
containing everything needed to build the site alone. **Every file the prune
removes is a file FCPM supplies — and therefore a file the member does not have
on the day they walk out.** Prune it to two YAML files and ejection stops being
a decision and becomes a migration.

Three ways out, and **the choice is hers**, because it is a promise about how
FCPM treats people and not a technical preference:

1. **Eject injects.** Prune hard; the eject step writes the layouts, config,
   Gemfile, feed and a workflow back into their repository as a commit. Ejection
   stays one decision, and it stays cheap, at the cost of a real piece of
   tooling that has to keep working.
2. **A prune floor.** The tenant repo keeps whatever it needs to build
   standalone, and the prune only removes what is genuinely redundant. Cheapest
   to build, and it caps how simple a member's repository can ever look.
3. **Ejection is honestly not free.** Say so, and drop that line from the README.
   Defensible, and it costs the thing she liked about it — that leaving should be
   *"easy, unembarrassing."*

**Option 1 is the one that matches everything else she said** — *we own nothing*,
delisting is complete, leaving is unembarrassing — and it is the only one that
survives pruning the template to a configuration. It is also the only one with
unbuilt tooling in it, which is why it should be chosen on purpose rather than
by default.

Until that is answered, the honest instruction to the person pruning is: **cut
anything that only exists to serve a per-tenant build** (that is the whole
`.github/`-shaped question and it is now settled), and **stop at `_layouts/`,
`feed.xml` and `Gemfile`**, because those three are exactly the files whose
removal is a decision about ejection rather than about tidiness.

---

## The hook is the product

Where the burnout framing and the services join up. Recorded in her order,
because the order is the argument.

**The drive that exists today:**

> There is a Samba network drive with eight partitions right now that was me just
> firing up about four gigabytes each — little mailboxes for files. They don't go
> anywhere, but people could stick them there and easily access them from any of
> the computers if they turn on the Wi-Fi. So it's a way to send files out to
> someone in those rooms, and it's a way for the people in those rooms to send
> files back in. It is perfectly reasonable that that is a network storage thing.
> It probably shouldn't be a thumb drive, but it is. Right now, we're okay.

**Where files go when they stop being mailboxes:**

> if I wanted to evict files from that network drive and bring them for
> processing, they would come to **the library in our node configuration layout
> of it.**

> we may find a reason to use our **media folder to stage things** that have to go
> to Dropbox or that have to go to different locations.

**The services are intention-shaped, not tool-shaped:**

> what we're trying to offer services to support — like why the file is coming to
> us at all and going out somewhere — it's based on **their intention**. Do they
> want to stem this audio for parts? Do they want to enhance the audio? Do they
> need to enhance video? What do they need to do? And so these are service
> questions that FCPM is asking **as a trade entity**.

**And this is the answer to burnout:**

> We will be able to offer services to let people do some self-service. And also,
> while they're in the studio, just kinda get automatic things done. They don't
> need someone to come in and help them enhance the audio. They can just do it
> when they have **more obvious places to attach their hook and catch the ride**,
> get some stuff done.

Put beside the first section: a member burns out *for want of a tool or an
answer at the moment they needed it*, and the cure is a place to attach a hook
without waiting for a person. **The website is not the product. The hook is.**
The site is where a member's work becomes addressable enough for a service to be
offered against it — which is why the factory matters, and also why a factory
that only produces pretty index pages would miss the point entirely.

It also sharpens what the intention vocabulary has to be. *Stem this for parts*,
*enhance the audio*, *enhance the video* are **requests a member makes**, not
pipelines an operator configures. Naming them the member's way is the whole
difference between self-service and a form that gets emailed to staff.

---

## Runner mode

New named concept, deferred by her, recorded so the name does not get reinvented:

> I want it to feel like that little network drive is being watched by one of our
> two bay computers, and they both might be running a copy of our repository, by
> the way, **in this runner mode**, which is what we're talking about here.
> **We're becoming active.** We are recognizing that when the active stuff is
> happening, that there's a CPU underneath it, that it can do stuff. And **they
> might know about each other**. So we're gonna talk about that stuff too, in due
> time.

Three things it connects to, all of which are already written down:

- **`STATION.md`: *"its job isn't so much to own everything as it is to own what
  it means to be on a machine."*** Runner mode is that sentence with a verb. Two
  checkouts is the expected case, and now they have work to do.
- **The plural crew that nobody has built.** *"They might know about each
  other"* is the unimplemented half of `crew.yml` — a roster per machine, and
  two machines that are aware of one another.
- **The workload board.** `abl-workload` exists precisely so that a machine
  holding the box for twenty minutes says what it is doing. *"There's a CPU
  underneath it"* plus an unattended studio is exactly the case that log was
  built for — and `STATION.md` already notes the board is arguably a node
  concern rather than a personal one.

Deferred *"in due time"*, and it should stay deferred. Nothing about the site
factory needs it.

---

## The engine question, contemplated and not settled

> this is a problem that I'm only gonna solve once, but I want other people to do
> it too. **So it's a lot like the engines.**

> However, I am contemplating for the first time if this problem doesn't need a
> full blown engine because **it's mostly just gluing things together**. What if
> what we're dealing with here is a **general purpose engine** — something that
> factorizes anything, as it were. I don't necessarily need it to factorize. You
> understand?

> I've been trying to think of another use case to bundle with this, but so far,
> I don't have one. So **we might wind up not implementing a general purpose thing
> yet and graduate what we make into it**, because the truth is I haven't
> prototyped it. And I don't know what all I wanted to do, and so I can't talk
> enough about it.

### What that amounts to, as an instruction

**Build the specific thing. Graduate it later.** Her reasoning is complete and
it does not need help: there is one use case, she has not prototyped it, and a
general engine with one consumer is a guess wearing a framework. The phrasing to
hold on to is *"graduate what we make into it"* — the specific thing should be
built so that generalising it later is a refactor rather than a rewrite, which
mostly means keeping the glue in configuration and out of code.

### The one hard requirement she did state

> if there were some sort of — you know, when it declares its residency, a
> general one declares its residency, **it must have the opportunity to do that**.
> And so it could say everything it has to. And it would mean that **if you
> wanted multiple things done that way, it could all appear there**.

**A general-purpose engine's residency declaration has to be plural**: many
declarations under one mount, all visible in one place, because a general engine
is by definition doing several unrelated jobs for the repository it sits in.

This is the third consumer to ask the residency vocabulary for something it does
not have, and the three are close enough that they may be one gap:

| asked by | asks for |
|---|---|
| `STATION.md`, library engine | *"declares its own residency, but as an owner"* — an engine that owns what it factors |
| `STATION.md`, library engine | *"It should be allowed to make multiple libraries"* |
| here, a general engine | many declarations under one mount, all appearing together |

All three are **plurality and ownership** in a vocabulary that today describes
one resident asking for one allocation. Worth filing upstream as one observation
rather than three, once she has decided whether the general engine is real.

### And the symmetry worth keeping

> if we can think of a way to glue them together with just a configuration, which
> is essentially what I'm talking about — if we can get things done with just a
> configuration, that is interesting.

The first briefing asked for *"almost no config"* for a **tenant**. This asks for
*"just a configuration"* for the **engine**. Same wish, two layers, and they
reinforce each other: an engine that is mostly configuration is one whose tenants
can be too, because there is no code in the middle insisting on its own inputs.

**One unfinished thought was retracted during this briefing** — *"Let me scratch
that"* — and its content is deliberately not carried here. Noted only so a later
reader knows something about serving remains unsaid rather than assuming the
transcript is complete.

> But there are many facets, so I'm gonna let this message land.

---

# Where the sites get served, and whose account that is

Third briefing, 2026-09-17, short and structural. `Cloudflare Flair pages` is
de-garbled to **Cloudflare Pages** — see *the product names do not agree* below,
because this repository does not actually use that product and the difference
turns out to matter.

> What I'm really talking about is the SaaS component of me offering by default,
> building and releasing into Cloudflare Pages on my **anecdote dot channel
> constellation**. But **if they buy a domain name, it can show up here.** We
> don't necessarily have to put it on anecdote constellation. It could go into
> Fort Collins public media account. Right? **I'm not trying to take their
> stuff.** But I think we want the SaaS thing. And I think my account needs it.
> But we'll talk about migrating FCPM's resources to another account because
> we're dealing with it so far.

`anecdote.channel` is the constellation the engines already come from —
`advocate.anecdote.channel` is mounted here, and `library.anecdote.channel` is
the one whose reserved category words `ADVOCATE.md` already quotes. So the
default hosting namespace and the engine namespace are the same place.

---

## A purchased domain is the account boundary

Two deployment homes, and the thing that moves a site between them is not a
tier, a policy or a conversation:

| where the site lands | when |
|---|---|
| **her account**, under the `anecdote.channel` constellation | by default. This is the SaaS offer. |
| **FCPM's own account**, on the member's domain | *"if they buy a domain name"* |
| nowhere — we do not build it | ejected, or affiliated-only |

**That is an unusually clean mechanism and it should be kept.** The thing a
member pays for is the thing that moves their site out of the default account.
Nothing has to be administered, nobody has to be told they have outgrown the
free tier, and there is no case-by-case judgement about who deserves what. The
purchase *is* the signal.

It also means the tenancy list from the second briefing gains a third field.
It was *in the list* and *do we build it*; it is now **in the list**, **do we
build it**, and **where does it land**.

*"It can show up here"* is read as FCPM's Cloudflare account rather than this
repository, because she names that account in the next breath. Worth confirming
if anything gets built on it.

---

## "I'm not trying to take their stuff" — and the architecture already honours it

This is the sentence a member would most want to hear, and the second briefing
already made it true rather than merely intended.

**The account is a deployment target, not a system of record.** Because a
project is the member's own repository and FCPM holds only a submodule pin,
hosting a site in her Cloudflare account confers nothing on her:

- the canonical bytes are in a repository the **member** owns;
- FCPM's claim on it is one gitlink, and removing that gitlink is the whole
  withdrawal;
- moving the site to a different Cloudflare account is a **deploy-target
  change** — rebuild the same source, point it somewhere else.

So defaulting to her account is safe rather than presumptuous, and it is safe
*because of a decision already made*. The usual failure mode of a hosted offer
is that the platform ends up holding the content, and leaving means extracting
it. Nothing here holds anybody's content. Say that to a member in those words;
it is the strongest thing this design has to offer them.

**The corollary is the honest one:** hosting in her account means FCPM does not
control where its members' sites are served from either. That is the argument
for the migration she deferred, and it is a succession question rather than a
trust question — *"we own nothing"* cuts both ways. It is also a small one, for
exactly the reason above: no data is at stake, only a deploy target.

---

## Migrating FCPM's resources: deferred, and what it will touch

> we'll talk about migrating FCPM's resources to another account because we're
> dealing with it so far.

Deferred by her. What the repository already says about the ground it will land
on, measured rather than assumed:

**Production does not deploy from a workflow.** It deploys from **Cloudflare's
own git integration**, which builds on every push to `main` using
`wrangler.jsonc`. There is no second path: a `workflow_dispatch`-only fallback
existed until 2026-09-17 and was removed — *"we don't wanna get confused about
that"* — so the git build is the only thing that publishes this site.

**The removed workflow left behind one lesson this migration will walk straight
into.** It was manual-only by deliberate design, and its header said why:

> IT IS MANUAL-ONLY SO IT CANNOT DOUBLE-DEPLOY. […] An earlier version of this
> ran on `push` and was kept harmless by the token being absent — which made an
> ordinary act, adding an organization secret, into a way to start publishing
> the same site twice without meaning to. **Safety that depends on a credential
> NOT existing is not safety; it is a landmine with a note on it.**

A two-account factory is *exactly* the thing that adds credentials to an
organisation secret. **The hazard that workflow disarmed must not be rearmed by
the factory.** Whatever deploys tenants needs its account selection to be
explicit per tenant, and a trigger that cannot fire twice for one site.

**The multi-account case is already half-anticipated.**
`CLOUDFLARE_PAGES_TOKEN` is an **organisation** secret, and
`CLOUDFLARE_ACCOUNT_ID` is documented as *"only needed when the token can see
more than one account"* — so the configuration has a slot for this and nothing
uses it yet.

**This is the `vendors` seat's G2 arriving from a different direction.** That
goal asks for *a recorded decision about deploying twice, to Azure and to
Cloudflare, rather than it continuing by default*. PR #74 took `api/` down and
[`deploying.md`](deploying.md) now names Cloudflare as the live path outright,
which settles the Azure half. The account question is the same subject: where
this organisation's deploys live, decided rather than inherited. The
`credentials` seat gains a second account to date and rotate.

### The product names do not agree with the product

She said Pages. This repository deploys a **Worker with static assets** —
`wrangler.jsonc` has no `main`, and its own comment says *"This is a static
site: no main, no runtime, nothing to execute."* Yet the secrets are named
`CLOUDFLARE_PAGES_TOKEN` and `CLOUDFLARE_PAGES_PROJECT`.

**And the choice is already made, by Cloudflare.** From
[`deploying.md`](deploying.md):

> Cloudflare now creates new projects as **Workers** rather than Pages, and the
> two behave differently at deploy time. This repository is set up for the
> Workers flow, which is what you get by default today.

So *"release into Cloudflare Pages"* is the older name for what will actually
happen. The factory should standardise on the Workers flow — it is the default,
it is what the flagship site is proven on, and picking Pages would mean opting
out of what Cloudflare hands you. **The `CLOUDFLARE_PAGES_*` names are legacy
and should be corrected**, because a secret whose name says Pages is how
somebody eventually configures the wrong product.

Either way this stays true, and it was already in the second briefing:
`wrangler.jsonc` names exactly one `assets.directory`, so **N tenants is N
configs and N deploys** whichever product is chosen.

---

## The zone question mostly dissolves, and this repository already proved it

An earlier draft of this section treated *"if they buy a domain name"* as
raising a hard question about **who holds the DNS zone**, on the assumption that
Cloudflare couples the serving account to the zone. **It does not, and this
repository has already measured that.** From [`deploying.md`](deploying.md):

> **The CNAME is enough.** Cloudflare issues a real certificate for
> `new.fcpublicmedia.org` even though it is not authoritative for the zone, so
> this needs no zone transfer, no nameserver change, and no move of the domain
> registration. That is worth stating plainly because the opposite is easy to
> assume and would turn a DNS record into a migration.

FCPM's own live site runs exactly this way today: Wix holds DNS for
`fcpublicmedia.org`, and `new.fcpublicmedia.org` is a CNAME in Wix's DNS
pointing at a `workers.dev` hostname, with a real certificate.

**So the good outcome is the default one.** A member buys a domain, keeps the
registrar and the DNS wherever they bought it, and points one CNAME at the site
we build for them. Nobody has to hold a zone on their behalf, nothing has to be
transferred, and the party who can point the domain somewhere else is the party
who paid for it. That is *"I'm not trying to take their stuff"* holding without
anyone having to be careful about it.

**Two things follow that are worth saying out loud.**

1. **A purchased domain does not technically force the account move.** She
   described the domain as the thing that lands a site in FCPM's account, and as
   a *policy* that is clean and worth keeping — but DNS is not what makes it
   necessary, because a CNAME works across accounts. So the boundary is a
   deliberate choice about billing, custody and which organisation's dashboard
   holds the project, not a constraint. Better to know that before something
   gets built around a requirement that is not there.
2. **A member who never buys a domain gets a `workers.dev` hostname or an
   `anecdote.channel` subdomain**, and in that case the party who can take the
   site off the internet is her. That is the actual residue of the zone
   question, it is small, and it is the same succession point as the account
   migration above rather than a separate one.

---

## Does this give the general engine its second consumer?

The second briefing's reason for *not* generalising was specific and it was the
absence of a second case:

> I've been trying to think of another use case to bundle with this, but so far,
> I don't have one.

And now:

> I think we want the SaaS thing. **And I think my account needs it.**

**That sentence has two readings and they give opposite answers.** One sentence
from her settles it; nothing should be built toward either in the meantime.

1. **`anecdote.channel` is only the default namespace** — the place FCPM's
   member sites happen to land, because she already has the account and the
   constellation. Then there is still one use case with one deployment, and
   *build the specific thing and graduate it later* stands exactly as recorded.
2. **`anecdote.channel` wants a factory of its own** — her constellation
   publishing its own properties through the same machinery, for her own
   reasons. Then there are two consumers, in two organisations, with different
   tenants and different accounts. That is the second case she went looking for
   and could not find.

Reading 2 also fits the shape of the requirement she stated last time: it makes
the **account a configuration value rather than a constant**, which is the same
move as a residency declaration that has to be plural. That consistency is
suggestive and it is not evidence. *"My account needs it"* is at least as
naturally read as *I want this offer to exist on my account*, which is
reading 1.

**Recommendation: assume reading 1 and build for it.** It is the cheaper
assumption, it is what she said last briefing, and reading 2 is reachable from
it by making one constant into a setting — which is precisely what *"graduate
what we make into it"* asks for.

---

## Where every question now stands

| first briefing asked | now |
|---|---|
| **1.** Tenant site in this repo, or its own? | **ANSWERED.** Its own repository, mounted as a submodule under the library's `trade` area. `sites/<name>/` does not happen. |
| **2.** Is "tenant" a site, or a member of the node? | **PARTLY.** The publishing unit is the **project** — *"a project is a repository here"* — and a member may hold several. The machine axis got its own name, **runner mode**, and was deferred. |
| **3.** What may a tenant switch off? | **STILL OPEN.** Not touched by the second briefing. |
| **4.** Does the second root slot hold tenants or machinery? | **ANSWERED.** It is `library/`, mounted as branches, and the tenant pins live in it. There is no third folder. |
| **5.** Which root documents survive the emptying? | **BEING ANSWERED ELSEWHERE.** PR #76 moves them into `docs/`. |

### And what the second briefing opened

1. **The prune floor versus the eject promise.** The pruner is blocked on it.
   Three options above; option 1 matches everything else she has said.
2. **Per-tenant cadence versus one house build.** *"Pick their day"* and
   *"building kinda all at once"* are not the same system.
3. **Withdrawal has to be an act on our list.** A member who withdraws by taking
   their own feed down looks like an outage, and carry-forward keeps their work
   up. Members should be told the working way to leave.
4. **Per-tenant isolation inside the managed batch.** One member's typo must not
   miss the promised day for everybody.
5. **Staying listed while private.** Deferred by her, but *unhook* is what
   happens by default whether it is chosen or not.

### And what the third briefing opened

1. **Is `anecdote.channel` the default namespace, or the general engine's second
   consumer?** One sentence settles it. Recommendation above: assume the former.
2. ~~Who holds the zone when a member buys a domain.~~ **Closed on reading
   [`deploying.md`](deploying.md)**: a CNAME from DNS held anywhere gets a real
   certificate, so the member keeps their registrar and their zone and nothing
   has to be transferred. It also means a purchased domain does not *force* the
   account move — that boundary is a policy worth keeping, not a constraint.
3. ~~Pages or Workers-with-assets.~~ **Closed the same way**: Cloudflare creates
   new projects as Workers now, which is what this repository already runs.
   Standardise on it, and correct the legacy `CLOUDFLARE_PAGES_*` names.
4. **The double-deploy landmine must not be rearmed.** A two-account factory is
   exactly the act that the removed manual workflow had to be trigger-guarded
   against. The workflow is gone; the hazard returns with the factory.
5. **Migrating FCPM's resources to its own account.** Deferred by her, and it is
   the `vendors` seat's G2 arriving from a different direction.

---

## Orientation note, not part of the briefing

`.advocate-engine` is pinned 5 commits behind its `origin/main` as of
2026-09-17. Reported, not bumped: a pin bump is a change to this repository
and gets its own pull request saying which merges ride along.
