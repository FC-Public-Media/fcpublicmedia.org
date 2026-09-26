# Troves

**A trove is a discipline's gear, packed.** If you have one of these, this is the
gear that plays it and the configuration that makes the gear fit, per platform.
The word is station-node's (`docs/instruments.md` there, *Troves: not built,
written down so it can be*):

> It inverts the usual tree of responsibility. The node does not learn every
> discipline's gear. The trove says *I know this gear, and here is what it takes
> to run it.* The crew then assembles gear from prepared troves.

Station-node wrote that down and declined to extract one, because *"one
discipline is not enough to say where a trove's edges are."* FCPM has two, the
screens and the recorders, and they share an edge, which is what this directory
is drafting against. Autumn, 2026-09-25: sometimes a thing is canonical enough
that you would submodule it to gain an instrument along with its operating gear.

Status: draft. Nothing reads this directory yet.

## Three layers, and a trove is only the first

| layer | says | lives | example |
|---|---|---|---|
| **trove** | if you have one of these, here is its gear and config, per platform | here, until a second node wants it; then its own repository, submoduled | `recorder/`: OBS, portable, on Windows; Audio Hijack on macOS |
| **node** | these are our instruments, and what each one shows or records | `../instruments/` | the rolling TV shows the wall |
| **metal** | this is plugged into me, so I provide it | nowhere: the host discovers it, every time | editing bay 1 finds the Vizio, so it drives the rolling TV |

The metal layer is never written down, for the reason `machines/README.md`
gives for names: anything declared is copied by the act that makes it wrong. The
node layer is intent. Only the host that finds the hardware on its bus or its
display stack can say it is there.

## Rules

- **One discipline per folder, and the folder can be lifted out whole.** Nothing
  in a trove reaches outside it except to cite. When a second node wants one,
  moving it to its own repository is a `git mv` and a submodule, not a rewrite.
- **A trove's gear lives under its own prefix on the host.** On Windows that is
  `%LOCALAPPDATA%\<profile>\troves\<trove>\`. The path to the executable then
  says whose instrument code is running, and so which grant it needs. That is
  station-node's reason, and it is the whole point of the prefix.
- **A trove never touches gear a person operates.** The bays are production
  machines other people sit down to every week. Their OBS, their browsers, and
  their settings are theirs. A trove brings its own copy, its own profile and its
  own ports, or it does not run.
- **A trove's gear comes aboard through the bay** (`../machines/BAY.md`): received,
  verified, staged, installed at a declared restart tier, confirmed. The trove
  carries the procedure; the host keeps the record of each arrival.

## The troves

| trove | plays | status |
|---|---|---|
| [`recorder/`](recorder/) | anything that produces files a node catches: capture decks, the RØDECaster | drafting |
| `kiosk-screen/` | a screen that shows a studio page | roller-tv's, after `instruments/` merges |
