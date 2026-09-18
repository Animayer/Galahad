#!/usr/bin/env python3
"""Composite the Galahad meme pack from existing Discord emotes + reaction stills.

Look-unchanged (Ryan 2026-09-18): do not regenerate, redraw, restyle, recolor,
upscale-with-AI, or invent sprites/emotes. This script only:

- loads existing PNGs (Discord emotes, reaction frames, canon sprites)
- knocks out sheet checker / tile-fill leftovers (no redraw)
- flattens every source onto opaque navy #0b1220 before layout
- nearest-neighbor resizes
- lays out solid navy panels, arrows, and caption bars
- writes 1080×1080 1:1 RGB PNGs

Usage:
    python3 scripts/make-galahad-memes.py
    python3 scripts/make-galahad-memes.py --set a
    python3 scripts/make-galahad-memes.py --set all
"""

from __future__ import annotations

import argparse
import html
import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required. Install with: python3 -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
EMOJI_DIR = ROOT / "assets" / "discord-emojis"
REACTION_DIR = ROOT / "assets" / "reactions" / "frames"
SPRITE_DIR = ROOT / "assets" / "roman_legionary" / "frames_96"
GIF_REACTION_DIR = ROOT / "assets" / "gifs" / "reactions"
OUT_DIR = ROOT / "assets" / "memes"

SIZE = 1080
NAVY = (11, 18, 32, 255)  # #0b1220
PANEL = (18, 26, 43, 255)
PANEL_2 = (15, 22, 38, 255)
BORDER = (36, 48, 73, 255)
CREAM = (232, 238, 252, 255)
MUTED = (139, 155, 184, 255)
INK = (8, 12, 20, 255)
CREST = (196, 84, 84, 255)
HOLD = (142, 199, 255, 255)
SIGN = (28, 38, 58, 255)
SIGN_EDGE = (214, 196, 140, 255)
TABLE = (22, 30, 46, 255)
BAR_FILL = (8, 14, 26, 235)
BAR_H = 120

# In-tile captions (NANI/BOOM/COOL/…) that sit in the top band of some
# Discord tiles. Extra source-pixel crop after fill knockout; crest-bearing
# busts are not listed. Keys are filenames in assets/discord-emojis/.
TOP_LABEL_CROP_PX = {
    "galahad_exploding.png": 36,
}

