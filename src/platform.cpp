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

    // No PRESENTVSYNC — WSL2's virtualised vsync signal is imprecise and causes
    // uneven frame delivery. We implement a manual frame cap in the game loop instead.
    p->renderer = SDL_CreateRenderer(p->window, -1, SDL_RENDERER_ACCELERATED);

    if (!p->renderer) {
        printf("SDL_CreateRenderer failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(p->window);
        p->window = NULL;
        SDL_Quit();
        return false;
    }

    SDL_RendererInfo info;
    if (SDL_GetRendererInfo(p->renderer, &info) == 0) {
        printf("Renderer: %s (%s)\n", info.name,
               (info.flags & SDL_RENDERER_ACCELERATED) ? "hardware" : "SOFTWARE — expect fill-rate limits at large window sizes");
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
