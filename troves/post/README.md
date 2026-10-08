# post

**What happens to a recording after it is let go.** The pools page is where
recordings are looked at, grouped and released. Once released, a take is no
longer the pools page's to talk about: it is scooped up, enhanced, transcribed,
and whatever else its show asks for. This is where it goes, and the page that
shows the pipeline it is going through: `fcpm post`.

> When it's done, their UI shouldn't be the thing talking about it anymore.
> They release it, it gets scooped up, it gets processed, and they still know
> about it, but they need a new place to put it. — Autumn, 2026-10-07

## The rules it is built from

- **No state anywhere but the disk.** Not in memory, not in a service, not on
  one machine's profile. These machines are used by people, turned off, and
  signed out of; work happens when a button is pushed. Whatever is lost when a
  machine goes down must be readable on the disk afterwards.
- **A folder per take, not a folder per step.** A step folder (`enhanced/`,
  `trimmed/`) holds files with no clue what was supposed to happen to them
  next. A take's folder carries its whole route, so it says on its own what is
  done, what is next, and what went wrong.
- **The name is the translation.** No guessing at file names: the take's id and
  each step's place in the route are in the names.
- **Any worker can pick it up.** A worker added later, on this machine or one on
  the share, reads the same folders and takes the next step it can do.
- **The rename is the declaration** (the depot's rule, `enhance/docs/CAPTURE.md`).
  Output is written hidden and renamed when it is whole.

## The layout

```
E:\POST\                              the post partition's root (machines/<profile>/post.yml)
  artfcally-s1e3.3f9a1c0b\            a take: its out name, then 8 hex of its route's SHA-256
    route.json                        the whole plan, written once at admission and never changed
    0-source\                         what was released: the recordings, with SHA256SUMS
    1-enhance\                        step 1's output, with SHA256SUMS
    .2-transcribe.claim               step 2 is held: by whom, on which machine, until when
    3-loudness.failed.json            a step that failed: what ran, its exit, the tail of its log
E:\DOORS\                             hand-offs to tools that only work with folders
  enhance\out\  enhance\back\         e.g. Adobe Podcast: dragged out, downloaded back
```

**Nothing records progress but the files.** The next step of a take is the
first step of its route with no output folder. There is no "state" field to
fall out of date.

| on disk | means | drawn |
|---|---|---|
| `N-step\` | done; its SHA256SUMS say what it made | ■ |
| nothing, step before it done | ready for any worker that can do it | □ |
| `.N-step.claim`, lease running | held by a worker | ◐ |
| `.N-step.claim`, `door` in it | waiting at a door for a person | ◑ |
| `.N-step.claim`, lease run out | the worker went quiet; anyone may take it back | ◌ |
| `N-step.failed.json` | failed; nothing after it runs until it is retried | ! |
| nothing, an earlier step not done | waiting its turn | · |

## A step, run

1. **Claim.** Create `.N-step.claim` exclusively (it fails if someone has it).
   It says the worker, the machine and the lease's end. The worker renews the
   lease while it works.
2. **Work.** Read the step before's folder (`N-1-...\`, or `0-source\`), and
   write into `.N-step.partial\`.
3. **Declare.** Write `SHA256SUMS` in the partial, rename it to `N-step\`,
   remove the claim.
4. **Or fail.** Write `N-step.failed.json`, remove the claim and the partial.
   Retrying moves the failure aside (kept, hidden) so the step is ready again.

A worker that dies leaves a claim whose lease runs out, and at worst a
`.partial`. Taking a step back renames the dead claim aside (only one taker's
rename succeeds) and starts the step clean.

**Leases are per step**, from the machine's `post.yml`: minutes for a command,
days for a door, where a person does the work.

## Doors

Some tools only take files from a folder, or from a person's hands (Adobe
Podcast today: drag in, download back). For those, the claim puts a copy of the
step's input in `E:\DOORS\<step>\out\`, named `<take>.<N>-<step>.<ext>`, and
waits. Whatever comes back into `E:\DOORS\<step>\back\` whose name starts with
`<take>.<N>-<step>` is the result: hashed, moved into the take's `N-step\`, and
the door's copy is removed. A door can be emptied at any time without losing
anything, because the take's folder is the record.

## Steps

What each step is, on this machine, is the machine's `post.yml`: a command
(run with `{in}`, `{out}`, `{take}`, `{python}`) or a door, and a lease. A step this
machine doesn't declare is left for a worker that does, drawn as waiting for
one. Which steps a take goes through is its show's pipeline (pools README, *A
show's pipeline*), copied into `route.json` when it is admitted, so a take
goes through what it was released with even if the show changes later.

## Admission

`fcpm post admit CONFIG` takes what releasing an episode renders (the show,
its out name, its pipeline, its recordings) and makes the take: its folder,
`route.json`, and `0-source\` with the recordings hashed (hard-linked when they
are already on the same volume, copied otherwise). Admitting the same release
twice finds the same folder: the id is the route's own hash.

The episode supervisor (`troves/pools/episodes.py`) is what will admit a
released episode, rather than running its steps from the groups file itself.

## The page

`fcpm post` serves it on `127.0.0.1:8093` while its window is open. One row per
take, one column per step, in route order, as the table above draws them.
Dark and dense, like the pools page; no prose. A row's mark opens its folder. A
failed cell shows its `failed.json`, and retries. **Run here** runs every ready
step this machine can do, until none is left, and exits: nothing is started
unless someone asks.

`fcpm post status` prints the same in a terminal. `fcpm post run` is the
button, without the page.

## Not yet

- **Delivery.** The last step. Autumn has notes; not picked up yet.
- **Eviction.** E: is a 1 TB slush. What is kept of a delivered take, and when
  the intermediates go.
- **The ledger.** The grants branch (`enhance/docs/GRANTS.md`) records hand-offs
  between machines; the page could mark where it and the disk disagree.
- **Squares on the pools page** that say "in post" for what was released, and
  open this page at the take.
