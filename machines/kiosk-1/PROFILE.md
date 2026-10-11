# kiosk-1

The media node: FCPM's own station-like host, called `kiosk`, answering to `200-FCPANEDIT2`
(names: [`code/AGENTS.md`](code/AGENTS.md)). The old editing bay 2, retired from media work.
Screens and content: [`docs/kiosk.md`](../../docs/kiosk.md).

## Host

- Windows 10 Pro 1909, Dell Precision T3600, 12 GB, Quadro 4000. IT-managed (CyberArk EPM,
  McAfee, SysAid, DameWare, Cisco AnyConnect). A user account, no administrator. winget v1.3,
  too old for zip or portable packages. Gear: the shared [`../gear.yml`](../gear.yml); Claude
  Code came by the PowerShell installer (`provisioner: hand`). Crew: one person at a console.
- Tooling from vendor releases, hash- and signature-checked: uv 0.12.18 (`uv python install
  3.13`), Node 24.21.0 LTS in `%LOCALAPPDATA%\media-node\node`, gh 2.101.0 in `~/.local/bin`
  (login in the keyring). No Ruby: CI builds the site.
- The broker runs here: `node --test worker/test/*.test.mjs`; `npx wrangler@4 dev --ip 127.0.0.1
  --var RP_ID:fcpm.localhost` on invented `*.localhost` hosts, passkeys from a DevTools virtual
  authenticator. `workerd` crashes on the system's Visual C++ 14.32: copy `msvcp140.dll`,
  `vcruntime140.dll`, `vcruntime140_1.dll` from Edge's application folder next to
  `workerd.exe`, again after each wrangler update.
- Checkout: `C:\Users\FCPM-user\code\work\fcpublicmedia.org@media-node`, branch `media-node`.
- No keyboard or mouse, out of reach: the per-user task `fcpm weekly` pulls `ref/`, where the
  root's instructions live, once a week (log `%LOCALAPPDATA%\fcpm\weekly.log`).

## The door

`door.py` (its docstring lists verbs and routes), on `[::]:8080`, at
`http://200-fcpanedit2.local:8080/`. The per-user task `media-node door` starts `supervise` at
logon and every five minutes (`door.py startup --install`); a named mutex keeps one running.
Log: `%LOCALAPPDATA%\media-node\door.log`.

| job | what it does |
|---|---|
| bounce | `serve` exits 75 when the checkout's commit moves; `supervise` restarts it; pages reload on `/revision` |
| pull | every 5 min, rebases `media-node` onto `origin/main`; a dirty tree or a conflict is left as it was |
| screens | every 30 s, one Edge kiosk per panel in `node.yml`, profile under `%LOCALAPPDATA%\media-node\screens\`: missing, astray, silent 120 s or moved is relaunched; covered is raised; none while a monitor is gone, or while stepped aside (a page's Minimize, until 10 min without input) |
| depot | scans the router's shares every 15 s; files are `declared` (a `.sha256` beside), `arriving` or `unwitnessed`; the index stays in memory |
| wall, turn | the wall, rewritten every 60 s to the depot share; `/turn/` is its shell on a panel here |
| server | every minute keeps `claude remote-control --no-create-session-in-dir` at `~/code` (output `server.*`); bounces it onto a newer `claude.exe` after 15 calm minutes; a killed one holds `~/code` a few minutes ("already served"); `door.py server` |
| sessions | starts none; snapshots `claude agents --json` to `sessions.json`, a record only; `door.py sessions` |
| camera | `door.py camera arm`, or the desk's button: a headless Edge reads a `wizard:kiosk+lights` reply; lights keep the screens awake |
| Dropbox | `TO DROPBOX` goes up to `dropbox.to`, removed once Dropbox holds the same bytes; off until `door.py dropbox link` |
| HELO | sets the AJA HELO's clock from this one when over 90 s out, never while it records |
| TI-89 | serves the runner from `ref/ti-89`, fast-forwarded with the pulls; the ROM only to this box |

## Asked of IT

- **Sign in automatically.** After a reboot nothing runs until somebody signs in.
- **Allow TCP 8080 in** for the venv's `pythonw.exe`, once `/kiosk/wifi/<n>` answers only the box.

## Files

`door.py`, `node.yml` (what it shows where), `m365-token.ps1` (a Microsoft 365 token signed by
the non-exportable certificate in `Cert:\CurrentUser\My`), `bookings.sample.yml` (a made-up
week, every booking "Sample"), `GOTCHAS.log` and `gotcha` (`merge=union`), `names`, `called`,
`GRANTS` (what sessions may run), `MANIFEST` (what `../sync` places), and `code/` and
`home/code/` (the `~/code` root, its instructions read from the mirror). Secrets live in Windows
Credential Manager and the certificate store. Publishing stays with station-node.