# Caption set A = default files. Set B = *_b alts.
# Voice: duty-first, dry understatement, Roman mouth — not shiny holy-knight.
FORMATS = [
    {
        "id": "01",
        "slug": "drake",
        "title": "Drake",
        "builder": "drake",
        "a": {
            "no": "Shiny paladin AU",
            "yes": "Hold the line.",
        },
        "b": {
            "no": "Miracle speech",
            "yes": "The watch. Then supper.",
        },
    },
    {
        "id": "02",
        "slug": "distracted",
        "title": "Distracted boyfriend",
        "builder": "distracted",
        "a": {
            "gf": "Glory",
            "bf": "Galahad",
            "other": "The line",
        },
        "b": {
            "gf": "The glory thread",
            "bf": "Galahad",
            "other": "Standing orders",
        },
    },
    {
        "id": "03",
        "slug": "thisisfine",
        "title": "This is fine",
        "builder": "this_is_fine",
        "a": {
            "emote": "galahad_meditating.png",
            "line": "This is fine.",
            "sub": "The raiders are a drill.",
        },
        "b": {
            "emote": "galahad_drinking.png",
            "line": "This is fine.",
            "sub": "The watch continues.",
        },
    },
    {
        "id": "04",
        "slug": "brain",
        "title": "Expanding brain",
        "builder": "brain",
        "a": {
            "lines": [
                "Ask for a miracle",
                "Read the standing orders",
                "Pray the line holds",
                "Hold. That's the brief.",
            ],
        },
        "b": {
            "lines": [
                "Hero arc",
                "Tactics",
                "The oath",
                "Duty. Then sleep.",
            ],
        },
    },
    {
        "id": "05",
        "slug": "yelling",
        "title": "Woman yelling / cat",
        "builder": "yelling",
        "a": {
            "left": "THE EAST GATE",
            "right": "…",
            "quiet": "galahad_shrug.png",
        },
        "b": {
            "left": "every shiny AU in the replies",
            "right": "The line, and my patience.",
            "quiet": "galahad_facepalm.png",
        },
    },
    {
        "id": "06",
        "slug": "waiting",
        "title": "Waiting",
        "builder": "waiting",
        "a": {
            "emote": "galahad_reading.png",
            "top": "GALAHAD WAITING FOR",
            "bot": "THE LINE TO BREAK",
        },
        "b": {
            # ghostly is a gray bust that collides with sheet-fill knockout;
            # shrug is a cleaner sibling bust from the same pack.
            "emote": "galahad_shrug.png",
            "top": "DAY FOUR HUNDRED",
            "bot": "OF THE WATCH",
        },
    },
    {
        "id": "07",
        "slug": "changemind",
        "title": "Change my mind",
        "builder": "change_mind",
        "a": {
            "emote": "galahad_sunglasses.png",
            "sign": "Glory is optional.\nThe line is not.",
        },
        "b": {
            "emote": "galahad_smug.png",
            "sign": "Hold is the whole\ndoctrine.",
        },
    },
    {
        "id": "08",
        "slug": "understatement",
        "title": "Understatement punch",
        "builder": "understatement",
        "a": {
            "setup": "The east wall is gone.",
            "punch": "Hold.",
            "react": "grin",
        },
        "b": {
            "setup": "They brought a dragon.",
            "punch": "Noted.",
            "react": "crest",
        },
    },
    {
        "id": "09",
        "slug": "trade",
        "title": "Trade offer",
        "builder": "trade",
        "a": {
            "give_label": "I RECEIVE",
            "give": "The duty",
            "get_label": "YOU RECEIVE",
            "get": "A closed gate",
            "right": "cheer",
        },
        "b": {
            "give_label": "I RECEIVE",
            "give": "No speeches",
            "get_label": "YOU RECEIVE",
            "get": "The line, held",
            "right": "block",
        },
    },
    {
        "id": "10",
        "slug": "bus",
        "title": "Bus guy",
        "builder": "bus",
        "a": {
            "emote": "galahad_scared.png",
            "thought": "Ah. Scripture.",
            "sign": "HOLD\nTHE LINE",
        },
        "b": {
            "emote": "galahad_shocked.png",
            "thought": "The brief.",
            "sign": "IF THE LINE HOLDS,\nWE ARGUE LATER",
        },
    },
    {
        "id": "11",
        "slug": "pigeon",
        "title": "Is this a pigeon",
        "builder": "pigeon",
        "a": {
            "mode": "confused_clown",
            "caption": "Is this a paladin?",
            "label": "shiny AU",
        },
        "b": {
            "mode": "clown_rage",
            "caption": "Is this the chosen one?",
            "label": "That's a no\nfrom the cohort.",
        },
    },
    {
        "id": "12",
        "slug": "walkoff",
        "title": "Walk of shame",
        "builder": "walkoff",
        "a": {
            "line": "We're done here.",
            "sub": "Leaving the shiny AU thread.",
        },
        "b": {
            "line": "The encore was a speech.",
            "sub": "I had a wall.",
        },
    },
]


def _font_path() -> Path:
    candidates = [
        Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError("No readable sans Bold TTF found")


FONT_PATH = _font_path()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def canvas() -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), NAVY)


