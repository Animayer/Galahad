#!/usr/bin/env python3
"""Author original Galahad Discord emoji frames and assemble upload GIFs.

Bust / head+crest / shield-Mark close-ups drawn at 64×64 and nearest-neighbor
scaled to 128×128. This pack does **not** load, crop, or rescale the canon
roman_legionary walk/run/reaction sheets — Ryan Mayer original IP, new art.

Usage:
    python3 scripts/make-discord-emojis.py --author   # PNGs then GIFs
    python3 scripts/make-discord-emojis.py            # GIFs from committed PNGs
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required. Install with: python3 -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
FRAME_ROOT = ROOT / "assets" / "discord-emojis" / "frames"
GIF_DIR = ROOT / "assets" / "discord-emojis"

NATIVE = 64
SCALE = 2
CANVAS = NATIVE * SCALE  # 128
NAVY = (11, 18, 32, 255)  # #0b1220 — pack-wide opaque background
MAX_BYTES = 256 * 1024
WARN_BYTES = 150 * 1024

# Visual lock: darker blue-grey lorica, tall red crest, battle-worn (not holy-knight chrome).
K = (8, 10, 16, 255)
R = (204, 40, 38, 255)
RD = (118, 18, 24, 255)
RH = (236, 84, 64, 255)
T = (74, 118, 122, 255)
TL = (124, 162, 158, 255)
TD = (44, 74, 80, 255)
TX = (28, 46, 52, 255)
N = (18, 24, 34, 255)
S = (198, 140, 104, 255)
SD = (154, 98, 72, 255)
SK = (120, 72, 54, 255)
B = (90, 48, 36, 255)
BL = (128, 74, 52, 255)
BD = (48, 26, 20, 255)
C = (156, 32, 42, 255)
CD = (86, 16, 24, 255)
CL = (184, 54, 56, 255)
EY = (236, 224, 204, 255)
PU = (28, 16, 14, 255)
MG = (232, 48, 160, 255)
MGL = (255, 110, 196, 255)
W = (120, 74, 52, 255)
WD = (78, 46, 34, 255)
BLD = (120, 26, 30, 255)
MK = (12, 12, 16, 255)
SP = (196, 124, 88, 255)
SPD = (132, 78, 58, 255)
# Gauntlets: cooler steel so they separate from lorica teal.
GT = (156, 168, 172, 255)
GD = (88, 98, 108, 255)
GX = (48, 54, 62, 255)


@dataclass
class Face:
    eyes: str = "open"  # open, closed, wide, magenta
    brow: int = 0  # -1 raised, 0, 1 lowered
    mouth: str = "flat"  # flat, frown, grin, open, o


@dataclass
class Pose:
    head_dx: int = 0
    head_dy: int = 0
    head_tilt: float = 0.0
    shrug: int = 0
    cape_sway: int = 0
    crest_sway: int = 0
    face: Face | None = None
    # Overlay extras drawn after the bust.
    extras: tuple = ()


class Pix:
    def __init__(self, w: int = NATIVE, h: int = NATIVE) -> None:
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()
        self.w, self.h = w, h

    def put(self, x: int, y: int, c: tuple[int, int, int, int]) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[x, y] = c

    def get(self, x: int, y: int) -> tuple[int, int, int, int]:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[x, y]
        return (0, 0, 0, 0)

    def fill(self, x0: int, y0: int, x1: int, y1: int, c: tuple) -> None:
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def disc(self, cx: int, cy: int, r: int, c: tuple) -> None:
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                    self.put(x, y, c)

    def ellipse(self, cx: int, cy: int, rx: int, ry: int, c: tuple) -> None:
        if rx <= 0 or ry <= 0:
            return
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                nx = (x - cx + 0.5) / rx
                ny = (y - cy + 0.5) / ry
                if nx * nx + ny * ny <= 1.0:
                    self.put(x, y, c)

    def stamp(self, ox: int, oy: int, rows: list[str], colors: dict[str, tuple]) -> None:
        filled: list[tuple[int, int, tuple]] = []
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in (".", " "):
                    continue
                color = colors.get(ch)
                if color is None:
                    continue
                filled.append((ox + i, oy + j, color))
        occupied = {(x, y) for x, y, _ in filled}
        for x, y, _ in filled:
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if (nx, ny) not in occupied:
                    self.put(nx, ny, K)
        for x, y, color in filled:
            self.put(x, y, color)

    def outline_opaque(self, color: tuple = K) -> None:
        hits: list[tuple[int, int]] = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] < 16:
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if not (0 <= nx < self.w and 0 <= ny < self.h) or self.p[nx, ny][3] < 16:
                        hits.append((nx, ny))
        for x, y in hits:
            if 0 <= x < self.w and 0 <= y < self.h and self.p[x, y][3] < 16:
                self.put(x, y, color)


def paste_offset(dst: Image.Image, src: Image.Image, dx: int, dy: int) -> None:
    sw, sh = src.size
    dw, dh = dst.size
    sx0, sy0 = max(0, -dx), max(0, -dy)
    dx0, dy0 = max(0, dx), max(0, dy)
    sx1, sy1 = min(sw, dw - dx0 + sx0), min(sh, dh - dy0 + sy0)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(src.crop((sx0, sy0, sx1, sy1)), (dx0, dy0))


def draw_mark(px: Pix, cx: int, cy: int, scale: int = 1, glow: int = 0) -> None:
    """Three-pronged claw / vertical trident in a circle — the Mark.

    Glow is teal/steel only. Magenta is reserved for the shocked/oath eye.
    """
    ink = TL if glow >= 2 else (T if glow == 1 else MK)
    stem = MK if glow == 0 else (TD if glow == 1 else TL)
    s = max(1, scale)
    r = 6 * s
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot(x - cx, y - cy)
            if abs(d - r) < 0.9:
                px.put(x, y, TL if glow else MK)
    # Stem.
    h = 5 * s
    for i in range(-h, h + 1):
        px.put(cx, cy + i, stem)
        if s > 1:
            px.put(cx - 1, cy + i, stem)
            px.put(cx + 1, cy + i, stem)
    # Three upward prongs (claw / trident) — wide at the top.
    for dy in range(0, 5 * s):
        y = cy - h + dy
        spread = (4 * s) - dy
        if spread < s:
            continue
        px.put(cx - spread, y, stem)
        px.put(cx + spread, y, stem)
        if s > 1:
            px.put(cx - spread - 1, y, stem)
            px.put(cx + spread + 1, y, stem)
        if glow:
            px.put(cx - spread - s, y, ink)
            px.put(cx + spread + s, y, ink)
    px.put(cx, cy - h - 1, stem)
    if glow >= 2:
        px.put(cx, cy - h - 2, TL)
        px.put(cx - 1, cy, TL)
        px.put(cx + 1, cy, TL)


def draw_crest(px: Pix, cx: int, top: int, height: int = 22, sway: int = 0) -> None:
    """Tall horsehair crest — drawn last so the galea cannot eat it."""
    for y in range(top, top + height):
        t = (y - top) / max(1, height - 1)
        half = 1 + int(7.0 * (t ** 0.85))
        sw = sway if y < top + height // 2 else 0
        for dx in range(-half, half + 1):
            x = cx + dx + sw
            adx = abs(dx) / max(1, half)
            strand = (x + y * 2) % 4
            if adx > 0.82:
                col = RD
            elif y < top + 3 or (adx < 0.22 and strand != 0):
                col = RH
            elif strand == 0:
                col = RD
            else:
                col = R
            px.put(x, y, col)
        px.put(cx - half - 1 + sw, y, K)
        px.put(cx + half + 1 + sw, y, K)
    # Horsehair wisps — breaks the perfect triangle.
    for y, dx, col in (
        (6, 3, R), (8, 5, RD), (11, 7, R), (14, 8, RD),
        (7, -4, RD), (10, -6, R), (13, -8, RD), (16, 6, R),
    ):
        px.put(cx + dx + (sway if y < top + height // 2 else 0), top + y, col)
    # Metal holder sits on the dome, not over the face.
    yb = top + height - 1
    px.fill(cx - 4, yb - 1, cx + 4, yb + 1, TX)
    px.fill(cx - 3, yb - 1, cx + 3, yb, TL)


def draw_face(px: Pix, cx: int, cy: int, face: Face) -> None:
    """Open galea: forehead skin, big eyes, nose, shaped beard. cy is the eye row."""
    px.ellipse(cx, cy + 4, 12, 12, S)
    px.fill(cx - 10, cy - 4, cx + 10, cy + 8, S)
    px.fill(cx - 9, cy + 6, cx + 9, cy + 10, SD)

    brow_y = cy - 6 + face.brow
    px.fill(cx - 10, brow_y, cx + 10, brow_y + 1, TX)
    px.fill(cx - 8, brow_y + 1, cx + 8, brow_y + 1, TD)

    def eye(ex: int, mode: str) -> None:
        if mode == "closed":
            px.fill(ex - 4, cy, ex + 4, cy + 1, BD)
            px.put(ex - 4, cy - 1, B)
            px.put(ex + 4, cy - 1, B)
            return
        if mode == "wide":
            px.fill(ex - 4, cy - 3, ex + 4, cy + 3, EY)
            px.fill(ex - 2, cy - 2, ex + 2, cy + 2, PU)
            px.put(ex + 1, cy - 2, EY)
            return
        if mode == "magenta":
            px.fill(ex - 4, cy - 3, ex + 4, cy + 3, MGL)
            px.fill(ex - 2, cy - 2, ex + 2, cy + 2, MG)
            px.put(ex + 2, cy - 3, EY)
            for dx, dy in (
                (-5, 0), (5, 0), (0, -4), (0, 4),
                (-4, -3), (4, -3), (-4, 3), (4, 3),
            ):
                px.put(ex + dx, cy + dy, MG)
            return
        px.fill(ex - 4, cy - 2, ex + 3, cy + 2, EY)
        px.fill(ex - 2, cy - 1, ex + 1, cy + 1, PU)
        px.put(ex + 2, cy - 2, EY)
        px.put(ex - 4, cy - 2, SD)

    left_mode = face.eyes
    right_mode = "open" if face.eyes == "magenta" else face.eyes
    if face.eyes == "magenta":
        left_mode = "magenta"
        right_mode = "wide"
    eye(cx - 6, left_mode)
    eye(cx + 6, right_mode)

    px.put(cx, cy + 4, SK)
    px.put(cx, cy + 5, SD)
    px.put(cx - 1, cy + 5, SK)
    px.put(cx + 1, cy + 5, SD)

    px.fill(cx - 8, cy + 6, cx + 8, cy + 7, BL)
    px.fill(cx - 11, cy + 8, cx + 11, cy + 12, B)
    px.fill(cx - 9, cy + 12, cx + 9, cy + 14, B)
    px.fill(cx - 6, cy + 14, cx + 6, cy + 16, BD)
    px.fill(cx - 3, cy + 16, cx + 3, cy + 18, BD)
    px.put(cx - 9, cy + 7, BL)
    px.put(cx + 9, cy + 7, BL)
    px.put(cx + 10, cy + 12, BLD)
    px.put(cx - 10, cy + 13, BD)

    my = cy + 9
    if face.mouth == "flat":
        px.fill(cx - 2, my, cx + 2, my, BD)
    elif face.mouth == "frown":
        px.put(cx - 3, my + 1, BD)
        px.fill(cx - 2, my, cx + 2, my, BD)
        px.put(cx + 3, my + 1, BD)
    elif face.mouth == "grin":
        px.put(cx - 3, my, BD)
        px.fill(cx - 2, my + 1, cx + 2, my + 1, SK)
        px.put(cx + 3, my, BD)
    elif face.mouth == "open":
        px.fill(cx - 2, my, cx + 2, my + 2, BD)
        px.fill(cx - 1, my + 1, cx + 1, my + 1, SK)
    elif face.mouth == "o":
        px.fill(cx - 1, my, cx + 1, my + 2, BD)
        px.put(cx, my + 1, SK)


def draw_helmet(px: Pix, cx: int, hy: int) -> None:
    """Open-face galea: skull cap + brow + cheek guards. Stops above the eyes."""
    px.ellipse(cx, hy, 17, 11, T)
    px.fill(cx - 16, hy - 2, cx + 16, hy + 5, T)
    px.fill(cx - 12, hy - 6, cx + 12, hy, T)
    px.fill(cx - 9, hy - 8, cx + 9, hy - 5, T)
    px.fill(cx - 12, hy - 6, cx - 2, hy + 1, TL)
    px.fill(cx + 6, hy - 2, cx + 15, hy + 4, TD)
    px.put(cx - 6, hy - 5, TX)
    px.put(cx - 5, hy - 4, TX)
    px.put(cx + 8, hy - 3, K)
    px.put(cx + 9, hy - 2, TX)
    px.fill(cx - 14, hy + 4, cx + 14, hy + 6, TX)
    px.fill(cx - 12, hy + 4, cx + 8, hy + 5, TD)
    px.fill(cx - 19, hy + 3, cx - 13, hy + 20, T)
    px.fill(cx + 13, hy + 3, cx + 19, hy + 20, T)
    px.fill(cx - 19, hy + 3, cx - 15, hy + 10, TL)
    px.fill(cx + 15, hy + 12, cx + 19, hy + 20, TD)
    px.fill(cx - 18, hy + 20, cx - 13, hy + 22, TD)
    px.fill(cx + 13, hy + 20, cx + 18, hy + 22, TD)
    px.put(cx - 17, hy + 14, BLD)
    px.put(cx - 16, hy + 15, BLD)
    px.put(cx - 18, hy + 8, TL)
    px.put(cx + 18, hy + 8, TX)


def draw_head_layer(face: Face, crest_sway: int) -> Image.Image:
    px = Pix()
    cx = 32
    draw_helmet(px, cx, 22)
    draw_face(px, cx, 34, face)
    px.fill(cx - 8, 50, cx + 8, 54, T)
    px.fill(cx - 6, 51, cx + 6, 53, TL)
    draw_crest(px, cx, 0, height=20, sway=crest_sway)
    px.outline_opaque()
    return px.im


def draw_body_layer(shrug: int, cape_sway: int) -> Image.Image:
    px = Pix()
    cy = 50 - shrug
    # Cape — wide tattered wings so red reads at 48px emoji size.
    px.fill(1 + cape_sway, cy - 8, 20 + cape_sway, 63, CD)
    px.fill(2 + cape_sway, cy - 6, 18 + cape_sway, 62, C)
    px.fill(4 + cape_sway, cy - 4, 12 + cape_sway, 50, CL)
    px.fill(44 - cape_sway, cy - 8, 62 - cape_sway, 63, CD)
    px.fill(46 - cape_sway, cy - 6, 61 - cape_sway, 62, C)
    px.fill(52 - cape_sway, cy - 2, 60 - cape_sway, 48, CL)
    # Jagged hem.
    for x, y in (
        (3 + cape_sway, 63),
        (10 + cape_sway, 61),
        (16 + cape_sway, 63),
        (48 - cape_sway, 63),
        (55 - cape_sway, 61),
        (60 - cape_sway, 63),
    ):
        px.put(x, y, (0, 0, 0, 0))
        px.put(x, y - 1, CD)

    # Red scarf / sagum.
    px.fill(18, cy - 10, 46, cy, C)
    px.fill(20, cy - 9, 44, cy - 3, CL)
    px.fill(22, cy - 4, 42, cy + 2, CD)

    # Pauldrons.
    px.ellipse(14, cy + 2, 14, 11, T)
    px.ellipse(50, cy + 2, 14, 11, T)
    px.fill(4, cy - 2, 26, cy + 12, T)
    px.fill(38, cy - 2, 60, cy + 12, T)
    px.fill(6, cy - 2, 18, cy + 4, TL)
    px.fill(46, cy + 4, 58, cy + 12, TD)
    draw_mark(px, 52, cy + 3, scale=1, glow=0)
    px.put(10, cy + 6, BLD)
    px.put(11, cy + 7, BLD)
    px.put(9, cy + 7, RD)
    px.put(8, cy + 4, TX)

    # Lorica bands.
    px.fill(20, cy + 4, 44, 63, T)
    for i, y in enumerate(range(cy + 6, 63, 3)):
        col = TL if i % 2 == 0 else TD
        px.fill(22, y, 42, y, col)
        px.fill(21, y + 1, 43, y + 1, T)
    px.fill(22, cy + 5, 42, cy + 6, TL)
    px.put(24, cy + 12, TX)
    px.put(25, cy + 13, K)
    px.put(38, cy + 16, BLD)

    px.outline_opaque()
    return px.im


GAUNTLET = [
    "   oooo   ",
    "  oOOOOo  ",
    " oOOOOOOo ",
    "oOOOOOOOOo",
    "oOOOOOOOOo",
    "oOOOOOOOOo",
    " oOOOOOOo ",
    "  oOOOOo  ",
    "   o##o   ",
    "    ##    ",
]
PALM = [
    "    oo    ",
    "   oOOo   ",
    "  oOOOO   ",
    " oOOOOO   ",
    "oOOOOOO   ",
    "oOOOOOO   ",
    " oOOOOO   ",
    "  oOOOo   ",
    "   o##    ",
    "    ##    ",
]
G_COLORS = {"o": GX, "O": GT, "#": W}


def draw_gauntlet(px: Pix, x: int, y: int, palm: bool = False) -> None:
    px.stamp(x, y, PALM if palm else GAUNTLET, G_COLORS)


def draw_forearm(px: Pix, x0: int, y0: int, x1: int, y1: int) -> None:
    """Thick steel tube between shoulder and gauntlet."""
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            px.put(x + dx, y + dy, GT if dx == 0 and dy == 0 else GD)
        px.put(x - 2, y, K)
        px.put(x + 2, y, K)


def draw_wave_hand(px: Pix, x: int, y: int) -> None:
    """Large open palm in the navy sky so the wave reads at 48px."""
    palm_cx, palm_cy = x + 7, y + 11
    px.disc(palm_cx, palm_cy, 7, GT)
    px.disc(palm_cx - 1, palm_cy - 1, 3, (210, 216, 220, 255))
    wag = 2 if y <= 4 else (1 if y <= 10 else 0)
    fingers = [(-6, 1), (-2, -1 - wag), (2, -2), (6, wag)]
    for dx, dy in fingers:
        fx = palm_cx + dx
        fy0 = y + 1 + dy
        px.fill(fx - 1, fy0, fx + 1, fy0 + 8, GT)
        px.put(fx, fy0 - 1, GT)
        px.put(fx - 2, fy0 + 2, K)
        px.put(fx + 2, fy0 + 2, K)
        px.put(fx, fy0 + 8, GX)
    # Thumb toward the crest.
    px.fill(palm_cx - 10, palm_cy - 2, palm_cx - 5, palm_cy + 3, GT)
    px.fill(palm_cx - 11, palm_cy, palm_cx - 8, palm_cy + 4, GX)


def draw_shield(px: Pix, cx: int, cy: int, radius: int = 18, glow: int = 0) -> None:
    px.disc(cx, cy, radius + 1, K)
    px.ellipse(cx, cy, radius, int(radius * 1.15), T)
    px.ellipse(cx - 3, cy - 4, int(radius * 0.55), int(radius * 0.6), TL)
    px.ellipse(cx + 4, cy + 4, int(radius * 0.5), int(radius * 0.55), TD)
    # Rim.
    r = radius
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot((x - cx) / 1.0, (y - cy) / 1.15)
            if abs(d - r) < 1.1:
                px.put(x, y, TX if glow else K)
    draw_mark(px, cx, cy + 1, scale=2 if radius >= 16 else 1, glow=glow)
    # Wear.
    px.put(cx - radius + 4, cy - 2, BLD)
    px.put(cx - radius + 5, cy - 1, RD)
    px.put(cx + radius - 3, cy + 6, TX)


def draw_spear(px: Pix, x: int, tip_y: int, fist_y: int) -> None:
    for i, spread in enumerate((0, 1, 2, 1, 0)):
        y = tip_y + i
        for dx in range(-spread, spread + 1):
            px.put(x + dx, y, TL if dx == 0 else T)
        px.put(x - spread - 1, y, K)
        px.put(x + spread + 1, y, K)
    for y in range(tip_y + 5, fist_y):
        px.put(x - 1, y, SPD)
        px.put(x, y, SP)
        px.put(x + 1, y, WD)
        px.put(x - 2, y, K)
        px.put(x + 2, y, K)
    draw_gauntlet(px, x - 4, fist_y - 2)


def compose_bust(pose: Pose) -> Image.Image:
    face = pose.face or Face()
    body = draw_body_layer(pose.shrug, pose.cape_sway)
    head = draw_head_layer(face, pose.crest_sway)
    if abs(pose.head_tilt) > 0.1:
        head = head.rotate(
            pose.head_tilt,
            resample=Image.Resampling.NEAREST,
            center=(32, 28),
            fillcolor=(0, 0, 0, 0),
        )
    out = Image.new("RGBA", (NATIVE, NATIVE), (0, 0, 0, 0))
    out.alpha_composite(body)
    paste_offset(out, head, pose.head_dx, pose.head_dy)
    return out


def apply_extras(im: Image.Image, extras: tuple) -> Image.Image:
    px = Pix()
    px.im = im.copy()
    px.p = px.im.load()
    for extra in extras:
        kind = extra[0]
        if kind == "gauntlet":
            _, x, y, palm = extra
            draw_gauntlet(px, x, y, palm=palm)
        elif kind == "wave_hand":
            _, x, y = extra
            draw_wave_hand(px, x, y)
        elif kind == "palm_out":
            _, x, y, sx, sy = extra
            draw_forearm(px, sx, sy, x + 4, y + 4)
            draw_gauntlet(px, x, y, palm=True)
        elif kind == "shield":
            _, cx, cy, radius, glow = extra
            draw_shield(px, cx, cy, radius=radius, glow=glow)
        elif kind == "spear":
            _, x, tip_y, fist_y = extra
            draw_spear(px, x, tip_y, fist_y)
        elif kind == "mark_only":
            _, cx, cy, scale, glow = extra
            draw_mark(px, cx, cy, scale=scale, glow=glow)
    px.outline_opaque()
    return px.im


def to_emoji(native: Image.Image) -> Image.Image:
    """Nearest-neighbor 64→128 onto opaque navy. No blur."""
    scaled = native.resize((CANVAS, CANVAS), Image.Resampling.NEAREST)
    bg = Image.new("RGBA", (CANVAS, CANVAS), NAVY)
    return Image.alpha_composite(bg, scaled)


# --- clip specs ----------------------------------------------------------------

EMOJI: dict[str, dict] = {
    "galahad_wave": {
        "caption": "Ave.",
        "shortcode": ":galahad_wave:",
        "loop": True,
        "durations": [160, 140, 140, 140, 140, 200],
    },
    "galahad_nod": {
        "caption": "Aye.",
        "shortcode": ":galahad_nod:",
        "loop": True,
        "durations": [180, 140, 160, 280, 160, 180],
    },
    "galahad_shake": {
        "caption": "No.",
        "shortcode": ":galahad_shake:",
        "loop": True,
        "durations": [90, 90, 90, 90, 90, 90, 110, 160],
    },
    "galahad_shrug": {
        "caption": "Not my cohort.",
        "shortcode": ":galahad_shrug:",
        "loop": True,
        "durations": [160, 140, 320, 240, 160, 180],
    },
    "galahad_salute": {
        "caption": "Affirmative.",
        "shortcode": ":galahad_salute:",
        "loop": True,
        "durations": [140, 120, 280, 200, 160, 180],
    },
    "galahad_hold": {
        "caption": "Hold.",
        "shortcode": ":galahad_hold:",
        "loop": True,
        "durations": [180, 140, 240, 200, 180, 200],
    },
    "galahad_victory": {
        "caption": "The line held.",
        "shortcode": ":galahad_victory:",
        "loop": True,
        "durations": [120, 100, 260, 180, 160, 200],
    },
    "galahad_facepalm": {
        "caption": "The line, and my patience.",
        "shortcode": ":galahad_facepalm:",
        "loop": True,
        "durations": [140, 120, 140, 360, 240, 180],
    },
    "galahad_think": {
        "caption": "…orders?",
        "shortcode": ":galahad_think:",
        "loop": True,
        "durations": [180, 160, 280, 220, 180, 200],
    },
    "galahad_shocked": {
        "caption": "The line— what.",
        "shortcode": ":galahad_shocked:",
        "loop": False,
        "durations": [120, 80, 90, 280, 180, 200],
    },
    "galahad_laugh": {
        "caption": "Hnh.",
        "shortcode": ":galahad_laugh:",
        "loop": True,
        "durations": [140, 140, 140, 180, 140, 200],
    },
    "galahad_mark": {
        "caption": "The Mark is a receipt.",
        "shortcode": ":galahad_mark:",
        "loop": True,
        "durations": [180, 140, 160, 220, 160, 200],
    },
}


def _bust(pose: Pose) -> Image.Image:
    im = compose_bust(pose)
    if pose.extras:
        im = apply_extras(im, pose.extras)
    return to_emoji(im)


def author_wave() -> list[Image.Image]:
    # Palm lives in the navy sky so steel reads against #0b1220, not teal armor.
    keys = [
        Pose(crest_sway=0, extras=(("wave_hand", 42, 16),)),
        Pose(crest_sway=1, extras=(("wave_hand", 44, 6),)),
        Pose(crest_sway=0, extras=(("wave_hand", 45, 1),)),
        Pose(crest_sway=-1, extras=(("wave_hand", 38, 1),)),
        Pose(crest_sway=0, extras=(("wave_hand", 45, 1),)),
        Pose(crest_sway=0, extras=(("wave_hand", 44, 6),)),
    ]
    return [_bust(p) for p in keys]


def author_nod() -> list[Image.Image]:
    offsets = [0, 2, 5, 6, 3, 0]
    frames = []
    for dy in offsets:
        frames.append(
            _bust(
                Pose(
                    head_dy=dy,
                    crest_sway=1 if dy >= 5 else 0,
                    face=Face(eyes="closed" if dy >= 5 else "open", mouth="flat"),
                )
            )
        )
    return frames


def author_shake() -> list[Image.Image]:
    xs = [0, -5, -7, -2, 5, 7, 2, 0]
    frames = []
    for dx in xs:
        frames.append(
            _bust(
                Pose(
                    head_dx=dx,
                    crest_sway=1 if dx > 0 else (-1 if dx < 0 else 0),
                    face=Face(brow=1, mouth="frown"),
                )
            )
        )
    return frames


def author_shrug() -> list[Image.Image]:
    steps = [
        Pose(),
        Pose(shrug=2, head_tilt=6, extras=(("palm_out", 0, 24, 14, 44), ("palm_out", 52, 24, 50, 44))),
        Pose(
            shrug=4,
            head_tilt=10,
            face=Face(brow=-1, mouth="flat"),
            extras=(("palm_out", 0, 18, 12, 42), ("palm_out", 52, 18, 52, 42)),
        ),
        Pose(
            shrug=4,
            head_tilt=10,
            face=Face(brow=-1, mouth="flat"),
            extras=(("palm_out", 0, 18, 12, 42), ("palm_out", 52, 18, 52, 42)),
        ),
        Pose(shrug=2, head_tilt=6, extras=(("palm_out", 0, 24, 14, 44), ("palm_out", 52, 24, 50, 44))),
        Pose(),
    ]
    return [_bust(p) for p in steps]


def author_salute() -> list[Image.Image]:
    steps = [
        Pose(),
        Pose(extras=(("gauntlet", 40, 18, False),)),
        Pose(head_dy=1, extras=(("gauntlet", 38, 12, False), ("spear", 6, 0, 26))),
        Pose(head_dy=2, face=Face(eyes="closed"), extras=(("gauntlet", 38, 12, False), ("spear", 6, 0, 26))),
        Pose(head_dy=1, extras=(("gauntlet", 38, 12, False), ("spear", 6, 0, 26))),
        Pose(extras=(("gauntlet", 38, 12, False), ("spear", 6, 2, 28))),
    ]
    return [_bust(p) for p in steps]


def author_hold() -> list[Image.Image]:
    # Shield plants toward camera; crest + visor stay above the rim.
    steps = [
        Pose(extras=(("shield", 48, 54, 12, 0),)),
        Pose(head_dy=1, extras=(("shield", 40, 56, 14, 0),)),
        Pose(head_dy=1, extras=(("shield", 34, 56, 16, 1),)),
        Pose(head_dx=-1, extras=(("shield", 34, 56, 16, 2),)),
        Pose(extras=(("shield", 34, 56, 16, 1),)),
        Pose(extras=(("shield", 34, 56, 16, 0),)),
    ]
    return [_bust(p) for p in steps]


def author_victory() -> list[Image.Image]:
    steps = [
        Pose(face=Face(mouth="flat")),
        Pose(head_dy=2, shrug=1, face=Face(mouth="grin")),
        Pose(
            head_dy=-2,
            crest_sway=1,
            face=Face(mouth="grin", eyes="closed"),
            extras=(("spear", 54, 0, 22),),
        ),
        Pose(
            head_dy=-1,
            crest_sway=1,
            face=Face(mouth="grin"),
            extras=(("spear", 54, 0, 20),),
        ),
        Pose(crest_sway=0, face=Face(mouth="grin"), extras=(("spear", 54, 0, 22),)),
        Pose(face=Face(mouth="grin"), extras=(("spear", 54, 2, 24),)),
    ]
    return [_bust(p) for p in steps]


def author_facepalm() -> list[Image.Image]:
    steps = [
        Pose(face=Face(brow=1, mouth="frown")),
        Pose(head_dy=1, extras=(("gauntlet", 42, 14, False),)),
        Pose(head_dy=3, head_tilt=-8, extras=(("gauntlet", 26, 18, False),)),
        Pose(
            head_dy=5,
            head_tilt=-10,
            face=Face(eyes="closed", brow=1, mouth="frown"),
            extras=(("gauntlet", 24, 20, False),),
        ),
        Pose(
            head_dy=5,
            head_tilt=-10,
            face=Face(eyes="closed", brow=1, mouth="frown"),
            extras=(("gauntlet", 25, 21, False),),
        ),
        Pose(
            head_dy=4,
            head_tilt=-8,
            face=Face(eyes="closed", mouth="frown"),
            extras=(("gauntlet", 24, 20, False),),
        ),
    ]
    return [_bust(p) for p in steps]


def author_think() -> list[Image.Image]:
    steps = [
        Pose(face=Face(brow=-1)),
        Pose(head_tilt=8, face=Face(brow=-1, mouth="flat"), extras=(("gauntlet", 40, 34, False),)),
        Pose(
            head_tilt=12,
            head_dx=1,
            face=Face(brow=-1, eyes="open", mouth="frown"),
            extras=(("gauntlet", 38, 36, False),),
        ),
        Pose(
            head_tilt=10,
            face=Face(brow=-1, eyes="closed", mouth="flat"),
            extras=(("gauntlet", 38, 36, False),),
        ),
        Pose(
            head_tilt=12,
            head_dx=1,
            face=Face(brow=-1, mouth="flat"),
            extras=(("gauntlet", 38, 37, False),),
        ),
        Pose(head_tilt=8, face=Face(brow=-1), extras=(("gauntlet", 40, 34, False),)),
    ]
    return [_bust(p) for p in steps]


def author_shocked() -> list[Image.Image]:
    steps = [
        Pose(),
        Pose(head_dx=-1, head_dy=-1, face=Face(eyes="wide", mouth="o", brow=-1)),
        Pose(head_dx=2, head_dy=-2, face=Face(eyes="magenta", mouth="o", brow=-1)),
        Pose(head_dx=-1, face=Face(eyes="magenta", mouth="o", brow=-1)),
        Pose(face=Face(eyes="wide", mouth="o")),
        Pose(face=Face(eyes="open", mouth="flat")),
    ]
    return [_bust(p) for p in steps]


def author_laugh() -> list[Image.Image]:
    steps = [
        Pose(face=Face(mouth="grin")),
        Pose(head_dy=1, shrug=1, face=Face(eyes="closed", mouth="grin")),
        Pose(head_dy=0, shrug=0, face=Face(eyes="closed", mouth="open")),
        Pose(head_dy=2, shrug=2, crest_sway=1, face=Face(eyes="closed", mouth="open")),
        Pose(head_dy=0, face=Face(eyes="closed", mouth="grin")),
        Pose(face=Face(mouth="grin")),
    ]
    return [_bust(p) for p in steps]


def author_mark() -> list[Image.Image]:
    """Shield-Mark close-up — emblem pulse, no tiny full-body."""
    frames = []
    glows = [0, 1, 2, 2, 1, 0]
    radii = [24, 24, 25, 25, 24, 24]
    for glow, r in zip(glows, radii):
        px = Pix()
        # Crest peek so the pack still reads as Galahad.
        draw_crest(px, 32, 0, height=14, sway=glow - 1)
        draw_shield(px, 32, 36, radius=r, glow=glow)
        px.outline_opaque()
        frames.append(to_emoji(px.im))
    return frames


AUTHORS = {
    "galahad_wave": author_wave,
    "galahad_nod": author_nod,
    "galahad_shake": author_shake,
    "galahad_shrug": author_shrug,
    "galahad_salute": author_salute,
    "galahad_hold": author_hold,
    "galahad_victory": author_victory,
    "galahad_facepalm": author_facepalm,
    "galahad_think": author_think,
    "galahad_shocked": author_shocked,
    "galahad_laugh": author_laugh,
    "galahad_mark": author_mark,
}


def save_png_frames(name: str, frames: list[Image.Image]) -> None:
    dest = FRAME_ROOT / name
    if dest.exists():
        for old in dest.glob("*.png"):
            old.unlink()
    dest.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        frame.save(dest / f"{i:02d}.png")


def load_png_frames(name: str) -> list[Image.Image]:
    dest = FRAME_ROOT / name
    paths = sorted(dest.glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"No PNG frames in {dest}")
    return [Image.open(p).convert("RGBA") for p in paths]


def quantize_sequence(frames: list[Image.Image]) -> list[Image.Image]:
    if not frames:
        raise ValueError("No frames to quantize")
    w, h = frames[0].size
    for i, frame in enumerate(frames):
        if frame.size != (w, h):
            raise ValueError(f"Frame {i} size {frame.size} != {w}x{h}; refusing to resize")
        if (w, h) != (CANVAS, CANVAS):
            raise ValueError(f"Frame {i} is {w}x{h}, expected {CANVAS}x{CANVAS}")
    sheet = Image.new("RGB", (w * len(frames), h))
    for i, frame in enumerate(frames):
        sheet.paste(frame.convert("RGB"), (i * w, 0))
    pal = sheet.quantize(
        colors=64,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )
    return [pal.crop((i * w, 0, (i + 1) * w, h)) for i in range(len(frames))]


def write_gif(dest: Path, frames: list[Image.Image], durations: list[int], loop: bool) -> None:
    palettes = quantize_sequence(frames)
    first, rest = palettes[0], palettes[1:]
    first.save(
        dest,
        save_all=True,
        append_images=rest,
        duration=durations,
        loop=0 if loop else 1,
        disposal=2,
        optimize=True,
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
            f"loop={loop}  {path.stat().st_size:6d} B  "
            f"{path.stat().st_size / 1024:5.1f} KB  dur={durs}"
        )


def author_all() -> None:
    FRAME_ROOT.mkdir(parents=True, exist_ok=True)
    for name, fn in AUTHORS.items():
        frames = fn()
        spec = EMOJI[name]
        if len(frames) != len(spec["durations"]):
            raise RuntimeError(
                f"{name}: {len(frames)} frames vs {len(spec['durations'])} durations"
            )
        save_png_frames(name, frames)
        print(f"  authored {name:22}  {len(frames)} PNG  {CANVAS}x{CANVAS}")


def build_gifs() -> list[tuple[str, int]]:
    GIF_DIR.mkdir(parents=True, exist_ok=True)
    sizes: list[tuple[str, int]] = []
    for name, spec in EMOJI.items():
        frames = load_png_frames(name)
        durations = spec["durations"]
        if len(frames) != len(durations):
            raise RuntimeError(f"{name}: {len(frames)} PNGs vs {len(durations)} durations")
        dest = GIF_DIR / f"{name}.gif"
        write_gif(dest, frames, durations, bool(spec["loop"]))
        print(f"  {inspect_gif(dest)}")
        n = dest.stat().st_size
        sizes.append((dest.name, n))
        if n > MAX_BYTES:
            raise SystemExit(f"FAIL {dest.name}: {n} bytes exceeds Discord 256 KB cap")
        if n > WARN_BYTES:
            print(f"    warning: {dest.name} exceeds 150 KB target ({n / 1024:.1f} KB)", file=sys.stderr)
    return sizes


def write_contact_sheet() -> Path:
    """Still-frame sheet of frame 00 for visual QA (not uploaded to Discord)."""
    names = list(EMOJI)
    cols = 4
    rows = math.ceil(len(names) / cols)
    pad = 8
    cell = CANVAS + pad
    sheet = Image.new("RGB", (cols * cell + pad, rows * cell + pad), NAVY[:3])
    for i, name in enumerate(names):
        path = FRAME_ROOT / name / "00.png"
        im = Image.open(path).convert("RGB")
        r, c = divmod(i, cols)
        sheet.paste(im, (pad + c * cell, pad + r * cell))
    dest = GIF_DIR / "_preview_sheet.png"
    sheet.save(dest)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author",
        action="store_true",
        help="Rebuild PNG frames from original bust drawings, then GIFs",
    )
    parser.add_argument(
        "--sheet",
        action="store_true",
        help="Write _preview_sheet.png of first frames",
    )
    args = parser.parse_args()
    print(f"Frames:  {FRAME_ROOT}")
    print(f"GIFs:    {GIF_DIR}")
    print(f"Canvas:  {CANVAS}x{CANVAS} from {NATIVE}x{NATIVE} ×{SCALE} NN")
    print(f"Background: #{NAVY[0]:02x}{NAVY[1]:02x}{NAVY[2]:02x} (opaque navy, pack-wide)")
    print()
    if args.author:
        print("Authoring original bust PNGs (not rescaled canon sheets)…")
        author_all()
        print()
    print("Building Discord GIFs…")
    build_gifs()
    if args.sheet:
        dest = write_contact_sheet()
        print(f"\nPreview sheet: {dest}")
    print("\nDone. Original Galahad busts; no walk2/run/reaction rescale.")


if __name__ == "__main__":
    main()
