# The hybrid edit (`src/edit.py`)

`edit.py` is the one file to change for a new footage-based ad. It writes `src/ad.js`, which the film page
(`film_hybrid.html`), the score (`music.py`) and the mixer (`mix.py`) all read. Four tables at its top:

## BRAND

Name, slogan, international and local phone number, website. Shown on the brand card and in the phone's
address bar. Change only when the user gives new details.

## NARRATION

The narrator's closing line in two phrases, as HTML: `vo1` is laid over the last footage shot, `vo2` over
the gold finale. `<br>` breaks the line; `<b>` turns words gold and larger. Keep each phrase to two short
lines so it reads in under three seconds.

## CUT

The edit, in order. Each entry is one of:

| type | fields | meaning |
|---|---|---|
| `clip` | `src=(in, out)` seconds of the footage, `speed`, optional `label` | A stretch of footage. `label` puts a stage title over it (used for construction shots; the counter "01 / 04" follows the number of labelled clips). |
| `phone` | `dur`, `freeze` | The phone insert with the real website, over a blurred frame of the footage taken at `freeze` seconds. It slides in, scrolls from the hero to the first project, taps "عرض المشروع", zooms. |
| `finale` | `dur`, `freeze` | Dissolve from the frozen footage frame to the gold house; the building rises behind it and its windows light up. |
| `brand` | `dur` | The brand card. Needs about 9.5 s: logo, the narrator's last line, then at least four seconds on the phone number. |

Segment ids `dialog`, `react`, `call`, `office`, `site`, `drawing`, `brand`, `phone` and the first labelled
clip are referenced further down the file for the score sections (`T`) and the narrator timing. When the
structure of a new ad differs, update those references together with `CUT`.

Cut on the scene changes that `look.py` prints. A clip may start or end mid-shot, but a jump inside one
continuous camera move shows as a glitch: either keep the move whole or change speed across it.

## SPOKEN

`(start, end, text)` for every line spoken on camera, in footage seconds. Take the times from the sound
intervals `look.py` prints, refined with the word times from `transcribe.py`. The text is the script's
spelling of what is actually said. The page reveals the words across the interval, so a wrong end time
makes the caption run ahead of or behind the voice.

## Narrator recordings (`src/voice.py`)

`PLAN` maps each recording to the lines it holds with rough windows (from `transcribe.py`), and `marks`
give rough positions inside a line where the on-screen phrase changes. `voice.py` finds the exact cut in
the quietest moment near each window, trims, levels, and writes `build/voice/L<n>.wav` plus `lines.json`.
The hybrid edit uses lines 8 (the narrator's closing line, mark `part2`) and 9 (the brand line, marks
`slogan` and `last`). Delete `build/voice/` after changing recordings so the build cuts them again.

## Sound in the hybrid cut

- `SRC_AUDIO` lists the stretches of the footage soundtrack to keep, each with the output time it lands on.
  They must cover the lip-synced shots and nothing with baked-in music.
- `SPEECH` (filled automatically) is every interval with a voice; the score ducks under these.
- `T` names the score sections: opening motif, the father's line, the child's question, decision, call,
  reply, on site, build, back to the child, narrator, brand. The score adapts its bar count to each
  section's length, so only the boundaries matter.
- `SFXT` places the three effects of the phone insert.

## When the footage has a different story

The pipeline does not care what the footage shows. Keep the order that makes this format work:
people and feeling first, the website as the way in, the owner or the site as proof, construction as
progress, a closing image under the narrator, then the brand card. Drop the segment types the story does
not need; a cut with only `clip` and `brand` segments is valid as long as the `T` references are updated.
