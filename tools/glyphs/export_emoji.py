#!/usr/bin/env python3
"""Export the emoji in emoji.txt as small color PNGs for hand tuning.

Each emoji is rendered large from Noto Color Emoji, scaled down to two cells
wide and one tall (12x12 for 6x12 cells), and saved as an RGBA PNG in
glyphs/emoji/<W>x<H>/<CODEPOINT>.png. Edit those in any paint program;
transparent pixels show the cell's background. Existing PNGs are never
overwritten (delete one to regenerate it), unless --force is given.

pack.py turns them into the 'EMOJ' resource, with versions for 256-color,
16-color and black-and-white screens.

usage: export_emoji.py [--force] [--size WxH]
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import glyphlib

FONT = "/usr/local/share/fonts/NotoColorEmoji.ttf"  # pinned release, see Containerfile
FONT_SIZE = 109  # the only size Noto Color Emoji's bitmaps come in
MARGIN = 1  # px of space left below and right, so emoji don't touch the next line


def read_emoji():
    path = os.path.join(os.path.dirname(__file__), "emoji.txt")
    cps = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            for item in line.split():
                cp = ord(item[0])
                if cp not in cps:
                    cps.append(cp)
    return cps


def render(cp, font, w, h):
    big = Image.new("RGBA", (FONT_SIZE * 2, FONT_SIZE * 2), (0, 0, 0, 0))
    ImageDraw.Draw(big).text((FONT_SIZE // 2, FONT_SIZE // 2), chr(cp), font=font, embedded_color=True)
    box = big.getbbox()
    if box is None:
        return None
    big = big.crop(box)

    # fit inside the two cells, keeping the shape
    room_w, room_h = w - MARGIN, h - MARGIN
    scale = min(room_w / big.width, room_h / big.height)
    size = (max(1, round(big.width * scale)), max(1, round(big.height * scale)))
    # scale with premultiplied alpha, so edges don't pick up the transparent colour
    small = big.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(small, ((room_w - size[0]) // 2, (room_h - size[1]) // 2))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="overwrite existing PNGs too")
    ap.add_argument("--size", help="only this cell size, as WxH")
    args = ap.parse_args()

    sizes = glyphlib.CELL_SIZES
    if args.size:
        w, h = map(int, args.size.lower().split("x"))
        sizes = [(w, h)]

    font = ImageFont.truetype(FONT, FONT_SIZE)
    emoji = read_emoji()

    for cw, ch in sizes:
        w, h = cw * 2, ch
        d = glyphlib.emoji_dir(w, h)
        os.makedirs(d, exist_ok=True)
        written = kept = 0
        missing = []
        for cp in emoji:
            path = os.path.join(d, f"{cp:04X}.png")
            if os.path.exists(path) and not args.force:
                kept += 1
                continue
            img = render(cp, font, w, h)
            if img is None:
                missing.append(cp)
                continue
            img.save(path)
            written += 1
        print(f"{w}x{h} emoji: wrote {written}, kept {kept} existing")
        if missing:
            print("  font has no image for: " + " ".join(f"U+{c:04X}" for c in missing))


if __name__ == "__main__":
    sys.exit(main())
