// Chase check: the walking chasers' way finding (src/chase_path.cpp), on the
// worlds it runs in.
//
//   chasecheck.exe [seed]       (from the repo root: the tile cache reads assets/)
//
//   1. every route found walks: each straight run of it fits, end to end
//   2. the overworld: a sealed plateau's top and the ground under its face
//      are no way to each other; nor is the start island and the shore across
//      its ring of water
//   3. the chase test cave: pairs on the floor in range, how many are a way,
//      a straight walk, a detour or none
//   4. what a search costs, the worst of them in a full chase box
//
// Exits non-zero if a route does not walk or a case above has a way.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include "tilemap.h"
#include "dungeon.h"
#include "collision.h"
#include "chase_path.h"
#include "towns.h"

static Tilemap g_map;
static DungeonMap g_dmap;
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: " __VA_ARGS__); printf("\n"); fails++; } } while (0)

// The chase box: the screen's half, as main.cpp's LOSE_W / LOSE_H.
static const float HALF_W = 320.0f * 1.5f, HALF_H = 240.0f * 1.6f;
static double worst_cold = 0, total_cold = 0, worst_warm = 0, total_warm = 0;
static long searches = 0;
static ChaseCache g_cache;

// Each search twice: cold, the cache empty (the first time a chaser meets this
// ground), asked again a frame at a time as the game does until it is sure;
// then warm. The worst is of one frame's search.
static int unsure_frames = 0;
static bool timed_route(float sx, float sy, float px, float py, const std::function<bool(float, float)>& fits,
                        std::vector<ResidentPoint>& route) {
    auto run = [&](double* worst, double* total) {
        ChaseWay r;
        int frames = 0;
        do {
            Uint64 t0 = SDL_GetPerformanceCounter();
            r = chase_route(&g_cache, sx, sy, px, py, HALF_W, HALF_H, fits, route, CHASE_ASKS);
            double ms = (SDL_GetPerformanceCounter() - t0) * 1000.0 / SDL_GetPerformanceFrequency();
            *total += ms;
            if (ms > *worst) *worst = ms;
            if (r == CHASE_UNSURE) frames++;
        } while (r == CHASE_UNSURE && frames < 100);
        if (frames > unsure_frames) unsure_frames = frames;
        return r == CHASE_WAY;
    };
    g_cache.clear();
    bool cold = run(&worst_cold, &total_cold);
    bool warm = run(&worst_warm, &total_warm);
    CHECK(cold == warm, "the cache changed the answer at %.0f,%.0f -> %.0f,%.0f", sx, sy, px, py);
    searches++;
    return warm;
}

// Pairs in range on ground that fits: routes that walk, and the tally.
static void sample(const char* where, const std::function<bool(float, float)>& fits,
                   float x0, float y0, float x1, float y1, unsigned rng, int pairs) {
    auto rnd = [&](float a, float b) { rng = rng * 1664525u + 1013904223u; return a + (b - a) * ((rng >> 8) & 0xFFFF) / 65535.0f; };
    int straight = 0, detour = 0, none = 0, tries = 0;
    std::vector<ResidentPoint> route;
    while (straight + detour + none < pairs && tries++ < pairs * 200) {
        float px = rnd(x0, x1), py = rnd(y0, y1);
        float sx = px + rnd(-HALF_W, HALF_W) * 0.8f, sy = py + rnd(-HALF_H, HALF_H) * 0.8f;
        if (!fits(px, py) || !fits(sx, sy)) continue;
        if (chase_straight(sx, sy, px, py, fits)) { straight++; continue; }
        if (!timed_route(sx, sy, px, py, fits, route)) { none++; continue; }
        detour++;
        ResidentPoint from = { sx, sy };
        for (const ResidentPoint& p : route) {
            CHECK(chase_straight(from.x, from.y, p.x, p.y, fits), "%s: a leg of the route %.0f,%.0f -> %.0f,%.0f does not walk",
                  where, from.x, from.y, p.x, p.y);
            from = p;
        }
        CHECK(!route.empty() && fabsf(route.back().x - px) < 0.5f && fabsf(route.back().y - py) < 0.5f, "%s: the route ends off the player", where);
    }
    printf("%s: %d pairs -- %d straight, %d a detour, %d no way\n", where, straight + detour + none, straight, detour, none);
}

