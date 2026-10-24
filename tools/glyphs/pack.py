#!/usr/bin/env python3
"""Pack glyphs/<W>x<H>/*.txt into glyphs.r, one 'GLYF' resource per cell size.

Resource layout (big-endian, as both 68k and PowerPC read it):

    uint16 cell_width, cell_height, count, row_bytes
    uint32 codepoints[count]          sorted, so the app can binary search
    uint8  bits[row_bytes * cell_height]

bits is a 1-bit strip of all glyphs side by side, glyph i at x = i * cell_width,
most significant bit leftmost, which is QuickDraw's BitMap format. row_bytes
is even, as QuickDraw requires.

Emoji PNGs in glyphs/emoji/<W>x<H>/ (W two cells wide) go into one 'EMOJ'
resource per size:

    uint16 width, height, count, row_bytes_1, row_bytes_4, row_bytes_8
    uint32 codepoints[count]
    uint8  mask[row_bytes_1 * height]     1 bit: which pixels to draw
    uint8  mono[row_bytes_1 * height]     1 bit: black-and-white version
    uint8  color4[row_bytes_4 * height]   4 bit: Mac standard 16-color palette
    uint8  color8[row_bytes_8 * height]   8 bit: Mac standard 256-color palette

each a strip of all the emoji side by side, like the 'GLYF' bitmap.

usage: pack.py [output.r]
"""

import os
import struct
import sys

import glyphlib

FIRST_ID = 128


