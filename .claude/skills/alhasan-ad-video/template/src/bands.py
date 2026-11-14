# Prints per-section band levels (dB) of a WAV so the mix balance can be checked without listening.
import sys, wave, numpy as np
w = wave.open(sys.argv[1]); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').reshape(-1, 2).mean(1) / 32768
edges = [float(v) for v in sys.argv[2].split(',')]
bands = [(20, 150), (150, 500), (500, 2000), (2000, 8000)]
print('section      ' + ''.join(f'{lo}-{hi}Hz'.rjust(13) for lo, hi in bands) + '   total')
for a, b in zip(edges[:-1], edges[1:]):
    seg = x[int(a * sr):int(b * sr)]; X = np.abs(np.fft.rfft(seg)) ** 2; f = np.fft.rfftfreq(len(seg), 1 / sr)
    tot = 10 * np.log10(np.mean(seg ** 2) + 1e-12)
    print(f'{a:5.1f}-{b:5.1f}  ' + ''.join(f'{10 * np.log10(X[(f >= lo) & (f < hi)].sum() / X.sum() + 1e-12):13.1f}' for lo, hi in bands) + f'  {tot:6.1f}')
