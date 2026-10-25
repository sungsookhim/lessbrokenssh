#!/usr/bin/env python3
"""Build lessbrokenssh-icons.r from the PNGs in docs/lessbrokenssh-icons/.

Inputs (RGBA; a pixel with alpha >= 128 is part of the icon and its mask):

    icon-32.png, icon-16.png         colour art, quantized to the Mac palettes
    icon-32-bw.png, icon-16-bw.png   hand-drawn 1-bit art (black = set bit)
    icon-48.png, icon-128.png        Icon Services sizes (Mac OS 8.5 and later)
    about-128.png                    picture in the About box

Resources written, all with ID SSHEVEN_APPLICATION_ICON except the PICT:

    'ICN#' 'icl4' 'icl8'   32x32 1-, 4- and 8-bit, what System 7 and later draw
    'ics#' 'ics4' 'ics8'   16x16 1-, 4- and 8-bit
    'icns'                 the above plus 48x48 (ich#/ich4/ich8/ih32/h8mk),
                           32-bit versions of every size and the 128x128
                           (it32/t8mk), for Icon Services
    'PICT' (PICT_ABOUT)    about-128.png as an 8-bit PICT 2 on white

usage: make_icons.py [art_dir] [output.r] [preview.png]
"""

import os
import struct
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Mac OS standard 4-bit colour table (clut 4), in index order
CLUT4 = [0xFFFFFF, 0xFCF305, 0xFF6402, 0xDD0806, 0xF20884, 0x4600A5, 0x0000D4, 0x02ABEA,
         0x1FB714, 0x006411, 0x562C05, 0x90713A, 0xC0C0C0, 0x808080, 0x404040, 0x000000]


def clut8():
    """Mac OS standard 8-bit colour table (clut 8), in index order."""
    cube = [0xFF, 0xCC, 0x99, 0x66, 0x33, 0x00]
    ramp = [0xEE, 0xDD, 0xBB, 0xAA, 0x88, 0x77, 0x55, 0x44, 0x22, 0x11]
    t = [(r << 16) | (g << 8) | b for r in cube for g in cube for b in cube][:-1]
    t += [v << 16 for v in ramp] + [v << 8 for v in ramp] + ramp
    t += [(v << 16) | (v << 8) | v for v in ramp] + [0x000000]
    return t


CLUT8 = clut8()


def rgb(c):
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def nearest(table, p, cache={}):
    key = (id(table), p)
    if key not in cache:
        cache[key] = min(range(len(table)),
                         key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb(table[i]), p)))
    return cache[key]


def load(art, name, size):
    im = Image.open(os.path.join(art, name)).convert("RGBA")
    if im.size != (size, size):
        sys.exit(f"{name}: is {im.size[0]}x{im.size[1]}, expected {size}x{size}")
    return [[im.getpixel((x, y)) for x in range(size)] for y in range(size)]


def opaque(p):
    return p[3] >= 128


def is_black(p):
    return opaque(p) and (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000 < 128


def bits(px, test):
    """1 bit per pixel, MSB leftmost, rows padded to whole bytes."""
    out = bytearray()
    for row in px:
        for x in range(0, len(row), 8):
            b = 0
            for i, p in enumerate(row[x:x + 8]):
                if test(p):
                    b |= 0x80 >> i
            out.append(b)
    return bytes(out)


def icon_list(bw):
    """'ICN#'-style data: the 1-bit image, then the mask."""
    return bits(bw, is_black) + bits(bw, opaque)


def indexed(px, table, depth):
    """Pixels as indexes into a Mac clut; transparent pixels are index 0 (white)."""
    out = bytearray()
    per = 8 // depth
    for row in px:
        for x in range(0, len(row), per):
            b = 0
            for p in row[x:x + per]:
                b = (b << depth) | (nearest(table, p[:3]) if opaque(p) else 0)
            out.append(b)
    return bytes(out)


def icns_rle(plane):
    """Icon Services RLE for one 8-bit channel of an is32/il32/ih32/it32."""
    out = bytearray()
    i, n = 0, len(plane)
    while i < n:
        run = 1
        while i + run < n and run < 130 and plane[i + run] == plane[i]:
            run += 1
        if run >= 3:
            out += bytes([run + 125, plane[i]])
            i += run
            continue
        start = i
        while i < n and i - start < 128:
            if i + 2 < n and plane[i] == plane[i + 1] == plane[i + 2]:
                break
            i += 1
        out.append(i - start - 1)
        out += plane[start:i]
    return bytes(out)


def rgb32(px):
    """32-bit element data: each of R, G, B compressed separately."""
    flat = [p if opaque(p) else (255, 255, 255, 0) for row in px for p in row]
    return b"".join(icns_rle(bytes(p[ch] for p in flat)) for ch in range(3))


def mask8(px):
    return bytes(255 if opaque(p) else 0 for row in px for p in row)


def icns(elements):
    body = b"".join(t.encode() + struct.pack(">I", len(d) + 8) + d for t, d in elements)
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def packbits(row):
    out = bytearray()
    i, n = 0, len(row)
    while i < n:
        run = 1
        while i + run < n and run < 128 and row[i + run] == row[i]:
            run += 1
        if run >= 2:
            out += bytes([257 - run, row[i]])
            i += run
            continue
        start = i
        while i < n and i - start < 128:
            if i + 1 < n and row[i] == row[i + 1]:
                break
            i += 1
        out.append(i - start - 1)
        out += row[start:i]
    return bytes(out)


def pict(px):
    """An 8-bit PICT 2 holding one PackBitsRect with its own colour table."""
    h, w = len(px), len(px[0])
    flat = [(p[:3] if opaque(p) else (255, 255, 255)) for row in px for p in row]
    colours = sorted(set(flat), key=lambda c: (c != (255, 255, 255), c))
    if len(colours) > 256:
        sys.exit("about picture has more than 256 colours")
    index = {c: i for i, c in enumerate(colours)}
    rect = struct.pack(">4h", 0, 0, h, w)
    row_bytes = (w + 1) & ~1

    d = bytearray()
    d += struct.pack(">HH", 0x0011, 0x02FF)                          # version 2
    d += struct.pack(">HhhII", 0x0C00, -2, 0, 0x00480000, 0x00480000) + rect + b"\0" * 4
    d += struct.pack(">HH", 0x001E, 0x0001) + struct.pack(">H", 10) + rect   # DefHilite; clip
    d += struct.pack(">H", 0x0098)                                   # PackBitsRect
    d += struct.pack(">H", row_bytes | 0x8000) + rect
    d += struct.pack(">hhIIIhhhhIII", 0, 0, 0, 0x00480000, 0x00480000, 0, 8, 1, 8, 0, 0, 0)
    d += struct.pack(">IHH", 0, 0, len(colours) - 1)
    for i, (r, g, b) in enumerate(colours):
        d += struct.pack(">4H", i, r * 257, g * 257, b * 257)
    d += rect + rect + struct.pack(">H", 0)                          # src, dst, srcCopy
    for y in range(h):
        row = bytes(index[c] for c in flat[y * w:(y + 1) * w]) + b"\0" * (row_bytes - w)
        packed = packbits(row) if row_bytes >= 8 else row
        d += (struct.pack(">B", len(packed)) if row_bytes <= 250 else struct.pack(">H", len(packed))) + packed
    if len(d) % 2:
        d += b"\0"
    d += struct.pack(">H", 0x00FF)
    return struct.pack(">H", (len(d) + 10) & 0xFFFF) + rect + bytes(d)


def rez(kind, rid, data):
    lines = [f"data '{kind}' ({rid}) {{"]
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16].hex().upper()
        lines.append('\t$"' + " ".join(chunk[j:j + 4] for j in range(0, len(chunk), 4)) + '"')
    return "\n".join(lines) + "\n};\n"


