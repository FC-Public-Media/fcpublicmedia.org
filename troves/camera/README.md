# The camera trove

**If you have a camera on a USB cable, this is the gear that runs it.** A
console that shows everything the camera reports and sets everything it lets
us set, and operator pages built on it: simple pages for one job, like a page
of curated presets where one button sets the camera up.

Status: built 2026-09-28 on editing bay 1 against the studio's Blackmagic Pocket
Cinema Camera 6K Pro. Reading every property and setting one (ISO) was proven
on the camera; the console and presets pages were first run with the camera
unplugged, and still have to be followed with it attached.

    fcpm camera                      the console, opened in this host's browser
    fcpm camera presets              the curated presets
    fcpm camera apply studio-tungsten  set one, then read every value back
    fcpm camera state                one reading, as JSON

The console is at `http://127.0.0.1:8790/` and the presets page at
`/presets`, on this host only.

## How it reaches the camera

Over USB, with nothing installed. The camera offers PTP, and Windows binds it
with its own MTP driver. Windows Portable Devices can send raw PTP operations
through that driver (the MTP extension commands), so `ptp.py` needs no driver
swap, no Blackmagic software and no administrator. It needs `comtypes`, which
`fcpm camera` brings through uv.

One thread owns the camera: it finds it, reads every property about once a
second, and runs one command at a time. A camera unplugged mid-read costs a
failed reading, the page says "Camera not connected", and it is picked up
again when it returns.

## What it answered

Blackmagic Pocket Cinema Camera 6K Pro, firmware 7.5.1, measured 2026-09-28.
Its PTP vendor extension is `blackmagicdesign.com: 1.0;`. Blackmagic added USB
PTP control in Camera 6.6 and has not published it; tal.org documents it for
the Pocket cameras.

| code | what it is | type | range | how we know |
|---|---|---|---|---|
| `5001` | battery | u8, read | 0–100 % | standard PTP |
| `5003` | resolution | string | 6144×3456 … 1920×1080, 10 choices | standard PTP |
| `5007` | iris, f-number ×100 | u16 | f/3.7 … f/19 with this lens | standard PTP |
| `5008` | focal length, mm ×100 | u32, read | 18–135 mm lens | standard PTP |
| `5009` | focus distance | u16 | 740–820, units unknown | standard PTP |
| `500F` | ISO | u16 | 100 … 16000 | standard PTP; set and read back |
| `D001` | shutter speed, 1/x | u16 | 24–5000 | range; 1/30 at 24 fps matched `D002` |
| `D002` | shutter angle ×100 | u16 | 173–36000 | range; 288° = 1/30 at 24 fps |
| `D003` | focus position | i32 | 0 near … 65536 infinity | tal.org |
| `D004` | white balance, K | u16 | 2500–10000, step 50 | the ATEM set it and it moved |
| `D005` | tint | i8 | −50 … 50 | the ATEM set it and it moved |
| `D006` | project frame rate ×100 | u32 | 23.98 … 59.94 | the choices |
| `D007` | not named | u32 | 5–60 | perhaps the off-speed frame rate |
| `D008` | not named | u8 | | |
| `D009` | not named | i32, read | 18, steady | |
| `D00A` | not named | u8, read | 0 | |
| `D00B` | ND filter, stops ×2048 | i16 | 0–15 stops | the ATEM set 2 stops and it read 4096 |
| `5011` | date and time | | | the camera says not supported |

Operations: GetDeviceInfo, sessions, GetStorageIDs, InitiateCapture,
Get/SetDevicePropValue, GetDevicePropDesc, InitiateOpenCapture and
TerminateOpenCapture (record start and stop). No file access and no events, so
the console polls.

The camera's enum lists carry a u32 count after the standard u16 count;
`ptp.py` skips it.

## Presets

`presets.yml` is the curation: one entry per button, in order, each a label, a
sentence, and the settings in the words a person uses (`wb: 3200`,
`shutter: 48`, `nd: 2`). Pressing one sets each value, reads them all back,
and says which took. The first four are drafts for Autumn to curate.

## Not yet

- **Followed with the camera attached**: the console's controls, a preset
  applied and checked, and record start and stop (which makes a real clip).
- **The other routes.** The ATEM can relay the same settings over HDMI (proven
  for white balance, tint, ND and ISO, with the ATEM session on station-node),
  and Bluetooth carries the full Blackmagic protocol. A later console could
  choose its route; this one is USB.
- **Whether the ATEM puts values back.** Blackmagic says a camera under ATEM
  control has settings changed on the camera reset by the switcher. The ATEM
  now holds white balance, tint, ND, ISO and shutter angle for Camera 4, sent
  during the 2026-09-28 tests, so a USB preset may be undone for those. Test it:
  apply a preset with the camera on the ATEM and read back a minute later.
- **Four properties still unnamed** (`D007`–`D00A`).
- **The camera's own device trove**, like `FC-Public-Media/atem-mini-pro`: its
  `instrument.yml` of measured facts.
