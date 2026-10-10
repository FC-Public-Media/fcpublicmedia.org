# digitization: the crew that streams and records the studio

**The contract for digitization, the way it is split up today.** It names the
troves it plays, splits the work into roles, and says which machine fills each
role. It carries none of the troves. Crews are explained in
[`docs/crews/README.md`](../README.md).

Status: draft, written by station-node, which wears this crew today and means to
vacate it for [`../../machines/digitization/`](../../machines/digitization/PROFILE.md).
It lives here because most of what it names is FCPM's, and because its members
are FCPM machines. There is no `services` order yet.

## What digitization is

Streaming and recording. The inputs are many, and that is the point; the
toolchain in the middle is the speciality; the outlets will keep multiplying.

```
inputs  ->  the toolchain  ->  outlets
many        capture, spool,    the tank, the live stream,
            hand on            the roller TV, ...
```

Where it stops: **the depot.** Digitization delivers finished, verified captures.
Timelines, scrubbing and editing are production's. The two crews meet at the
contract below and share nothing else.

## A crew of roles, with members

A crew is named by the work, not the machine. It is made of **roles**, and a
role is filled by a **member**: a machine that answers the role's contract. The
membership is plural. Digitization already has a Windows member; station-node
just does not hold it.

Each role fixes what has to be true and leaves the rest free. Any machine that
meets the contract can fill it, on any platform.

| role | fixed: the contract | free | filled today by |
|---|---|---|---|
| **capture** | arms the inputs, records them, and hands each finished capture to the tank in the depot's shape. Anywhere a capture rests on the way, it is shared, and production is granted read | the recorder, the platform, the timer, the scratch disk | station-node (macOS); `digitization` (Debian), templating |
| **tank host** | keeps the tank attached and shared as `enhance`: capture is granted write, production read and write | which machine is the initiator; how the share is served | editing bay 1 (Windows) |
| **screen** | puts an outlet on the roller TV | how it is driven | editing bay 1 (Windows) |

Outside the crew, and relied on: **production's pools**, the view production
shepherds the pipeline through. It runs on production's machine and reads every
disk where a capture rests, in place. Nothing is moved somewhere else to be seen
better, so every such disk is served to it, with a grant, by whoever holds it.

| disk | held by | served as | granted |
|---|---|---|---|
| the tank | tank host | SMB `enhance` | capture: write; production: read, write |
| capture's scratch | capture | SMB, name not chosen | production: read |

## What the pack names

