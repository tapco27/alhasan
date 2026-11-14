# First look at new footage: contact sheet (one frame per second), scene cuts, speech intervals, and whether music sits under the speech.
# Usage: look.py <footage.mp4> <outDir>
import glob, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
run = lambda *a: subprocess.run(a, capture_output=True, text=True)
print(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate', '-of', 'compact', src).stdout.strip())

# Contact sheet
for f in glob.glob(os.path.join(out, 's_*.jpg')):
    os.remove(f)
run('ffmpeg', '-v', 'error', '-i', src, '-vf', 'fps=1,scale=216:-2', '-q:v', '4', os.path.join(out, 's_%03d.jpg'))
files = sorted(glob.glob(os.path.join(out, 's_*.jpg'))); cols = 11
w, h = Image.open(files[0]).size
sheet = Image.new('RGB', (cols * w, ((len(files) + cols - 1) // cols) * h), '#111')
for i, f in enumerate(files):
    im = Image.open(f); ImageDraw.Draw(im).text((6, 4), f'{i}s', fill='#0f0'); sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(os.path.join(out, 'sheet.jpg'), quality=85)
print('contact sheet:', os.path.join(out, 'sheet.jpg'))

# Scene cuts
log = run('ffmpeg', '-hide_banner', '-nostats', '-i', src, '-vf', "select='gt(scene,0.3)',showinfo", '-an', '-f', 'null', '-').stderr
print('cuts (s):', ' '.join(l.split('pts_time:')[1].split()[0] for l in log.splitlines() if 'pts_time:' in l))

# Speech intervals from the soundtrack's loudness envelope
SR = 16000
x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(float)
hop, win = int(.01 * SR), int(.03 * SR)
e = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, 'same')[::hop] + 1e-12); db = 20 * np.log10(e / e.max()); on = db > -38
segs, i = [], 0
while i < len(on):
    if on[i]:
        j = i
        while j < len(on) and (on[j] or on[j:j + 18].any()):
            j += 1
        segs.append((i * .01, j * .01)); i = j
    else:
        i += 1
segs = [s for s in segs if s[1] - s[0] > .15]
print('sound (s):', ' '.join(f'{a:.2f}-{b:.2f}' for a, b in segs))
# Gaps: near -50 dBFS means clean dialogue; around -25 to -35 means music or ambience is baked in there
for (a0, b0), (a1, b1) in zip(segs, segs[1:]):
    if a1 - b0 > .8:
        g = x[int((b0 + .2) * SR):int((a1 - .2) * SR)]
        print(f'  gap {b0:.1f}-{a1:.1f}s: {20 * np.log10(np.sqrt(np.mean(g ** 2)) + 1e-9):.0f} dBFS')
