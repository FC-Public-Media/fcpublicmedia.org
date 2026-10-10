# The Ki Pro trove

**If you have an AJA Ki Pro, this is how it records and how a bay reads it.**
The first-generation Ki Pro (about 2009) is a file recorder and player: video
in, Apple ProRes `.mov` out, onto a removable drive. The studio has one, named
**Studio Ki Pro**, at `10.1.10.63` on the studio network. It is the backup
recorder behind the TriCaster.

Status: found and read from editing bay 1 on 2026-10-06. Nothing was changed on
it. It usually sits powered off, so a bay sees it only after someone turns it on.

## The unit

| | |
|---|---|
| name | `Studio Ki Pro` |
| serial | `2B03548` |
| hardware address | `00:0C:17:08:0B:E8` (Wi-Fi `00:19:88:10:CE:8B`, Wi-Fi off) |
| address | `10.1.10.63`, static, gateway `10.1.10.1`. The label on its top says the same |
| firmware | 3.2 (`eParamID_SWVersion` `0x03020011`) |
| web page | `http://10.1.10.63/`, **no password** (`eParamID_Authentication` Disabled) |

Its LAN cable has a broken clip and works loose; it is often unplugged.

## How it is set up, as read

- **Video in: SDI**, the TriCaster's feed. No input was detected at the
  reading because the TriCaster was off.
- **Audio in: the two XLRs**, analog, +12 dBu, 2 channels. These appear to come
  from the Mackie DL32R's outputs 13 L / 14 R. Not traced by hand yet.
- **Records ProRes 422 HQ**, 1080i 29.97, free-run timecode from 01:00:00:00.
- **Clip names: `LPC Backup`, take 178.** About 178 backups have been made under
  that name. LPC is probably a city board covered by Fort Collins TV; not
  confirmed.
- **Record is armed by the front REC key.** RS-422 remote is off (Local Only).
- **The drive (slot D1) is in and empty**: no clips, 99% free. Whoever uses it
  copies recordings off and clears it.

## The hardware

- **Front:** the ribbed box in the middle is the **Storage Module**, a drive in
  a caddy; ⏏ on the left releases it once the unit is idle. The two slots on the
  right are card slots (`S1`, `S2`), empty and unused. Transport keys, a
  two-channel audio meter and gain knobs, headphones.
- **Rear:** SDI in/out, HDMI, component (BNC Y/Pb/Pr), composite (CVBS), two XLR
  audio inputs with a Line / Mic / +48V switch, RCA audio out, LTC in/out,
  LANC loop, lens tally, RS-422, Ctrl/TC, LAN, and FireWire (`Host`).

## Getting files off

The Storage Module carries its own FireWire 800 port. Pulled from the Ki Pro
and plugged into a Mac, it mounts as a drive, and the `.mov` files copy off.
That is almost certainly why the studio keeps FireWire cables. ProRes opens
on the bays (Premiere, Resolve, ffmpeg).

Whether this firmware can hand files over the network instead has not been
checked.

## Recording a show

1. Turn on the TriCaster and have it output program.
2. Turn on the Ki Pro and wait for it to finish starting.
3. Press the red record key. Stop it when the show ends.

The clip is named `LPC Backup` with the next take number. Changing that is a
setting on the CONFIG menu or the web page, and it belongs to whoever runs those
recordings.

## Reading it from a bay

The web page is the front panel in a browser. Underneath it is a small HTTP
interface; these are the reads used on 2026-10-06:

| ask | answers |
|---|---|
| `GET /descriptors` | an HTML page describing every parameter, with its `eParamID_…` id |
| `GET /config?action=get&paramid=eParamID_…` | one parameter's current value, as JSON |
| `GET /clips?action=get_clips` | the clips on the selected drive, as JSON |

Useful ids: `eParamID_TransportState`, `eParamID_DetectInputFormat`,
`eParamID_VideoInSelect`, `eParamID_EncodeType`, `eParamID_CurrentMediaAvailable`,
`eParamID_CustomClipName`, `eParamID_CustomTake`.

AJA documents `action=set` on the same endpoint for changing settings and
driving the transport. It has not been used here, and nothing here should use
it until whoever owns the LPC recordings agrees.

## Not yet

- **Digitizing tape through it.** Its composite and component inputs take
  analog video, which carries no HDCP. Switching `VideoInSelect` from SDI to
  composite would make it a capture deck for VHS and similar sources, with
  ProRes files out. It is set up for the LPC backups now, so that is a person's
  decision, not a trove's.
- **A start/stop verb** (`fcpm`), through `action=set`, once the above is
  agreed.
- Confirming the DL32R 13/14 audio and what feeds the HDMI by tracing cables.
- A replacement LAN cable with a working clip.
