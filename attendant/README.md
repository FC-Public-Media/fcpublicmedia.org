# Attendants

**An attendant is a seat that can do on a studio page exactly what a person
at that page can do, and nothing else.** Autumn, 2026-09-26, after a shutdown
made the startup pool worth planning for:

> operators who have known jobs who can perform the work our UI does, while a
> human is also present but requiring a11y for basically any reason, voice
> control eventually and basic "i don't understand, do it for me" assistance.

Status: draft. No attendant runs yet. What exists is this page and the
recipes beside it, which a person can follow today.

## The word

She said *operator*. Across this constellation **the operator is the person
who runs a node** (station-node's `docs/the-antenna.md`: *each operator mounts
their own antenna*; `SEATS.md` in library.anecdote.channel: *the constituency
is the operator's*). An "operator seat" would read as hers. *Attendant* is the
recognised word for somebody on the floor who helps a person use what is
already there. **Settled** (Autumn, 2026-09-26): "attendant is fine to
confirm. It was on my mind as well."

## Where it sits among the seats

| seat | works on | a person is | its authority |
|---|---|---|---|
| advocate | background branches, research | not there | its seat's goals, its own branch |
| dev | thaws and grants | with it, directly | the thaw and the grant |
| **attendant** | known jobs on one page | **at the page**, not at the agent | **the page's own controls** |

**An attendant has no console, no Remote Control and no worktree.** The page
it is attending is its whole grant. If the person in front of the screen could
not do it with the controls on that screen, neither can the attendant.

## The accessibility tree is its interface

An attendant finds what to do the way assistive technology does: **by role
and accessible name.** *Button "Files"*, not `nav button[data-m=files]`.

That is one rule doing three jobs:

- **Parity is checkable.** What the attendant can reach is exactly what the
  page exposes, so "only what the person could do" is a fact about the page
  rather than a promise about the agent.
- **A control it cannot find by name is a bug**, and it is the same bug a
  screen reader or switch user hits. Fixing it for one fixes it for both.
- **Voice control later needs nothing new.** "Show files" is the same lookup.

## Recipes

A recipe is one known job on one page, written so that a person and an agent
following it do the same thing and can tell whether it worked.

    page:     the module or route, not the screen (shows reference modules;
              see ../instruments/README.md)
    shown on: the instruments it is on today, for finding it
    before:   what the page looks like when you start
    steps:    role + accessible name, each with the visible result that proves it
    done:     the check a person could make by looking

Every step names something visible. **"It worked" is never a claim about
state the person cannot see**, because an attendant that says it did something
the person cannot confirm has not helped them.

Because the steps are by role and name, a recipe is also an integration
test: Playwright's `getByRole(role, {name})` runs it as written. The existing
suite in `site/tests/` selects by `data-` attributes and ids, which is right
for what it tests and is not this.

| recipe | page | last followed |
|---|---|---|
| [`wall.md`](wall.md) | the wall (rolling TV) | 2026-09-26, on roller-tv from a local render |

## When a step fails, it is a bug, not a gotcha

- A **gotcha** is a surprise about the environment: a machine, a network, a
  tool. They go where they already go (`machines/kiosk-1/gotcha`).
- A **bug** is the page not offering what the recipe says it does, or
  offering it without a name. It goes in [`BUGS.md`](BUGS.md), committed.

Committed is the point. An advocate whose unit of work is usability finds
them on `main` and can research them in the background, and Autumn can step in
on any of them. That is the loop: recipes prove the page, failures become
bugs, and bugs become work.

A recipe that is wrong about the page (the page is fine and the recipe went
stale) is fixed in the recipe, not logged.

## Open

- **Waking an attendant.** The pool (`bin/pool.ps1` on editing bay 1, `door.py
  sessions` on the media node) can hold one idle, but nothing can call it yet.
  The shape is a signal on an `attendant` channel: the loudspeaker, designed in
  station-node's `docs/the-antenna.md` (its PR #174). A signal has no
  recipient, so it is written whether anyone is listening or not, and a
  daemon can commit it even though only a seated agent can send a message.
  **What is missing is the watcher.** A commit wakes nobody. Something has to
  watch the channel's ref and start a session when it moves, and that is a
  job the node declares for its own pool (a `kind:` in station-node's
  `bin/services`), not a property of the channel. A node that only tails a
  channel reads the same format and starts nothing.
- **A local copy of each page.** The wall is written to the depot's share and
  editing bay 1 cannot reach it (`../instruments/README.md`, *Open*). It can
  render one itself (see *How it was followed* in [`wall.md`](wall.md)), with
  the real shell and thin data. Nothing does that as a step yet, so a recipe
  is followed by hand rather than run as a test.
- **Pages people hold rather than screens we drive.** `/check-in/` is a
  person's own phone. An attendant has no place there. Whether a recipe for it
  still belongs here, as the "do it for me" script read aloud, is undecided.
