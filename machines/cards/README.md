# Cards

A card boots known-good FCPM code on any machine. It is not a job: its type says what it carries,
and the checkout on it holds every job's profile. Every card boots through Ventoy, whose key is
enrolled where Secure Boot is on.

    machines/cards/build TYPE /dev/sdX sdX       erases the card; a window on this screen asks first

| type | boots | carries | |
|---|---|---|---|
| [`steward`](steward/card) | Debian XFCE live, 16G persistence; SystemRescue; Alpine | home, origin, toolbox | brings FCPM back with nothing else around |
| [`lan`](lan/card) | Alpine, diskless | kit, code, home | leans on the LAN: code from digitization, packages from the internet |

A type is a folder: `card` (its partitions, `name:fs:size`), and `fill`, which `build` runs on each
one. The home is encrypted under its holder's passphrase, asked in a window, and belongs to account
`user` on every type, so a home moves between cards unchanged.

## lan

- **kit** (FAT, readable anywhere) at `/media/lan-kit`: Alpine's package cache (`cache/`, signed by
  Alpine), the saved settings (`card.apkovl.tar.gz`, written by `lbu commit`), `bin/claude`.
  [`lan/kit DIR`](lan/kit) makes or refreshes one on any Linux; saved settings already there are kept.
- **code** (ext4) at `/srv/code`: the checkout that built the card, outside the home so a job can
  start before anyone unlocks it.
- **home** (LUKS) at `/home/user`: tty1 ([`lan/seat`](lan/seat)) asks its passphrase, then logs in;
  logging out locks it.
