// Stair audit: does every dungeon have exactly the ways out it is supposed to?
//
//   dngportals.exe [seeds_per_form] [worlds]   (defaults 24 and 4)
//
// A dungeon has one entry and, if it is partnered, one exit. A cave system has
// one way out per mouth. Nothing checked that until a catacombs turned up with
// four sets of stairs in it, each of which put the player back outside: the
// pair had been re-sited after generation and the old positions were stamped
// back as stairs on top of the new ones, so every partnered dungeon in the game
// had two entries and two exits.
//
// That went unseen because the three ways a dungeon gets wired to the overworld
// lived inline in main.cpp's input handler, where nothing headless could run
// them. They are dungeon_bind_solo/pair/cave_mouths in src/dungeon.cpp now, and
// this tool calls those -- the shipped path, not a copy of it. A checker with
// its own idea of how binding works is a checker that passes while the game is
// broken.
//
// THE INVARIANT, checked per archetype per form per seed:
//
//   1. exactly one DNG_ENTRY tile on the map
//   2. DNG_EXIT tile count == num_portals - 1
//   3. the set of stair tiles equals the set of portal tiles, BOTH ways -- no
//      stair tile missing from the array (the catacombs bug), and no portal
//      pointing at a tile that is not stairs
//   4. every portal tile reachable from portal 0 over non-wall tiles: a way out
//      you cannot walk to is not a way out
//   5. every portal carries a destination (ow_x >= 0), or standing on it falls
//      back to whatever main.cpp last put in its loop-local pair
//
// THE SECOND SWEEP runs over real worlds rather than synthetic forms, and asks
// what dungeon_wiring_for() answers for every entrance in them:
//
//   6. every mouth of a cave system resolves to the SAME seed, difficulty and
//      archetype -- one mountain, one cave. This is the one that broke: the
//      seed rules were four last-writer-wins blocks in main.cpp and the partner
//      rule beat the cave anchor, so 13.4% of multi-mouth systems hid two caves.
//   7. both ends of a partnered pair resolve to the same three. The seed was
//      always made order-independent; difficulty never was, so one shared cave
//      was Bronze from one mouth and Kharvite from the other.
//   8. no entrance is both a multi-mouth cave mouth and partnered -- a link
//      nothing can honour should not be sitting in the data at all.
//
// It also reports how many pairs straddle an ore boundary. That is not a
// failure: it is the size of the damage rule 7 used to do, read straight off
// the entrance records, and it stays printed so the fix cannot quietly stop
// mattering.
//
// Exits non-zero if any check fails, so it can be run as a gate rather than
// read. Build: `make dngportals` from the repo root, and RUN from there too --
// tilemap_init_tile_cache() reads assets/tileset.png by relative path.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include "tilemap.h"
#include "dungeon.h"

static DungeonMap g_dmap;
static uint8_t    g_seen[DMAP_H][DMAP_W];

#define NTYPE DUNGEON_ENT_COUNT

// Sized off the enum rather than typed in, the same guard tools/dngcensus.cpp
// keeps: adding an archetype must not leave this auditing eight of nine.
static const char* ENT_NAME[NTYPE] = {
    "cave", "ruins", "graveyard_sm", "graveyard_lg", "oasis",
    "pyramid", "stonehenge", "large_tree", "catacombs"
};

// A form is one of the three shapes a bound dungeon can take. mouths > 0 means
// the cave-system case and is only ever asked of CAVE.
struct Form { const char* name; int mouths; };

// The seeds the rest of tools/ measures on, so a surprise here can be re-run
// against dngcensus and shot on the very same world.
static const unsigned WORLD_SEED[] = { 407, 463, 387, 398, 99, 5150, 1234, 7, 20260812, 555 };

struct Fail { int type; Form form; unsigned seed; float angle; const char* what; int a, b; };
static std::vector<Fail> g_fails;

static void fail(int type, Form form, unsigned seed, float angle,
                 const char* what, int a, int b) {
    g_fails.push_back({ type, form, seed, angle, what, a, b });
}

// 4-connected flood from (sx,sy) over anything that is not wall. The player
// walks floors, entries and exits alike, so the reachable set is every non-wall
// tile joined to the start.
static void flood(const DungeonMap* d, int sx, int sy) {
    memset(g_seen, 0, sizeof(g_seen));
    if (sx < 0 || sy < 0 || sx >= DMAP_W || sy >= DMAP_H) return;
    if (d->tiles[sy][sx] == DNG_WALL) return;
    std::vector<std::pair<int,int>> st;
    st.push_back({sx, sy});
    g_seen[sy][sx] = 1;
    const int dx[4] = {1,-1,0,0}, dy[4] = {0,0,1,-1};
    while (!st.empty()) {
        auto p = st.back(); st.pop_back();
        for (int k = 0; k < 4; k++) {
            int nx = p.first + dx[k], ny = p.second + dy[k];
            if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H) continue;
            if (g_seen[ny][nx] || d->tiles[ny][nx] == DNG_WALL) continue;
            g_seen[ny][nx] = 1;
            st.push_back({nx, ny});
        }
    }
}

