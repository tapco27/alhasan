---
name: alhasan-ad-video
description: Makes vertical 9:16 video ads for شركة الحسن للهندسة والبناء (Al-Hasan Engineering & Construction, alhasan-ec.com) in its house style - the user's footage or a fully drawn faceless film, word-timed Arabic captions, the real company website inside a phone, construction stage titles, the gold-logo end card with the Syrian phone number and website, a synthesized score, and a -14 LUFS mix, rendered to a 1080x1920 MP4. Use this whenever the user asks for an Al-Hasan ad, reel, promo or "فيديو إعلاني / إعلان للحسن / قالب الحسن / فيديو للشركة", sends footage, a voice-over or a script for one, or wants an existing Al-Hasan ad re-cut, shortened, re-timed or updated (new number, new project, new line), even if they do not mention the template.
---

# Al-Hasan ad video

A working project template that turns a script, voice recordings and (optionally) footage into a finished
vertical ad. Everything is rendered from code: a web page draws each frame, Playwright captures it, ffmpeg
encodes it, and Python synthesizes the music and mixes the sound. Nothing needs an API key.

The template lives in `template/`. It already contains the first ad made with it ("حلم الرجعة") as the worked
example: its script, voice recordings and edit plan are what the scripts currently hold.

## Two modes

| Mode | When | What it looks like | Per-ad file |
|---|---|---|---|
| `hybrid` | The user has footage (usually AI-generated characters) | Their footage with captions, the real website in a phone, stage titles over construction shots, a gold house-to-building finale, the brand card | `src/edit.py` |
| `illustrated` | No footage, or the user wants nobody on screen | A fully drawn film: a child's crayon drawing, a phone, a blueprint that becomes a building, the brand card | `src/retime.py` |

Prefer `hybrid` when footage exists: real-looking people carry the emotion, and the graphics carry the
information and the brand. The illustrated scenes were drawn for the "حلم الرجعة" story; a different story
needs its scenes redrawn in `film_illustrated.html`, so say that plainly before promising it.

## Start

1. Copy `template/` to a working folder the user can open, then inside it run `npm install` (fonts).
2. Check the tools: `ffmpeg`, `python3` with `numpy` and `pillow`, and Node with Playwright
   (`node -e "require('playwright')"`). For transcription, `pip install faster-whisper` (the model downloads
   from Hugging Face on first use; if that is blocked, work from the script text and the loudness envelope).
3. Find out what the user has: the script, footage, voice recordings. Ask for original footage files.
   A clip that went through WhatsApp arrives at 480x854 and looks soft next to the sharp graphics.
4. Put footage at `assets/ref/user-cut.mp4` (or pass `FOOTAGE=path`), voice recordings in `assets/voice/`.

## Building

```bash
./build.sh hybrid out/ad.mp4          # footage + graphics, 24 fps (or the footage's rate)
./build.sh illustrated out/ad.mp4     # drawn version, 30 fps
REFRESH_SITE=1 ./build.sh hybrid      # also re-capture alhasan-ec.com for the phone scene
```

A full build takes two to five minutes. Before one, render a handful of stills and look at them; it is the
fastest way to catch a layout or timing mistake:

```bash
node src/render.mjs film_hybrid.html --stills build/seq 2,19.8,33,45.5,49,58
python3 src/sheet.py build/seq build/sheet.jpg 6      # then read build/sheet.jpg
```

(The pages read `src/ad.js` or `src/timeline.js`, which the build writes. For stills before the first build,
run `src/edit.py` or `src/retime.py` by hand with the arguments shown in `build.sh`.)

## A new hybrid ad

Read `references/hybrid-edit.md` for the fields. The work, in order:

1. **Look at the footage.** `python3 src/look.py <footage> build/look` writes a contact sheet (one frame
   per second), and prints the scene cuts, where sound occurs, and how loud the gaps are. Read the sheet.