def preview(art, path, sizes, about):
    """What the Finder draws at 4-bit, 8-bit and 1-bit depth, 4x, on grey."""
    tiles = []
    for size, colour, bw in sizes:
        for table in (CLUT4, CLUT8, None):
            im = Image.new("RGB", (size, size), (204, 204, 204))
            for y in range(size):
                for x in range(size):
                    p = (bw if table is None else colour)[y][x]
                    if opaque(p):
                        im.putpixel((x, y), (0, 0, 0) if table is None and is_black(p) else
                                    (255, 255, 255) if table is None else rgb(table[nearest(table, p[:3])]))
            tiles.append(im.resize((size * 4, size * 4), Image.NEAREST))
    about_im = Image.new("RGB", (128, 128), (255, 255, 255))
    for y in range(128):
        for x in range(128):
            if opaque(about[y][x]):
                about_im.putpixel((x, y), about[y][x][:3])
    tiles.append(about_im.resize((256, 256), Image.NEAREST))
    out = Image.new("RGB", (sum(t.width + 16 for t in tiles) + 16, max(t.height for t in tiles) + 32), (238, 238, 238))
    x = 16
    for t in tiles:
        out.paste(t, (x, 16))
        x += t.width + 16
    out.save(path)


def main():
    art = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "lessbrokenssh-icons")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "lessbrokenssh-icons.r")

    c32, c16 = load(art, "icon-32.png", 32), load(art, "icon-16.png", 16)
    b32, b16 = load(art, "icon-32-bw.png", 32), load(art, "icon-16-bw.png", 16)
    c48, c128 = load(art, "icon-48.png", 48), load(art, "icon-128.png", 128)
    about = load(art, "about-128.png", 128)

    family = [
        ("ICN#", icon_list(b32)), ("icl4", indexed(c32, CLUT4, 4)), ("icl8", indexed(c32, CLUT8, 8)),
        ("ics#", icon_list(b16)), ("ics4", indexed(c16, CLUT4, 4)), ("ics8", indexed(c16, CLUT8, 8)),
    ]
    huge = [
        ("ich#", icon_list(c48)), ("ich4", indexed(c48, CLUT4, 4)), ("ich8", indexed(c48, CLUT8, 8)),
        ("ih32", rgb32(c48)), ("h8mk", mask8(c48)),
        ("il32", rgb32(c32)), ("l8mk", mask8(c32)),
        ("is32", rgb32(c16)), ("s8mk", mask8(c16)),
        ("it32", b"\0\0\0\0" + rgb32(c128)), ("t8mk", mask8(c128)),
    ]

    text = "/* generated by tools/icons/make_icons.py from docs/lessbrokenssh-icons/; do not edit */\n\n"
    for kind, data in family:
        text += rez(kind, "SSHEVEN_APPLICATION_ICON", data) + "\n"
    text += rez("icns", "SSHEVEN_APPLICATION_ICON", icns(family + huge)) + "\n"
    text += rez("PICT", "PICT_ABOUT", pict(about))
    # leave an unchanged file alone, so the build doesn't rerun Rez every time
    if not os.path.exists(out) or open(out).read() != text:
        with open(out, "w") as f:
            f.write(text)

    if len(sys.argv) > 3:
        preview(art, sys.argv[3], [(16, c16, b16), (32, c32, b32), (48, c48, c48)], about)


if __name__ == "__main__":
    main()