def nn_resize(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    return im.resize(size, Image.Resampling.NEAREST)


def nn_scale(im: Image.Image, factor: int) -> Image.Image:
    w, h = im.size
    return nn_resize(im, (w * factor, h * factor))


def nn_fit(im: Image.Image, box: tuple[int, int]) -> Image.Image:
    bw, bh = box
    iw, ih = im.size
    scale = min(bw / iw, bh / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    return nn_resize(im, (nw, nh))


def flatten_rgba(im: Image.Image, bg: tuple[int, int, int, int] = NAVY) -> Image.Image:
    """Composite RGBA onto an opaque background. Alpha never reaches layout."""
    out = Image.new("RGBA", im.size, bg)
    out.alpha_composite(im.convert("RGBA"))
    return out


def _is_sheet_fill(r: int, g: int, b: int) -> bool:
    """Ryan-sheet leftover: light checker / muted blue-gray tile fill."""
    sat = max(r, g, b) - min(r, g, b)
    lum = (r + g + b) / 3
    if sat <= 40 and 85 <= lum <= 230:
        return True
    # bluish gray like (120, 136, 151)
    if sat <= 50 and 90 <= lum <= 190 and b >= g - 6 and g >= r - 4:
        return True
    return False


def _is_tight_navy(r: int, g: int, b: int, thr: int = 8) -> bool:
    """GIF/canvas navy only. Tight so legionary outlines are not punched."""
    return abs(r - NAVY[0]) + abs(g - NAVY[1]) + abs(b - NAVY[2]) <= thr


def flood_knockout(
    im: Image.Image,
    *,
    punch_sheet_fill: bool = False,
    punch_navy: bool = False,
    navy_thr: int = 8,
) -> Image.Image:
    """Punch background pixels reachable from transparent pixels / the border.

    Floods through sheet-fill / checker and (optionally) quantized navy so
    interior outlines and bust pixels stay put.
    """
    rgba = im.convert("RGBA").copy()
    w, h = rgba.size
    px = rgba.load()
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def punchable(r: int, g: int, b: int, a: int) -> bool:
        if a <= 16:
            return True
        if punch_navy and _is_tight_navy(r, g, b, navy_thr):
            return True
        if punch_sheet_fill and _is_sheet_fill(r, g, b):
            return True
        return False

    def seed(x: int, y: int) -> None:
        if visited[y][x]:
            return
        visited[y][x] = True
        q.append((x, y))

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            border = x == 0 or y == 0 or x == w - 1 or y == h - 1
            if a <= 16:
                seed(x, y)
            elif border and punchable(r, g, b, a):
                seed(x, y)

    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        if not punchable(r, g, b, a):
            continue
        if a > 16:
            px[x, y] = (r, g, b, 0)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                nr, ng, nb, na = px[nx, ny]
                if punchable(nr, ng, nb, na):
                    seed(nx, ny)
    return rgba


def _components(im: Image.Image) -> list[dict]:
    w, h = im.size
    px = im.load()
    seen = [[False] * w for _ in range(h)]
    comps: list[dict] = []
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for y in range(h):
        for x in range(w):
            if seen[y][x] or px[x, y][3] <= 16:
                continue
            q: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            cells: list[tuple[int, int]] = []
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and px[nx, ny][3] > 16:
                        seen[ny][nx] = True
                        q.append((nx, ny))
            xs = [p[0] for p in cells]
            ys = [p[1] for p in cells]
            comps.append(
                {
                    "n": len(cells),
                    "bbox": (min(xs), min(ys), max(xs) + 1, max(ys) + 1),
                    "cells": cells,
                }
            )
    comps.sort(key=lambda c: -c["n"])
    return comps


def drop_label_blobs(im: Image.Image, band: int = 36, max_blob: int = 320, max_h: int = 28) -> Image.Image:
    """Drop leftover NANI/BOOM/COOL letter blobs in the top band. No redraw."""
    out = im.copy()
    px = out.load()
    for c in _components(out):
        if c["n"] >= 400:
            continue
        x0, y0, x1, y1 = c["bbox"]
        bh = y1 - y0
        if y0 <= band and bh <= max_h and c["n"] <= max_blob:
            for x, y in c["cells"]:
                r, g, b, _a = px[x, y]
                px[x, y] = (r, g, b, 0)
    return out


def crop_content(im: Image.Image, pad: int = 2) -> Image.Image:
    """BBox crop of remaining opaque pixels."""
    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 16:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if maxx < 0:
        return rgba
    return rgba.crop(
        (
            max(0, minx - pad),
            max(0, miny - pad),
            min(w, maxx + 1 + pad),
            min(h, maxy + 1 + pad),
        )
    )


def prepare_emote(name: str) -> Image.Image:
    """Discord tile → bust on opaque navy. Existing pixels only."""
    path = EMOJI_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing Discord emote: {path}")
    im = Image.open(path).convert("RGBA")
    im = flood_knockout(im, punch_sheet_fill=True, punch_navy=False)
    im = drop_label_blobs(im)
    extra = TOP_LABEL_CROP_PX.get(name, 0)
    if extra:
        im = im.crop((0, min(extra, im.size[1] - 1), im.size[0], im.size[1]))
    im = crop_content(im, pad=2)
    # Keep alpha. Canvas is already navy/panel; flattening here would stamp a
    # navy rectangle onto lighter panels.
    return im


def prepare_still(im: Image.Image) -> Image.Image:
    """Reaction GIF / canon sprite still → sprite with navy matte punched."""
    rgba = flatten_rgba(im.convert("RGBA"), NAVY)
    rgba = flood_knockout(rgba, punch_sheet_fill=False, punch_navy=True, navy_thr=16)
    return crop_content(rgba, pad=2)


def load_reaction_frame(beat: str, frame: str) -> Image.Image:
    png = REACTION_DIR / beat / frame
    if png.is_file():
        return prepare_still(Image.open(png).convert("RGBA"))
    gif = GIF_REACTION_DIR / f"{beat}.gif"
    if not gif.is_file():
        raise FileNotFoundError(f"Missing reaction still: {png} or {gif}")
    im = Image.open(gif)
    idx = int(Path(frame).stem)
    n_frames = getattr(im, "n_frames", 1)
    im.seek(min(idx, n_frames - 1))
    # Flatten onto navy *before* any crop so GIF matte/index never survives.
    return prepare_still(flatten_rgba(im.convert("RGBA"), NAVY))


def load_sprite(name: str) -> Image.Image:
    path = SPRITE_DIR / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing canon sprite: {path}")
    return prepare_still(Image.open(path).convert("RGBA"))


def crop_mark(sprite: Image.Image) -> Image.Image:
    """Tight crop of helm / visor (the Mark) from an existing cast pose."""
    return sprite.crop((34, 6, 70, 42))


def paste(base: Image.Image, im: Image.Image, xy: tuple[int, int], anchor: str = "lt") -> None:
    x, y = xy
    w, h = im.size
    if "m" in anchor[0]:
        x -= w // 2
    elif anchor[0] == "r":
        x -= w
    if len(anchor) > 1:
        if anchor[1] == "m":
            y -= h // 2
        elif anchor[1] == "b":
            y -= h
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    base.alpha_composite(im, (int(x), int(y)))


def paste_in(base: Image.Image, im: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    fitted = nn_fit(im.convert("RGBA"), (w, h))
    px = x + (w - fitted.size[0]) // 2
    py = y + (h - fitted.size[1]) // 2
    base.alpha_composite(fitted, (px, py))


def draw_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill=PANEL,
    outline=BORDER,
    width: int = 4,
    radius: int = 18,
) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> str:
    paragraphs = text.split("\n")
    lines: list[str] = []
    for para in paragraphs:
        words = para.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if fnt.getlength(trial) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return "\n".join(lines)


def fit_font(text: str, max_width: int, max_height: int, start: int, min_size: int = 22) -> tuple[ImageFont.FreeTypeFont, str]:
    size = start
    while size >= min_size:
        fnt = font(size)
        wrapped = wrap_text(text, fnt, max_width)
        bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).multiline_textbbox(
            (0, 0), wrapped, font=fnt, spacing=6, align="center"
        )
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if tw <= max_width and th <= max_height:
            return fnt, wrapped
        size -= 2
    fnt = font(min_size)
    return fnt, wrap_text(text, fnt, max_width)


def text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    max_width: int,
    max_height: int,
    start: int,
    fill=CREAM,
    stroke: int = 2,
    stroke_fill=INK,
    align: str = "center",
    anchor: str = "mm",
) -> None:
    fnt, wrapped = fit_font(text, max_width, max_height, start)
    draw.multiline_text(
        xy,
        wrapped,
        font=fnt,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
        align=align,
        anchor=anchor,
        spacing=8,
    )


