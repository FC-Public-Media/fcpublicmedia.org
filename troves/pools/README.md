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

## Not yet

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
