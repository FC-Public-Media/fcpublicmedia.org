# The pools trove

The storage pools and their recordings, as one page. `fcpm pools` serves `pools.py` on
`127.0.0.1:8091` (production serves it always) and opens Edge onto it; `fcpm pools timeline` opens
at `/timeline`. Verbs: `key` (the depot's password, into Credential Manager), `sample [clear]`, `groups`.

## Config

`machines/<profile>/pools.yml`: `pools:`, `view:` (`debris_seconds`, `cluster_minutes`,
`day_starts_at`), `stages:` (label, colour), `transcribe:`, and a default `pipeline:`. A pool is
`smb` (the depot's shares, staged by `stage_by_share`) or `folder` (a subfolder named after a stage
is that stage; `create: true` with `capacity:` is the emulated pool). A recording ends at its last
write and starts its length earlier (WAV or AIFF header), else at the time in its name.

## Pages

`/` is the squares: a row per share or folder, by day and cluster. Colour is the stage, brightness
the average level, size the length; anything under `debris_seconds` piles as chips. Border: pulsing
is under 90 s old, bright is today, dashed is under 3 s. A click opens Explorer, only inside a pool.

`/timeline` is one lane per night from `day_starts_at`. Dragging along it (or clicking a date, or
`all`) opens a window below, where: drag selects; `z` zooms to the selection; the wheel zooms;
Backspace goes back; Esc closes; Space plays through, skipping gaps; `m` is sound; `t` is transcript
time; ctrl-click, right-click or a long press plays exactly there. Settings: amplify (dB), compress
gaps, preview removals, follow the playhead, skip clips under 3, 6 or 10 s.

## Groups

The window's list puts the selection under a show (`site/_shows/`) or a provisional name, or marks
it for removal or transcription. Groups and the page's state live in
`%LOCALAPPDATA%\<profile>\pools\`; the pools server is their one writer. **Remove marked** moves
marked recordings into the pool's `.removed\<date>\`; nothing is deleted. A recording gone, or in
the Recycle Bin, stays as a ghost.

The manifest button writes and downloads `manifests\<time>-<hash>.json`: each recording in the
window by SHA-256 with its part in the edit, the cuts, settings, groups and transcripts, and the
manifest's own SHA-256 over its canonical form, to timestamp or seal.

## Transcription

Experimental. The speech button sends what is marked, after skips and cuts, to the engine in
`transcribe:` (`engines/whisper.py`: faster-whisper on CUDA; `engines/windows-speech.ps1`: rough,
nothing installed). Jobs and results are `jobs\<id>*.json`; transcripts stay on this computer.
Transcript time shows each region's control text, and each engine's words scored against it.

## Episodes

In a show's group, the episode panel keeps title, season, number, people and summary, names the
outputs `<show>-s<season>e<number>` (else by date), and shows the show's pipeline
(`site/_shows/<slug>.md` `pipeline:`, else `pools.yml`). An episode is held (◇) until released (◆).
With `eject: true`, releasing commits `episodes/<out>.yml` to `work/<repo>@ejected`; a person pushes.
`episodes.py tick` (production, every few minutes) admits each released episode to
[post](../post/README.md#admission) and records the take on the episode (`fcpm crew episodes`).
