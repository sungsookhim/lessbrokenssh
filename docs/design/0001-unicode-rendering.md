0001: Unicode rendering
=======================

- **Status:** draft
- **Date:** 2026-10-23
- **Scope:** first feature update for lessbrokenssh

## Summary

Make the terminal draw what modern full-screen programs actually send: box drawing, block elements, symbols, emoji, and (where possible) Korean, Japanese and Chinese text. The main targets are the Claude CLI and btop running on an EC2 host.

The plan keeps a fast bitmap font for ordinary text and adds a **glyph atlas** for everything else:

1. **Base characters** (ASCII and Mac Roman) stay on the existing fast path: a bitmap font through `DrawText`.
2. **Symbols** (`⏺ ✻ ❯ ✓ …`) come from bitmaps exported at build time from a known good font.
3. **Block and box characters** (`─ │ ╭ ▀ ▌ █ ⣿ …`) are drawn by code into the atlas at the current cell size, so they line up perfectly with no gaps.
4. **Emoji** are pre-rendered color bitmaps in 16-color and 256-color versions, plus a mask.
5. **CJK** uses the system's own fonts on the 800×600 iMac when they're installed. Otherwise it falls back to a 1- or 2-cell replacement glyph chosen from a table.

## Background: what happens today

Every cell is converted to one Mac Roman byte before drawing (`ssheven-console.c`, `draw_screen_color` and `draw_screen_fast`):

- **ASCII** draws normally in Monaco at `prefs.font_size` (default 9).
- **U+0080–U+FFFF** goes through `map_unicode()` (`ssheven-unicode.h`). That's a lookup table of nearest-ASCII lookalikes, such as `é` → `e`. Anything not in the table becomes the lozenge `◊`. The table has no entries for box drawing or block elements, so U+2500–U+259F all become `◊`.
- **Above U+FFFF** (all emoji) always becomes `◊`.
- **Wide characters:** libvterm gives the cell `width = 2` and returns `0xFFFFFFFF` in `chars[0]` for the right-half continuation cell. The drawing code treats that as one more character above U+FFFF, so a wide character draws as `◊◊`.
- **Color:** only `fg.indexed.idx` and `bg.indexed.idx` are read, and they're mapped to the 8 classic QuickDraw colors. RGB colors (256-color and truecolor) are read through the wrong union member.
- **Copy/paste:** `get_selection()` and `select_word()` take `(char)chars[0]`, so non-ASCII text copies as garbage.

The result is the screen "breaking apart" in the Claude CLI: borders turn into rows of lozenges, the logo and spinners become noise, and any emoji or CJK text pushes the rest of the line one column off.

## Goals

1. **Correct layout first.** Every character occupies exactly the number of cells the server thinks it does, even if what's drawn is only a placeholder.
2. **Box, block and Braille characters render cleanly** at any cell size, including btop's graphs and the Claude CLI's borders and logo.
3. **The symbols the Claude CLI and btop use render recognizably** on the 512×384 LC screen.
4. **Common emoji render in color** on 16- and 256-color screens, with a readable fallback on black-and-white screens.
5. **CJK is readable on the iMac** when the system has the fonts. Where it doesn't, it gets a replacement glyph that keeps the layout correct and hints at what was there.
6. **Don't slow down plain text.** An ASCII-only screen must redraw as fast as it does today on the LC II.

## Non-goals (for this update)

- 256-color and truecolor mapping. It's needed and comes next, but here we only make sure RGB colors no longer get misread (see Color below).
- Full emoji coverage, ZWJ sequences (family emoji and the like), or skin tones. These draw as their base emoji.
- Right-to-left scripts, combining-mark stacking, and complex shaping.
- Unicode input from the Mac keyboard.

## Display targets

