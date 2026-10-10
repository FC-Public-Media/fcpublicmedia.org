# `troves/pools/pools.py`

Moved out of the file. Unreviewed.

## 1

Above `import functools, json, os, re, shutil, struct, subprocess, sys, threading, time, urllib.parse`

pools.py — scan this machine's storage pools and show them as a page on
127.0.0.1, for as long as the window that ran it stays open: squares at /,
the timeline at /timeline, where stretches of it are grouped into shows.
  pools.py [view|scan|key|sample|sample clear|groups]
Doc: docs/troves/pools/README.md. Config: machines/<profile>/pools.yml.

## 2

Above `end = st.st_mtime`

One recording: when it ran, how long, and what state it is in.

It ran until its last write, for as long as it is: Audio Hijack names a
file for the minute it was armed, which can be long before its first byte
(enhance/docs/CAPTURE.md). The name's stamp is only for a file whose
length cannot be read.

## 3

Above `_levels = {}   # level_key -> dBFS`

--- loudness: one number per recording, its average level (RMS, dBFS) ------
Enough to tell a room's background from people talking. Worked out once per
file by a background pass and kept on disk beside the groups, so a restart
does not read the pile again. A settled file only: one still being written
is measured once it settles.

## 4

Above `f = levels_file()`

Measure every settled recording on a folder pool that has no level yet.
Depot copies are skipped: the page counts a copy once, by name and size.

## 5

Above `_seen = None`

--- what was here and is not now --------------------------------------------
Every recording a folder pool has shown is remembered (seen.json, beside the
groups). One that has gone from a folder that is still there is a ghost:
moved aside into .removed (by this page or by hand), or gone. A pool that is
not reachable makes no ghosts: its recordings are not gone, only out of sight.

## 6

Above `out, root = [], Path(Path(base).anchor) / "$RECYCLE.BIN"`

Recordings from under base that sit in its drive's Recycle Bin. Windows
keeps, per deleted file, an $I record (original path, size, when) beside
the file itself ($R, with its original times), so the ghost goes exactly
where the recording was.

## 7

Above `PIECE = 20 * 60   # seconds of joined recordings Whisper hears at a time`

--- transcription: a selection out, a transcript back ------------------------
A job is the window's edit list: the recordings that play, in order, after
the page's skips, silences and cuts. It is kept (jobs/<id>.json, beside the
groups) with its settings, so what was sent can be read back, and its result
(jobs/<id>.result.json) fills in as each recording is heard. The engine is
the machine's choice (pools.yml `transcribe: engine:`); engines/ holds them.

## 8

Above `work = jobs_dir() / jid`

The whole job in one run of the engine: the model loads once. A line comes back
per WAV (a piece of joined recordings) as it is heard; the result fills in as they do.

## 9

Above `pieces, pcm, at = [], bytearray(), []`

The recordings joined end to end, with no gaps, as the window plays them:
Whisper hears one continuous take, and a word cut in two by a recording's
end is heard whole. Joined in pieces of up to PIECE seconds (a line comes
back per piece); each piece keeps where in it each recording begins.

## 10

Above `_hashes = {}   # "path|size|mtime" -> sha256, read once`

--- the manifest: what the window did, provably ------------------------------
Every recording in the window by SHA-256, with its part in the edit (played,
skipped as short, silenced as marked, removed), the cuts, the settings, the
groups and the transcription events; then the manifest's own SHA-256, the one
value to timestamp or seal. A recording revealed later can be checked against
it without revealing any other. Kept beside the jobs (manifests/), on this
computer only: like the transcripts, it is private.

## 11

Above `data = scan(cfg)`

Move every recording inside a group marked for removal into its pool's
.removed/<date>/ folder, keeping its place below the pool. Nothing is
deleted: moving it back undoes it. Returns what moved.

## 12

Above `out = []`

