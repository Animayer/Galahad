# Galahad reaction GIF pack

Short looping reaction GIFs for Discord / X, authored from Ryan Mayer’s canon legionary sprites (`assets/roman_legionary/frames_96/`) plus original pixel overlays in the same teal / red / magenta palette.

**Not** ripped or traced from copyrighted meme GIFs. The beats are the usual reaction tropes (nod, shrug, facepalm, walk-off); the art is 100% Galahad.

Source animation PNGs live in [`assets/reactions/frames/`](../../reactions/frames/). Rebuild:

```bash
python3 -m pip install Pillow
python3 scripts/make-reaction-gifs.py --author   # regenerate PNGs from canon, then GIFs
python3 scripts/make-reaction-gifs.py            # GIFs from committed PNGs only
```

## Background

Opaque dark navy **`#0b1220`**, same as [`assets/gifs/`](../). 128×128 canvas, nearest-neighbor composites, shared palette, no dither. Target size is well under 200 KB each.

Do not mirror left/right walk frames. `walk_away.gif` turns with `idle_right` (a distinct drawing) then uses `walk_right_*` off-stage.

Pillow may coalesce consecutive identical hold frames when writing the GIF; the PNG folders are the source of truth for pose counts. Timings below are the authored per-PNG durations (ms). All clips loop.

## Files

| GIF | Beat | PNG frames | ms/frame | Suggested caption |
|---|---|---|---|---|
| `agree_nod.gif` | Slow approving nod (crest dips) | 8 | 180, 160, 160, 280, 220, 160, 160, 200 | Aye. |
| `disagree_shake.gif` | Head / crest shake “no” | 10 | 90 × 8, then 110, 140 | That's a no from the cohort. |
| `shrug.gif` | “Not my cohort” tilt + palms | 6 | 160, 140, 320, 280, 160, 180 | Not my cohort. |
| `facepalm.gif` | Helm visor facepalm | 6 | 140, 120, 140, 360, 280, 200 | The line, and my patience. |
| `salute_yes.gif` | Spear present-arms + nod | 6 | 140, 120, 140, 300, 160, 180 | Affirmative. |
| `point_you.gif` | Pointing / calling someone out | 6 | 140, 120, 280, 220, 160, 180 | You. Step forward. |
| `victory_crest.gif` | Spear high, “the line held” | 6 | 120, 100, 280, 180, 160, 200 | The line held. |
| `confused.gif` | Puzzled helmet tilt | 6 | 180, 160, 280, 220, 180, 200 | …orders? |
| `slow_clap.gif` | Slow gauntlet clap | 6 | 220, 220, 340, 220, 220, 260 | Well fought. Eventually. |
| `walk_away.gif` | Turns, walks off stage right | 8 | 220, 140, 140, 120, 120, 120, 120, 160 | We're done here. |
| `shocked.gif` | Recoil + magenta visor flash | 6 | 120, 80, 80, 220, 160, 180 | The line— what. |
| `hold_the_line.gif` | Braced shield. “Hold.” | 6 | 180, 160, 280, 200, 180, 200 | Hold. |

## Expanded action loops (128×128)

Authored with `scripts/make-expanded-gifs.py` from the expanded 96px poses. Same navy canvas as the reaction pack. All of these **loop**. Left/right runs are distinct drawings — not flips.

| GIF | Beat | PNG frames | Notes |
|---|---|---|---|
| `walk2_front.gif` | 8-frame walk | 8 | **8 distinct** connected poses (was ~4 readable) |
| `run_front.gif` | Front dash | 6 | **6 distinct** (was torn torso/leg split) |
| `run_left.gif` | Left dash | 6 | From `walk_left_*`, not a flip |
| `run_right.gif` | Right dash | 6 | From `walk_right_*`, not a flip |
| `block.gif` | Shield up | 4 | Guard |
| `thrust.gif` | Front spear jab | 5 | Not `attack_21–24` |
| `cast.gif` | Magenta visor / Mark | 4 | Portrait lore |
| `jump.gif` | Leap | 5 | Extra hop on this 128 canvas |
| `wave.gif` | Beckon | 6 | Non-combat |
| `kneel.gif` | Brace | 4 | Low stance |
| `cheer.gif` | Spear high hop | 5 | Camp energy |
| `turn.gif` | Pivot | 4 | Canon idles, no mirrored 3/4 |

Rebuild action loops (and the 96px GIFs) with:

```bash
python3 scripts/make-expanded-gifs.py --author
```

