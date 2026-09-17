# What this repository is when it is not a website

Written 2026-09-17 from a long spoken briefing by Autumn. **Every quotation
below is dictated speech**, lightly de-garbled where speech-to-text mangled a
proper noun and not otherwise. Where a sentence of hers decides something, it is
quoted rather than summarised, because the summary is the part that rots.

Nothing here is built. Nothing here mounts an engine, adds a submodule or moves
a pin — each of those is its own pull request by whoever owns it. This is the
posture, written down while it is fresh, so that the member-site factory and
everything after it start from findings instead of from a conversation nobody
can find.

Companion documents: [`NODE.md`](NODE.md) for the shape of the repository
itself, and [`DESIGN-NOTES.md`](DESIGN-NOTES.md) for the services this posture
is *for* — the digitization station and workstation sign-in are written up
there. [`TENANCY.md`](TENANCY.md) came from a later briefing the same day and
**limits this one**: the workflows here travel to FCPM, but station-node's
stranger-at-the-studio role explicitly does not travel to a tenant.

---

## The prototype is a real machine, and it is already in the building

> Station node is my personal computer. It is inside the FCPM studio.

That is the fact that makes all of this concrete rather than aspirational. The
node being copied from is not a design document; it is a workstation sitting in
the studio, taking a deliberate posture:

> [It] tests how it could use stations on the LAN — little editing bays, Fort
> Collins Public Media — to render video cooperatively. This is the kind of
> thing that FCPM ought to be able to do for itself. I'm using it for whatever
> reason. I want them to use it for whatever reason.

**DiscoveryWritten uses station-node to represent itself**, and it is positioned
to prototype how to use the equipment. FCPM does the same thing for its own
reasons. The two are not the same organisation and the node is not shared; the
*shape* is what travels.

**There is no FCPM station-node machine yet, and that is deliberate.**

> Presently, we don't have a machine that would be an FCPM station node. And so
> we are avoiding that part of it so far. This is a GitHub repository more than
> anything right now.

So nothing in this document should be read as waiting on hardware. The
repository can carry the posture before any machine runs it, and the parts that
need a machine are named as such.

---

## This repository is public, and that is the design constraint

> This is a public repository. And we're only going to implement things here
> that match the clean specifications that we set out where there is
> encryption. I said in antibody tooling that it would be okay if your
> repository was public. FCPM is that case now.

FCPM is the worked example of a claim the antibody tooling has been making all
along. That makes the public-repository rule a **standing constraint on what
gets implemented here**, not a warning label:

- **Only the encrypted-by-specification path gets built here.** If a capability
  only works by keeping a secret in the repository, it does not go in this
  repository. It waits for the specified form, or it lives somewhere else.
- **The station-node configurations do not come with it.** Those exist so that
  people Autumn hires can use her workstation, and so work can be split up and
  granted securely to other workstations. They are private clients integrated
  into tools. *That* capability — splitting work and granting it securely to
  other workstations — is wanted here. The configurations are not.

### What the constraint buys immediately

> If our public rules hold, there's no risk to checking it out anywhere, in
> fact.

That is the payoff, and it is large. Any machine this is checked out to becomes
a backup — editing bay two is already empowered to do a couple of things, such
as scheduling the Cablecast material. A repository that is safe to clone
anywhere is a repository that does not need a custody plan.

**It also means the public rules holding is load-bearing.** The moment something
lands here that would be wrong to clone onto an editing bay, that whole property
is gone and nothing announces it. Anything added under this posture should be
checked against that sentence before it is written.

---

## The website keeps working the entire time

> The website needs to build and serve and just keep doing exactly what it was
> doing all along. The rest of this is going to be under construction while the
> public face is up.

This is the rule that makes everything else safe to attempt. The grant system
and the services become **a background concern to the website**, not a
refactor of it.

> It won't matter if we change domain names. It's not a problem. It doesn't
> matter.

Worth recording because it settles a question that would otherwise stall
things: the public face is not pinned to its current address, so nothing under
construction has to be designed around preserving one.

---

## Its job is to own what it means to be on a machine

The sharpest sentence in the briefing, and the one that should shape the code:

> The truth is we might be running two of this at once. That means this
> repository may be checked out on editing bay one and two. It might be running
> on both of them, which means that its job isn't so much to own everything as
> it is to own **what it means to be on a machine**.

A repository that assumes it is the only copy will be wrong here on day one.
Two live checkouts is the *expected* case, not a degraded one.

### Crews, and why this is an interesting step

> Because there are two machines, it means that there might be two profiles.
> We've been talking about profiles as more of a — we call them crews. They're
> not fully implemented as being multiple, and so that's why this is an
> interesting step for us.

**Crews are documented but not implemented as plural.** FCPM is the case that
forces the plural, which makes this repository a genuine consumer of that idea
rather than an adopter of it.

### Where the prototype has already got to

Read before reinventing any of it. In `station-node`:

| | |
|---|---|
| `docs/profiles.md` | a profile says *what is there to be configured when the bytes arrive* |
| `docs/roaming.md` | and its companion: *where the bytes are*, discovered rather than assumed |
| `docs/the-crew.md` | settles the word, and adds the mechanism — **putting a profile on is itself a commit** |
| `docs/claiming-a-profile.md` | the claim half |
| `docs/the-crew-watch.md`, `docs/gear.md` | the watch, and what a crew stands on |
| `machine/crew.yml`, `machine/gear.yml` | the node's own declarations. A roster, explicitly not a startup script |

Two of those bear directly on the sentence above.

**`crew.yml` is the node's declaration, not a resident's.** Every other
long-running thing there is asked for by the engine that wants it; an agent
binding has no resident to ask for it, because it is not a service a mount wants
— it is how work gets done at all. FCPM will need the same file for the same
reason, and will need it *per machine*, which is the plural nobody has built.

