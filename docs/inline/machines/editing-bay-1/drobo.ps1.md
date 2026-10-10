# `machines/editing-bay-1/drobo.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

drobo.ps1 -- this bay as the Drobo B810i's iSCSI initiator.

drobo.ps1 status        the Drobo's disks as Windows sees them, and their volumes
drobo.ps1 connect       every Drobo target a favorite, with one-way CHAP (asks the secret once)
drobo.ps1 header        read the HFS+ volume header: files, folders, used, dates
drobo.ps1 list OUT      walk the HFS+ catalog into OUT (folders.json, files.tsv, summary.txt)

Only this bay may log in: a second initiator on the HFS+ LUN corrupts it.
Nothing here writes to a Drobo disk. `header` and `list` open the HFS+ disk
for reading only, and never initialize, format or mount it.

The Drobo's data portal is a parameter; its target is found at the portal
(the one named com.drobo), and the HFS+ disk by its partition type, so no
serial number or disk number is written here. The CHAP name is this
initiator's IQN, as Dashboard set it; the secret is typed, held in memory,
and handed to the initiator's own persistent login. It is never written.

`connect` makes each of the Drobo's targets (one per LUN) a favorite that
carries the secret, so all of them come back after a restart. A target already
logged in stays logged in: its favorites are replaced underneath it, and a
mounted drive (E:, the enhance share) is never dropped. One left out is logged
in. A favorite saved without the secret (by hand, in the initiator's own
window) would be refused at startup; this is what puts that right.

A `list` can hold members' names: OUT stays on this machine, never in a repo.

`connect`, `header` and `list` need an administrator. Run from a plain shell,
they ask Windows for it (one prompt) and show their log when done.

Windows PowerShell 5.1, no modules. ASCII only.

## 2

Above `function Favorites {`

The favorites there now, as the initiator lists them. Only an
administrator can read them; iscsicli is the initiator's own tool.

## 3

Above `foreach ($f in Favorites) {`

1. Take away the Drobo's favorites as they stand, the ones without
the secret included. This logs nothing out: a favorite is only
what the initiator does at startup.

## 4

Above `foreach ($t in $ts) {`

2. Each target a favorite again, with the secret: the logged-in
ones by registering their session (they stay up), the others by
logging in.
