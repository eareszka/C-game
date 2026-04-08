#include "core.h"
#include <SDL2/SDL.h>

double time_delta_seconds(void) {
    static Uint64 prev = 0;

    if (prev == 0) {
        prev = SDL_GetPerformanceCounter();
        return 0.0;
    }

    Uint64 now = SDL_GetPerformanceCounter();
    double dt = (double)(now - prev) / (double)SDL_GetPerformanceFrequency();
    prev = now;
    return dt;
}
