# Transcribes the voice files with word timestamps so lines can be matched and cut precisely.
import sys, json, subprocess
import numpy as np
from faster_whisper import WhisperModel
model = WhisperModel(sys.argv[1], device="cpu", compute_type="int8")
out = {}
for f in sys.argv[3:]:
    # Decode with ffmpeg to 16 kHz mono float32
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), language="ar", word_timestamps=True, vad_filter=False, beam_size=5)
    words = [{"w": w.word.strip(), "a": round(w.start, 2), "b": round(w.end, 2)} for s in segs for w in s.words]
    out[f] = words
    print(f, "|", " ".join(f"{w['w']}[{w['a']}-{w['b']}]" for w in words), flush=True)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
