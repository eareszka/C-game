// Biome census: how much of the land each biome covers, how many separate
// regions of it a world has, and how big they are in tiles and in walking
// time. The overworld is 3000 tiles across and a window shows 20 of them, so
// this is the only way to see where the biomes are.
//
//   biomecensus.exe <png dir> <seed> [seed ...]
//
// Writes <png dir>/biomes_<seed>.png, one pixel to the tile (forest dark
// green, meadow green, desert tan, snow white, wasteland brown, the rest
// blue-grey, towns red), prints a table per seed, and exits 1 if any world
// fails the gate: snow, desert and wasteland each at least 5% of the land,
// in one region at least 600 tiles across, and no more than two regions of
// 120x120 or bigger. Build: `make biomecensus`, run from the repo root.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <vector>
#include <algorithm>
#include "tilemap.h"

static Tilemap g_map;
enum { B_GRASS, B_MEADOW, B_SAND, B_SNOW, B_WASTE, B_OTHER, B_N };
static const char* BN[B_N] = { "forest", "meadow", "desert", "snow", "waste", "other" };
static const Uint8 BC[B_N][3] = {
    { 0x20, 0x6A, 0x2A }, { 0x40, 0xC0, 0x60 }, { 0xD8, 0xC0, 0x70 },
    { 0xFF, 0xF8, 0xF0 }, { 0x50, 0x30, 0x1C }, { 0x20, 0x30, 0x60 } };

static int classify(int t) {
    if (t == TILE_GRASS) return B_GRASS;
    if (t == TILE_MEADOW) return B_MEADOW;
    if (t == TILE_SAND) return B_SAND;
    if (t == TILE_SNOW || (t >= TILE_CLIFF_SNOW_1 && t <= TILE_CLIFF_SNOW_5)) return B_SNOW;
    if (t == TILE_WASTELAND || t == TILE_LAVA || (t >= TILE_CLIFF_WASTE_1 && t <= TILE_CLIFF_WASTE_5)) return B_WASTE;
    return B_OTHER;
}

