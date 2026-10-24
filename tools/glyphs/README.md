glyph tools
-----------

Make the bitmaps that lessbrokenssh draws for characters the Mac's font doesn't have. The design is in [docs/design/0001-plan.md](../../docs/design/0001-plan.md).

```
glyphs/6x12/2500.txt      one text-art file per glyph per cell size (the source of truth)
        │  tools/glyphs/pack.py        runs on every ./build.sh
        ▼
glyphs.r                  'GLYF' resource, included from ssheven.r (generated, committed)
```

### Making and tuning glyphs

```
./build.sh glyphs
```

This does three things:

1. Redraws the procedural glyphs (box, block, shade, quadrant, sextant, Braille, Powerline) with `procedural.py`, skipping any you've hand-edited.
2. Packs everything into `glyphs.r`.
3. Writes `build-glyphs/preview-6x12.png`, which has the test pattern rendered with the glyphs (grey boxes are characters with no glyph yet) and every glyph zoomed in on its pixel grid.

To fix a glyph, open its file, for example `glyphs/6x12/256D.txt` for `╭`:

```
# U+256D BOX DRAWINGS LIGHT ARC DOWN AND RIGHT  source=procedural  edited=no
......
......
......
......
......
...###
..##..
..#...
..#...
..#...
..#...
..#...
```

Edit the pixels (`#` ink, `.` paper), then change `edited=no` to `edited=yes` so the generator never overwrites your version. Run `./build.sh glyphs` again to check the preview, then `./build.sh g3` (or another target) to try it on a Mac.

To throw away hand edits and regenerate everything, run `python3 tools/glyphs/procedural.py --force`.

### Rules

- Every file in `glyphs/WxH/` must be exactly W pixels wide and H rows tall; `pack.py` stops with an error otherwise.
- Box drawing lines sit on column 2 and row 5 (light) or columns 2–3 and rows 5–6 (heavy) of a 6×12 cell. Keep edits on those lines, or neighbouring cells won't join up.
- Braille dots are 2×2 px on a 3 px pitch that carries on into the next cell, which keeps btop's graphs seamless.
