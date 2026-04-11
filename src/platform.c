#include "platform.h"
#include <stdio.h>

bool platform_init(Platform* p, const char* title, int width, int height) {
    p->window = NULL;
    p->renderer = NULL;
    p->width = width;
    p->height = height;

    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        printf("SDL_Init failed: %s\n", SDL_GetError());
        return false;
    }

    p->window = SDL_CreateWindow(
        title,
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        width, height,
        SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE
    );

    if (!p->window) {
        printf("SDL_CreateWindow failed: %s\n", SDL_GetError());
        SDL_Quit();
        return false;
    }

    p->renderer = SDL_CreateRenderer(
        p->window,
        -1,
        SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC
    );

    if (!p->renderer) {
        printf("SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(p->window);
        p->window = NULL;
        SDL_Quit();
        return false;
    }

    return true;
}

void platform_shutdown(Platform* p) {
    if (p->renderer) SDL_DestroyRenderer(p->renderer);
    if (p->window) SDL_DestroyWindow(p->window);
    p->renderer = NULL;
    p->window = NULL;
    SDL_Quit();
}