int main(int argc, char** argv) {
    if (argc < 3) { printf("usage: biomecensus <png dir> <seed> [seed ...]\n"); return 1; }
    SDL_SetMainReady();
    SDL_Init(SDL_INIT_VIDEO);
    IMG_Init(IMG_INIT_PNG);
    const int CELL = 10, CW = MAP_WIDTH / CELL, CH = MAP_HEIGHT / CELL;
    const float WALK = 120.0f / TILE_SIZE, RUN = 240.0f / TILE_SIZE;   // tiles a second
    printf("world %dx%d tiles; walk %.2f tiles/s, run %.2f; across the world: walk %.0fs, run %.0fs\n",
           MAP_WIDTH, MAP_HEIGHT, WALK, RUN, MAP_WIDTH / WALK, MAP_WIDTH / RUN);
    std::vector<int> cls((size_t)MAP_WIDTH * MAP_HEIGHT), cell(CW * CH), comp(CW * CH);
    int failed = 0;
    for (int a = 2; a < argc; a++) {
        unsigned seed = (unsigned)strtoul(argv[a], nullptr, 10);
        SDL_Surface* m = SDL_CreateRGBSurfaceWithFormat(0, MAP_WIDTH, MAP_HEIGHT, 32, SDL_PIXELFORMAT_RGBA32);
        SDL_Renderer* mr = SDL_CreateSoftwareRenderer(m);
        tilemap_init_tile_cache(mr);
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        Uint32 colour[B_N];
        for (int b = 0; b < B_N; b++) colour[b] = SDL_MapRGBA(m->format, BC[b][0], BC[b][1], BC[b][2], 255);
        Uint32 red = SDL_MapRGBA(m->format, 255, 0, 0, 255);
        long count[B_N] = {0};
        Uint32* px = (Uint32*)m->pixels;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int c = classify(g_map.tiles[y][x]);
                cls[(size_t)y * MAP_WIDTH + x] = c; count[c]++;
                px[y * (m->pitch / 4) + x] = colour[c];
            }
        for (int i = 0; i < 3; i++) {   // the towns, as red squares
            int tx = g_map.towns[i].x, ty = g_map.towns[i].y;
            for (int dy = -6; dy <= 6; dy++) for (int dx = -6; dx <= 6; dx++) {
                int X = tx + dx, Y = ty + dy;
                if (X >= 0 && Y >= 0 && X < MAP_WIDTH && Y < MAP_HEIGHT) px[Y * (m->pitch / 4) + X] = red;
            }
        }
        char out[512]; snprintf(out, sizeof(out), "%s/biomes_%u.png", argv[1], seed);
        IMG_SavePNG(m, out);

        // Regions are counted on a 10-tile grid, each cell its majority biome,
        // so a river or a road through a region does not split it in two.
        for (int cy = 0; cy < CH; cy++) for (int cx = 0; cx < CW; cx++) {
            int h[B_N] = {0};
            for (int y = cy * CELL; y < (cy + 1) * CELL; y++)
                for (int x = cx * CELL; x < (cx + 1) * CELL; x++) h[cls[(size_t)y * MAP_WIDTH + x]]++;
            int best = B_OTHER, bc = 0;
            for (int b = 0; b < B_OTHER; b++) if (h[b] > bc) { bc = h[b]; best = b; }
            cell[cy * CW + cx] = bc >= CELL * CELL / 4 ? best : B_OTHER;
        }
        long land = 0; for (int b = 0; b < B_OTHER; b++) land += count[b];
        static const char* SIDE[4] = { "west", "east", "north", "south" };
        printf("\n== seed %u: ocean %s, cliff peak at %d,%d ==\n", seed, SIDE[g_map.ocean_side & 3],
               (int)g_map.cliff_peak_x, (int)g_map.cliff_peak_y);
        printf("%-7s %6s %8s %8s %9s  %s\n", "biome", "land%", "regions", ">=40x40", ">=120x120",
               "largest: ~side tiles (walk s / run s) bbox");
        bool ok = true;
        for (int b = 0; b < B_OTHER; b++) {
            std::fill(comp.begin(), comp.end(), -1);
            struct R { long cells; int x0, y0, x1, y1; };
            std::vector<R> regs;
            std::vector<int> stack;
            for (int i = 0; i < CW * CH; i++) {
                if (cell[i] != b || comp[i] >= 0) continue;
                int id = (int)regs.size(); R r{0, CW, CH, -1, -1};
                stack.push_back(i); comp[i] = id;
                while (!stack.empty()) {
                    int j = stack.back(); stack.pop_back(); r.cells++;
                    int jx = j % CW, jy = j / CW;
                    r.x0 = std::min(r.x0, jx); r.x1 = std::max(r.x1, jx);
                    r.y0 = std::min(r.y0, jy); r.y1 = std::max(r.y1, jy);
                    for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) {
                        int nx = jx + dx, ny = jy + dy;
                        if (g_map.wrap_axis == WRAP_X) nx = (nx + CW) % CW; else ny = (ny + CH) % CH;   // the joined axis
                        if (nx < 0 || ny < 0 || nx >= CW || ny >= CH) continue;
                        int k = ny * CW + nx;
                        if (cell[k] == b && comp[k] < 0) { comp[k] = id; stack.push_back(k); }
                    }
                }
                regs.push_back(r);
            }
            std::sort(regs.begin(), regs.end(), [](const R& p, const R& q) { return p.cells > q.cells; });
            int big = 0, huge = 0;
            for (auto& r : regs) { if (r.cells >= 16) big++; if (r.cells >= 144) huge++; }
            double share = 100.0 * count[b] / land;
            float side0 = regs.empty() ? 0.0f : sqrtf((float)regs[0].cells) * CELL;
            printf("%-7s %5.1f%% %8d %8d %9d  ", BN[b], share, (int)regs.size(), big, huge);
            for (int i = 0; i < (int)regs.size() && i < 4; i++) {
                float side = sqrtf((float)regs[i].cells) * CELL;
                printf("%s%.0f (%.0f/%.0f) %dx%d", i ? ", " : "", side, side / WALK, side / RUN,
                       (regs[i].x1 - regs[i].x0 + 1) * CELL, (regs[i].y1 - regs[i].y0 + 1) * CELL);
            }
            bool tier = b == B_SAND || b == B_SNOW || b == B_WASTE;
            if (tier && (share < 5.0 || side0 < 600.0f || huge > 2)) {
                printf("  <-- FAIL (want >=5%% of land, one region >=600 across, <=2 regions >=120x120)");
                ok = false;
            }
            printf("\n");
        }
        printf("other (water/cliff/rock/road) %.1f%% of all tiles; %s\n",
               100.0 * count[B_OTHER] / ((double)MAP_WIDTH * MAP_HEIGHT), ok ? "PASS" : "FAIL");
        if (!ok) failed++;
        SDL_DestroyRenderer(mr); SDL_FreeSurface(m);
    }
    printf("\n%d world%s failed\n", failed, failed == 1 ? "" : "s");
    return failed ? 1 : 0;
}
