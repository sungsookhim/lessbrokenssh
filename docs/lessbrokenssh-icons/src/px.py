"""Tiny pixel canvas for the lessbrokenssh icons: exact pixels, palette colours, generated 1-px black outlines."""
import math
from PIL import Image

# Mac OS 4-bit system palette (clut 4)
P4 = dict(W=(255, 255, 255), Y=(252, 243, 5), O=(255, 100, 2), R=(221, 8, 6), P=(242, 8, 132), V=(70, 0, 165),
          U=(0, 0, 212), C=(2, 171, 234), G=(31, 183, 20), g=(0, 100, 17), B=(86, 44, 5), T=(144, 113, 58),
          L=(192, 192, 192), M=(128, 128, 128), D=(64, 64, 64), K=(0, 0, 0))
PAL4 = set(P4.values())


def pal8():
    v = [0xFF, 0xCC, 0x99, 0x66, 0x33, 0x00]
    cube = {(r, g, b) for r in v for g in v for b in v}
    ramp = [0xEE, 0xDD, 0xBB, 0xAA, 0x88, 0x77, 0x55, 0x44, 0x22, 0x11]
    for x in ramp:
        cube |= {(x, 0, 0), (0, x, 0), (0, 0, x), (x, x, x)}
    return cube


PAL8 = pal8()


def c(v):
    return P4[v] if isinstance(v, str) else v


class Canvas:
    def __init__(self, n):
        self.n = n
        self.px = {}

    def set(self, x, y, col):
        if 0 <= x < self.n and 0 <= y < self.n:
            if col is None:
                self.px.pop((x, y), None)
            else:
                self.px[(x, y)] = c(col)

    def put(self, pts, col):
        for x, y in pts:
            self.set(x, y, col)

    def rect(self, x0, y0, x1, y1, col):
        self.put(rect(x0, y0, x1, y1), col)

    def outline(self, mask, col="K", diag=True):
        ring = set()
        nb = [(-1, 0), (1, 0), (0, -1), (0, 1)] + ([(-1, -1), (1, -1), (-1, 1), (1, 1)] if diag else [])
        for x, y in mask:
            for dx, dy in nb:
                if (x + dx, y + dy) not in mask:
                    ring.add((x + dx, y + dy))
        self.put(ring, col)
        return ring

    def text(self, x, y, s, col, font):
        for ch in s:
            rows = font[ch]
            for j, row in enumerate(rows):
                for i, b in enumerate(row):
                    if b == "#":
                        self.set(x + i, y + j, col)
            x += len(rows[0]) + 1
        return x

    def image(self):
        im = Image.new("RGBA", (self.n, self.n), (0, 0, 0, 0))
        for (x, y), col in self.px.items():
            im.putpixel((x, y), col + (255,))
        return im


def rect(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def disc(cx, cy, r):
    """Pixels whose centres lie within r of (cx, cy); use .5 centres for odd sizes."""
    return {(x, y) for x in range(int(cx - r) - 1, int(cx + r) + 2) for y in range(int(cy - r) - 1, int(cy + r) + 2)
            if (x + .5 - cx) ** 2 + (y + .5 - cy) ** 2 <= r * r}


def thick(x0, y0, x1, y1, w):
    """Pixels whose centres lie within w/2 of the segment."""
    out = set()
    for x in range(int(min(x0, x1) - w) - 1, int(max(x0, x1) + w) + 2):
        for y in range(int(min(y0, y1) - w) - 1, int(max(y0, y1) + w) + 2):
            px, py = x + .5, y + .5
            dx, dy = x1 - x0, y1 - y0
            t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
            if math.hypot(px - x0 - t * dx, py - y0 - t * dy) <= w / 2:
                out.add((x, y))
    return out


def check(im, pal):
    bad = [p for p in im.getdata() if p[3] not in (0, 255) or (p[3] == 255 and p[:3] not in pal)]
    return len(bad)


def zoom(im, k, bg=(255, 255, 255)):
    base = Image.new("RGB", im.size, bg)
    base.paste(im, mask=im.split()[3])
    return base.resize((im.width * k, im.height * k), Image.NEAREST)


def roundel(x0, y0, widths):
    """Hand-shaped round blob: one centred run per row, e.g. [4, 8, 10, 10, 12, ...]."""
    w = max(widths)
    return {(x0 + (w - n) // 2 + i, y0 + j) for j, n in enumerate(widths) for i in range(n)}


def art(cv, x0, y0, rows, colours):
    """Paint an ASCII block; '.' leaves the pixel alone."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                cv.set(x0 + i, y0 + j, colours.get(ch, ch))
