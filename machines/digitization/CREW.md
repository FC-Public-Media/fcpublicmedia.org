# digitization

Digitization streams and records the studio: many inputs, a capture toolchain, and outlets (the tank, the live stream, the rolling TV). It stops at the depot: it delivers finished, verified captures, and timelines and editing are production's. Station-node wears it today and is to hand it to [`machines/digitization/`](../../machines/digitization/PROFILE.md). It has no `services` order yet.

## Roles

A role is filled by a member: any machine, on any platform, that meets the role's contract.

| role | contract | free | filled by |
|---|---|---|---|
| capture | arms the inputs, records them, hands each finished capture to the tank in the depot's shape | recorder, platform, timer, scratch disk | station-node (macOS); `digitization` (Debian, templating) |
| tank host | keeps the tank attached and shared as `enhance` | the initiator; how the share is served | editing bay 1 |
| screen | puts an outlet on the rolling TV | how it is driven | editing bay 1 |

The tank is the Drobo B810i's 1 TB NTFS partition, attached over iSCSI to one initiator and shared from `E:\` as SMB `enhance`: capture writes, production reads and writes. Production's pools read every disk a capture rests on, in place, so capture's scratch is shared too, with production's read grant. What lands on the tank, and in what shape, is declared here; the tank host only keeps the share up.

## Gear

Inputs: RØDECaster Pro II (the podcast studio as one merged pair), ATEM Mini Pro (four HDMI into one program), AJA HELO (hardware encoder, also an outlet). Monitor: Integra DTR-6.3. Recorders: Audio Hijack on macOS, OBS on Windows ([`troves/recorder`](../../troves/recorder/README.md)); each crew runs its own OBS copy, profile and ports. Outlet: the rolling TV ([`troves/kiosk-screen`](../../troves/kiosk-screen/)). Device facts: [`rodecaster-pro-ii`](https://github.com/FC-Public-Media/rodecaster-pro-ii), [`atem-mini-pro`](https://github.com/FC-Public-Media/atem-mini-pro), [`aja-helo`](https://github.com/FC-Public-Media/aja-helo), [`drobo`](https://github.com/FC-Public-Media/drobo). RØDECaster multitrack (Settings → Outputs → Multitrack → USB) puts 16 channels on USB 1, four of them the mics, one per combo input; USB 2 carries a stereo pair only.

## Depot contract

The depot's, not digitization's to reshape. Captures land on the tank and stay; production's work is written beside them.

- One folder per capture session: `<instrument>-YYYY-MM-DD-HHMMSS/`. Files as recorded, modified times kept, never changed in place: an improvement is a new file beside the original.
- `SHA256SUMS` is written last; a folder without it is unfinished.
- Capture records to a local scratch, never straight to the tank: a network stall mid-recording breaks the file. On close: copy, check, write `SHA256SUMS` on the tank, remove the local copy. If the tank does not answer and take a write, the file is held, retried on the next timer, and reported after a few minutes.

## Members

- **station-node, capture:** `instrument arm`/`disarm` open an `.ahcommand` in Audio Hijack; a file still being written is `lsof` or touched in the last 10 s; the tank is remounted every 2 min from the Keychain; `instrument catch` copies, verifies and writes `SHA256SUMS`; `instrument teardown` evicts after closing; the timer is launchd.
- **A capture member gives**, per input: a recorder installed, licensed and granted the device (on Windows, the recorder trove's portable OBS plus one firewall rule); the tank's credential in its own store; a port and spool space; one timer job; a share of its scratch with production's read grant. **A tank host gives** the initiator, the share and its accounts.
