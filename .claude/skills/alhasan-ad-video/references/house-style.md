# House style, with reasons

## Brand

- **Company:** شركة الحسن للهندسة والبناء. Slogan: من أرض المشروع… منبني الثقة.
- **Logo:** `assets/logo.png`, the gold calligraphy isolated from the image the owner supplied, shown on
  near-black. If the owner sends a transparent PNG or SVG of the logo, replace the file (same name); it will
  be cleaner than the extraction. `src/extract_logo.py` repeats the extraction from a new source image.
- **Colours:** navy `#0B1730` (the owner's suits and site gear are navy), gold `#E3BE5A` to `#F3D98B` to
  match the logo, near-black `#030303` for the brand card, warm white for text.
- **Fonts:** Tajawal for captions, titles and numbers (close to the logo's own tagline lettering);
  Amiri bold for the narrator's lines, because a classical naskh carries weight; Playpen Sans Arabic for a
  child's handwriting in the illustrated film.
- **Number:** `+963 947 728 079` with the flag, then `من داخل سوريا: 0947 728 079`. The flag is drawn in
  the page (green, white, black, three red stars) because emoji fonts still ship the old flag.
- **Website:** `alhasan-ec.com`, on the brand card and in the phone's address bar. The phone scene scrolls
  a capture of the real projects page; `REFRESH_SITE=1` takes a fresh one.

## Picture

- 1080x1920. Captions sit in the lower third above the platform UI zone; titles and narrator lines sit
  below the top 220 px.
- Captions: white Tajawal 700 with a soft shadow over a bottom gradient, revealed word by word with the
  voice. One or two lines; long lines switch to a smaller size automatically (`long`).
- Over footage, no speaker labels: the viewer sees who is talking. The illustrated film has nobody on
  screen, so it labels each speaker.
- Stage titles over construction shots: a small gold counter, a large white title, a progress bar.
- Transitions between footage shots are plain cuts. Dissolves are kept for the move from footage to the
  gold finale and from the finale to the brand card.

## Sound

- Voices are levelled to the same loudness, lightly compressed, and placed centre.
- The score is synthesized in `src/music.py`: a quiet motif in D minor for the opening, darker under the
  father's line, a pulse when he decides, then F major from the site onward, resolving as the logo lands.
  It is deliberately simple; it has to sit under speech on a phone speaker.
- In the illustrated film the owner's reply during the call is band-limited to sound like a phone speaker.
  In the hybrid cut he is on camera, so his voice stays full.
- Master: -14 LUFS integrated, limiter ceiling about -1.5 dBFS.

## Honesty in the ad

- The disclaimer "مشاهد توضيحية بالذكاء الاصطناعي" stays on AI-made scenes that could be read as the real
  project. Footage the user generated may already carry its own; do not stack a second one on it.
- A real person's likeness (the owner) appears only in footage the user supplies. Do not generate it.
- Do not invent prices, delivery dates or availability. The only place such figures appear is the capture
  of the company's own site.
