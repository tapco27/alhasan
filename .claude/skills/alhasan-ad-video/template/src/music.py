# Synthesizes the score and sound effects for the film, timed from timeline.js.
# Usage: music.py <timeline.js> <out.wav>
import json, re, sys, wave
import numpy as np

SR = 44100
tl = json.loads(re.sub(r'^[^{]*', '', open(sys.argv[1], encoding='utf-8').read()).strip().rstrip(';'))
T = tl['T']
END = T['end']
N = int(SR * (END + 1.0))
rng = np.random.default_rng(7)
dry = np.zeros((N, 2))   # goes straight to the mix
wet = np.zeros((N, 2))   # goes through the reverb
sfx = np.zeros((N, 2))


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, t0, gain=1.0, pan=0.0, send=0.3, bus=None):
    i = int(round(t0 * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), N - i)
    if n <= 0:
        return
    l, r = gain * np.cos((pan + 1) * np.pi / 4), gain * np.sin((pan + 1) * np.pi / 4)
    target = dry if bus is None else bus
    target[i:i + n, 0] += sig[:n] * l
    target[i:i + n, 1] += sig[:n] * r
    if send:
        wet[i:i + n, 0] += sig[:n] * l * send
        wet[i:i + n, 1] += sig[:n] * r * send


# ---------- Instruments ----------
def piano(m, dur, vel=1.0):
    f = mtof(m); n = int(SR * (dur + 2.4)); t = np.arange(n) / SR; out = np.zeros(n)
    for k in range(1, 10):
        fk = f * k * np.sqrt(1 + 0.00035 * k * k)
        if fk > 8000:
            break
        out += np.sin(2 * np.pi * fk * t + k * 0.7) * np.exp(-t * (0.9 + 0.5 * k) * (f / 220) ** 0.3) / k ** 1.9
    out *= np.minimum(t / 0.008, 1.0) * np.where(t > dur, np.exp(-(t - dur) * 5.0), 1.0)
    return out * vel * 0.8


def pluck(m, dur=1.8, vel=1.0, tau=1.1):
    f = mtof(m); P = max(2, int(round(SR / f))); n = int(SR * dur)
    y = rng.random(P) * 2 - 1
    for _ in range(3):
        y = 0.5 * (y + np.roll(y, 1))
    y -= y.mean(); damp = np.exp(-1.0 / (tau * f)); chunks = []
    for _ in range(n // P + 1):
        chunks.append(y); y = damp * (0.65 * y + 0.35 * np.roll(y, 1))
    out = np.concatenate(chunks)[:n]
    out *= np.minimum(np.arange(n) / (0.002 * SR), 1.0)
    out[-2205:] *= np.linspace(1, 0, 2205)
    return out / (np.max(np.abs(out)) + 1e-9) * vel * 0.72


def oud(m, dur=1.6, vel=1.0):
    a, b = pluck(m, dur, vel), pluck(m + 0.05, dur, vel * 0.8)
    out = a.copy(); d = int(0.011 * SR); out[d:] += b[:-d]
    return out * 0.85


def pad(notes, dur, vel=1.0, att=1.0, rel=1.8, bright=2.0):
    n = int(SR * (dur + rel)); t = np.arange(n) / SR; out = np.zeros(n)
    for m in notes:
        f = mtof(m)
        for cents in (-6, 0, 7):
            ff = f * 2 ** (cents / 1200); ph = rng.random() * 6.28
            for k in range(1, 7):
                if ff * k > 6000:
                    break
                out += np.sin(2 * np.pi * ff * k * t + ph * k) / k ** bright
    env = np.minimum(t / att, 1.0) * np.where(t > dur, np.maximum(0, 1 - (t - dur) / rel) ** 2, 1.0)
    return out * env * (1 + 0.07 * np.sin(2 * np.pi * 0.21 * t)) * vel * 0.03


def bass(m, dur, vel=1.0):
    f = mtof(m); n = int(SR * (dur + 0.5)); t = np.arange(n) / SR
    out = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return out * np.minimum(t / 0.03, 1) * np.exp(-t * 0.5) * np.where(t > dur, np.exp(-(t - dur) * 10), 1) * vel * 0.19


def bandnoise(n, lo, hi):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(np.sqrt(lo * hi))) / (np.log(hi / lo) / 2.2)) ** 2)
    y = np.fft.irfft(X, n)
    return y / (np.max(np.abs(y)) + 1e-9)


