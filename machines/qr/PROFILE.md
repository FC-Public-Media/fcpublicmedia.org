# qr

Kiosk's pickup point and the studio's intake by camera, carrying the [`scanner`](../../troves/scanner/README.md)
trove. Worn by the [`bounce`](../bounce/PROFILE.md) Pi, **joined**: its eyes, its page and its intake all run on
the box, so it stands on its own and answers at `qr.local`. It is not a helm: it holds no wizard and applies no
reply. What it catches it keeps first, then hands to Helm ([`helms.yml`](../helms.yml) `intakes:`): a reply some
helm holds to that helm, any other to digitization's. While Helm is out of reach the replies wait in its inbox,
and go on a later pass. Machines: [docs/station.md](../../docs/station.md).

| | |
|---|---|
| `names` | `linux Hostname bounce` |
| eyes + page | [`eyes.service`](eyes.service) on tty1: `troves/scanner/eyes.py` with `page.py` as its page, both from this box's checkout, no ssh between them. The page reads the loop and the inbox from the helm it hands to (`/asks/bottles/`, `/inbox/now`), and its title bar from main Helm's helm console |
| intake | crew line `intake`: `door.py serve` with only `replies` watched, on port 80 (`net.ipv4.ip_unprivileged_port_start=80`). The camera's catches and `POST /drop` are kept in `~/.local/state/media-node/replies/inbox`, then handed on (`replies.py status` says where each went) |
| joined | Helm's helm console lists it after the helms: `Q qr answering joined` while its door answers and it hands to that helm; the board's `qr` row says the same |
| names | crew line `names`: `qr.local` ([`lan.yml`](lan.yml)), the bays' join point (`http://qr.local/drop`) |
| follow | crew line `follow`: the checkout keeps to origin.local's main, the scanner at its pin, by the box's own key (`~/.ssh/origin`, a [`KEYHOLDERS`](../origin/KEYHOLDERS) line) |
| a helm later | when a job this box wears is a helm in `helms.yml`, its wizards are applied here and only the rest handed on; nothing else changes |

## Wear it

From digitization's checkout, with the box up: `machines/qr/install fcpm@bounce.local`. It carries a shallow
checkout over once, gives the box its own key to the origin (printed: it needs its `KEYHOLDERS` line), asks for
the box's password in a window on digitization's screen, and runs `install root` there: python3-yaml and
avahi-utils if missing, port 80 for fcpm, `eyes.service` (the leashed one kept as `eyes.service.before-qr-joined`),
and the crew (`crew.sh install qr`). The bounce island also wants port 80: the two are not worn at once.
