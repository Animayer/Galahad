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

Non-looping clips (`attack`, `hurt`, `death`) write Netscape loop count `1` (play once, then hold in viewers that honor it). Looping clips use `0` (infinite).
