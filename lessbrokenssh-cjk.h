/*
 * lessbrokenssh CJK text: draws Japanese and Korean (and the Chinese
 * characters Japanese or Korean fonts have) with the system's own fonts,
 * when those script systems are installed. See docs/design/0001-plan.md.
 */

#pragma once

#include <stdint.h>

#include "MacTypes.h"

// find the installed CJK script fonts and load the conversion tables
void cjk_init(void);

// which scripts can be drawn, for the startup line, e.g. " JP KR" or ""
const char* cjk_scripts(void);

// look up a full-width character: returns a handle for cjk_draw, or -1 if no
// installed script can draw it
int32_t cjk_lookup(uint32_t codepoint);

// draw a looked-up character over two cells, baseline at y, in the port's colors
void cjk_draw(int32_t handle, short left, short baseline, short size);

// decomposed Hangul (NFD, common in file names made on macOS) arrives as a
// leading consonant with the vowel and final consonant as combining characters
// in the same cell; put them back together into the syllable, Unicode's way.
// chars is a cell's chars[], at least 3 long; returns chars[0] if it isn't that.
static inline uint32_t compose_hangul(const uint32_t* chars)
{
	uint32_t l = chars[0];
	uint32_t v = chars[1];

	if (l < 0x1100 || l > 0x1112 || v < 0x1161 || v > 0x1175) return l;

	uint32_t t = chars[2];
	uint32_t t_index = (t >= 0x11A8 && t <= 0x11C2) ? t - 0x11A7 : 0;

	return 0xAC00 + ((l - 0x1100) * 21 + (v - 0x1161)) * 28 + t_index;
}
