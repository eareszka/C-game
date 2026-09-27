// Dungeon kind census: which of the fifteen kinds spawn, in which worlds, how
// many, and whether they came out in the order include/dungeon_kinds.h asks for.
//
//   dngcensus.exe [seed ...]        (no args: the default sample, see DEFAULT below)
//   DNGCENSUS_N=<count> dngcensus.exe    (no args: that many seeds instead of 32)
//
// A "kind" is a row of DUNGEON_KINDS: the eight non-cave archetypes and the
// seven cave materials, commonest first, each with a per-world target. Ordinary
// placement draws a site's type by how far each biome-native type still is
// from its target, and cave materials are quantile bands of cave difficulty
// sized by the same table -- so the table is a claim about generated worlds,
// and this is what checks the claim. It prints target beside measured for every
// row and flags any adjacent pair that came out the wrong way round. Whether a
// world contains ALL fifteen is a separate question, answered at the end.
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
//   2. DNG_FIXED_ENTRANCES entrances are hard-coded: phase 1 stamps a CAVE and a
//      GRAVEYARD_SM at fixed tiles in every world. Counting them toward "did
//      this kind spawn" would make those two trivially always-present and answer
//      the question falsely, so the presence verdict below is taken over
//      procedural entrances only. They are still counted in the totals, which
//      are about what a world contains.
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
#include "dungeon_kinds.h"

static Tilemap g_map;

// Sized off the table rather than typed in, so adding a kind cannot leave this
// counting fourteen of fifteen and reporting a clean sweep. The last slot
// catches a record outside the table rather than corrupting a neighbour.
#define NKIND DUNGEON_KIND_COUNT

