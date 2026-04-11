#ifndef CORE_H
#define CORE_H

#include <SDL2/SDL.h>

double time_delta_seconds(void);

// Draws a live FPS counter in the top-left corner.
// Pass the current frame's dt each frame.
void draw_fps(SDL_Renderer* renderer, float dt);

#endif
