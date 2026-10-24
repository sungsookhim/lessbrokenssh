"""Shared helpers for the glyph tools: reading and writing glyph text-art files.

A glyph file (glyphs/<W>x<H>/<CODEPOINT>.txt) looks like:

    # U+2580 UPPER HALF BLOCK  source=procedural  edited=no
    ######
    ......

One line per pixel row, '#' for ink and '.' for paper. Set edited=yes after
editing by hand; the generators then leave the file alone unless --force.
"""

import os
import re
import unicodedata

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
GLYPH_DIR = os.path.join(ROOT, "glyphs")

# cell sizes we make glyph sets for, as (width, height)
CELL_SIZES = [(6, 12)]

HEADER_RE = re.compile(r"^#\s*U\+([0-9A-Fa-f]+)\b(.*)$")


def set_dir(w, h):
    return os.path.join(GLYPH_DIR, f"{w}x{h}")


def glyph_path(w, h, cp):
    return os.path.join(set_dir(w, h), f"{cp:04X}.txt")


def char_name(cp):
    return unicodedata.name(chr(cp), f"<U+{cp:04X}>")


def read_glyph(path):
    """Returns (codepoint, rows as list of lists of 0/1, header fields dict)."""
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]
    m = HEADER_RE.match(lines[0])
    if not m:
        raise ValueError(f"{path}: first line must be '# U+XXXX ...'")
    cp = int(m.group(1), 16)
    fields = dict(re.findall(r"(\w+)=(\S+)", m.group(2)))
    rows = []
    for n, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        if set(line) - set("#."):
            raise ValueError(f"{path}:{n}: only '#' and '.' allowed")
        rows.append([1 if c == "#" else 0 for c in line])
    return cp, rows, fields


def is_edited(path):
    if not os.path.exists(path):
        return False
    try:
        return read_glyph(path)[2].get("edited", "no") == "yes"
    except ValueError:
        # a broken file is someone's work in progress; don't clobber it
        return True


def write_glyph(w, h, cp, rows, source, force=False):
    """Writes a glyph file unless it was hand-edited. Returns True if written."""
    path = glyph_path(w, h, cp)
    if not force and is_edited(path):
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# U+{cp:04X} {char_name(cp)}  source={source}  edited=no\n")
        for row in rows:
            f.write("".join("#" if p else "." for p in row) + "\n")
    return True


def load_set(w, h):
    """All glyphs of one cell size as {codepoint: rows}, checking their size."""
    glyphs = {}
    d = set_dir(w, h)
    if not os.path.isdir(d):
        return glyphs
    for name in sorted(os.listdir(d)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(d, name)
        cp, rows, _ = read_glyph(path)
        if len(rows) != h or any(len(r) != w for r in rows):
            raise ValueError(f"{path}: must be {w}x{h}, is {max(map(len, rows))}x{len(rows)}")
        glyphs[cp] = rows
    return glyphs