def dum(vel=1.0):
    n = int(SR * 0.5); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (58 * t + 2.2 * (1 - np.exp(-t * 28)))) * np.exp(-t * 8) * np.minimum(t / 0.004, 1) * vel * 0.33


def tek(vel=1.0):
    n = int(SR * 0.12); t = np.arange(n) / SR
    return bandnoise(n, 1800, 7000) * np.exp(-t * 42) * vel * 0.16


def bell(m, dur=1.6, vel=1.0):
    f = mtof(m); n = int(SR * dur); t = np.arange(n) / SR
    out = sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) * a for r, d, a in ((1, 3, 1), (2.76, 5, .4), (5.4, 8, .2)))
    return out * np.minimum(t / 0.003, 1) * vel * 0.18


def whoosh(dur, lo=300, hi=5000, rise=True):
    n = int(SR * dur); t = np.arange(n) / SR; p = t / dur
    y = bandnoise(n, lo, hi) * np.sin(np.pi * p ** (0.6 if rise else 1.6)) ** 2
    return y * (0.4 + 0.6 * (p if rise else 1 - p))


# ---------- Harmony ----------
CH = {
    'Dm': (38, [50, 57, 62, 65]), 'Bb': (34, [46, 53, 58, 62]), 'Gm': (31, [43, 50, 55, 58]), 'A': (33, [45, 52, 57, 61]),
    'F': (29, [41, 48, 53, 57, 60]), 'C': (36, [48, 55, 60, 64]), 'Csus': (36, [48, 55, 60, 65]), 'Fadd9': (29, [41, 48, 53, 57, 60, 67]),
}


def chord_pad(name, t0, dur, vel=1.0, att=1.0, bright=2.0, low=False):
    root, notes = CH[name]
    add(pad(notes, dur, vel, att=att, bright=bright), t0, pan=0.0, send=0.45)
    if low:
        add(pad([root + 12], dur, vel * 0.5, att=att, bright=2.4), t0, send=0.3)


def notes(seq, a, b, inst, vel=0.5, pan=0.0, send=0.45, dur=1.2):
    # seq: (fraction of the span, midi note, optional velocity scale)
    for item in seq:
        frac, m = item[0], item[1]; v = vel * (item[2] if len(item) > 2 else 1)
        add(inst(m, dur, v), a + frac * (b - a), pan=pan, send=send)


S = lambda k: T[k]

# Scene 1: lullaby motif over Dm - Bb
a, b = S('s1'), S('s2'); h = (b - a) / 2
chord_pad('Dm', a + .2, h, .8, att=1.6); chord_pad('Bb', a + h, h, .8)
notes([(.07, 69), (.19, 74), (.31, 77), (.43, 76, .8), (.56, 74), (.70, 69, .8), (.80, 70), (.91, 74, .9)], a, b, piano, .42, pan=-.15)

# Scene 2: the father's line, darker (Gm - A)
a, b = S('s2'), S('s3'); h = (b - a) / 2
chord_pad('Gm', a, h, .85, low=True); chord_pad('A', a + h, h, .8, low=True)
notes([(.06, 67), (.24, 70), (.42, 74, .8), (.58, 69), (.74, 73), (.90, 76, .7)], a, b, piano, .36, pan=.1, dur=1.6)

# Scene 3: the child's question, then silence
a, b = S('s3'), S('s4'); d = b - a
chord_pad('Dm', a, d * .35, .75, low=True); chord_pad('Bb', a + d * .35, d * .35, .7, low=True); chord_pad('A', a + d * .7, d * .3, .45, att=1.5)
notes([(.03, 74), (.14, 77), (.26, 81, .8), (.38, 70), (.49, 74), (.60, 77, .8), (.76, 76, .55)], a, b, piano, .36, pan=-.1, dur=2.0)

# Scene 4: the decision, a quiet pulse starts
a, b = S('s4'), S('s5'); n = max(2, round((b - a) / 2)); bd = (b - a) / n
for i, name in enumerate((['Dm', 'F', 'C', 'Gm'] * 3)[:n]):
    t0 = a + i * bd; root, tones = CH[name]
    chord_pad(name, t0, bd, .8, att=.5); add(bass(root + 12, bd * .9, .5), t0, send=.1)
    if i == 0:
        add(piano(tones[2] + 12, 1.5, .4), t0 + .3, send=.5); continue
    for k, m in enumerate([tones[1] + 12, tones[2] + 12, tones[1] + 12, tones[3] + 12] * 2):
        add(piano(m, .5, .2 + .05 * (k % 4 == 0)), t0 + k * bd / 8, pan=(-.2 if k % 2 else .2), send=.4)

