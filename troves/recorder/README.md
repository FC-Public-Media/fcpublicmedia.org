# The recorder trove

**If you have something that produces recordings a node has to catch, this is
the gear that records it.** A capture deck, a multiviewer, the RØDECaster:
hardware played through a recorder, whose files are caught and handed on.

Status: draft. Nothing reads this directory yet, and no instrument is attached
to editing bay 1 yet. What is here is the recorder itself, brought aboard ahead
of the hardware, so that the first capture is not also the first install.

## What a recorder has to answer

Station-node's `docs/instruments.md`, *Controlling it*, measured Audio Hijack
against four rows and then said: *"A digitization kiosk on Windows has none. It
will need a recorder that answers the same four rows."* These are those rows,
with the three that digitization adds:

| row | macOS: Audio Hijack | Windows: OBS, portable |
|---|---|---|
| **start / stop** | a `.ahcommand` file, one-way; success is read back from the disk | obs-websocket `StartRecord` / `StopRecord`, which answer |
| **is it recording** | a file open under `from:` | `GetRecordStatus` |
| **a file finished** | `fileDidEnd`, not wired | the `RecordStateChanged` event, which carries the file's path |
| **what the feed carries** | the RØDECaster App, by hand | the scene collection and profile, which are files this trove can carry |
| **split on silence** | built in: *Start new file* at -60 dB / 2 s | not built in. Advanced Scene Switcher can start and stop on an audio level; it would be a second payload, because a portable OBS does not load plugins installed for the system copy |
| **many tracks, one file** | no | up to six audio tracks in MKV |
| **lossless video** | no | FFV1 in MKV through the custom FFmpeg output; NVENC for proxies |

The macOS column is station-node's, and it stays there. This trove cites it so
that the two answers can be read side by side; it does not carry Audio Hijack.

## The Windows answer: an OBS nobody sits down to

The bays are production machines. Editing bay 1 already has an OBS that people
use, installed by winget into `Program Files`, with somebody's show in
`%APPDATA%\obs-studio`: profiles, scene collections, and a websocket on 4455
with a password. **None of that is ours, and this trove never writes to it.** The
procedure's `confirm` lists that folder, names and sizes and times but never
contents, before and after it runs, to show it was left alone.

So the recorder is a second, separate OBS:

- **Portable.** Unzipped to `%LOCALAPPDATA%\<profile>\troves\recorder\obs\` with
  `obs_portable_mode.txt` beside `bin\`. OBS then keeps every setting under its
  own `config\` folder. Checked against 32.1.1's `obs64.exe`, which looks for
  that file and for `portable_mode.txt`.
- **`--multi`**, so it runs while a person has the system OBS open, and neither
  one asks the other to close.
- **Its own profile and scene collection**, named `fcpm-recorder`, launched with
  `--profile` and `--collection`, and carried by this trove as templates.
- **Its own websocket port, `4456`, and its own password**, kept in Credential
  Manager under `fcpm-recorder:obs-websocket`, never in a file here.
- **No self-update.** `EnableAutoUpdates=false` in its `global.ini`, asserted
  by the bay after every install, so the bay stays the only way a version
  arrives. Ablative's first payload went around its bay by a different road;
  this closes the one road OBS itself offers.
- **No admin to install.** Everything lands in a folder this user owns.
  Station-node's gear page calls that the strongest argument there is for a
  node owning an install path.

### The one grant: inbound, refused

obs-websocket has no setting for which address it listens on: its config holds
`server_enabled`, `server_port` and `server_password`, and nothing else (read
from 32.1.1's `obs-websocket.dll`). So the first time the recorder's websocket
listens, Windows Firewall asks whether `obs64.exe` may accept connections.

**The answer is no, and it is placed in advance.** Windows Firewall does not
filter loopback, so a block rule for this one executable leaves the recorder
reachable from this machine and from nowhere else. That is exactly what a
recorder wants: the node that arms it runs here. The rule needs an
administrator, so it is placed at the desk as part of install, the way
station-node's `LAUNCH.md` says grants are placed: before the job runs, never
during.

## Files

| | |
|---|---|
| `gear.yml` | the recorder as gear: what it is, where it comes from, who may replace it |
| `bay/obs-portable.ps1` | the procedure that brings it aboard. `check` changes nothing |

A payload record is the host's, not the trove's: it says what arrived on one
machine on one day. Editing bay 1's live in `machines/editing-bay-1/bay/`.

## Open

- **Whether OBS is the recorder for digitization at all** waits on the capture
  hardware, which waits on HDCP. Bringing OBS aboard first is cheap and changes
  nothing that is anybody else's.
- **Silence**, as above. The design digitization described is *armed, then
  catch what arrives while the signal is not flat*, and OBS does not split on
  silence by itself.
- **The profile and scene collection templates** are not written. They depend on
  what is plugged in.
