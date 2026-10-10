# `machines/RUNNABLES`

Moved out of the file. Unreviewed.

## 1

Above `# holder                        | run        | shape                | class   | says`

RUNNABLES: what this repository's own tools say they do, one verb per line.

This is the SUPPLIER's half: a claim, written by whoever wrote the tool. It
grants nothing. What a machine actually allows is its crew's answer, in
`<profile>/GRANTS`, compiled into the settings its sessions read. The whole
design is docs/RUNNABLES.md, after station-node's `the-runnable-manifest.md`.

THE CLAIM IS A MENU, NOT A PERMISSION. A verb listed here and answered nowhere
is never allowed, and nothing complains. A runnable file with no line here at
all is UNDECLARED: `bin/runnables` shows it, and it matches no rule.

ONE LINE PER VERB, AT ITS NARROWEST REUSABLE SHAPE. A rule cut to one exact
invocation fires once and is a receipt; a rule for the whole tool is the hole
the gate exists to close. The shape is what follows the holder on the command
line, and a trailing ` *` means "and any further arguments". `-` is the tool
with no arguments at all.

Fields, separated by `|`:

  holder   the file, relative to the repository root
  run      how it is started: sh (Git Bash on Windows), python, powershell
  shape    the verb, as above
  class    what it touches. The class decides the DEFAULT answer, and a
           profile may narrow it; only a merge to main widens one.

             read      reads, prints, changes nothing           allow
             inside    writes inside this checkout only         allow
             outside   writes outside it: the host, the depot   ask
             desk      needs a person there, or an admin grant  ask
             secret    prints or handles a credential           deny
             service   a job's own verb, never a session's      deny

  says     one line: what it does, in the tool's own words where it has them

Git Bash only to read, no yaml: this is parsed by `bin/runnables`, which has
to run on a bay that has no Python yet.

## 2

Above `troves/recorder/bay/obs-portable.ps1 | powershell | check    | read    | what is received, staged, i`

The recorder trove's bay procedure (docs/troves/recorder/README.md, docs/machines/BAY.md).
Bare verbs: the defaults (-Version 32.2.2, -Node editing-bay-1) are the use.
Every step but check appends to %LOCALAPPDATA%\<profile>\bay.ndjson, so
none of them is `read`. None needs an administrator; install and confirm are
desk because install is where the firewall grant is placed, and confirm opens
an OBS window on the screen of a machine people use.

## 3

Above `troves/recorder/obs.ps1         | powershell | status       | read    | is ours installed, the bay's`

The recorder's runtime verbs (troves/recorder/obs.ps1, README "Playing it").
Only its own websocket on 4456, never the members' OBS. prepare is desk, not
secret: a person runs it once, and it stores a credential without printing it.

## 4

Above `# The crew's one switch. Its other verbs reach tools claimed above or below`

NOT CLAIMED YET, on purpose. site/bin holds the syncs, the pricing and the
claim minting: they reach the network, money and tokens, and a claim for one
is its author's to write, not a census's to guess. They show as undeclared.

## 5

Above `machines/fcpm                   | sh         | -                    | read    | which profile, and w`

The crew's one switch. Its other verbs reach tools claimed above or below
(bin/refs, the pool, bin/runnables) and are answered there, not here.
