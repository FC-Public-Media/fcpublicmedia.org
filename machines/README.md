# Machines

One folder per job a machine does, named for the job. A computer takes the job by answering to the
folder's `names` ([`binding`](binding)); what the computer is, and what it is called on its sticker
and by Windows, is in the folder's `PROFILE.md`. A computer without a job or a name yet keeps a
placeholder (`editing-bay-2`, `thin-client`). Profiles, sync and grants: [`docs/station.md`](../docs/station.md).
Gear comes from [`troves/`](../troves/README.md).

| job | looks after | the computer |
|---|---|---|
| [`production`](production/CREW.md) | recordings after they land: pools, transcription, episodes, release; it drives the roller TV for the kiosk and hosts digitization's tank | editing bay 1 (`EDIT2`) |
| [`kiosk`](kiosk/CREW.md) | the front door, the screens and the roller TV's page, check-in, and the pickup point, where digitization's grants are redeemed | the old editing bay 2 (`200-FCPANEDIT2`) |
| [`qr`](qr/PROFILE.md) | the kiosk's pickup point ([`troves/scanner`](../troves/scanner/README.md)) | a Raspberry Pi 3 |
| [`thin-client`](thin-client/PROFILE.md) | the kiosk's overflow console, beside the scanner | a donated HP t510 |
| [`origin`](origin/PROFILE.md) | FCPM's git origin on its own box; today a standby, a minute behind digitization's | the HP t510 |
| [`digitization`](digitization/CREW.md) | capture: arming, presence, the ledger, the recorders, the tank | station-node today; the OptiPlex 9020M is to take it over |

A job's folder holds its contract (`CREW.md`: what it looks after and what it serves) beside its
hardware (`PROFILE.md`, `names`) and, when it runs anything, its order (`services`) and its post
steps (`post.yml`); its own menu sits beside the folder (`machines/<job>.yml`). A computer named in
two jobs' `names` does both. Station-node uses the same model, so a job can
move between machines on either side. [`crew.yml`](crew.yml) is something else: which agents can be
mustered on an FCPM machine.

## Supervisor

Each job a machine does has one supervisor there, `machines/crew.py serve <job>` (verbs: its docstring), run by one service named for the job: a scheduled task on Windows (`machines/crew.ps1`), `fcpm-crew@<job>` on Linux (`machines/crew.sh`). Never one service per line.

- **Menu.** What a source can run is `<from>.yml`, written by this repository beside the source: `troves/pools.yml` beside `troves/pools/`, `machines/production.yml` beside `machines/production/`. A trove never names where it is mounted. Each `serves:` entry has `service`, `for`, `start`, and as needed `alive`, `needs`, `desktop`, `env`, `cwd`. Declaring starts nothing.
- **Order.** `machines/<job>/services`, one line per ordered service: `name keep from` or `name every N[smhd] from`, `from` being the source's path. A line naming nothing on a menu is reported, never run. The file is re-read on change: a new line starts, a removed one stops.
- **Running.** `keep` restarts after 5 s, doubling to 5 min, reset after 10 min up. `every` runs on its interval, never two at once. `desktop: true` runs only where there is a desktop; `needs:` waits for the named lines.
- **Status** is asked live by the service's `alive:` (a port that answers, a process pattern); anything already serving it counts. Keep process patterns specific: a loose one matches the shell that launched a test.
- **Start lines** fill `{python}` (Windows: uv, Python 3.12, pyyaml; Linux: the supervisor's own `python3`, with `python3-yaml`), `{home}`, `{code}`, `{repo}`. Children get no console; each line logs to `%LOCALAPPDATA%\editing-bay-1\crew\<name>.log`, or `~/.local/state/fcpm/crew/<name>.log` on Linux. A named mutex (Linux: a lock file there) keeps one supervisor per job per machine.
- **Windows only:** a scheduled task (S4U), a named mutex, the session id for "has a desktop", `taskkill /T`, `Win32_Process`.
- **Linux only:** one systemd instance per job, all under `fcpm.target` (`machines/fcpm-crew@.service`, `machines/fcpm.target`), restarted by systemd; `DISPLAY` for "has a desktop"; each line in its own process group; `/proc` for process patterns.