| Machine | Screen | Depth | Base font | Cell (approx.) | Terminal size |
|---|---|---|---|---|---|
| LC II (68030, no FPU) | 512×384 LC monitor | 4- or 8-bit, depending on VRAM | Monaco 9 (bitmap) | 6×12 | 80×28 |
| LC 475 (68LC040, no FPU) | 512×384 or 640×480 | 8- or 16-bit | Monaco 9 (bitmap) | 6×12 | 80×28 (512) / 100×36 (640) |
| iMac G3 | 800×600 | 16- or 32-bit | fixed-width TrueType subset | 8×16 | 98×34 |

At 512×384, 80 columns × 6 px = 480 px, which leaves room for the window frame. The menu bar and title bar take about 40 px, so about 28 rows fit. The Claude CLI needs about 80 columns to lay out properly, so **6 px wide cells are a hard requirement at 512**. The exact Monaco 9 cell height (11 or 12 px, from `GetFontInfo`) gets measured in an emulator during milestone 1.

The atlas is built for a small fixed set of cell sizes: **6×12** (512 screens) and **8×16** (800 screens). A 7×14 size can be added later if needed. Code-drawn glyphs work at any size. Exported glyphs need a set made for that size; if none exists, the nearest smaller set is drawn centered in the cell.

## Design

### Pipeline

```
libvterm cell ──► classify(codepoint, width) ──► renderer
                                                  ├─ TEXT     → batched into the row's DrawText run (fast path)
                                                  ├─ ATLAS    → CopyBits a 1-bit glyph, colored with fg/bg
                                                  ├─ EMOJI    → CopyMask a color bitmap (4- or 8-bit variant)
                                                  ├─ SYSFONT  → TEC convert + DrawText with a script font (iMac only)
                                                  └─ REPLACE  → atlas replacement glyph, 1 or 2 cells wide
```

`classify()` only runs for code points above 0x7F, so plain ASCII never leaves the fast path.

### 1. Classification and the character table

There's one generated, sorted table of ranges: `{first, last, class, arg}`. `classify()` does a binary search on it, and a 64-entry direct-mapped cache in front of the search covers the handful of distinct characters a screen typically uses.

| Range | Contents | Class |
|---|---|---|
| 0x00A0–0x00FF and other Mac Roman characters | Latin-1, punctuation | TEXT (converted to a Mac Roman byte) |
| U+2500–U+257F | box drawing | ATLAS, code-drawn |
| U+2580–U+259F | block elements | ATLAS, code-drawn |
| U+2800–U+28FF | Braille (btop graphs) | ATLAS, code-drawn |
| U+1FB00–U+1FB3B | sextants (some TUIs) | ATLAS, code-drawn |
| U+E0A0–U+E0D4 | Powerline / Nerd Font separators | ATLAS, code-drawn (triangles and half circles) |
| selected symbols (see the symbol list) | arrows, check marks, dingbats, the Claude CLI's spinner | ATLAS, exported |
| emoji with an exported bitmap | | EMOJI |
| U+1100–U+11FF, U+3130–U+318F, U+AC00–U+D7A3 | Hangul | SYSFONT or REPLACE |
| U+3040–U+30FF, U+31F0–U+31FF | kana | SYSFONT or REPLACE |
| U+4E00–U+9FFF, U+3400–U+4DBF | CJK ideographs | SYSFONT or REPLACE |
| U+FF00–U+FFEF | fullwidth and halfwidth forms | TEXT (fold to ASCII) or SYSFONT |
| everything else | | REPLACE |

The table is generated by `tools/unicode/gen_table.py` from the glyph sets that were actually exported, so a character can never be classed ATLAS without a bitmap behind it.

The existing `map_unicode()` lookalike table stays as a fallback before REPLACE for characters that have a sensible ASCII stand-in.

### 2. Base font

