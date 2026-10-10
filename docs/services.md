# Services

Services FCPM means to offer, designed far enough to resume. Each section says what is built. Open
questions are in [`OPEN.md`](OPEN.md).

## Member scheduling

A member picks a slot for their program and staff approve it, instead of staff placing every file. Not built.

What Cablecast allows (checked against its live API):

- Shows and schedule items are separate resources. A show can exist unscheduled and airs nowhere; the vendor's `new-show.mjs` example (`github.com/trms`) creates the show, then schedules it.
- Free time in a week is computable from public data: schedule items' `runDateTime` plus shows' `totalRunTime` (seconds).
- A show's `runCount` counts all-time runs; `site/_data/airings.json` covers 365 days and carries last aired. Each answers what the other cannot.
- No draft state is observable: a sampled week's 455 items all had `runStatus: 1`, `runType: null`, `runLock: false`. Creating a schedule item may write the live schedule.

Decisions:

- First version: members create the show, not the schedule item; staff schedule it.
- If Cablecast has a draft `runStatus`, use it and keep Cablecast the source of truth. Holding requests outside Cablecast is the last resort: two systems would disagree about one week.
- No locking. Staff approval settles two members picking the same gap.
- The member proves who they are with the member-site passkey (`/authorize/`, the broker in `worker/`).
- Dropbox stays as the fallback intake. A direct upload arrives as a record with its own metadata.

## Publishing without staff

Approval moves from once per submission to once per device: an approved device publishes to its site every week with nobody in the middle. Built in the broker (`worker/src/enroll.js`, `/bind`, `/device`; [`worker/README.md`](../worker/README.md)) and its pages (`/authorize/`, `/devices/`, `/upload/`); the broker is not deployed (`url` is empty in `site/_data/authorize.yml`).

- **Enrollment** (a claim link binds a device to a site) is separate from **authority** (`may_publish` on the device record in `.auth/devices.json`). A forwarded claim can only get a device listed.
- The first device to bind is trusted. Every later device arrives listed and not allowed, and an existing publisher approves it. If no active device may publish, the next to bind counts as first.
- The residual risk is the very first link intercepted before the owner opens it; a short expiry covers most of it.
- `/upload/` takes a title, a summary and a date. Preparing show notes is a separate act.

## Digitization

FCPM digitizes people's media and hands back more than a file on a thumb drive: a private view of the results, delivered to them, with large files collected at the studio. Not built as a service; the tooling exists.

