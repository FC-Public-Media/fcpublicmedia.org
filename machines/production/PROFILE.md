# production

Editing bay 1 by its sticker; Windows answers to `EDIT2`. The studio's strongest machine. Its state
on disk keeps the profile's old name, `%LOCALAPPDATA%\editing-bay-1\` (the OBS install, the pool's
task and log, the Whisper models), and so does the `editing-bay-1 pool` task. Profiles, sync and
grants: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| system | Windows 11 Home. i7-13700KF (24 threads), 32 GB, RTX 4080, 2 TB on `D:` |
| user | one local account, `fcpub`. Nothing below assumes an administrator |
| shells | Git Bash and Windows PowerShell 5.1. `python` on PATH is the Store stub; Python comes from uv |
| network | `Ethernet` (onboard) on the building's network, 10.1.10.x; `Ethernet 2` (USB 2.5GbE) on the switched network (Helm), 10.209.1.20. Windows' categories here are not to be believed (`Ethernet 2` carries a profile named "FC Public Media Guest 2", Public), so a rule names an address range, never a category. The Wi-Fi is unused |
| storage | the Drobo B810i over iSCSI (`10.209.1.179`): `E:` "TO ENHANCE", 1 TB, shared as `enhance`; and an HFS+ LUN, read only, that only this bay may log in to |
| screens | two HP E273s at the desk, and the rolling TV, which it drives for the kiosk ([roller-tv](../kiosk/roller-tv/README.md)) |
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
| `model.ps1`, `model.yml`, `models/`, `shapes/` | `fcpm model`: the language models, an instrument answering the switched network only (llama.cpp serving the spread in [`models/`](models/README.md), Qwen3.5 4B the default); its effort words, the shapes it offers, and the contexts it keeps |
| `helm.ps1` | `fcpm helm`: this bay's helm, the crew's `helm` line (the door's intake and pages only, on 8080), which takes what a peer helm passes it ([`../helms.yml`](../helms.yml)); its one rule |
| `keys.yml` | its own keychain (`fcpm keys`, [`../keys`](../keys)): a Cloudflare token for the site's deploy and the tanks' drain. See Deploy |
| `pools.yml`, `post.yml` | `fcpm pools` ([troves/pools](../../troves/pools/README.md)), `fcpm post` ([troves/post](../../troves/post/README.md)) |

## Inbound

What may reach this bay is one rule per need, placed by its verb (an administrator's step), naming a
program, a port and an address range:

| rule | placed by | admits |
|---|---|---|
| `fcpm-model inbound` | `fcpm model grant` | TCP 9931 to llama-server.exe, from 10.209.1.0/24 |
| `fcpm-helm inbound` | `fcpm helm grant` | TCP 8080, the crew's `helm` line (its Python moves, so the port), from 10.209.1.0/24 |
| `fcpm-roku relay inbound 8888` | `fcpm roku grant` | TCP 8888 to mediamtx.exe, from the local subnet |
| `fcpm-recorder obs64 HELO RTP` | by hand | UDP to obs64.exe, from the HELO (10.209.1.114) |

Clicking Allow on Windows' prompt makes a wider rule (any port, any address): obs64, obs-browser-page
and mediamtx.exe carry those now. Vendors' own rules (Adobe, DaVinci, Drobo) are theirs.

## Deploy

The site deploys from here the way it does from digitization: `fcpm deploy` (or `fcpm deploy --build`, which
uploads nothing) runs `bin/deploy-site` in Git Bash, from `refs\fcpublicmedia.org`, with uv's Python,
RubyInstaller's Jekyll and the bay's Node. It needs, once:

1. Ruby: `winget install --id RubyInstallerTeam.RubyWithDevKit.3.2 --exact --scope user`, then `ridk install`
   (MSYS2 and its toolchain, option 3). Then `bundle install` in `refs\fcpublicmedia.org\site`.
2. This bay's own Cloudflare token: made in the dashboard for bay 1 alone (`keys.yml` says which two
   permissions), then `fcpm keys take cloudflare CLOUDFLARE_API_TOKEN` and
   `fcpm keys take cloudflare CLOUDFLARE_ACCOUNT_ID` at the desk (a window, never a chat). It sits in
   `%USERPROFILE%\.config\fcpm\keys`, which anyone signed in as `fcpub` can read: the token may deploy
   the site and drain the tanks, and nothing else.
3. `fcpm check`: Jekyll 4 and both keys `ok`.

The board's deploy (`/deploy/`, `wizard:site+deploy`) runs on the machine whose helm holds it in
[`../helms.yml`](../helms.yml). Moving it here is that one line. The tanks' drain is a crew line held by one
machine at a time: it is in `services`, commented, until it moves here from digitization (its archive,
`%USERPROFILE%\fcpm\answers`, holds names and addresses, so it is the bay's to keep private).

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