# Scene 5: waiting on the call
a, b = S('s5'), S('s6'); h = (b - a) / 2
chord_pad('Bb', a, h, .7, low=True); chord_pad('C', a + h, h, .75, low=True)
add(piano(77, 2, .28), a + h + .4, send=.6)

# Scene 6: the warm reply
a, b = S('s6'), S('s7'); n = max(2, round((b - a) / 2)); bd = (b - a) / n
for i, name in enumerate((['F', 'F', 'C', 'Csus'] * 3)[:n]):
    t0 = a + i * bd; root, tones = CH[name]
    chord_pad(name, t0, bd, .85, att=.6, bright=1.8); add(bass(root + 12, bd * .9, .45), t0, send=.1)
    for k, m in enumerate([tones[2], tones[3], tones[2] + 12, tones[3]]):
        add(piano(m + 12, .8, .24), t0 + k * bd / 4, pan=(.2 if k % 2 else -.2), send=.45)

# Scene 7: on site, the lift into the hopeful theme (Bb - C)
a, b = S('s7') + tl.get('LEAD7', 1.2), S('s8'); h = (b - a) / 2
add(dum(.9), a, send=.5); add(bass(22 + 12, 2.5, .6), a, send=.2)
chord_pad('Bb', a, h, 1.5, att=.4, bright=1.7, low=True); chord_pad('C', a + h, h, 1.6, att=.4, bright=1.7, low=True)
add(bass(CH['C'][0] + 12, h * .9, .55), a + h, send=.1)
notes([(.02, 70), (.14, 74), (.26, 77), (.38, 82, .9), (.52, 72), (.64, 76), (.76, 79), (.88, 84, .9)], a, b, oud, .78, pan=.15)

# Scene 8: build stages, one chord each (F - C - Dm - Bb); fewer stages when the scene is short
a = S('s8'); ns = max(1, min(4, round((S('s9') - a) / 2.75))); sd = (S('s9') - a) / ns; beat = sd / 4
MEL = {'F': [69, 72, 77, 81], 'C': [67, 72, 76, 79], 'Dm': [69, 74, 77, 81], 'Bb': [70, 74, 77, 82]}
for i, name in enumerate(['F', 'C', 'Dm', 'Bb'][:ns]):
    t0 = a + i * sd; root, tones = CH[name]
    chord_pad(name, t0, sd, 1.35, att=.3, bright=1.6, low=True)
    add(bell(84 if i % 2 == 0 else 88, 1.8, .5), t0, pan=.3, send=.7)
    for q in range(4):
        add(bass(root + 12, beat * .8, .55 if q % 2 == 0 else .35), t0 + q * beat, send=.08)
        add(dum(.55 if q == 0 else .3), t0 + q * beat, send=.25) if q in (0, 2) else None
        add(tek(.8), t0 + q * beat + beat / 2, pan=.25, send=.3)
    arp = [tones[1], tones[2], tones[3], tones[2]] * 2
    for k, m in enumerate(arp):
        add(pluck(m + 12, 1.0, .42 + .08 * (k % 4 == 0)), t0 + k * beat / 2, pan=(-.35 if k % 2 else .35), send=.35)
    for k, m in enumerate(MEL[name]):
        add(oud(m, 1.4, .66), t0 + k * beat, pan=.1, send=.45)

# Scene 9: back to the child, the same motif in major
a, b = S('s9'), S('s10'); q = (b - a) / 4
if b - a >= 4:
    for i, name in enumerate(['F', 'Bb', 'C', 'Csus']):
        chord_pad(name, a + i * q, q, .7 + .1 * i, att=.9 if i == 0 else .5, bright=1.9 - .08 * i, low=i > 1)
    notes([(.05, 72), (.13, 77), (.21, 81), (.29, 79, .8), (.37, 77), (.46, 72, .8), (.54, 74), (.62, 77), (.70, 82), (.78, 81, .9), (.86, 79), (.94, 76, .9)], a, b, piano, .3, pan=-.1)
else:
    chord_pad('Bb', a, (b - a) / 2, 1.0, att=.3, low=True); chord_pad('C', a + (b - a) / 2, (b - a) / 2, 1.1, att=.3, low=True)
    notes([(.1, 74), (.55, 76)], a, b, piano, .35)

