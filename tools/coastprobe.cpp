// Does the coastal town actually stand out over the water?
//
//   coastprobe.exe [seed ...]        (default: a spread of twenty)
//
// Town 1 is meant to reach COAST_REACH tiles past the waterline: the shore
// search puts its landward edge where the coast comes furthest inland across
// its 156 rows, and the whole footprint is then pushed that far out to sea. So
// the number that has to be exact is the deepest reach, not the average one.
// Along the rest of the edge the town reaches a little less, as the coastline
// wanders, and what must never happen is a line reaching nothing at all -- a
// town that has quietly pulled back onto dry land.
//
// The finished world cannot be asked. The town paves what it covers: its whole
// footprint is stamped with the blueprint placeholder, so once worldgen is done
// there is nothing left in the tile grid saying where the waterline used to be,
// and the sea and the town meet in a flat edge whether the town is thirty tiles
// out or none. A screenshot says even less.
//
// The tracing hook answers it. tilemap.cpp calls GEN_STAGE at every pass
// boundary, which compiles to gen_trace_stage() when GEN_TRACE is defined and
// to nothing otherwise, so this takes a copy of the world the moment before the
// towns are stamped and measures the finished town against that. Nothing in the
// shipping build changes.
//
//   make coastprobe
//
// Exits non-zero if any seed fails, so it can gate a build.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "tilemap.h"
#include "towns.h"      // TOWN_W/H

// Must match COAST_REACH in the town 1 block of src/tilemap.cpp.
static const int COAST_REACH = 30;

static Tilemap g_map;

// The world as it stood before the towns went on. Only the tile grid is needed,
// but all of it is needed: where the town lands is not known until afterwards.
static int  g_pre[MAP_HEIGHT][MAP_WIDTH];
static bool g_have_pre = false;

void gen_trace_stage(const Tilemap* map, const char* stage)
{
    if (g_have_pre || strcmp(stage, "before Towns 1-3") != 0) return;
    memcpy(g_pre, map->tiles, sizeof(g_pre));
    g_have_pre = true;
}

// What the shore search made of this world. The measurements below say whether
// the town ended up standing over the water; this says why it did not, which is
// a question the finished grid cannot answer -- by then the search is over and
// the fallback has already put the town somewhere inland.
static ShoreTally g_tally;

void gen_trace_shore(const ShoreTally* tally) { g_tally = *tally; }

// The same families the town search's own is_cliff covers -- see the lambda
// above the town block in src/tilemap.cpp.
static bool is_cliff(int t)
{
    return (t >= TILE_CLIFF        && t <= TILE_CLIFF_5)
        || (t >= TILE_CLIFF_EDGE_1 && t <= TILE_CLIFF_EDGE_5)
        || (t >= TILE_CLIFF_SNOW_1 && t <= TILE_CLIFF_CORNER_NE_5);
}

// Which edge the ocean floods, read off the world rather than assumed: 0=W,
// 1=E, 2=N, 3=S, the same numbering the Ocean pass uses.
static int ocean_side()
{
    long n[4] = {0,0,0,0};
    for (int y = 0; y < MAP_HEIGHT; y++) {
        if (g_pre[y][0]             == TILE_WATER) n[0]++;
        if (g_pre[y][MAP_WIDTH-1]   == TILE_WATER) n[1]++;
    }
    for (int x = 0; x < MAP_WIDTH; x++) {
        if (g_pre[0][x]             == TILE_WATER) n[2]++;
        if (g_pre[MAP_HEIGHT-1][x]  == TILE_WATER) n[3]++;
    }
    int best = 0;
    for (int i = 1; i < 4; i++) if (n[i] > n[best]) best = i;
    return best;
}

// One line across the town's seaward edge: how many of the town's own tiles on
// that line were sea before it was stamped, counted inward from the seaward
// edge. Deliberately local to the footprint. Measuring in from the map edge
// instead would be measuring the whole ocean band, and would report a failure
// here every time something else in the world happened to sit out in the water.
//
// `stopper` takes the tile that ended the run, which is the thing worth seeing
// when a line reaches no water at all.
static int reach_on_line(int side, int tx, int ty, int i, int* stopper)
{
    int x, y, sx, sy;
    switch (side) {
        case 0:  x = tx,              y = ty + i, sx =  1, sy =  0; break;
        case 1:  x = tx + TOWN_W - 1, y = ty + i, sx = -1, sy =  0; break;
        case 2:  x = tx + i,          y = ty,     sx =  0, sy =  1; break;
        default: x = tx + i, y = ty + TOWN_H - 1, sx =  0, sy = -1; break;
    }
    int span = (side <= 1) ? TOWN_W : TOWN_H;
    for (int n = 0; n < span; n++, x += sx, y += sy)
        if (g_pre[y][x] != TILE_WATER) { *stopper = g_pre[y][x]; return n; }
    return span;
}

// True for a footprint tile that the shift newly covered -- the seaward strip,
// where sea is expected. Everything else is the town's landward part, where it
// is not.
static bool in_sea_strip(int side, int dx, int dy)
{
    switch (side) {
        case 0:  return dx <  COAST_REACH;
        case 1:  return dx >= TOWN_W - COAST_REACH;
        case 2:  return dy <  COAST_REACH;
        default: return dy >= TOWN_H - COAST_REACH;
    }
}

