# The Nest Cam trove

**If you have a 2015 Nest Cam, this is what it brings with it and what that
is worth now.** Plugged into a computer by USB, the camera shows up as a small
drive called *Nest Cam Setup*, with a setup program for Windows and one for
Mac. This trove is about that drive. It is the first trove whose gear the
instrument carries itself, so it is also a draft of how a trove records a
**setup volume**: what is on it, by platform, what each piece does, and
whether to run it.

Status: **retired, 2026-10-06.** Its setup drive was read on 2026-10-05 from
editing bay 1, and nothing on it was run. The camera offered only WPA and WEP
when Autumn last set it up, and no network in the building, including her own
router as it is now, offers one it will join. The notes stay because they
hold up past this camera: the 24-hour stream concept (below) and the setup
volume pattern (`docs/troves/README.md`, *Gear that brings its own software*).

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

## What it was for: a 24-hour stream, as a proof of concept

This outlived the camera. `../ptz/` picks it up.

Autumn, 2026-10-05: the studio has talked about security cameras and would
buy something better than a Nest for that. This one is for demonstrating the
*concept*: a picture that is live all day and night and shown. The
Pocket 6K is not needed to prove that. The donated Fort Collins city TV PTZ
cameras and the TriCaster Flex are a separate track, and this has nothing to
do with them.

**What it looks at** is the privacy control. It is aimed so that, ideally,
no one is ever on it: down into a corner, or at the kiosk so that people
passing by are seen only from the shoulder down. **Audio stays off** at the
camera, and the page that shows it plays muted besides.

**How the picture leaves Google** (Device Access, the Smart Device
Management API; [Google's camera page][sdm-cam], read 2026-10-05):

- Every legacy Nest Cam is supported. On the Google Home app this model
  streams **WebRTC**; on the old Nest app it streamed RTSP. It can be on
  only one of the two at a time, and the Nest app is on its way out, so this
  plan is WebRTC.
- A stream lasts **5 minutes** and is kept alive with `ExtendWebRtcStream`.
  24 hours is a loop that extends it, and starts a new one when that fails.
- The offer has to include an Opus audio line, receive-only. The protocol
  requires it; it doesn't make anything audible.
- Registering is **US$5 once, per account, and only from a consumer Google
  account** (gmail.com), not Workspace ([get started][sdm-start]). It also
  needs a Google Cloud project and an OAuth client.
- The share-a-public-link feature was in the Nest app and is not in Google
  Home, so that shortcut is gone.

**The shape, following `../kiosk-screen/`:** a page served on this host
that holds the WebRTC session and shows the picture muted, fullscreen, on
whichever screen it is given. The OAuth refresh token goes in Credential
Manager and never in a file. The camera's power should come from a wall
adapter, not the bay: the bay restarts, and while it is plugged into the
bay the camera keeps putting its setup drive on the bay.

[sdm-cam]: https://developers.google.com/nest/device-access/api/camera
[sdm-start]: https://developers.google.com/nest/device-access/get-started

## What it would have waited on

- **Whose Google account.** The camera is probably still on the account it
  was a baby monitor under. The demo needs a consumer Google account to own both
  the camera and the Device Access registration. FCPM's own would be best;
  Workspace can't register.
- **Shown where.** A screen in the studio is the smallest step. Streaming it
  to the public is a different, board-shaped question, because whatever
  passes under the camera goes out with it.
- **The $5 registration**, made from that account.
- Whether a cloud camera belongs in the studio for real is the board's,
  and this demo is meant to inform it, not to answer it.

