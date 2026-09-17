# The multi-tenant turn

Written 2026-09-17 from **two** spoken briefings by Autumn, the same day as
[`STATION.md`](STATION.md) and [`NODE.md`](NODE.md) and continuous with them.
**Every quotation is dictated speech**, lightly de-garbled where speech-to-text
mangled a proper noun (`Jecal` → Jekyll) and not otherwise.

The first briefing set the frame and left the central thing unnamed. The second
one — *The factory, and what it is for*, below — answered most of what the first
one asked and moved the subject onto `site-template/`. **Read both; the second
supersedes the first in two places and says so where it does.**

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
into `docs/`. What is left is `CLAUDE.md`, an empty `README.md`, `Gemfile`,
`_config.yml`, `advocate.yml`, `wrangler.jsonc`, and four directories.

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

## Which of the questions above are now answered

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

---

## Orientation note, not part of the briefing

`.advocate-engine` is pinned 5 commits behind its `origin/main` as of
2026-09-17. Reported, not bumped: a pin bump is a change to this repository
and gets its own pull request saying which merges ride along.