// One generated-and-bound dungeon, checked against all five rules. Returns the
// number of rules it broke.
static int audit(int type, Form form, unsigned seed, float angle) {
    const DungeonMap* d = &g_dmap;
    int before = (int)g_fails.size();

    int n_entry = 0, n_exit = 0;
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            if (d->tiles[y][x] == DNG_ENTRY) n_entry++;
            else if (d->tiles[y][x] == DNG_EXIT) n_exit++;
        }

    if (n_entry != 1)
        fail(type, form, seed, angle, "entry tiles", n_entry, 1);
    if (n_exit != d->num_portals - 1)
        fail(type, form, seed, angle, "exit tiles", n_exit, d->num_portals - 1);

    // Rule 3, portal -> tile. Portal 0 must be the entry, the rest exits.
    for (int p = 0; p < d->num_portals; p++) {
        int tx = d->portals[p].tx, ty = d->portals[p].ty;
        if (tx < 0 || ty < 0 || tx >= DMAP_W || ty >= DMAP_H) {
            fail(type, form, seed, angle, "portal off map", p, 0);
            continue;
        }
        uint8_t want = p ? DNG_EXIT : DNG_ENTRY;
        if (d->tiles[ty][tx] != want)
            fail(type, form, seed, angle, "portal not on its stair tile", p,
                 (int)d->tiles[ty][tx]);
        if (d->portals[p].ow_x < 0)
            fail(type, form, seed, angle, "portal has no destination", p, 0);
    }

    // Rule 3, tile -> portal. This is the direction the catacombs bug broke:
    // stairs on the map that no portal knows about.
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            uint8_t t = d->tiles[y][x];
            if (t != DNG_ENTRY && t != DNG_EXIT) continue;
            bool found = false;
            for (int p = 0; p < d->num_portals && !found; p++)
                found = (d->portals[p].tx == x && d->portals[p].ty == y);
            if (!found)
                fail(type, form, seed, angle, "stair tile in no portal", x, y);
        }

    if (d->num_portals > 0) {
        flood(d, d->portals[0].tx, d->portals[0].ty);
        for (int p = 1; p < d->num_portals; p++) {
            int tx = d->portals[p].tx, ty = d->portals[p].ty;
            if (tx < 0 || ty < 0 || tx >= DMAP_W || ty >= DMAP_H) continue;
            if (!g_seen[ty][tx])
                fail(type, form, seed, angle, "portal unreachable from entry", p, 0);
        }
    }

    return (int)g_fails.size() - before;
}

