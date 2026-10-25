# jukebox

The house's music: whatever cleared music a machine can reach, played as one endless stream. It is a
role, not a box. Any job takes it with one line in its `services` (`jukebox keep machines/jukebox`),
and the machine wearing it plays its own storage, so no disk is anybody's in particular. Editing bay 1
wears it first (`production/services`); when the bay is off, there is no jukebox, and the standby page
carries on without music.

## The library

A folder named `jukebox` at the top of any disk the machine has (every drive letter on Windows, every
real mount on Linux, `/Volumes` on a Mac), and `~/Music/jukebox`. `FCPM_JUKEBOX` names folders
instead. It is looked at again every minute: a folder dropped in plays from the next turn.

Inside, one folder per artist. A folder plays only when it says who it is and that it may air:

```yaml
# jukebox/Jane Doe/artist.yml
name: Jane Doe                       # as said on the air
cleared: 2026-10-24, Autumn          # who cleared it for the air, and when
link: janedoe.bandcamp.com           # optional: where to find more
```

What it plays goes out on YouTube and, one day, channel 97. One track without the rights can get the
whole stream flagged. So `cleared:` is a person's word, and a folder without it is held, with the
reason, in `/now.json`. Tracks are any audio ffmpeg reads; the title is the file's own tag, else its
name.

## The stream

Shuffled, every track once before any again, no artist twice running where it can be helped, every
track to one loudness, gapless. On port 8093 (`FCPM_JUKEBOX_PORT`), open to the LAN:

| | |
|---|---|
| `GET /stream.mp3` | the music, 128 kbit/s MP3, endless; OBS takes it as a media source, a page as `<audio>` |
| `GET /now.json` | the track playing (artist, title, position, length), the next five, the libraries, what is held |
| `GET /tracks.json` | every track that may play |
| `POST /skip` | end this track |
| `POST /up` | `{"track": id}`: play it next |

Requests from YouTube's comments will come in as `up`s, kept, checked against the library, then
queued or held with the reason. Not built yet.

## Who shows it

Not to be confused with the floor's own music ([`broadcast/jukebox`](../broadcast/jukebox)): that one
plays `/srv/landing/jukebox` into digitization's floor, under everything. This role is the layer on top:
the machine that puts the standby page on the air mixes it in, keeping the floor's sound or muting it.


The standby page ([`broadcast/ch97/page/standby/`](../broadcast/ch97/page/standby/)) reads
`/now.json` and puts the music on its slant. The machine that puts the page on the air mixes in
`/stream.mp3`; see [`broadcast/PROFILE.md`](../broadcast/PROFILE.md), "To YouTube".

`python3 -I machines/jukebox/jukebox --check` says what it finds. ffmpeg and ffprobe, and a Python
with yaml (the crew's). On Windows the first listen from another machine needs an inbound rule for
port 8093; the bay's own OBS reaches it without one.
