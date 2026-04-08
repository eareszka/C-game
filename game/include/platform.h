#ifndef PLATFORM_H
#define PLATFORM_H

#include <stdbool.h>
#include <SDL2/SDL.h>

typedef struct Platform {
    SDL_Window* window;
    SDL_Renderer* renderer;
    int width;
    int height;
} Platform;

bool platform_init(Platform* p, const char* title, int width, int height);
void platform_shutdown(Platform* p);

#endif
