# Roman Legionary — Grok Build Sprite Pack

Processed from a Gemini concept sheet into **transparent PNGs**, **equal-size animation strips**, a **TexturePacker-style atlas**, and a drop-in preview.

Character: helmeted legionary, red cape, round shield, spear. Pixel-art, 4-dir locomotion + attack / hurt / death.

## Drop this into Grok Build

Point Grok Build at this folder and say something like:

> Use `roman_legionary/` as the player sprite. Load `animations.json` and the frames in `frames_normalized/` (or the 96px set). Idle/walk 4 directions, space to attack, death on 0 HP. Anchor sprites at bottom-center.

Recommended default size for a browser game: **`frames_96/`** (96px tall).  
Hi-res source: **`frames_normalized/`** (344×320 canvas, feet planted).

## Folder map

| Path | What it is |
|---|---|
| `frames/` | Tight-cropped transparent PNGs (native extracted size) |
| `frames_normalized/` | Same frames padded onto a shared canvas, **feet aligned** |
| `frames_96/` | Nearest-neighbor scale to 96px tall — best for Grok Build / Phaser |
| `frames_64/` | 64px tall set |
| `strips/` | Horizontal strips, one PNG per animation, equal frame width |
| `atlas.png` + `atlas.json` | Packed sheet, TexturePacker/Phaser hash format |
| `animations.json` | Frame lists, timings, loop flags |
| `preview.html` | Open locally to click-test every animation |
| `preview/*.gif` | Quick look at walk / attack |

## Animations

| Name | Frames | Loop | ms/frame |
|---|---|---|---|
| idle_front / back / left / right | 1 | yes | 400 |
| walk_front / back / left / right | 4 | yes | 120 |
| walk2_front / back / left / right | 8 | yes | 90 |
| run_front / back / left / right | 6 | yes | 80 |
| turn | 4 | yes | 160 |
| attack | 4 (`attack_21`–`24`) | no | 90 |
| thrust | 5 | no | 90 |
| block | 4 | no | 110 |
| cast | 4 | no | 110 |
| kneel | 4 | no | 130 |
| wave | 6 | yes | 130 |
| jump | 5 | no | 100 |
| cheer | 5 | yes | 120 |
| hurt | 2 | no | 140 |
| death | 3 | no | 160 |
| corpse | 2 | yes | 800 |

Extras (not in the body strips):

- `projectile_spear` — thrown spear VFX
- `dust_front_*` / `dust_back_*` — foot-dust particles under the walk cycle
- `attack_back` — rear-view attack pose if you need it

## How to load in a Grok Build canvas game

Strips are the simplest. Each strip is `N` frames of `frame_w × frame_h`:

```js
const spec = {
  walk_front: { src: 'strips/walk_front.png', frames: 4, fw: 344, fh: 320, ms: 120, loop: true },
  attack:     { src: 'strips/attack.png',     frames: 4, fw: 344, fh: 320, ms: 90,  loop: false },
};

function drawFrame(ctx, img, spec, index, x, y, scale = 0.3) {
  const i = index % spec.frames;
  const dw = spec.fw * scale, dh = spec.fh * scale;
  ctx.drawImage(img, i * spec.fw, 0, spec.fw, spec.fh, x - dw / 2, y - dh, dw, dh);
}
```

Anchor is **bottom-center** (`x = feet, y = feet`). That keeps the body planted while frame widths differ.

## Notes / limits of the source sheet

- Walk cycles are 4 frames and fairly close together — Gemini drew a reference sheet, not a production cycle. Fine for a prototype; swap later if you want more smear.
- Side-walk left/right are distinct drawings, not a flip. Don't mirror them or the shield/spear will swap hands.
- Attack is a thrust / throw. `projectile_spear` is the airborne spear.
- `thrust` is a **front-facing** jab (teal spear, different silhouette from `attack_21`–`24`).
- `walk2_*` keeps the original four walk names and inserts authored in-betweens. Prefer it when you want smoother GIF / later Hold the Line motion.
- New expanded frames are **transparent** 103×96 PNGs. Spec: `animations_expanded.json`. Rebuild: `python3 scripts/make-expanded-gifs.py --author`.
- Original sheet numbers (21–30) were punched out of the frames.

## License / source

You generated the source image. This pack is a mechanical slice + chroma key of that image. Use it in your own Grok Build project.
