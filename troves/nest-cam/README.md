# The Nest Cam trove

**If you have a 2015 Nest Cam, this is what it brings with it and what that
is worth now.** Plugged into a computer by USB, the camera shows up as a small
drive called *Nest Cam Setup*, with a setup program for Windows and one for
Mac. This trove is about that drive. It is the first trove whose gear the
instrument carries itself, so it is also a draft of how a trove records a
**setup volume**: what is on it, by platform, what each piece does, and
whether to run it.

Status: read on 2026-10-05 from editing bay 1, which the camera was plugged
into. Nothing on the drive has been run. The camera has not been set up.

## What the camera is, on the cable

| | |
|---|---|
| USB | `0525:A4A5`, the Linux USB gadget's stock mass-storage ID. The camera is a small Linux computer pretending to be a disk |
| drive | *Nest Cam Setup*, 1.3 MB, FAT, with an `autorun.inf` that names the Windows program (Windows no longer runs autorun from USB) |
| video | none. The cable gives the camera power and the setup drive, and nothing else. Its picture goes over Wi-Fi to Google |

The volume carries a `.dcdata` folder and its programs are signed and named
by **Dropcam**, the company Nest bought in 2014. This camera is the Dropcam
design under Nest's name.

## The setup volume

| platform | file | what it is | runs here? |
|---|---|---|---|
| Windows | `Nest Cam Setup (Windows).exe`, 121,672 bytes | Authenticode valid, signed *Dropcam, Inc.*; certificate expired 2017-12-29 but timestamped, so Windows still calls it valid | not run |
| macOS | `Nest Cam Setup (Macintosh).app` | a universal PowerPC/Intel 32-bit build for Mac OS X 10.4, and asks for administrator rights | no: macOS dropped 32-bit programs in 10.15 |
| either | `.dcdata/offset` | the number `1312768`: where on the drive the camera listens | data |

Hashes are in the bay's record of the arrival,
`../../machines/editing-bay-1/bay/nest-cam-setup-2015.yml`. The programs are
Dropcam's, not ours to republish, so this repository holds their hashes and
not the files.

**They are not installers.** Neither puts anything on the computer. Read from
their own strings, each does one thing: open the drive as a raw disk, use the
spot at `offset` as a private line to the camera, and lend the camera the
computer's internet while it introduces itself. Then it opens a browser at

    https://www.dropcam.com/setup/<camera>?cv=..&fv=..&hv=..&platform=..

with the camera's connect, firmware and hardware versions, and the page there
finishes setup (Wi-Fi, account). On failure it opens
`https://www.dropcam.com/setup/failed?...`.

**Where that ends today:** on 2026-10-05, `dropcam.com/setup/...` answered
with a redirect to `home.nest.com/#camera/failed/setup`. The desktop path
leads to a failure page before it starts. Setting up this camera now goes
through Google's phone app, not this drive. Which app, and whether Google
still sets up this model at all, has not been checked.

## So, as an instrument

Not a studio camera in the sense of `../camera/`. That trove runs a camera
from the bay over the cable. This one can't be run from here: everything it
does goes through a Google account and Google's servers, and the cable does
nothing once it is set up.

## Waiting on Autumn

- **Whether a cloud camera belongs in the studio.** It sends what it sees to
  Google. In a public studio that includes members and guests, so it is a
  board-shaped question, not a setup step.
- **Whose Google account** it would live under, if it does. An FCPM account,
  not a person's, and its password in Credential Manager like the others.
- **What it is for.** A room monitor, a door camera, or a lost-and-found
  donation to pass on.

## Setup volumes, as a pattern

Some gear arrives with its own software on board. When it does, the trove:

1. copies the volume into the bay's `received\` and runs nothing from it;
2. records each file's hash and signature in the bay, as for any payload;
3. reads what each program does before calling it an installer;
4. checks whether the place it sends you still answers;
5. writes the verdict here, per platform.

The volume is the instrument's offer. The bay decides whether to take it.
