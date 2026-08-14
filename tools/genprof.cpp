// Worldgen profiler: builds a world and reports how long each generation stage
// took, worst first.
//
//   genprof.exe [seed]
//
// Worldgen is two dozen passes over a nine-million-tile map and the player
// waits for all of it, so "which pass is the slow one" is the question that has
// to be answerable before anything is tuned. It is answered off the tracing
// hook that is already there: tilemap.cpp calls GEN_STAGE at every stage
// boundary, which compiles to gen_trace_stage() when GEN_TRACE is defined and
// to nothing otherwise. Nothing in the shipping build changes.
//
// Build it from MSYS2 MINGW64, with tilemap.cpp compiled -DGEN_TRACE for this
// binary only (note -Umain, as in tools/shot.cpp: without it SDL's
// -Dmain=SDL_main turns main into SDL_main and the link fails on WinMain):
//
//   g++ -O2 -w -std=c++17 -Iinclude -DGEN_TRACE -c src/tilemap.cpp -o tilemap_prof.o
//   g++ -O2 -w -std=c++17 -I. -Iinclude -DSDL_MAIN_HANDLED -DGEN_TRACE \
//     $(pkg-config --cflags sdl2 SDL2_image) -Umain tools/genprof.cpp \
//     tilemap_prof.o src/resource_node.o src/core.o src/camera.o -o genprof.exe \
//     $(pkg-config --libs sdl2 SDL2_image | sed "s/-lSDL2main//; s/-mwindows//")
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include "tilemap.h"

static Tilemap g_map;

struct Stage { std::string name; double ms; };
static std::vector<Stage> g_stages;
static Uint64 g_last, g_freq;

// The stage name handed over is the boundary *before* a pass, so the time
// charged here belongs to the pass named by the previous call. Recording it
// that way round is what makes the table read as "this pass cost this much"
// rather than off by one.
static std::string g_pending = "(startup)";

void gen_trace_stage(const Tilemap* /*map*/, const char* stage)
{
    Uint64 now = SDL_GetPerformanceCounter();
    double ms = (double)(now - g_last) * 1000.0 / (double)g_freq;
    g_stages.push_back({ g_pending, ms });
    g_pending = stage ? stage : "(null)";
    g_last = now;
}

int main(int argc, char** argv)
{
    unsigned seed = (argc > 1) ? (unsigned)strtoul(argv[1], nullptr, 10) : 387u;

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);

    SDL_Surface* s = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* r = SDL_CreateSoftwareRenderer(s);

    // Timed separately because the player waits for this too: it is the tile
    // sheet being cut up and the cliff ink mask being read back off it, and it
    // happens once at startup whether or not a world is being built.
    Uint64 freq0 = SDL_GetPerformanceFrequency();
    Uint64 ti = SDL_GetPerformanceCounter();
    tilemap_init_tile_cache(r);
    double init_ms = (double)(SDL_GetPerformanceCounter() - ti) * 1000.0 / (double)freq0;
    printf("tile cache init %.0f ms\n", init_ms);

    g_freq = SDL_GetPerformanceFrequency();
    Uint64 t0 = SDL_GetPerformanceCounter();
    g_last = t0;

    tilemap_build_overworld_phase1(&g_map, seed);
    double p1 = (double)(SDL_GetPerformanceCounter() - t0) * 1000.0 / (double)g_freq;

    Uint64 t1 = SDL_GetPerformanceCounter();
    tilemap_build_overworld_phase2(&g_map, seed);
    double p2 = (double)(SDL_GetPerformanceCounter() - t1) * 1000.0 / (double)g_freq;

    // Whatever was still pending when the last stage ran.
    gen_trace_stage(&g_map, "(end)");

    // A checksum of the whole world, which is what an optimisation has to leave
    // alone. A rendered window is the wrong instrument here: it covers 44x30 of
    // 3000x3000, and a biome pass can move a desert on the far side of the map
    // without touching a single pixel of it. Hash every tile and every overlay
    // instead, and the test covers all nine million.
    uint64_t h = 1469598103934665603ull;                    // FNV-1a
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            h = (h ^ (uint64_t)(unsigned)g_map.tiles[y][x])   * 1099511628211ull;
            h = (h ^ (uint64_t)(unsigned)g_map.overlay[y][x]) * 1099511628211ull;
        }

    double total = p1 + p2;
    printf("seed %u   phase1 %.0f ms   phase2 %.0f ms   total %.0f ms   world %016llx\n",
           seed, p1, p2, total, (unsigned long long)h);

    // Castles 0-2 are placed during phase2 and keep {-1,-1} when their pass
    // finds nowhere to stand. Worth printing: castle 1 spent the project so far
    // never placing at all, and nothing said so.
    static const char* CASTLE_NAME[3] = { "ocean", "mountain", "lava" };
    printf("  castles:");
    for (int i = 0; i < 3; i++) {
        if (g_map.castles[i].x < 0) printf("  %s=none", CASTLE_NAME[i]);
        else printf("  %s=%d,%d", CASTLE_NAME[i], g_map.castles[i].x, g_map.castles[i].y);
    }
    printf("\n\n");

    std::vector<Stage> by_cost = g_stages;
    std::sort(by_cost.begin(), by_cost.end(),
              [](const Stage& a, const Stage& b) { return a.ms > b.ms; });

    printf("%-52s %9s %7s\n", "stage", "ms", "share");
    printf("%-52s %9s %7s\n", "-----", "--", "-----");
    double shown = 0.0;
    for (const Stage& st : by_cost) {
        if (st.ms < 1.0) continue;              // noise
        shown += st.ms;
        printf("%-52s %9.1f %6.1f%%\n", st.name.c_str(), st.ms,
               total > 0.0 ? 100.0 * st.ms / total : 0.0);
    }
    printf("\n%zu stages, %.0f ms accounted for out of %.0f\n",
           g_stages.size(), shown, total);
    return 0;
}
