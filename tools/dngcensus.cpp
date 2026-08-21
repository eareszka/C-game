// Dungeon archetype census: which of the eight spawn, in which worlds, how many.
//
//   dngcensus.exe [seed ...]        (no args: the default sample, see DEFAULT below)
//   DNGCENSUS_N=<count> dngcensus.exe    (no args: that many seeds instead of 32)
//
// Nothing about the generator guarantees a world contains all eight archetypes.
// There is no per-type quota: pick_entrance_type() (tilemap.cpp) hands back a
// pool decided by the biome under the candidate tile, and the mix that results is
// just biome area times pool membership. Several types are structurally scarce --
// oasis and pyramid are desert-only, ruins is snow and wasteland, large tree is
// forest, and stonehenge needs a 1-in-8 roll merely to JOIN the flat-grass pool
// before it can win a draw from it. So "does every type appear in every seed" is
// an open question about generated worlds, and this answers it by counting.
//
// TWO CORRECTIONS THIS APPLIES, both of which a naive histogram gets wrong:
//
//   1. A cave entrance is a MOUTH, not a cave. One mountain spends up to four
//      records on one system -- a mouth cut into the wall plus one on each storey
//      top -- and they all share cave_anchor_x/y (tilemap.cpp's stamp_mouth). On
//      seed 387 that is 713 mouths across 330 systems, so counting records
//      inflates caves by better than double. Both numbers are reported, and the
//      ranking uses systems, because a system is what a player finds.
//
//   2. Two entrances are hard-coded. tilemap_build_overworld_phase1() stamps
//      entrance 0 as a CAVE and entrance 1 as a GRAVEYARD_SM at fixed tiles in
//      every world. Counting them toward "did this type spawn" would make those
//      two types trivially always-present and answer the question falsely, so
//      the presence verdict below is taken over procedural entrances only. They
//      are still counted in the totals, which are about what a world contains.
//
// Build: `make dngcensus` from the repo root. Must RUN from the repo root too --
// tilemap_init_tile_cache() reads assets/tileset.png by relative path, and
// skipping it is not an option: it builds the cliff ink mask that
// tilemap_is_walkable() consults, which cave-mouth placement queries, so a tool
// without it silently generates a different world than the game does.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include "tilemap.h"
#include "dungeon.h"

static Tilemap g_map;

// Sized off the enum rather than typed in, so adding an archetype cannot leave
// this counting eight of nine and reporting a clean sweep.
#define NTYPE DUNGEON_ENT_COUNT

// The last slot catches a type outside the enum rather than corrupting a
// neighbour, the same guard tools/genprof.cpp keeps.
static const char* ENT_NAME[NTYPE + 1] = {
    "cave", "ruins", "graveyard_sm", "graveyard_lg", "oasis",
    "pyramid", "stonehenge", "large_tree", "catacombs", "?"
};

// Column headings, in the same order. Short enough to keep the per-seed table
// one line per world.
static const char* ENT_COL[NTYPE] = {
    "cave", "ruins", "grv_sm", "grv_lg", "oasis",
    "pyram", "stone", "tree", "catac"
};

// The ten seeds the rest of this directory measures on (tools/seed_sweep.sh),
// then a deterministic spread to fill out the sample. Fixed rather than random so
// two runs of this census are comparable, and so a surprising seed can be re-run
// on its own.
static unsigned default_seed(int i) {
    static const unsigned KNOWN[] = { 407, 463, 387, 398, 99, 5150, 1234, 7, 20260812, 555 };
    if (i < (int)(sizeof(KNOWN) / sizeof(KNOWN[0]))) return KNOWN[i];
    return 100000u + (unsigned)i * 7919u;
}

struct Row { int type; int total; int seeds_with; };

static int cmp_row(const void* a, const void* b) {
    const Row* ra = (const Row*)a;
    const Row* rb = (const Row*)b;
    if (ra->total != rb->total) return rb->total - ra->total;
    return ra->type - rb->type;
}

