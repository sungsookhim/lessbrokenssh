/*
 * lessbrokenssh CJK text, see ssheven-cjk.h
 */

#include "ssheven-cjk.h"

#include <Memory.h>
#include <Resources.h>
#include <Quickdraw.h>
#include <Script.h>

#include <string.h>

// one script we can draw: its font and its 'CJKT' table (see tools/unicode/gen_cjk.py)
struct cjk_script
{
	short script;     // Script Manager code, smJapanese etc.
	short table_id;   // 'CJKT' resource
	const char* tag;
	short font;       // 0 if not installed
	int count;
	const uint16_t* pairs;  // { unicode, code } sorted by unicode
};

static struct cjk_script scripts[] =
{
	{ smJapanese, 128, " JP", 0, 0, NULL },
	{ smKorean,   129, " KR", 0, 0, NULL },
};

#define SCRIPT_COUNT ((int)(sizeof(scripts) / sizeof(scripts[0])))

static char script_tags[16] = "";

void cjk_init(void)
{
	script_tags[0] = '\0';

	for (int i = 0; i < SCRIPT_COUNT; i++)
	{
		struct cjk_script* s = &scripts[i];
		s->font = 0;

		if (!GetScriptVariable(s->script, smScriptEnabled)) continue;

		// prefer the script's monospaced font, which fits the grid; high word is the font
		short font = (short)(GetScriptVariable(s->script, smScriptMonoFondSize) >> 16);
		if (font == 0) font = (short)GetScriptVariable(s->script, smScriptAppFond);
		if (font == 0) continue;

		Handle h = GetResource('CJKT', s->table_id);
		if (h == NULL) continue;

		HNoPurge(h);
		HLockHi(h);

		s->font = font;
		s->count = *(uint16_t*)*h;
		s->pairs = (const uint16_t*)(*h + 2);

		strcat(script_tags, s->tag);
	}
}

const char* cjk_scripts(void)
{
	return script_tags;
}

static int find(const struct cjk_script* s, uint16_t c)
{
	int lo = 0;
	int hi = s->count - 1;

	while (lo <= hi)
	{
		int mid = (lo + hi) / 2;
		uint16_t here = s->pairs[mid * 2];

		if (here == c) return s->pairs[mid * 2 + 1];
		if (here < c) lo = mid + 1;
		else hi = mid - 1;
	}

	return -1;
}

static int is_hangul(uint32_t c)
{
	return (c >= 0xAC00 && c <= 0xD7A3) || (c >= 0x3130 && c <= 0x318F);
}

int32_t cjk_lookup(uint32_t c)
{
	if (c > 0xFFFF) return -1;

	// Hangul only in Korean; everything else (kana, ideographs, fullwidth
	// letters) in Japanese first, then Korean, which also has hanja
	for (int i = 0; i < SCRIPT_COUNT; i++)
	{
		if (scripts[i].font == 0) continue;
		if (is_hangul(c) && scripts[i].script != smKorean) continue;

		int code = find(&scripts[i], (uint16_t)c);
		if (code >= 0) return ((int32_t)i << 16) | code;
	}

	return -1;
}

void cjk_draw(int32_t handle, short left, short baseline, short size)
{
	const struct cjk_script* s = &scripts[handle >> 16];
	char bytes[2] = { (char)((handle >> 8) & 0xFF), (char)(handle & 0xFF) };

	short save_font = qd.thePort->txFont;
	short save_size = qd.thePort->txSize;

	TextFont(s->font);
	TextSize(size);
	MoveTo(left, baseline);
	DrawText(bytes, 0, 2);

	TextFont(save_font);
	TextSize(save_size);
}
