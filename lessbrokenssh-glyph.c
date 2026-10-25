/*
 * lessbrokenssh glyph atlas, see lessbrokenssh-glyph.h
 */

#include "lessbrokenssh-glyph.h"

#include <Memory.h>
#include <Resources.h>
#include <Quickdraw.h>

#include <string.h>

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

// one row of cells, where a row's glyphs are put together so each run of them
// takes one CopyBits instead of one per cell; most of a CopyBits to a deep
// screen is fixed setup, so that's what made Braille graphs slow on 68k
static BitMap row_bits;
static Ptr row_buffer = NULL;
static long row_buffer_size = 0;
static short row_height = 0;

void glyph_row_begin(int columns)
{
	if (glyph_count == 0) return;

	short row_bytes = (short)(((columns * glyph_width + 15) / 16) * 2);
	long size = (long)row_bytes * glyph_bits.bounds.bottom;

	if (size > row_buffer_size)
	{
		if (row_buffer) DisposePtr(row_buffer);
		row_buffer = NewPtr(size);
		row_buffer_size = row_buffer ? size : 0;
	}

	if (row_buffer == NULL) return;

	row_height = glyph_bits.bounds.bottom;
	row_bits.baseAddr = row_buffer;
	row_bits.rowBytes = row_bytes;
	SetRect(&row_bits.bounds, 0, 0, (short)(columns * glyph_width), row_height);
	memset(row_buffer, 0, (size_t)size);
}

void glyph_row_put(int index, int column)
{
	if (row_buffer == NULL) return;

	const unsigned char* src_base = (const unsigned char*)glyph_bits.baseAddr;
	unsigned char* dst_base = (unsigned char*)row_buffer;
	long src_bit = (long)index * glyph_width;
	long dst_bit = (long)column * glyph_width;
	int src_shift = (int)(src_bit & 7);
	int dst_shift = (int)(dst_bit & 7);
	int src_bytes = (src_shift + glyph_width + 7) / 8; // at most 4, cells are under 25 px wide
	int dst_bytes = (dst_shift + glyph_width + 7) / 8;

	const unsigned char* src = src_base + (src_bit >> 3);
	unsigned char* dst = dst_base + (dst_bit >> 3);

	for (short y = 0; y < row_height; y++)
	{
		// the glyph's line, left-aligned in 32 bits
		uint32_t bits = 0;
		for (int b = 0; b < src_bytes; b++) bits |= (uint32_t)src[b] << (24 - 8 * b);
		bits = (bits << src_shift) & ~(0xFFFFFFFFUL >> glyph_width);

		// into the row, which starts out clear
		bits >>= dst_shift;
		for (int b = 0; b < dst_bytes; b++) dst[b] |= (unsigned char)(bits >> (24 - 8 * b));

		src += glyph_bits.rowBytes;
		dst += row_bits.rowBytes;
	}
}

int glyph_row_draw(int start_column, int length, const Rect* cells)
{
	if (row_buffer == NULL) return 0;

	Rect src;
	SetRect(&src, (short)(start_column * glyph_width), 0, (short)((start_column + length) * glyph_width), row_height);

	// a 1-bit source gets colored with the port's foreground and background colors
	CopyBits(&row_bits, &qd.thePort->portBits, &src, cells, srcCopy, NULL);
	return 1;
}

// layout of an 'EMOJ' resource, see tools/glyphs/pack.py
struct emoji_header
{
	uint16_t width;
	uint16_t height;
	uint16_t count;
	uint16_t row_bytes_1;
	uint16_t row_bytes_4;
	uint16_t row_bytes_8;
	// then uint32_t codepoints[count], then the mask, mono, 4-bit and 8-bit strips
};

static Handle emoji_res = NULL;
static const uint32_t* emoji_codepoints = NULL;
static int emoji_count = 0;
static short emoji_width = 0;
static BitMap emoji_mask;
static BitMap emoji_mono;
static PixMap emoji_pixels;
static int emoji_depth = 0; // 4 or 8 when drawing in color, 0 for the mono version

static void emoji_unload(void)
{
	if (emoji_res)
	{
		HUnlock(emoji_res);
		ReleaseResource(emoji_res);
	}

	emoji_res = NULL;
	emoji_codepoints = NULL;
	emoji_count = 0;
	emoji_depth = 0;
}