- **512 screens (LC II, LC 475): Monaco 9, as today.** It's a bitmap font in every System 7 install, it's 6 px wide, and DrawText with it is the fastest thing QuickDraw can do. If Monaco 9's look or metrics become a problem, we can ship our own `NFNT` (bitmap font resource) made from the same source as the atlas (see Glyph sources) inside the app's resource fork. The Font Manager finds fonts in the running app's resource fork, so nothing needs installing.
- **800 screens (iMac G3): a fixed-width TrueType subset**, also embedded in the app's resource fork as `sfnt` plus `FOND` resources.
  - **Catch:** classic QuickDraw draws TrueType through the font's **Mac Roman (1,0) cmap**, so `DrawText` can only reach 256 glyphs per font. The subset therefore covers ASCII and Mac Roman only, and we remap its cmap so the Mac Roman slots point to the right glyphs.
  - **Everything else:** symbols, blocks and emoji still go through the atlas, rendered at the 8×16 size from the same TTF.
  - **ATSUI:** Mac OS 8.5+ has a Unicode text API (ATSUI), and Retro68 ships `libATSUnicodeLib.a`. Using it for the base text is an experiment for later (see open questions). It isn't the plan of record, because per-cell layout through ATSUI is likely too slow for full redraws.
  - **Candidate fonts** (all with open licenses that allow subsetting): JetBrains Mono, DejaVu Sans Mono, Cascadia Mono, Iosevka. Pick by how they look at 12–13 pt on the iMac's screen.

The base font sets `con.cell_width` and `con.cell_height` as it does today (`font_size_change()`), and the atlas is built or loaded for that cell size.

### 3. Glyph atlas

The atlas is one offscreen 1-bit `BitMap` per cell size, with glyphs laid out in a strip. It's indexed by the `arg` in the character table.

**Code-drawn glyphs** (box, block, Braille, sextant and Powerline characters) are rendered into the atlas **at startup and whenever the font size changes**, using `PaintRect`, `MoveTo`/`LineTo` and `PaintPoly` into the offscreen port. They're derived from the cell size, so they fill the cell edge to edge and join seamlessly with their neighbours. Things to get right:

- **Lines:** light and heavy weights (1 and 2 px at 6×12; 1 and 2 px at 8×16) and double lines.
- **Rounded corners** `╭╮╰╯`: drawn as a quarter arc. The Claude CLI uses these for every box.
- **Partial blocks** `▁▂▃▄▅▆▇` and `▏▎▍▌▋▊▉`: rounded to whole pixels. At 12 px tall, some eighth-blocks collapse together; that's acceptable.
- **Quadrants** `▖▗▘▙▚▛▜▝▞▟`: these make up the Claude CLI's logo.
- **Shades** `░▒▓`: drawn as 25/50/75% dither patterns.
- **Braille dots:** 2×4 dots per cell. At 6×12 each dot is 2×2 px.

Drawing these once into the atlas and then blitting means the per-frame cost is the same as for any exported glyph.

**Exported glyphs** are 1-bit bitmaps produced at build time (see Build-time tooling) and stored as a resource. They're loaded into the same atlas at startup.

**Drawing:** `CopyBits` from the atlas to the window with `srcCopy`. With a 1-bit source, QuickDraw colors the set bits with the port's foreground color and the clear bits with its background color, which is exactly the cell's colors. This works on both the 68030 and PowerPC. Consecutive atlas cells with the same colors are blitted one at a time but share the color setup, the same way text runs do today.

### 4. Emoji

- **Pre-rendered, two cells wide and one cell tall:** 12×12 for the 6×12 cell size and 16×16 for 8×16.
- **Three variants per emoji:**
  - **8-bit:** indexed to the standard Mac 256-color system palette.
  - **4-bit:** indexed to the standard Mac 16-color palette.
  - **1-bit:** a hand-tuned or dithered black-and-white version for monochrome screens and FASTEST mode.
