# `troves/pools/engines/whisper.py`

Moved out of the file. Unreviewed.

## 1

Above `import json, math, os, site, sys, wave`

whisper.py -- the pools page's Whisper engine (faster-whisper, large-v3).

    python whisper.py LIST.json MODELS_DIR       one JSON line per WAV, as each is heard

LIST.json is a list of 16 kHz mono 16-bit WAV paths, the job's recordings in
order. The model is loaded once for the whole job. For each WAV, a line:
{"i": n, "segments": [{"at", "len", "text", "conf", "no_speech", "logp", "cr"}]}
or {"i": n, "error": "..."}. `at` is seconds from the WAV's start (pools.py joins recordings into each WAV and maps it back).

Held back from inventing: it hears only what a voice-activity filter passes
(no silence or hum reaches it), and it is not fed its own previous words
(which is what sends Whisper round in loops). Every segment keeps the numbers
that tell an invention from speech: how sure it is that anything was said
(no_speech), how sure of the words (logp, and conf = e^logp), and how
repetitive the text is (cr, the compression ratio). The page decides what to do
with them; this only hears.

Runs in its own venv (bay/faster-whisper-1.1.1.yml). Python 3.12.

## 2

Above `with wave.open(path) as w:`

The WAV's samples as float32, read here: faster-whisper's own decoder (av)
does not match the av that came with it.
