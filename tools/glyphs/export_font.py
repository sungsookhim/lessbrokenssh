#!/usr/bin/env python3
"""Export the symbols in symbols.txt from fonts into glyph text art.

Each symbol is rendered at SCALE times the cell size from the first font in
FONTS that has it, then scaled down by area averaging and thresholded, and
written to glyphs/<W>x<H>/ for hand tuning. Hand-edited files (edited=yes)
are left alone unless --force is given.

The em size is picked so DejaVu Sans Mono's cell is exactly SCALE times ours
(its advance is 0.602 em), and the baseline sits where Monaco's does, so
symbols line up with the text around them. Symbols are centred sideways, and
shrunk to fit if they're too big for the cell.

usage: export_font.py [--force] [--size WxH]
"""

import argparse
import os
import sys

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

import glyphlib

SCALE = 8
MIN_COVERAGE = 0.15

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/noto"]
FONTS = [
    "DejaVuSansMono.ttf",
    "DejaVuSans.ttf",
    "NotoSansSymbols2-Regular.ttf",
    "NotoSansSymbols-Regular.ttf",
    "NotoSansMath-Regular.ttf",
]

DEJAVU_MONO_ADVANCE = 1233 / 2048  # em fraction


def find_fonts():
    fonts = []
    for name in FONTS:
        for d in FONT_DIRS:
            path = os.path.join(d, name)
            if os.path.exists(path):
                fonts.append((name, path, set(TTFont(path, lazy=True).getBestCmap())))
                break
        else:
            print(f"warning: font {name} not found", file=sys.stderr)
    return fonts


def read_symbols():
    path = os.path.join(os.path.dirname(__file__), "symbols.txt")
    cps = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cps.append(ord(line.split("\t")[0].strip()[0]))
    return cps


def baseline_row(h):
    # Monaco's baseline in its cell: 10 of 12 rows down at 9 pt
    return h - round(h / 6)


def render(cp, font_path, w, h):
    """The glyph for cp as rows of 0/1, or None if the font draws nothing."""
    W, H = w * SCALE, h * SCALE
    em = round(W / DEJAVU_MONO_ADVANCE)
    base = baseline_row(h) * SCALE
    ch = chr(cp)

    def draw(size, y, anchor):
        # on a canvas 3 cells big, with the cell itself in the middle
        font = ImageFont.truetype(font_path, size)
        big = Image.new("L", (W * 3, H * 3), 0)
        ImageDraw.Draw(big).text((W, H + y), ch, fill=255, font=font, anchor=anchor)
        return big

    big = draw(em, base, "ls")
    box = big.getbbox()
    if box is None:
        return None
    top = H  # where the cell starts on the canvas

    if box[2] - box[0] > W * 0.95 or box[1] < H or box[3] > 2 * H:
        # too big for the cell: shrink it to fit, centred up and down as well
        fit = min(W * 0.95 / (box[2] - box[0]), H * 0.9 / (box[3] - box[1]), 1.0)
        big = draw(max(4, int(em * fit)), H / 2, "lm")
        box = big.getbbox()
        top = box[1] - (H - (box[3] - box[1])) // 2

    # centre sideways
    left = box[0] - (W - (box[2] - box[0])) // 2
    cell = big.crop((left, top, left + W, top + H))

    return to_bits(cell.resize((w, h), Image.BOX))


def to_bits(small):
    """Threshold so the 1-bit glyph keeps about as much ink as the large one.

    A fixed cutoff drops strokes thinner than about half a small pixel, which
    is most of them in a symbol font at 12 px. Instead, turn on as many
    pixels as the total ink adds up to, darkest first, ignoring faint
    smudges below MIN_COVERAGE.
    """
    w, h = small.size
    cover = [(small.getpixel((x, y)) / 255, x, y) for y in range(h) for x in range(w)]
    budget = round(sum(c for c, _, _ in cover))
    rows = [[0] * w for _ in range(h)]
    for c, x, y in sorted(cover, reverse=True)[:budget]:
        if c >= MIN_COVERAGE:
            rows[y][x] = 1
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="overwrite hand-edited glyphs too")
    ap.add_argument("--size", help="only this cell size, as WxH")
    args = ap.parse_args()

    sizes = glyphlib.CELL_SIZES
    if args.size:
        w, h = map(int, args.size.lower().split("x"))
        sizes = [(w, h)]

    fonts = find_fonts()
    symbols = read_symbols()

    for w, h in sizes:
        written = kept = 0
        missing = []
        for cp in symbols:
            source = next(((name, path) for name, path, cmap in fonts if cp in cmap), None)
            if source is None:
                missing.append(cp)
                continue
            rows = render(cp, source[1], w, h)
            if rows is None:
                missing.append(cp)
                continue
            if glyphlib.write_glyph(w, h, cp, rows, f"font:{source[0]}", force=args.force):
                written += 1
            else:
                kept += 1
        print(f"{w}x{h}: wrote {written} symbols, kept {kept} hand-edited")
        if missing:
            print("  no font has: " + " ".join(f"{chr(c)} U+{c:04X}" for c in missing))


if __name__ == "__main__":
    sys.exit(main())
