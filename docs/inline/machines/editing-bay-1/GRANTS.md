# `machines/editing-bay-1/GRANTS`

Moved out of the file. Unreviewed.

## 1

Above `# The admitted code is the read-only mirror: it only ever fast-forwards to`

GRANTS: editing bay 1's answer to ../RUNNABLES. What this crew wears, on purpose.

See ../kiosk-1/GRANTS for the line types and docs/RUNNABLES.md for the design.
Compiled by `bin/runnables compile editing-bay-1`; put in place by a person
with `machines/sync install`, never by a session. An allow reaches the
settings only for a holder whose blob is in bay/runnables.proven.

THIS MACHINE IS NOT OURS TO RUN. People sit down to it every week, and the
software they use is theirs: their OBS in Program Files with its settings in
%APPDATA%\obs-studio, its virtual camera, its shortcuts, and whatever talks
to it (a member's Streamer.bot does). The recorder trove's OBS is a second,
portable copy for staff and attendant tasks, prepared so that a person can
use it too, and it goes nowhere else (../../troves/recorder/README.md).

## 2

Above `checkout  refs/fcpublicmedia.org`

The admitted code is the read-only mirror: it only ever fast-forwards to
main, so a rule naming it names what was merged. This bay keeps no live
checkout (~/code/AGENTS.md).

## 3

Above `wears  troves/recorder/bay/obs-portable.ps1`

  wears <holder>                    answer only for these holders. A profile
                                    with no `wears` line answers for every
                                    claim, as kiosk-1 does

The door is the media node's; this bay does not run it. What it wears:

## 4

Above `runner  powershell  Bash        powershell -NoProfile -ExecutionPolicy Bypass -File`

Windows PowerShell 5.1, as the pool's task runs its own script. The Bash form
is canonical; the PowerShell tool's form gets the denies too.

## 5

Above `host  deny  PowerShell(Stop-Process -Name *)`

NEVER STOP ANYTHING BY NAME ON THIS MACHINE.

The staff OBS and the members' OBS are both obs64.exe. A stop by name cannot
tell them apart, and it would end somebody's recording or stream. The trove
stops its own copy by the PID it started (troves/recorder/obs.ps1). The same
is true of every other program here, so the rule is not about OBS: a process
on this machine is stopped by its id, or by a person.

## 6

Above `wears      troves/recorder/obs.ps1`

THE STAFF OBS, DRIVEN BY ISSUED TASKS.

An attendant's task may start the recorder's OBS, record, and stop it,
without asking, because of everything below and nothing less:
  - the bay installed this copy and confirmed it kept to itself
    (bay/obs-portable-32.2.2.yml), and obs.ps1 `start` refuses any obs64.exe
    whose hash is not the one that record names;
  - the cycle a task runs was exercised on this machine, at this blob of
    obs.ps1, and left the members' OBS exactly as it found it;
  - and this file, with these lines, was merged.
`prepare` is a person's, at the desk. Changing obs.ps1 revokes all of it
until it is exercised again.

  exercise <holder> | <shape> ; ...   the cycle `prove --exercise` runs
  untouched <path>                    listed the same after (names, sizes, times)
  quiet <image>                       none running before it, none after
  expect <file> <text>                the cycle must append <text> to <file>
  admit allow <holder> | <shape>      an outside verb, allowed once exercised
  depends <holder> | <path>           a repo file the holder reads at run time;
                                      its blob is part of the proof

## 7

Above `depends    troves/recorder/obs.ps1 | machines/editing-bay-1/bay/obs-portable-32.2.2.yml`

obs.ps1 takes the installed obs64.exe's hash from the bay's record at run
time and refuses any other copy (code-81, 2026-09-26). So the record is part
of what is proven: edit it, and the task verbs ask again. The file is named
by the installed version, so a new OBS through the bay means a new line here
and a new exercise.

## 8

Above `expect     {LOCALAPPDATA}/editing-bay-1/troves/recorder/obs.ndjson "how":"closed"`

The stop has to CLOSE it. A kill can leave a recording unfinished, and a
cycle that ends in one is not the behaviour being granted.

## 9

Above `host  deny  PowerShell(Remove-Item *obs-studio*)`

Theirs, by path. Reading a name to show it is untouched is the bay's job, and
`confirm` does it; nothing a session runs writes here.
