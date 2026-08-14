// Worldgen profiler: builds a world and reports how long each generation stage
// took, worst first.
//
//   genprof.exe [seed]
//
// Worldgen is two dozen passes over a nine-million-tile map and the player
// waits for all of it, so "which pass is the slow one" is the question that has
// to be answerable before anything is tuned. It is answered off the tracing
// hook that is already there: tilemap.cpp calls GEN_STAGE at every stage
// boundary, which compiles to gen_trace_stage() when GEN_TRACE is defined and
// to nothing otherwise. Nothing in the shipping build changes.
//
// Build it from MSYS2 MINGW64, with tilemap.cpp compiled -DGEN_TRACE for this
// binary only (note -Umain, as in tools/shot.cpp: without it SDL's
// -Dmain=SDL_main turns main into SDL_main and the link fails on WinMain):
//
//   g++ -O2 -w -std=c++17 -Iinclude -DGEN_TRACE -c src/tilemap.cpp -o tilemap_prof.o
//   g++ -O2 -w -std=c++17 -I. -Iinclude -DSDL_MAIN_HANDLED -DGEN_TRACE \
//     $(pkg-config --cflags sdl2 SDL2_image) -Umain tools/genprof.cpp \
//     tilemap_prof.o src/resource_node.o src/core.o src/camera.o -o genprof.exe \
//     $(pkg-config --libs sdl2 SDL2_image | sed "s/-lSDL2main//; s/-mwindows//")
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <algorithm>
#include "tilemap.h"
#include "dungeon.h"

static Tilemap g_map;

struct Stage { std::string name; double ms; };
static std::vector<Stage> g_stages;
static Uint64 g_last, g_freq;

// The stage name handed over is the boundary *before* a pass, so the time
// charged here belongs to the pass named by the previous call. Recording it
// that way round is what makes the table read as "this pass cost this much"
// rather than off by one.
static std::string g_pending = "(startup)";

void gen_trace_stage(const Tilemap* /*map*/, const char* stage)
{
    Uint64 now = SDL_GetPerformanceCounter();
    double ms = (double)(now - g_last) * 1000.0 / (double)g_freq;
    g_stages.push_back({ g_pending, ms });
    g_pending = stage ? stage : "(null)";
    g_last = now;
}

