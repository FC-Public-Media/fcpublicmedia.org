# editing bay 1

Called *production*; the sticker says editing bay 1; Windows answers to `EDIT2`. The studio's
strongest machine. Profiles, sync and grants: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| system | Windows 11 Home. i7-13700KF (24 threads), 32 GB, RTX 4080, 2 TB on `D:` |
| user | one local account, `fcpub`. Nothing below assumes an administrator |
| shells | Git Bash and Windows PowerShell 5.1. `python` on PATH is the Store stub; Python comes from uv |
| network | Ethernet on the building's managed network and the guest Wi-Fi, category Public. The depot (`10.209.1.1`) answers only on the opt-in Wi-Fi |
| storage | the Drobo B810i over iSCSI (`10.209.1.179`): `E:` "TO ENHANCE", 1 TB, shared as `enhance`; and an HFS+ LUN, read only, that only this bay may log in to |
| screens | two HP E273s at the desk, and the rolling TV ([instruments/roller-tv](../../instruments/roller-tv/)) |
| not ours | the OBS in Program Files, browser profiles, display settings. People use this machine every week |

| file | what it is |
|---|---|
| `names`, `called` | `windows ComputerName EDIT2`; `production` |
| `MANIFEST` | carries `code/`, the pointers in `home/code/`, the git ignore (`.pr`), `fcpm.cmd`, `~/.local/bin` on PATH, and the compiled GRANTS |
| `code/` | the `~/code` root: `AGENTS.md` (read in place from the mirror), `bin/refs`, `bin/pool.ps1`, `refs.wanted` (the mirrors) |
| `GRANTS` | admits the recorder's OBS cycle; denies stopping any process by name |
| `gear.yml`, `bay/` | this bay's gear (replaces `../gear.yml`); a record per payload, and `runnables.proven` |
| `check.ps1` | gear, Developer Mode, `core.autocrlf`, the pool's task, `~/code` trust, the depot. Changes nothing |
| `audit.ps1`, `audition.ps1`, `drobo.ps1`, `share.ps1` | `fcpm audit`, `audition`, `drobo` (with `hfs_list.py`), `share` |
| `pools.yml`, `post.yml` | `fcpm pools` ([troves/pools](../../troves/pools/README.md)), `fcpm post` ([troves/post](../../troves/post/README.md)) |

## Bringing it up

1. At the desk: `winget install --id Git.Git --exact`.
2. Paste the start line from [README.md](../../README.md), *Setting up a machine*: it gets this
   repository and runs `fcpm install`. Clone station-node's mirror into `refs/` by hand, if wanted.
3. At the desk: Developer Mode (Settings > System > For developers), for symlinks without
   elevation; Claude Code from the vendor's installer into `~/.local/bin`, opened once in `~/code`
   to accept the folder (the root's server cannot start until then).
4. `fcpm pool install`: the per-user logon task that keeps the root's server up.
5. Gear: gh and Node through the bay, uv by winget for this user. `gh auth login` is the desk's.
6. `fcpm check`. What is still `WANTED` is what is left.

After step 2 every step is an `fcpm` verb. `.ps1` files run with `-ExecutionPolicy Bypass`; the
machine's policy is left alone. Windows settings can revert, so a differing `check.ps1` run is data.