- **A 1-bit mask** is shared by all three.
- **At startup** the variant is picked from the main screen's depth (`(**GetMainDevice()).gdPMap` pixel size): 1-bit → mono, 2- or 4-bit → 4-bit, 8-bit or deeper → 8-bit. QuickDraw converts the 8-bit version up on 16- and 32-bit screens, so the iMac doesn't need a true-color set.
- **Drawn** with `CopyMask` over the cell's background color.
- **Subset:** a curated list of about 150–300 emoji that terminal programs and LLM output actually produce, such as ✅ ❌ ⚠️ 🚀 ✨ 🎉 📁 📄 🔍 💡 🔧 📝 🐛 ⭐ 👍 🔥 💻. The list lives in `tools/unicode/emoji.txt` and should be extended using the capture tool (see Testing). Anything not on the list goes to REPLACE as a 2-cell "emoji" replacement glyph.
- **Memory:** at 12×12, one emoji is 144 bytes (8-bit) + 72 bytes (4-bit) + 18 bytes (mono) + 18 bytes (mask) ≈ 250 bytes, so 300 emoji ≈ 75 KB. Only the variant in use needs loading, which is about 50 KB. That's fine for the LC II's 10 MB.
- **Variation selectors:** libvterm stores U+FE0F (emoji style) and U+FE0E (text style) as combining characters in `chars[1..]`. FE0F forces EMOJI if a bitmap exists; FE0E forces the text symbol from the atlas if one exists.
- **Joined sequences** (ZWJ, skin tones) draw as the first emoji in the sequence.

### 5. CJK and other wide characters

**On the iMac (800×600, Mac OS 8.5+), when the fonts exist:**

- **Detect** installed script systems at startup with `GetScriptManagerVariable(smEnabled)` and `GetScriptVariable(script, smScriptAppFond)`, and look up the fonts by name: Osaka (Japanese), AppleGothic or Seoul (Korean), Apple LiSung or LiGothic (traditional Chinese), Song or Hei (simplified Chinese).
- **Convert** each run of same-script cells from UTF-32 to the script's encoding (Shift-JIS, EUC-KR, GB2312, Big5) with the Text Encoding Converter (TEC), which is present in Mac OS 8.5+.
- **Draw** the run with `DrawText` in that font at a size whose glyphs fit in 2 cells (16×16 on the iMac). Each glyph must start exactly on its cell boundary, so draw one glyph at a time if the font's advance width doesn't match 2 cells exactly.
- **This needs the matching Language Kit** or a multilingual Mac OS install. If it's missing, fall back to REPLACE.

**Everywhere else**, including all 512 screens (a 12 px tall cell is too small for legible ideographs anyway), use REPLACE.

**Replacement glyphs** come from the atlas and always match the cell width libvterm reports:

