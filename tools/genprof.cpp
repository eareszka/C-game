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
#include "towns.h"      // TOWN_W/H and VILLAGE_W/H, for the road-coverage check

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
        printf("  dungeons: %d total of %d capacity%s, %d on mountain (cliff>=3)\n",
               g_map.num_dungeon_entrances, MAX_DUNGEON_ENTRANCES,
               g_map.num_dungeon_entrances >= MAX_DUNGEON_ENTRANCES
                   ? "   <-- FULL, mountains silently lost caves" : "",
               n_mtn);
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
            long area_by_mouth[8] = {0}; int area_n[8] = {0};
            double angle_err = 0.0; int angle_n = 0;
            for (int s = 0; s < sys && tested < 60; s++) {
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
                // Feed the carve the mouths' arrangement, exactly as main.cpp
                // does, or the star it builds will not be the one the game gets.
                int mox[DMAP_MAX_PORTALS], moy[DMAP_MAX_PORTALS], k = 0, ssx = 0, ssy = 0;
                for (int i = 0; i < g_map.num_dungeon_entrances && k < n_mouth; i++) {
                    const DungeonEntrance& e = g_map.dungeon_entrances[i];
                    if (e.cave_anchor_x != seen_ax[s] || e.cave_anchor_y != seen_ay[s]) continue;
                    mox[k] = e.x; moy[k] = e.y; ssx += e.x; ssy += e.y; k++;
                }
                ssx /= k; ssy /= k;
                for (int m = 0; m < k; m++) {
                    dm.want_ox[m] = mox[m] - ssx;
                    dm.want_oy[m] = moy[m] - ssy;
                }
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

                // Does the cave grow with the mountain? Floor tiles by mouth
                // count; a constant average across the groups would mean
                // want_portals never reached the carve.
                int floor_n = 0;
                for (int ty = 0; ty < DMAP_H; ty++)
                    for (int tx = 0; tx < DMAP_W; tx++)
                        if (dm.tiles[ty][tx] != DNG_WALL) floor_n++;
                if (n_mouth < 8) { area_by_mouth[n_mouth] += floor_n; area_n[n_mouth]++; }

                // And does the inside face the way the outside does? Compare each
                // mouth's bearing from the mouths' centroid with its portal's
                // bearing from the portals' centroid. Near zero means the star is
                // wired; near 90 means the old spine is still in charge.
                if (k >= 2 && dm.num_portals >= 2) {
                    float pcx = 0, pcy = 0;
                    for (int p = 0; p < dm.num_portals; p++) { pcx += dm.portals[p].tx; pcy += dm.portals[p].ty; }
                    pcx /= dm.num_portals; pcy /= dm.num_portals;
                    for (int m = 0; m < k && m < dm.num_portals; m++) {
                        float ax2 = atan2f((float)dm.want_oy[m], (float)dm.want_ox[m]);
                        float bx2 = atan2f(dm.portals[m].ty - pcy, dm.portals[m].tx - pcx);
                        float d = fabsf(ax2 - bx2);
                        while (d > 3.14159265f) d = 6.28318531f - d;
                        angle_err += d * 57.2957795f; angle_n++;
                    }
                }
            }
            printf("  cave interiors: %d tested, %.2f portals vs %.2f mouths, "
                   "%d short of a portal, %d unreachable%s\n",
                   tested, tested ? (double)portals_total / tested : 0.0,
                   tested ? (double)mouths_total / tested : 0.0,
                   short_portals, broken,
                   (broken || short_portals) ? "   <-- A MOUTH DOES NOT CONNECT" : "");
            printf("  cave floor by mouths:");
            for (int m = 2; m < 8; m++)
                if (area_n[m]) printf("  %d->%ld", m, area_by_mouth[m] / area_n[m]);
            printf("\n  mouth-to-portal bearing error: %.1f deg%s\n",
                   angle_n ? angle_err / angle_n : 0.0,
                   (angle_n && angle_err / angle_n > 45.0)
                       ? "   <-- inside does not match outside" : "");
        }

        // And nothing ordinary may sit within 16 tiles of highland.
        int too_near = 0;
        for (int i = 0; i < g_map.num_dungeon_entrances; i++) {
            const DungeonEntrance& e = g_map.dungeon_entrances[i];
            if (e.cave_anchor_x >= 0) continue;          // mouths are meant to be there
            // Overlap, not proximity: standing beside a cliff is fine now, being
            // inside one or behind its wall is not.
            int s2 = e.size + 1, hit = 0;
            for (int py = e.y; py < e.y + s2 && !hit; py++)
                for (int px = e.x; px < e.x + s2 && !hit; px++) {
                    if (px < 0 || py < 0 || px >= MAP_WIDTH || py >= MAP_HEIGHT) continue;
                    int t = g_map.tiles[py][px];
                    if (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1 ||
                        t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2 ||
                        t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) hit = 1;
                    if (tilemap_face_at(px, py)) hit = 1;
                }
            too_near += hit;
        }
        printf("  ordinary dungeons overlapping a hill or its wall: %d%s\n",
               too_near, too_near ? "   <-- collision test leaking" : "");
        for (int t = 0; t < 9; t++)
            if (flat[t] || mtn[t])
                printf("     %-14s flat %4d   mountain %3d\n", ENT_NAME[t], flat[t], mtn[t]);
    }

    // Roads: how much got laid, whether it goes anywhere it should not, and
    // whether every settlement actually ended up on the network.
    {
        static uint8_t rseen[MAP_HEIGHT][MAP_WIDTH];
        static int rq[MAP_HEIGHT * MAP_WIDTH];
        long road_n = 0, bridge_n = 0, on_cliff = 0, unwalkable = 0;
        int deck_wide = 0, deck_long = 0, deck_wx = -1, deck_wy = -1;
        auto is_road = [&](int x, int y) {
            int t = g_map.tiles[y][x];
            return t == TILE_ROAD || t == TILE_ROAD_BRIDGE;
        };
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int t = g_map.tiles[y][x];
                if (t == TILE_ROAD)        road_n++;
                if (t == TILE_ROAD_BRIDGE) bridge_n++;
                if (!is_road(x, y)) continue;
                if (tilemap_face_at(x, y)) on_cliff++;
                // A road you cannot walk on is not a road.
                if (!tilemap_is_walkable(&g_map, x, y)) unwalkable++;
                if (t != TILE_ROAD_BRIDGE) continue;
                // A deck is three across and no longer than the crossing it was
                // allowed. Measured both ways round: the short run is the width,
                // the long one is the span, and two crossings fused at a corner
                // would show up as a deck wider than three.
                int h = 1, v = 1;
                for (int x2 = x-1; x2 >= 0 && g_map.tiles[y][x2] == TILE_ROAD_BRIDGE; x2--) h++;
                for (int x2 = x+1; x2 < MAP_WIDTH && g_map.tiles[y][x2] == TILE_ROAD_BRIDGE; x2++) h++;
                for (int y2 = y-1; y2 >= 0 && g_map.tiles[y2][x] == TILE_ROAD_BRIDGE; y2--) v++;
                for (int y2 = y+1; y2 < MAP_HEIGHT && g_map.tiles[y2][x] == TILE_ROAD_BRIDGE; y2++) v++;
                int shortr = h < v ? h : v, longr = h < v ? v : h;
                if (shortr > deck_wide) { deck_wide = shortr; deck_wx = x; deck_wy = y; }
                if (longr  > deck_long) deck_long  = longr;
            }

        // Flood the road network from the first road tile; then ask how many
        // settlements have road within reach of their footprint.
        memset(rseen, 0, sizeof rseen);
        int comps = 0, biggest = 0;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int t = g_map.tiles[y][x];
                if (rseen[y][x] || (t != TILE_ROAD && t != TILE_ROAD_BRIDGE)) continue;
                int n = 0, hd = 0;
                rq[n++] = y * MAP_WIDTH + x; rseen[y][x] = 1;
                while (hd < n) {
                    int v = rq[hd++], vy = v / MAP_WIDTH, vx = v % MAP_WIDTH;
                    const int DX[4] = {1,-1,0,0}, DY[4] = {0,0,1,-1};
                    for (int d = 0; d < 4; d++) {
                        int nx = vx + DX[d], ny = vy + DY[d];
                        if (nx < 0 || ny < 0 || nx >= MAP_WIDTH || ny >= MAP_HEIGHT) continue;
                        int tt = g_map.tiles[ny][nx];
                        if (rseen[ny][nx] || (tt != TILE_ROAD && tt != TILE_ROAD_BRIDGE)) continue;
                        rseen[ny][nx] = 1; rq[n++] = ny * MAP_WIDTH + nx;
                    }
                }
                comps++; if (n > biggest) biggest = n;
            }

        // How far outside the footprint the nearest road stops. A boolean with a
        // threshold picked out of the air only argues with itself; the distance
        // says whether a road ends at the wall, at a moat ring, or nowhere near.
        auto road_gap_at = [&](int px, int py, int w, int h) {
            for (int m = 0; m <= 140; m++) {
                for (int y = py - m; y <= py + h + m; y++)
                    for (int x = px - m; x <= px + w + m; x++) {
                        if (x < 0 || y < 0 || x >= MAP_WIDTH || y >= MAP_HEIGHT) continue;
                        // Only the ring at exactly this margin is new.
                        if (m && x > px - m && x < px + w + m && y > py - m && y < py + h + m) continue;
                        int t = g_map.tiles[y][x];
                        if (t == TILE_ROAD || t == TILE_ROAD_BRIDGE) return m;
                    }
            }
            return 999;
        };
        
        // The question the roads have to answer is "can the player drive from
        // any settlement to any other", so the measure is how far short of each
        // one the road stops, and the worst of those. A settlement a road never
        // reaches at all reads 999 and is a different failure from one the road
        // stops twenty tiles outside because something solid is in the way.
        int served_n = 0, total_places = 0, worst = 0;
        char miss[512] = {0}, shown[64] = {0};
        auto note = [&](const char* kind, int i, int px, int py, int gap) {
            total_places++;
            if (gap > worst) worst = gap;
            if (gap <= 6) {
                served_n++;
                if (!shown[0]) snprintf(shown, sizeof shown, "  (look at %s %d: %d,%d)", kind, i, px, py);
            } else {
                snprintf(miss + strlen(miss), sizeof miss - strlen(miss),
                         "%s%s %d at %d,%d stops %d out",
                         miss[0] ? ", " : "", kind, i, px, py, gap);
            }
        };
        for (int i = 0; i < 3; i++)
            if (g_map.towns[i].x >= 0)
                note("town", i, g_map.towns[i].x, g_map.towns[i].y,
                     road_gap_at(g_map.towns[i].x, g_map.towns[i].y, TOWN_W, TOWN_H));
        for (int i = 0; i < g_map.num_villages; i++)
            note("village", i, g_map.villages[i].x, g_map.villages[i].y,
                 road_gap_at(g_map.villages[i].x, g_map.villages[i].y, VILLAGE_W, VILLAGE_H));
        printf("  roads: %ld tiles, %ld bridge, %d network%s (biggest %d), "
               "%d/%d reached, worst approach %d%s\n",
               road_n, bridge_n, comps, comps == 1 ? "" : "s", biggest,
               served_n, total_places, worst,
               on_cliff ? "   <-- ROAD ON A CLIFF" : "");
        printf("    decks %d wide (at %d,%d), longest span %d; %ld road tile%s unwalkable%s\n",
               deck_wide, deck_wx, deck_wy, deck_long, unwalkable, unwalkable == 1 ? "" : "s",
               (unwalkable || on_cliff) ? "   <-- BAD" : "");
        extern int s_route_nodes, s_route_anchors, s_route_lone;
        extern int s_trail_edges, s_trail_unroutable;
        printf("    router saw %d places, anchored %d, %d component%s held only one; "
               "%d edges, %d would not route\n",
               s_route_nodes, s_route_anchors, s_route_lone, s_route_lone == 1 ? "" : "s",
               s_trail_edges, s_trail_unroutable);
        if (miss[0]) printf("    unserved: %s\n", miss);
        // What a settlement with no road is actually surrounded by. Guessing it
        // from a downscaled picture is how the last hour went.
        if (miss[0] && getenv("ROADMAP_DIR")) {
            for (int i = 0; i < 3; i++) {
                if (g_map.towns[i].x < 0) continue;
                int cx2 = g_map.towns[i].x + TOWN_W / 2, cy2 = g_map.towns[i].y + TOWN_H / 2;
                if (road_gap_at(g_map.towns[i].x, g_map.towns[i].y, TOWN_W, TOWN_H) <= 6) continue;
                long hist[256] = {0};
                for (int y = cy2 - 150; y <= cy2 + 150; y++)
                    for (int x = cx2 - 150; x <= cx2 + 150; x++) {
                        if (x < 0 || y < 0 || x >= MAP_WIDTH || y >= MAP_HEIGHT) continue;
                        long dx = x - cx2, dy = y - cy2, r2 = dx*dx + dy*dy;
                        if (r2 < 78L*78 || r2 > 150L*150) continue;
                        hist[g_map.tiles[y][x] & 255]++;
                    }
                printf("    town %d ring 78-150 tiles:", i);
                for (int k = 0; k < 5; k++) {
                    int b = 0; for (int t = 0; t < 256; t++) if (hist[t] > hist[b]) b = t;
                    if (!hist[b]) break;
                    printf("  id%d x%ld", b, hist[b]); hist[b] = 0;
                }
                printf("\n");
            }
        }
        if (shown[0]) printf("  %s\n", shown);

        // A road is a thing you follow across the whole map, so the whole map is
        // the only view that shows whether it worked. Sixteen tiles to a pixel:
        // a 3-wide road survives as a hairline, which is all that is needed to
        // see where the network goes, where it stops, and what it went around.
        if (const char* dir = getenv("ROADMAP_DIR")) {
            const int SC = 4, W = MAP_WIDTH / SC, H = MAP_HEIGHT / SC;
            SDL_Surface* s = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
            Uint32* px = (Uint32*)s->pixels;
            auto put = [&](int x, int y, Uint8 r, Uint8 g, Uint8 b) {
                px[y * (s->pitch / 4) + x] = SDL_MapRGBA(s->format, r, g, b, 255);
            };
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++) {
                    int best = 0;   // 0 ground, 1 cliff, 2 water, 3 bridge, 4 road
                    for (int j = 0; j < SC; j++)
                        for (int i = 0; i < SC; i++) {
                            int t = g_map.tiles[y * SC + j][x * SC + i];
                            bool liquid = t == TILE_WATER || t == TILE_RIVER || t == TILE_LAVA;
                            bool high   = (t >= TILE_CLIFF && t <= TILE_CLIFF_5 && t != 5 && t != 6 && t != 7) ||
                                          (t >= TILE_CLIFF_SNOW_1 && t <= TILE_CLIFF_WASTE_5) ||
                                          tilemap_face_at(x * SC + i, y * SC + j);
                            int r = t == TILE_ROAD        ? 4
                                  : t == TILE_ROAD_BRIDGE ? 3
                                  : liquid ? 2 : high ? 1 : 0;
                            if (r > best) best = r;
                        }
                    switch (best) {
                        case 4: put(x, y, 90, 50, 30);    break;
                        case 3: put(x, y, 255, 140, 0);   break;
                        case 2: put(x, y, 110, 150, 220); break;
                        case 1: put(x, y, 130, 130, 130); break;
                        default: put(x, y, 150, 200, 130);
                    }
                }
            auto dot = [&](int cx, int cy, Uint8 r, Uint8 g, Uint8 b) {
                for (int j = -2; j <= 2; j++)
                    for (int i = -2; i <= 2; i++) {
                        int x = cx / SC + i, y = cy / SC + j;
                        if (x >= 0 && y >= 0 && x < W && y < H) put(x, y, r, g, b);
                    }
            };
            for (int i = 0; i < 3; i++)
                if (g_map.towns[i].x >= 0)
                    dot(g_map.towns[i].x + TOWN_W / 2, g_map.towns[i].y + TOWN_H / 2, 220, 40, 40);
            for (int i = 0; i < g_map.num_villages; i++)
                dot(g_map.villages[i].x + VILLAGE_W / 2, g_map.villages[i].y + VILLAGE_H / 2,
                    250, 240, 60);
            char path[512];
            snprintf(path, sizeof path, "%s/roadmap_%u.png", dir, seed);
            IMG_SavePNG(s, path);
            SDL_FreeSurface(s);
            printf("    wrote %s\n", path);
        }
    }

    {
        int placed_towns = 0;
        for (int i = 0; i < 3; i++) if (g_map.towns[i].x >= 0) placed_towns++;
        printf("  towns: %d of 3 placed   villages: %d\n",
               placed_towns, g_map.num_villages);
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
