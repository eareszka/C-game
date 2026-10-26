// Prop check: the overworld's props break as they should. Builds a world,
// and for one prop of each kind of blow (axe, stone, any) and the biggest
// found, strikes it with a club until it breaks, then checks that it took
// the blows its table says, that every cell of it is gone and kept gone
// (persist.h), and that the break paid exactly its drops.
//
//   propcheck.exe [seed]
//
// Exits 1 on any failure. Build: `make propcheck`, run from the repo root.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include "tilemap.h"
#include "core.h"
#include "persist.h"
#include "crafting.h"
#include "resource_node.h"
#include "props.inc"

static Tilemap g_map;
static const int KINDS = (int)(sizeof PROP_KINDS / sizeof *PROP_KINDS);

// Which prop kind a sheet id is a cell of, and the cell; false if none.
static bool kind_at(int id, int* k, int* cx, int* cy) {
    int rel = id - TILE_TOWN0_BASE;
    if (rel < 0) return false;
    int col = rel % TOWN0_SHEET_COLS, row = rel / TOWN0_SHEET_COLS;
    for (int i = 0; i < KINDS; i++) {
        const PropKind& p = PROP_KINDS[i];
        if (row >= p.row && row < p.row + p.h && col >= p.col && col < p.col + p.w * p.frames) {
            *k = i; *cx = (col - p.col) % p.w; *cy = row - p.row;
            return true;
        }
    }
    return false;
}

int main(int argc, char** argv) {
    unsigned seed = argc > 1 ? (unsigned)strtoul(argv[1], nullptr, 10) : 387u;
    SDL_SetMainReady();
    SDL_Init(SDL_INIT_VIDEO);
    persist_clear();
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);

    // one of each: by target, and the biggest
    int want[4] = { -1, -1, -1, -1 }, wx[4], wy[4], laid[KINDS] = {};
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            int k, cx, cy;
            if (!kind_at(g_map.overlay[y][x], &k, &cx, &cy)) continue;
            if (cx == 0 && cy == PROP_KINDS[k].h - 1) laid[k]++;
            int slot = PROP_KINDS[k].target == HARVEST_TREE ? 0 : PROP_KINDS[k].target == HARVEST_ROCK ? 1 : 2;
            if (want[slot] < 0) { want[slot] = k; wx[slot] = x; wy[slot] = y; }
            if (want[3] < 0 || PROP_KINDS[k].w * PROP_KINDS[k].h > PROP_KINDS[want[3]].w * PROP_KINDS[want[3]].h) {
                want[3] = k; wx[3] = x; wy[3] = y;
            }
        }
    int missing = 0;
    for (int k = 0; k < KINDS; k++) if (!laid[k]) { printf("kind %d (col %d) never laid\n", k, PROP_KINDS[k].col); missing++; }
    printf("seed %u: %d of %d kinds laid\n", seed, KINDS - missing, KINDS);

    int failed = 0;
    for (int s = 0; s < 4; s++) {
        int k = want[s];
        if (k < 0) { printf("slot %d: none found\n", s); failed++; continue; }
        const PropKind& p = PROP_KINDS[k];
        int kk, cx, cy;
        kind_at(g_map.overlay[wy[s]][wx[s]], &kk, &cx, &cy);
        const int ox = wx[s] - cx, oy = wy[s] - cy;
        Weapon club = { WEAPON_CLUB, MAT_STONE };
        int blows = 0, broke = 0, paid[2] = { 0, 0 };
        while (!broke && blows < 50) {
            HarvestResult out = {};
            world_advance(0.25f);                                   // past the one-blow window
            // a blow on the cell found, and in the same swing on its other cells
            for (int j = 0; j < p.h; j++)
                for (int i = 0; i < p.w; i++)
                    tilemap_strike_point(&g_map, (ox + i + 0.5f) * TILE_SIZE, (oy + j + 0.5f) * TILE_SIZE, club, &out);
            blows++;
            for (int h = 0; h < out.count; h++) {
                if (!out.hits[h].destroyed) continue;
                broke = 1;
                for (int d = 0; d < 2; d++)
                    if (out.hits[h].item == p.item[d] && p.item[d] >= 0) paid[d] += out.hits[h].amount;
            }
        }
        int left = 0, kept = 1;
        for (int j = 0; j < p.h; j++)
            for (int i = 0; i < p.w; i++) {
                int a, b, c;
                if (kind_at(g_map.overlay[oy + j][ox + i], &a, &b, &c) && a == k) left++;
            }
        kept = persist_tile_has(tilemap_tile_key(wx[s], wy[s]));
        int expect = (p.hp + weapon_harvest_damage(club, p.target) - 1) / weapon_harvest_damage(club, p.target);
        bool ok = broke && left == 0 && kept && blows == expect &&
                  paid[0] == (p.item[0] >= 0 ? p.n[0] : 0) && paid[1] == (p.item[1] >= 0 ? p.n[1] : 0);
        printf("%-5s kind %2d at %d,%d (%dx%d): %d blows (want %d), %d cells left, kept gone %d, paid %d+%d (want %d+%d)  %s\n",
               s == 0 ? "axe" : s == 1 ? "stone" : s == 2 ? "any" : "big", k, ox, oy, p.w, p.h, blows, expect, left, kept,
               paid[0], paid[1], p.item[0] >= 0 ? p.n[0] : 0, p.item[1] >= 0 ? p.n[1] : 0, ok ? "ok" : "FAIL");
        if (!ok) failed++;
    }
    // and regrown, the broken stay broken
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);
    for (int s = 0; s < 4; s++) {
        if (want[s] < 0) continue;
        int a, b, c;
        if (kind_at(g_map.overlay[wy[s]][wx[s]], &a, &b, &c)) { printf("slot %d: back after regrowth  FAIL\n", s); failed++; }
    }
    printf("%s\n", failed ? "FAILED" : "all ok");
    return failed || missing ? 1 : 0;
}
