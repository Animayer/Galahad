# Galahad GIF pack

Canon legionary clips as GIFs. Rebuilt from `assets/roman_legionary/frames_96/` using the frame lists, timings, and loop flags in `assets/roman_legionary/animations.json`. No new art. Left/right walks are distinct drawings — do not mirror them.

## Background

**Dark navy `#0b1220`** (opaque). GIF only has 1-bit transparency, which fringes anti-aliased pixel edges, so each PNG is composited onto navy before palettizing. No resize, no dither.

## Rebuild

```bash
python3 -m pip install Pillow
python3 scripts/make-gifs.py
```

The script refuses to resample or flip frames. Missing canon PNGs fail the build.

## Files

| GIF | Frames | ms/frame | Loop |
|---|---|---|---|
| `idle_front.gif` | 1 (`idle_front`) | 400 | yes |
| `idle_back.gif` | 1 (`idle_back`) | 400 | yes |
| `idle_left.gif` | 1 (`idle_left`) | 400 | yes |
| `idle_right.gif` | 1 (`idle_right`) | 400 | yes |
| `walk_front.gif` | 4 | 120 | yes |
| `walk_back.gif` | 4 | 120 | yes |
| `walk_left.gif` | 4 | 120 | yes |
| `walk_right.gif` | 4 | 120 | yes |
| `attack.gif` | 4 (`attack_21`–`24`) | 90 | no |
| `hurt.gif` | 2 (`hurt_25`–`26`) | 140 | no |
| `death.gif` | 3 (`death_27`, `death_28`, `corpse_29`) | 160 | no |
| `corpse.gif` | 2 (`corpse_29`–`30`) | 800 | yes |

Canvas is the 96px-tall pack (103×96). Target size is well under 200 KB each.

Expanded motion clips (`walk2_*`, `run_*`, `turn`, `block`, `thrust`, `cast`, `kneel`, `wave`, `jump`, `cheer`) are listed in `assets/roman_legionary/animations_expanded.json` and written into this folder by `scripts/make-gifs.py` (merged spec) or `scripts/make-expanded-gifs.py`. Canon `walk_*` GIFs stay 4 frames.

### Frame counts (quality pass)

| GIF | Before | After |
|---|---|---|
| `walk_front/back/left/right.gif` | 4f (chroma holes) | 4f, hole-filled PNGs |
| `walk2_front/back/left/right.gif` | 8f listed, ~4 readable (waist gaps on in-betweens) | **8 distinct** connected poses |
| `run_front/back/left/right.gif` | 6f listed, ~4 readable (torso/leg punch) | **6 distinct** connected poses |
| `attack.gif` | 4f | 4f, hole-filled |
| `thrust.gif` | 5f, feet clipped | 5f, feet planted |
| `jump.gif` | 5f, crest/feet clipped | 5f, crest on-canvas |
| `block.gif` | 4f, hip holes | 4f, hip filled, feet planted |

Pillow `n_frames` for walk2/run did not change; the missing poses were torn in-betweens, not omitted files. Left/right are not mirrors.

128×128 looping showcase versions of the new actions also live in [`reactions/`](reactions/).

Non-looping clips (`attack`, `hurt`, `death`, `block`, `thrust`, `cast`, `kneel`, `jump`) write Netscape loop count `1` (play once, then hold in viewers that honor it). Looping clips use `0` (infinite).
