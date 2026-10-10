# Crews

A crew is the work a machine takes on, under a contract: what it looks after and what it serves. A
machine wears one or more crews; a peer can wear the same crew beside it and offer the same services.
Station-node uses the same model, so a crew can move between machines on either side.

| layer | named for | lives at |
|---|---|---|
| troves | a discipline's gear | [`troves/`](../troves/README.md) |
| crews | the work | `crews/<crew>/`: `CREW.md` (contract), `services` (order), its own `residency.yml`, `post.yml` |
| machines | the hardware | [`machines/<name>/`](../docs/station.md#profiles), which says the crews it wears (`wears`) |

[`machines/crew.yml`](../machines/crew.yml) is separate: which agents can be mustered on an FCPM machine.

| crew | looks after | worn by |
|---|---|---|
| [`production`](production/CREW.md) | recordings after they land: pools, transcription, episodes, release | editing bay 1 (`EDIT2`) |
| `kiosk` | the media node: the front door, the screens, check-in ([`machines/kiosk-1/`](../machines/kiosk-1/PROFILE.md)) | kiosk-1 (`200-FCPANEDIT2`) |
| [`digitization`](digitization/CREW.md) | capture: arming, presence, the ledger, the recorders, the tank | station-node; editing bay 1 is a member |

## Supervisor

Each crew a machine wears has one supervisor there, `crews/crew.py serve <crew>` (verbs: its docstring), run by one service named for the crew (`crews/crew.ps1`). Never one service per line.

- **Menu.** A residency's `residency.yml` lists what it `serves:` (`troves/*/`, a mounted repository, or the crew's own). Declaring starts nothing.
- **Order.** `crews/<crew>/services`, one line per ordered service: `name keep from` or `name every N[smhd] from`, `from` being the residency's path. A line naming nothing on a menu is reported, never run. The file is re-read on change: a new line starts, a removed one stops.
- **Running.** `keep` restarts after 5 s, doubling to 5 min, reset after 10 min up. `every` runs on its interval, never two at once. `desktop: true` runs only where there is a desktop; `needs:` waits for the named lines.
- **Status** is asked live by the service's `alive:` (a port that answers, a process pattern); anything already serving it counts. Keep process patterns specific: a loose one matches the shell that launched a test.
- **Start lines** fill `{python}` (uv, Python 3.12, pyyaml), `{home}`, `{code}`, `{repo}`. Children get no console; each line logs to `%LOCALAPPDATA%\editing-bay-1\crew\<name>.log`. A named mutex keeps one supervisor per crew per machine.
- **Windows only:** a scheduled task (S4U), a named mutex, the session id for "has a desktop", `taskkill /T`, `Win32_Process`.
