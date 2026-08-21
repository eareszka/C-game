// Cave difficulty census: what material tier would each cave actually yield?
//
//   oreprof.exe [seed ...]        (defaults to a spread of seeds)
//
// The material a cave holds is meant to be gated on DungeonEntrance.difficulty
// -- ((dist/max_dist) + cliff_lvl/5) * 0.5, tilemap.cpp:4574 -- so that a
// player has to travel out or climb to reach the good stuff. But difficulty is
// an AVERAGE of two normalised terms, which compresses its range toward the
// middle, and caves are cut into mountains so their elevation term is never
// zero. Both push the distribution away from the ends.
//
// If every cave lands between 0.3 and 0.7 then a linear tier = difficulty*7
// only ever produces the middle tiers and the ladder is broken at both ends.
// That is a question about generated worlds, not about the formula, so this
// measures it: the histogram of cave difficulty, and the resulting tier counts.
//
// Build (from MSYS2 MINGW64, links the already-built objects like shot.exe):
//   g++ -std=c++17 -O2 -Iinclude -w -DSDL_MAIN_HANDLED \
//       $(pkg-config --cflags sdl2 SDL2_image) -Umain tools/oreprof.cpp \
//       $(ls src/*.o | grep -v src/main.o) -o oreprof.exe \
//       $(pkg-config --libs sdl2 SDL2_image | sed 's/-lSDL2main//; s/-mwindows//') \
//       -lm -lpthread
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include "tilemap.h"
#include "dungeon.h"

static Tilemap g_map;

static int cmpf(const void* a, const void* b) {
    float fa = *(const float*)a, fb = *(const float*)b;
    return (fa > fb) - (fa < fb);
}

// The shipped mapping, not a replica of it -- material_for_difficulty() is
// linked in from src/dungeon.cpp so this census can never disagree with what
// the game actually does.
static int tier_of(float difficulty) {
    return (int)material_for_difficulty(difficulty);
}

int main(int argc, char** argv) {
    unsigned seeds[16];
    int nseeds = 0;
    if (argc > 1) {
        for (int i = 1; i < argc && nseeds < 16; i++)
            seeds[nseeds++] = (unsigned)strtoul(argv[i], nullptr, 10);
    } else {
        unsigned d[] = { 407, 463, 387, 398, 99, 5150, 1234, 7 };
        for (unsigned s : d) seeds[nseeds++] = s;
    }

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);

    int tier_tot[7] = {0};
    int sys_tier_tot[7] = {0};
    int bucket[10] = {0};
    int mouths_tot = 0, systems_tot = 0;
    static float all_diff[8192]; int n_all = 0;
    float lo = 2.0f, hi = -1.0f;

    for (int si = 0; si < nseeds; si++) {
        tilemap_build_overworld_phase1(&g_map, seeds[si]);
        tilemap_build_overworld_phase2(&g_map, seeds[si]);

        int tier[7] = {0};
        int mouths = 0;
        // One cave system = one anchor. Counting mouths would over-weight the
        // mountains, where a single cave opens three or four ways.
        int ax[512], ay[512]; int sys = 0;
        int sys_tier[7] = {0};

        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            if (e.type != DUNGEON_ENT_CAVE) continue;
            mouths++;
            int t = tier_of(e.difficulty);
            tier[t]++;
            if (e.difficulty < lo) lo = e.difficulty;
            if (e.difficulty > hi) hi = e.difficulty;
            int b = (int)(e.difficulty * 10.0f); if (b > 9) b = 9; if (b < 0) b = 0;
            bucket[b]++;

            bool known = false;
            if (e.cave_anchor_x >= 0) {
                for (int s = 0; s < sys; s++)
                    if (ax[s] == e.cave_anchor_x && ay[s] == e.cave_anchor_y) { known = true; break; }
                if (!known && sys < 512) { ax[sys] = e.cave_anchor_x; ay[sys] = e.cave_anchor_y; sys++; }
            } else {
                sys++;   // a flat/wasteland cave is its own system
            }
            if (!known) { sys_tier[t]++; if (n_all < 8192) all_diff[n_all++] = e.difficulty; }
        }

        printf("seed %-9u caves: %3d mouths, %3d systems   tiers by system:", seeds[si], mouths, sys);
        for (int t = 0; t < 7; t++) printf(" %d:%d", t, sys_tier[t]);
        printf("\n");

        mouths_tot += mouths; systems_tot += sys;
        for (int t = 0; t < 7; t++) { tier_tot[t] += tier[t]; sys_tier_tot[t] += sys_tier[t]; }
    }

    printf("\n=== across %d seeds: %d cave systems (%d mouths) ===\n",
           nseeds, systems_tot, mouths_tot);
    printf("difficulty range seen: %.3f .. %.3f\n\n", lo, hi);

    printf("difficulty histogram (by mouth):\n");
    for (int b = 0; b < 10; b++) {
        printf("  %.1f-%.1f  %5d  ", b / 10.0f, (b + 1) / 10.0f, bucket[b]);
        int bar = mouths_tot ? bucket[b] * 50 / mouths_tot : 0;
        for (int i = 0; i < bar; i++) putchar('#');
        putchar('\n');
    }

    printf("\nmaterial tier by CAVE SYSTEM (what the player actually encounters):\n");
    int empty = 0;
    for (int t = 0; t < 7; t++) {
        float pct = systems_tot ? 100.0f * sys_tier_tot[t] / systems_tot : 0.0f;
        printf("  tier %d %-13s %5d  %5.1f%%  %s\n", t, material_name((Material)t), sys_tier_tot[t], pct,
               sys_tier_tot[t] == 0 ? "<-- UNREACHABLE" : "");
        if (sys_tier_tot[t] == 0) empty++;
    }
    printf("\n%d of 7 tiers never spawn.%s\n", empty,
           empty ? "  The ladder has gaps -- the mapping needs to change." : "  Every rung exists.");
    // Quantile cut points. A linear tier = difficulty*7 fails because the
    // distribution is neither uniform nor full-range, so thresholds have to come
    // from the distribution itself. Target shares descend deliberately: common at
    // the bottom, rare at the top -- but every rung must exist.
    if (n_all > 0) {
        qsort(all_diff, n_all, sizeof(float), cmpf);
        static const float SHARE[7] = { 0.25f, 0.22f, 0.20f, 0.15f, 0.10f, 0.06f, 0.02f };
        printf("\ncalibrated cut points from %d systems:\n", n_all);
        float acc = 0.0f;
        for (int t = 0; t < 6; t++) {
            acc += SHARE[t];
            int idx = (int)(acc * n_all); if (idx >= n_all) idx = n_all - 1;
            printf("  %-13s | %-13s  cut at %.4f   [%.0f%% cumulative]\n",
                   material_name((Material)t), material_name((Material)(t+1)), all_diff[idx], acc * 100.0f);
        }
    }
    return 0;
}
