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
| here | **has one been put on, and which?** | there are two, simultaneously |

That second half is the new work, and it is the reason this repository is a real
consumer of the idea rather than an adopter of it.

## Which profile a checkout wears is discovered, never declared

This follows from a rule the prototype already established, and it is worth
stating rather than re-deriving:

> Anything declared is copied by the act that makes it wrong.

A file on `main` saying *this checkout is bay one* travels to bay two the moment
somebody clones it, and is then a confident lie. So no such file exists. Instead:

- Each profile carries a **`names`** file — the values that host *should* answer
  to. That is intent.
- The machine answers `scutil --get LocalHostName` — that is fact.
- **The profile a host wears is the one whose `names` matches the fact.**
  Presence of a match is the claim. `machines/binding` reports it.

Config describes intent; the system discovers fact. Same house rule as
everything else here.

### No profile is the clean state, not the failure case

> A clone with no profile is not a broken station. It is data.

`machines/binding` on a laptop that is neither bay prints exactly that and exits
0. It is the correct answer, it is the common answer, and it is what these bytes
should be by default everywhere they land.

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
- **There is no FCPM station node yet**, and neither bay is one. *"Presently, we
  don't have a machine that would be an FCPM station node. And so we are
  avoiding that part of it so far."* A bay that becomes one gains folders; it
  does not need a different kind of profile.
- **Claiming is not a signed act here.** The prototype wants putting a profile on
  to be a commit with the right signers, and the provisioning step for that does
  not exist on either node. Matching on `names` is weaker and is what can be
  built today; it is not a substitute for that design and should not be allowed
  to become one.
