#!/usr/bin/env python3
"""Draw box, block, shade, quadrant, sextant, Braille and Powerline glyphs.

Each glyph is drawn at SCALE times the cell size, then scaled down by area
averaging and thresholded to 1 bit, and written to glyphs/<W>x<H>/ as text
art for hand tuning. Hand-edited files (edited=yes) are left alone unless
--force is given.

Straight lines are placed on the small cell's pixel grid, so they come out
crisp and join up with neighbouring cells; curves, diagonals and dots get
the benefit of drawing large.

usage: procedural.py [--force] [--size WxH]
"""

import argparse
import re
import sys

from PIL import Image, ImageDraw

import glyphlib

SCALE = 8
THRESHOLD = 0.5


class Canvas:
    """A large drawing surface addressed in small-cell pixel units."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("L", (w * SCALE, h * SCALE), 0)
        self.draw = ImageDraw.Draw(self.img)

    def rect(self, x0, y0, x1, y1, ink=True):
        """Fill [x0, x1) x [y0, y1) in small pixels."""
        if x1 <= x0 or y1 <= y0:
            return
        self.draw.rectangle(
            [x0 * SCALE, y0 * SCALE, x1 * SCALE - 1, y1 * SCALE - 1], fill=255 if ink else 0
        )

    def polygon(self, points, ink=True):
        self.draw.polygon([(x * SCALE, y * SCALE) for x, y in points], fill=255 if ink else 0)

    def line(self, points, width=1.0):
        self.draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=255, width=round(width * SCALE))

    def quarter_ring(self, ox, oy, r, sx, sy, width=1.0):
        """Ink within width/2 of the circle around (ox, oy) of radius r, in the
        quarter on the (sx, sy) side of the centre (sx, sy are +1 or -1)."""
        px = self.img.load()
        for y in range(self.h * SCALE):
            for x in range(self.w * SCALE):
                fx, fy = (x + 0.5) / SCALE - ox, (y + 0.5) / SCALE - oy
                if fx * sx < 0 or fy * sy < 0:
                    continue
                if abs((fx * fx + fy * fy) ** 0.5 - r) <= width / 2:
                    px[x, y] = 255

    def ellipse(self, x0, y0, x1, y1):
        self.draw.ellipse([x0 * SCALE, y0 * SCALE, x1 * SCALE - 1, y1 * SCALE - 1], fill=255)

    def rows(self, threshold=THRESHOLD):
        """Scale down by area averaging and threshold to 1 bit."""
        small = self.img.resize((self.w, self.h), Image.BOX)
        cut = threshold * 255
        return [[1 if small.getpixel((x, y)) >= cut else 0 for x in range(self.w)] for y in range(self.h)]


# --- box drawing (U+2500-U+257F) --------------------------------------------

WEIGHTS = {"LIGHT": "light", "SINGLE": "light", "HEAVY": "heavy", "DOUBLE": "double"}
DIRS = {"UP": "u", "DOWN": "d", "LEFT": "l", "RIGHT": "r", "VERTICAL": "ud", "HORIZONTAL": "lr"}


def parse_box_name(name):
    """Turn a box drawing character name into its parts.

    Returns ("lines", {direction: weight}, dashes), ("arc", directions, 0) or
    ("diagonal", kind, 0).
    """
    n = name[len("BOX DRAWINGS "):]

    if " ARC " in f" {n} ":
        return "arc", "".join(DIRS[w] for w in n.split() if w in DIRS), 0
    if "DIAGONAL" in n:
        kind = "x" if "CROSS" in n else ("/" if "UPPER RIGHT TO LOWER LEFT" in n else "\\")
        return "diagonal", kind, 0

    dashes = 0
    m = re.search(r"\b(DOUBLE|TRIPLE|QUADRUPLE) DASH\b", n)
    if m:
        dashes = {"DOUBLE": 2, "TRIPLE": 3, "QUADRUPLE": 4}[m.group(1)]
        n = n.replace(m.group(0), "")

    arms = {}
    pending = []  # directions of clauses that haven't named their weight yet
    last = None
    for clause in n.split(" AND "):
        weight = None
        dirs = ""
        for word in clause.split():
            if word in WEIGHTS:
                weight = WEIGHTS[word]
            elif word in DIRS:
                dirs += DIRS[word]
            else:
                raise ValueError(f"unexpected word {word!r} in {name!r}")
        # "LIGHT DOWN AND RIGHT": a clause without a weight shares the previous one
        if weight is None:
            weight = last
        if weight is None:
            pending.append(dirs)
            continue
        for d in "".join(pending) + dirs:
            arms[d] = weight
        pending = []
        last = weight
    if pending or not arms:
        raise ValueError(f"can't work out the weights in {name!r}")
    return "lines", arms, dashes


def stroke_span(center, weight):
    """Pixel span [lo, hi) a line of this weight covers across its direction."""
    if weight == "light":
        return center, center + 1
    if weight == "heavy":
        return center, center + 2
    return center - 1, center + 2  # double: two 1 px lines around a 1 px gap


def draw_box_lines(c, arms, dashes):
    w, h = c.w, c.h
    cx, cy = (w - 1) // 2, (h - 1) // 2

    def span_union(spans, default):
        spans = [s for s in spans if s]
        if not spans:
            return default
        return min(s[0] for s in spans), max(s[1] for s in spans)

    # how far the vertical strokes reach sideways, and the horizontal ones up and down,
    # so arms run into the middle far enough to join
    vcore = span_union([stroke_span(cx, arms[d]) for d in "ud" if d in arms], (cx, cx + 1))
    hcore = span_union([stroke_span(cy, arms[d]) for d in "lr" if d in arms], (cy, cy + 1))

    def arm_rect(d, weight):
        if d in "lr":
            y0, y1 = stroke_span(cy, weight)
            return (vcore[0], y0, w, y1) if d == "r" else (0, y0, vcore[1], y1)
        x0, x1 = stroke_span(cx, weight)
        return (x0, hcore[0], x1, h) if d == "d" else (x0, 0, x1, hcore[1])

    # doubles: fill a 3 px band, then cut the 1 px gap down its middle
    for d, weight in arms.items():
        if weight == "double":
            c.rect(*arm_rect(d, weight))
    for d, weight in arms.items():
        if weight == "double":
            gap = {"r": (cx, cy, w, cy + 1), "l": (0, cy, cx + 1, cy + 1),
                   "d": (cx, cy, cx + 1, h), "u": (cx, 0, cx + 1, cy + 1)}[d]
            c.rect(*gap, ink=False)
    # light and heavy arms go on top, repairing any gap the doubles cut through them
    for d, weight in arms.items():
        if weight != "double":
            c.rect(*arm_rect(d, weight))

    if dashes:
        # break the line into evenly spaced dashes, about 60% ink
        length = w if "l" in arms else h
        period = length / dashes
        for i in range(dashes):
            gap0 = i * period + period * 0.6
            gap1 = (i + 1) * period
            if "l" in arms:
                c.rect(gap0, 0, gap1, h, ink=False)
            else:
                c.rect(0, gap0, w, gap1, ink=False)


def draw_box_arc(c, dirs):
    """Rounded corners ╭╮╰╯: a quarter circle on the light line's centre."""
    w, h = c.w, c.h
    lx, ly = (w - 1) // 2 + 0.5, (h - 1) // 2 + 0.5  # centre of the light lines
    r = min(w, h) / 2 - 0.5
    sx = 1 if "r" in dirs else -1
    sy = 1 if "d" in dirs else -1
    ox, oy = lx + sx * r, ly + sy * r  # circle centre
    # the quarter of the circle facing back towards the cell centre
    c.quarter_ring(ox, oy, r, -sx, -sy)
    # straight runs from the arc to the cell edges
    c.line([(ox, ly), (w if sx > 0 else 0, ly)])
    c.line([(lx, oy), (lx, h if sy > 0 else 0)])