def caption_bar(
    im: Image.Image,
    y0: int,
    y1: int,
    text: str,
    *,
    fill=None,
    start: int = 56,
    x0: int = 0,
    x1: int = SIZE,
    color=CREAM,
) -> None:
    """Semi-opaque navy/black bar + white sans. Never draws on the bust."""
    draw = ImageDraw.Draw(im)
    draw.rectangle((x0, y0, x1, y1), fill=fill or BAR_FILL)
    text_block(
        draw,
        ((x0 + x1) // 2, (y0 + y1) // 2),
        text,
        max_width=(x1 - x0) - 48,
        max_height=y1 - y0 - 16,
        start=start,
        fill=color,
        stroke=2,
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill=CREAM, width: int = 10) -> None:
    draw.line([start, end], fill=fill, width=width)
    ang_x = end[0] - start[0]
    ang_y = end[1] - start[1]
    length = max((ang_x * ang_x + ang_y * ang_y) ** 0.5, 1)
    ux, uy = ang_x / length, ang_y / length
    px, py = -uy, ux
    tip = end
    left = (int(tip[0] - ux * 28 + px * 16), int(tip[1] - uy * 28 + py * 16))
    right = (int(tip[0] - ux * 28 - px * 16), int(tip[1] - uy * 28 - py * 16))
    draw.polygon([tip, left, right], fill=fill)


# --- builders --------------------------------------------------------------

def build_drake(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    mid_top = BAR_H + 10
    mid = SIZE // 2
    mid_bot = SIZE - BAR_H - 10
    draw_panel(draw, (24, mid_top, SIZE - 24, mid - 8), fill=PANEL)
    draw_panel(draw, (24, mid + 8, SIZE - 24, mid_bot), fill=PANEL_2)
    paste_in(im, prepare_emote("galahad_thumbs_down.png"), (48, mid_top + 16, SIZE - 96, mid - mid_top - 40))
    if caps.get("use_hold"):
        hold = load_reaction_frame("hold_the_line", "03.png")
        paste_in(im, nn_scale(hold, 6), (48, mid + 24, SIZE - 96, mid_bot - mid - 40))
    else:
        paste_in(im, prepare_emote("galahad_thumbs_up.png"), (48, mid + 24, SIZE - 96, mid_bot - mid - 40))
    caption_bar(im, 0, BAR_H, caps["no"], start=58, color=CREST)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["yes"], start=58, color=HOLD)
    return im


def build_distracted(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, BAR_H + 8, SIZE - 24, SIZE - BAR_H - 8))
    third = SIZE // 3
    paste_in(im, prepare_emote("galahad_rage.png"), (36, BAR_H + 24, third - 48, SIZE - 2 * BAR_H - 56))
    paste_in(im, prepare_emote("galahad_grin.png"), (third + 12, BAR_H + 24, third - 24, SIZE - 2 * BAR_H - 56))
    paste_in(im, prepare_emote("galahad_smug.png"), (2 * third + 12, BAR_H + 24, third - 48, SIZE - 2 * BAR_H - 56))
    arrow(draw, (2 * third - 20, SIZE // 2), (2 * third + 16, SIZE // 2 - 20), fill=HOLD, width=10)
    caption_bar(im, 0, BAR_H, "THE OATH", start=40, color=MUTED)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["gf"], start=36, x0=0, x1=third, color=CREST)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["bf"], start=36, x0=third, x1=2 * third, color=MUTED)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["other"], start=36, x0=2 * third, x1=SIZE, color=HOLD)
    return im


