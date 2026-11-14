# Builds the edit for the hybrid cut: footage segments (with speed), graphic inserts, captions, cues and audio plan.
# Usage: edit.py <lines.json> <site/marks.json> <out ad.js> <footage.mp4>
# This is the one file to change for a new ad: BRAND, NARRATION, CUT and SPOKEN below.
import json, subprocess, sys

L = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}
marks = json.load(open(sys.argv[2]))
# Frame rate and frame count of the footage
probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=r_frame_rate,nb_read_packets', '-of', 'json', sys.argv[4]], capture_output=True, text=True, check=True)
st = json.loads(probe.stdout)['streams'][0]; num, den = st['r_frame_rate'].split('/')
SRC_FPS, SRC_FRAMES = float(num) / float(den), int(st['nb_read_packets'])

# ---------- Brand card and narrator text ----------
BRAND = {'name': 'شركة الحسن للهندسة والبناء', 'slogan': 'من أرض المشروع… منبني الثقة.', 'phoneIntl': '+963 947 728 079', 'phoneLocal': '0947 728 079', 'website': 'alhasan-ec.com'}
# Narrator's line in two phrases (first over the footage, second over the gold finale); <b> marks the gold words
NARRATION = {'vo1': 'في بيوت منشتريها<br>حتى نسكن فيها…', 'vo2': 'وفي بيوت منبني عليها<br><b>حلم الرجعة.</b>'}

# ---------- The cut: source in/out (seconds of the supplied video) and playback speed ----------
# Silent stretches run faster; anything with lip-sync stays at speed 1.
CUT = [
    dict(id='dialog',   type='clip', src=(0.00, 15.29), speed=1),
    dict(id='react',    type='clip', src=(15.29, 18.17), speed=2),
    dict(id='pick',     type='clip', src=(18.17, 19.70), speed=2),
    dict(id='phone',    type='phone', dur=4.0, freeze=19.70),
    dict(id='call',     type='clip', src=(22.125, 25.875), speed=1),
    dict(id='office',   type='clip', src=(25.875, 31.75), speed=1),
    dict(id='site',     type='clip', src=(31.75, 38.71), speed=1),
    dict(id='rebar',    type='clip', src=(38.71, 39.25), speed=0.75, label='الحديد والتسليح'),
    dict(id='pour',     type='clip', src=(39.25, 42.25), speed=1.8, label='صبّ البيتون'),
    dict(id='frame',    type='clip', src=(42.25, 44.25), speed=1.5, label='الأعمدة والأسقف'),
    dict(id='interior', type='clip', src=(44.25, 45.75), speed=1.25, label='الشقق من الداخل'),
    dict(id='child',    type='clip', src=(45.75, 50.00), speed=2),
    dict(id='drawing',  type='clip', src=(50.00, 53.20), speed=1),
    dict(id='finale',   type='finale', dur=3.0, freeze=53.20),
    dict(id='brand',    type='brand', dur=9.7),
]
t = 0.0
for s in CUT:
    if s['type'] == 'clip':
        s['dur'] = (s['src'][1] - s['src'][0]) / s['speed']
    s['t0'], s['t1'] = round(t, 3), round(t + s['dur'], 3)
    t = s['t1']
SEG = {s['id']: s for s in CUT}
END = round(t, 2)


def out(src_t):
    # Source time -> output time (for speed-1 footage segments)
    for s in CUT:
        if s['type'] == 'clip' and s['src'][0] - 0.6 <= src_t <= s['src'][1] + 0.01 and s['speed'] == 1:
            return round(s['t0'] + (src_t - s['src'][0]), 2)
    raise ValueError(src_t)


