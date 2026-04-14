#ifndef CORE_H
#define CORE_H

#include <SDL2/SDL.h>

double time_delta_seconds(void);

void draw_fps(SDL_Renderer* renderer, float dt);

// Draw an uppercase string at (x, y). scale=1 → 8px tall, scale=2 → 16px tall.
// Supports A-Z, 0-9, space, colon, hyphen, period, question mark.
void draw_text(SDL_Renderer* ren, const char* text, int x, int y, int scale,
               Uint8 r, Uint8 g, Uint8 b);

// Returns the pixel width of the string at the given scale.
int text_width(const char* text, int scale);

#endif
