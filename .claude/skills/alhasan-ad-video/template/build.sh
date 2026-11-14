#!/usr/bin/env bash
# Builds an ad. Usage: [FOOTAGE=path.mp4] [REFRESH_SITE=1] ./build.sh hybrid|illustrated [output.mp4]
#   hybrid      - footage + graphics; the edit is defined in src/edit.py
#   illustrated - fully drawn, faceless version, timed by src/retime.py
#   REFRESH_SITE=1 re-captures the company site for the phone scene (otherwise the saved capture is used)
set -euo pipefail
cd "$(dirname "$0")"
MODE="${1:-hybrid}"
OUT="${2:-out/alhasan-ad-$MODE.mp4}"
FOOTAGE="${FOOTAGE:-assets/ref/user-cut.mp4}"
mkdir -p out build

# Voice lines cut from the recordings (once per set of recordings)
[ -f build/voice/lines.json ] || python3 src/voice.py assets/voice build/voice

if [ "$MODE" = hybrid ]; then
  PAGE=film_hybrid.html; CFG=src/ad.js
  [ "${REFRESH_SITE:-0}" = 1 ] && node src/site_shot.mjs https://alhasan-ec.com/ assets/site
  # Footage frames, scaled to 1080x1920 (redone only when the footage file changes), and the edit plan
  STAMP="$(stat -c '%n %s %Y' "$FOOTAGE")"
  if [ "$(cat build/plates/.src 2>/dev/null)" != "$STAMP" ]; then
    rm -rf build/plates; mkdir -p build/plates
    ffmpeg -hide_banner -loglevel error -i "$FOOTAGE" -vf "hqdn3d=1.5:1.5:3:3,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,unsharp=7:7:0.7" -q:v 3 build/plates/p_%05d.jpg
    echo "$STAMP" > build/plates/.src
  fi
  python3 src/edit.py build/voice/lines.json assets/site/marks.json "$CFG" "$FOOTAGE" > /dev/null
  FPS=$(python3 -c "import json,re;print(json.loads(re.sub(r'^[^{]*','',open('$CFG',encoding='utf-8').read()).strip().rstrip(';'))['fps'])")
  EXTRA="$FOOTAGE"
else
  PAGE=film_illustrated.html; CFG=src/timeline.js; FPS=30; EXTRA=""
  python3 src/retime.py build/voice/lines.json "$CFG" > /dev/null
fi

# Score, then voices on top, then master to -14 LUFS with a peak limiter
python3 src/music.py "$CFG" build/music.wav
python3 src/mix.py "$CFG" build/music.wav build/voice build/mix.wav $EXTRA
I=$(ffmpeg -hide_banner -nostats -i build/mix.wav -af ebur128 -f null - 2>&1 | awk '/I:/{v=$2} END{print v}')
G=$(python3 -c "print(round(-14-($I),2))")
ffmpeg -hide_banner -loglevel error -y -i build/mix.wav -af "volume=${G}dB,alimiter=limit=0.84:attack=4:release=80:level=false" build/master.wav
echo "master gain ${G} dB"

# Frames (4 parallel workers), then encode
rm -rf build/frames
for w in 0 1 2 3; do node src/render.mjs "$PAGE" build/frames "$w" 4 & done
wait
ffmpeg -hide_banner -loglevel error -y -framerate "$FPS" -i build/frames/f_%05d.jpg -i build/master.wav \
  -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of compact "$OUT"