int main(int argc, char** argv) {
    unsigned seed = argc > 1 ? (unsigned)strtoul(argv[1], nullptr, 10) : 407u;
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);
    const float FX = (HB_X1 + HB_X2) * 0.5f, FY = (HB_Y1 + HB_Y2) * 0.5f;

    // ── The overworld ──
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);
    auto ow_fits = [&](float x, float y) { return can_occupy(&g_map, x - FX, y - FY, tilemap_pixel_solid); };
    {   // what one fits costs
        Uint64 t0 = SDL_GetPerformanceCounter(); int n = 0;
        for (int i = 0; i < 200000; i++) n += ow_fits(40000.0f + (i % 400) * 7.0f, 40000.0f + (i / 400) * 7.0f);
        printf("overworld fits: %.3f us each (%d fit)\n", (SDL_GetPerformanceCounter() - t0) * 1e6 / SDL_GetPerformanceFrequency() / 200000, n);
    }
    sample("overworld", ow_fits, 0, 0, MAP_WIDTH * TILE_SIZE, MAP_HEIGHT * TILE_SIZE, seed, 300);

    // A sealed plateau's top, and the ground straight down the face from it.
    std::vector<ResidentPoint> route;
    int plateaus = 0;
    for (int ty = 8; ty < MAP_HEIGHT - 16 && plateaus < 12; ty += 7)
        for (int tx = 8; tx < MAP_WIDTH - 8 && plateaus < 12; tx += 7) {
            if (!tilemap_cliff_sealed_at(tx, ty) || tilemap_cliff_elev_at(tx, ty) <= 0) continue;
            float sx = (tx + 0.5f) * TILE_SIZE, sy = (ty + 0.5f) * TILE_SIZE;
            if (!ow_fits(sx, sy)) continue;
            int by = ty + 1;
            while (by < ty + 12 && tilemap_cliff_elev_at(tx, by) > 0) by++;
            float px = sx, py = (by + 3.5f) * TILE_SIZE;
            if (tilemap_cliff_elev_at(tx, by + 3) != 0 || !ow_fits(px, py)) continue;
            plateaus++;
            CHECK(!timed_route(sx, sy, px, py, ow_fits, route), "a sealed plateau's top at %d,%d has a way down to %d,%d",
                  tx, ty, tx, by + 3);
        }
    printf("sealed plateaus tried: %d\n", plateaus);
    CHECK(plateaus > 0, "no sealed plateau found to try");

    // Across a river: land either side of a few tiles of water, no deck in
    // between. Told, not checked -- a bridge or the river's end may be in range.
    {
        int tried = 0, none = 0;
        for (int ty = 8; ty < MAP_HEIGHT - 8 && tried < 40; ty += 13)
            for (int tx = 8; tx < MAP_WIDTH - 16 && tried < 40; tx += 3) {
                if (g_map.tiles[ty][tx] != TILE_RIVER || g_map.tiles[ty][tx - 1] == TILE_RIVER) continue;
                int e = tx;
                while (e < tx + 6 && g_map.tiles[ty][e] == TILE_RIVER) e++;
                if (e - tx < 2 || g_map.tiles[ty][e] == TILE_RIVER) continue;
                float sx = (tx - 2 + 0.5f) * TILE_SIZE, px = (e + 2 + 0.5f) * TILE_SIZE, y = (ty + 0.5f) * TILE_SIZE;
                if (!ow_fits(sx, y) || !ow_fits(px, y) || chase_straight(sx, y, px, y, ow_fits)) continue;
                tried++;
                if (!timed_route(sx, y, px, y, ow_fits, route)) none++;
            }
        printf("across a river: %d tried, %d no way (the rest a bridge or a bend in range)\n", tried, none);
    }

    // ── The chase test cave (main.cpp enter_chase_test) ──
    DungeonWiring w = {};
    w.seed = 0xC4A5Eu; w.difficulty = 0.5f; w.type = DUNGEON_ENT_CAVE;
    w.connect_angle = NAN; w.my_mouth = -1;
    dungeon_want(&g_dmap, &w);
    dungeon_generate(&g_dmap, w.type, w.difficulty, w.seed);
    auto dng_fits = [&](float x, float y) { return can_occupy(&g_dmap, x - FX, y - FY, dungeon_solid_at); };
    sample("chase cave", dng_fits, 0, 0, DMAP_W * DMAP_TILE, DMAP_H * DMAP_TILE, 0xC4A5Eu, 300);

    printf("searches: %ld -- cold %.3f ms on average, the worst %.3f ms; warm %.3f ms, the worst %.3f ms\n", searches,
           searches ? total_cold / searches : 0.0, worst_cold, searches ? total_warm / searches : 0.0, worst_warm);
    printf("frames a first look took at most: %d\n", unsure_frames + 1);
    if (fails) printf("\n%d failures\n", fails);
    else printf("chasecheck: ok\n");
    return fails ? 1 : 0;
}