The shows FCPM keeps a record of (site/_shows/*.md): slug and title, and
with the machine's config, each show's pipeline (see pipeline()).

## 13

Above `def pipeline(cfg, mine=None):`

--- a show's pipeline: one for every episode, managed or ejected --------------
What is done to a show's recordings (enhance, loudness, transcribe, ...) is
the show's, not the episode's: every episode goes through the same steps, and
only what goes in and comes out differs (its recordings, its metadata). The
show's record in the site (site/_shows/<slug>.md `pipeline:`) is managed: the
site's factory owns it and can change it under us, so by default nothing is
written from it (eject: false) and every run reads it fresh. A show without
one gets this machine's barest default (pools.yml `pipeline:`). eject: true
renders the show's pipeline with an episode's metadata and edit list into one
config of its own, the ejected copy automation can run from as it stands.

## 14

Above `gs = groups()`

An episode's own details, kept on its show's group (on this computer:
who was in it is nobody else's business until it is published).

## 15

Above `gs = groups()`

An episode is held until it is released: the supervisor (whatever runs
the show's pipeline) leaves a held episode alone, and gets to a released one
in its own time. Releasing an ejected show's episode renders its config then,
so what runs is what was released. Held back again, it is left alone again.

## 16

Above `gs = groups()`

What the episode supervisor (episodes.py) did with a released episode's
step: kept as an event on the episode, the way a person's acts are. It
writes nothing else; this server stays the one writer of the groups.

## 17

Above `ep = g.get("episode") or {}`

What an episode's outputs are called: the show, then season and number
when it has them, else the night it was recorded.

## 18

Above `g = show_group(groups(), float(body["start"]), float(body["end"]))`

The show's pipeline with one episode's metadata and edit list: what
automation would run. Written out only on release (write), and only when
the pipeline is ejected; otherwise shown, not kept.

## 19

Above `repo = (show.get("repository") or "").split("/")[-1]`

Ejected, it goes to the show's own repository (private: an episode names
people), into the checkout kept for it beside the others: work/<repo>@ejected,
made with `bin/refs work <repo> ejected`. Committed there; pushed by a person.

## 20

Above `def groups_file():`

A group is a stretch of the timeline someone has said belongs to one show.
Kept on this machine until it is written to the show's own repository.

## 21

Above `start, end = float(body["start"]), float(body["end"])`

Assign [start, end] to a show, or to a provisional name for what nobody
has identified yet ("unknown 1"), replacing any group it overlaps; or
ungroup it, when neither is given.

## 22

Above `on, gs, keep = bool(body[flag]), groups(), []`

A mark is its own range, exactly the stretch given: never a flag set on
the group around it (that once marked a whole show for removal when a
piece of it was meant). Unmarking takes away the marks of that kind the
stretch touches (a mark with a history only loses the flag), and clears
the flag from any named group that carried it the old way.

## 23

Above `raw = Path(path).read_bytes()`

A recording as WAV bytes, for the page's player: browsers cannot play
AIFF, which is big-endian PCM, so its samples are swapped into a WAV.

## 24

Above `st = os.stat(path)`

A recording's envelope: the loudest sample in each of n slices, per
channel, 0..1: {"ch": [[...], [...]]}. 16-bit PCM only; else flat.

## 25

Above `start, end, text = float(body["start"]), float(body["end"]), str(body.get("text") or "")`

A transcription region's control: what its marker knows is said in it,
kept on that region alone, never merged with another's.

## 26

Above `import ctypes`

Explorer at each folder, with the given files selected (all of them, not
just one: SHOpenFolderAndSelectItems, which /select cannot do).

## 27

Above `roots = [os.path.normcase(r["path"]).rstrip("\\/") for p in data["pools"] for r in p["rows"]]`

A share's root comes with a trailing separator (\\server\share\); trim it,
or nothing on a depot share is ever inside it.

## 28

Above `if not path or not os.path.isfile(path) or not known_path(current(cfg), path):`

One recording, as WAV, with byte ranges so the player can seek.
Only a file inside a pool, as with /open.
