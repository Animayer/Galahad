#!/usr/bin/env python3
"""Author original Galahad reaction frames and assemble Discord/X GIFs.

Source pixels come from the canon roman_legionary pack
(``assets/roman_legionary/frames_96/``) plus hand-authored overlays in
the same teal / red / magenta palette. No third-party meme stills, no
mirroring of left/right walk cycles.

Usage:
    python3 scripts/make-reaction-gifs.py           # GIFs from committed PNGs
    python3 scripts/make-reaction-gifs.py --author  # rebuild PNGs, then GIFs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow is required. Install with: python3 -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "assets" / "roman_legionary" / "frames_96"
FRAME_ROOT = ROOT / "assets" / "reactions" / "frames"
GIF_DIR = ROOT / "assets" / "gifs" / "reactions"

NAVY = (11, 18, 32, 255)  # #0b1220
CANVAS = (128, 128)
# 103x96 canon sprite, 8px floor, 24px headroom for raised spear / nods.
ORIGIN = ((CANVAS[0] - 103) // 2, CANVAS[1] - 96 - 8)  # (12, 24)

# Sampled from idle_front, plus portrait-lore magenta.
ARMOR = (101, 154, 136, 255)
ARMOR_LT = (129, 174, 154, 255)
ARMOR_DK = (70, 120, 121, 255)
MAGENTA = (232, 48, 160, 255)
MAGENTA_LT = (255, 96, 196, 255)
OUTLINE = (10, 18, 30, 255)

# --- reaction spec: timings + suggested captions (ms per frame, infinite loop)

REACTIONS: dict[str, dict] = {
    "agree_nod": {
        "caption": "Aye.",
        "durations": [180, 160, 160, 280, 220, 160, 160, 200],
    },
    "disagree_shake": {
        "caption": "That's a no from the cohort.",
        "durations": [90, 90, 90, 90, 90, 90, 90, 90, 110, 140],
    },
    "shrug": {
        "caption": "Not my cohort.",
        "durations": [160, 140, 320, 280, 160, 180],
    },
    "facepalm": {
        "caption": "The line, and my patience.",
        "durations": [140, 120, 140, 360, 280, 200],
    },
    "salute_yes": {
        "caption": "Affirmative.",
        "durations": [140, 120, 140, 300, 160, 180],
    },
    "point_you": {
        "caption": "You. Step forward.",
        "durations": [140, 120, 280, 220, 160, 180],
    },
    "victory_crest": {
        "caption": "The line held.",
        "durations": [120, 100, 280, 180, 160, 200],
    },
    "confused": {
        "caption": "…orders?",
        "durations": [180, 160, 280, 220, 180, 200],
    },
    "slow_clap": {
        "caption": "Well fought. Eventually.",
        "durations": [220, 220, 340, 220, 220, 260],
    },
    "walk_away": {
        "caption": "We're done here.",
        "durations": [220, 140, 140, 120, 120, 120, 120, 160],
    },
    "shocked": {
        "caption": "The line— what.",
        "durations": [120, 80, 80, 220, 160, 180],
    },
    "hold_the_line": {
        "caption": "Hold.",
        "durations": [180, 160, 280, 200, 180, 200],
    },
}


def load_canon(name: str) -> Image.Image:
    path = CANON / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing canon frame: {path}")
    return Image.open(path).convert("RGBA")


def blank_canvas() -> Image.Image:
    return Image.new("RGBA", CANVAS, NAVY)


def place(dst: Image.Image, sprite: Image.Image, dx: int = 0, dy: int = 0) -> Image.Image:
    x, y = ORIGIN[0] + dx, ORIGIN[1] + dy
    layer = Image.new("RGBA", dst.size, (0, 0, 0, 0))
    paste_offset(layer, sprite, x, y)
    return Image.alpha_composite(dst, layer)


def paste_offset(dst: Image.Image, src: Image.Image, dx: int, dy: int) -> None:
    """alpha_composite ``src`` onto ``dst`` at (dx, dy), clipping as needed."""
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
    mp = mask.load()
    px = im.load()
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


def idle_head_mask(im: Image.Image) -> Image.Image:
    # Crest + helmet + visor; spear lives at x<=32.
    return mask_from_pred(im, lambda x, y, p: y <= 42 and x >= 38)


def idle_spear_mask(im: Image.Image) -> Image.Image:
    # Grounded spear + grip. Keep the red cape on the left hip.
    def pred(x, y, p):
        r, g, b, a = p
        if x > 31:
            return False
        if y >= 50 and r >= 90 and r > g + 15:
            return False
        return True

    return mask_from_pred(im, pred)


def disarm(im: Image.Image) -> Image.Image:
    """Hard-punch the grounded spear column; keep cape reds."""
    out = im.copy()
    px = out.load()
    for y in range(0, 92):
        for x in range(0, 34):
            r, g, b, a = px[x, y]
            if a <= 16:
                continue
            if y >= 50 and r >= 90 and r > g + 15:
                continue
            px[x, y] = (0, 0, 0, 0)
    return out


def draw_vertical_spear(im: Image.Image, cx: int, tip_y: int, fist_y: int) -> None:
    """Teal head, brown shaft, gauntlet at the grip. Pixel-crisp, no resize."""
    px = im.load()
    w, h = im.size

    def put(x: int, y: int, color: tuple) -> None:
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = color

    # Spear head (diamond).
    head = [
        (0, ARMOR_LT),
        (1, ARMOR_LT),
        (2, ARMOR),
        (3, ARMOR_LT),
        (4, ARMOR),
    ]
    for i, (spread, color) in enumerate(head):
        y = tip_y + i
        for dx in range(-spread, spread + 1):
            put(cx + dx, y, color)
        put(cx - spread - 1, y, OUTLINE)
        put(cx + spread + 1, y, OUTLINE)

    shaft_top = tip_y + len(head)
    shaft_bot = fist_y - 3
    # Light brown so the shaft reads on navy #0b1220.
    wood = (186, 118, 86, 255)
    wood_dk = (132, 78, 58, 255)
    for y in range(shaft_top, max(shaft_top, shaft_bot)):
        put(cx - 2, y, OUTLINE)
        put(cx - 1, y, wood_dk)
        put(cx, y, wood)
        put(cx + 1, y, wood_dk)
        put(cx + 2, y, OUTLINE)

    stamp(im, cx - 3, fist_y - 3, GAUNTLET, G_COLORS)


def idle_shield_mask(im: Image.Image) -> Image.Image:
    return mask_from_pred(im, lambda x, y, p: x >= 68 and 46 <= y <= 86)


def shift_layer(im: Image.Image, mask: Image.Image, dx: int, dy: int) -> Image.Image:
    layer = layer_from_mask(im, mask)
    body = punch(im, mask)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(body)
    paste_offset(out, layer, dx, dy)
    return out


def rotate_layer(im: Image.Image, mask: Image.Image, angle: float, pivot: tuple[int, int]) -> Image.Image:
    layer = layer_from_mask(im, mask)
    body = punch(im, mask)
    rotated = layer.rotate(
        angle, resample=Image.Resampling.NEAREST, center=pivot, fillcolor=(0, 0, 0, 0)
    )
    return Image.alpha_composite(body, rotated)


def inpaint_neck(body: Image.Image, source: Image.Image) -> Image.Image:
    """Fill small holes under a moved helmet from the gorget row."""
    out = body.copy()
    bp = out.load()
    sp = source.load()
    w, h = out.size
    for y in range(36, 48):
        for x in range(40, 74):
            if x >= w or y >= h:
                continue
            if bp[x, y][3] >= 16:
                continue
            for yy in range(y + 1, min(y + 8, h)):
                if sp[x, yy][3] > 180:
                    bp[x, y] = sp[x, yy]
                    break
    return out


def flash_eyes(im: Image.Image, glow: int = 1) -> Image.Image:
    """Portrait-lore magenta in the visor slit."""
    out = im.copy()
    px = out.load()
    cores = [(50, 33), (51, 33), (50, 34), (51, 34), (59, 33), (60, 33), (59, 34), (60, 34)]
    ring = [(49, 33), (52, 33), (58, 33), (61, 33), (50, 32), (51, 32), (59, 32), (60, 32)]
    for x, y in cores:
        if 0 <= x < out.size[0] and 0 <= y < out.size[1] and px[x, y][3] > 16:
            px[x, y] = MAGENTA_LT if glow >= 2 else MAGENTA
    if glow >= 2:
        for x, y in ring:
            if 0 <= x < out.size[0] and 0 <= y < out.size[1] and px[x, y][3] > 16:
                px[x, y] = MAGENTA
    return out


def stamp(im: Image.Image, ox: int, oy: int, rows: list[str], colors: dict[str, tuple]) -> None:
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
    # Dark outline first so overlays read against teal armor.
    occupied = {(x, y) for x, y, _ in filled}
    for x, y, _ in filled:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (nx, ny) not in occupied and 0 <= nx < w and 0 <= ny < h:
                px[nx, ny] = OUTLINE
    for x, y, color in filled:
        px[x, y] = color


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
FINGER_POINT = [
    "    oooo     ",
    "  ooOOOOOo   ",
    " oOOOOOOOOo  ",
    "oOOOOOOOOOo  ",
    "oOOOOOOOOOo  ",
    "oOOOOOoooOo  ",
    " oOOOOoooo   ",
    "  oooo  ##   ",
    "        ##   ",
    "        ##   ",
    "        ###  ",
    "         ##  ",
    "         ##  ",
]
CLAP_HAND = [
    "  oooo  ",
    " oOOOOo ",
    "oOOOOOOo",
    "oOOOOOOo",
    "oOOOOOOo",
    " oOOOOo ",
    "  oooo  ",
]

G_COLORS = {"o": ARMOR_DK, "O": ARMOR, "#": ARMOR_LT}
P_COLORS = {"o": ARMOR_DK, "O": ARMOR, "#": ARMOR_LT}


def pose_canvas(sprite: Image.Image, dx: int = 0, dy: int = 0) -> Image.Image:
    return place(blank_canvas(), sprite, dx, dy)


def author_agree_nod() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    offsets = [0, 1, 3, 5, 5, 3, 1, 0]
    frames = []
    for dy in offsets:
        posed = shift_layer(idle, head, 0, dy)
        if dy:
            posed = inpaint_neck(posed, idle)
        frames.append(pose_canvas(posed))
    return frames


def author_disagree_shake() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    offsets = [0, -3, -5, -2, 3, 5, 2, -3, 3, 0]
    frames = []
    for dx in offsets:
        posed = shift_layer(idle, head, dx, 0)
        posed = inpaint_neck(posed, idle)
        frames.append(pose_canvas(posed))
    return frames


def author_shrug() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    shield = idle_shield_mask(idle)
    upper = mask_from_pred(idle, lambda x, y, p: y < 78)
    frames = []
    steps = [
        (0, 0, 0, 0),
        (6, 2, 4, 2),
        (10, 4, 8, 3),
        (10, 4, 8, 3),
        (6, 2, 4, 2),
        (0, 0, 0, 0),
    ]
    for tilt, lift, hdx, hdy in steps:
        posed = idle
        if lift:
            posed = shift_layer(posed, upper, 0, -lift)
        posed = rotate_layer(posed, head, tilt, (56, 42 - lift))
        posed = inpaint_neck(posed, idle)
        posed = shift_layer(posed, shield, 3 if lift else 0, lift)
        c = pose_canvas(posed)
        if hdx:
            stamp(c, ORIGIN[0] + 16, ORIGIN[1] + 46 - hdy, PALM, P_COLORS)
            stamp(c, ORIGIN[0] + 74, ORIGIN[1] + 42 - hdy, PALM, P_COLORS)
        frames.append(c)
    return frames


def author_facepalm() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    keys = [
        (0, None),
        (2, (ORIGIN[0] + 62, ORIGIN[1] + 14)),
        (4, (ORIGIN[0] + 50, ORIGIN[1] + 24)),
        (6, (ORIGIN[0] + 46, ORIGIN[1] + 26)),
        (6, (ORIGIN[0] + 47, ORIGIN[1] + 27)),
        (5, (ORIGIN[0] + 46, ORIGIN[1] + 26)),
    ]
    frames = []
    for bow, hand in keys:
        posed = shift_layer(idle, head, 0, bow)
        posed = inpaint_neck(posed, idle)
        c = pose_canvas(posed)
        if hand:
            stamp(c, hand[0], hand[1], GAUNTLET, G_COLORS)
        frames.append(c)
    return frames


def author_salute_yes() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    keys = [
        (False, 0),
        (True, 0),
        (True, 1),
        (True, 3),
        (True, 2),
        (True, 0),
    ]
    frames = []
    for raised, nod in keys:
        posed = disarm(idle) if raised else idle
        if nod:
            posed = shift_layer(posed, head, 0, nod)
            posed = inpaint_neck(posed, idle)
        c = pose_canvas(posed)
        if raised:
            draw_vertical_spear(c, ORIGIN[0] + 22, 4, ORIGIN[1] + 28 + nod)
        frames.append(c)
    return frames


def author_point_you() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    frames = []
    keys = [
        (0, 0, False, 0),
        (1, 1, True, 0),
        (2, 2, True, 4),
        (3, 2, True, 8),
        (2, 1, True, 4),
        (1, 1, True, 2),
    ]
    for lean, nod, show, jab in keys:
        posed = idle
        posed = shift_layer(posed, head, 0, nod)
        posed = inpaint_neck(posed, idle)
        c = pose_canvas(posed, dx=lean, dy=lean)
        if show:
            stamp(
                c,
                ORIGIN[0] + 72 + jab,
                ORIGIN[1] + 52 + jab // 2,
                FINGER_POINT,
                P_COLORS,
            )
        frames.append(c)
    return frames


def author_victory_crest() -> list[Image.Image]:
    idle = load_canon("idle_front")
    keys = [
        (0, 0, False),
        (2, 0, False),
        (-4, -2, True),
        (-5, -2, True),
        (-4, -1, True),
        (-2, 0, True),
    ]
    frames = []
    for hop, crouch, raised in keys:
        posed = disarm(idle) if raised else idle
        if crouch:
            lowered = Image.new("RGBA", idle.size, (0, 0, 0, 0))
            paste_offset(lowered, posed, 0, crouch)
            posed = lowered
        c = pose_canvas(posed, dy=hop)
        if raised:
            draw_vertical_spear(
                c,
                ORIGIN[0] + 24,
                max(2, ORIGIN[1] + hop - 18),
                ORIGIN[1] + 22 + hop,
            )
        frames.append(c)
    return frames


def author_confused() -> list[Image.Image]:
    idle = load_canon("idle_front")
    head = idle_head_mask(idle)
    angles = [0, 8, 14, 12, 6, 10]
    frames = []
    for ang in angles:
        posed = rotate_layer(idle, head, ang, (56, 42))
        posed = inpaint_neck(posed, idle)
        frames.append(pose_canvas(posed))
    return frames


def author_slow_clap() -> list[Image.Image]:
    idle = load_canon("idle_front")
    shield = idle_shield_mask(idle)
    gaps = [12, 7, 1, 7, 12, 8]
    frames = []
    for gap in gaps:
        posed = disarm(idle)
        if gap <= 1:
            posed = shift_layer(posed, shield, -2, 0)
        c = pose_canvas(posed)
        cx = ORIGIN[0] + 50
        cy = ORIGIN[1] + 52
        stamp(c, cx - 10 - gap, cy, CLAP_HAND, G_COLORS)
        stamp(c, cx + 2 + gap, cy, CLAP_HAND, G_COLORS)
        if gap <= 1:
            px = c.load()
            for spark in ((cx + 6, cy - 2), (cx + 8, cy - 4), (cx + 5, cy - 5)):
                x, y = spark
                if 0 <= x < c.size[0] and 0 <= y < c.size[1]:
                    px[x, y] = ARMOR_LT
        frames.append(c)
    return frames


def author_walk_away() -> list[Image.Image]:
    # Turn with distinct idle drawings (no mirrors), then walk_right off-stage.
    sequence = [
        ("idle_front", 0),
        ("idle_right", 4),
        ("walk_right_0", 10),
        ("walk_right_1", 20),
        ("walk_right_2", 32),
        ("walk_right_3", 44),
        ("walk_right_0", 58),
        ("walk_right_1", 72),
    ]
    frames = []
    for name, dx in sequence:
        frames.append(pose_canvas(load_canon(name), dx=dx))
    return frames


def author_shocked() -> list[Image.Image]:
    idle = load_canon("idle_front")
    hurt_a = load_canon("hurt_25")
    hurt_b = load_canon("hurt_26")
    return [
        pose_canvas(idle),
        pose_canvas(flash_eyes(idle, glow=2), dx=-1),
        pose_canvas(flash_eyes(hurt_a, glow=2), dx=2),
        pose_canvas(flash_eyes(hurt_b, glow=1), dx=-1),
        pose_canvas(flash_eyes(hurt_a, glow=1)),
        pose_canvas(idle, dx=0),
    ]


def author_hold_the_line() -> list[Image.Image]:
    idle = load_canon("idle_front")
    braced = load_canon("attack_24")
    dust = load_canon("dust_front_1")
    frames = []
    # Idle → repaired block poses (connected sprite, no shield punch).
    frames.append(pose_canvas(idle))
    # Prefer repaired block frames (connected sprite). Fall back to idle.
    block1 = CANON / "block_1.png"
    block2 = CANON / "block_2.png"
    if block1.is_file() and block2.is_file():
        b1 = load_canon("block_1")
        b2 = load_canon("block_2")
        frames.append(pose_canvas(b1, dy=1))
        frames.append(pose_canvas(b2, dy=1))
        shove = pose_canvas(b2, dy=2, dx=-1)
        paste_offset(shove, dust, ORIGIN[0] + 20, ORIGIN[1] + 70)
        frames.append(shove)
        frames.append(pose_canvas(b2, dy=1))
        frames.append(pose_canvas(b1, dy=1))
    else:
        planted = idle.copy()
        frames.append(pose_canvas(planted, dy=1))
        frames.append(pose_canvas(braced, dy=1))
        shove = pose_canvas(braced, dy=2, dx=-1)
        paste_offset(shove, dust, ORIGIN[0] + 20, ORIGIN[1] + 70)
        frames.append(shove)
        frames.append(pose_canvas(braced, dy=1))
        frames.append(pose_canvas(braced, dy=1, dx=0))
    return frames


AUTHORS = {
    "agree_nod": author_agree_nod,
    "disagree_shake": author_disagree_shake,
    "shrug": author_shrug,
    "facepalm": author_facepalm,
    "salute_yes": author_salute_yes,
    "point_you": author_point_you,
    "victory_crest": author_victory_crest,
    "confused": author_confused,
    "slow_clap": author_slow_clap,
    "walk_away": author_walk_away,
    "shocked": author_shocked,
    "hold_the_line": author_hold_the_line,
}


def save_png_frames(name: str, frames: list[Image.Image]) -> Path:
    dest_dir = FRAME_ROOT / name
    if dest_dir.exists():
        for old in dest_dir.glob("*.png"):
            old.unlink()
    dest_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(dest_dir / f"{i:02d}.png")
    return dest_dir


def load_png_frames(name: str) -> list[Image.Image]:
    dest_dir = FRAME_ROOT / name
    paths = sorted(dest_dir.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"No PNG frames in {dest_dir}")
    return [Image.open(p).convert("RGBA") for p in paths]


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
        colors=128,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )
    return [pal.crop((i * w, 0, (i + 1) * w, h)) for i in range(len(frames))]


def write_gif(dest: Path, frames: list[Image.Image], durations: list[int]) -> None:
    palettes = quantize_sequence(frames)
    first, rest = palettes[0], palettes[1:]
    first.save(
        dest,
        save_all=True,
        append_images=rest,
        duration=durations,
        loop=0,
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
            f"{path.name:20}  {im.size[0]}x{im.size[1]}  {n}f  "
            f"dur={durs}  loop={loop}  {path.stat().st_size / 1024:5.1f} KB"
        )


def author_all() -> None:
    FRAME_ROOT.mkdir(parents=True, exist_ok=True)
    for name, fn in AUTHORS.items():
        frames = fn()
        spec = REACTIONS[name]
        if len(frames) != len(spec["durations"]):
            raise RuntimeError(
                f"{name}: {len(frames)} frames vs {len(spec['durations'])} durations"
            )
        save_png_frames(name, frames)
        print(f"  authored {name:16}  {len(frames)} PNG  {CANVAS[0]}x{CANVAS[1]}")


def build_gifs() -> None:
    GIF_DIR.mkdir(parents=True, exist_ok=True)
    for name, spec in REACTIONS.items():
        frames = load_png_frames(name)
        durations = spec["durations"]
        if len(frames) != len(durations):
            raise RuntimeError(
                f"{name}: {len(frames)} PNGs vs {len(durations)} durations"
            )
        dest = GIF_DIR / f"{name}.gif"
        write_gif(dest, frames, durations)
        line = inspect_gif(dest)
        print(f"  {line}")
        if dest.stat().st_size > 300 * 1024:
            print(f"    warning: {dest.name} exceeds 300 KB", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author",
        action="store_true",
        help="Rebuild PNG frames from canon sprites, then GIFs",
    )
    args = parser.parse_args()
    print(f"Canon:   {CANON}")
    print(f"Frames:  {FRAME_ROOT}")
    print(f"GIFs:    {GIF_DIR}")
    print(f"Canvas:  {CANVAS[0]}x{CANVAS[1]}  bg=#{NAVY[0]:02x}{NAVY[1]:02x}{NAVY[2]:02x}")
    print()
    if args.author:
        print("Authoring reaction PNGs…")
        author_all()
        print()
    print("Building GIFs…")
    build_gifs()
    print("\nDone. Original Galahad composites; no mirrored walks, no meme rips.")


if __name__ == "__main__":
    main()
