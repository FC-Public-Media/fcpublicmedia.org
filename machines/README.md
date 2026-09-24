# Machines

**A profile describes a host this repository can plausibly run on.** It is here
so that an agent arriving on that machine does not have to work the environment
out, which is the whole of the ask:

> Any machine profile that something could plausibly run inside of should
> document a lot about its environment, actually, so that agents who are working
> there don't have to fuss.

Nothing here runs anything. A profile is a description and a set of intents; the
system is what has the facts.

## This is the plural, and that is the point

`station-node` has one of these, called `machine/`, and its own notes say why
that shape is provisional:

> It is not labelled [a profile], because there is exactly one and a category
> with one member looks like a thing rather than a kind.

FCPM is where the kind gets a second member. There are two editing bays, this
repository is expected to be checked out on both, and **both may be running at
once.** So the question a checkout has to answer is not the one station-node
asks.

| | asks | because |
|---|---|---|
| `station-node` | **has a profile been put on?** | there is only one it could be |
| here | **has one been put on, and which?** | there are several, simultaneously |

That second half is the new work, and it is the reason this repository is a real
consumer of the idea rather than an adopter of it.

There are three profiles now rather than two, and the third is not a third bay:
`kiosk-1` is Windows, which is the case the prototype wrote a schema for and
declined to implement. The plural was already the point; the third member is
what makes it a plural of *kinds* and not just of copies.

## Which profile a checkout wears is discovered, never declared

This follows from a rule the prototype already established, and it is worth
stating rather than re-deriving:

> Anything declared is copied by the act that makes it wrong.

A file on `main` saying *this checkout is bay one* travels to bay two the moment
somebody clones it, and is then a confident lie. So no such file exists. Instead:

- Each profile carries a **`names`** file — the values that host *should* answer
  to. That is intent.
- The machine is asked its name, in whatever way its platform answers that
  question — `scutil --get LocalHostName` on macOS, `%COMPUTERNAME%` on
  Windows. That is fact.
- **The profile a host wears is the one whose `names` matches the fact.**
  Presence of a match is the claim. `machines/binding` reports it.

A `names` line therefore carries its platform:

    # platform   key             value
    windows      ComputerName    FCPM-KIOSK-1

and it has to, because **macOS has a `ComputerName` and Windows has a
`COMPUTERNAME` and they are not the same field.** One is a display string with
spaces and an apostrophe in it; the other is a NetBIOS-flavoured label. A
single-column file would have let one host match the other's name — which is
not a theoretical objection, it is what the format was changed to prevent the
first time a non-macOS profile existed here.

Config describes intent; the system discovers fact. Same house rule as
everything else here.

### No profile is the clean state, not the failure case

> A clone with no profile is not a broken station. It is data.

`machines/binding` on a laptop that is neither bay prints exactly that and exits
0. It is the correct answer, it is the common answer, and it is what these bytes
should be by default everywhere they land.

## Windows is the default here, and that is the sharpest difference from the prototype

station-node is a Mac and everything in it reads that way: `open -a`, launchd,
`scutil`, Homebrew, a bundle identifier as the thing that survives a move. FCPM
is not that, and pretending otherwise produces a directory that describes no
machine anybody here owns.

> I'm setting up profile information that I'm not going to have had because I
> was on a Mac before, and so here the crew and the gear are going to look
> different. On Windows, I'm using winget in the toolchain […] FC Public Media
> would need a couple types, but I'm going to say that their default is
> Windows. And so their crew is Windows and their gear comes from winget.
>
> — Autumn, 2026-09-23

The prototype anticipated this and declined to build it, on purpose. From
station-node's own `docs/gear.md`:

> *"I need to be able to also specify what Windows is doing here, because
> Windows doesn't get to benefit from any of what we've done so far. It's not
> that I want to do it — in fact, we shouldn't, because I'm not gonna use it
> that way. But one of the other projects might."*
>
> A Windows profile whose gear is `winget` and four items **is finished**. […]
> The dichotomy is carried in the **schema** — a `platform:` and a
> `provisioner:` that a reader may not implement — and the implementation stays
> macOS-only until somebody has a Windows host to run it on.

**This is that project, and this is that host.** `machines/kiosk-1` is the
first one. So the keys station-node wrote and did not implement get filled in
here rather than invented: `platform: windows`, `provisioner: winget`. Nothing
below is a new vocabulary; it is the prototype's vocabulary reaching a machine
it was written for and never met.

## What a default is

Three files sit at the top of `machines/`, beside the profiles rather than
inside one:

| | |
|---|---|
| [`crew.yml`](crew.yml) | who can be started on an FCPM machine, and how |
| [`gear.yml`](gear.yml) | what the crew stands on, and who may replace it |
| [`toolkits`](toolkits) | which tool a language's work is done with |

They are the **default**, which means: what an FCPM machine is, absent a
profile saying otherwise. Today that default is Windows and winget, because
that is what the only described host runs.

**A profile's own copy replaces the default whole. It does not merge with it.**
Merging two rosters produces a third that nobody wrote and nobody can read off
a page — you would have to run something to find out what a machine claims,
which is precisely the property this directory exists to avoid. So a profile
that diverges says everything, and a profile that agrees says nothing.

That makes **absence meaningful in both directions**, which is the same rule as
the folders:

- `machines/kiosk-1/` has no `gear.yml`. That is not an omission. It is the
  claim that this machine is exactly the default.
- The editing bays are macOS and carry no gear at all. Also not an omission —
  nothing on either has been established as ours to configure, so there is
  nothing to be issued.

## Crew and gear

The words are station-node's and the line between them is worth stating once:

| | | |
|---|---|---|
| **crew** | who is here to do the work | [`crew.yml`](crew.yml) |
| **gear** | what the crew stands on — software somebody put there on purpose | [`gear.yml`](gear.yml) |
| **a toolkit** | which tool a language's work is done with | [`toolkits`](toolkits) |
| **an advocate** | *why* an agent runs here and what it may conclude | [`../advocate.yml`](../advocate.yml) |

The last row is the one to be careful about, because it is the row that would
otherwise become a second list of the same agents. `advocate.yml` says why a
session happens and what it is allowed to write. `crew.yml` says what can be
started on this machine. An advocate round is something the crew is capable of
hosting; it is not a provider.

### Where winget changes the shape, and not just the commands

**Gear stops being "a launchable".** station-node defines it against a CLI on
PATH — gear is what you reach with `open -a`, a CLI is a `link` entry in its
MANIFEST — and on macOS that is a real boundary between two different kinds of
object, found different ways. On Windows it is not there to draw:
`winget install Git.Git` and `winget install Microsoft.VisualStudioCode` are
the same act, land in the same inventory, and are listed by the same
`winget list`. One ends up in the Start menu and one ends up on PATH; VS Code
ends up in both. So `gear.yml` here lists **whatever winget owns**, and the
reason is written in the file: maintaining a split the platform does not make,
against a census that does not honour it, is how a census stops being run.

**The identifier changes and the job does not.** A bundle id survives a move
where a path does not; on Windows the winget package id (`Git.Git`) does the
same work. Same field, different registry.

**What an upgrade must not lose gets smaller, honestly.** On macOS a TCC grant
is keyed to the designated requirement, so a swap with the same DR inherits it
silently and one without it arrives with none — which is why station-node's
entries carry `grants:` and a DR check. There is no TCC here. What survives an
upgrade on Windows is per-user configuration and a PATH entry, and saying only
that is more useful than importing a field with nothing behind it.

**A toolkit preference stops being separable from how the tool arrives.**
station-node's `config/toolkits` is four lines of `<language> <tool>`, and it
can be, because acquisition is somebody else's file — brew, asdf, a version
manager. On Windows the tool and its arrival are one act, which is what Autumn
meant by *"toolchain as a file is no longer like that simple over in the
station node."* So [`toolkits`](toolkits) carries a third column for how a tool
arrives, and every row of it is currently unfilled, which is the true state.

### What is not implemented, deliberately

There is no `crew` command and no `gear` command here. station-node has both;
this directory runs exactly one thing, `binding`, and that restraint is stated
at the top of this page. `winget list` is already the census — a reader wrapping
it would add a second place for the answer to live before anybody has run the
first.

## A directory is a profile when it has a `PROFILE.md`

Stated because the first version of `binding` counted every directory, and duly
reported `__pycache__` as a machine the moment something imported it. A
blocklist would have fixed that one case and waited for the next; the positive
rule is also the honest one. **A profile's page is the profile.** A directory
with no page is not an undescribed machine — it is not a machine.

## A folder in a profile is a claim to have the thing it names

Borrowed whole, because it is the rule that keeps a profile honest:

> `shell/` present means this kind of host has a shell whose environment is ours
> to set. A profile with no `shell/` is not missing one — it is saying there is
> nothing there to configure, and that is a complete and useful answer.

So an empty profile directory is a profile that claims nothing yet. Both of
these claim nothing yet. **Do not add a folder to make a profile look complete.**
Add one when the thing it names is real, and the folder becomes the claim.

## What is not decided

- **The names are placeholders.** `editing-bay-1` and `editing-bay-2` are what
  Autumn calls them out loud. Nothing on either machine has been asked what it
  answers to, so `names` in both is unfilled. Renaming the directories is free
  while they are empty and expensive afterwards.
- **There is now a candidate FCPM station node, and it is `kiosk-1`.** This
  reverses the position recorded above it and in
  [`../docs/STATION.md`](../docs/STATION.md) — *"presently, we don't have a
  machine that would be an FCPM station node"* — which was true when it was
  written on 2026-09-17 and stopped being the plan on 2026-09-23: *"I want to
  use it to prove fcpm.org as a station node of its own."* What "prove" means
  is not settled, and it is explicitly not "install station-node":
  [`../docs/TENANCY.md`](../docs/TENANCY.md) limits what travels to a tenant. A
  bay that became one would gain folders; it would not need a different kind of
  profile.
- **Nothing has been read off `kiosk-1` yet.** Every fact in its `PROFILE.md`
  came out of a spoken briefing, including the ones that look mechanical. The
  single most valuable unrun command in this directory is `winget list` on that
  box, because it is the first thing that would turn `gear.yml` from a list of
  intentions into a diff.
- **Claiming is not a signed act here.** The prototype wants putting a profile on
  to be a commit with the right signers, and the provisioning step for that does
  not exist on either node. Matching on `names` is weaker and is what can be
  built today; it is not a substitute for that design and should not be allowed
  to become one.