# ---------- Captions: what is said in the footage, timed on its soundtrack (source seconds) ----------
SPOKEN = [
    (0.46, 2.15, 'شو عم ترسم يا بابا؟'),
    (2.45, 4.03, 'بيتنا بسوريا.'),
    (6.27, 7.84, 'بس نحنا ما عنا بيت بسوريا!'),
    (8.90, 9.75, 'بعرف بابا…'),
    (11.26, 15.28, 'بس إنت مو كل سنة بتقلنا إنو رح يصير عنا بيت ونرجع؟'),
    (21.88, 25.64, 'السلام عليكم، بدي اسأل عن الشقق بحريتان.'),
    (26.20, 28.82, 'وعليكم السلام، أهلاً وسهلاً فيك.'),
    (30.26, 31.48, 'خليني فرجيك المشروع.'),
    (32.00, 35.16, 'نحنا بشركة الحسن مو بس عم نبني شقق…'),
    (35.45, 38.50, 'عم نساعد أهلنا يحققوا حلم الرجعة.'),
]
CAPS, SPEECH = [], []
for sa, sb, text in SPOKEN:
    a, b = out(sa), out(sb)
    CAPS.append({'a': round(a - .15, 2), 'b': round(b + .35, 2), 'sa': a, 'sb': b, 'src': [sa, sb], 'text': text, 'long': len(text) > 40})
    SPEECH.append([a, b])
# A line that starts just before its shot (J-cut) shows its caption from the cut
for c in CAPS:
    for g in CUT:
        if g['type'] == 'clip' and g['speed'] == 1 and g['t0'] - .6 < c['a'] < g['t0']:
            c['a'] = g['t0']
# Captions never overlap: the earlier one gives way
for c, n in zip(CAPS, CAPS[1:]):
    c['b'] = min(c['b'], round(n['a'] - .03, 2))

# ---------- Narrator lines (clean recordings) ----------
vo8 = round(SEG['drawing']['t0'] + .2, 2)
vo9 = round(SEG['brand']['t0'] + .75, 2)
VOICE = [{'n': 8, 'at': vo8, 'dur': L[8]['dur']}, {'n': 9, 'at': vo9, 'dur': L[9]['dur']}]
SPEECH += [[vo8, vo8 + L[8]['dur']], [vo9, vo9 + L[9]['dur']]]

b0, ph = SEG['brand']['t0'], SEG['phone']['t0']
CUES = {
    'vo1': round(vo8 - .1, 2), 'vo2': round(vo8 + L[8]['part2'] - .1, 2), 'voEnd': round(vo8 + L[8]['dur'] + .35, 2),
    'brand': round(vo9 + .35, 2), 'slogan': round(vo9 + L[9]['slogan'] - .1, 2), 'contact': round(vo9 + L[9]['last'] + .05, 2),
    'tap': round(ph + 3.0, 2), 'zoom': round(ph + 3.5, 2),
}
# Stage titles over the construction shots
LABELS = [{'a': s['t0'], 'b': s['t1'], 'text': s['label']} for s in CUT if s.get('label')]

# ---------- Audio plan ----------
# The footage soundtrack is used where people speak on camera; everything else is score + narrator.
call = SEG['call']
SRC_AUDIO = [
    {'src0': 0.0, 'src1': 15.29, 'at': 0.0},
    {'src0': 21.75, 'src1': 38.62, 'at': round(call['t0'] - (call['src'][0] - 21.75), 3)},
]
# Score sections (same keys the score script uses)
T = {'s1': 0.0, 's2': 4.4, 's3': 8.4, 's4': SEG['react']['t0'], 's5': call['t0'], 's6': SEG['office']['t0'], 's7': SEG['site']['t0'],
     's8': SEG['rebar']['t0'], 's9': SEG['child']['t0'], 's10': SEG['drawing']['t0'], 's11': b0, 'end': END}

AD = {
    'fps': 24, 'duration': END, 'plates': '../build/plates/p_', 'srcFps': SRC_FPS, 'srcFrames': SRC_FRAMES,
    'segs': CUT, 'caps': CAPS, 'labels': LABELS, 'cues': CUES, 'site': marks, 'brand': BRAND, 'texts': NARRATION,
    'T': T, 'LEAD7': 0.0, 'LAND': 1.5, 'SFXT': {'phone_in': ph, 'tap': CUES['tap'], 'zoom': CUES['zoom']},
    'VOICE': VOICE, 'SRC_AUDIO': SRC_AUDIO, 'SPEECH': SPEECH,
}
open(sys.argv[3], 'w', encoding='utf-8').write('window.AD = ' + json.dumps(AD, ensure_ascii=False, indent=1) + ';\n')
print('duration', END)
for s in CUT:
    print(f"{s['id']:9s} {s['t0']:6.2f}-{s['t1']:6.2f}  ({s['dur']:.2f}s)")
print('cues', CUES)
