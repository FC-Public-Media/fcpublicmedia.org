# The Nest Cam trove

A 2015 Nest Cam (Dropcam's design) and the setup drive it carries. Retired: it offers only WPA or
WEP, and no network here takes it. Kept as the record of a setup volume
([`../README.md`](../README.md#rules)); its 24-hour stream concept is now [`../ptz/`](../ptz/README.md).

## Setup volume

USB `0525:A4A5` (the Linux USB gadget's stock ID) gives power and a 1.3 MB FAT drive, *Nest Cam
Setup*; video goes only over Wi-Fi. Hashes: `machines/editing-bay-1/bay/nest-cam-setup-2015.yml`.

| file | is |
|---|---|
| `Nest Cam Setup (Windows).exe` | 121,672 bytes, Authenticode signed *Dropcam, Inc.*, timestamped, so still valid |
| `Nest Cam Setup (Macintosh).app` | PowerPC/Intel 32-bit for Mac OS X 10.4; asks for an administrator; macOS no longer runs it |
| `.dcdata/offset` | `1312768`: where on the drive the camera listens |

Neither installs anything: each talks to the camera through the raw drive at `offset`, lends it the
internet, and opens `dropcam.com/setup/<camera>`, which now redirects to a `home.nest.com` failure.

## Device Access

Google's Smart Device Management API streams this model as WebRTC, 5 minutes at a time, extended with
`ExtendWebRtcStream`; the offer must carry a receive-only Opus line. Registration is US$5 once, from a
consumer Google account (not Workspace), with a Google Cloud project and an OAuth client.
