# The multi-tenant turn

Written 2026-09-17 from a spoken briefing by Autumn, the same day as
[`STATION.md`](STATION.md) and [`NODE.md`](NODE.md) and continuous with them.
**Every quotation is dictated speech**, lightly de-garbled where speech-to-text
mangled a proper noun (`Jecal` → Jekyll) and not otherwise.

**Nothing here is built, and the central thing is not yet named.** Her words:
*"we're gonna have something that we're gonna talk about."* This file exists so
that the talk starts from what has already been said and measured, rather than
from scratch — and so that the part she has already decided is not re-litigated
when it does.

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

**"Mostly empty" is a target, not a description.** The root currently holds
eleven markdown documents, `api/`, `worker/`, `script/`, `tests/`,
`site-template/`, a Gemfile and four config files. *"We're gonna move more"*
means that list is expected to shrink, and no session should read the present
clutter as the settled shape.

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
   step in `script/` is the option that matches how everything else here works.
4. **`sites/<name>/` is already the reserved name** if tenants live in this
   repository. `site/` is deliberately singular and every path in the docs,
   scripts and workflows now says so.

### And half of it is already built

`site-template/` is a complete Jekyll site, cut as a scaffold rather than an
example, and `script/check-template.py` builds it on every push and reads its
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

## The questions the talk has to answer

Written as questions because they are hers, and because each one changes what
gets built rather than how.

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

## Orientation note, not part of the briefing

`.advocate-engine` is pinned 5 commits behind its `origin/main` as of
2026-09-17. Reported, not bumped: a pin bump is a change to this repository
and gets its own pull request saying which merges ride along.