int main(int argc, char** argv) {
    int nseed = (argc > 1) ? atoi(argv[1]) : 24;
    if (nseed < 1)   nseed = 1;
    if (nseed > 512) nseed = 512;
    int nworld = (argc > 2) ? atoi(argv[2]) : 4;
    if (nworld < 0)  nworld = 0;
    if (nworld > (int)(sizeof(WORLD_SEED)/sizeof(WORLD_SEED[0])))
        nworld = (int)(sizeof(WORLD_SEED)/sizeof(WORLD_SEED[0]));

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 2; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    // Cheap here and not optional: draw_cave_wall() reads the generated tileset
    // region out of this cache, and a cave generated without it is not the cave
    // the game generates.
    tilemap_init_tile_cache(ren);

    // Solo and partnered are asked of every archetype. The mouth counts are
    // asked only of CAVE, which is the only thing that grows more than two ways
    // out -- see want_portals in dungeon_generate().
    static const Form FORMS[] = {
        { "solo",      0 },
        { "paired",    0 },
        { "2 mouths",  2 },
        { "3 mouths",  3 },
        { "4 mouths",  4 },
        { "5 mouths",  5 },
        { "6 mouths",  6 },
    };
    const int NFORM = (int)(sizeof(FORMS) / sizeof(FORMS[0]));

    printf("%-13s %-9s %7s %7s   %s\n", "archetype", "form", "cases", "portals", "verdict");
    printf("%-13s %-9s %7s %7s   %s\n", "---------", "----", "-----", "-------", "-------");

    int total_cases = 0;
    for (int t = 0; t < NTYPE; t++) {
        for (int f = 0; f < NFORM; f++) {
            Form form = FORMS[f];
            if (form.mouths > 0 && t != (int)DUNGEON_ENT_CAVE) continue;
            // A cave's own solo/paired rows are the single-mouth case: one mouth
            // in a hillside is bound exactly like any other dungeon.
            int bad = 0, portals_seen = -1;

            for (int si = 0; si < nseed; si++) {
                unsigned seed = 0xD006u + (unsigned)si * 2654435761u;
                // Eight bearings, so orientation is exercised on every axis
                // rather than on whichever one seed 0 happened to pick.
                float angle = (float)(si % 8) * 0.7853982f;

                g_dmap.want_portals = (form.mouths > 0) ? form.mouths : 2;
                if (form.mouths > 0) {
                    // Mouths spread around the mountain's centroid, the shape
                    // main.cpp hands the carve.
                    for (int m = 0; m < form.mouths; m++) {
                        float a = (float)m * 6.2831853f / (float)form.mouths;
                        g_dmap.want_ox[m] = (int)(cosf(a) * 6.0f);
                        g_dmap.want_oy[m] = (int)(sinf(a) * 6.0f);
                    }
                }

                dungeon_generate(&g_dmap, (DungeonEntranceType)t, 0.5f, seed);

                if (form.mouths > 0) {
                    int ow_x[DMAP_MAX_PORTALS], ow_y[DMAP_MAX_PORTALS];
                    for (int m = 0; m < form.mouths; m++) { ow_x[m] = 100 + m * 10; ow_y[m] = 200 + m * 10; }
                    dungeon_bind_cave_mouths(&g_dmap, ow_x, ow_y, form.mouths);
                } else if (f == 1) {
                    dungeon_bind_pair(&g_dmap, angle, 100, 200, 300, 400);
                } else {
                    dungeon_bind_solo(&g_dmap, 100, 200);
                }

                if (portals_seen < 0) portals_seen = g_dmap.num_portals;
                else if (portals_seen != g_dmap.num_portals) portals_seen = -2;

                bad += audit(t, form, seed, angle);
                total_cases++;
            }

            char pcol[16];
            if (portals_seen == -2) snprintf(pcol, sizeof(pcol), "varies");
            else                    snprintf(pcol, sizeof(pcol), "%d", portals_seen);
            printf("%-13s %-9s %7d %7s   %s\n", ENT_NAME[t], form.name, nseed, pcol,
                   bad ? "FAIL" : "ok");
        }
    }

    printf("\n%d cases, %d failures\n", total_cases, (int)g_fails.size());

    // ── Real worlds ───────────────────────────────────────────────────────
    //
    // Most of this needs no interior at all: the wiring is a question about
    // entrance records, so every entrance of every world gets asked rather than
    // a sample of them. Only the stair audit needs a generated dungeon, and
    // that part is sampled -- the synthetic sweep above already covers the
    // shapes, and what is being checked here is the wiring that reaches them.
    if (nworld > 0) {
        static Tilemap map;
        long systems = 0, split_systems = 0;
        long pairs = 0, split_pairs = 0, ore_boundary = 0, both = 0, sampled = 0;

        printf("\n%-10s %9s %8s %6s %8s %10s   %s\n", "world", "entrances",
               "systems", "pairs", "audited", "ore-split", "verdict");
        printf("%-10s %9s %8s %6s %8s %10s   %s\n", "-----", "---------",
               "-------", "-----", "-------", "---------", "-------");

        for (int wi = 0; wi < nworld; wi++) {
            unsigned wseed = WORLD_SEED[wi];
            tilemap_build_overworld_phase1(&map, wseed);
            tilemap_build_overworld_phase2(&map, wseed);
            int n = map.num_dungeon_entrances;
            int before = (int)g_fails.size();
            long w_ore = 0;
            Form wf = { "world", 0 };

            for (int i = 0; i < n; i++) {
                const DungeonEntrance* e = &map.dungeon_entrances[i];
                DungeonWiring w = dungeon_wiring_for(&map, wseed, i);

                if (w.n_mouths >= 2 && e->partner_idx >= 0) {
                    both++;
                    fail((int)e->type, wf, wseed, 0.0f,
                         "cave system also partnered", i, e->partner_idx);
                }

                // Rule 6, asked once per system -- from its lowest-indexed
                // mouth, which is the one dungeon_wiring_for numbers 0, so a
                // four-mouth mountain is reported once and not four times.
                if (w.n_mouths >= 2 && w.my_mouth == 0) {
                    systems++;
                    bool agree = true;
                    for (int j = 0; j < n; j++) {
                        const DungeonEntrance* m = &map.dungeon_entrances[j];
                        if (m->cave_anchor_x != e->cave_anchor_x ||
                            m->cave_anchor_y != e->cave_anchor_y) continue;
                        DungeonWiring wj = dungeon_wiring_for(&map, wseed, j);
                        if (wj.seed != w.seed || wj.difficulty != w.difficulty ||
                            wj.type != w.type) agree = false;
                    }
                    if (!agree) {
                        split_systems++;
                        fail((int)e->type, wf, wseed, 0.0f,
                             "cave system mouths disagree",
                             e->cave_anchor_x, e->cave_anchor_y);
                    }
                }

                // Rule 7, asked once per pair -- from the lower of the two.
                if (e->partner_idx > i) {
                    pairs++;
                    const DungeonEntrance* p = &map.dungeon_entrances[e->partner_idx];
                    DungeonWiring wp = dungeon_wiring_for(&map, wseed, e->partner_idx);
                    if (wp.seed != w.seed || wp.difficulty != w.difficulty ||
                        wp.type != w.type) {
                        split_pairs++;
                        fail((int)e->type, wf, wseed, 0.0f,
                             "pair ends disagree", i, e->partner_idx);
                    }
                    // How far apart the two ends stand on their own -- the size
                    // of what the shared-difficulty rule is holding shut.
                    if (material_for_difficulty(e->difficulty) !=
                        material_for_difficulty(p->difficulty)) { ore_boundary++; w_ore++; }
                }
            }

            int step = (n > 40) ? n / 40 : 1;
            int w_audited = 0;
            for (int i = 0; i < n; i += step) {
                DungeonWiring w = dungeon_wiring_for(&map, wseed, i);
                g_dmap.want_portals = (w.n_mouths >= 2) ? w.n_mouths : 2;
                for (int m = 0; m < w.n_mouths; m++) {
                    g_dmap.want_ox[m] = w.want_ox[m];
                    g_dmap.want_oy[m] = w.want_oy[m];
                }
                dungeon_generate(&g_dmap, w.type, w.difficulty, w.seed);
                if (w.n_mouths >= 2)
                    dungeon_bind_cave_mouths(&g_dmap, w.mouth_ow_x, w.mouth_ow_y, w.n_mouths);
                else if (!isnan(w.connect_angle))
                    dungeon_bind_pair(&g_dmap, w.connect_angle,
                                      w.entry_ow_x, w.entry_ow_y,
                                      w.exit_ow_x,  w.exit_ow_y);
                else
                    dungeon_bind_solo(&g_dmap, w.entry_ow_x, w.entry_ow_y);
                audit((int)w.type, wf, wseed, 0.0f);
                w_audited++; sampled++;
            }

            printf("%-10u %9d %8ld %6ld %8d %10ld   %s\n", wseed, n, systems, pairs,
                   w_audited, w_ore,
                   (int)g_fails.size() == before ? "ok" : "FAIL");
        }

        printf("\nmulti-mouth cave systems %ld, disagreeing with themselves %ld\n",
               systems, split_systems);
        printf("linked pairs %ld, ends disagreeing %ld\n", pairs, split_pairs);
        printf("entrances both cave-system and partnered: %ld\n", both);
        printf("pairs whose ends sit in different ore bands: %ld"
               " -- all resolve to the harder end now; this is what used to split\n",
               ore_boundary);
        printf("interiors built from real wirings and stair-audited: %ld\n", sampled);
    }

    // Every distinct failure once, with a count: a broken invariant fires on
    // every seed and a thousand identical lines say nothing the first one did
    // not. The example seed is printed so it can be re-run on its own.
    if (!g_fails.empty()) {
        printf("\n%-13s %-9s %-30s %8s %8s %6s  %s\n",
               "archetype", "form", "check", "got", "want", "count", "example seed");
        for (size_t i = 0; i < g_fails.size(); i++) {
            const Fail& fi = g_fails[i];
            bool first = true;
            int count = 0;
            for (size_t j = 0; j < g_fails.size(); j++) {
                const Fail& fj = g_fails[j];
                if (fj.type != fi.type || fj.form.name != fi.form.name ||
                    fj.what != fi.what) continue;
                if (j < i) { first = false; break; }
                count++;
            }
            if (!first) continue;
            printf("%-13s %-9s %-30s %8d %8d %6d  %u\n",
                   ENT_NAME[fi.type], fi.form.name, fi.what, fi.a, fi.b, count, fi.seed);
        }
    }

    return g_fails.empty() ? 0 : 1;
}