static void set_bitmap(BitMap* b, Ptr bits, uint16_t row_bytes, short width, short height)
{
	b->baseAddr = bits;
	b->rowBytes = (short)row_bytes;
	SetRect(&b->bounds, 0, 0, width, height);
}

int emoji_load(short cell_width, short cell_height, int screen_depth)
{
	emoji_unload();

	short n = CountResources('EMOJ');

	for (short i = 1; i <= n; i++)
	{
		Handle h = GetIndResource('EMOJ', i);
		if (h == NULL) continue;

		struct emoji_header* header = (struct emoji_header*)*h;

		if (header->width != 2 * cell_width || header->height != cell_height)
		{
			ReleaseResource(h);
			continue;
		}

		HNoPurge(h);
		HLockHi(h);
		header = (struct emoji_header*)*h;

		emoji_res = h;
		emoji_count = header->count;
		emoji_width = (short)header->width;
		emoji_codepoints = (const uint32_t*)(*h + sizeof(struct emoji_header));

		short strip_width = (short)(emoji_count * emoji_width);
		short height = (short)header->height;
		Ptr p = (Ptr)(emoji_codepoints + emoji_count);

		set_bitmap(&emoji_mask, p, header->row_bytes_1, strip_width, height);
		p += header->row_bytes_1 * height;
		set_bitmap(&emoji_mono, p, header->row_bytes_1, strip_width, height);
		p += header->row_bytes_1 * height;
		Ptr pixels4 = p;
		p += header->row_bytes_4 * height;
		Ptr pixels8 = p;

		// in color if the screen can show it, using the standard system palette
		// the colors were matched to
		int depth = (screen_depth >= 8) ? 8 : (screen_depth >= 4) ? 4 : 0;
		CTabHandle palette = depth ? GetCTable((short)depth) : NULL;

		if (palette)
		{
			memset(&emoji_pixels, 0, sizeof(emoji_pixels));
			emoji_pixels.baseAddr = (depth == 8) ? pixels8 : pixels4;
			emoji_pixels.rowBytes = (short)(((depth == 8) ? header->row_bytes_8 : header->row_bytes_4) | 0x8000);
			SetRect(&emoji_pixels.bounds, 0, 0, strip_width, height);
			emoji_pixels.hRes = 72L << 16;
			emoji_pixels.vRes = 72L << 16;
			emoji_pixels.pixelType = 0; // indexed
			emoji_pixels.pixelSize = (short)depth;
			emoji_pixels.cmpCount = 1;
			emoji_pixels.cmpSize = (short)depth;
			emoji_pixels.pmTable = palette;
			emoji_depth = depth;
		}

		return emoji_count;
	}

	return 0;
}

int emoji_loaded_count(void)
{
	return emoji_count;
}

int emoji_index(uint32_t codepoint)
{
	int lo = 0;
	int hi = emoji_count - 1;

	while (lo <= hi)
	{
		int mid = (lo + hi) / 2;
		uint32_t here = emoji_codepoints[mid];

		if (here == codepoint) return mid;
		if (here < codepoint) lo = mid + 1;
		else hi = mid - 1;
	}

	return -1;
}

void emoji_draw(int index, const Rect* cells)
{
	Rect src;
	SetRect(&src, (short)(index * emoji_width), 0, (short)((index + 1) * emoji_width), emoji_mask.bounds.bottom);

	if (emoji_depth)
	{
		// black on white, or CopyMask tints the colors with the port's colors
		RGBColor save_fg, save_bg;
		RGBColor black = { 0, 0, 0 };
		RGBColor white = { 0xFFFF, 0xFFFF, 0xFFFF };
		GetForeColor(&save_fg);
		GetBackColor(&save_bg);
		RGBForeColor(&black);
		RGBBackColor(&white);

		CopyMask((BitMap*)&emoji_pixels, &emoji_mask, &qd.thePort->portBits, &src, &src, cells);

		RGBForeColor(&save_fg);
		RGBBackColor(&save_bg);
	}
	else
	{
		// the black-and-white version, in the cell's own colors
		CopyMask(&emoji_mono, &emoji_mask, &qd.thePort->portBits, &src, &src, cells);
	}
}