def draw_box_diagonal(c, kind):
    w, h = c.w, c.h
    if kind in "/x":
        c.line([(w, 0), (0, h)], width=1.2)
    if kind in "\\x":
        c.line([(0, 0), (w, h)], width=1.2)


def box_glyph(c, cp):
    kind, arg, dashes = parse_box_name(glyphlib.char_name(cp))
    if kind == "lines":
        draw_box_lines(c, arg, dashes)
        return c.rows()
    if kind == "arc":
        draw_box_arc(c, arg)
        return c.rows()
    draw_box_diagonal(c, arg)
    return c.rows(threshold=0.4)


# --- block elements (U+2580-U+259F) -----------------------------------------

def eighths(n, length):
    return int(length * n / 8 + 0.5)


def shade(c, density):
    """25/50/75% dither patterns, aligned so neighbouring cells tile."""
    for y in range(c.h):
        for x in range(c.w):
            # one dot in every 2x2, staggered on alternate dot rows
            sparse = y % 2 == 0 and (x + y // 2) % 2 == 0
            on = {1: sparse, 2: (x + y) % 2 == 0, 3: not sparse}[density]
            if on:
                c.rect(x, y, x + 1, y + 1)


QUADRANTS = {  # bits: 1 upper left, 2 upper right, 4 lower left, 8 lower right
    0x2596: 4, 0x2597: 8, 0x2598: 1, 0x2599: 1 | 4 | 8, 0x259A: 1 | 8,
    0x259B: 1 | 2 | 4, 0x259C: 1 | 2 | 8, 0x259D: 2, 0x259E: 2 | 4, 0x259F: 2 | 4 | 8,
}


def quadrants(c, bits):
    hw, hh = c.w // 2, c.h // 2
    if bits & 1: c.rect(0, 0, hw, hh)
    if bits & 2: c.rect(hw, 0, c.w, hh)
    if bits & 4: c.rect(0, hh, hw, c.h)
    if bits & 8: c.rect(hw, hh, c.w, c.h)


def block_glyph(c, cp):
    w, h = c.w, c.h
    if cp == 0x2580: c.rect(0, 0, w, h // 2)                       # ▀
    elif 0x2581 <= cp <= 0x2588:                                   # ▁ .. █
        c.rect(0, h - eighths(cp - 0x2580, h), w, h)
    elif 0x2589 <= cp <= 0x258F:                                   # ▉ .. ▏
        c.rect(0, 0, eighths(0x2590 - cp, w), h)
    elif cp == 0x2590: c.rect(w // 2, 0, w, h)                     # ▐
    elif 0x2591 <= cp <= 0x2593: shade(c, cp - 0x2590)             # ░ ▒ ▓
    elif cp == 0x2594: c.rect(0, 0, w, eighths(1, h))              # ▔
    elif cp == 0x2595: c.rect(w - eighths(1, w), 0, w, h)          # ▕
    else: quadrants(c, QUADRANTS[cp])                              # ▖ .. ▟
    return c.rows()


# --- sextants (U+1FB00-U+1FB3B) ---------------------------------------------

def sextant_patterns():
    """Code point -> 2x3 bit pattern (bit 0 top left ... bit 5 bottom right).

    Unicode skips the patterns that already exist elsewhere: empty, full,
    left half (▌) and right half (▐).
    """
    cp = 0x1FB00
    out = {}
    for bits in range(1, 63):
        if bits in (0b010101, 0b101010):
            continue
        out[cp] = bits
        cp += 1
    return out


def sextant_glyph(c, bits):
    xs = [0, c.w // 2, c.w]
    ys = [0, c.h // 3, 2 * c.h // 3, c.h]
    for i in range(6):
        if bits & (1 << i):
            col, row = i % 2, i // 2
            c.rect(xs[col], ys[row], xs[col + 1], ys[row + 1])
    return c.rows()


# --- Braille (U+2800-U+28FF) -------------------------------------------------

# dot number -> (column, row); bit n of (cp - 0x2800) is dot n+1
BRAILLE_DOTS = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]


def braille_glyph(c, cp):
    """2x4 dots on an even pitch that continues across cell borders, so
    btop's graphs don't show seams. At 6x12 that's 2x2 px dots every 3 px."""
    pitch_x, pitch_y = c.w / 2, c.h / 4
    dot = max(1, round(min(pitch_x, pitch_y) * 2 / 3))
    bits = cp - 0x2800
    for n, (col, row) in enumerate(BRAILLE_DOTS):
        if bits & (1 << n):
            x0, y0 = int(col * pitch_x), int(row * pitch_y)
            c.ellipse(x0, y0, x0 + dot, y0 + dot)
    return c.rows(threshold=0.3)


# --- Powerline separators (private use) --------------------------------------

def powerline_glyph(c, cp):
    w, h = c.w, c.h
    if cp == 0xE0B0: c.polygon([(0, 0), (w, h / 2), (0, h)])              # solid right
    elif cp == 0xE0B2: c.polygon([(w, 0), (0, h / 2), (w, h)])            # solid left
    elif cp == 0xE0B1: c.line([(0, 0), (w - 0.5, h / 2), (0, h)])         # thin right
    elif cp == 0xE0B3: c.line([(w, 0), (0.5, h / 2), (w, h)])             # thin left
    return c.rows(threshold=0.4)


# --- driver ------------------------------------------------------------------

def all_glyphs():
    """(code point, drawing function) for everything this script makes."""
    for cp in range(0x2500, 0x2580):
        yield cp, box_glyph
    for cp in range(0x2580, 0x25A0):
        yield cp, block_glyph
    for cp, bits in sextant_patterns().items():
        yield cp, (lambda c, _cp, bits=bits: sextant_glyph(c, bits))
    for cp in range(0x2800, 0x2900):
        yield cp, braille_glyph
    for cp in (0xE0B0, 0xE0B1, 0xE0B2, 0xE0B3):
        yield cp, powerline_glyph


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="overwrite hand-edited glyphs too")
    ap.add_argument("--size", help="only this cell size, as WxH")
    args = ap.parse_args()

    sizes = glyphlib.CELL_SIZES
    if args.size:
        w, h = map(int, args.size.lower().split("x"))
        sizes = [(w, h)]

    for w, h in sizes:
        written = kept = 0
        for cp, fn in all_glyphs():
            rows = fn(Canvas(w, h), cp)
            if glyphlib.write_glyph(w, h, cp, rows, "procedural", force=args.force):
                written += 1
            else:
                kept += 1
        print(f"{w}x{h}: wrote {written} glyphs, kept {kept} hand-edited")


if __name__ == "__main__":
    sys.exit(main())