def build_this_is_fine(caps: dict) -> Image.Image:
    im = canvas()
    fire = nn_scale(prepare_emote("galahad_exploding.png"), 3)
    paste(im, fire, (8, BAR_H + 8))
    paste(im, fire, (SIZE - 8, BAR_H + 8), "rt")
    paste(im, fire, (8, SIZE - BAR_H - 8), "lb")
    paste(im, fire, (SIZE - 8, SIZE - BAR_H - 8), "rb")
    draw = ImageDraw.Draw(im)
    # Navy plate so explosion tiles never cover the seated bust.
    draw.rounded_rectangle((200, 200, 880, 860), radius=28, fill=NAVY, outline=BORDER, width=6)
    paste_in(im, prepare_emote(caps["emote"]), (230, 230, 620, 610))
    caption_bar(im, 0, BAR_H, caps["line"], start=64)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["sub"], start=42)
    return im


def build_brain(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    emotes = [
        "galahad_confused.png",
        "galahad_reading.png",
        "galahad_praying.png",
        "galahad_smug.png",
    ]
    fills = [
        (16, 22, 34, 255),
        (20, 28, 44, 255),
        (26, 36, 56, 255),
        (34, 48, 74, 255),
    ]
    row_h = SIZE // 4
    bar = 78
    for i, (emote, line, fill) in enumerate(zip(emotes, caps["lines"], fills)):
        y0 = i * row_h
        draw.rectangle((0, y0, SIZE, y0 + row_h), fill=fill)
        if i:
            draw.line((0, y0, SIZE, y0), fill=BORDER, width=3)
        brain = 16 + i * 12
        bx, by = 86, y0 + (row_h - bar) // 2
        draw.rounded_rectangle(
            (bx - brain, by - brain, bx + brain, by + brain),
            radius=6,
            outline=HOLD if i == 3 else MUTED,
            width=3,
        )
        paste_in(im, prepare_emote(emote), (150, y0 + 6, 300, row_h - bar - 12))
        caption_bar(
            im,
            y0 + row_h - bar,
            y0 + row_h,
            line,
            start=40,
            color=CREAM if i < 3 else HOLD,
        )
    return im


def build_yelling(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (20, 20, SIZE // 2 - 10, SIZE - BAR_H - 12), fill=(42, 24, 28, 255), outline=CREST)
    draw_panel(draw, (SIZE // 2 + 10, 20, SIZE - 20, SIZE - BAR_H - 12), fill=PANEL)
    paste_in(im, prepare_emote("galahad_rage.png"), (36, 80, 508, 720))
    paste_in(im, prepare_emote(caps["quiet"]), (SIZE // 2 + 26, 80, 508, 720))
    caption_bar(im, SIZE - BAR_H, SIZE, caps["left"], start=36, x0=0, x1=SIZE // 2, color=CREST)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["right"], start=36, x0=SIZE // 2, x1=SIZE, color=MUTED)
    return im


def build_waiting(caps: dict) -> Image.Image:
    im = canvas()
    paste_in(im, prepare_emote(caps["emote"]), (140, BAR_H + 20, 800, SIZE - 2 * BAR_H - 40))
    caption_bar(im, 0, BAR_H, caps["top"], start=52)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["bot"], start=52)
    return im


def build_change_mind(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 780, SIZE, SIZE - BAR_H), fill=TABLE)
    draw.line((0, 780, SIZE, 780), fill=BORDER, width=6)
    paste_in(im, prepare_emote(caps["emote"]), (270, BAR_H + 8, 540, 430))
    # The table sign is itself a caption bar (format chrome), not face overlay.
    draw_panel(draw, (160, 500, 920, 770), fill=SIGN, outline=SIGN_EDGE, width=8, radius=8)
    caption_bar(im, 500, 770, caps["sign"], start=48, x0=168, x1=912, fill=SIGN)
    mark = nn_scale(crop_mark(Image.open(SPRITE_DIR / "cast_2.png").convert("RGBA")), 4)
    paste(im, mark, (118, 840), "mm")
    caption_bar(im, SIZE - BAR_H, SIZE, "CHANGE MY MIND.", start=48, color=MUTED)
    return im


def build_understatement(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    mid_top = BAR_H + 10
    mid = SIZE // 2
    mid_bot = SIZE - BAR_H - 10
    draw_panel(draw, (24, mid_top, SIZE - 24, mid - 8), fill=PANEL)
    draw_panel(draw, (24, mid + 8, SIZE - 24, mid_bot), fill=PANEL_2)
    paste_in(im, prepare_emote("galahad_exploding.png"), (48, mid_top + 16, SIZE - 96, mid - mid_top - 40))
    if caps["react"] == "crest":
        crest = load_reaction_frame("victory_crest", "02.png")
        paste_in(im, nn_scale(crest, 6), (48, mid + 24, SIZE - 96, mid_bot - mid - 40))
    else:
        paste_in(im, prepare_emote("galahad_grin.png"), (48, mid + 24, SIZE - 96, mid_bot - mid - 40))
    caption_bar(im, 0, BAR_H, caps["setup"], start=48, color=CREST)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["punch"], start=72, color=HOLD)
    return im


def build_trade(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    caption_bar(im, 0, BAR_H, "TRADE OFFER", start=64, color=SIGN_EDGE, fill=(28, 22, 18, 255))
    draw_panel(draw, (24, BAR_H + 16, SIZE // 2 - 14, SIZE - BAR_H - 16), fill=PANEL)
    draw_panel(draw, (SIZE // 2 + 14, BAR_H + 16, SIZE - 24, SIZE - BAR_H - 16), fill=PANEL_2)
    paste_in(im, prepare_emote("galahad_thumbs_up.png"), (50, BAR_H + 36, 440, SIZE - 2 * BAR_H - 80))
    if caps["right"] == "block":
        paste_in(im, nn_scale(load_sprite("block_2"), 6), (SIZE // 2 + 50, BAR_H + 36, 440, SIZE - 2 * BAR_H - 80))
    else:
        paste_in(im, prepare_emote("galahad_cheering.png"), (SIZE // 2 + 50, BAR_H + 36, 440, SIZE - 2 * BAR_H - 80))
    left_text = f"{caps['give_label']}\n{caps['give']}"
    right_text = f"{caps['get_label']}\n{caps['get']}"
    caption_bar(im, SIZE - BAR_H, SIZE, left_text, start=32, x0=0, x1=SIZE // 2, color=HOLD)
    caption_bar(im, SIZE - BAR_H, SIZE, right_text, start=32, x0=SIZE // 2, x1=SIZE, color=HOLD)
    return im


def build_bus(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    caption_bar(im, 0, BAR_H, caps["thought"], start=44)
    draw_panel(draw, (24, BAR_H + 16, 460, SIZE - 24), fill=PANEL)
    paste_in(im, prepare_emote(caps["emote"]), (44, BAR_H + 32, 420, SIZE - BAR_H - 80))
    draw.rounded_rectangle((490, 200, 1056, 780), radius=28, fill=(36, 48, 28, 255), outline=SIGN_EDGE, width=8)
    # Bus destination sign — a caption bar, not face overlay.
    caption_bar(im, 250, 540, caps["sign"], start=48, x0=520, x1=1026, fill=(18, 28, 22, 255), color=HOLD)
    draw.ellipse((560, 760, 700, 900), fill=INK, outline=BORDER, width=6)
    draw.ellipse((860, 760, 1000, 900), fill=INK, outline=BORDER, width=6)
    return im


def build_pigeon(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 24, SIZE - 24, SIZE - BAR_H - 88), fill=PANEL)
    if caps["mode"] == "clown_rage":
        paste_in(im, prepare_emote("galahad_clown.png"), (60, 48, 460, 700))
        paste_in(im, prepare_emote("galahad_rage.png"), (560, 48, 460, 700))
        caption_bar(im, SIZE - BAR_H - 80, SIZE - BAR_H, "shiny AU", start=32, x0=40, x1=SIZE // 2 - 8, color=MUTED)
        caption_bar(
            im,
            SIZE - BAR_H - 80,
            SIZE - BAR_H,
            caps["label"],
            start=32,
            x0=SIZE // 2 + 8,
            x1=SIZE - 40,
            color=CREST,
        )
    else:
        paste_in(im, prepare_emote("galahad_confused.png"), (60, 48, 460, 700))
        paste_in(im, prepare_emote("galahad_clown.png"), (560, 48, 460, 700))
        arrow(draw, (500, 380), (580, 380), fill=HOLD, width=12)
        caption_bar(im, SIZE - BAR_H - 80, SIZE - BAR_H, "Galahad", start=32, x0=40, x1=SIZE // 2 - 8, color=MUTED)
        caption_bar(
            im,
            SIZE - BAR_H - 80,
            SIZE - BAR_H,
            caps["label"],
            start=32,
            x0=SIZE // 2 + 8,
            x1=SIZE - 40,
            color=CREST,
        )
    caption_bar(im, SIZE - BAR_H, SIZE, caps["caption"], start=56)
    return im


def build_walkoff(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, BAR_H + 16, 470, SIZE - BAR_H - 16), fill=PANEL)
    paste_in(im, prepare_emote("galahad_theatre_mask.png"), (44, BAR_H + 36, 430, 540))
    walk = load_reaction_frame("walk_away", "04.png")
    paste_in(im, nn_scale(walk, 8), (500, BAR_H + 40, 540, SIZE - 2 * BAR_H - 80))
    arrow(draw, (700, SIZE - BAR_H - 40), (980, SIZE - BAR_H - 40), fill=MUTED, width=8)
    caption_bar(im, 0, BAR_H, caps["line"], start=52)
    caption_bar(im, SIZE - BAR_H, SIZE, caps["sub"], start=40)
    return im


BUILDERS = {
    "drake": build_drake,
    "distracted": build_distracted,
    "this_is_fine": build_this_is_fine,
    "brain": build_brain,
    "yelling": build_yelling,
    "waiting": build_waiting,
    "change_mind": build_change_mind,
    "understatement": build_understatement,
    "trade": build_trade,
    "bus": build_bus,
    "pigeon": build_pigeon,
    "walkoff": build_walkoff,
}


def filename(fmt: dict, set_id: str) -> str:
    stem = f"meme_{fmt['id']}_{fmt['slug']}"
    if set_id == "b":
        stem += "_b"
    return f"{stem}.png"


def write_gallery(out_dir: Path, written: list[tuple[dict, str, Path]]) -> None:
    cards = []
    for fmt, set_id, path in written:
        label = f"{fmt['id']}. {fmt['title']}" + (" · B" if set_id == "b" else " · A")
        cards.append(
            f"""<figure>
  <a href="{html.escape(path.name)}"><img src="{html.escape(path.name)}" alt="{html.escape(label)}" width="540" height="540" /></a>
  <figcaption>{html.escape(label)}<br /><code>{html.escape(path.name)}</code></figcaption>
</figure>"""
        )
    a_cards = [c for (fmt, set_id, path), c in zip(written, cards) if set_id == "a"]
    b_cards = [c for (fmt, set_id, path), c in zip(written, cards) if set_id == "b"]
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Galahad meme pack</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: #0b1220;
      color: #e8eefc;
      padding: 1.5rem;
    }}
    h1 {{ font-size: 1.6rem; margin: 0 0 0.25rem; }}
    h2 {{ font-size: 1.15rem; margin: 1.75rem 0 0.75rem; }}
    .sub {{ opacity: 0.75; margin-bottom: 1.25rem; max-width: 46rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
    }}
    figure {{
      margin: 0;
      background: #121a2b;
      border: 1px solid #243049;
      border-radius: 10px;
      padding: 0.75rem;
      text-align: center;
    }}
    img {{ width: 100%; height: auto; background: #0b1220; }}
    figcaption {{ margin-top: 0.5rem; font-size: 0.85rem; }}
    a {{ color: #8ec7ff; }}
    code {{ font-size: 0.8rem; opacity: 0.85; }}
  </style>
</head>
<body>
  <h1>Galahad · meme pack</h1>
  <p class="sub">
    12 formats · 1080×1080 composites · existing Ryan sheet emotes + reaction stills + captions.
    Look unchanged: no redraw, no restyle. Sources flattened onto navy #0b1220; captions in top/bottom bars.
    <a href="README.md">rebuild notes</a> ·
    <a href="https://github.com/Animayer/Galahad/tree/main/assets/memes">GitHub folder</a> ·
    <a href="../discord-emojis/">Discord emotes</a> ·
    <a href="../../">Hold the Line</a>
  </p>
  <h2>Set A (default)</h2>
  <div class="grid">
    {"".join(a_cards)}
  </div>
  <h2>Set B (alts)</h2>
  <div class="grid">
    {"".join(b_cards)}
  </div>
</body>
</html>
"""
    (out_dir / "index.html").write_text(page, encoding="utf-8")


def flatten_rgb(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", im.size, NAVY)
    bg.alpha_composite(im)
    return bg.convert("RGB")


def _sheet_fill_gray(r: int, g: int, b: int) -> bool:
    """Muted mid-gray like Ryan-sheet checker / tile fill (not navy, not steel glints)."""
    if abs(r - g) > 18 or abs(g - b) > 18 or abs(r - b) > 22:
        return False
    lum = (r + g + b) / 3
    return 95 <= lum <= 175


def checker_pair_count(im: Image.Image, run: int = 4, delta: int = 8) -> int:
    """NN-scaled sheet checker: identical gray A|B pairs stacked for ``run`` rows."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    n = 0
    last = run - 1
    for y in range(h - last):
        for x in range(w - 1):
            a = px[x, y]
            b = px[x + 1, y]
            if not _sheet_fill_gray(*a) or not _sheet_fill_gray(*b):
                continue
            if abs(sum(a) / 3 - sum(b) / 3) < delta:
                continue
            stacked = True
            for k in range(1, run):
                if px[x, y + k] != a or px[x + 1, y + k] != b:
                    stacked = False
                    break
            if stacked:
                n += 1
    return n


def render_one(fmt: dict, set_id: str, out_dir: Path) -> Path:
    builder = BUILDERS[fmt["builder"]]
    caps = dict(fmt[set_id])
    if fmt["slug"] == "drake" and set_id == "b":
        caps["use_hold"] = True
    img = builder(caps)
    if img.size != (SIZE, SIZE):
        raise RuntimeError(f"{fmt['slug']} produced {img.size}, expected {SIZE}x{SIZE}")
    dest = out_dir / filename(fmt, set_id)
    rgb = flatten_rgb(img)
    pairs = checker_pair_count(rgb)
    # Sheet-checker memes were 400–3000+ runs. Helmet dither lands ~0–150.
    if pairs > 250:
        raise RuntimeError(f"{dest.name}: checkerboard-like gray pairs={pairs}")
    rgb.save(dest, "PNG", optimize=True)
    print(f"  checker-runs={pairs}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description="Composite Galahad memes from existing assets.")
    parser.add_argument("--set", choices=("a", "b", "all"), default="all")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    sets = ["a", "b"] if args.set == "all" else [args.set]
    written: list[tuple[dict, str, Path]] = []
    for fmt in FORMATS:
        for set_id in sets:
            dest = render_one(fmt, set_id, out_dir)
            written.append((fmt, set_id, dest))
            print(f"wrote {dest.relative_to(ROOT)}  ({dest.stat().st_size} bytes)")

    if args.set == "all":
        write_gallery(out_dir, written)
        print(f"wrote {(out_dir / 'index.html').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