**Wearing a profile leaves a line.** From the operator, in `the-crew.md`:

> If they put it on and do no work, I don't wanna see no commits. So the flow is
> still desirable to cause change just by wearing it.

> It's not that I'm thinking that we can stop them. It's just a log, really.
> We're trying to make the log compulsive.

That is the answer to *"own what it means to be on a machine"* already worked
out one node over. With two editing bays, the log stops being a nicety: it is
the only thing that can say which machine did which work, and it costs nothing
because the act of arriving writes it.

### What a machine profile owes

> Any machine profile that something could plausibly run inside of should
> document a lot about its environment, actually, so that agents who are
> working there don't have to fuss.

The standard is high on purpose and the reason is named: **so an agent arriving
on that machine does not have to work the environment out.** Anyone who has
watched a session burn three turns discovering that `pgrep -f` returns nothing
on a particular box knows exactly what this is buying.

> We are not necessarily trying to bring agents in immediately, but it is in the
> cards. I want us to understand that.

So a profile is written for a reader who is not here yet. That is not a reason
to write it thinly.

---

## The library is mounted as a branch, on purpose

> I do want to implement our version of this where branches hold library
> contents. At minimum, I wanna start with this version having its library
> mounted as a branch instead of a folder at the root on main. We're gonna stand
> as a different use case where we try this on purpose. Supposed to be
> configurable in the end.

**FCPM starts on branches rather than migrating to them**, which is materially
different from the station-node case and is the reason this is worth saying out
loud. The station node audited what *moving* its library would cost; FCPM never
has to move one.

Three things this asks of `.library-engine`, which is why they are being filed
upstream rather than invented here:

1. **A library instance is a branch.** Already petitioned from station-node
   (`a-library-is-a-branch-and-the-engine-factors-them`); FCPM is a second
   consumer with a different case.
2. **More than one at a time.**
   > It should be allowed to make multiple libraries.
3. **The engine declares its own residency — as an owner.**
   > The library engine declares its own residency in the repository, but as an
   > owner.

   Residency vocabulary today describes a *resident* asking the library for
   space. An engine that owns the instances it factors is a different
   relationship and does not have a word yet.

### What goes in it, and what does not

> Things don't have to go in this repository and thus its branches without being
> relevant to the station concept where they are being deployed. So this is not
> necessarily a full configuration backup of all media ever made.

The test is **relevance to the station concept where it is deployed**, not
completeness. A library here is a selection, and the thing it is emphatically
not is an archive of everything FCPM has ever produced.

> The library is where traffic and public trade is gonna take place, and is
> gonna host some important public resources like trade and city information
> and voices in the community.

`trade`, `city` and `voices` are three of the library's reserved category words,
and this is the first time anyone has said what FCPM would put under them. It is
not yet the answer to the node seat's G4 — that still wants the board's own
decisions — but it is the first concrete sentence pointing at one.

---

## The engines, and the order they arrive in

| | | |
|---|---|---|
| `.advocate-engine` | **mounted** | The only one today. |
| `.library-engine` | **wanted, and next** | *"The library engine is going to be present in order to provide for us a place to keep many things that are considered internal to this station."* As branches, per above. |
| `.ablative-engine` | **partly, and it needs a conversation** | See below. |
| `.proofing-engine` | **wanted, with new faces** | Needs none of station-node's private-client configuration. See `DESIGN-NOTES.md`. |
| `.tell-engine` | **later, on purpose** | *"We're going to be bringing the tell engine, but I don't think we need to go there yet. I wanna have a bulletproof implementation before I try that."* |
| Bottles | **not yet** | *"I don't need the bottles yet."* |

### The ablative conversation, stated rather than settled

Autumn flagged this one explicitly as unfinished, so it is written as an open
question and not as a plan:

> We're gonna have a computer in FCPM that behaves like station node writ large,
> which is to say some of this ablative stuff needs to come in. Not everything,
> and so we need to have a talk about that. And the result of the talk might be
> that ablative loses some functionality because it belongs in a better
> canonical place.

> So far, I consider ablative a personal thing. I wouldn't give it to someone
> and say run this. I don't know why they would. So we're not trying to bring
> ablative's tooling with us, but **the thing ablative does want to do is
> observe. And so that is not misplaced.**

The distinction to hold on to: **observation is not personal; ablative's tooling
is.** A machine in a studio that several people use has a stronger claim to
knowing what it is doing than a machine with one operator, not a weaker one.

Three shapes the talk could reach, written down so it can be resumed rather than
rediscovered:

- **Bring ablative with a couple of modules.** Cheapest, and leaves the split
  undone — FCPM would carry a personal tool with most of it switched off.
- **Split observation out of ablative into its own thing**, canonically, and
  both nodes mount that. This is what *"ablative loses some functionality
  because it belongs in a better canonical place"* sounds like from the other
  end. Most work, best outcome, and the decision is not FCPM's alone to make.
- **Re-home individual concerns where they already belong.** Several ablative
  appliances are arguably already somebody else's subject; the workload board,
  for instance, is about *declaring intent*, which is a node concern rather than
  a personal one.

Nothing is filed upstream for this yet, deliberately. Autumn said it needs a
talk, and a petition asserting a split would be deciding it in the hallway.

---

## What is deliberately not here

- **Agents running on FCPM machines.** In the cards, not immediate. Machine
  profiles are written for them anyway.
- **The tell engine.** Waiting on a bulletproof implementation, by her call.
- **Bottles.** Not needed yet.
- **A full media archive.** Explicitly out of scope — see *what goes in it*.
- **Anything that needs a secret in a public repository.** Structurally out, not
  merely discouraged.