// The ten seeds the rest of this directory measures on (tools/seed_sweep.sh),
// then a deterministic spread to fill out the sample. Fixed rather than random so
// two runs of this census are comparable, and so a surprising seed can be re-run
// on its own.
static unsigned default_seed(int i) {
    static const unsigned KNOWN[] = { 407, 463, 387, 398, 99, 5150, 1234, 7, 20260812, 555 };
    if (i < (int)(sizeof(KNOWN) / sizeof(KNOWN[0]))) return KNOWN[i];
    return 100000u + (unsigned)i * 7919u;
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

    int dung_tot[NKIND + 1] = {0};    // caves counted as systems
    int cave_sys_tot = 0, cave_mouth_tot = 0;
    int seeds_with[NKIND + 1] = {0};  // seeds where this kind spawned PROCEDURALLY
    int full_seeds = 0, complete_seeds = 0;

    // Column headings straight from the table, so a header cannot drift out of
    // step with its columns. Seven characters keeps 15 columns on one line.
    char label[NKIND][24];
    for (int k = 0; k < NKIND; k++) dungeon_kind_label(k, label[k], sizeof(label[k]));

    printf("%-10s", "seed");
    for (int k = 0; k < NKIND; k++) printf(" %7.7s", DUNGEON_KINDS[k].name);
    printf("   %s\n", "notes");
    printf("%-10s", "----");
    for (int k = 0; k < NKIND; k++) printf(" %7s", "-------");
    printf("   %s\n", "-----");

    for (int si = 0; si < nseeds; si++) {
        tilemap_build_overworld_phase1(&g_map, seeds[si]);
        tilemap_build_overworld_phase2(&g_map, seeds[si]);

        int dung[NKIND + 1] = {0};
        int proc[NKIND + 1] = {0};   // procedural only -- the presence verdict

        // One cave system = one anchor. Sized to the whole entrance array: an
        // anchor store that fills up stops deduping SILENTLY and under-reports.
        static int ax[MAX_DUNGEON_ENTRANCES], ay[MAX_DUNGEON_ENTRANCES];
        int sys = 0, mouths = 0;

        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            int k = dungeon_kind_of(&e);
            if (k < 0 || k >= NKIND) k = NKIND;
            bool fixed = (i < DNG_FIXED_ENTRANCES);

            if (e.type != DUNGEON_ENT_CAVE) {
                dung[k]++;
                if (!fixed) proc[k]++;
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
                sys++;   // a cave with no landform stands alone and is its own system
            }
            if (!known) { dung[k]++; if (!fixed) proc[k]++; }
        }

        // Worldgen drops caves without saying so once the array is full, so a
        // saturated seed's numbers are a floor, not a count.
        bool full = g_map.num_dungeon_entrances >= MAX_DUNGEON_ENTRANCES;
        if (full) full_seeds++;

        char notes[512]; notes[0] = '\0';
        int missing = 0;
        for (int k = 0; k < NKIND; k++) if (proc[k] == 0) missing++;
        if (missing == 0) {
            complete_seeds++;
        } else {
            size_t len = SDL_strlen(notes);
            SDL_snprintf(notes + len, sizeof(notes) - len, "<-- MISSING:");
            for (int k = 0; k < NKIND; k++)
                if (proc[k] == 0) {
                    len = SDL_strlen(notes);
                    SDL_snprintf(notes + len, sizeof(notes) - len, " %s", label[k]);
                }
        }
        if (full) {
            size_t len = SDL_strlen(notes);
            SDL_snprintf(notes + len, sizeof(notes) - len, "%s<-- ARRAY FULL, caves lost",
                         len ? "  " : "");
        }

        printf("%-10u", seeds[si]);
        for (int k = 0; k < NKIND; k++) printf(" %7d", dung[k]);
        printf("   %s\n", notes);

        for (int k = 0; k <= NKIND; k++) {
            dung_tot[k] += dung[k];
            if (proc[k] > 0) seeds_with[k]++;
        }
        cave_sys_tot += sys; cave_mouth_tot += mouths;
    }

    int grand = 0;
    for (int k = 0; k <= NKIND; k++) grand += dung_tot[k];

    printf("\n=== across %d seeds: %d dungeons ===\n", nseeds, grand);
    printf("Caves are counted as SYSTEMS: %d systems (%.1f per seed) across %d mouths.\n",
           cave_sys_tot, (double)cave_sys_tot / nseeds, cave_mouth_tot);
    printf("\"seeds\" is how many of the %d worlds grew this kind WITHOUT counting\n"
           "phase 1's fixed entrances -- see the note at the top of this file.\n\n",
           nseeds);

    // In TABLE order, not sorted: the question is whether the world agrees with
    // the table, and a sorted list would hide exactly the rows that disagree.
    printf("%-4s %-18s %7s %9s %8s   %s\n", "want", "kind", "target", "per seed", "share", "seeds");
    printf("%-4s %-18s %7s %9s %8s   %s\n", "----", "----", "------", "--------", "-----", "-----");
    int broken = 0;
    for (int k = 0; k < NKIND; k++) {
        printf("%-4d %-18s %7d %9.1f %7.1f%%   %d/%d%s\n",
               k + 1, label[k], DUNGEON_KINDS[k].target,
               (double)dung_tot[k] / nseeds,
               grand ? 100.0 * dung_tot[k] / grand : 0.0,
               seeds_with[k], nseeds,
               seeds_with[k] == nseeds ? "" : "  <-- not in every world");
        if (k + 1 < NKIND && dung_tot[k] < dung_tot[k + 1]) broken++;
    }
    for (int k = 0; k + 1 < NKIND; k++)
        if (dung_tot[k] < dung_tot[k + 1])
            printf("ORDER BROKEN: %s (%.1f) outnumbers %s (%.1f)\n",
                   label[k + 1], (double)dung_tot[k + 1] / nseeds,
                   label[k],     (double)dung_tot[k] / nseeds);
    if (!broken) printf("\nEvery adjacent pair is in table order.\n");

    if (dung_tot[NKIND]) printf("\n%d entrances had a kind outside the table.\n", dung_tot[NKIND]);

    printf("\n%d of %d seeds contain all %d kinds.%s\n", complete_seeds, nseeds, NKIND,
           complete_seeds == nseeds ? "  Every kind spawns in every world."
                                    : "  Some worlds are missing a kind -- see the table.");
    if (full_seeds)
        printf("%d seed(s) hit MAX_DUNGEON_ENTRANCES (%d); their counts are a floor.\n",
               full_seeds, MAX_DUNGEON_ENTRANCES);
    return broken ? 2 : (complete_seeds == nseeds ? 0 : 1);
}