def pack_set(w, h, glyphs):
    cps = sorted(glyphs)
    width = len(cps) * w
    row_bytes = (width + 15) // 16 * 2
    bits = bytearray(row_bytes * h)
    for i, cp in enumerate(cps):
        for y, row in enumerate(glyphs[cp]):
            for x, on in enumerate(row):
                if on:
                    px = i * w + x
                    bits[y * row_bytes + px // 8] |= 0x80 >> (px % 8)
    header = struct.pack(">HHHH", w, h, len(cps), row_bytes)
    return header + struct.pack(f">{len(cps)}I", *cps) + bytes(bits)


def mac_palette_8():
    """The standard Mac OS 256-color palette ('clut' 8), in index order."""
    levels = [0xFF, 0xCC, 0x99, 0x66, 0x33, 0x00]
    cube = [(r, g, b) for r in levels for g in levels for b in levels][:215]  # black goes last
    ramp = [0xEE, 0xDD, 0xBB, 0xAA, 0x88, 0x77, 0x55, 0x44, 0x22, 0x11]
    return (cube + [(v, 0, 0) for v in ramp] + [(0, v, 0) for v in ramp]
            + [(0, 0, v) for v in ramp] + [(v, v, v) for v in ramp] + [(0, 0, 0)])


# the standard Mac OS 16-color palette ('clut' 4), in index order
MAC_PALETTE_4 = [
    (0xFF, 0xFF, 0xFF), (0xFC, 0xF3, 0x05), (0xFF, 0x64, 0x02), (0xDD, 0x08, 0x06),
    (0xF2, 0x08, 0x84), (0x46, 0x00, 0xA5), (0x00, 0x00, 0xD4), (0x02, 0xAB, 0xEA),
    (0x1F, 0xB7, 0x14), (0x00, 0x64, 0x11), (0x56, 0x2C, 0x05), (0x90, 0x71, 0x3A),
    (0xC0, 0xC0, 0xC0), (0x80, 0x80, 0x80), (0x40, 0x40, 0x40), (0x00, 0x00, 0x00),
]
MAC_PALETTE_8 = mac_palette_8()


def nearest(palette, rgb):
    r, g, b = rgb
    # weighted towards green, roughly how bright each channel looks
    return min(range(len(palette)),
               key=lambda i: 2 * (palette[i][0] - r) ** 2 + 4 * (palette[i][1] - g) ** 2 + 3 * (palette[i][2] - b) ** 2)


def even_row_bytes(bits):
    return (bits + 15) // 16 * 2


BAYER_4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def mono_ink(img, x, y, luma):
    """Black-and-white version: outline the shape, ordered-dither the inside."""
    w, h = img.size
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if not (0 <= nx < w and 0 <= ny < h) or img.getpixel((nx, ny))[3] < 128:
            return True
    return luma < (BAYER_4[y % 4][x % 4] + 0.5) * 16


def pack_emoji(w, h, paths):
    from PIL import Image  # only emoji need it

    cps = sorted(paths)
    n = len(cps)
    rb1, rb4, rb8 = even_row_bytes(n * w), even_row_bytes(n * w * 4), even_row_bytes(n * w * 8)
    mask, mono = bytearray(rb1 * h), bytearray(rb1 * h)
    color4, color8 = bytearray(rb4 * h), bytearray(rb8 * h)
    cache4, cache8 = {}, {}

    for i, cp in enumerate(cps):
        img = Image.open(paths[cp]).convert("RGBA")
        if img.size != (w, h):
            raise ValueError(f"{paths[cp]}: must be {w}x{h}, is {img.width}x{img.height}")
        for y in range(h):
            for x in range(w):
                r, g, b, a = img.getpixel((x, y))
                if a < 128:
                    continue
                px = i * w + x
                mask[y * rb1 + px // 8] |= 0x80 >> (px % 8)
                if mono_ink(img, x, y, 0.30 * r + 0.59 * g + 0.11 * b):
                    mono[y * rb1 + px // 8] |= 0x80 >> (px % 8)
                c4 = cache4.setdefault((r, g, b), nearest(MAC_PALETTE_4, (r, g, b)))
                c8 = cache8.setdefault((r, g, b), nearest(MAC_PALETTE_8, (r, g, b)))
                color4[y * rb4 + px // 2] |= c4 << (4 if px % 2 == 0 else 0)
                color8[y * rb8 + px] = c8
    # paper (index 0, white) where the mask is clear doesn't matter; it isn't drawn

    header = struct.pack(">HHHHHH", w, h, n, rb1, rb4, rb8)
    return header + struct.pack(f">{n}I", *cps) + bytes(mask + mono + color4 + color8)


def emoji_paths(w, h):
    d = glyphlib.emoji_dir(w, h)
    if not os.path.isdir(d):
        return {}
    return {int(name[:-4], 16): os.path.join(d, name) for name in os.listdir(d) if name.endswith(".png")}


def rez_data(res_id, name, data, res_type="GLYF"):
    lines = [f'data \'{res_type}\' ({res_id}, "{name}") {{']
    for i in range(0, len(data), 32):
        lines.append(f'\t$"{data[i:i + 32].hex().upper()}"')
    lines.append("};")
    return "\n".join(lines)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(glyphlib.ROOT, "glyphs.r")
    parts = ["/* generated by tools/glyphs/pack.py from glyphs/; edit those, not this */", ""]
    res_id = FIRST_ID
    for w, h in glyphlib.CELL_SIZES:
        glyphs = glyphlib.load_set(w, h)
        if not glyphs:
            continue
        data = pack_set(w, h, glyphs)
        parts.append(rez_data(res_id, f"{w}x{h}", data))
        parts.append("")
        print(f"{w}x{h}: {len(glyphs)} glyphs, {len(data)} bytes, 'GLYF' {res_id}")
        res_id += 1

    res_id = FIRST_ID
    for cw, ch in glyphlib.CELL_SIZES:
        w, h = cw * 2, ch
        paths = emoji_paths(w, h)
        if not paths:
            continue
        data = pack_emoji(w, h, paths)
        parts.append(rez_data(res_id, f"{w}x{h}", data, "EMOJ"))
        parts.append("")
        print(f"{w}x{h} emoji: {len(paths)}, {len(data)} bytes, 'EMOJ' {res_id}")
        res_id += 1

    text = "\n".join(parts)
    # only touch the file when it changes, so builds don't redo the resources
    if os.path.exists(out) and open(out).read() == text:
        return
    with open(out, "w") as f:
        f.write(text)


if __name__ == "__main__":
    sys.exit(main())