int main(int argc, char** argv)
{
    unsigned seed = (argc > 1) ? (unsigned)strtoul(argv[1], nullptr, 10) : 387u;

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);

    SDL_Surface* s = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* r = SDL_CreateSoftwareRenderer(s);

    // Timed separately because the player waits for this too: it is the tile
    // sheet being cut up and the cliff ink mask being read back off it, and it
    // happens once at startup whether or not a world is being built.
    Uint64 freq0 = SDL_GetPerformanceFrequency();
    Uint64 ti = SDL_GetPerformanceCounter();
    tilemap_init_tile_cache(r);
    double init_ms = (double)(SDL_GetPerformanceCounter() - ti) * 1000.0 / (double)freq0;
    printf("tile cache init %.0f ms\n", init_ms);

    g_freq = SDL_GetPerformanceFrequency();
    Uint64 t0 = SDL_GetPerformanceCounter();
    g_last = t0;

    tilemap_build_overworld_phase1(&g_map, seed);
    double p1 = (double)(SDL_GetPerformanceCounter() - t0) * 1000.0 / (double)g_freq;

    Uint64 t1 = SDL_GetPerformanceCounter();
    tilemap_build_overworld_phase2(&g_map, seed);
    double p2 = (double)(SDL_GetPerformanceCounter() - t1) * 1000.0 / (double)g_freq;

    // Whatever was still pending when the last stage ran.
    gen_trace_stage(&g_map, "(end)");

    // A checksum of the whole world, which is what an optimisation has to leave
    // alone. A rendered window is the wrong instrument here: it covers 44x30 of
    // 3000x3000, and a biome pass can move a desert on the far side of the map
    // without touching a single pixel of it. Hash every tile and every overlay
    // instead, and the test covers all nine million.
    uint64_t h = 1469598103934665603ull;                    // FNV-1a
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            h = (h ^ (uint64_t)(unsigned)g_map.tiles[y][x])   * 1099511628211ull;
            h = (h ^ (uint64_t)(unsigned)g_map.overlay[y][x]) * 1099511628211ull;
        }

    double total = p1 + p2;
    printf("seed %u   phase1 %.0f ms   phase2 %.0f ms   total %.0f ms   world %016llx\n",
           seed, p1, p2, total, (unsigned long long)h);

    // Castles 0-2 are placed during phase2 and keep {-1,-1} when their pass
    // finds nowhere to stand. Worth printing: castle 1 spent the project so far
    // never placing at all, and nothing said so.
    // Why the mountain castle did or did not place. It wants a 16x16 block that
    // is all top-level plateau with no cliff drawn over any of it, so the
    // question is simply how big the largest such block in the world is.
    // Largest-square dynamic programming, one row of state at a time.
    for (int L = 3; L >= 1; L--) {
        static int prev[MAP_WIDTH], cur[MAP_WIDTH];
        int best = 0, bx = -1, by = -1;
        int open_tiles = 0;
        for (int x = 0; x < MAP_WIDTH; x++) prev[x] = 0;
        for (int y = 0; y < MAP_HEIGHT; y++) {
            for (int x = 0; x < MAP_WIDTH; x++) {
                int t = g_map.tiles[y][x];
                bool lvl = (L == 3 && (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3))
                        || (L == 2 && (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2))
                        || (L == 1 && (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1));
                bool open_ = lvl && !tilemap_face_at(x, y);
                if (open_) open_tiles++;
                if (!open_ || x == 0 || y == 0) { cur[x] = open_ ? 1 : 0; }
                else {
                    int a = prev[x], b = cur[x-1], c = prev[x-1];
                    int m = a < b ? a : b; if (c < m) m = c;
                    cur[x] = m + 1;
                }
                if (cur[x] > best) { best = cur[x]; bx = x; by = y; }
            }
            for (int x = 0; x < MAP_WIDTH; x++) prev[x] = cur[x];
        }
        printf("  level %d: open %d tiles, largest open square %dx%d at %d,%d%s\n",
               L, open_tiles, best, best, bx, by,
               best >= 16 ? "   (fits a castle)" : "   <-- too small for 16x16");
    }

    // Landforms by how many storeys they carry. This is what the cave roll is
    // taken against, so the shape of this table decides whether "5% of
    // one-storey mountains" is a handful of caves or a hundred.
    {
        static uint8_t seen[MAP_HEIGHT][MAP_WIDTH];
        static int q[MAP_HEIGHT * MAP_WIDTH];
        memset(seen, 0, sizeof seen);
        auto lvl_at = [&](int x, int y) {
            int t = g_map.tiles[y][x];
            if (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1) return 1;
            if (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2) return 2;
            if (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) return 3;
            return 0;
        };
        int by_top[4] = {0,0,0,0}, area_top[4] = {0,0,0,0};
        for (int y0 = 0; y0 < MAP_HEIGHT; y0++)
            for (int x0 = 0; x0 < MAP_WIDTH; x0++) {
                if (seen[y0][x0] || !lvl_at(x0, y0)) continue;
                int n = 0, head = 0, top = 0;
                q[n++] = y0 * MAP_WIDTH + x0; seen[y0][x0] = 1;
                while (head < n) {
                    int v = q[head++], vy = v / MAP_WIDTH, vx = v % MAP_WIDTH;
                    int L = lvl_at(vx, vy); if (L > top) top = L;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int px = vx + dx, py = vy + dy;
                            if (px < 0 || py < 0 || px >= MAP_WIDTH || py >= MAP_HEIGHT) continue;
                            if (seen[py][px] || !lvl_at(px, py)) continue;
                            seen[py][px] = 1; q[n++] = py * MAP_WIDTH + px;
                        }
                }
                if (top >= 1 && top <= 3) { by_top[top]++; area_top[top] += n; }
            }
        printf("  landforms: 1-storey %d (avg %d tiles), 2-storey %d (avg %d), 3-storey %d (avg %d)\n",
               by_top[1], by_top[1] ? area_top[1]/by_top[1] : 0,
               by_top[2], by_top[2] ? area_top[2]/by_top[2] : 0,
               by_top[3], by_top[3] ? area_top[3]/by_top[3] : 0);
        printf("  would roll caves: 3-storey %d + 2-storey ~%.1f + 1-storey ~%.1f = ~%.1f\n",
               by_top[3], by_top[2] * 0.33, by_top[1] * 0.05,
               by_top[3] + by_top[2] * 0.33 + by_top[1] * 0.05);
    }

    // Dungeon entrances by archetype, split by whether they landed on mountain
    // ground. "Mountain" is what tilemap.cpp calls cliff_level_of() >= 3, i.e.
    // the top storey only — level 1 and 2 plateaus count as flat ground here.
    {
        static const char* ENT_NAME[9] = {
            "cave", "ruins", "graveyard_sm", "graveyard_lg", "oasis",
            "pyramid", "stonehenge", "large_tree", "?"
        };
        int flat[9] = {0}, mtn[9] = {0}, n_mtn = 0;
        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            int t = (int)g_map.dungeon_entrances[i].type;
            if (t < 0 || t > 7) t = 8;
            bool is_mtn = g_map.dungeon_entrances[i].cliff_level >= 3;
            if (is_mtn) { mtn[t]++; n_mtn++; } else flat[t]++;
        }
        // Cave systems: mouths sharing one anchor are one cave. Also check each
        // mouth is where it claims to be — a 2x2 should have band drawn on the
        // tile north of it and none south, which is what "cut into the foot of
        // a south wall" means; a 1x1 should sit on a plateau top.
        int sys = 0, mouths = 0, bad_face = 0, bad_top = 0, unreachable = 0, no_approach = 0;
        int first_mouth_x = -1, first_mouth_y = -1;
        int seen_ax[512], seen_ay[512];
        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            if (e.cave_anchor_x < 0) continue;
            mouths++;
            bool known = false;
            for (int s = 0; s < sys; s++)
                if (seen_ax[s] == e.cave_anchor_x && seen_ay[s] == e.cave_anchor_y) known = true;
            if (!known && sys < 512) { seen_ax[sys] = e.cave_anchor_x; seen_ay[sys] = e.cave_anchor_y; sys++; }

            int s = e.size + 1;
            if (e.size == 1) {          // the 2x2 in the wall
                // Mountain above it — either more wall, or the plateau itself
                // where the wall is only as deep as the mouth is tall.
                int above = g_map.tiles[e.y - 1][e.x];
                bool up = tilemap_face_at(e.x, e.y - 1) ||
                          (above == TILE_CLIFF || above == TILE_CLIFF_SNOW_1 ||
                           above == TILE_CLIFF_WASTE_1 || above == TILE_CLIFF_2 ||
                           above == TILE_CLIFF_3);
                if (!up) bad_face++;
                if (tilemap_face_at(e.x, e.y + s)) bad_face++;   // open below
                // The one that decides whether the cave can be entered at all:
                // you walk in from the south, so the row under the mouth has to
                // be crossable. A mouth one row shy of the foot is walkable
                // itself and still sealed by the rock beneath it.
                for (int c = 0; c < s; c++)
                    if (!tilemap_is_walkable(&g_map, e.x + c, e.y + s)) no_approach++;
                if (first_mouth_x < 0) { first_mouth_x = e.x; first_mouth_y = e.y; }
            } else {                     // a 1x1 on a top
                int t = g_map.tiles[e.y][e.x];
                (void)t;                 // the tile is the mouth now; level came from placement
                if (e.cliff_level < 1) bad_top++;
            }
            // The mouth itself must be crossable, or it cannot be stood on.
            for (int r = 0; r < s; r++)
                for (int c = 0; c < s; c++)
                    if (!tilemap_is_walkable(&g_map, e.x + c, e.y + r)) unreachable++;
        }
        printf("  dungeons: %d total, %d on mountain (cliff>=3)\n",
               g_map.num_dungeon_entrances, n_mtn);
        printf("  caves: %d systems, %d mouths, %.1f per system"
               "   [bad_face %d  bad_top %d  unwalkable %d  no_approach %d]\n",
               sys, mouths, sys ? (double)mouths / sys : 0.0,
               bad_face, bad_top, unreachable, no_approach);
        if (first_mouth_x >= 0)
            printf("  first cave mouth at %d,%d\n", first_mouth_x, first_mouth_y);

        // Castle 1 must be on a mountain that has a cave, because the cave is
        // how the player gets up to it. Proxy: a mouth within 100 tiles. The
        // castle's own footprint is placeholder tiles, so it is a hole in the
        // level map and cannot be flood-filled from directly.
        // Exact, not a distance proxy: flood the landform the castle stands on
        // and ask whether any cave system's anchor is a tile of it. The anchor
        // is the landform's own canonical top-left, so membership is the whole
        // question. Seed from a highland tile just outside the castle footprint,
        // because the footprint itself is placeholder tiles and reads as a hole.
        if (g_map.castles[1].x >= 0) {
            static uint8_t cseen[MAP_HEIGHT][MAP_WIDTH];
            static int cq[MAP_HEIGHT * MAP_WIDTH];
            memset(cseen, 0, sizeof cseen);
            auto is_hi = [&](int x, int y) {
                int t = g_map.tiles[y][x];
                return t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1 ||
                       t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2 ||
                       t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3;
            };
            int sx0 = -1, sy0 = -1;
            for (int d = -1; d <= 16 && sx0 < 0; d++)
                for (int p = 0; p < 4 && sx0 < 0; p++) {
                    int qx = g_map.castles[1].x + (p == 0 ? d : p == 1 ? d : p == 2 ? -1 : 16);
                    int qy = g_map.castles[1].y + (p == 0 ? -1 : p == 1 ? 16 : d);
                    if (qx < 0 || qy < 0 || qx >= MAP_WIDTH || qy >= MAP_HEIGHT) continue;
                    if (is_hi(qx, qy)) { sx0 = qx; sy0 = qy; }
                }
            int found = 0, comp = 0;
            if (sx0 >= 0) {
                int n2 = 0, hd = 0;
                cq[n2++] = sy0 * MAP_WIDTH + sx0; cseen[sy0][sx0] = 1;
                while (hd < n2) {
                    int v = cq[hd++], vy = v / MAP_WIDTH, vx = v % MAP_WIDTH;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int px = vx + dx, py = vy + dy;
                            if (px < 0 || py < 0 || px >= MAP_WIDTH || py >= MAP_HEIGHT) continue;
                            if (cseen[py][px] || !is_hi(px, py)) continue;
                            cseen[py][px] = 1; cq[n2++] = py * MAP_WIDTH + px;
                        }
                }
                comp = n2;
                for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
                    const DungeonEntrance& e = g_map.dungeon_entrances[i];
                    if (e.cave_anchor_x < 0) continue;
                    if (cseen[e.cave_anchor_y][e.cave_anchor_x]) { found = 1; break; }
                }
            }
            printf("  castle1 mountain (%d tiles): cave %s\n", comp,
                   found ? "YES" : "NO   <-- castle unreachable by cave");
        }

        // Do the mouths actually connect? Generate each system's interior the
        // way main.cpp does — same seed from the shared anchor, same portal
        // count — and flood the floor from portal 0. Every portal must be
        // reachable, or a mouth is a way in that leads nowhere and the mountain
        // is not a route through.
        {
            static DungeonMap dm;
            static uint8_t dseen[DMAP_H][DMAP_W];
            static int dq[DMAP_H * DMAP_W];
            int tested = 0, broken = 0, portals_total = 0, short_portals = 0, mouths_total = 0;
            for (int s = 0; s < sys && tested < 12; s++) {
                int n_mouth = 0; float diff = 0.0f;
                for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
                    const DungeonEntrance& e = g_map.dungeon_entrances[i];
                    if (e.cave_anchor_x != seen_ax[s] || e.cave_anchor_y != seen_ay[s]) continue;
                    if (!n_mouth) diff = e.difficulty;
                    n_mouth++;
                }
                if (n_mouth < 2) continue;
                if (n_mouth > DMAP_MAX_PORTALS) n_mouth = DMAP_MAX_PORTALS;
                unsigned dseed = seed
                    ^ ((unsigned)seen_ax[s] * 73856093u)
                    ^ ((unsigned)seen_ay[s] * 19349663u);
                dm.want_portals = n_mouth;
                dungeon_generate(&dm, DUNGEON_ENT_CAVE, diff, dseed);
                tested++;
                portals_total += dm.num_portals;
                mouths_total  += n_mouth;
                // A mouth with no portal is a way in with no way back out.
                if (dm.num_portals < n_mouth) short_portals++;

                memset(dseen, 0, sizeof dseen);
                int n2 = 0, hd = 0;
                dq[n2++] = dm.portals[0].ty * DMAP_W + dm.portals[0].tx;
                dseen[dm.portals[0].ty][dm.portals[0].tx] = 1;
                while (hd < n2) {
                    int v = dq[hd++], vy = v / DMAP_W, vx = v % DMAP_W;
                    const int DX[4] = {1,-1,0,0}, DY[4] = {0,0,1,-1};
                    for (int d = 0; d < 4; d++) {
                        int nx = vx + DX[d], ny = vy + DY[d];
                        if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H) continue;
                        if (dseen[ny][nx] || dm.tiles[ny][nx] == DNG_WALL) continue;
                        dseen[ny][nx] = 1; dq[n2++] = ny * DMAP_W + nx;
                    }
                }
                for (int p = 0; p < dm.num_portals; p++)
                    if (!dseen[dm.portals[p].ty][dm.portals[p].tx]) { broken++; break; }
            }
            printf("  cave interiors: %d tested, %.2f portals vs %.2f mouths, "
                   "%d short of a portal, %d unreachable%s\n",
                   tested, tested ? (double)portals_total / tested : 0.0,
                   tested ? (double)mouths_total / tested : 0.0,
                   short_portals, broken,
                   (broken || short_portals) ? "   <-- A MOUTH DOES NOT CONNECT" : "");
        }

        // And nothing ordinary may sit within 16 tiles of highland.
        int too_near = 0;
        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            if (e.cave_anchor_x >= 0) continue;          // mouths are meant to be there
            int s2 = e.size + 1, hit = 0;
            for (int py = e.y - 16; py < e.y + s2 + 16 && !hit; py++)
                for (int px = e.x - 16; px < e.x + s2 + 16 && !hit; px++) {
                    if (px < 0 || py < 0 || px >= MAP_WIDTH || py >= MAP_HEIGHT) continue;
                    int t = g_map.tiles[py][px];
                    if (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1 ||
                        t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2 ||
                        t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) hit = 1;
                }
            too_near += hit;
        }
        printf("  ordinary dungeons within 16 tiles of highland: %d%s\n",
               too_near, too_near ? "   <-- keep-out leaking" : "");
        for (int t = 0; t < 9; t++)
            if (flat[t] || mtn[t])
                printf("     %-14s flat %4d   mountain %3d\n", ENT_NAME[t], flat[t], mtn[t]);
    }

    static const char* CASTLE_NAME[3] = { "ocean", "mountain", "lava" };
    printf("  castles:");
    for (int i = 0; i < 3; i++) {
        if (g_map.castles[i].x < 0) { printf("  %s=none", CASTLE_NAME[i]); continue; }
        printf("  %s=%d,%d", CASTLE_NAME[i], g_map.castles[i].x, g_map.castles[i].y);
        if (i != 1) continue;
        // Which storey the mountain castle ended up on. Its own footprint is
        // placeholder tiles by now, so read the ring just outside it.
        int seen[6] = {0,0,0,0,0,0};
        int x0 = g_map.castles[i].x, y0 = g_map.castles[i].y;
        for (int d = -1; d <= 16; d++) {
            const int pts[4][2] = { {x0+d,y0-1}, {x0+d,y0+16}, {x0-1,y0+d}, {x0+16,y0+d} };
            for (int p = 0; p < 4; p++) {
                int qx = pts[p][0], qy = pts[p][1];
                if (qx < 0 || qy < 0 || qx >= MAP_WIDTH || qy >= MAP_HEIGHT) continue;
                int t = g_map.tiles[qy][qx], lv = 0;
                if (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1) lv = 1;
                if (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2) lv = 2;
                if (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) lv = 3;
                seen[lv]++;
            }
        }
        int top = 0;
        for (int l = 1; l <= 3; l++) if (seen[l] > seen[top]) top = l;
        printf("(L%d)", top);
    }
    printf("\n\n");

    std::vector<Stage> by_cost = g_stages;
    std::sort(by_cost.begin(), by_cost.end(),
              [](const Stage& a, const Stage& b) { return a.ms > b.ms; });

    printf("%-52s %9s %7s\n", "stage", "ms", "share");
    printf("%-52s %9s %7s\n", "-----", "--", "-----");
    double shown = 0.0;
    for (const Stage& st : by_cost) {
        if (st.ms < 1.0) continue;              // noise
        shown += st.ms;
        printf("%-52s %9.1f %6.1f%%\n", st.name.c_str(), st.ms,
               total > 0.0 ? 100.0 * st.ms / total : 0.0);
    }
    printf("\n%zu stages, %.0f ms accounted for out of %.0f\n",
           g_stages.size(), shown, total);
    return 0;
}
