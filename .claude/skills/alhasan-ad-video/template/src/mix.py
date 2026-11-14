# Mixes the voice lines over the score: places each line, ducks the music under speech.
# Usage: mix.py <timeline.js|ad.js> <music.wav> <voiceDir> <out.wav> [footage.mp4]
import json, os, re, subprocess, sys, wave
import numpy as np

SR = 44100
tl = json.loads(re.sub(r'^[^{]*', '', open(sys.argv[1], encoding='utf-8').read()).strip().rstrip(';'))
vdir = sys.argv[3]
MUSIC_GAIN, DUCK, VOICE_RMS = 0.55, 0.30, 0.11
PHONE_LINES = set(tl.get('PHONE_LINES', [6] if 'SRC_AUDIO' not in tl else []))   # heard through the phone speaker
CLEAN = 'highpass=f=75,acompressor=threshold=0.05:ratio=4:attack=2:release=60'


def read_wav(p):
    w = wave.open(p)
    return (np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float64) / 32768).reshape(-1, w.getnchannels())


def voice(n):
    # Clean-up per line: rumble filter, light compression; phone lines are band-limited
    chain = CLEAN
    if n in PHONE_LINES:
        chain = 'highpass=f=300,lowpass=f=3400,' + chain
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(vdir, f'L{n}.wav'), '-af', chain, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, np.float32).astype(np.float64)
    return level(x)


def level(x):
    act = x[np.abs(x) > 0.02 * np.abs(x).max()]
    return x * VOICE_RMS / (np.sqrt(np.mean(act ** 2)) + 1e-9)


def footage_audio(seg):
    # Dialogue recorded with the footage (keeps lip-sync)
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(seg['src0']), '-to', str(seg['src1']), '-i', sys.argv[5], '-af', CLEAN, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = level(np.frombuffer(pcm, np.float32).astype(np.float64)); f = int(.06 * SR)
    x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    return x


music = read_wav(sys.argv[2]); N = len(music)
gain = np.ones(N); speech = np.zeros((N, 2))
for x, at in [(voice(v['n']), v['at']) for v in tl['VOICE']] + [(footage_audio(g), g['at']) for g in tl.get('SRC_AUDIO', [])]:
    i = int(at * SR); n = min(len(x), N - i)
    speech[i:i + n] += x[:n, None]
for a, b in tl.get('SPEECH', [[v['at'], v['at'] + v['dur']] for v in tl['VOICE']]):
    # Duck: ease down before the line, hold, ease back up after it
    i0, i1, i2, i3 = (int(s * SR) for s in (a - .35, a, b, b + .8))
    shape = np.ones(N)
    shape[max(i0, 0):i1] = DUCK + (1 - DUCK) * (.5 + .5 * np.cos(np.linspace(0, np.pi, i1 - max(i0, 0))))
    shape[i1:i2] = DUCK
    shape[i2:min(i3, N)] = DUCK + (1 - DUCK) * (.5 - .5 * np.cos(np.linspace(0, np.pi, i3 - i2)))[:max(0, min(i3, N) - i2)]
    gain = np.minimum(gain, shape)

mix = music * MUSIC_GAIN * gain[:, None] + speech
peak = np.abs(mix).max()
if peak > 0.98:
    mix *= 0.98 / peak
with wave.open(sys.argv[4], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
sp = np.abs(speech[:, 0]) > 0.01
print(f'voice {rms(speech[sp, 0]):.1f} dBFS | music under voice {rms((music * MUSIC_GAIN * gain[:, None])[sp].mean(1)):.1f} | music alone {rms((music * MUSIC_GAIN)[gain > .99].mean(1)):.1f} | peak {peak:.2f}')
