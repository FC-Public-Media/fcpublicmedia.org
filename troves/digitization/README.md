# The digitization pack

**If you are the machine that streams and records the studio, this is what you
are made of.** A pack is a trove whose gear is other troves: it names them, and
says how they chain. It carries none of them.

Status: draft, for reference. Written by station-node, which is the only machine
doing this job today, and kept here because most of what it names is FCPM's.
Nothing reads this directory yet.

## What digitization is

Streaming and recording. The inputs are many, and that is the point; the
toolchain in the middle is the speciality; the outlets will keep multiplying.

```
inputs  ->  the toolchain  ->  outlets
many        capture, spool,    the enhance queue, the live stream,
            hand on            the roller TV, ...
```

Where it stops: **the depot.** Digitization delivers finished, verified captures.
Timelines, scrubbing and editing are production's. The two crews meet at the
contract below and share nothing else.

Crews are named by the work, not by the machine: *production* may run on two
bays at once, and *digitization* is whichever machine stands up for it. Today
that is station-node.

## What the pack names

Each row says how the pack stands to it. **Plays**: the pack drives it.
**Uses**: gear the pack runs its own copy of. **Relies on**: something a
neighbour runs, which the pack needs and does not run.

| what | role | how | where its facts live |
|---|---|---|---|
| RØDECaster Pro II | input: the podcast studio, as one merged pair | plays | [`rodecaster-pro-ii`](https://github.com/FC-Public-Media/rodecaster-pro-ii) |
| ATEM Mini Pro | input: four HDMI into one program | plays | [`atem-mini-pro`](https://github.com/FC-Public-Media/atem-mini-pro) |
| AJA HELO | input and outlet: the hardware encoder; records and streams | plays | [`aja-helo`](https://github.com/FC-Public-Media/aja-helo) |
| Integra DTR-6.3 | monitor: the room-sized one | plays | no trove yet |
| roller TV | outlet: a screen on a stand | plays, through editing bay 1 | [`../kiosk-screen/`](../kiosk-screen/), [`../../instruments/`](../../instruments/README.md) |
| the enhance queue | outlet: where captures land for production | relies on | [`../pools/`](../pools/README.md) |
| the Drobo B810i | the disk under the enhance queue, attached and shared by editing bay 1 | relies on | [`drobo`](https://github.com/FC-Public-Media/drobo) |
| Audio Hijack | gear: the recorder on macOS | uses | [`../recorder/`](../recorder/README.md) |
| OBS | gear: the recorder on Windows, and more | uses, its own copy | [`../recorder/`](../recorder/README.md) |

Coming, not named yet: the VCR; a multichannel interface, so the podcast studio
can leave as separate channels as well as the merged pair; the rack compressors
that sit in front of it.

### Uses: one gear, several crews

OBS is the case that will recur. Production uses it, the members use it, and
digitization will. Each brings its own copy, profile and ports, as the trove
rules already say, so a pack that uses OBS never touches anyone else's. The ATEM
may go the same way: one device, with configurations instanced per use. Not
designed yet.

### Relies on: what someone else runs

The Drobo is run by editing bay 1, partly as a favour to digitization. The pack
cannot run it and should not try. What it can do is **name the neighbour and ask,
never assume**: before handing on, check that the enhance share answers and takes
a write. A failed check is not something digitization can fix. It holds the
capture and says so (see *The spool*).

Whether that check becomes a handshake between stations, one supervisor asking
another whether it is up, is open. It is where a pack starts needing to know its
neighbours.

## The contract with the depot

Not ours to reshape; the depot's, written down here so both crews read the same
words.

- One folder per capture session: `<instrument>-YYYY-MM-DD-HHMMSS/`.
- The files as recorded, modified times kept.
- `SHA256SUMS` written **last**. A folder without it is not finished, and
  whoever watches the queue waits.
- What each capture should also say, so a timeline can use it later: which
  input, when it started, and where the session broke. Cheap at capture time,
  hard to recover afterwards. Not done yet.

## The spool

The recorder writes to a local disk, never straight to the share: a network
stall during a write that runs for an hour is a broken file, and no recorder
retries it. So the local disk is a buffer, not a home:

1. a file closes; the catch runs at once;
2. it is copied, checked, and `SHA256SUMS` is written on the share;
3. the local copy is removed;
4. if the share is not there, the file waits, the catch retries on the next
   timer, and anything held longer than a few minutes is reported.

Holding is what happens when something is wrong, not the normal state.

## What a host must give

Everything else is the pack's. These four it cannot carry, **per input**:

1. **A recorder, granted.** Installed, licensed where it needs one, allowed the
   microphone or the capture device, and allowed to be driven. On Windows the
   recorder trove carries a portable OBS, so this shrinks to one firewall rule.
2. **The share's credential**, in the host's own store. The pack names the share;
   it never holds the password.
3. **A port, and spool space.** Every new input costs one. This is why
   digitization wants a machine of its own, not a bay's last free port.
4. **A timer.** One recurring job, to catch what was held.

Not declared, because any machine has them: a system Python, a scheduler, a
local disk.

## Open

- The Integra DTR-6.3 has no trove.
- The cross-station check for what the pack relies on.
- Instanced configurations for gear that several crews use (ATEM, OBS).
- The capture metadata in the contract.
