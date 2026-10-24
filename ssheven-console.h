/* 
 * ssheven
 * 
 * Copyright (c) 2020 by cy384 <cy384@cy384.com>
 * See LICENSE file for details
 */

#pragma once

#include "MacTypes.h"

void reset_console(void);
void console_setup(void);

void draw_screen(Rect* r);

void printf_i(const char* c, ...);

void check_cursor(void);

// select: shift held, so select text even if the program wants the mouse
void mouse_click(Point p, int click, int select);

void update_console_colors(void);

size_t get_selection(char** selection);

void clear_selection(void);

void font_size_change(void);

void print_display_info(void);

// width of the scrollback scroll bar on the right of the window
#define SCROLL_BAR_WIDTH 15

void position_scroll_bar(void);
int scroll_bar_click(Point p);
void console_scroll(int lines);
void console_scroll_to_bottom(void);
int console_page_lines(void);
