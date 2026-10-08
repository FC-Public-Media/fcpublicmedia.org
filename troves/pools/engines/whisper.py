"""whisper.py -- the pools page's Whisper engine (faster-whisper, large-v3).

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
"""
import json, math, os, site, sys, wave

for d in site.getsitepackages():   # CUDA's libraries come as wheels: tell Windows where they are
    for sub in ("nvidia/cublas/bin", "nvidia/cudnn/bin"):
        p = os.path.join(d, sub)
        if os.path.isdir(p):
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

import numpy as np
from faster_whisper import WhisperModel


def samples(path):
    """The WAV's samples as float32, read here: faster-whisper's own decoder (av)
    does not match the av that came with it."""
    with wave.open(path) as w:
        if w.getnchannels() != 1 or w.getframerate() != 16000 or w.getsampwidth() != 2:
            raise ValueError("not 16 kHz mono 16-bit")
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def main():
    paths = json.load(open(sys.argv[1], encoding="utf-8"))
    model = WhisperModel("large-v3", device="cuda", compute_type="float16", download_root=sys.argv[2])
    for i, path in enumerate(paths):
        try:
            segs, _ = model.transcribe(samples(path), language="en", beam_size=5,
                                       vad_filter=True, condition_on_previous_text=False)
            out = [{"at": round(s.start, 2), "len": round(s.end - s.start, 2), "text": s.text.strip(),
                    "conf": round(math.exp(s.avg_logprob), 3), "no_speech": round(s.no_speech_prob, 3),
                    "logp": round(s.avg_logprob, 3), "cr": round(s.compression_ratio, 2)} for s in segs]
            print(json.dumps({"i": i, "segments": out}), flush=True)
        except Exception as e:   # one recording failing is one line, not the job
            print(json.dumps({"i": i, "error": f"{type(e).__name__}: {e}"}), flush=True)


if __name__ == "__main__":
    main()
