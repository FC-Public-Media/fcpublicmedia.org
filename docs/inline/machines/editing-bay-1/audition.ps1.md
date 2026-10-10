# `machines/editing-bay-1/audition.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

audition.ps1 -- Audition as gear on this bay: the enhance engine's panel.

audition.ps1 status    is Audition here, is the panel linked, is debug mode on, what did it probe
audition.ps1 install   turn on PlayerDebugMode and link the panel from the engine's mirror
audition.ps1 remove    unlink the panel and turn PlayerDebugMode off

The panel is the engine's, not this bay's: enhance/gear/audition/ (README
there). It is read where it sits, in the engine's mirror (~/code/refs/enhance,
kept on main by bin/refs pull), through a junction in this user's CEP
extensions folder. So it changes when the engine's main changes, and a
reformat loses nothing that git does not have. Nothing here needs an
administrator: the setting is under HKCU and a junction needs no rights.

PlayerDebugMode lets Audition load panels Adobe has not signed. It is per user
and per CSXS version; Audition 26.x reads CSXS.12. `remove` turns it off for
the versions this script turned it on for.

Windows PowerShell 5.1, no modules. ASCII only.
