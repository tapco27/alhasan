# Checks a finished hybrid ad: lip-sync of every spoken caption (sound vs picture) and loudness.
# Usage: verify.py <ad.js> <footage.mp4> <final.mp4>
import json, re, subprocess, sys
import numpy as np

SR = 8000
ad = json.loads(re.sub(r'^[^{]*', '', open(sys.argv[1], encoding='utf-8').read()).strip().rstrip(';'))
load = lambda f: np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(float)
src, out = load(sys.argv[2]), load(sys.argv[3])
worst = 0
for c in ad['caps']:
    sa, sb = c['src']; ref = src[int(sa * SR):int(sb * SR)]; best = (-1, 0)
    for off in np.arange(-.25, .2501, .005):
        i = int((c['sa'] + off) * SR); w = out[i:i + len(ref)]
        if len(w) == len(ref):
            best = max(best, (float(np.dot(ref, w) / (np.linalg.norm(ref) * np.linalg.norm(w) + 1e-9)), off))
    worst = max(worst, abs(best[1]))
    print(f"{c['sa']:6.2f}s  offset {best[1] * 1000:+4.0f} ms  {c['text'][:34]}")
print('lip-sync:', 'OK' if worst <= 1.0 / ad['fps'] else f'CHECK (worst {worst * 1000:.0f} ms, more than one frame)')
log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', sys.argv[3], '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
print(' '.join(l.strip() for l in log.splitlines()[-12:] if re.match(r'\s+(I|Peak):', l)))
