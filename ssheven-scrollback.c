/*
 * lessbrokenssh scrollback, see ssheven-scrollback.h
 */

#include "ssheven-scrollback.h"
#include "ssheven-cjk.h"

#include <stdlib.h>
#include <string.h>

// a cell, packed: one character (decomposed Hangul composed first), its width,
// colors and the attributes we draw. 16 bytes instead of VTermScreenCell's 40.
struct sb_cell
{
	uint32_t ch;
	VTermColor fg;
	VTermColor bg;
	uint8_t width;
	uint8_t attrs; // bit 0 bold, 1 italic, 2 underline, 3 reverse
	uint16_t pad;
};

struct sb_line
{
	uint16_t cols; // cells stored; trailing blanks are dropped
	struct sb_cell cells[];
};

// a ring of lines: lines[(first + i) % SCROLLBACK_LINES] is line i, 0 the oldest
static struct sb_line* lines[SCROLLBACK_LINES];
static int first = 0;
static int count = 0;

// what a dropped trailing blank looks like, from the last one seen
static VTermScreenCell blank;
static int have_blank = 0;

int scrollback_count(void)
{
	return count;
}

static int is_blank(const VTermScreenCell* c)
{
	return c->chars[0] == 0 && !c->attrs.reverse && VTERM_COLOR_IS_DEFAULT_BG(&c->bg);
}

static void drop_oldest(void)
{
	free(lines[first]);
	lines[first] = NULL;
	first = (first + 1) % SCROLLBACK_LINES;
	count--;
}

void scrollback_push(int cols, const VTermScreenCell* cells)
{
	int used = cols;
	while (used > 0 && is_blank(&cells[used - 1])) used--;

	if (used < cols)
	{
		blank = cells[used];
		have_blank = 1;
	}

	if (count == SCROLLBACK_LINES) drop_oldest();

	struct sb_line* line = malloc(sizeof(struct sb_line) + (size_t)used * sizeof(struct sb_cell));
	if (line == NULL && count > 0)
	{
		// short on memory: give up the oldest line and try once more
		drop_oldest();
		line = malloc(sizeof(struct sb_line) + (size_t)used * sizeof(struct sb_cell));
	}
	if (line == NULL) return;

	line->cols = (uint16_t)used;
	for (int i = 0; i < used; i++)
	{
		const VTermScreenCell* c = &cells[i];
		struct sb_cell* s = &line->cells[i];

		s->ch = compose_hangul(c->chars);
		s->fg = c->fg;
		s->bg = c->bg;
		s->width = (uint8_t)c->width;
		s->attrs = (uint8_t)((c->attrs.bold ? 1 : 0) | (c->attrs.italic ? 2 : 0)
			| (c->attrs.underline ? 4 : 0) | (c->attrs.reverse ? 8 : 0));
		s->pad = 0;
	}

	lines[(first + count) % SCROLLBACK_LINES] = line;
	count++;
}

static void unpack(const struct sb_line* line, int col, VTermScreenCell* cell)
{
	if (col >= line->cols)
	{
		if (have_blank)
		{
			*cell = blank;
		}
		else
		{
			memset(cell, 0, sizeof(*cell));
			cell->width = 1;
			cell->fg.type = VTERM_COLOR_INDEXED | VTERM_COLOR_DEFAULT_FG;
			cell->bg.type = VTERM_COLOR_INDEXED | VTERM_COLOR_DEFAULT_BG;
			cell->bg.indexed.idx = 7;
		}
		return;
	}

	const struct sb_cell* s = &line->cells[col];

	memset(cell, 0, sizeof(*cell));
	cell->chars[0] = s->ch;
	cell->width = (char)s->width;
	cell->fg = s->fg;
	cell->bg = s->bg;
	cell->attrs.bold = (s->attrs & 1) ? 1 : 0;
	cell->attrs.italic = (s->attrs & 2) ? 1 : 0;
	cell->attrs.underline = (s->attrs & 4) ? 1 : 0;
	cell->attrs.reverse = (s->attrs & 8) ? 1 : 0;
}

void scrollback_cell(int line, int col, VTermScreenCell* cell)
{
	unpack(lines[(first + line) % SCROLLBACK_LINES], col, cell);
}

int scrollback_pop(int cols, VTermScreenCell* cells)
{
	if (count == 0) return 0;

	int newest = (first + count - 1) % SCROLLBACK_LINES;
	for (int i = 0; i < cols; i++) unpack(lines[newest], i, &cells[i]);

	free(lines[newest]);
	lines[newest] = NULL;
	count--;

	return 1;
}

void scrollback_clear(void)
{
	while (count > 0) drop_oldest();
	first = 0;
}
