#!/usr/bin/env python3
"""Author expanded Galahad sprite frames and rebuild motion GIFs.

New poses are derived from the canon ``frames_96`` pack (teal lorica,
red crest/cape, spear + round shield). Pixel-crisp translations and
overlays only — no blur, no left/right mirroring.

Transparent 103×96 PNGs land in ``assets/roman_legionary/frames_96/``
and ``assets/sprites/expanded/``. GIFs composite onto opaque navy
``#0b1220`` (GIF 1-bit transparency fringes pixel edges).

Usage:
    python3 scripts/make-expanded-gifs.py --author   # PNGs + GIFs
    python3 scripts/make-expanded-gifs.py            # GIFs from committed PNGs
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow is required. Install with: python3 -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "assets" / "roman_legionary" / "frames_96"
EXPANDED_PNG = ROOT / "assets" / "sprites" / "expanded"
PACK = ROOT / "assets" / "roman_legionary"
EXPANDED_JSON = PACK / "animations_expanded.json"
GIF_DIR = ROOT / "assets" / "gifs"
REACT_DIR = ROOT / "assets" / "gifs" / "reactions"

NAVY = (11, 18, 32, 255)  # #0b1220
CANVAS_96 = (103, 96)
CANVAS_128 = (128, 128)
# Same placement as the reaction pack: 8px floor, 24px headroom.
ORIGIN_128 = ((CANVAS_128[0] - CANVAS_96[0]) // 2, CANVAS_128[1] - CANVAS_96[1] - 8)

ARMOR = (101, 154, 136, 255)
ARMOR_LT = (129, 174, 154, 255)
ARMOR_DK = (70, 120, 121, 255)
MAGENTA = (232, 48, 160, 255)
MAGENTA_LT = (255, 96, 196, 255)
OUTLINE = (10, 18, 30, 255)
WOOD = (186, 118, 86, 255)
WOOD_DK = (132, 78, 58, 255)
SHAFT = (90, 130, 122, 255)
SHAFT_DK = (58, 88, 90, 255)
CREST = (196, 48, 52, 255)
CREST_LT = (232, 86, 78, 255)

GAUNTLET = [
    "  oooo  ",
    " oOOOOo ",
    "oOOOOOOo",
    "oOOOOOOo",
    "oOOOOOOo",
    " oOOOOo ",
    "  oooo  ",
]
PALM = [
    "   oo   ",
    "  oOOo  ",
    " oOOOO  ",
    "oOOOOO  ",
    "oOOOOO  ",
    " oOOOO  ",
    "  oOOo  ",
]
G_COLORS = {"o": ARMOR_DK, "O": ARMOR, "#": ARMOR_LT}


# ---------------------------------------------------------------------------
# Spec: new animation sets. Existing walk_* / attack names stay as they are.
# ---------------------------------------------------------------------------

EXPANDED_ANIMS: dict[str, dict] = {
    "walk2_front": {
        "frames": [
            "walk_front_0",
            "walk2_front_1",
            "walk_front_1",
            "walk2_front_3",
            "walk_front_2",
            "walk2_front_5",
            "walk_front_3",
            "walk2_front_7",
        ],
        "frameDurationMs": 90,
        "loop": True,
        "notes": "8-frame front walk. Even slots reuse canon walk_front_*; odd slots are authored in-betweens.",
    },
    "walk2_back": {
        "frames": [
            "walk_back_0",
            "walk2_back_1",
            "walk_back_1",
            "walk2_back_3",
            "walk_back_2",
            "walk2_back_5",
            "walk_back_3",
            "walk2_back_7",
        ],
        "frameDurationMs": 90,
        "loop": True,
        "notes": "8-frame back walk. Distinct drawings, not a flip of front.",
    },
    "walk2_left": {
        "frames": [
            "walk_left_0",
            "walk2_left_1",
            "walk_left_1",
            "walk2_left_3",
            "walk_left_2",
            "walk2_left_5",
            "walk_left_3",
            "walk2_left_7",
        ],
        "frameDurationMs": 90,
        "loop": True,
        "notes": "8-frame left walk. Authored from walk_left_*; never mirrored from right.",
    },
    "walk2_right": {
        "frames": [
            "walk_right_0",
            "walk2_right_1",
            "walk_right_1",
            "walk2_right_3",
            "walk_right_2",
            "walk2_right_5",
            "walk_right_3",
            "walk2_right_7",
        ],
        "frameDurationMs": 90,
        "loop": True,
        "notes": "8-frame right walk. Authored from walk_right_*; never mirrored from left.",
    },
    "run_front": {
        "frames": [f"run_front_{i}" for i in range(6)],
        "frameDurationMs": 80,
        "loop": True,
        "notes": "Front dash. Wider stride and bob than walk; dust on contact.",
    },
    "run_back": {
        "frames": [f"run_back_{i}" for i in range(6)],
        "frameDurationMs": 80,
        "loop": True,
        "notes": "Back dash from walk_back poses.",
    },
    "run_left": {
        "frames": [f"run_left_{i}" for i in range(6)],
        "frameDurationMs": 80,
        "loop": True,
        "notes": "Left dash. Distinct side drawing — spear/shield hands stay put.",
    },
    "run_right": {
        "frames": [f"run_right_{i}" for i in range(6)],
        "frameDurationMs": 80,
        "loop": True,
        "notes": "Right dash. Distinct side drawing — not a flip of run_left.",
    },
    "turn": {
        "frames": ["idle_front", "idle_right", "idle_back", "idle_left"],
        "frameDurationMs": 160,
        "loop": True,
        "notes": "Pivot using canon idle drawings (front→right→back→left). No mirrored 3/4.",
    },
    "block": {
        "frames": [f"block_{i}" for i in range(4)],
        "frameDurationMs": 110,
        "loop": False,
        "notes": "Front guard. Shield rises to cover chest and visor.",
    },
    "thrust": {
        "frames": [f"thrust_{i}" for i in range(5)],
        "frameDurationMs": 90,
        "loop": False,
        "notes": "Front spear thrust. Different silhouette from attack_21–24 (3/4 side).",
    },
    "cast": {
        "frames": [f"cast_{i}" for i in range(4)],
        "frameDurationMs": 110,
        "loop": False,
        "notes": "Oath flash — magenta visor / Mark glow from the portrait lore.",
    },
    "kneel": {
        "frames": [f"kneel_{i}" for i in range(4)],
        "frameDurationMs": 130,
        "loop": False,
        "notes": "Brace / kneel. Feet planted (bottom-center anchor); torso compresses down.",
    },
    "wave": {
        "frames": [f"wave_{i}" for i in range(6)],
        "frameDurationMs": 130,
        "loop": True,
        "notes": "Beckon. Spear grounded off, gauntlet waves.",
    },
    "jump": {
        "frames": [f"jump_{i}" for i in range(5)],
        "frameDurationMs": 100,
        "loop": False,
        "notes": "Anticipation, tucked air, land. 96px canvas hop is modest; 128 GIF lifts the sprite.",
    },
    "cheer": {
        "frames": [f"cheer_{i}" for i in range(5)],
        "frameDurationMs": 120,
        "loop": True,
        "notes": "Camp energy: hop + spear present-arms.",
    },
}

# 128×128 gallery loops (infinite). Per-frame ms can vary.
SHOWCASE: dict[str, dict] = {
    "walk2_front": {"caption": "Walk 8-frame", "durations": [90] * 8, "hop": None},
    "run_front": {"caption": "Run front", "durations": [80] * 6, "hop": None},
    "run_left": {"caption": "Run left (not a flip)", "durations": [80] * 6, "hop": None},
    "run_right": {"caption": "Run right (not a flip)", "durations": [80] * 6, "hop": None},
    "block": {"caption": "Shield up", "durations": [140, 120, 280, 200], "hop": None},
    "thrust": {"caption": "Front thrust", "durations": [110, 90, 90, 150, 130], "hop": None},
    "cast": {"caption": "Oath flash", "durations": [160, 110, 240, 180], "hop": None},
    "jump": {"caption": "Leap", "durations": [120, 90, 150, 150, 160], "hop": [0, 2, -10, -14, 1]},
    "wave": {"caption": "Beckon", "durations": [140, 120, 140, 140, 140, 180], "hop": None},
    "kneel": {"caption": "Brace", "durations": [140, 140, 280, 200], "hop": None},
    "cheer": {"caption": "The line held", "durations": [120, 100, 200, 160, 140], "hop": [0, 2, -6, -4, 0]},
    "turn": {"caption": "Pivot", "durations": [180, 180, 180, 180], "hop": None},
}


# ---------------------------------------------------------------------------
# Pixel helpers (nearest-neighbor, no resize)
# ---------------------------------------------------------------------------

def load_canon(name: str) -> Image.Image:
    path = CANON / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing canon frame: {path}")
    im = Image.open(path).convert("RGBA")
    if im.size != CANVAS_96:
        # Dust / projectile may differ; pad onto 103×96, feet at bottom.
        canvas = Image.new("RGBA", CANVAS_96, (0, 0, 0, 0))
        x = (CANVAS_96[0] - im.size[0]) // 2
        y = CANVAS_96[1] - im.size[1]
        canvas.alpha_composite(im, (max(0, x), max(0, y)))
        return canvas
    return im


def paste_offset(dst: Image.Image, src: Image.Image, dx: int, dy: int) -> None:
    sw, sh = src.size
    dw, dh = dst.size
    sx0, sy0 = max(0, -dx), max(0, -dy)
    dx0, dy0 = max(0, dx), max(0, dy)
    sx1, sy1 = min(sw, dw - dx0 + sx0), min(sh, dh - dy0 + sy0)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    crop = src.crop((sx0, sy0, sx1, sy1))
    dst.alpha_composite(crop, (dx0, dy0))


def mask_from_pred(im: Image.Image, pred) -> Image.Image:
    w, h = im.size
    mask = Image.new("L", (w, h), 0)
    mp, px = mask.load(), im.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if p[3] > 16 and pred(x, y, p):
                mp[x, y] = 255
    return mask


def layer_from_mask(im: Image.Image, mask: Image.Image) -> Image.Image:
    empty = Image.new("RGBA", im.size, (0, 0, 0, 0))
    return Image.composite(im, empty, mask)


def punch(im: Image.Image, mask: Image.Image) -> Image.Image:
    out = im.copy()
    r, g, b, a = out.split()
    out.putalpha(ImageChops.subtract(a, mask))
    return out


def shift_layer(im: Image.Image, mask: Image.Image, dx: int, dy: int) -> Image.Image:
    layer = layer_from_mask(im, mask)
    body = punch(im, mask)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(body)
    paste_offset(out, layer, dx, dy)
    return out


def legs_mask(im: Image.Image, y0: int = 70) -> Image.Image:
    return mask_from_pred(im, lambda x, y, p: y >= y0)


def torso_mask(im: Image.Image, y1: int = 70) -> Image.Image:
    return mask_from_pred(im, lambda x, y, p: y < y1)


def is_cape_red(p) -> bool:
    r, g, b, a = p
    return a > 16 and r >= 90 and r > g + 15 and r > b + 10


def idle_shield_mask(im: Image.Image) -> Image.Image:
    return mask_from_pred(im, lambda x, y, p: x >= 66 and 46 <= y <= 88)


def idle_spear_mask(im: Image.Image) -> Image.Image:
    def pred(x, y, p):
        if x > 32:
            return False
        if y >= 50 and is_cape_red(p):
            return False
        return True

    return mask_from_pred(im, pred)


def disarm(im: Image.Image) -> Image.Image:
    """Punch the grounded spear. Keep cape reds; also clear anti-aliased shaft dust."""
    out = im.copy()
    px = out.load()
    for y in range(0, min(94, out.size[1])):
        xmax = 30 if y < 54 else 22
        for x in range(0, xmax):
            r, g, b, a = px[x, y]
            if a <= 16:
                continue
            if y >= 52 and is_cape_red((r, g, b, a)):
                continue
            px[x, y] = (0, 0, 0, 0)
    return out


def stamp(im: Image.Image, ox: int, oy: int, rows: list[str], colors: dict) -> None:
    px = im.load()
    w, h = im.size
    filled = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in (" ", "."):
                continue
            color = colors.get(ch)
            if color is None:
                continue
            x, y = ox + i, oy + j
            if 0 <= x < w and 0 <= y < h:
                filled.append((x, y, color))
    occupied = {(x, y) for x, y, _ in filled}
    for x, y, _ in filled:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (nx, ny) not in occupied and 0 <= nx < w and 0 <= ny < h:
                px[nx, ny] = OUTLINE
    for x, y, color in filled:
        px[x, y] = color


def put_px(im: Image.Image, x: int, y: int, color: tuple) -> None:
    if 0 <= x < im.size[0] and 0 <= y < im.size[1]:
        im.putpixel((x, y), color)


def draw_teal_shaft(im: Image.Image, cx: int, y0: int, y1: int) -> None:
    """Canon-matching metal shaft (teal, not brown wood)."""
    lo, hi = (y0, y1) if y0 < y1 else (y1, y0)
    for y in range(lo, hi):
        put_px(im, cx - 2, y, OUTLINE)
        put_px(im, cx - 1, y, SHAFT_DK)
        put_px(im, cx, y, SHAFT)
        put_px(im, cx + 1, y, ARMOR_DK)
        put_px(im, cx + 2, y, OUTLINE)


def draw_teal_head(im: Image.Image, cx: int, cy: int, scale: int = 1) -> None:
    """Diamond spear head. scale 1 = canon-ish, 2 = foreshortened thrust."""
    spreads = [0, 1, 2, 1, 0] if scale <= 1 else [0, 1, 2, 3, 2, 1, 0]
    for i, spread in enumerate(spreads):
        y = cy + i
        col = ARMOR_LT if i in (0, len(spreads) // 2) else ARMOR
        for d in range(-spread, spread + 1):
            put_px(im, cx + d, y, col)
        put_px(im, cx - spread - 1, y, OUTLINE)
        put_px(im, cx + spread + 1, y, OUTLINE)


def draw_vertical_spear(im: Image.Image, cx: int, tip_y: int, fist_y: int, scale: int = 1) -> None:
    draw_teal_head(im, cx, tip_y, scale=scale)
    head_h = 5 if scale <= 1 else 7
    draw_teal_shaft(im, cx, tip_y + head_h, max(tip_y + head_h, fist_y - 3))
    stamp(im, cx - 3, fist_y - 3, GAUNTLET, G_COLORS)


def flash_eyes(im: Image.Image, glow: int = 1) -> Image.Image:
    """Magenta in the visor slit — portrait-lore Mark."""
    out = im.copy()
    px = out.load()
    cores = [
        (49, 31), (50, 31), (51, 31), (52, 31),
        (57, 31), (58, 31), (59, 31), (60, 31),
        (49, 32), (50, 32), (51, 32), (52, 32),
        (57, 32), (58, 32), (59, 32), (60, 32),
        (50, 33), (51, 33), (58, 33), (59, 33),
    ]
    ring = [
        (48, 30), (53, 30), (56, 30), (61, 30),
        (48, 31), (61, 31), (48, 32), (61, 32),
        (49, 34), (60, 34), (50, 30), (59, 30),
    ]
    for x, y in cores:
        if 0 <= x < out.size[0] and 0 <= y < out.size[1] and px[x, y][3] > 16:
            px[x, y] = MAGENTA_LT if glow >= 2 else MAGENTA
    if glow >= 1:
        for x, y in ring:
            if 0 <= x < out.size[0] and 0 <= y < out.size[1] and px[x, y][3] > 16:
                px[x, y] = MAGENTA
    if glow >= 2:
        for x, y in ((74, 62), (75, 62), (74, 63), (76, 60), (78, 64), (72, 58), (80, 66)):
            if 0 <= x < out.size[0] and 0 <= y < out.size[1] and px[x, y][3] > 16:
                px[x, y] = MAGENTA_LT
        # Crest spark.
        for x, y in ((54, 8), (55, 8), (54, 10), (56, 12)):
            if px[x, y][3] > 16:
                px[x, y] = MAGENTA_LT
    return out


def inpaint_holes(body: Image.Image, source: Image.Image, x0: int, y0: int, x1: int, y1: int) -> Image.Image:
    out = body.copy()
    bp, sp = out.load(), source.load()
    w, h = out.size
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            if bp[x, y][3] >= 16:
                continue
            found = None
            for dx in range(1, 14):
                xx = x - dx
                if 0 <= xx < w and sp[xx, y][3] > 180:
                    found = sp[xx, y]
                    break
            if found is None:
                for dy in range(1, 10):
                    yy = min(h - 1, y + dy)
                    if sp[x, yy][3] > 180:
                        found = sp[x, yy]
                        break
            if found is not None:
                bp[x, y] = found
    return out


def composite_dust(im: Image.Image, which: str = "dust_front_1", dy: int = 0) -> Image.Image:
    dust = load_canon(which)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ox = (im.size[0] - dust.size[0]) // 2
    paste_offset(out, dust, ox, dy)
    out.alpha_composite(im)
    return out


def pixel_diff(a: Image.Image, b: Image.Image) -> int:
    pa, pb = a.load(), b.load()
    n = 0
    for y in range(a.size[1]):
        for x in range(a.size[0]):
            if pa[x, y] != pb[x, y]:
                n += 1
    return n


# ---------------------------------------------------------------------------
# Authors
# ---------------------------------------------------------------------------

def inbetween_walk(a: Image.Image, b: Image.Image, bob: int = 1, leg_dx: int = 0) -> Image.Image:
    """Pixel-crisp in-between: a's torso (bobbed) + b's legs. No blending."""
    out = a.copy()
    lm_a = legs_mask(a)
    lm_b = legs_mask(b)
    out = punch(out, lm_a)
    legs = layer_from_mask(b, lm_b)
    paste_offset(out, legs, leg_dx, 0)
    tm = torso_mask(out)
    out = shift_layer(out, tm, 0, bob)
    return out


def author_walk2(direction: str) -> dict[str, Image.Image]:
    frames = [load_canon(f"walk_{direction}_{i}") for i in range(4)]
    # Odd slots: in-betweens. Slight opposite-leg dx so sides don't collapse.
    extra_dx = {"front": 0, "back": 0, "left": -1, "right": 1}[direction]
    pairs = [(0, 1, 1), (1, 2, 0), (2, 3, 1), (3, 0, 0)]
    odd_idx = [1, 3, 5, 7]
    out = {}
    for (ia, ib, bob), name_i in zip(pairs, odd_idx):
        posed = inbetween_walk(frames[ia], frames[ib], bob=bob, leg_dx=extra_dx)
        if pixel_diff(posed, frames[ia]) < 80:
            posed = shift_layer(posed, torso_mask(posed), 0, 1)
        out[f"walk2_{direction}_{name_i}"] = posed
    return out


def author_run(direction: str) -> dict[str, Image.Image]:
    walks = [load_canon(f"walk_{direction}_{i}") for i in range(4)]
    # Sides lean into travel; front/back stay centered so the waist does not tear.
    lean_sign = {"front": 0, "back": 0, "left": -1, "right": 1}[direction]
    # (walk_index, lean, bob, stride, dust?)
    if direction in ("front", "back"):
        keys = [
            (0, 0, 0, 1, True),
            (1, 0, -2, 0, False),
            (2, 0, -3, 0, False),
            (3, 0, 0, -1, True),
            (0, 0, -3, 0, False),
            (1, 0, -1, 1, True),
        ]
    else:
        keys = [
            (0, 1, 0, 2, True),
            (1, 2, -2, 1, False),
            (2, 2, -3, -1, False),
            (3, 1, 0, -2, True),
            (0, 2, -3, 1, False),
            (1, 1, -1, 2, True),
        ]
    dust_name = "dust_back_1" if direction == "back" else "dust_front_1"
    out = {}
    for i, (wi, lean, bob, stride, use_dust) in enumerate(keys):
        im = walks[wi]
        posed = im
        if lean or bob:
            posed = shift_layer(posed, torso_mask(posed, 68), lean_sign * lean, bob)
        if stride:
            posed = shift_layer(posed, legs_mask(posed, 68), lean_sign * stride, 0)
        if use_dust:
            posed = composite_dust(posed, dust_name, dy=2)
        out[f"run_{direction}_{i}"] = posed
    return out


def restore_right_hip(body: Image.Image, idle: Image.Image) -> Image.Image:
    """After the shield leaves the hip, fill holes with greave/tunic — never the old shield."""
    out = body.copy()
    bp, sp = out.load(), idle.load()
    w, h = out.size
    fill = sp[56, 80]
    for y in range(62, min(h, 94)):
        for x in range(64, min(w, 92)):
            if bp[x, y][3] >= 16:
                continue
            src = sp[min(62, x), y]
            bp[x, y] = src if src[3] > 180 else fill
    return out


def author_block() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    shield = idle_shield_mask(idle)
    frames = []
    frames.append(idle.copy())
    mid = shift_layer(idle, shield, -6, -10)
    mid = restore_right_hip(mid, idle)
    frames.append(crouch(mid, 1))
    high = shift_layer(idle, shield, -12, -20)
    high = restore_right_hip(high, idle)
    frames.append(crouch(high, 2))
    pulse = shift_layer(high, idle_shield_mask(high), -1, -1)
    frames.append(crouch(pulse, 2))
    return {f"block_{i}": im for i, im in enumerate(frames)}


def author_thrust() -> dict[str, Image.Image]:
    """Front-facing jab. Teal spear stays on-model; silhouette ≠ attack_21–24."""
    idle = load_canon("idle_front")
    frames = []
    frames.append(idle.copy())
    coil = crouch(disarm(idle), 1)
    draw_vertical_spear(coil, 20, 1, 48, scale=1)
    frames.append(coil)
    jab = crouch(disarm(idle), 2)
    jab = shift_layer(jab, torso_mask(jab), 1, 0)
    draw_vertical_spear(jab, 24, 10, 54, scale=1)
    frames.append(jab)
    hit = crouch(disarm(idle), 3)
    hit = shift_layer(hit, torso_mask(hit), 2, 0)
    draw_vertical_spear(hit, 28, 18, 58, scale=1)
    frames.append(hit)
    frames.append(crouch(idle, 1))
    return {f"thrust_{i}": im for i, im in enumerate(frames)}


def author_cast() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    frames = [
        idle.copy(),
        flash_eyes(shift_layer(idle, torso_mask(idle), 0, -1), glow=1),
        flash_eyes(shift_layer(idle, torso_mask(idle), 0, -2), glow=2),
        flash_eyes(idle, glow=1),
    ]
    return {f"cast_{i}": im for i, im in enumerate(frames)}


def crouch(im: Image.Image, dy: int) -> Image.Image:
    """Shift the whole sprite down and clip. Reads as a squat; no torso/leg split."""
    if dy <= 0:
        return im.copy()
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    paste_offset(out, im, 0, dy)
    return out


def tuck_feet(im: Image.Image, rows: int = 10, hop: int = -3) -> Image.Image:
    """Clear the lowest pixels so the feet leave the ground, then hop up."""
    cut = im.copy()
    px = cut.load()
    w, h = cut.size
    for y in range(max(0, h - rows), h):
        for x in range(w):
            px[x, y] = (0, 0, 0, 0)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    paste_offset(out, cut, 0, hop)
    return out


def author_kneel() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    low = crouch(idle, 10)
    braced = shift_layer(low, idle_shield_mask(low), -4, 2)
    frames = [
        idle.copy(),
        crouch(idle, 5),
        braced,
        shift_layer(braced, idle_shield_mask(braced), -1, 1),
    ]
    return {f"kneel_{i}": im for i, im in enumerate(frames)}


def author_wave() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    bare = disarm(idle)
    hand_keys = [
        None,
        (58, 48),
        (64, 28),
        (70, 22),
        (62, 30),
        (56, 46),
    ]
    frames = []
    for i, hand in enumerate(hand_keys):
        posed = bare.copy() if hand else idle.copy()
        if i in (2, 3, 4):
            posed = shift_layer(posed, torso_mask(posed), 1, 0)
        if hand:
            stamp(posed, hand[0], hand[1], PALM if i >= 2 else GAUNTLET, G_COLORS)
        frames.append(posed)
    return {f"wave_{i}": im for i, im in enumerate(frames)}


def author_jump() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    frames = [
        idle.copy(),
        crouch(idle, 7),
        tuck_feet(idle, rows=12, hop=-4),
        tuck_feet(idle, rows=14, hop=-5),
        composite_dust(crouch(idle, 3), "dust_front_0", dy=6),
    ]
    return {f"jump_{i}": im for i, im in enumerate(frames)}


def author_cheer() -> dict[str, Image.Image]:
    idle = load_canon("idle_front")
    frames = []
    keys = [
        (0, False),
        (2, False),
        (-2, True),
        (-3, True),
        (0, True),
    ]
    for hop, raised in keys:
        posed = disarm(idle) if raised else idle.copy()
        if hop:
            shifted = Image.new("RGBA", posed.size, (0, 0, 0, 0))
            paste_offset(shifted, posed, 0, hop)
            posed = shifted
        if raised:
            # Fist stays on the right-hand column even when the body hops.
            draw_vertical_spear(posed, 21, max(1, 8 + hop), 50 + hop, scale=1)
        frames.append(posed)
    return {f"cheer_{i}": im for i, im in enumerate(frames)}


def author_all_new() -> dict[str, Image.Image]:
    out: dict[str, Image.Image] = {}
    for d in ("front", "back", "left", "right"):
        out.update(author_walk2(d))
        out.update(author_run(d))
    out.update(author_block())
    out.update(author_thrust())
    out.update(author_cast())
    out.update(author_kneel())
    out.update(author_wave())
    out.update(author_jump())
    out.update(author_cheer())
    for name, im in out.items():
        if im.size != CANVAS_96:
            raise RuntimeError(f"{name} is {im.size}, expected {CANVAS_96}")
    return out


# ---------------------------------------------------------------------------
# Save / GIF
# ---------------------------------------------------------------------------

def save_pngs(frames: dict[str, Image.Image]) -> None:
    EXPANDED_PNG.mkdir(parents=True, exist_ok=True)
    CANON.mkdir(parents=True, exist_ok=True)
    for name, im in sorted(frames.items()):
        # Transparent 103×96 — matches existing frames_96.
        dest_canon = CANON / f"{name}.png"
        dest_exp = EXPANDED_PNG / f"{name}.png"
        im.save(dest_canon)
        shutil.copyfile(dest_canon, dest_exp)
        print(f"  png  {name:22}  {im.size[0]}x{im.size[1]}  RGBA transparent")


def write_expanded_json() -> None:
    spec = {
        "name": "roman_legionary_expanded",
        "parent": "animations.json",
        "source": "Authored from canon frames_96 poses; original Galahad pixels only.",
        "canvas": {"w": CANVAS_96[0], "h": CANVAS_96[1]},
        "anchor": {"x": 0.5, "y": 1.0},
        "background": {
            "png": "transparent",
            "gif": "#0b1220",
            "notes": (
                "New frames are transparent 103×96 PNGs, same as the canon pack, "
                "so Hold the Line can load them later. GIFs composite onto opaque "
                "navy #0b1220 (GIF only has 1-bit transparency)."
            ),
        },
        "rules": [
            "Do not flip left/right cycles. Shield and spear stay in drawn hands.",
            "Pixel-crisp: nearest-neighbor translations and overlays, no blur/resize.",
            "Existing walk_* / attack / idle names are unchanged.",
        ],
        "animations": {
            k: {
                "frames": v["frames"],
                "frameDurationMs": v["frameDurationMs"],
                "loop": v["loop"],
                "notes": v["notes"],
            }
            for k, v in EXPANDED_ANIMS.items()
        },
    }
    EXPANDED_JSON.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {EXPANDED_JSON.relative_to(ROOT)}")


def load_frame(name: str) -> Image.Image:
    path = CANON / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing frame {path}")
    return Image.open(path).convert("RGBA")


def composite_navy(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", im.size, NAVY)
    return Image.alpha_composite(bg, im)


def to_128(sprite: Image.Image, dx: int = 0, dy: int = 0) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_128, NAVY)
    paste_offset(canvas, sprite, ORIGIN_128[0] + dx, ORIGIN_128[1] + dy)
    return canvas


def quantize_sequence(frames: list[Image.Image]) -> list[Image.Image]:
    if not frames:
        raise ValueError("No frames to quantize")
    w, h = frames[0].size
    for i, frame in enumerate(frames):
        if frame.size != (w, h):
            raise ValueError(f"Frame {i} size {frame.size} != {w}x{h}")
    sheet = Image.new("RGB", (w * len(frames), h))
    for i, frame in enumerate(frames):
        sheet.paste(frame.convert("RGB"), (i * w, 0))
    pal = sheet.quantize(
        colors=128 if w >= 128 else 256,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )
    return [pal.crop((i * w, 0, (i + 1) * w, h)) for i in range(len(frames))]


def write_gif(dest: Path, frames: list[Image.Image], duration, loop: bool) -> None:
    palettes = quantize_sequence(frames)
    first, rest = palettes[0], palettes[1:]
    first.save(
        dest,
        save_all=True,
        append_images=rest,
        duration=duration,
        loop=0 if loop else 1,
        disposal=2,
        optimize=False,
    )


def inspect_gif(path: Path) -> str:
    with Image.open(path) as im:
        n = getattr(im, "n_frames", 1)
        durs = []
        for i in range(n):
            im.seek(i)
            durs.append(im.info.get("duration", "?"))
        loop = im.info.get("loop", "?")
        return (
            f"{path.name:22}  {im.size[0]}x{im.size[1]}  {n}f  "
            f"dur={durs}  loop={loop}  {path.stat().st_size / 1024:5.1f} KB"
        )


def build_96_gifs() -> None:
    GIF_DIR.mkdir(parents=True, exist_ok=True)
    print("Building 96px navy GIFs → assets/gifs/")
    for name, clip in EXPANDED_ANIMS.items():
        rgba = [composite_navy(load_frame(n)) for n in clip["frames"]]
        dest = GIF_DIR / f"{name}.gif"
        write_gif(dest, rgba, clip["frameDurationMs"], clip["loop"])
        print(f"  {inspect_gif(dest)}")
        if dest.stat().st_size > 200 * 1024:
            print(f"    warning: {dest.name} exceeds 200 KB", file=sys.stderr)


def build_128_gifs() -> None:
    REACT_DIR.mkdir(parents=True, exist_ok=True)
    print("Building 128px showcase GIFs → assets/gifs/reactions/")
    for name, show in SHOWCASE.items():
        clip = EXPANDED_ANIMS[name]
        hops = show.get("hop") or [0] * len(clip["frames"])
        frames = []
        for i, fname in enumerate(clip["frames"]):
            dy = hops[i] if i < len(hops) else 0
            frames.append(to_128(load_frame(fname), dy=dy))
        durs = show["durations"]
        if len(durs) != len(frames):
            raise RuntimeError(f"{name}: {len(frames)} frames vs {len(durs)} durations")
        dest = REACT_DIR / f"{name}.gif"
        write_gif(dest, frames, durs, loop=True)
        print(f"  {inspect_gif(dest)}")
        if dest.stat().st_size > 300 * 1024:
            print(f"    warning: {dest.name} exceeds 300 KB", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author",
        action="store_true",
        help="Rebuild expanded PNGs from canon poses, then GIFs",
    )
    args = parser.parse_args()
    print(f"Canon:     {CANON}")
    print(f"Expanded:  {EXPANDED_PNG}")
    print(f"PNG canvas:{CANVAS_96[0]}x{CANVAS_96[1]} transparent")
    print(f"GIF bg:    #{NAVY[0]:02x}{NAVY[1]:02x}{NAVY[2]:02x}")
    print()
    if args.author:
        print("Authoring expanded PNGs…")
        frames = author_all_new()
        save_pngs(frames)
        write_expanded_json()
        print()
    elif not EXPANDED_JSON.is_file():
        raise SystemExit("No animations_expanded.json — run with --author first.")
    print("Building GIFs…")
    build_96_gifs()
    print()
    build_128_gifs()
    print("\nDone. Original Galahad poses; no mirrored walks, no meme rips.")


if __name__ == "__main__":
    main()
