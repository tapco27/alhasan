# Cuts the four voice recordings into the nine script lines and reports their timing.
# Usage: voice.py <voiceDir> <outDir>
import json, os, subprocess, sys, wave
import numpy as np

SR = 44100
src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)


def load(name):
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(src, name), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).astype(np.float64)


def envelope(x, hop=0.005, win=0.02):
    h, w = int(hop * SR), int(win * SR)
    e = np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same')[::h] + 1e-12)
    return 20 * np.log10(e / e.max()), hop


def quietest(x, a, b):
    # Centre of the quietest 60 ms between a and b (seconds)
    e, hop = envelope(x); i0, i1 = int(a / hop), int(b / hop)
    sm = np.convolve(e, np.ones(12) / 12, 'same')[i0:i1]
    return (i0 + int(np.argmin(sm))) * hop, float(sm.min())


def bounds(x, a, b, thr=-34):
    # First and last moment of speech between a and b
    e, hop = envelope(x); i0, i1 = int(a / hop), min(int(b / hop), len(e))
    idx = np.where(e[i0:i1] > thr)[0]
    return (i0 + idx[0]) * hop, (i0 + idx[-1] + 1) * hop


# Which file holds which lines, with rough windows taken from the transcript.
# "marks" are rough positions inside a line where a caption or on-screen phrase changes.
A, B, Cf, D = load('a.mp3'), load('b.mp3'), load('c.mp3'), load('d.mp3')
cut_c, level_c = quietest(Cf, 0.95, 1.45)
print(f'father: split between line 1 and 3 at {cut_c:.2f}s (dip {level_c:.0f} dB)')
PLAN = {
    1: (Cf, 0.0, cut_c, {}),
    3: (Cf, cut_c, 3.40, {}),
    5: (Cf, 3.40, 99, {}),
    2: (B, 0.0, 1.60, {}),
    4: (B, 1.60, 99, {'part2': (2.92, 3.75)}),
    6: (D, 0.0, 6.26, {'part2': (2.17, 2.60)}),
    7: (D, 6.26, 99, {'part2': (8.94, 9.32)}),
    8: (A, 0.0, 5.63, {'part2': (2.44, 2.90)}),
    9: (A, 5.63, 99, {'slogan': (7.75, 8.15), 'last': (9.34, 9.76)}),
}

info = {}
for n, (x, a, b, marks) in sorted(PLAN.items()):
    b = min(b, len(x) / SR)
    s, e = bounds(x, a, b)
    s, e = max(a, s - 0.04), min(b, e + 0.14)
    seg = x[int(s * SR):int(e * SR)].copy()
    # Short fades so cuts never click
    fi, fo = int(0.012 * SR), int(0.06 * SR)
    seg[:fi] *= np.linspace(0, 1, fi); seg[-fo:] *= np.linspace(1, 0, fo)
    # Same speech level for every line
    act = seg[np.abs(seg) > 0.02 * np.abs(seg).max()]
    seg *= 0.09 / (np.sqrt(np.mean(act ** 2)) + 1e-9)
    rel = {}
    for k, (ma, mb) in marks.items():
        if mb - ma < 0.45:      # no clean pause known: take the quietest point
            q, _ = quietest(x, ma, mb); rel[k] = round(q - s, 3)
        else:                   # a real pause: the phrase starts where speech resumes
            rel[k] = round(bounds(x, (ma + mb) / 2, b)[0] - 0.03 - s, 3)
    with wave.open(os.path.join(out, f'L{n}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(seg, -1, 1) * 32767).astype('<i2').tobytes())
    info[n] = {'dur': round(len(seg) / SR, 3), **rel}
    print(n, f'{s:.2f}-{e:.2f}', info[n], f'peak {np.abs(seg).max():.2f}')
json.dump(info, open(os.path.join(out, 'lines.json'), 'w'), indent=1)
