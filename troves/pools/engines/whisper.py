"""see docs/inline/troves/pools/engines/whisper.py.md#1"""
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
    """see docs/inline/troves/pools/engines/whisper.py.md#2"""
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
