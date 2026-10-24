/*
 * lessbrokenssh glyph atlas: bitmaps for characters the base font doesn't
 * have (box drawing, blocks, Braille, ...), from the 'GLYF' resources that
 * tools/glyphs/pack.py makes. See docs/design/0001-plan.md.
 */

#pragma once

#include <stdint.h>

#include "MacTypes.h"

// load the glyph set for this cell size; returns how many glyphs it has (0 if none)
int glyphs_load(short cell_width, short cell_height);

// how many glyphs the loaded set has
int glyphs_count(void);

// index of the glyph for a code point, or -1 if there isn't one
int glyph_index(uint32_t codepoint);

// draw a glyph into a cell of the current port, in its foreground and background colors
void glyph_draw(int index, const Rect* cell);

// load the emoji set for this cell size (two cells per emoji), in color if the
// screen depth allows; returns how many emoji it has (0 if none)
int emoji_load(short cell_width, short cell_height, int screen_depth);

// how many emoji the loaded set has
int emoji_loaded_count(void);

// index of the emoji for a code point, or -1 if there isn't one
int emoji_index(uint32_t codepoint);

// draw an emoji into two cells of the current port, over what's there
void emoji_draw(int index, const Rect* cells);
