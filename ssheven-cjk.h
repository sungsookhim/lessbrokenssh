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