- **Contact sheets** come first, with no human in the loop: a Drive link in, thumbnails written back. A sheet is derived; a wrong one is deleted and regenerates.
- **`.contact-sheets-engine`** (`FC-Public-Media/contact-sheets`, private) does most of it: `process-all.sh` → `process-clip.sh` → `assemble.sh` (folder, clip, sheet; a clip's `.done` marker means it is never re-read), `proof.sh` with `proof-rates.conf` (frame rates), `ranges.py` (a ranges document, CSV and JSON, clip-relative and wall-clock), `segment.py` (camera settled or in transit), `make-sheet-html.py` and `build-site.py` (a static site from the cache), `reconcile.py` (on the phone, not on Drive). It reads Google Drive through the local CloudStorage mount, which pulls byte ranges as it streams. Its `residency.yml` declares five storage labels instead of carrying files.
- **Its rules:** the sheet is how a person finds a moment and the ranges document how a tool does; cutting writes new files to a new folder and takes the ranges document as input.
- **Access by construction:** the customer puts a Drive shortcut to their footage inside a folder shared with FCPM. A shortcut keeps the target's permissions, so FCPM can read and cannot edit.
- **Two intakes, one pipe:** a customer's Drive link and a tape captured in the studio differ only in where the file starts. Tape captures in real time: an hour of tape costs an hour of a machine.
- **Storage:** results live in the workstation libraries without being committed, and can be written back to the customer's own Drive folder. Working files are scratch.
- **Scope:** a script first; an AI worker is a later shape of the same pipe. GPU rendering is not required. Interactive frame intervals (point at part of a timeline for denser frames) belong in `.proofing-engine`, not in a fork here, and proofing is not in scope yet.

## Depot index

What is on the studio drive is shown by walking its shares and publishing an index that a page renders: a browser cannot speak SMB. Built in `machines/kiosk-1/door.py` ("the depot", shown at `/depot/`); see [`kiosk.md`](kiosk.md).

The drive's limits are declared, not sniffed: Samba reports every partition as NTFS whatever it is, and the router mounts only FAT.

- No file over 4 GiB (2 GiB on FAT16), so masters do not fit; say so at submit time.
- Nothing in a partition's root: a FAT16 root holds about 512 entries, a long name takes several, and a full root reads as a full disk.
- No permissions or ownership: inbox and outbox are a directory convention.
- `mtime` is local time at two-second resolution with no zone: never order a queue by it.
- `: * ? " < > |`, trailing dots and trailing spaces are illegal: sanitize on write, keep the original title in the index.

Completeness comes from the writer, never from inspection:

| state | means |
|---|---|
| `declared` | the writer left `<name>.sha256` beside it |
| `arriving` | it grew between two scans |
| `unwitnessed` | present, not growing, undeclared: a guess, and named as one |

- A state is a name with its evidence, never an ordinal: `arriving` → `unwitnessed` is a lost signal, not progress, and a file finished between scans never passes through `arriving`.
- `growth_last_observed` is an instant written once when growth stops; absent means never seen growing.
- The index is never written to disk or committed: it names people's files. Each observation carries its own instant, so a screen can say when it last heard anything. A page can show only what the index names.
- Volume identity (not built): a marker file at a known subpath holds an id written once. A missing marker reads `unidentified`; a duplicate id means a copy was made. The label is a display name allowed to collide; the heading is what the partition `holds:` (`wants:` in a residency).

## Workstation sign-in

A phone signs a person in to a shared workstation by a QR code on its screen, so the studio knows who is there without accounts on the device. Today a bay has one shared Windows account, and identity is whichever browser profile was clicked. Not built.

- It is a new consumer of the broker, check-in with a different consequence: passkeys (`worker/`: `/bind`, `/device`), signed claims (`site/bin/mint-claim.py`, `site/_data/identity.yml`, `site/assets/js/claims.js`), a QR code standing in for a session (`/check-in/`, `site/bin/make-qr.py`, `site/_data/checkin.yml`), and policy (`site/_data/authorize.yml`).
- The phone is one way in, never the only one: nobody is kept from working for want of a smartphone.
- A link that opens a workstation needs one-to-one claims, against the forwarding `site/_data/authorize.yml` allows.
- Production's service starts with the computer, before anyone signs in, which makes room for a welcome: a check-in code (on the lock screen, through a welcome account, or on the rolling TV), identifying yourself as the grant for one sitting, and a space of your own (your page, your browser profile) put away when it ends. No program draws on the lock screen, the machine-wide lock-screen picture setting is for business editions (the bay runs Home), and the guest Wi-Fi cannot reach the LAN.

## Production's door

A page for members at editing bay 1, served on the studio LAN only, on port 8080, from the local disk: never public and never through Cloudflare. Not built.

- It starts from the person ("I recorded tonight", "I want my recordings", "I am here for a show"), with short paths through the pools, transcription, the show's pipeline and release: glyphs, colour and state, words in tooltips.
- It is always up and says something true, asked live each time: a show's nights and episodes, held and released, or plainly that nothing is running and what would bring it back.
- The machinery (lines, logs, menus) is one level down, for whoever tends it.
- It works the same on the rolling TV, a phone or laptop on the LAN, and the desk.
- The bay's network category is Public, so the LAN needs one inbound firewall rule for this port, scoped to the local subnet, in the elevated install.
