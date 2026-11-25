# dj

DJ: the Dell Precision 5820 that was Editing Bay 3 (service tag 5YQX4Z2). "The old boy, but he's going to dribble a whole
lot." Named and given his jobs 2026-11-20: the test server and static CI, and the DJ role, the streaming. Headless
Debian 13: NVIDIA's driver, which the P4000's encoder needs, is built for glibc, so not Alpine. His drives were mirrored
to the Buffalo first (`../digitization/PROFILE.md`, Mirrors). Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| hardware | Core i9-9940X (14 cores, 28 threads), 32 GB DDR4-2666 (4 of 8 slots), NVIDIA Quadro P4000 8 GB (NVENC: no cap on encode sessions), Intel I219-LM gigabit, SK hynix PC601 512 GB NVMe (the system), Micron 1300 1 TB SATA (data), DVD, USB 3, PS/2, serial. UEFI, Secure Boot on. BIOS 2.2.0 |
| `names` | `linux Hostname dj`: `dj.local` |
| [`install`](install) | from a workstation: `root@steward.local DISK SERIAL` puts Debian on DISK from the president card's Alpine (`disk`); `fcpm@dj.local` outfits him as he runs (`outfit`) |
| [`disk`](disk) | GPT (EFI 512M, root ext4), `debootstrap` trixie with Debian's own keyring, then Debian's signed shim and grub, so Secure Boot stays on. sshd by key only (`fcpm`, sudo), avahi, systemd-networkd by DHCP, zram, Fort Collins time |
| [`outfit`](outfit) | NVIDIA's driver (DKMS, signed), `nvidia-smi`, ffmpeg. The first run asks the firmware to trust the module's signing key: at the next boot, at DJ's screen, MokManager asks once for the password it prints |
| jobs | the stream ([`services`](services)): `ingest`, `fetch` and `youtube`, the broadcast job's lines ([`../broadcast`](../broadcast/PROFILE.md), To YouTube), and `follow`. `proofs` ([`proves`](proves), [`gear`](gear)): each tree waiting to land and main, tested by its own `.checks` as the user `proof`, signed by DJ ([../../docs/proofs.md](../../docs/proofs.md)). Nothing a member project pushes runs here by itself |
| keys | DJ is a holder of the keychain and the origin (`machine dj` in [`../keychain/HOLDERS`](../keychain/HOLDERS) and [`../origin/KEYHOLDERS`](../origin/KEYHOLDERS)), by `identity-dj`, minted on the keychain. [`keys.yml`](keys.yml) is its grant: a group named there is handed to DJ, and to no machine whose own `keys.yml` does not name it. `youtube` is never kept on DJ's disk. The Secure Boot signing key is `dj-secureboot` on the keychain |

## Installing

From the president card, at DJ, with nobody else driving:

1. Boot DJ from the card: Ventoy's menu, Alpine (grub2 mode by itself). Unlock the card's home at the console.
2. `fcpm provision dj`. It lists DJ's disks with their serials and asks which; pick the NVMe (`nvme0n1`), type its serial
   back, and it installs Debian there from what the card carries. Then `shutdown`, take the card out, power on:
   `dj.local`.
3. From a keeper's workstation (digitization), `machines/dj/install fcpm@dj.local`: DJ's identity and signing key
   from the keychain, NVIDIA's driver, the LAN's names, the checkout from origin.local, and the crew. Reboot. Only
   when the firmware has not enrolled the signing key yet (the first time, or a new board), answer the blue
   MokManager screen once at DJ (Enroll MOK, Continue, Yes, the password it printed, Reboot). `nvidia-smi -L`
   names the P4000.

A workstation can also do step 2 over SSH: `machines/dj/install root@steward.local /dev/nvme0n1 SERIAL`.
