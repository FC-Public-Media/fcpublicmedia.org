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

**Compressed time.** With **compress gaps** on (the default), a gap that is long
for the zoom (at least 20 s, and 1/120 of the window) shrinks to a narrow cut
labelled with how long it was (`+22:17`), and short clips the skip passes over
inside it show as dots (`â¢Ã8`). Recordings share the width. The waveform is a
smoothed contour (binned every 3 px, eased 1-2-1), drawn in decibels when
**amplify** is on. Off, the window is plain time with its grid.

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
`fcpm pools timeline` is the same, opened at the nights' timeline; the desktop's
*Pools timeline* shortcut runs it.

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

## Transcription (experimental)

Transcription is a phase you choose, not a button anywhere: `mark for transcription`
in a window's list marks the groups it covers (or makes a bare mark, "to
transcribe"), and only what is marked goes. Beside a marked group's name, its
state: ○ marked, ◐ being heard, ● heard (●! if some recordings could not be). Sending is
an event, kept on each group it was sent for (job, engine, when, how much).
Transcripts are private: they stay on this computer, never in a public repository.

The speech-bubble button in the window's strip sends what is marked out as a job:
its edit list, the recordings that play after the skips, silences and cuts,
with the settings that made it (`jobs/<id>.json`, beside the groups). The
machine's engine (`transcribe: engine:` in its `pools.yml`; `engines/`) hears
each recording, and what it heard comes back onto the window as a line of text
where it was said (`jobs/<id>.result.json`, filling in as it goes); a badge
counts it. The only engine so far is `windows-speech`: Windows' own dictation
recognizer, nothing installed, and rough on a room of people. It proves the
leg; a real engine (Whisper on the bay's RTX 4080, Audition's own, or Audio
Hijack's Transcribe on station-node) arrives the bay's way before it is named.

## Transcript time and the episode (Autumn, 2026-10-07)

The window is the show block. Its transcription regions, and its episode, are
looked at in **transcript time**: the nights give way to one panel each, side
by side, for what the window shows and nothing else. A new window brings its
own; nothing from another is left up. Put away (the header's arrow, `t`, or
Esc) they all go at once, to marks in the header that bring them all back.
One or the other, never both.

- **A region's panel:** its control (what you know is said in it, typed as you
  like, kept as you type) and what each engine heard there, scored against it.
- **The episode's panel**, first, once the window is in a show's group (or
  `episode…` in the list): its own details (title, season, episode, who is in
  it, what it is about), kept on the group on this computer; what its outputs
  are called (`<show>-s0e3`, or the night recorded); and the show's pipeline.

**A show's pipeline is the show's, not the episode's.** Every episode goes
through the same steps; only what goes in and comes out differs. It lives in
the show's record (`site/_shows/<slug>.md` `pipeline:`), managed by the site;
a show without one gets the machine's barest default (`pools.yml`
`pipeline:`). `eject: false` (the default) writes nothing: every run reads
the managed pipeline fresh, and render only shows what it would make.
`eject: true` renders the pipeline with an episode's details and edit list
into a config of its own (`ejected\<show>\<out>.yml` beside the groups, or
`pipeline: eject_to:`), the copy automation can run from as it stands.
Audition's steps are named, not run, until its panel proves out.

## The manifest

The manifest button in the window's strip writes down what the window did, so
it can be proved later: every recording in the window by SHA-256, with its part
in the edit (played; short, skipped; silenced, marked for removal; removed,
hashed where it still exists in the Recycle Bin or `.removed`), the cuts and
their lengths, the settings that made the edit, the groups the window touches,
and the transcription results there, each by hash. Then the manifest's own
SHA-256, over its canonical form (keys sorted, no spaces, without that line):
the one value to timestamp or seal. Revealing any one recording later can be
checked against it without revealing the others; what was left out is listed
as surely as what was kept. Kept in `manifests/` beside the jobs, on this
computer only, and downloaded exactly as written.

## Next: the window as a dispatch hub (Autumn, 2026-10-07)

The window is where calls to Audition are made, or at least where what is
sent is decided. Its settings are not only ways of looking: skipping, cutting
gaps and silencing are a manual pre-processing step, and they are what gets
rasterized into the job (an edit list: what plays, what is cut, what is
silenced). A show's profile can add steps per group (transcription, say).
Think like production engineers: a map, not a form.

1. **Silence what is marked for removal.** Marked stretches pass silently,
   like skipped clips, and count as cut. A toggle beside the others.
2. **An icon strip, not words.** Checkbox-driven toggles drawn as glyphs,
   words only in tooltips:
   - amplify: a small waveform, pressed in when on;
   - compress gaps: drawn the way cuts are drawn, an ellipsis pinched in;
   - skip short clips: a short, tightly ticked slider whose stops (3, 6, 10 s,
     and off) are what matter and are clickable; the space between stops shows
     only their relative size, not to scale;
   - silence marked: the removal mark's own glyph.
3. **The waveform as a path.** Trace the peaks as one line in the group's
   (show's) colour; the area under it is the same colour, much dimmer, falling
   toward the background (a mask, not a solid fill), so focus goes where it is
   due. A run of touching clips is one path, not a shape per clip, so it is no
   longer crooked at gaps that nothing skips. The alternating tones go.
4. **The selection range is the readout.** The clock and range are coded in
   the selection's own look, not washed-out text. Counts (shown, cuts, skipped,
   silenced) become a cluster of small badges with glyphs; the words go into
   tooltips. Nothing ends in an ellipsis.
5. **A night's label selects the night.** Clicking the date at a lane's left
   opens the whole night as the window. The wheel then zooms in and out of it;
   zooming out stops at what there is, not three days into nowhere.
6. **Everything can be one window.** Selecting all the nights at once is
   allowed: compressed, it reads as a timeline to shuttle to Audition, and well
   marked, whole swaths drop out.
7. **Missing nights are dividers.** Not "1 night, nothing": one hard divider
   per missing night, drawn like the zone underlines.
8. **Send the selection to transcription, and see it come back here.** An
   experiment to prove the transcription leg: the window's range (with its
   cuts, skips and silences applied) goes out as a job, and the transcript
   returns onto this timeline, text aligned under the waveform to when it was
   said. The first engine to try is whichever proves out on this bay:
   Audition's own speech-to-text (it ships Whisper's tokenizer and speech
   models), Whisper run locally on the RTX 4080, or Audio Hijack's Transcribe on
   station-node (the reel's route, `enhance/docs/REEL.md`). The job and its
   result belong to the group, so a show's profile can later ask for it.

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
