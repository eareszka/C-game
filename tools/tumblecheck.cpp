// Tumble check: the desert's rolling tumbleweeds (src/tumbleweed.cpp) let
// loose all over a world's sand and blown about for their whole lives.
//
//   tumblecheck.exe [seed]      (from the repo root: the tile cache reads assets/)
//
//   1. none is laid on the map any more: no cell of its frames on the overlay
//   2. its ground point never stands inside shut ground (a cliff, water, a wall)
//      -- props and rocks it hops, so those it may pass over
//   3. it never sinks below the ground
//   4. it goes somewhere: most travel ten tiles or more (a few may fetch up in
//      a corner the wind holds them in, and are told)
//   5. it turns through its frames, and some landings are the big hops
//
// Exits non-zero if any check fails.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "tilemap.h"
#include "tumbleweed.h"

static Tilemap g_map;
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: " __VA_ARGS__); printf("\n"); fails++; } } while (0)

int main(int argc, char** argv) {
    unsigned seed = argc > 1 ? (unsigned)strtoul(argv[1], nullptr, 10) : 407u;
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);

    // 1. The tile ones: its eight frames are cells 13-20 of sheet row 226.
    long laid = 0;
    const int first = TILE_TOWN0_BASE + 226 * TOWN0_SHEET_COLS + 13;
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++)
            if (g_map.overlay[y][x] >= first && g_map.overlay[y][x] < first + 8) laid++;
    CHECK(laid == 0, "%ld tumbleweed cells still laid on the map", laid);

    // Sand to let them loose on, spread over the desert.
    std::vector<std::pair<float, float>> starts;
    for (int ty = 5; ty < MAP_HEIGHT - 5; ty += 11)
        for (int tx = 5; tx < MAP_WIDTH - 5; tx += 11) {
            if (g_map.tiles[ty][tx] != TILE_SAND) continue;
            float x = (tx + 0.5f) * TILE_SIZE, y = (ty + 0.5f) * TILE_SIZE;
            if (!tilemap_pixel_solid(&g_map, x, y)) starts.push_back({ x, y });
        }
    CHECK(!starts.empty(), "no sand in this world");
    const int RUNS = 200;
    size_t step = starts.size() / RUNS ? starts.size() / RUNS : 1;

    long runs = 0, shut = 0, sunk = 0, short_runs = 0, hops = 0, big = 0, deflects = 0;
    bool frames[8] = {};
    double total_dist = 0;
    for (size_t k = 0; k < starts.size() && runs < RUNS; k += step, runs++) {
        tumble_clear();
        float x0 = starts[k].first, y0 = starts[k].second;
        Tumbleweed* t = tumble_spawn_at(x0, y0);
        double world = runs * 137.0;   // the wind from all round the day
        float far = 0;
        for (int f = 0; f < 40 * 60; f++) {
            tumble_step(t, &g_map, world, 1.0f / 60.0f);
            world += 1.0 / 60.0;
            if (t->z < 0.0f) sunk++;
            if (tilemap_pixel_solid(&g_map, t->x, t->y) && !tilemap_low_obstacle(&g_map, t->x, t->y)) shut++;
            frames[tumble_frame(*t)] = true;
            float dx = wrap_dpx(t->x - x0), dy = wrap_dpy(t->y - y0);
            far = fmaxf(far, sqrtf(dx * dx + dy * dy));
        }
        total_dist += far;
        if (far < 10 * TILE_SIZE) short_runs++;
        hops += t->hops; big += t->big_hops; deflects += t->deflects;
    }
    int nframes = 0;
    for (bool b : frames) nframes += b;
    printf("%ld runs of 40 s: %ld landings, %ld big hops, %ld glances off shut ground\n", runs, hops, big, deflects);
    printf("farthest from its start: %.1f tiles on average; %ld under 10 tiles\n", total_dist / runs / TILE_SIZE, short_runs);
    printf("frames shown: %d of 8\n", nframes);
    CHECK(shut == 0, "%ld frames with the ground point inside shut ground", shut);
    CHECK(sunk == 0, "%ld frames below the ground", sunk);
    CHECK(short_runs * 10 <= runs, "%ld of %ld went under 10 tiles", short_runs, runs);
    CHECK(nframes == 8, "only %d of the 8 frames turned through", nframes);
    CHECK(big > 0, "no big hops");
    // TUMBLE_PNG=out.png: one weed's way over the sand, a frame of it every
    // tenth of a second laid over the last, the ground drawn as the game does --
    // to judge the ball, its bounces and its shadow in the world.
    if (const char* png = getenv("TUMBLE_PNG")) {
        const int W = 640, H = 360;
        SDL_Surface* shot = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
        SDL_Renderer* r = SDL_CreateSoftwareRenderer(shot);
        tilemap_init_tile_cache(r);
        // The first start with open sand ahead along the wind at world time 0.
        for (size_t k = 0; k < starts.size(); k++) {
            tumble_clear();
            Tumbleweed* t = tumble_spawn_at(starts[k].first, starts[k].second);
            t->z = 0; t->vz = 200;
            std::vector<Tumbleweed> trail;
            double world = 0;
            for (int f = 0; f < 150; f++) {   // 2.5 s
                tumble_step(t, &g_map, world, 1.0f / 60.0f);
                world += 1.0 / 60.0;
                if (f % 15 == 0) trail.push_back(*t);
            }
            if (t->deflects || fabsf(wrap_dpx(t->x - starts[k].first)) < 250.0f) continue;
            Camera cam = {};
            cam.screen_w = W; cam.screen_h = H; cam.zoom = 1.0f;
            float mx = starts[k].first + wrap_dpx(t->x - starts[k].first) * 0.5f;
            float my = starts[k].second + wrap_dpy(t->y - starts[k].second) * 0.5f - 20.0f;
            camera_place(&cam, mx - W / 2, my - H / 2);
            SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
            SDL_RenderClear(r);
            tilemap_draw_base(&g_map, &cam, r);
            Tumbleweed* live = (Tumbleweed*)tumble_list();
            for (const Tumbleweed& snap : trail) {
                live[0] = snap;
                tumble_draw_one(r, &cam, tilemap_get_town_tex(), 0);
            }
            tilemap_draw_depth(&g_map, &cam, r);
            SDL_RenderPresent(r);
            IMG_SavePNG(shot, png);
            printf("wrote %s (start %.0f,%.0f)\n", png, starts[k].first, starts[k].second);
            break;
        }
    }
    if (fails) printf("\n%d failures\n", fails);
    else printf("tumblecheck: ok\n");
    return fails ? 1 : 0;
}
