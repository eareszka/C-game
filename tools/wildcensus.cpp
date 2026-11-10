// Wild census: the overworld's packs (src/wilds.cpp) across worlds -- how many
// squares hold one, how far from a track they stand, how big they run, which
// tiers and regions they draw, and what a square costs to roll.
//
//   wildcensus.exe [seed ...]          (no args: 6 fixed seeds)
//
// WILD_PNG=out.png: the first seed's world drawn half size, tracks orange and
// every pack member a red dot, to see the wilds against the roads.
//
// Exits non-zero if a pack stands nearer a track than WILD_ROAD_CLEAR, or if
// rolling the same square twice gives two answers. Run from the repo root (it
// reads assets/tileset.png, like spawncensus).
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "tilemap.h"
#include "wilds.h"
#include "enemy.h"

static Tilemap g_map;

int main(int argc, char** argv) {
    std::vector<unsigned> seeds;
    for (int i = 1; i < argc; i++) seeds.push_back((unsigned)strtoul(argv[i], nullptr, 10));
    if (seeds.empty()) { const unsigned KNOWN[] = { 407, 463, 387, 99, 5150, 1234 }; for (unsigned s : KNOWN) seeds.push_back(s); }
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);

    static const char* TN[] = { "unset", "starter", "low", "medium", "upper", "hard", "severe", "elite", "boss1", "boss2", "boss3" };
    static const char* RN[] = { "grass", "forest", "snow", "desert", "waste", "mountain", "ocean" };
    long squares = 0, packs = 0, members = 0, by_size[WILD_PACK_MAX + 1] = {}, by_road[10] = {};
    long per_tier[16] = {}, per_region[7] = {};
    int bad = 0;
    double ms_total = 0;
    for (unsigned seed : seeds) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        long sp = 0;
        Uint64 t0 = SDL_GetPerformanceCounter();
        for (int cy = 0; cy < WILD_CHUNKS_Y; cy++)
            for (int cx = 0; cx < WILD_CHUNKS_X; cx++) {
                WildPack p, q;
                wild_pack(&g_map, seed, cx, cy, &p);
                squares++;
                if ((cx * 7 + cy) % 97 == 0) {   // the same square, the same pack
                    wild_pack(&g_map, seed, cx, cy, &q);
                    if (q.n != p.n || (p.n && (q.enemy[0] != p.enemy[0] || q.x[0] != p.x[0]))) {
                        printf("  seed %u square %d,%d rolled two ways\n", seed, cx, cy); bad++;
                    }
                }
                if (!p.n) continue;
                packs++; sp++; by_size[p.n]++; members += p.n;
                by_road[p.road / 10 < 9 ? p.road / 10 : 9]++;
                for (int i = 0; i < p.n; i++) {
                    int tx = (int)(p.x[i] / TILE_SIZE), ty = (int)(p.y[i] / TILE_SIZE);
                    int d = wild_road_distance(&g_map, tx, ty, WILD_ROAD_CLEAR);
                    if (d < WILD_ROAD_CLEAR - 3) {   // members gather a couple of tiles round the spot
                        printf("  seed %u square %d,%d member %d stands %d from a road\n", seed, cx, cy, i, d); bad++;
                    }
                    if (g_map.route[ty][tx] != ROUTE_NONE) {   // beside a trail is fine, on one is not
                        printf("  seed %u square %d,%d member %d stands on a track\n", seed, cx, cy, i); bad++;
                    }
                    per_tier[enemy_tier(p.enemy[i])]++;
                    per_region[enemy_region(p.enemy[i])]++;
                }
            }
        double ms = (SDL_GetPerformanceCounter() - t0) * 1000.0 / SDL_GetPerformanceFrequency();
        if (const char* png = getenv("WILD_PNG"); png && seed == seeds[0]) {
            const int W = MAP_WIDTH / 2, H = MAP_HEIGHT / 2;
            SDL_Surface* img = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
            Uint32* px = (Uint32*)img->pixels;
            auto rgb = [&](int r, int g, int b) { return SDL_MapRGBA(img->format, r, g, b, 255); };
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++) {
                    int tx = x * 2, ty = y * 2, t = g_map.tiles[ty][tx];
                    Uint32 c = rgb(70, 140, 60);
                    if (t == TILE_WATER || t == TILE_RIVER || t == TILE_HUB || t == TILE_POND) c = rgb(40, 80, 170);
                    else if (t == TILE_SAND)      c = rgb(210, 190, 120);
                    else if (t == TILE_SNOW)      c = rgb(230, 235, 245);
                    else if (t == TILE_WASTELAND) c = rgb(110, 95, 110);
                    else if (t == TILE_LAVA)      c = rgb(40, 20, 50);
                    else if (t == TILE_MEADOW)    c = rgb(120, 175, 80);
                    if (g_map.overlay[ty][tx] == TILE_TREE) c = rgb(35, 90, 40);
                    if (tilemap_cliff_elev_at(tx, ty) > 0) c = rgb(130, 100, 70);
                    if (g_map.route[ty][tx] || g_map.route[ty][tx + 1] || g_map.route[ty + 1][tx]) c = rgb(255, 150, 0);
                    px[y * W + x] = c;
                }
            for (int cy = 0; cy < WILD_CHUNKS_Y; cy++)
                for (int cx = 0; cx < WILD_CHUNKS_X; cx++) {
                    WildPack p;
                    wild_pack(&g_map, seed, cx, cy, &p);
                    for (int i = 0; i < p.n; i++) {
                        int x = (int)(p.x[i] / TILE_SIZE) / 2, y = (int)(p.y[i] / TILE_SIZE) / 2;
                        for (int dy = -1; dy <= 1; dy++)
                            for (int dx = -1; dx <= 1; dx++)
                                if (x + dx >= 0 && x + dx < W && y + dy >= 0 && y + dy < H) px[(y + dy) * W + x + dx] = rgb(230, 20, 20);
                    }
                }
            IMG_SavePNG(img, png);
            printf("wrote %s\n", png);
        }
        ms_total += ms;
        printf("seed %-9u packs %5ld of %d squares  (%.3f ms a square)\n", seed, sp,
               WILD_CHUNKS_X * WILD_CHUNKS_Y, ms / (WILD_CHUNKS_X * WILD_CHUNKS_Y));
    }
    printf("\n%ld packs in %ld squares (%.1f%%), %ld members, %.2f a pack\n", packs, squares,
           100.0 * packs / squares, members, packs ? (double)members / packs : 0.0);
    printf("size:"); for (int n = 1; n <= WILD_PACK_MAX; n++) printf("  %d: %.1f%%", n, 100.0 * by_size[n] / packs); printf("\n");
    printf("tiles from a track:"); for (int b = 0; b < 10; b++) printf("  %d%s: %ld", b * 10, b == 9 ? "+" : "s", by_road[b]); printf("\n");
    printf("tiers:"); for (int t = 0; t < 11; t++) if (per_tier[t]) printf("  %s %.1f%%", TN[t], 100.0 * per_tier[t] / members); printf("\n");
    printf("regions:"); for (int r = 0; r < 7; r++) if (per_region[r]) printf("  %s %.1f%%", RN[r], 100.0 * per_region[r] / members); printf("\n");
    printf("rolling: %.3f ms a square on average\n", ms_total / squares);
    if (bad) printf("\n%d problems\n", bad);
    return bad ? 1 : 0;
}