# Scene 10: the narrator, full theme (F - C - Dm - Bb)
a, b = S('s10'), S('s11'); bd = (b - a) / 4
J_MEL = [[69, 72, 77, 81], [79, 76, 72, 67], [77, 74, 69, 74], [74, 77, 82, 81]]
for i, name in enumerate(['F', 'C', 'Dm', 'Bb']):
    t0 = a + i * bd; root, tones = CH[name]
    chord_pad(name, t0, bd, 1.15, att=.35, bright=1.55, low=True)
    add(bass(root + 12, bd * .9, .6), t0, send=.1); add(dum(.45), t0, send=.3); add(tek(.6), t0 + bd * .625, pan=.2, send=.3)
    for k, m in enumerate(tones[:4]):
        add(piano(m + 12, 1.6, .3), t0 + k * .03, pan=-.2, send=.5)
    for k, m in enumerate(J_MEL[i]):
        add(oud(m, 1.5, .55), t0 + k * bd / 4, pan=.15, send=.5)

# Scene 11: brand card, resolve when the logo lands
a = S('s11'); land = a + tl.get('LAND', 2.3); lead = land - a
chord_pad('Csus', a - .1, lead * .55, 1.0, att=.4, bright=1.6, low=True); chord_pad('C', a + lead * .5, lead * .5, 1.05, att=.3, bright=1.6, low=True)
chord_pad('Fadd9', land, END - land - 1.6, 1.15, att=.25, bright=1.7, low=True)
add(bass(29 + 12, 5, .7), land, send=.2); add(dum(.8), land, send=.5)
for k, m in enumerate([65, 69, 72, 77, 81, 84]):
    add(piano(m, 3.5, .34), land + k * .17, pan=(-.25 + .1 * k), send=.6)
for k, m in enumerate([84, 89]):
    add(piano(m, 3, .26), tl.get('cues', tl.get('CUES', {})).get('contact', a + 4.3) + .5 + k * .5, pan=.2, send=.7)
# Shimmer while the logo is revealed
sd_ = lead + .4; n = int(SR * sd_); t = np.arange(n) / SR
shim = sum(np.sin(2 * np.pi * mtof(m) * t + i) for i, m in enumerate([89, 93, 96, 101])) * np.sin(np.pi * t / sd_) ** 2 * (1 + .3 * np.sin(2 * np.pi * 7 * t)) * .012
add(shim + bandnoise(n, 6000, 12000) * np.sin(np.pi * t / sd_) ** 2 * .012, a + .2, send=.8)
add(bell(96, 2.2, .5), land + .6, pan=.2, send=.8)

# ---------- Sound effects ----------
def crayon(dur, kind='line'):
    n = int(SR * dur); t = np.arange(n) / SR; p = t / dur
    if kind == 'zig':
        am = np.abs(np.sin(2 * np.pi * 5.5 * t)) ** .6
    else:
        k = max(4, int(dur * (26 if kind == 'write' else 15))); am = np.interp(t, np.linspace(0, dur, k), .35 + .65 * rng.random(k))
    return bandnoise(n, 900, 5200) * np.sin(np.pi * p) ** .5 * am


