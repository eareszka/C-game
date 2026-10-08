// Spawn census: how dungeon difficulty spreads across worlds, and which enemies
// (by tier) the spawn picker puts where.
//
//   spawncensus.exe [seed ...]          (no args: 16 fixed seeds)
//
// Prints the difficulty quantiles that src/dungeon.cpp's TIER_CUTS are set
// from, then simulates DNG_SPAWNER_BUDGET picks in every dungeon through the
// game's own dungeon_pick_enemy() and reports picks per tier and per enemy --
// any common never picked is a hole in the pools. Run from the repo root (it
// reads assets/tileset.png, like dngcensus).
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <vector>
#include "tilemap.h"
#include "dungeon.h"
#include "enemy.h"

static Tilemap g_map;

int main(int argc, char** argv) {
    std::vector<unsigned> seeds;
    for (int i = 1; i < argc; i++) seeds.push_back((unsigned)strtoul(argv[i], nullptr, 10));
    if (seeds.empty()) {
        const unsigned KNOWN[] = { 407, 463, 387, 398, 99, 5150, 1234, 7, 20260812, 555 };
        for (unsigned s : KNOWN) seeds.push_back(s);
        for (int i = 10; i < 16; i++) seeds.push_back(100000u + (unsigned)i * 7919u);
    }
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);

    std::vector<float> diffs;
    std::vector<std::pair<int, float>> sites;   // (type, difficulty)
    for (unsigned seed : seeds) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            diffs.push_back(e.difficulty);
            sites.push_back({ (int)e.type, e.difficulty });
        }
    }
    std::sort(diffs.begin(), diffs.end());
    printf("%zu dungeon entrances over %zu seeds\ndifficulty quantiles:", diffs.size(), seeds.size());
    for (int q = 10; q <= 90; q += 10) printf("  q%d=%.3f", q, diffs[diffs.size() * q / 100]);
    printf("\n");

    int per_enemy[ENEMY_COUNT] = {}, per_tier[16] = {}, total = 0;
    uint32_t rng = 12345u;
    for (auto& s : sites)
        for (int k = 0; k < DNG_SPAWNER_BUDGET; k++) {
            int e = dungeon_pick_enemy((DungeonEntranceType)s.first, s.second, &rng);
            per_enemy[e]++; per_tier[enemy_tier(e)]++; total++;
        }
    static const char* TN[] = { "unset", "starter", "low", "medium", "upper", "hard", "severe", "elite", "boss1", "boss2" };
    printf("\npicks by tier (%d):\n", total);
    for (int t = 0; t < 10; t++) if (per_tier[t]) printf("  %-8s %6.1f%%\n", TN[t], 100.0 * per_tier[t] / total);
    printf("\npicks by enemy:\n");
    for (int e = 0; e < ENEMY_COUNT; e++)
        printf("  %02d %-7s %6.2f%%%s\n", e, TN[enemy_tier(e)], 100.0 * per_enemy[e] / total,
               per_enemy[e] == 0 && !enemy_is_boss(e) ? "   <-- NEVER" : "");
    return 0;
}
