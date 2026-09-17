#!/usr/bin/env python3
"""Rebuild the Galahad GIF pack from canon roman_legionary frames.

Reads frame lists, timings, and loop flags from
``assets/roman_legionary/animations.json`` and PNG frames from
``assets/roman_legionary/frames_96/``. Does not invent, flip, or
resample art. Left/right walks stay as drawn.

Usage:
    python3 scripts/make-gifs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required. Install with: python3 -m pip install Pillow")

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "assets" / "roman_legionary"
FRAMES_DIR = PACK / "frames_96"
ANIM_PATH = PACK / "animations.json"
OUT_DIR = ROOT / "assets" / "gifs"

# Opaque dark navy. GIF has 1-bit transparency; compositing onto navy
# avoids fringe on pixel edges while matching the night-watch tone.
NAVY = (11, 18, 32, 255)  # #0b1220


def load_canon_frame(name: str) -> Image.Image:
    path = FRAMES_DIR / f"{name}.png"
    if not path.is_file():
        raise FileNotFoundError(f"Missing canon frame: {path}")
    return Image.open(path).convert("RGBA")


def composite_navy(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", im.size, NAVY)
    return Image.alpha_composite(bg, im)


def quantize_sequence(frames: list[Image.Image]) -> list[Image.Image]:
    """Shared palette, no dither, no resize."""
    if not frames:
        raise ValueError("No frames to quantize")
    w, h = frames[0].size
    for i, frame in enumerate(frames):
        if frame.size != (w, h):
            raise ValueError(
                f"Frame {i} size {frame.size} != {w}x{h}; refusing to resize"
            )
    sheet = Image.new("RGB", (w * len(frames), h))
    for i, frame in enumerate(frames):
        sheet.paste(frame.convert("RGB"), (i * w, 0))
    pal = sheet.quantize(
        colors=256,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )
    return [pal.crop((i * w, 0, (i + 1) * w, h)) for i in range(len(frames))]


def write_gif(
    dest: Path,
    frames: list[Image.Image],
    duration_ms: int,
    loop: bool,
) -> None:
    palettes = quantize_sequence(frames)
    first, rest = palettes[0], palettes[1:]
    first.save(
        dest,
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=0 if loop else 1,
        disposal=2,
        optimize=False,
    )


def build() -> None:
    spec = json.loads(ANIM_PATH.read_text(encoding="utf-8"))
    animations = spec.get("animations") or {}
    if not animations:
        raise SystemExit(f"No animations in {ANIM_PATH}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Source frames: {FRAMES_DIR}")
    print(f"Spec:          {ANIM_PATH}")
    print(f"Output:        {OUT_DIR}")
    print(f"Background:    #{NAVY[0]:02x}{NAVY[1]:02x}{NAVY[2]:02x} (dark navy)")
    print()

    for name, clip in animations.items():
        frame_names = clip["frames"]
        duration_ms = int(clip["frameDurationMs"])
        loop = bool(clip.get("loop", False))
        rgba = [composite_navy(load_canon_frame(n)) for n in frame_names]
        dest = OUT_DIR / f"{name}.gif"
        write_gif(dest, rgba, duration_ms, loop)
        size_kb = dest.stat().st_size / 1024
        print(
            f"  {dest.name:18}  {len(frame_names)}f  {duration_ms}ms  "
            f"{'loop' if loop else 'once':4}  {size_kb:6.1f} KB  "
            f"{' '.join(frame_names)}"
        )
        if dest.stat().st_size > 200 * 1024:
            print(f"    warning: {dest.name} exceeds 200 KB", file=sys.stderr)

    print("\nDone. Canon frames only; no mirroring or resampling.")


if __name__ == "__main__":
    build()