static bool check(unsigned seed)
{
    g_have_pre = false;
    g_tally = ShoreTally{};
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);

    if (!g_have_pre) {
        printf("seed %-6u FAIL  the trace hook never fired -- built without -DGEN_TRACE?\n", seed);
        return false;
    }
    // Every town, not just the coastal one. Town 0 is stamped at the map centre
    // in phase 1 and town 2 relaxes its spacing rather than give up, so neither
    // is expected to go missing -- which is exactly why nothing was watching
    // them, and why a silent -1 here would have gone unnoticed.
    bool all_there = true;
    for (int t = 0; t < 3; t++)
        if (g_map.towns[t].x < 0) {
            printf("seed %-6u FAIL  town %d was not placed at all\n", seed, t);
            all_there = false;
        }
    if (!all_there) return false;

    const int c0x = MAP_WIDTH / 2 - TOWN_W / 2, c0y = MAP_HEIGHT / 2 - TOWN_H / 2;
    if (g_map.towns[0].x != c0x || g_map.towns[0].y != c0y) {
        printf("seed %-6u FAIL  town 0 is at (%d,%d), not the map centre (%d,%d)\n",
               seed, g_map.towns[0].x, g_map.towns[0].y, c0x, c0y);
        return false;
    }

    // Two 156x156 footprints that overlap are one misshapen town, whichever of
    // them was meant to be where.
    for (int a = 0; a < 3; a++)
        for (int b = a + 1; b < 3; b++) {
            int adx = g_map.towns[a].x - g_map.towns[b].x;
            int ady = g_map.towns[a].y - g_map.towns[b].y;
            if (adx > -TOWN_W && adx < TOWN_W && ady > -TOWN_H && ady < TOWN_H) {
                printf("seed %-6u FAIL  towns %d and %d overlap: (%d,%d) and (%d,%d)\n",
                       seed, a, b, g_map.towns[a].x, g_map.towns[a].y,
                       g_map.towns[b].x, g_map.towns[b].y);
                return false;
            }
        }

    int tx = g_map.towns[1].x, ty = g_map.towns[1].y;

    int side  = ocean_side();
    int lines = (side <= 1) ? TOWN_H : TOWN_W;
    int lo = 1 << 30, hi = -(1 << 30), dry = 0, dry_tile = -1, dry_n = 0;
    for (int i = 0; i < lines; i++) {
        int stop = -1;
        int r = reach_on_line(side, tx, ty, i, &stop);
        if (r < lo) lo = r;
        if (r > hi) hi = r;
        if (r <= 0) {
            dry++;
            // Whichever ground turns up most often where the sea should be.
            if (stop == dry_tile) dry_n++;
            else if (--dry_n < 0) { dry_tile = stop; dry_n = 0; }
        }
    }

    int wet_inland = 0, rivers = 0, cliffs = 0;
    for (int dy = 0; dy < TOWN_H; dy++)
        for (int dx = 0; dx < TOWN_W; dx++) {
            int t = g_pre[ty+dy][tx+dx];
            if (t == TILE_WATER && !in_sea_strip(side, dx, dy)) wet_inland++;
            if (t == TILE_RIVER) rivers++;
            if (is_cliff(t))     cliffs++;
        }

    // Where the town ended up is the requirement, and it is the whole of it.
    // A footprint with cliff or river under it is worth saying out loud, but a
    // town that levelled some rock to stand on the coast is in the right place;
    // one sitting inland in a meadow is not. The shore search only settles for
    // rough ground when no clean window exists -- see its relaxed path.
    bool ok = (hi == COAST_REACH) && (dry == 0) && !wet_inland;
    printf("seed %-6u ocean %c  town1 (%4d,%4d)  reach %3d-%3d  %s\n",
           seed, "WENS"[side], tx, ty, lo, hi, ok ? "ok" : "FAIL");
    if (hi != COAST_REACH)
        printf("             deepest reach is %d, expected exactly %d\n", hi, COAST_REACH);
    if (dry)
        printf("             %d of %d lines reach no water at all (mostly tile %d)\n",
               dry, lines, dry_tile);
    if (wet_inland)
        printf("             %d sea tiles inside the town's landward part\n", wet_inland);
    if (g_tally.relaxed_cost >= 0)
        printf("             note: no clean window on this coast -- took the least bad "
               "of %d, covering %d river and %d cliff tiles\n",
               g_tally.coastal, rivers, cliffs);
    else if (rivers || cliffs)
        printf("             note: %d river and %d cliff tiles under the footprint\n",
               rivers, cliffs);
    if (!ok)
        printf("             shore search: %d windows -> %d no coast, %d off-map, "
               "%d near town 0, %d unclean, %d kept, %d coastal\n",
               g_tally.windows, g_tally.no_coast, g_tally.bounds, g_tally.near_town0,
               g_tally.unclean, g_tally.kept, g_tally.coastal);
    return ok;
}

int main(int argc, char** argv)
{
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);

    unsigned spread[20];
    for (int i = 0; i < 20; i++) spread[i] = 1u + (unsigned)i * 97u;

    int n = (argc > 1) ? argc - 1 : 20;
    int failed = 0;
    for (int i = 0; i < n; i++) {
        unsigned seed = (argc > 1) ? (unsigned)strtoul(argv[i+1], nullptr, 10) : spread[i];
        if (!check(seed)) failed++;
    }
    printf("\n%d of %d worlds ok\n", n - failed, n);
    return failed ? 1 : 0;
}
