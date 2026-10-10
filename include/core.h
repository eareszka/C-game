#ifndef CORE_H
#define CORE_H

#include <SDL2/SDL.h>

double time_delta_seconds(void);

void draw_fps(SDL_Renderer* renderer, float dt, float player_x, float player_y);

// Draw an uppercase string at (x, y). scale=1 → 8px tall, scale=2 → 16px tall.
// Supports A-Z, 0-9, space, colon, hyphen, period, question mark.
void draw_text(SDL_Renderer* ren, const char* text, int x, int y, int scale,
               Uint8 r, Uint8 g, Uint8 b);

// Returns the pixel width of the string at the given scale.
int text_width(const char* text, int scale);

// A window as the menu reference draws them: black inside, a 4px frame with
// stepped round corners (white unless coloured), and a 2px black edge round
// the outside of the rect. Content area starts at (x+4, y+4); NES_PAD (4).
void draw_nes_panel(SDL_Renderer* ren, int x, int y, int w, int h,
                    Uint8 r = 255, Uint8 g = 255, Uint8 b = 255);

// A meter: black, filled cur/max of the way in (r,g,b), white outline.
void draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
              float cur, float max, Uint8 r, Uint8 g, Uint8 b);
static const int NES_PAD = 4;

// The textbox: one line of text (small font) in a window just big enough for it,
// centred near the top of the screen -- or, with low, mirrored to the bottom
// (a battle does that to keep it off the player). extra_h is room under the
// text. Returns the window's rect.
SDL_Rect draw_textbox(SDL_Renderer* ren, const char* text, Uint8 r, Uint8 g, Uint8 b,
                      bool low = false, int extra_h = 0);

// Half-period of the flashing player marker on both minimaps, in milliseconds.
// Shared so the overworld and dungeon maps blink in step.
static const Uint32 MINIMAP_FLASH_MS = 350;

#endif