int main(int argc, char** argv) {
    static unsigned seeds[512];
    int nseeds = 0;
    if (argc > 1) {
        for (int i = 1; i < argc && nseeds < 512; i++)
            seeds[nseeds++] = (unsigned)strtoul(argv[i], nullptr, 10);
    } else {
        const char* n_env = getenv("DNGCENSUS_N");
        int want = n_env ? atoi(n_env) : 32;
        if (want < 1) want = 1;
        if (want > 512) want = 512;
        for (int i = 0; i < want; i++) seeds[nseeds++] = default_seed(i);
    }

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);

    int dung_tot[NTYPE + 1] = {0};    // caves counted as systems
    int ent_tot[NTYPE + 1] = {0};     // caves counted as mouths
    int seeds_with[NTYPE + 1] = {0};  // seeds where this type spawned PROCEDURALLY
    int full_seeds = 0, complete_seeds = 0;

    // Printed from the table rather than as a fixed format string: a header that
    // can drift out of step with its columns is worse than no header.
    printf("%-10s %8s", "seed", ENT_COL[0]);
    for (int t = 1; t < NTYPE; t++) printf(" %6s", ENT_COL[t]);
    printf("   %s\n", "notes");
    printf("%-10s %8s", "----", "----");
    for (int t = 1; t < NTYPE; t++) printf(" %6s", "-----");
    printf("   %s\n", "-----");

    for (int si = 0; si < nseeds; si++) {
        tilemap_build_overworld_phase1(&g_map, seeds[si]);
        tilemap_build_overworld_phase2(&g_map, seeds[si]);

        int dung[NTYPE + 1] = {0};
        int ent[NTYPE + 1] = {0};
        int proc[NTYPE + 1] = {0};   // procedural only -- the presence verdict

        // One cave system = one anchor. Sized to the whole entrance array, not to
        // the 512 tools/oreprof.cpp and tools/genprof.cpp still use: systems per
        // world is past 330 since commit 8eb12e0, and an anchor store that fills
        // up stops deduping SILENTLY and under-reports.
        static int ax[MAX_DUNGEON_ENTRANCES], ay[MAX_DUNGEON_ENTRANCES];
        int sys = 0, mouths = 0;

        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            int t = (int)e.type;
            if (t < 0 || t >= NTYPE) t = NTYPE;
            // Entrances 0 and 1 are phase 1's fixed pair, identical in every world.
            bool fixed = (i < 2);

            ent[t]++;
            if (t != (int)DUNGEON_ENT_CAVE) {
                dung[t]++;
                if (!fixed) proc[t]++;
                continue;
            }

            mouths++;
            bool known = false;
            if (e.cave_anchor_x >= 0) {
                for (int s = 0; s < sys; s++)
                    if (ax[s] == e.cave_anchor_x && ay[s] == e.cave_anchor_y) { known = true; break; }
                if (!known && sys < MAX_DUNGEON_ENTRANCES) {
                    ax[sys] = e.cave_anchor_x; ay[sys] = e.cave_anchor_y; sys++;
                }
            } else {
                sys++;   // a flat or wasteland cave stands alone and is its own system
            }
            if (!known) { dung[t]++; if (!fixed) proc[t]++; }
        }

        // Worldgen drops caves without saying so once the array is full, so a
        // saturated seed's numbers are a floor, not a count.
        bool full = g_map.num_dungeon_entrances >= MAX_DUNGEON_ENTRANCES;
        if (full) full_seeds++;

        char notes[256]; notes[0] = '\0';
        int missing = 0;
        for (int t = 0; t < NTYPE; t++) if (proc[t] == 0) missing++;
        if (missing == 0) {
            complete_seeds++;
        } else {
            size_t len = SDL_strlen(notes);
            SDL_snprintf(notes + len, sizeof(notes) - len, "<-- MISSING:");
            for (int t = 0; t < NTYPE; t++)
                if (proc[t] == 0) {
                    len = SDL_strlen(notes);
                    SDL_snprintf(notes + len, sizeof(notes) - len, " %s", ENT_NAME[t]);
                }
        }
        if (full) {
            size_t len = SDL_strlen(notes);
            SDL_snprintf(notes + len, sizeof(notes) - len, "%s<-- ARRAY FULL, caves lost",
                         len ? "  " : "");
        }

        char cavecell[24];
        SDL_snprintf(cavecell, sizeof(cavecell), "%d(%d)", sys, mouths);
        printf("%-10u %8s", seeds[si], cavecell);
        for (int t = 1; t < NTYPE; t++) printf(" %6d", dung[t]);
        printf("   %s\n", notes);

        for (int t = 0; t <= NTYPE; t++) {
            dung_tot[t] += dung[t];
            ent_tot[t]  += ent[t];
            if (proc[t] > 0) seeds_with[t]++;
        }
    }

    int grand = 0;
    for (int t = 0; t <= NTYPE; t++) grand += dung_tot[t];

    printf("\n=== across %d seeds: %d dungeons ===\n", nseeds, grand);
    printf("Caves are counted as SYSTEMS. Per-seed cave cells read systems(mouths).\n");
    printf("\"seeds\" is how many of the %d worlds grew this type WITHOUT counting\n"
           "phase 1's two fixed entrances -- see the note at the top of this file.\n\n",
           nseeds);

    Row rows[NTYPE];
    for (int t = 0; t < NTYPE; t++) { rows[t].type = t; rows[t].total = dung_tot[t]; rows[t].seeds_with = seeds_with[t]; }
    qsort(rows, NTYPE, sizeof(Row), cmp_row);

    printf("%-4s %-14s %8s %9s %8s   %s\n", "rank", "type", "total", "per seed", "share", "seeds");
    printf("%-4s %-14s %8s %9s %8s   %s\n", "----", "----", "-----", "--------", "-----", "-----");
    for (int r = 0; r < NTYPE; r++) {
        const Row& row = rows[r];
        printf("%-4d %-14s %8d %9.1f %7.1f%%   %d/%d%s\n",
               r + 1, ENT_NAME[row.type], row.total,
               (double)row.total / nseeds,
               grand ? 100.0 * row.total / grand : 0.0,
               row.seeds_with, nseeds,
               row.seeds_with == nseeds ? "" : "  <-- not in every world");
    }

    if (ent_tot[(int)DUNGEON_ENT_CAVE] != dung_tot[(int)DUNGEON_ENT_CAVE])
        printf("\ncave records: %d mouths for %d systems (%.2f per system) -- counting\n"
               "records instead would put cave at %.1f%% of all dungeons rather than %.1f%%.\n",
               ent_tot[0], dung_tot[0],
               dung_tot[0] ? (double)ent_tot[0] / dung_tot[0] : 0.0,
               (grand - dung_tot[0] + ent_tot[0])
                   ? 100.0 * ent_tot[0] / (grand - dung_tot[0] + ent_tot[0]) : 0.0,
               grand ? 100.0 * dung_tot[0] / grand : 0.0);

    if (ent_tot[NTYPE]) printf("\n%d entrances had a type outside the enum.\n", ent_tot[NTYPE]);

    printf("\n%d of %d seeds contain all %d types.%s\n", complete_seeds, nseeds, NTYPE,
           complete_seeds == nseeds ? "  Every archetype spawns in every world."
                                    : "  Some worlds are missing an archetype -- see the table.");
    if (full_seeds)
        printf("%d seed(s) hit MAX_DUNGEON_ENTRANCES (%d); their counts are a floor.\n",
               full_seeds, MAX_DUNGEON_ENTRANCES);
    return 0;
}
