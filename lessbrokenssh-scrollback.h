/*
 * lessbrokenssh scrollback: lines that scroll off the top of the terminal,
 * kept so they can be scrolled back to. Fed by libvterm's sb_pushline.
 */

#pragma once

#include <vterm.h>

#define SCROLLBACK_LINES 1000

// how many lines are stored (0 .. SCROLLBACK_LINES)
int scrollback_count(void);

// store a line that scrolled off the top (libvterm sb_pushline)
void scrollback_push(int cols, const VTermScreenCell* cells);

// take back the newest line, when the screen grows taller (libvterm sb_popline);
// returns 0 if there are none
int scrollback_pop(int cols, VTermScreenCell* cells);

// forget everything (libvterm sb_clear, e.g. from `clear`)
void scrollback_clear(void);

// one cell of stored line `line` (0 is the oldest); past the end of the line it's blank
void scrollback_cell(int line, int col, VTermScreenCell* cell);