| what | for | role that plays it | where its facts live |
|---|---|---|---|
| RØDECaster Pro II | input: the podcast studio, as one merged pair | capture | [`rodecaster-pro-ii`](https://github.com/FC-Public-Media/rodecaster-pro-ii) |
| ATEM Mini Pro | input: four HDMI into one program | capture | [`atem-mini-pro`](https://github.com/FC-Public-Media/atem-mini-pro) |
| AJA HELO | input and outlet: the hardware encoder; records and streams | capture | [`aja-helo`](https://github.com/FC-Public-Media/aja-helo) |
| Integra DTR-6.3 | monitor: the room-sized one | capture | no trove yet |
| the Drobo B810i, its 1 TB partition | the tank: where every capture lands | tank host | [`drobo`](https://github.com/FC-Public-Media/drobo) |
| roller TV | outlet: a screen on a stand | screen | [`troves/kiosk-screen`](../../../troves/kiosk-screen), [`instruments`](../../instruments/README.md) |
| Audio Hijack | gear: the recorder on macOS | capture | [`troves/recorder`](../../troves/recorder/README.md) |
| OBS | gear: the recorder on Windows, and more | any, its own copy | [`troves/recorder`](../../troves/recorder/README.md) |

Coming, not named yet: the VCR; a multichannel interface, so the podcast studio
can leave as separate channels as well as the merged pair; the rack compressors
that sit in front of it.

**One gear, several crews.** OBS is the case that will recur. Production uses it,
the members use it, and digitization will. Each brings its own copy, profile and
ports, as the trove rules already say, so a pack that uses OBS never touches
anyone else's. The ATEM may go the same way: one device, with configurations
instanced per use. Not designed yet.

**The tank is ours, emphatically.** The configuration is built on that
partition. It could have been attached by the capture machine; it is attached by
editing bay 1, because the Drobo speaks iSCSI to one initiator and the data path
stays on Windows. What the tank is for, and what lands on it in what shape, is
declared here. The tank host is not asked to understand digitization, only to
keep the share up.

## The members' answers

Each member writes down how it fills its role. These are answers, not
questions: what is actually running.

### capture: station-node, macOS

| verb | how |
|---|---|
| start and stop a recording | an `.ahcommand` file opened in Audio Hijack (`instrument arm`, `disarm`) |
| a file finished | Audio Hijack's `fileDidEnd`; not wired yet |
| is a file still being written | `lsof`, and nothing touched in the last 10 s |
| is the tank there, and does it take a write | the share is mounted, re-mounted every 2 min from the Keychain credential |
| catch, verify, `SHA256SUMS` last | `instrument catch` |
| evict what is verified | `instrument teardown`, after closing; to become right after each catch |
| hold, and say so | not built yet |
| the timer | launchd |

### capture: `digitization`, Debian (templating)

A Dell OptiPlex 9020M, live-booted from a USB stick, with no internal drive yet
(whether one is on hand is being found out). Its profile is
[`../../machines/digitization/`](../../machines/digitization/PROFILE.md). No
Audio Hijack on Linux, so every verb above needs an answer here; none is written
yet. Its scratch for now would be the Buffalo attached to it: a stopgap, because
that array is degraded and still holds what is waiting to move to the Drobo.

### tank host and screen: editing bay 1, Windows

For editing bay 1 to write. What station-node knows from outside: the Drobo's
partition is a 1 TB NTFS volume, attached over iSCSI and shared from `E:\` as
`enhance`. The rest is the bay's to state: the initiator and how it reconnects
after a restart, the share and who may read and write it, what it watches on the
Drobo, and how it drives the roller TV.

## The contract with the depot

Not ours to reshape; the depot's, written down here so both crews read the same
words. The tank is a working surface, not a mailbox: captures land and stay, and
what production does to them (nominations, suppressions, cuts, the gap-free
renders sent to processing, transcripts) is written beside them and fetchable.

- One folder per capture session: `<instrument>-YYYY-MM-DD-HHMMSS/`.
- The files as recorded, modified times kept. **Never changed in place**: an
  improvement is a new file beside the original.
- `SHA256SUMS` written **last**. A folder without it is not finished, and
  whoever watches the queue waits.
- What each capture should also say, because the pools place it on a timeline
  and cut inside it: which input, when its sound started, and where the session
  broke. Cheap at capture time, hard to recover afterwards. Not done yet. Audio
  Hijack's file names give when the *silence* began, not the sound, and the
  rule fails across a power cut (the RØDECaster trove measured both).

## The scratch

The capture member records to a local disk, never straight to the tank: a
network stall during a write that runs for an hour is a broken file, and no
recorder retries it. So the local disk is a buffer, not a home:

1. a file closes; the catch runs at once;
2. it is copied, checked, and `SHA256SUMS` is written on the tank;
3. the local copy is removed;
4. if the tank is not there, the file waits, the catch retries on the next
   timer, and anything held longer than a few minutes is reported.

Holding is what happens when something is wrong, not the normal state. While a
capture is held it is still in view: the scratch is one of the disks the pools
read, as a stage of its own. Before
handing on, capture asks whether the tank answers and takes a write; it never
assumes. A failed check is not something capture can fix: it holds, and says so.

## What a member's machine must give

Everything else is the pack's. What the pack cannot carry, by role:

**capture**, per input:

1. **A recorder, granted.** Installed, licensed where it needs one, allowed the
   microphone or the capture device, and allowed to be driven. On Windows the
   recorder trove carries a portable OBS, so this shrinks to one firewall rule.
2. **The tank's credential**, in the machine's own store. The pack names the
   share; it never holds the password.
3. **A port, and spool space.** Every new input costs one. This is why capture
   wants a machine of its own, not a bay's last free port.
4. **A timer.** One recurring job, to catch what was held.

5. **A share of its scratch**, and the grant that lets production read it.

**tank host**: the initiator, the share, and the accounts that may use it.

Not declared, because any machine has them: a system Python, a scheduler, a
local disk.

## The RØDECaster's channels

Stereo by default. With **Settings → Outputs → Multitrack → USB** on the device,
USB 1 carries 16 channels, of which four are mics, one per combo input; the rest
are the mix, Bluetooth, the pads and the USB returns. USB 1 only: USB 2 runs at
12 Mb/s and carries a stereo pair. Not yet tried here. More than four separate
voices still needs a separate interface.

## Open

- Editing bay 1's answers, above, and the Debian member's.
- An internal drive for the Debian member, so the scratch is not the Buffalo.
- **Whether capture should keep splitting on silence.** If the pools can cut
  inside a file and suppress what lies between, one continuous recording per
  session keeps the timing whole and leaves what is kept to the people
  shepherding it. Splitting decides that at recording time, for good.
  Production's to answer, as their cut tools arrive.
- The Integra DTR-6.3 has no trove.
- Whether capture's check on the tank becomes a handshake between members, one
  supervisor asking another whether it is up.
- Instanced configurations for gear that several crews use (ATEM, OBS).
- The capture metadata in the contract.
