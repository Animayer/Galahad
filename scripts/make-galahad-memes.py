#!/usr/bin/env python3
"""Composite the Galahad meme pack from existing Discord emotes + reaction stills.

Look-unchanged (Ryan 2026-09-18): do not regenerate, redraw, restyle, recolor,
upscale-with-AI, or invent sprites/emotes. This script only:

- loads existing PNGs (Discord emotes, reaction frames, canon sprites)
- nearest-neighbor resizes
- lays out solid navy panels, arrows, and caption bars
- writes 1080×1080 1:1 PNGs

Usage:
    python3 scripts/make-galahad-memes.py
    python3 scripts/make-galahad-memes.py --set a
    python3 scripts/make-galahad-memes.py --set all
"""

from __future__ import annotations

import argparse
import html
import sys
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
            "emote": "galahad_trapped.png",
            "top": "GALAHAD WAITING FOR",
            "bot": "THE LINE TO BREAK",
        },
        "b": {
            "emote": "galahad_ghostly.png",
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


def load_emoji(name: str) -> Image.Image:
    path = EMOJI_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing Discord emote: {path}")
    return Image.open(path).convert("RGBA")


def load_reaction_frame(beat: str, frame: str) -> Image.Image:
    png = REACTION_DIR / beat / frame
    if png.is_file():
        return Image.open(png).convert("RGBA")
    gif = GIF_REACTION_DIR / f"{beat}.gif"
    if not gif.is_file():
        raise FileNotFoundError(f"Missing reaction still: {png} or {gif}")
    im = Image.open(gif)
    idx = int(Path(frame).stem)
    im.seek(min(idx, im.n_frames - 1))
    return im.convert("RGBA")


def load_sprite(name: str) -> Image.Image:
    path = SPRITE_DIR / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing canon sprite: {path}")
    return Image.open(path).convert("RGBA")


def crop_mark(sprite: Image.Image) -> Image.Image:
    """Tight crop of helm / visor (the Mark) from an existing cast pose."""
    return sprite.crop((34, 6, 70, 42))


def crop_visible(im: Image.Image, pad: int = 2) -> Image.Image:
    """Bbox crop of non-navy, opaque pixels. No redraw."""
    rgba = im.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a <= 20:
                continue
            if abs(r - NAVY[0]) + abs(g - NAVY[1]) + abs(b - NAVY[2]) <= 18:
                continue
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
    if maxx < 0:
        return rgba
    cropped = rgba.crop(
        (
            max(0, minx - pad),
            max(0, miny - pad),
            min(w, maxx + 1 + pad),
            min(h, maxy + 1 + pad),
        )
    )
    return navy_to_alpha(cropped)


def navy_to_alpha(im: Image.Image) -> Image.Image:
    """Treat packed navy fill as transparent so stills sit on meme panels."""
    rgba = im.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and abs(r - NAVY[0]) + abs(g - NAVY[1]) + abs(b - NAVY[2]) <= 18:
                px[x, y] = (r, g, b, 0)
    return rgba


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
    base.alpha_composite(im, (int(x), int(y)))


def paste_in(base: Image.Image, im: Image.Image, box: tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    fitted = nn_fit(im, (w, h))
    px = x + (w - fitted.size[0]) // 2
    py = y + (h - fitted.size[1]) // 2
    base.alpha_composite(fitted, (px, py))


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill=PANEL, outline=BORDER, width: int = 4, radius: int = 18) -> None:
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
    stroke: int = 3,
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
) -> None:
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, y0, SIZE, y1), fill=fill or (8, 14, 26, 230))
    text_block(
        draw,
        (SIZE // 2, (y0 + y1) // 2),
        text,
        max_width=SIZE - 80,
        max_height=y1 - y0 - 16,
        start=start,
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
    draw_panel(draw, (24, 24, SIZE - 24, SIZE // 2 - 10), fill=PANEL)
    draw_panel(draw, (24, SIZE // 2 + 10, SIZE - 24, SIZE - 24), fill=PANEL_2)
    paste_in(im, load_emoji("galahad_thumbs_down.png"), (48, 48, 500, 470))
    if caps.get("use_hold"):
        hold = crop_visible(load_reaction_frame("hold_the_line", "03.png"))
        paste_in(im, nn_scale(hold, 6), (48, SIZE // 2 + 34, 500, 470))
    else:
        paste_in(im, load_emoji("galahad_thumbs_up.png"), (48, SIZE // 2 + 34, 500, 470))
    text_block(draw, (790, 270), caps["no"], max_width=470, max_height=400, start=64, fill=CREST)
    text_block(draw, (790, 810), caps["yes"], max_width=470, max_height=400, start=64, fill=HOLD)
    return im


def build_distracted(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 24, SIZE - 24, SIZE - 24))
    text_block(draw, (SIZE // 2, 70), "THE OATH", max_width=900, max_height=70, start=40, fill=MUTED)
    paste_in(im, load_emoji("galahad_rage.png"), (50, 150, 300, 620))
    paste_in(im, load_emoji("galahad_grin.png"), (390, 210, 300, 560))
    paste_in(im, load_emoji("galahad_smug.png"), (730, 150, 300, 620))
    arrow(draw, (690, 430), (728, 400), fill=HOLD, width=10)
    text_block(draw, (200, 880), caps["gf"], max_width=300, max_height=140, start=40, fill=CREST)
    text_block(draw, (540, 940), caps["bf"], max_width=300, max_height=80, start=36, fill=MUTED)
    text_block(draw, (880, 880), caps["other"], max_width=300, max_height=140, start=40, fill=HOLD)
    return im


def build_this_is_fine(caps: dict) -> Image.Image:
    im = canvas()
    boom = nn_scale(load_emoji("galahad_exploding.png"), 3)
    paste(im, boom, (8, 128))
    paste(im, boom, (SIZE - 8, 128), "rt")
    paste(im, boom, (8, SIZE - 128), "lb")
    paste(im, boom, (SIZE - 8, SIZE - 128), "rb")
    draw = ImageDraw.Draw(im)
    # Navy plate so explosion tiles never cover the seated face.
    draw.rounded_rectangle((200, 190, 880, 870), radius=28, fill=NAVY, outline=BORDER, width=6)
    sit = nn_scale(load_emoji(caps["emote"]), 5)
    paste(im, sit, (SIZE // 2, 530), "mm")
    caption_bar(im, 0, 120, caps["line"], start=64)
    caption_bar(im, 960, SIZE, caps["sub"], start=42)
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
    for i, (emote, line, fill) in enumerate(zip(emotes, caps["lines"], fills)):
        y0 = i * row_h
        draw.rectangle((0, y0, SIZE, y0 + row_h), fill=fill)
        if i:
            draw.line((0, y0, SIZE, y0), fill=BORDER, width=3)
        # Expanding layout chrome — nested squares, not character art.
        brain = 16 + i * 12
        bx, by = 86, y0 + row_h // 2
        draw.rounded_rectangle(
            (bx - brain, by - brain, bx + brain, by + brain),
            radius=6,
            outline=HOLD if i == 3 else MUTED,
            width=3,
        )
        paste_in(im, load_emoji(emote), (140, y0 + 12, 246, row_h - 24))
        text_block(
            draw,
            (720, y0 + row_h // 2),
            line,
            max_width=620,
            max_height=row_h - 30,
            start=48,
            fill=CREAM if i < 3 else HOLD,
        )
    return im


def build_yelling(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (20, 20, SIZE // 2 - 10, SIZE - 20), fill=(42, 24, 28, 255), outline=CREST)
    draw_panel(draw, (SIZE // 2 + 10, 20, SIZE - 20, SIZE - 20), fill=PANEL)
    paste_in(im, load_emoji("galahad_rage.png"), (36, 36, 508, 800))
    paste_in(im, load_emoji(caps["quiet"]), (SIZE // 2 + 26, 36, 508, 800))
    text_block(draw, (270, 920), caps["left"], max_width=480, max_height=140, start=40, fill=CREST)
    text_block(draw, (810, 920), caps["right"], max_width=480, max_height=140, start=40, fill=MUTED)
    return im


def build_waiting(caps: dict) -> Image.Image:
    im = canvas()
    paste_in(im, load_emoji(caps["emote"]), (140, 160, 800, 760))
    caption_bar(im, 0, 140, caps["top"], start=52)
    caption_bar(im, 940, SIZE, caps["bot"], start=52)
    return im


def build_change_mind(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 780, SIZE, SIZE), fill=TABLE)
    draw.line((0, 780, SIZE, 780), fill=BORDER, width=6)
    paste_in(im, load_emoji(caps["emote"]), (270, 40, 540, 430))
    draw_panel(draw, (160, 470, 920, 790), fill=SIGN, outline=SIGN_EDGE, width=8, radius=8)
    text_block(
        draw,
        (SIZE // 2, 630),
        caps["sign"],
        max_width=700,
        max_height=260,
        start=56,
        fill=CREAM,
    )
    mark = nn_scale(crop_mark(load_sprite("cast_2")), 4)
    paste(im, mark, (118, 900), "mm")
    text_block(draw, (640, 930), "CHANGE MY MIND.", max_width=720, max_height=90, start=48, fill=MUTED)
    return im


def build_understatement(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 24, SIZE - 24, SIZE // 2 - 10), fill=PANEL)
    draw_panel(draw, (24, SIZE // 2 + 10, SIZE - 24, SIZE - 24), fill=PANEL_2)
    paste_in(im, load_emoji("galahad_exploding.png"), (48, 48, 500, 470))
    if caps["react"] == "crest":
        crest = crop_visible(load_reaction_frame("victory_crest", "02.png"))
        paste_in(im, nn_scale(crest, 6), (48, SIZE // 2 + 34, 500, 470))
    else:
        paste_in(im, load_emoji("galahad_grin.png"), (48, SIZE // 2 + 34, 500, 470))
    text_block(draw, (790, 270), caps["setup"], max_width=470, max_height=400, start=56, fill=CREST)
    text_block(draw, (790, 810), caps["punch"], max_width=470, max_height=400, start=72, fill=HOLD)
    return im


def build_trade(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, SIZE, 150), fill=(28, 22, 18, 255))
    text_block(draw, (SIZE // 2, 75), "TRADE OFFER", max_width=960, max_height=110, start=72, fill=SIGN_EDGE)
    draw_panel(draw, (24, 174, SIZE // 2 - 14, SIZE - 24), fill=PANEL)
    draw_panel(draw, (SIZE // 2 + 14, 174, SIZE - 24, SIZE - 24), fill=PANEL_2)
    text_block(draw, (270, 230), caps["give_label"], max_width=460, max_height=60, start=32, fill=MUTED)
    text_block(draw, (810, 230), caps["get_label"], max_width=460, max_height=60, start=32, fill=MUTED)
    paste_in(im, load_emoji("galahad_thumbs_up.png"), (70, 280, 400, 520))
    if caps["right"] == "block":
        paste_in(im, nn_scale(crop_visible(load_sprite("block_2")), 6), (SIZE // 2 + 60, 270, 400, 540))
    else:
        paste_in(im, load_emoji("galahad_cheering.png"), (SIZE // 2 + 70, 280, 400, 520))
    text_block(draw, (270, 900), caps["give"], max_width=460, max_height=140, start=44, fill=HOLD)
    text_block(draw, (810, 900), caps["get"], max_width=460, max_height=140, start=44, fill=HOLD)
    return im


def build_bus(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 40, 460, 1040), fill=PANEL)
    paste_in(im, load_emoji(caps["emote"]), (44, 60, 420, 620))
    # Thought line — layout chrome, not new character art.
    draw.ellipse((70, 720, 410, 860), fill=SIGN, outline=BORDER, width=4)
    text_block(draw, (240, 790), caps["thought"], max_width=300, max_height=100, start=32, fill=CREAM, stroke=2)
    draw.ellipse((390, 680, 434, 724), fill=SIGN, outline=BORDER, width=3)
    draw.ellipse((440, 640, 472, 672), fill=SIGN, outline=BORDER, width=3)
    draw.rounded_rectangle((490, 200, 1056, 780), radius=28, fill=(36, 48, 28, 255), outline=SIGN_EDGE, width=8)
    draw.rectangle((520, 250, 1026, 540), fill=(18, 28, 22, 255))
    text_block(draw, (773, 395), caps["sign"], max_width=480, max_height=240, start=52, fill=HOLD)
    draw.ellipse((560, 760, 700, 900), fill=INK, outline=BORDER, width=6)
    draw.ellipse((860, 760, 1000, 900), fill=INK, outline=BORDER, width=6)
    return im


def build_pigeon(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 24, SIZE - 24, 900), fill=PANEL)
    if caps["mode"] == "clown_rage":
        paste_in(im, load_emoji("galahad_clown.png"), (60, 80, 460, 620))
        paste_in(im, load_emoji("galahad_rage.png"), (560, 80, 460, 620))
        text_block(draw, (290, 760), "shiny AU", max_width=440, max_height=100, start=36, fill=MUTED)
        text_block(draw, (790, 760), caps["label"], max_width=440, max_height=120, start=36, fill=CREST)
    else:
        paste_in(im, load_emoji("galahad_confused.png"), (60, 80, 460, 620))
        paste_in(im, load_emoji("galahad_clown.png"), (560, 80, 460, 620))
        arrow(draw, (500, 380), (580, 380), fill=HOLD, width=12)
        text_block(draw, (290, 760), "Galahad", max_width=440, max_height=80, start=36, fill=MUTED)
        text_block(draw, (790, 760), caps["label"], max_width=440, max_height=80, start=36, fill=CREST)
    caption_bar(im, 920, SIZE, caps["caption"], start=56)
    return im


def build_walkoff(caps: dict) -> Image.Image:
    im = canvas()
    draw = ImageDraw.Draw(im)
    draw_panel(draw, (24, 150, 470, 920), fill=PANEL)
    paste_in(im, load_emoji("galahad_theatre_mask.png"), (44, 190, 430, 540))
    walk = crop_visible(load_reaction_frame("walk_away", "04.png"), pad=2)
    paste_in(im, nn_scale(walk, 8), (500, 200, 540, 700))
    arrow(draw, (700, 860), (980, 860), fill=MUTED, width=8)
    caption_bar(im, 0, 130, caps["line"], start=52)
    caption_bar(im, 940, SIZE, caps["sub"], start=40)
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
    Look unchanged: no redraw, no restyle.
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


def render_one(fmt: dict, set_id: str, out_dir: Path) -> Path:
    builder = BUILDERS[fmt["builder"]]
    caps = dict(fmt[set_id])
    if fmt["slug"] == "drake" and set_id == "b":
        caps["use_hold"] = True
    img = builder(caps)
    if img.size != (SIZE, SIZE):
        raise RuntimeError(f"{fmt['slug']} produced {img.size}, expected {SIZE}x{SIZE}")
    dest = out_dir / filename(fmt, set_id)
    flatten_rgb(img).save(dest, "PNG", optimize=True)
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
        print(f"wrote { (out_dir / 'index.html').relative_to(ROOT) }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
