# Galahad meme pack

Twelve square (1080×1080) meme composites for X / Discord. Caption **set A** is the default filename; set **B** is the `_b` alt.

## Look unchanged (Ryan 2026-09-18)

Do **not** regenerate, redraw, restyle, recolor, upscale-with-AI, or “improve” Galahad’s face, armor, crest, or Mark. Do **not** invent new sprites, emotes, or art styles.

This folder is **composites only**: existing PNGs + text captions + simple layout chrome (navy panels, arrows, labels). Pixel art is resized nearest-neighbor. Background is navy `#0b1220`.

## Source assets (repo paths — do not invent)

| Use | Path |
|---|---|
| Discord emotes | `assets/discord-emojis/galahad_*.png` (Ryan sheet, 128×128) |
| Reaction stills | `assets/reactions/frames/{hold_the_line,walk_away,victory_crest}/` (same art as the GIFs) |
| Mark crop / block pose | `assets/roman_legionary/frames_96/cast_2.png`, `block_2.png` |

GIF binaries under `assets/gifs/reactions/` are a fallback if a reaction PNG is missing. Do not open those GIFs in vision/`read_file` tools.

## Rebuild

```bash
python3 -m pip install Pillow
python3 scripts/make-galahad-memes.py
```

Writes `meme_01_drake.png` … `meme_12_walkoff.png` plus `_b` alts and regenerates `index.html`.

```bash
python3 scripts/make-galahad-memes.py --set a   # defaults only
```

Gallery: [https://animayer.github.io/Galahad/assets/memes/](https://animayer.github.io/Galahad/assets/memes/)

## Formats

1. Drake — thumbs down / thumbs up (B uses hold-the-line still)
2. Distracted boyfriend — rage / grin / smug (oath triangle)
3. This is fine — meditating or drinking on exploding tiles
4. Expanding brain — confused → reading → praying → smug
5. Woman yelling / cat — rage vs shrug or facepalm
6. Waiting — trapped or ghostly
7. Change my mind — sunglasses or smug + Mark crop
8. Understatement punch — exploding → grin or victory crest
9. Trade offer — thumbs up vs cheering or block
10. Bus guy — scared or shocked + bible thought line
11. Is this a pigeon — confused/clown vs rage (anti shiny AU)
12. Walk of shame — theatre mask + walk-away still
