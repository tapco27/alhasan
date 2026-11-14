# Builds timeline.js from the measured voice lines: scene lengths, captions, on-screen cues, voice placement.
# Usage: retime.py <lines.json> <timeline.js>
import json, sys

L = {int(k): v for k, v in json.load(open(sys.argv[1])).items()}
d = lambda n: L[n]['dur']
T, CAPS, VOICE = {}, [], []


def say(n, at):
    VOICE.append({'n': n, 'at': round(at, 3), 'dur': d(n)})
    return at, at + d(n)


def cap(a, b, who, text, sa=None, sb=None, **extra):
    c = {'a': round(a, 2), 'b': round(b, 2), 'who': who, 'text': text, **extra}
    if sa is not None:
        c.update(sa=round(sa, 2), sb=round(sb, 2))
    CAPS.append(c)


# Scene 1: the drawing takes 8 s; father asks while the walls go up, the child answers over the roof
T['s1'] = 0.0
a, b = say(1, 1.8); cap(a - .2, b + .55, 'father', 'شو عم ترسم يا بابا؟', a, b)
a, b = say(2, 4.7); cap(a - .2, b + .7, 'son', 'بيتنا بسوريا.', a, b)
T['s2'] = 8.0

# Scene 2: the father's answer, then a beat while the house fades
a, b = say(3, T['s2'] + .6); cap(a - .2, b + .7, 'father', 'بس نحنا ما عنا بيت بسوريا!', a, b)
T['s3'] = round(b + 1.65, 2)

# Scene 3: the child's question in two captions, then the father's silence
a, b = say(4, T['s3'] + .5); p2 = a + L[4]['part2']
cap(a - .2, p2 - .1, 'son', 'بعرف بابا…', a, p2 - .5)
cap(p2 - .05, b + .5, 'son', 'بس إنت مو كل سنة بتقلنا إنو رح يصير عنا بيت ونرجع؟', p2, b, long=True)
cap(b + .75, b + 2.75, 'father', '• • •', silent=True)
T['s4'] = round(b + 2.95, 2)

# Scene 4: paper, phone, search (no voice)
T['s5'] = T['s4'] + 8.0

# Scene 5: ringing, connect at +2.0, the father speaks
a, b = say(5, T['s5'] + 2.3); cap(a - .2, b + .35, 'father', 'السلام عليكم، بدي استفسر عن شقق بحريتان.', a, b)
T['s6'] = round(b + .45, 2)

# Scene 6: the owner's reply in two captions
a, b = say(6, T['s6'] + .3); p2 = a + L[6]['part2']
cap(a - .2, p2 - .08, 'co', 'وعليكم السلام، أهلاً وسهلاً فيك.', a, p2 - .3)
cap(p2 - .04, b + .4, 'co', 'أنا صاحب شركة الحسن، وخليني فرجيك المشروع بحريتان.', p2, b)
T['s7'] = round(b + .5, 2)

# Scene 7: on site, the owner's line in two phrases
a, b = say(7, T['s7'] + 1.5)
CUES = {'ow1': round(a - .2, 2), 'ow2': round(a + L[7]['part2'] - .1, 2), 'owEnd': round(max(b + .6, T['s7'] + 7.6), 2)}
T['s8'] = round(max(T['s7'] + 8.0, b + 1.0), 2)

# Scenes 8 and 9: build stages and the door (no voice)
T['s9'] = T['s8'] + 11.0
T['s10'] = T['s9'] + 9.0

# Scene 10: the narrator in two phrases
a, b = say(8, T['s10'] + .9)
CUES.update(vo1=round(a - .2, 2), vo2=round(a + L[8]['part2'] - .1, 2), voEnd=round(max(b + .6, T['s10'] + 7.4), 2))
T['s11'] = round(max(T['s10'] + 8.0, b + 1.2), 2)

# Scene 11: logo, name and slogan with the voice, then the contact block and a hold on the number
a, b = say(9, T['s11'] + 1.1)
CUES.update(brand=round(a + .5, 2), slogan=round(a + L[9]['slogan'] - .1, 2), contact=round(a + L[9]['last'] + .1, 2))
T['end'] = round(CUES['contact'] + 1.3 + 4.6, 2)

body = json.dumps({'T': T, 'CUES': CUES, 'CAPS': CAPS, 'VOICE': VOICE}, ensure_ascii=False, indent=1)
open(sys.argv[2], 'w', encoding='utf-8').write('window.TL = ' + body + ';\n')
print('T', T); print('CUES', CUES)
