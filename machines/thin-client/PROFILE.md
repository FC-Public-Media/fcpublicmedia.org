# thin-client

**Status: drafted 2026-10-09 from photos, not yet reformatted.** A donated HP
thin client in the control rack, under the headphone amp and above the switcher.
It boots HP ThinPro (Linux underneath) straight into one remote desktop
connection its last owner left, and does nothing else. It is to be wiped and
given a job here.

The folder name is a placeholder until Autumn names it (`names`).

| | |
|---|---|
| model | most likely an **HP gt7725**, the ThinPro twin of the Windows gt7720. Confirm from ThinPro's System Information or the underside label |
| CPU | AMD Turion X2 Ultra ZM-84, two 64-bit cores at 2.3 GHz. Family 11h: SSE3 and SSE4a, no SSSE3 or SSE4.1 |
| graphics | AMD RS780G (Radeon HD 3200): DVI-I and DVI-D, two independent screens, up to 2560×1600 |
| memory | two DDR2 SO-DIMM sockets (PC2-6400S), 2 GB as these shipped |
| storage | a 1 GB flash module on the 44-pin IDE header, replaceable |
| network | gigabit Ethernet (Broadcom BCM5787M). Not on the studio LAN on 2026-10-09: no HP hardware address answered on 10.209.1.0/24 |
| other ports | serial, parallel, two PS/2, USB 2.0 front and back, mic and headphone |
| power | 19 V on a 7.4 mm barrel. About 20 W idle, 40 W busy |

The specs are the family's, from [parkytowers' gt7725 page](https://parkytowers.me.uk/thin/hp/gt7725),
until this unit's own System Information confirms them. The ports are from the
photos.

## Two screens

The hardware drives both DVI ports at once. Showing only one screen is how
ThinPro is set up, not a limit of the box.

## What it could be

**Proposed: a screens box.** Debian 13, as on `../digitization`, with a
browser in kiosk mode on each monitor showing studio pages, the way
`../../troves/kiosk-screen` keeps the rolling TV from bay 1. It is already in
the rack with two monitors on it, and it draws about 20 W. The CPU is fine for
showing pages, and too slow for encoding or enhance work.

- **Browser:** Firefox ESR has `--kiosk` and only needs SSE2. Whether current
  Chromium still runs on a CPU without SSSE3 is to be tested, not assumed.
- **Graphics:** the Radeon needs `firmware-amd-graphics` (non-free firmware,
  which the Debian 13 installer offers).

## Reformatting

1. **Read it first.** Photograph System Information (model, serial, BIOS,
   memory, flash size) and the label underneath, and fill in the table.
2. **Storage.** 1 GB won't hold Debian with a browser. One of these:
   - run live from a USB stick, as `../digitization` does, with nothing to buy;
   - install to a USB stick or SSD that stays plugged in;
   - swap the IDE flash module for a bigger one (8–32 GB).
3. **Make the stick on the iMac.** Kiosk-1 and the bays can't write a raw
   disk without an administrator.
4. **Boot it.** HP's setup key is usually F10. A thin client from an
   enterprise may have a BIOS password or USB boot turned off, and that would
   be the first thing to stop us.

## Not known yet

- The exact model, serial, memory and flash size.
- Where its network cable goes, since it isn't the studio LAN.
- Whether the BIOS is locked.
- What it is called (`names`).