| Class | Width | Replacement glyph |
|---|---|---|
| Hangul | 2 | box with a small `한`-style mark (custom 12×12 drawing) |
| kana | 2 | box with a small `あ`-style mark |
| CJK ideograph | 2 | box with a small `漢`-style mark |
| emoji not in the subset | 2 | outlined circle |
| other wide | 2 | box containing the code point in hex (4×5 px digits, Unifont style) |
| other narrow | 1 | `◊` (today's lozenge), or the lookalike from `map_unicode()` |

The hex box makes unknown characters identifiable while debugging, and the script marks make it obvious which language a line was in. The full table lives in `tools/unicode/replacement.tsv` and is compiled into the same generated table as everything else.

### 6. Width agreement with the server

Layout is only correct if libvterm and the program on the server agree on how many cells each character takes. They currently don't:

- libvterm's `src/fullwidth.inc` is from about Unicode 12 and ends at U+1FA95.
- The Claude CLI measures strings with its own JavaScript width table (`string-width`), which is current Unicode and counts emoji presentation sequences like `⚠️` (U+26A0 U+FE0F) as 2 cells. libvterm counts U+26A0 as 1 cell and ignores the FE0F.
- btop and htop use the host's `wcwidth()` (glibc), which is somewhere in between.

**Proposed fix**, in our libvterm:

1. Regenerate `fullwidth.inc` from the current `EastAsianWidth.txt` and `emoji-data.txt`, counting Extended_Pictographic characters with emoji presentation as wide.
2. When U+FE0F follows a narrow character that has emoji presentation, widen the cell to 2. This matches what string-width and modern terminals do.

This changes code in the `libvterm` submodule, which points to cy384's repository. We'd fork it to `sungsookhim/libvterm` and point `.gitmodules` at the fork. That's small, and we'll need the fork for color work anyway.

### 7. Color

This update doesn't do 256-color or truecolor mapping, but the new drawing path must not misread colors:

- Check `VTERM_COLOR_IS_INDEXED` before reading `.indexed.idx`.
- For RGB colors, map to the nearest of the 16 ANSI colors for now. That's a small function, which the color update will later replace with real palette mapping.
- Keep sending `xterm-16color` as the terminal type until the color work lands, so programs don't send colors we can't show.

### 8. Changes to the drawing loop

`draw_screen_color` and `draw_screen_fast` change from building one `char row_text[]` per row to building **segments**:

- **A TEXT run** collects Mac Roman bytes with the same style and colors, then draws with one `EraseRect` + `DrawText`, exactly as today.
- **A non-TEXT cell** ends the current run. It erases its cell rectangle (1 or 2 cells wide) and draws its glyph.
- **Continuation cells** (the right half of a wide character, where libvterm sets `chars[0] == (uint32_t)-1`) are skipped.

Both drawing paths share one `draw_cell_special()` helper, so the two loops don't each need their own copy of the special-glyph logic.

**Selection and copy** switch from `(char)chars[0]` to encoding the full `chars[]` as UTF-8, then converting to Mac Roman for the clipboard. On the iMac with TEC, the Unicode text can go to the clipboard as well.

**Performance:** on the LC II, the risk is a screen full of box drawing (the Claude CLI's frame) turning one `DrawText` per row into dozens of `CopyBits` calls. Ways to cut that down:

- **Merge neighbours:** adjacent atlas cells with the same colors can go in one `CopyBits` call when the atlas stores them next to each other, which is common for `─` runs. Alternatively, keep a per-row scratch bitmap.
- **Measure first:** milestone 3 measures redraw time on a 68030 in an emulator before and after the change. The goal is to stay within 20% of today on a screen like the Claude CLI's.

## Glyph sources

| Use | Source | License | Notes |
|---|---|---|---|
| 6×12 symbols, and a possible NFNT base | [Spleen](https://github.com/fcambus/spleen) 6×12, or [Cozette](https://github.com/slavfox/Cozette) 6×13 | BSD-2 / MIT | Designed as pixel fonts, so much crisper at 12 px than a rasterized TTF. Cozette covers many symbols and Nerd Font icons. |
| 8×16 symbols | Spleen 8×16, or the chosen iMac TTF rasterized at 16 px | BSD-2 / OFL | |
| Symbols missing from those | [Noto Sans Symbols 2](https://fonts.google.com/noto/specimen/Noto+Sans+Symbols+2) rasterized, then hand-touched | OFL 1.1 | |
| Emoji | [Twemoji](https://github.com/jdecked/twemoji) PNGs, or Noto Emoji | CC-BY 4.0 / OFL 1.1 | Twemoji needs attribution, which goes in the README and the About box. |

Hand-tuned pixel sources come first. Rasterizing a TTF at 12 px gives blurry, uneven 1-bit glyphs, so it's only the fallback for characters the pixel fonts don't have. Every source's license text gets copied into `third_party/` next to the generated data.

## Build-time tooling

The tools are new and live in `tools/unicode/`. They run on the build host inside the existing container image, with Python 3, Pillow and fontTools added to the `Containerfile`.

| Script | Input | Output |
|---|---|---|
| `export_glyphs.py` | BDF or TTF sources, `symbols.txt` (the code points wanted) | 1-bit glyph strips per cell size |
| `export_emoji.py` | Twemoji PNGs, `emoji.txt` | 8-bit, 4-bit and mono variants + masks, quantized to the Mac system palettes |
| `gen_table.py` | the above + `replacement.tsv` | `unicode-table.h` (the sorted range table) and `glyphs.r` (resource data included from `ssheven.r`) |
| `capture.py` | a session log recorded on the server with `script` | a histogram of the non-ASCII code points used, to grow `symbols.txt` and `emoji.txt` |

Generated files are committed so a normal build doesn't need the source fonts. `./build.sh` gets a `glyphs` target to regenerate them.

## Initial symbol list

These are expected from looking at the Claude CLI and btop, and need confirming with `capture.py` against real sessions:

- **Claude CLI:** `⏺ ⎿ ✻ ✢ ✳ ✶ ✽ · ❯ › ⏵ ✓ ✔ ✗ ✘ ● ○ ◯ ◆ ◇ ▶ ▸ ► … ↑ ↓ ← → ↵ ⧉ ⚠ ★ ☐ ☒ ✎`, rounded box drawing `╭ ╮ ╰ ╯ │ ─`, and the quadrant/half-block logo `▐ ▛ █ ▜ ▌ ▝ ▘`.
- **btop:** Braille `⣀–⣿` for graphs, `▁▂▃▄▅▆▇█` meters, `■ ▪ •`, box drawing including `┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`, and arrows `↑ ↓`.
- **htop:** mostly ASCII. Optionally box drawing and `│`.
- **Shells and git prompts:** `✓ ✗ ➜ ⇡ ⇣`, the Nerd Font branch icon U+E0A0, and the Powerline separators U+E0B0–U+E0B3.

## Testing

- **Test pattern:** `tests/unicode-sample.txt` holds every class above, plus lines with known widths, so misalignment is easy to spot. Run `cat` on it over SSH.
- **Emulators:** check in Basilisk II (LC-like 68030 at 512×384 in 4-bit, then 8-bit) and SheepShaver or QEMU at 800×600 in 16-bit. Store a screenshot per target in `docs/design/0001/` for before/after comparison.
- **Real programs:** run the Claude CLI and btop through `capture.py` to grow the lists, then in each emulator to check the layout.
- **Timing:** time full redraws with `TickCount()` on a fixed screen dump, reported in the debug window, for the before/after numbers.
- **Real hardware:** LC II, LC 475, and the iMac.

## Milestones

1. **Layout correctness.** Skip continuation cells, check color types, regenerate the libvterm width table, and widen emoji when FE0F follows. Everything outside Mac Roman draws as the right-width replacement. The screen stops "breaking apart", even though most special characters are still placeholders.
2. **Code-drawn atlas.** Box, block, Braille and shade characters. This fixes the Claude CLI's frame and logo and btop's graphs.
3. **Exported symbols** at 6×12 and 8×16, plus the capture tool, plus timing on the 68030.
4. **Emoji** in 4-bit, 8-bit and mono.
5. **iMac:** the TrueType base font, and CJK through system fonts and TEC.
6. **Unicode copy/paste.**

Milestones 1 and 2 alone should make the Claude CLI usable on the LC II.

## Open questions

- **Monaco 9 or our own NFNT** for the 512 base font? Monaco has no box drawing of its own, but that doesn't matter here. The deciding factor is whether its 12 px row height leaves room for clean 2×2 Braille dots and partial blocks.
- **ATSUI on the iMac.** Is it fast enough to draw the base text and do CJK font fallback without the TEC and script-font setup? Worth a quick measurement, since it would also handle fonts that only have a Unicode cmap.
- **Does the Claude CLI use sequences** (ZWJ, skin tones, flags) often enough to need more than the "draw the first emoji" rule?
- **Should the 4-bit emoji set be hand-tuned?** Automatic quantization to 16 colors at 12×12 may look muddy.
- **Atlas memory on PowerPC.** Fine for one cell size. Building every size up front isn't needed; rebuild on font size change instead.
