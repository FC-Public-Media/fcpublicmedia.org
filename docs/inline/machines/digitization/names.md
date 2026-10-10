# `machines/digitization/names`

Moved out of the file. Unreviewed.

## 1

Above `# platform   key        value`

What this machine is called, declared. Same rules as ../kiosk-1/names:
intent, not a mirror. `../binding` asks the machine and reports a mismatch.

DECIDED 2026-10-09 (Autumn): the machine takes the crew's name, `digitization`.
It is the identity FCPM bootstraps under. The same code is meant to be handed
off later under a new name, so this file is the one place the name lives, and
renaming should stay cheap.

NOT APPLIED YET. The box boots Debian live and answers `debian` today. Setting it
is a deliberate act (`sudo hostnamectl hostname digitization`), and on a live
boot it lasts only until reboot, until the stick carries it.

The first Linux profile here. Check on the machine with `hostname`.
