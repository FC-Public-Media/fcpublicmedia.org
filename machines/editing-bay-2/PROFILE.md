# editing bay 2

FCPMEDIT2: a Windows bay, the twin of editing bay 1 ([production](../production/PROFILE.md)), and
new to us on 2026-11-09. Its user is `fcpme`. Git is `Git.Git` from winget, machine-wide, as on bay
1; the repository's start line (README.md, Setting up a machine), ending in `editing-bay-2`, installs
Git and the rest of [`gear.yml`](gear.yml) and puts the profile on. It carries `fcpm` and what it
takes from its twin below; its hardware is unread, and nothing else is claimed. Machines and
profiles: [docs/station.md](../../docs/station.md).

## From its twin, a verb at a time

Bay 2 becomes bay 1 progressively: a verb comes over when it is wanted, never the whole list.

| verb | how |
|---|---|
| `fcpm model` | [`model.ps1`](model.ps1) runs bay 1's, with bay 1's `model.yml`, spread (`models/`) and shapes, so a model picked here is one bay 1 knows. This bay's own: its state, `%LOCALAPPDATA%\editing-bay-2\model`, and its contexts' addresses, `editing-bay-2/<name>`. `install` verifies llama.cpp's build attestation, so `gh` signed in first; `on` needs an address in `10.209.1.0/24`; `grant` is an administrator's |
| `fcpm helm`, `fcpm crew` | [`services`](services) orders one line, `helm`, from bay 1's menu ([`../production.yml`](../production.yml)): the door's intake and pages on 8080, applying `wizard:model+up` by this bay's `model.ps1` for a reply naming `job: editing-bay-2` ([`../helms.yml`](../helms.yml)). [`helm.ps1`](helm.ps1) is bay 1's. Its crew's state is `%LOCALAPPDATA%\editing-bay-2\crew`. `fcpm crew install` and `fcpm helm grant` are an administrator's; until this bay has an address on the switched network, `helms.yml` gives it none and replies for it wait |

An earlier note here described a macOS bay that schedules FCPM's Cablecast material. Which machine
that is, if it is not this one, is not established.

The bays share a network drive of about 32 GB in some eight partitions of a little under 4 GB, one
per box. Where it mounts here, and which partition is this bay's, is not established.
