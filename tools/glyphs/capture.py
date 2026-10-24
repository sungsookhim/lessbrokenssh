#!/usr/bin/env python3
"""List the non-ASCII characters a terminal session used, and how each draws.

Record a session on the server with script(1), e.g.

    script -q -c claude claude.log
    script -q -c btop btop.log

copy the logs here, and run

    capture.py claude.log btop.log

Each character is reported as one of
    glyph      there's a glyph for it (in glyphs/6x12)
    text       Monaco has it (Mac Roman)
    MISSING    neither; it draws as a lozenge. Add it to symbols.txt.

usage: capture.py [--size WxH] log...
"""

import argparse
import collections
import sys
import unicodedata

import glyphlib


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--size", default="6x12")
    ap.add_argument("logs", nargs="+")
    args = ap.parse_args()

    w, h = map(int, args.size.lower().split("x"))
    glyphs = glyphlib.load_set(w, h)

    counts = collections.Counter()
    for path in args.logs:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ch in f.read():
                if ord(ch) >= 128 and ch != "�":
                    counts[ch] += 1

    def status(ch):
        if ord(ch) in glyphs:
            return "glyph"
        try:
            ch.encode("mac_roman")
            return "text"
        except UnicodeEncodeError:
            return "MISSING"

    rows = sorted(counts.items(), key=lambda kv: (status(kv[0]) != "MISSING", -kv[1]))
    for ch, n in rows:
        print(f"{status(ch):8} {n:7}  U+{ord(ch):04X}  {ch}  {unicodedata.name(ch, '?').lower()}")

    missing = [ch for ch, _ in rows if status(ch) == "MISSING"]
    if missing:
        print(f"\n{len(missing)} missing; for symbols.txt:\n" + "\n".join(missing))


if __name__ == "__main__":
    sys.exit(main())
