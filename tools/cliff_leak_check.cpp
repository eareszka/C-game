// The player can walk behind an island, under its back outline, as far as the
// real back edge (BackRun in src/tilemap.cpp). That must not be a way up: a
// sealed top is reached by cave and nothing else. Every outline in the world is
// walked from its north, the feet flooded through the way behind it by the rule
// the game moves them with, and none may come out on the plateau.
//
//   cliff_leak_check.exe [seed ...]     exits 1 if any did
//
// Build: make cliff_leak_check. Run from the repo root (it reads the sheet).
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "tilemap.h"
#include "camera.h"

static Tilemap g_map;

int main(int argc, char** argv)
{
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 2; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* s = SDL_CreateRGBSurfaceWithFormat(0, 16, 16, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(s);
    tilemap_init_tile_cache(ren);

    std::vector<unsigned> seeds;
    for (int i = 1; i < argc; i++) seeds.push_back((unsigned)strtoul(argv[i], nullptr, 10));
    if (seeds.empty()) seeds = { 387u, 407u, 463u };

    int total = 0;
    for (unsigned seed : seeds) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        BehindAudit a;
        tilemap_behind_audit(&g_map, &a);
        printf("seed %u: %d outlines, %d can be walked behind, %lld feet positions, %d escapes",
               seed, a.runs, a.usable, a.positions, a.escapes);
        if (a.escapes) printf(" (first near tile %d,%d)", a.first_x, a.first_y);
        printf("\n");
        fflush(stdout);
        total += a.escapes;
    }
    printf("%s: %d escapes\n", total ? "FAIL" : "ok", total);
    return total ? 1 : 0;
}
