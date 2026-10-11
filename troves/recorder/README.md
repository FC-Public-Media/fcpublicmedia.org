# The recorder trove

The gear that records whatever makes files a node catches (a capture deck, the RØDECaster). macOS:
Audio Hijack, station-node's. Windows: the staff copy, a second, portable OBS beside the members'
one, whose websocket confirms start and stop and returns each file's path. No instrument is attached.

## The staff copy

It lives in `%LOCALAPPDATA%\<profile>\troves\recorder\obs\` with `obs_portable_mode.txt`, runs
`--multi --portable` as profile and scene collection **FCPM Recorder** (its title bar says so) and
records to `troves\recorder\recordings\`. Websocket 4456; its password is in Credential Manager
(`fcpm-recorder:obs-websocket`) and in OBS's own `config.json`. The bay asserts
`EnableAutoUpdates=false` after each install. The one grant, placed at the desk: obs-websocket cannot
pick its address, so a firewall rule blocks inbound for this `obs64.exe` (loopback is not filtered).

It never starts the virtual camera, has a shortcut named OBS, uses 4455 (the members' OBS and their
Streamer.bot), touches `HKLM\SOFTWARE\OBS Studio` or `%APPDATA%\obs-studio`, stops `obs64` by name,
or records to `%USERPROFILE%\Videos`.

## Files

- `gear.yml`: the recorder as gear.
- `bay/obs-portable.ps1`: `check` (changes nothing), `receive`, `verify`, `stage` (core binaries must
  be signed by OBS Project), `install`, `confirm` (shows `%APPDATA%\obs-studio` untouched). The
  host's records are in `machines/editing-bay-1/bay/`.
- `obs.ps1` (`fcpm recorder`): `status`, `prepare`, `start` (only the binary the bay recorded, with
  the grant in place and 4456 free), `record start|stop` (stop prints the file), `stop` (only the
  process id `start` wrote), `grant` (asks Windows for an administrator itself).

A crew asks for a recorder by name and schematic, not by path, and goes without it when absent.
