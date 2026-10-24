#!/usr/bin/env python3
"""Render glyph sets to PNG contact sheets for reviewing without a Mac.

For each cell size, writes build-glyphs/preview-<W>x<H>.png with:
  - every glyph at ZOOM x with its pixel grid and code point
  - tests/unicode-sample.txt at 2x, using the glyphs where we have them
    (other characters show as grey boxes, so missing glyphs stand out)

usage: preview.py
"""

import os
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

import glyphlib

ZOOM = 8
COLS = 16
INK, PAPER, GRID, MISSING = (0, 0, 0), (255, 255, 255), (220, 220, 220), (200, 200, 200)


def draw_glyph(img, rows, ox, oy, zoom, grid=False):
    d = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, on in enumerate(row):
            box = [ox + x * zoom, oy + y * zoom, ox + (x + 1) * zoom - 1, oy + (y + 1) * zoom - 1]
            d.rectangle(box, fill=INK if on else PAPER, outline=GRID if grid else None)


def sample_lines():
    path = os.path.join(glyphlib.ROOT, "tests", "unicode-sample.txt")
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f]


def render_sample(w, h, glyphs, zoom=2):
    font = ImageFont.load_default()
    lines = sample_lines()
    cols = max(len(l) for l in lines) + 4
    img = Image.new("RGB", (cols * w * zoom, len(lines) * h * zoom), PAPER)
    d = ImageDraw.Draw(img)
    for row, line in enumerate(lines):
        col = 0
        for ch in line:
            cp = ord(ch)
            x, y = col * w * zoom, row * h * zoom
            if cp in glyphs:
                draw_glyph(img, glyphs[cp], x, y, zoom)
            elif cp < 128:
                d.text((x, y), ch, fill=INK, font=font)
            elif cp in (0xFE0F, 0x200D):
                continue
            span = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
            if cp >= 128 and cp not in glyphs:
                d.rectangle([x + 1, y + 1, x + span * w * zoom - 2, y + h * zoom - 2], fill=MISSING)
            col += span
    return img


def contact_sheet(w, h, glyphs):
    font = ImageFont.load_default()
    cps = sorted(glyphs)
    cell_w, cell_h = w * ZOOM + 16, h * ZOOM + 24
    rows = (len(cps) + COLS - 1) // COLS
    img = Image.new("RGB", (COLS * cell_w, rows * cell_h), PAPER)
    d = ImageDraw.Draw(img)
    for i, cp in enumerate(cps):
        ox, oy = (i % COLS) * cell_w + 8, (i // COLS) * cell_h + 4
        draw_glyph(img, glyphs[cp], ox, oy, ZOOM, grid=True)
        d.text((ox, oy + h * ZOOM + 4), f"{cp:04X}", fill=INK, font=font)
    return img


def main():
    out_dir = os.path.join(glyphlib.ROOT, "build-glyphs")
    os.makedirs(out_dir, exist_ok=True)
    for w, h in glyphlib.CELL_SIZES:
        glyphs = glyphlib.load_set(w, h)
        if not glyphs:
            continue
        sheet = contact_sheet(w, h, glyphs)
        sample = render_sample(w, h, glyphs)
        img = Image.new("RGB", (max(sheet.width, sample.width), sheet.height + sample.height + 16), PAPER)
        img.paste(sample, (0, 0))
        img.paste(sheet, (0, sample.height + 16))
        path = os.path.join(out_dir, f"preview-{w}x{h}.png")
        img.save(path)
        print(f"{w}x{h}: {path}")


if __name__ == "__main__":
    sys.exit(main())
