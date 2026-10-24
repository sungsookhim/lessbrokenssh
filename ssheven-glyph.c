/*
 * lessbrokenssh glyph atlas, see ssheven-glyph.h
 */

#include "ssheven-glyph.h"

#include <Memory.h>
#include <Resources.h>
#include <Quickdraw.h>

// layout of a 'GLYF' resource, see tools/glyphs/pack.py
struct glyph_header
{
	uint16_t cell_width;
	uint16_t cell_height;
	uint16_t count;
	uint16_t row_bytes;
	// then uint32_t codepoints[count], sorted, then the bitmap
};

static Handle glyph_res = NULL;
static const uint32_t* glyph_codepoints = NULL;
static int glyph_count = 0;
static short glyph_width = 0;
static BitMap glyph_bits;

static void glyphs_unload(void)
{
	if (glyph_res)
	{
		HUnlock(glyph_res);
		ReleaseResource(glyph_res);
	}

	glyph_res = NULL;
	glyph_codepoints = NULL;
	glyph_count = 0;
}

int glyphs_load(short cell_width, short cell_height)
{
	glyphs_unload();

	short n = CountResources('GLYF');

	for (short i = 1; i <= n; i++)
	{
		Handle h = GetIndResource('GLYF', i);
		if (h == NULL) continue;

		struct glyph_header* header = (struct glyph_header*)*h;

		if (header->cell_width != cell_width || header->cell_height != cell_height)
		{
			ReleaseResource(h);
			continue;
		}

		// keep it around and still, since glyph_bits points into it
		HNoPurge(h);
		HLockHi(h);
		header = (struct glyph_header*)*h;

		glyph_res = h;
		glyph_count = header->count;
		glyph_width = cell_width;
		glyph_codepoints = (const uint32_t*)(*h + sizeof(struct glyph_header));

		glyph_bits.baseAddr = (Ptr)(glyph_codepoints + glyph_count);
		glyph_bits.rowBytes = (short)header->row_bytes;
		SetRect(&glyph_bits.bounds, 0, 0, (short)(glyph_count * cell_width), cell_height);

		return glyph_count;
	}

	return 0;
}

int glyphs_count(void)
{
	return glyph_count;
}

int glyph_index(uint32_t codepoint)
{
	int lo = 0;
	int hi = glyph_count - 1;

	while (lo <= hi)
	{
		int mid = (lo + hi) / 2;
		uint32_t here = glyph_codepoints[mid];

		if (here == codepoint) return mid;
		if (here < codepoint) lo = mid + 1;
		else hi = mid - 1;
	}

	return -1;
}

void glyph_draw(int index, const Rect* cell)
{
	Rect src;
	SetRect(&src, (short)(index * glyph_width), 0, (short)((index + 1) * glyph_width), glyph_bits.bounds.bottom);

	// a 1-bit source gets colored with the port's foreground and background colors
	CopyBits(&glyph_bits, &qd.thePort->portBits, &src, cell, srcCopy, NULL);
}
