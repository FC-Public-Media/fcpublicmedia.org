# The pools trove

**A view into the studio's storage, and the recordings moving through it.**
Autumn, 2026-10-05: one dark page, squares for the audio files, colours and
borders saying what is happening to each, so anyone can sit here and watch it.

Status: first pass, on production (editing bay 1). `fcpm pools` opens it.

## What it shows

- **One section per pool, one strip per share or folder.** A recording is a
  square, left to right in time, grouped by day. A bigger square is a bigger file.
- **Colour is the step it is at.** The steps and their colours are the
  machine's own (`machines/<profile>/pools.yml`, `stages:`), not a list in
  code. An emulated pool's folder named after a step *is* that step; a depot
  share maps to one with `stage_by_share`.
- **The border is its state:**

  | border | means |
  |---|---|
  | white, pulsing | being written now: changed in the last 90 seconds |
  | bright | today |
  | faint | settled |
  | dashed | under 3 seconds: likely a cough, footsteps, a mic bump |

- **Free space trails off each strip**, hatched, so scrolling sideways gives a
  feel for used against available.
- **Click a square** and Explorer opens with that file selected. **Click a
  strip's name** and it opens that folder. That covers the step people do by
  hand today: open *To enhance*, select all, drag into Adobe Podcast. The page
  can open Explorer only inside a pool, and nothing else.
- When the recording was made comes from a timestamp in the file name, the way
  Audio Hijack names them. Without one, it's the file's last write minus its
  length. Length is read from a WAV's header.

## The timeline

`timeline`, at the top of the page, shows the same recordings on the clock:
one lane per night, from the day's seam to the next (`view: day_starts_at` in
the machine's `pools.yml`; 9 on production), so a session past midnight stays
whole and no debris sits at a lane's far end. The squares page splits days at
the same hour. Each
recording sits where it ran, as long as it ran: its last write, less its
length (AIFF and WAV lengths are read from their headers, once). What was
silent has no bytes and is left empty, so sessions, the breaks inside them,
and the nights with nothing show for what they are.

**Dragging along time sets a window**, the way text is selected: press, drag,
let go, carrying on into the next lane as a line of text does. The window is
that stretch at full width, docked below, snapped to the recordings it covers.
It is the zoom: drag inside it to look closer, drag either edge's handle (in
the window or on the nights) to adjust it, or turn the wheel over it to zoom
about the pointer. Backspace returns to the previous view, whatever changed
it; Esc closes. It is also a player, silent until `m` (or the button) turns sound on:
click to place the playhead, Space to play. It runs through the recordings in
order at real speed and skips the gaps, which have no bytes. Browsers cannot
play AIFF, so `/audio` hands the page each recording as WAV.

The window can be grouped under a show from its bar, one button per show FCPM
has a record of (`site/_shows/`), or under a provisional name for what nobody
has identified yet (`+ new group`: "unknown 1", editable). Provisional groups
are dashed and italic, and their names come back as buttons to reuse. Click a group's line to open its window,
to change it or ungroup it. Double-click a recording to open it in Explorer.

**Proofing.** The bar under the window has two settings, kept between visits:
**amplify** (on: ordinary talk fills the height and a peak over about -9 dBFS
crosses the strong-voice line; off: true scale), and **skip clips under
3/6/10 s** (on: playing and clicking pass over short clips, drawn faint).
Insisting overrides the skip for that spot: ctrl-click, right-click or a long
press puts the playhead exactly there and plays that clip, then skipping
resumes.
A recording on two pools (the same name and size) counts once; its tooltip
says where else it is.

Groups are kept on this computer (`%LOCALAPPDATA%\<profile>\pools\groups.json`)
until they are written to the show's own repository. `pools.py groups` lists
them.

It runs only while its window is open. `fcpm pools` starts a small server on
`127.0.0.1:8091`, opens Edge onto it, and stops when that window closes.
Running it a second time just opens another window onto the first.

## The pools

| kind | what | how it is reached |
|---|---|---|
| `smb` | the depot: the router's USB drive, over the Helm Wi-Fi | its shares, by the names kiosk keeps (`machines/kiosk-1/node.yml`, `depot:`), plus any the router offers beyond them. It needs the depot's password saved on this computer, once: `fcpm pools key` (Windows Credential Manager; nothing in any file) |
| `folder` | the **emulated pool**: `~/code/pools/emulated`, with a pretend capacity | a folder standing in for a Buffalo or Drobo pool until this computer is their iSCSI initiator. Same shape: folders per step, files, free space |

`fcpm pools sample` puts 40 small WAVs into the emulated pool, spread over the
last six days, so the page has something to show. `fcpm pools sample clear`
takes them out.

## Removing

A recording that was here and is not now stays on the timeline as a ghost (a
dashed outline) where it was: the page remembers every recording it has seen
(`seen.json`, beside the groups), and reads the drive's Recycle Bin, where
Windows keeps each deleted file's original path and times. A pool that cannot be
reached makes no ghosts.

Groups are how a stretch is removed. `mark for removal` in a window's list marks
the groups it covers (or makes one, "to remove"); they draw red. **Remove
marked** in the header moves every recording inside them into the pool's
`.removed/<date>/` folder, after asking. Nothing is deleted: moving a file back
undoes it.

## Not yet

- **Squares that are units, not files** (Autumn, 2026-10-07). On a pile of
  silence-split fragments, one square per file is a sliver per file, and the
  page runs to a width nobody can use. A square should be what gets enhanced
  as a unit: one long continuous stretch is one square, and a cluster of a lot
  of little activity close together is one square too. That clustering is our
  guess at what belonged together, so a square's time varies; its size stops
  meaning duration and the page shows structure instead. The squares page
  becomes that; the timeline keeps real time.

- **Real mass storage.** The Buffalo and the Drobo, as iSCSI targets with this
  computer as the initiator. Each becomes a pool beside the depot, which stays
  a small pickup station that kiosk hands things out of. A file in this
  repository could then say which machine holds each pool, so it's
  recorded in one place.
- **Super-rows for people.** Who was booked and who was hosting, from the
  bookings and check-in records, so a day's recordings group under a show, a
  host, or *unhosted time*.
- **Show configurations.** A member show's repository, submoduled here, says
  which steps its recordings take: enhancement, silence trimming,
  transcription. A step asked for late runs late, like a CI job, and its
  output lands in the same place.
- **Promotion to a final timeline.** Every file means something was heard.
  Not every file deserves the timeline. Declining is the *Not promoted* step.
- **Audition as gear.** Adobe Audition, scripted, as deployable as OBS with a
  config: an enhancement step that runs here, beside the Adobe Podcast drag.
