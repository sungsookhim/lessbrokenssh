"""lessbrokenssh large art: icon-48 (4-bit palette), icon-128 and about-128 (8-bit palette)."""
import math
from px import Canvas, rect, roundel, art, disc, thick

# 8-bit Mac palette colours used here (all from the 6x6x6 cube or the grey ramp)
W, K = (255, 255, 255), (0, 0, 0)
PLAT = (221, 221, 221)          # DDDDDD platinum
PLAT_D = (187, 187, 187)        # BBBBBB
SHADOW = (136, 136, 136)        # 888888
STRIPE = (119, 119, 119)        # 777777
GOLD_HI, GOLD, GOLD_SH, GOLD_DK = (255, 255, 153), (255, 204, 0), (204, 153, 0), (153, 102, 0)
GREEN, RED, CYAN, BLUE, YELLOW = (0, 204, 0), (255, 51, 51), (0, 204, 255), (51, 102, 255), (255, 255, 0)
ORANGE, GREY = (255, 153, 0), (102, 102, 102)

FONT = {  # 3x5
    "1": [".#.", "##.", ".#.", ".#.", "###"], "2": ["##.", "..#", ".#.", "#..", "###"],
    "[": ["##.", "#..", "#..", "#..", "##."], "]": [".##", "..#", "..#", "..#", ".##"],
    "M": ["#.#", "###", "###", "#.#", "#.#"], "C": [".##", "#..", "#..", "#..", ".##"],
    "P": ["##.", "#.#", "##.", "#..", "#.."], "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "$": [".##", "##.", ".#.", ".##", "##."], "~": ["...", ".#.", "#.#", "...", "..."],
    "L": ["#..", "#..", "#..", "#..", "###"], "E": ["###", "#..", "##.", "#..", "###"],
    "S": [".##", "#..", ".#.", "..#", "##."], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "O": [".#.", "#.#", "#.#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "N": ["##.", "#.#", "#.#", "#.#", "#.#"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"], " ": ["...", "...", "...", "...", "..."],
}
CHECK = [".......", "......#", ".....##", "#...##.", "##.##..", ".###...", "..#...."]
STAR = ["...#...", "...#...", "#######", ".#####.", "..###..", ".##.##.", "##...##"]
HEART = [".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."]


def icon48():
    cv = Canvas(48)
    cv.put(rect(0, 0, 42, 35), "K")
    cv.rect(1, 1, 41, 34, "L")
    cv.put(rect(3, 2, 7, 6) - rect(4, 3, 6, 5), "K")                 # close box
    for y in (2, 4, 6):
        cv.rect(9, y, 40, y, "D")
    cv.rect(1, 8, 41, 8, "K")
    cv.rect(3, 10, 39, 32, "K")                                     # screen
    cv.put((rect(5, 11, 32, 20) - rect(6, 12, 31, 19)) - {(5, 11), (32, 11), (5, 20), (32, 20)}, "W")
    cv.rect(8, 13, 27, 13, "G")
    cv.rect(8, 15, 18, 15, "Y"), cv.rect(19, 15, 22, 15, "R")
    cv.rect(8, 17, 14, 17, "C")
    for i, h in enumerate([1, 2, 3, 2, 3, 3, 2, 1, 2, 3, 2, 1]):  # braille area graph
        for k in range(h):
            cv.set(5 + 2 * i, 27 - 2 * k, "W")
    bow = roundel(27, 21, [6, 10, 12, 14, 16, 16, 18, 18, 18, 18, 18, 18, 16, 16, 14, 12, 10, 6])
    shaft = rect(10, 29, 27, 32)
    teeth = rect(11, 33, 13, 36) | rect(16, 33, 18, 35) | rect(21, 33, 22, 34)
    cv.outline(bow | shaft | teeth)
    cv.rect(10, 29, 27, 31, "Y"), cv.rect(10, 32, 27, 32, "T")
    cv.put(teeth, "T")
    cv.put(bow, "Y")
    cv.put(rect(31, 25, 32, 27) | rect(38, 25, 39, 27), "K")        # eyes
    cv.put([(30, 31), (41, 31), (31, 32), (40, 32), (32, 33), (33, 33), (38, 33), (39, 33)] +
           [(x, 34) for x in range(34, 38)], "K")                   # smile
    return cv, (1, 4)


def icon128(about=False):
    cv = Canvas(128)
    # window frame
    cv.put(rect(4, 6, 115, 97), K)
    cv.put(rect(5, 7, 114, 96), PLAT)
    for y in (9, 11, 13, 15, 17):
        cv.put(rect(22, y, 97, y), STRIPE)
        cv.put(rect(22, y + 1, 97, y + 1), W)
    if about:
        cv.put(rect(31, 9, 88, 18), PLAT)
        cv.text(34, 11, "LESSBROKENSSH", K, FONT)
    for x0 in (10, 101):                                            # close box, zoom box
        cv.put(rect(x0, 9, x0 + 8, 17), K)
        cv.put(rect(x0 + 1, 10, x0 + 7, 16), PLAT_D)
        cv.put(rect(x0 + 1, 10, x0 + 6, 10) | rect(x0 + 1, 10, x0 + 1, 15), W)
        cv.put(rect(x0 + 2, 16, x0 + 7, 16) | rect(x0 + 7, 11, x0 + 7, 16), SHADOW)
    cv.put(rect(101, 9, 105, 13) - rect(102, 10, 104, 12), K)      # zoom box's inner square
    cv.put(rect(5, 20, 114, 20), K)
    cv.put(rect(5, 21, 113, 21) | rect(5, 21, 5, 95), W)            # body bevel
    cv.put(rect(114, 21, 114, 96) | rect(5, 96, 114, 96), SHADOW)
    cv.put(rect(9, 24, 110, 24) | rect(9, 24, 9, 92), SHADOW)       # screen well
    cv.put(rect(9, 92, 110, 92) | rect(110, 24, 110, 92), W)
    cv.put(rect(10, 25, 109, 91), K)

    # htop meters
    meters = [("1", [(GREEN, 14), (RED, 4)]), ("2", [(GREEN, 9), (RED, 2), (BLUE, 2)]),
              ("M", [(GREEN, 12), (BLUE, 3), (YELLOW, 5)])]
    for row, (label, segs) in enumerate(meters):
        y = 28 + row * 7
        cv.text(13, y, label + "[", W, FONT)
        x = 21
        for col, n in segs:
            for _ in range(n):
                cv.put(rect(x, y, x, y + 4), col)
                x += 2
        cv.text(64, y, "]", W, FONT)
    if about:
        for x, glyph, col in ((74, CHECK, GREEN), (84, STAR, YELLOW), (94, HEART, RED)):
            art(cv, x, 27, glyph, {"#": col})
    cv.text(74, 40 if about else 30, "$", W, FONT)
    cv.put(rect(78, 40 if about else 30, 80, 44 if about else 34), W)  # block cursor

    # btop-style rounded box with a braille area graph
    box = (rect(12, 50, 70, 88) - rect(13, 51, 69, 87)) - {(12, 50), (70, 50), (12, 88), (70, 88)}
    cv.put(box, SHADOW)
    cv.put(rect(15, 48, 29, 52), K)
    cv.text(17, 48, "CPU", W, FONT)
    for i in range(28):
        h = max(1, min(16, round(7 + 4 * math.sin(i / 2.5) + 3 * math.sin(i / 1.1 + 1))))
        for k in range(h):
            y = 86 - 2 * k
            cv.set(14 + 2 * i, y, GREEN if y > 74 else YELLOW if y > 64 else RED)

    # the key: smiley bow, shaft to the left, teeth down
    cx, cy, r = 100, 100, 22.5
    bow = disc(cx, cy, r)
    shaft = rect(28, 94, 80, 105) - {(28, 94), (28, 105)}
    teeth = rect(32, 106, 41, 115) | rect(47, 106, 54, 112) | rect(59, 106, 64, 110)
    cv.outline(bow | shaft | teeth, K)
    cv.put(rect(28, 96, 80, 102) & shaft, GOLD)
    cv.put(rect(28, 94, 80, 95) & shaft, GOLD_HI)
    cv.put(rect(28, 103, 80, 105) & shaft, GOLD_SH)
    cv.put(teeth, GOLD_SH)
    cv.put({(x, y) for x, y in teeth if (x, y + 1) not in teeth}, GOLD_DK)
    for x, y in bow:                                                # light from the upper left
        d = math.hypot(x + .5 - cx, y + .5 - cy)
        lit = math.hypot(x + .5 - (cx - 9), y + .5 - (cy - 9)) / r
        cv.set(x, y, GOLD_DK if d > r - 1.5 and lit > 1.25 else GOLD_SH if lit > 1.32 else
               GOLD_HI if math.hypot(x + .5 - (cx - 13), y + .5 - (cy - 14)) < 4.6 else GOLD)
    cv.put(disc(cx - 14, cy - 15, 1.6), W)                          # specular glint
    for ex in (cx - 8, cx + 8):
        cv.put(thick(ex, cy - 11, ex, cy - 4, 5), K)                # eyes
    mouth = {(x, y) for x in range(int(cx - 18), int(cx + 18)) for y in range(int(cy), int(cy + 18))
             if 12.5 <= math.hypot(x + .5 - cx, y + .5 - (cy - 1)) <= 16
             and 25 <= math.degrees(math.atan2(y + .5 - (cy - 1), x + .5 - cx)) <= 155}
    cv.put(mouth, K)
    return cv, (0, 3)
