"""lessbrokenssh icons, design B: System 7 window with a terminal, and an SSH key whose bow is a smiley.

  icons.py <out_dir>    writes every PNG plus preview.png
Colour icons use the 4-bit Mac palette only; icon-128 and about-128 also use the 8-bit palette.
`bw=True` draws the hand-made 1-bit version of the same art (not a threshold).
"""
import os, sys
from PIL import Image
from px import Canvas, rect, roundel, art, check, zoom, PAL4, PAL8


def shifted(im, dx, dy):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (dx, dy))
    return out


def icon32(bw=False):
    cv = Canvas(32)
    cv.put(rect(0, 0, 28, 23), "K")
    cv.rect(1, 1, 27, 22, "W" if bw else "L")
    cv.put(rect(3, 2, 5, 4) - {(4, 3)}, "K")                        # close box
    for y in (2, 4):
        cv.rect(7, y, 26, y, "K" if bw else "D")                    # title stripes
    cv.rect(1, 6, 27, 6, "K")
    cv.rect(2, 8, 26, 21, "K")                                      # terminal screen
    cv.put((rect(4, 9, 20, 15) - rect(5, 10, 19, 14)) - {(4, 9), (20, 9), (4, 15), (20, 15)}, "W")  # rounded box
    cv.rect(6, 11, 17, 11, "W" if bw else "G")
    if bw:
        cv.rect(6, 13, 14, 13, "W")
    else:
        cv.rect(6, 13, 11, 13, "Y"), cv.rect(12, 13, 14, 13, "R")
    cv.put([(4, 18), (5, 17), (7, 17), (8, 18), (10, 18), (11, 17), (13, 17), (14, 18), (16, 18)], "W")  # braille graph
    # key: smiley bow on the right, shaft to the left, teeth hanging down
    bow = roundel(18, 14, [4, 8, 10, 10, 12, 12, 12, 12, 10, 10, 8, 4])
    shaft = rect(7, 20, 18, 22)
    teeth = rect(8, 23, 9, 25) | rect(11, 23, 12, 24) | {(14, 23)}
    cv.outline(bow | shaft | teeth)
    gold, shade = ("W", "W") if bw else ("Y", "T")
    cv.put(bow, gold)
    cv.rect(7, 20, 18, 21, gold), cv.rect(7, 22, 18, 22, shade)
    cv.put(teeth, shade)
    cv.put([(21, 17), (21, 18), (26, 17), (26, 18)], "K")          # eyes
    cv.put([(20, 21), (27, 21), (21, 22), (26, 22), (22, 23), (23, 23), (24, 23), (25, 23)], "K")  # smile
    return shifted(cv.image(), 0, 2)


def icon16(bw=False):
    cv = Canvas(16)
    stripe = "K" if bw else "D"
    art(cv, 0, 0, ["KKKKKKKKKKKKKK",
                   "KLLLLLLLLLLLLK",
                   "KLSSSSSSSSSSLK",
                   "KLLLLLLLLLLLLK",
                   "KKKKKKKKKKKKKK",
                   "KLKKKKKKKKKKLK",
                   "KLKKKKKKKKKKLK",
                   "KLKKKKKKKKKKLK",
                   "KLKKKKKKKKKKLK",
                   "KLKKKKKKKKKKLK",
                   "KLKKKKKKKKKKLK",
                   "KLLLLLLLLLLLLK",
                   "KKKKKKKKKKKKKK"], {"L": "W" if bw else "L", "S": stripe})
    cv.rect(3, 5, 7, 5, "W" if bw else "G")
    if bw:
        cv.rect(3, 7, 6, 7, "W")
    else:
        cv.rect(3, 7, 5, 7, "Y"), cv.set(6, 7, "R")
    cv.put([(3, 9), (5, 9), (7, 9)], "W")
    bow = roundel(9, 8, [4, 6, 6, 6, 6, 4])
    shaft = rect(3, 11, 8, 12)
    teeth = rect(3, 13, 4, 14) | {(6, 13)}
    cv.outline(bow | shaft | teeth)
    gold, shade = ("W", "W") if bw else ("Y", "T")
    cv.put(bow, gold)
    cv.rect(3, 11, 8, 11, gold), cv.rect(3, 12, 8, 12, shade)
    cv.put(teeth, shade)
    cv.put([(10, 9), (13, 9), (10, 11), (13, 11), (11, 12), (12, 12)], "K")
    return cv.image()


def build():
    import big
    bwpal = {(0, 0, 0), (255, 255, 255)}
    c48, o48 = big.icon48()
    c128, o128 = big.icon128()
    cab, oab = big.icon128(about=True)
    return {"icon-32.png": (icon32(), PAL4), "icon-32-bw.png": (icon32(True), bwpal),
            "icon-16.png": (icon16(), PAL4), "icon-16-bw.png": (icon16(True), bwpal),
            "icon-48.png": (shifted(c48.image(), *o48), PAL4),
            "icon-128.png": (shifted(c128.image(), *o128), PAL8),
            "about-128.png": (shifted(cab.image(), *oab), PAL8)}


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    made = build()
    for name, (im, pal) in made.items():
        im.save(os.path.join(out, name))
        print(f"{name:15} {im.size}  off-palette or partial-alpha pixels: {check(im, pal)}")
    big_tiles = [zoom(made[n][0], k) for n, k in (("about-128.png", 4), ("icon-128.png", 4))]
    small = [zoom(made[n][0], k) for n, k in (("icon-48.png", 8), ("icon-32.png", 12), ("icon-32-bw.png", 12),
                                              ("icon-16.png", 24), ("icon-16-bw.png", 24))]
    sheet = Image.new("RGB", (1990, 512 + 10 + 400), (200, 200, 200))
    sheet.paste(big_tiles[0], (10, 10)); sheet.paste(big_tiles[1], (530, 10))
    x = 10
    for t in small:
        sheet.paste(t, (x, 532)); x += t.width + 10
    x = 1060
    for n in made:                                                   # actual size
        im = zoom(made[n][0], 1)
        sheet.paste(im, (x, 10)); x += im.width + 8 if im.width < 100 else 0
    sheet.save(os.path.join(out, "preview.png"))