2. **Transcribe it.** `python3 src/transcribe.py turbo build/words.json <footage-audio.wav>` gives word
   times. Captions must say what is actually spoken in the footage, which often differs from the script
   by a word or two.
3. **Cut the narrator recordings into lines** with `src/voice.py` (its `PLAN` table maps files to lines).
4. **Write the edit** in `src/edit.py`: `BRAND`, `NARRATION`, `CUT`, `SPOKEN`.
5. Build, review stills, run `python3 src/verify.py src/ad.js <footage> <final.mp4>`, deliver.

How to cut, and why:

- **Lip-synced shots play at speed 1 with their own sound.** Speeding or re-voicing them breaks the match
  between mouth and voice, which viewers notice instantly.
- **Silent shots run faster** (1.25x to 2x) or get trimmed. The user asked for less time without a voice;
  a silent beat longer than about two seconds should earn its place. Do not speed up a face reacting:
  trim it instead, because sped-up expressions look comic.
- **Use the footage soundtrack only where it is clean.** `look.py` shows the level of each gap: near
  -50 dBFS means clean dialogue; -25 to -35 dBFS means music or effects are baked in, and that stretch
  must take its sound from the separate recordings and the score instead, or two pieces of music collide.
- **Replace any AI-drawn phone or app screen with the phone insert**, which shows the real site.
- **A line that starts just before its shot** (a J-cut) is fine; `edit.py` holds its caption until the cut.

## House style

Details and reasons are in `references/house-style.md`. The essentials:

- 1080x1920. Keep text out of the top 220 px and the bottom 340 px, where Reels and TikTok put their UI.
- Arabic text on screen is always typeset in the page (Tajawal, Amiri for the narrator), never taken from
  AI video, which garbles Arabic letters.
- Brand card: gold logo on black, company name, slogan, "للاستفسار والتواصل", the number in international
  form `+963 947 728 079` beside the current Syrian flag (green, white, black, three red stars), the
  website, and the local form of the number. The audience is largely abroad, so the international form leads.
- AI-made scenes of the project carry "مشاهد توضيحية بالذكاء الاصطناعي", so nobody takes them for the real building.
- The phone scene shows the live site, prices included. Mention this to the user, since a saved ad keeps
  showing the prices of the day it was captured.
- Sound: voices lead, the score ducks about 10 dB under speech, the master sits at -14 LUFS with peaks
  under -1 dBFS.

## Checking work you cannot see or hear

You can read still frames but you cannot listen. Verify with measurements and say which is which:

- `verify.py` reports, per spoken caption, how far the sound sits from its picture. More than one frame
  is a real lip-sync error.
- Transcribe the final file's audio; every line should come back at its planned time. Whisper invents a
  closing phrase such as "اشتركوا في القناة" over music-only endings; that is not in the audio.
- `bands.py` shows the score's frequency balance per section. Most energy should sit between 150 Hz and
  2 kHz, or the music vanishes on phone speakers.
- Tell the user what you measured and what only their ears can judge: the music itself, and any word the
  transcriber stumbled on.

## Delivering

Send the MP4 as a file. Reply in the user's language (they write Syrian Arabic), briefly: what changed,
what was verified, what they should listen for. If the session is temporary, tell them to download it.

## Lessons already paid for

- A script named after a Python standard module (`inspect.py`, `json.py`) silently breaks `numpy` imports
  for every other script in the folder.
- In an `.mjs` file, load Playwright with `createRequire(import.meta.url)('playwright')`; a plain `import`
  does not find the globally installed copy.
- SVG draw-on animation (`pathLength` + dash offset) breaks under `vector-effect: non-scaling-stroke`;
  scale the stroke width by hand instead.
- The film pages must be pure functions of time (`renderAt(t)`), with no CSS animations or timers, because
  four workers render interleaved frames.
- The site's lazy images only load when scrolled into view; `site_shot.mjs` scrolls the page first.
