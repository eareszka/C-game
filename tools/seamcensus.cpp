// Seam census: is the join where the world wraps as invisible as any other
// line of the map?
//
//   seamcensus.exe [seed ...]        (no args: 12 seeds covering all four ocean sides)
//
// The world wraps on one axis (see WrapAxis in include/tilemap.h). Along that
// axis every pair of adjacent lines of tiles -- column x and column x+1 for an
// east-west wrap -- differs from each other a little: a biome edge crosses,
// a cliff steps, a track bends. The seam is the pair (last line, first line).
// If the world is periodic it differs by the same small amounts; if anything
// in worldgen still treats the edge as an edge, the seam shows up as an
// outlier -- a cut in the terrain, a track that stops dead, a river that ends.
//
// For each measure this prints the seam's mismatch count and where it ranks
// among all the interior pairs: "rank 97%" means 97% of interior pairs differ
// by less. A seam that ranks above RANK_FLAG is marked.
//
// Build: `make seamcensus`; run from the repo root (it reads assets/tileset.png,
// for the same reason dngcensus does).
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <algorithm>
#include "tilemap.h"

static Tilemap g_map;

static const double RANK_FLAG = 0.99;

enum { M_TILE, M_ELEV, M_ROUTE, M_LIQUID, M_OVERLAY, M_COUNT };
static const char* M_NAME[M_COUNT] = { "tile", "elev", "route", "liquid", "overlay" };

static bool liquid(int t) {
    return t == TILE_WATER || t == TILE_RIVER || t == TILE_POND || t == TILE_LAVA;
}

static bool structure(int t) {
    return t >= TILE_TOWN0_BASE || t == TILE_BLUEPRINT ||
           t == TILE_VILLAGE_PLACEHOLDER || t == TILE_CASTLE_PLACEHOLDER;
}

// Mismatches between line a and line b across the whole of the other axis.
static void compare(bool wx, int a, int b, int* out) {
    for (int m = 0; m < M_COUNT; m++) out[m] = 0;
    int n = wx ? MAP_HEIGHT : MAP_WIDTH;
    for (int i = 0; i < n; i++) {
        int ax = wx ? a : i, ay = wx ? i : a;
        int bx = wx ? b : i, by = wx ? i : b;
        int ta = g_map.tiles[ay][ax], tb = g_map.tiles[by][bx];
        // Structures are left out of the tile measure. A footprint may not
        // straddle the seam but may end on it, and its straight edge there is
        // a town wall, not a cut in the terrain -- one town lying against the
        // seam is 156 mismatches and ranks at 100% of interior pairs.
        if (ta != tb && !structure(ta) && !structure(tb)) out[M_TILE]++;
        if (tilemap_cliff_elev_at(ax, ay) != tilemap_cliff_elev_at(bx, by)) out[M_ELEV]++;
        if ((g_map.route[ay][ax] != 0) != (g_map.route[by][bx] != 0)) out[M_ROUTE]++;
        if (liquid(ta) != liquid(tb)) out[M_LIQUID]++;
        if ((g_map.overlay[ay][ax] != 0) != (g_map.overlay[by][bx] != 0)) out[M_OVERLAY]++;
    }
}

int main(int argc, char** argv) {
    std::vector<unsigned> seeds;
    for (int i = 1; i < argc; i++) seeds.push_back((unsigned)strtoul(argv[i], nullptr, 10));
    if (seeds.empty()) seeds = { 407, 463, 387, 398, 99, 5150, 1234, 7, 555, 630, 718, 747 };

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);

    static const char* SIDE = "WENS";
    int flagged_seeds = 0;
    printf("%-8s %-5s", "seed", "wrap");
    for (int m = 0; m < M_COUNT; m++) printf("  %-18s", M_NAME[m]);
    printf("\n");

    for (unsigned seed : seeds) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        bool wx = g_map.wrap_axis == WRAP_X;
        int L = wx ? MAP_WIDTH : MAP_HEIGHT;

        std::vector<int> interior[M_COUNT];
        int c[M_COUNT];
        for (int k = 0; k + 1 < L; k++) {
            compare(wx, k, k + 1, c);
            for (int m = 0; m < M_COUNT; m++) interior[m].push_back(c[m]);
        }
        int seam[M_COUNT];
        compare(wx, L - 1, 0, seam);

        bool flag = false;
        printf("%-8u %c/%-3s", seed, SIDE[g_map.ocean_side & 3], wx ? "E-W" : "N-S");
        for (int m = 0; m < M_COUNT; m++) {
            int below = 0;
            for (int v : interior[m]) if (v < seam[m]) below++;
            double rank = (double)below / interior[m].size();
            std::sort(interior[m].begin(), interior[m].end());
            int med = interior[m][interior[m].size() / 2];
            bool bad = rank > RANK_FLAG;
            if (bad) flag = true;
            char cell[32];
            snprintf(cell, sizeof cell, "%d (med %d) %3.0f%%%s", seam[m], med, rank * 100.0, bad ? "!" : "");
            printf("  %-18s", cell);
        }
        printf("\n");
        // Where along the seam the tiles disagree, as runs, so a flagged seed
        // can be looked at: shot.exe with a window over the run.
        if (flag) {
            printf("         tile mismatches along the seam:");
            int n = wx ? MAP_HEIGHT : MAP_WIDTH, run0 = -1;
            for (int i = 0; i <= n; i++) {
                bool diff = false;
                if (i < n) {
                    int ax = wx ? L - 1 : i, ay = wx ? i : L - 1;
                    int bx = wx ? 0 : i,     by = wx ? i : 0;
                    diff = g_map.tiles[ay][ax] != g_map.tiles[by][bx];
                }
                if (diff && run0 < 0) run0 = i;
                if (!diff && run0 >= 0) { if (i - run0 >= 4) printf(" %d-%d", run0, i - 1); run0 = -1; }
            }
            printf("\n");
            flagged_seeds++;
        }
    }
    printf("\n%d of %d seeds have a seam measure above the %.0f%% rank of interior pairs.\n",
           flagged_seeds, (int)seeds.size(), RANK_FLAG * 100.0);
    return flagged_seeds ? 1 : 0;
}