def illustrated_effects():
    for base, strokes in ((S('s1'), [(.7, 1.4), (1.5, 3.0), (3.1, 4.3), (4.35, 5.35, 'zig'), (5.5, 6.15), (6.2, 6.38), (6.42, 6.6), (6.75, 7.3), (7.3, 7.85)]),
                          (S('s9'), [(2.6, 3.55), (3.6, 3.82), (4.0, 4.9, 'write'), (5.0, 6.1, 'write'), (6.5, 6.75), (6.85, 7.35), (7.55, 8.3)])):
        for st in strokes:
            add(crayon(st[1] - st[0], st[2] if len(st) > 2 else 'line'), base + st[0], gain=.05, pan=.1, send=.15, bus=sfx)

    p4 = S('s4')
    add(whoosh(1.0, 200, 2500), p4 + 1.6, gain=.05, send=.3, bus=sfx)                       # phone slides in
    for i in range(17):                                                                     # typing
        tt = p4 + 3.0 + 1.6 * i / 17; n = int(SR * .03); t = np.arange(n) / SR
        add((np.sin(2 * np.pi * 1900 * t) * .5 + bandnoise(n, 2500, 8000)) * np.exp(-t * 160), tt, gain=.035, pan=.05, send=.1, bus=sfx)
    n = int(SR * .12); t = np.arange(n) / SR
    add(np.sin(2 * np.pi * 170 * t) * np.exp(-t * 40) + bandnoise(n, 2000, 6000) * np.exp(-t * 120) * .5, p4 + 7.35, gain=.07, send=.15, bus=sfx)   # tap
    # Ringback, then the connect chime
    p5 = S('s5')
    for r0 in (.15, 1.0):
        n = int(SR * .62); t = np.arange(n) / SR
        add((np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * np.sin(np.pi * t / .62) ** .3, p5 + r0, gain=.022, send=.25, bus=sfx)
    for k, m in enumerate((81, 88)):
        add(bell(m, .7, .5), p5 + 2.0 + k * .11, send=.4, bus=sfx)
    # Zoom through the phone, pin drop
    p7 = S('s7')
    add(whoosh(1.0, 250, 6000), p7 + .25, gain=.09, send=.4, bus=sfx)
    add(bell(79, 1.2, .6), p7 + 2.1, pan=-.1, send=.6, bus=sfx)
    # Build stages: steel clinks, concrete rumble, soft thumps
    p8 = S('s8')
    for i in range(9):
        tt = p8 + .25 + i * .19 + rng.random() * .05; n = int(SR * .25); t = np.arange(n) / SR
        clink = sum(np.sin(2 * np.pi * f * (1 + .02 * rng.random()) * t) * np.exp(-t * d) for f, d in ((2140, 26), (3420, 34), (5230, 46)))
        add(clink, tt, gain=.012, pan=rng.random() - .5, send=.5, bus=sfx)
    n = int(SR * 2.5); t = np.arange(n) / SR
    add(bandnoise(n, 60, 500) * np.sin(np.pi * t / 2.5) ** .7, p8 + 2.9, gain=.05, send=.2, bus=sfx)
    for k in range(4):
        add(dum(.5), p8 + 5.6 + k * .64 + .6, gain=.5, send=.4, bus=sfx)
    add(whoosh(.95, 300, 7000), p8 + 10.05, gain=.08, send=.5, bus=sfx)


def listed_effects(fx):
    # Effects for the footage edit: phone slides in, tap, zoom
    if 'phone_in' in fx:
        add(whoosh(.7, 200, 2500), fx['phone_in'], gain=.05, send=.3, bus=sfx)
    if 'tap' in fx:
        n = int(SR * .12); t = np.arange(n) / SR
        add(np.sin(2 * np.pi * 170 * t) * np.exp(-t * 40) + bandnoise(n, 2000, 6000) * np.exp(-t * 120) * .5, fx['tap'], gain=.07, send=.15, bus=sfx)
    if 'zoom' in fx:
        add(whoosh(.5, 250, 6000), fx['zoom'], gain=.08, send=.4, bus=sfx)


listed_effects(tl['SFXT']) if 'SFXT' in tl else illustrated_effects()

# ---------- Reverb and master ----------
def make_ir(dur, seed):
    n = int(SR * dur); r = np.random.default_rng(seed); t = np.arange(n) / SR
    X = np.fft.rfft(r.standard_normal(n) * np.exp(-t * 2.5)); f = np.fft.rfftfreq(n, 1 / SR)
    ir = np.fft.irfft(X / (1 + (f / 3200) ** 2), n); k = int(.012 * SR); ir[:k] *= np.linspace(0, 1, k)
    return ir / np.sqrt(np.sum(ir ** 2))


def convolve(x, ir):
    n = len(x) + len(ir) - 1; nfft = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]


rev = np.stack([convolve(wet[:, c], make_ir(2.8, 11 + c)) for c in (0, 1)], axis=1)
mix = dry + sfx + rev * 0.55
# Master EQ: trim sub/low end, add presence so the melody carries on phone speakers
f = np.fft.rfftfreq(N, 1 / SR)
gain_db = -5.0 / (1 + (f / 170) ** 2) + 2.5 * np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(3000)) / 0.6) ** 2)
H = 10 ** (gain_db / 20) * (f / 38) ** 2 / (1 + (f / 38) ** 2)
mix = np.stack([np.fft.irfft(np.fft.rfft(mix[:, c]) * H, N) for c in (0, 1)], axis=1)
# Fade in/out, gentle saturation, peak at -3 dBFS
t = np.arange(N) / SR
mix *= (np.minimum(t / 0.6, 1) * np.clip((END - t) / 1.4, 0, 1))[:, None]
mix = np.tanh(mix / (np.percentile(np.abs(mix), 99.9) + 1e-9) * 0.9)
mix = mix / np.max(np.abs(mix)) * 0.707
mix = mix[:int(SR * END)]
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('wrote', sys.argv[2], f'{len(mix) / SR:.1f}s')
