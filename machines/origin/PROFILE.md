# origin

FCPM's git origin on its own box, so the origin does not leave with digitization's SD card. Today
it is the **standby**: digitization pushes every branch and tag here each minute (`../digitization/origin-standby`).
It becomes the primary when it holds its own GitHub login; then remotes point here and intake runs here.

| | |
|---|---|
| computer | the HP t510 ([`../thin-client/PROFILE.md`](../thin-client/PROFILE.md)), booting a 29 GB USB stick |
| `names` | `linux Hostname origin`: `origin.local` |
| system | Debian 13, no desktop, DHCP. Built on another Debian box by [`build`](build), which erases the stick |
| `fcpm` | management, by key only, with sudo. Its key: digitization's |
| `git` | pushes, `git-shell` only. Its keys: digitization's standby key; keyholders' when it is primary |
| repos | `/srv/origin/<owner>/<repo>`, bare, as on digitization |

**Promote it** (the card is gone): on each checkout, `git remote set-url origin git@origin.local:/srv/origin/<owner>/<repo>`.
