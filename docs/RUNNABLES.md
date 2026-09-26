# Runnables: what a crew may run, worn where it can be inspected

`status: draft`, 2026-09-26. station-node's `docs/the-runnable-manifest.md`
worked out the shape. This page applies it to FCPM's machines, starting with the
media node's own tools.

> It's not the goal for this thing to just vomit anything in bin/ for mass
> auto-use.

## The harness already agrees

In auto mode, Claude Code settles a **narrow** allow rule before its classifier
runs, and **suspends broad ones**: `Bash(*)`, `PowerShell(*)`, wildcarded
interpreters such as `Bash(python*)`, and package-manager run commands
([permission modes](https://code.claude.com/docs/en/permission-modes.md#how-the-classifier-evaluates-actions)).
So a list made by allowing everything in `bin/` would not work anyway, and a
narrow one does. station-node's page left this open, as "run this before
building the pipeline"; the documentation answers it, and the first proven
verb on a machine is the measurement.

Two more facts decide the shape:

- A compound command is allowed only if **every** part matches a rule.
- Project settings are read from the directory a session **starts** in, and
  rule paths are relative to it. FCPM's sessions start in `~/code`, so rules
  name `work/fcpublicmedia.org@media-node/...`: the live checkout, which only
  ever holds what was merged. The same verb run from an edited worktree does
  not match, and asks.

## Four layers

| layer | says | where | written by |
|---|---|---|---|
| **census** | every runnable this checkout carries, and its blob | `bin/runnables`, printed, never stored | nobody; it reads |
| **claim** | per verb: its narrowest shape, and what it touches | `machines/RUNNABLES` | the tool's author |
| **proof** | this holder, at this blob, does what its claims say | `machines/<profile>/bay/runnables.proven` | the bay |
| **answer** | what this crew may run without asking | `machines/<profile>/GRANTS` | the crew, by merged PR |

`bin/runnables compile <profile>` joins the last three into harness settings.
It has no judgment in it on purpose: a machine that grants permissions should
be boring.

**Being on the census grants nothing.** A file with no claim is *undeclared*: it
is shown, and it matches no rule. `site/bin`'s syncs, pricing and claim minting
are undeclared today on purpose; they touch the network, money and tokens, and
their claims are their authors' to write.

**A class sets the default answer.** `read` and `inside` allow; `outside` and
`desk` ask; `secret` and `service` deny. A profile may `narrow` an answer and
never loosen one. Only a merge to `main` widens.

**Unproven means unlisted, not `ask`.** An ask rule forces a prompt even where
the harness would have let a command through, and a background session has
nobody to answer it. So an allow the bay has not proven is left off, and the
command meets the harness exactly as it would with no list.

## The bay proves our own tools too

ablative's survey of its internal services (`bay/surveys/2026-09-22-internal-services.md`
there) put it plainly: internal software answers the same questions as foreign
software, and "nothing about 'ours' removes a field". A payload from outside is
proven by the vendor's digest and its signature. A runnable of ours is proven
by:

- **its identity:** the git blob at the commit the machine runs. It is the same
  on every host with that commit, and it changes when the code does, so a
  changed tool falls off the list until it is proven again;
- **what it runs as:** the interpreter or shell that starts it (`runner` in
  GRANTS). A grant to an interpreter is a grant to every script it runs, which
  is why rules name the script and never `python *`;
- **its claims against its code:** every `read` verb changes nothing, and every
  `inside` verb writes only inside the checkout.

The proof record is the host's, beside its payload records
(`machines/BAY.md`), because an arrival is a fact about one machine.

## Worn by the crew, on purpose

The answer lives with the crew because it is the crew's outfit. It is committed
so that anybody inspecting a machine can read what it is set up to do, and
propose a change to it the way any change is proposed. A repository may carry
several: one per profile, each for the platform that profile names.

`machines/sync`, after station-node's `machine/sync`, is what puts it on:
`binding` finds the profile this host wears, and `sync` installs that profile's
compiled settings into `~/code/.claude/`, or says how they differ. It is the
same entry point on every platform, and the profile says where things go.

**A person runs `sync install`, never a session.** A session writing its own
allow rules is the move the gate exists to stop, and the classifier says so: the
media node's sessions were refused four times as `[Permission Grant]`. `sync
status` is a session's to run; installing is Autumn's, and later the signed
request's.

**What the media node wore before this: nothing.** Asked on 2026-09-26, it had no
permission rules in any settings file, and every session ran in auto mode with
the classifier as the only gate. kiosk-1's GRANTS is the first set it would wear.

**A deny names a text, not an act.** Rules match what a session types, so a deny
catches the forms GRANTS lists as runners and not a path spelled another way.
Denies are a floor under the classifier, not a wall around a secret. The wall is
where a secret lives: the certificate store's non-exportable key, and a token
that is printed and never written. A command that is not ours, such as
restarting the door's task, can be listed with `host` to ask or deny, never to
allow.

## Where this goes

Autumn, 2026-09-26: admission is a merge to `main` **for now**. Later, a request
to run something will carry a passkey signature. A person at a kiosk or on a
phone signs on their own checkout of a control branch, and the attendant or
operator acting on it is held to exactly what that person could do anyway. The
point is that a non-technical board can bring in new equipment, and have dev
agents and attendants provision it, without one person's account looking after
it for five years. This layer is written so that it stays "just git" when that
arrives: the claim, the proof and the answer are commits, and a signature over
a commit is what the gesture adds.

## Proving, and wearing

`bin/runnables prove <profile> <holder> --by <who>` (2026-09-26). The holder
must be one the profile wears, committed, and unchanged from its commit. Each
`read` verb is run exactly as the profile's canonical runner starts it, and
nothing may change: not the checkout, and not the profile's `bay` or `troves`
folders in `%LOCALAPPDATA%`. Then one line goes into
`machines/<profile>/bay/runnables.proven`: holder, blob, date, the verbs that
ran, and who read the rest of the code. It proves the read verbs by running
them; an `inside` verb rides on the same line, which is what `--by` is for.

**`depends <holder> | <path>`** names a repository file the holder reads at run
time. `prove` records its blob in the proof line, and `compile` counts the proof
only while every declared dependency is at that blob, so an edit to the file
revokes the grant exactly as an edit to the holder would. The recorder's
`obs.ps1` depends on the bay's record, because that is where it reads the hash
of the only `obs64.exe` it will start. Files outside the repository (the staff
copy's own config, a password in Credential Manager) cannot be pinned by blob;
the holder guards those itself, and says how in its header.

**`wears <holder>`** in a profile's GRANTS limits it to those holders. The bays
do not run the door, so the door's rules are not theirs to carry. A profile with
no `wears` line answers for every claim.

**Proven for tasks, not in general.** A proof is of these bytes on this
machine, run the way this crew runs them. The recorder's OBS is the first case
it was built for: the staff copy is allowed to be driven by an issued task
because the bay installed it, confirmed it kept to itself, and proved the
script that drives it, and because a merge admitted the answer. None of that
carries to another machine, or to the OBS people use here.

## Not built

- **`machines/sync` installing the settings.** `sync` puts a profile's carried
  files in place; the compiled settings are not one of them yet, and installing
  them is a person's step.
- **One canonical form, taught.** The media node's sessions have typed door.py
  several ways (`$LOCALAPPDATA` or an absolute path, either slash, Bash or
  PowerShell, from the checkout or from `~/code`). GRANTS picks the venv's
  `python.exe` from `~/code`. The machine's AGENTS.md has to say so, or the allow
  never fires.
- **A door verb for restarting the door.** Today it is `Stop-Process` and
  `Start-ScheduledTask` by hand, which GRANTS holds at `ask`. A claimed verb
  would let that be one line with one answer.
- **Editing bay 1's own tools.** `bin/refs` and `bin/pool.ps1` live in `~/code`,
  in no repository, so no blob can be proven. They move into
  `machines/editing-bay-1/` before that profile can answer for them.
- **A session starting somewhere else.** When a session's working directory
  moves into a worktree, which rules it reads afterwards has not been measured.
