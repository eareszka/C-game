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
#include <vector>
#include "tilemap.h"
#include "collision.h"  // the feet (can_occupy)
#include "towns.h"      // TOWN_W/H
#include "../src/sheet_sprites.inc"     // where a yard's fence and wall are on the sheet
#include "../src/landmarks.inc"         // the landmarks' kinds: their blocks and caches

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

    // The boardwalk and its lighthouse: are they out over the sea? Every cell
    // of the deck is on sheet row TOWN1_DECK_ROW0, which nothing else uses, laid
    // as a tile over water and as an overlay on dry ground -- so both grids are
    // read, and each cell is asked what was under it before the town went on.
    // The lighthouse stands at the seaward tip; TIP_LINES is that end.
    // The country's bridges are drawn in the same cells, but only ever as
    // overlays: the wharf is the deck cells that touch one laid as a tile.
    const int TIP_LINES = 12;
    auto deck_cell = [](int t) {
        return t >= TILE_TOWN0_BASE && (t - TILE_TOWN0_BASE) / TOWN0_SHEET_COLS == TOWN1_DECK_ROW0;
    };
    static unsigned char wharf_at[MAP_HEIGHT][MAP_WIDTH];
    {
        static int stack[MAP_HEIGHT * MAP_WIDTH];
        memset(wharf_at, 0, sizeof wharf_at);
        int top = 0;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++)
                if (deck_cell(g_map.tiles[y][x])) { wharf_at[y][x] = 1; stack[top++] = y * MAP_WIDTH + x; }
        while (top) {
            int q = stack[--top];
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++) {
                    int nx = q % MAP_WIDTH + dx, ny = q / MAP_WIDTH + dy;
                    if (nx < 0 || ny < 0 || nx >= MAP_WIDTH || ny >= MAP_HEIGHT || wharf_at[ny][nx]) continue;
                    if (!deck_cell(g_map.overlay[ny][nx])) continue;
                    wharf_at[ny][nx] = 1;
                    stack[top++] = ny * MAP_WIDTH + nx;
                }
        }
    }
    auto is_deck = [&](int x, int y) { return wharf_at[y][x] != 0; };
    // How far out a cell is: larger is further to sea, whichever side that is.
    auto out = [&](int x, int y) { return side == 0 ? -x : side == 1 ? x : side == 2 ? -y : y; };
    int deck = 0, deck_dry = 0, tip_out = -(1 << 30), tip_x = 0, tip_y = 0;
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            if (!is_deck(x, y)) continue;
            deck++;
            if (g_pre[y][x] != TILE_WATER) deck_dry++;
            if (out(x, y) > tip_out) { tip_out = out(x, y); tip_x = x; tip_y = y; }
        }
    int tip_dry = 0, tip_past = 0;
    if (deck) {
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++)
                if (is_deck(x, y) && out(x, y) > tip_out - TIP_LINES && g_pre[y][x] != TILE_WATER) tip_dry++;
        // From the tip back toward land: how much sea lies between it and the shore.
        const int bx = side == 0 ? 1 : side == 1 ? -1 : 0, by = side == 2 ? 1 : side == 3 ? -1 : 0;
        for (int x = tip_x, y = tip_y; x >= 0 && y >= 0 && x < MAP_WIDTH && y < MAP_HEIGHT
                 && g_pre[y][x] == TILE_WATER; x += bx, y += by) tip_past++;
    }
    bool wharf_ok = deck > 0 && tip_dry == 0 && deck_dry <= TOWN1_WHARF_DRY_MAX;

    // The buildings and the things on the green: the town's art, sheet rows
    // TOWN1_ART_ROW0 up to the deck's. Every cell of it the blueprint and the
    // wharf lay has to be there, standing in the overlay with its feet and its
    // depth (tilemap_art_depth) -- none lost, none flat in the ground -- and
    // each thing has to be one the player can walk up to: from the middle of
    // Main Street over whole open tiles to the tile in front of its foot.
    // Whole tiles are the coarse answer, so a way found here is a way.
    const int TOWN1_ART_ROW0 = 180;
    auto is_art = [](int t) {
        int row = (t - TILE_TOWN0_BASE) / TOWN0_SHEET_COLS;
        return t >= TILE_TOWN0_BASE && row >= TOWN1_ART_ROW0 && row < TOWN1_DECK_ROW0;
    };
    int art_want = 0, art = 0, art_flat = 0, things = 0, walled = 0, walled_at[4][2];
    for (int dy = 0; dy < TOWN_H; dy++)
        for (int dx = 0; dx < TOWN_W; dx++)
            art_want += is_art(TILE_TOWN0_BASE + town_1[dy][dx] - 6);
    const TownWharf& wf = TOWN1_WHARF[side];
    for (int i = 0; i < wf.w * wf.h; i++) art_want += wf.art[i] != 0;
    {
        const int M = 100;                                  // the wharf runs out past the town's edge
        const int x0 = tx - M < 0 ? 0 : tx - M, y0 = ty - M < 0 ? 0 : ty - M;
        const int x1 = tx + TOWN_W + M > MAP_WIDTH ? MAP_WIDTH : tx + TOWN_W + M;
        const int y1 = ty + TOWN_H + M > MAP_HEIGHT ? MAP_HEIGHT : ty + TOWN_H + M;
        const int bw = x1 - x0;
        static unsigned char seen[(TOWN_H + 200) * (TOWN_W + 200)];   // 1 walked to, 2 a thing already counted
        static int queue[(TOWN_H + 200) * (TOWN_W + 200)];
        memset(seen, 0, sizeof seen);
        auto at = [&](int x, int y) -> unsigned char& { return seen[(y - y0) * bw + (x - x0)]; };
        auto in = [&](int x, int y) { return x >= x0 && y >= y0 && x < x1 && y < y1; };
        auto open = [&](int x, int y) {
            int ov = g_map.overlay[y][x];
            return tilemap_is_walkable(&g_map, x, y) && ov != TILE_TREE && ov != TILE_DEAD_TREE && ov != TILE_ROCK;
        };
        static const int D[4][2] = { {1, 0}, {-1, 0}, {0, 1}, {0, -1} };
        int head = 0, tail = 0;
        queue[tail++] = (ty + TOWN1_MAIN_Y - y0) * bw + (tx + TOWN_W / 2 - x0);
        seen[queue[0]] = 1;
        while (head < tail) {
            int q = queue[head++], x = x0 + q % bw, y = y0 + q / bw;
            for (auto& d : D) {
                int nx = x + d[0], ny = y + d[1];
                if (!in(nx, ny) || at(nx, ny) || !open(nx, ny)) continue;
                at(nx, ny) = 1;
                queue[tail++] = (ny - y0) * bw + (nx - x0);
            }
        }
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                if (is_art(g_map.tiles[y][x])) art_flat++;
                // the town's own, by where it stands: the villages lay the green's
                // furniture too, from the same rows of the sheet
                if (!is_art(g_map.overlay[y][x]) || !in(x, y)) continue;
                art++;
                if (!tilemap_art_depth(g_map.overlay[y][x])) art_flat++;
                if (!in(x, y) || at(x, y) == 2) continue;
                // one thing: the cells of art that touch. Its front is a tile
                // walked to, under a cell it stands on.
                things++;
                bool front = false;
                head = tail = 0;
                queue[tail++] = (y - y0) * bw + (x - x0);
                at(x, y) = 2;
                while (head < tail) {
                    int q = queue[head++], cx = x0 + q % bw, cy = y0 + q / bw;
                    if (!tilemap_is_walkable(&g_map, cx, cy) && in(cx, cy + 1) && at(cx, cy + 1) == 1) front = true;
                    for (auto& d : D) {
                        int nx = cx + d[0], ny = cy + d[1];
                        if (!in(nx, ny) || at(nx, ny) == 2 || !is_art(g_map.overlay[ny][nx])) continue;
                        at(nx, ny) = 2;
                        queue[tail++] = (ny - y0) * bw + (nx - x0);
                    }
                }
                if (!front) {
                    if (walled < 4) { walled_at[walled][0] = x; walled_at[walled][1] = y; }
                    walled++;
                }
            }
    }
    // A hill may stand in the town's woods, and is only counted. What it may
    // not do is close anything drawn (the user, 2026-10-13: natural obstacles
    // "can form near the town but they cant block any buildings or roads or
    // any object thats drawn on the tilemap besides trees"): no drawn tile --
    // a sheet tile in the ground, or art, the deck or a sign in the overlay --
    // with a hill's top or wall on it or on one of the eight round it. And a
    // tree keeps the hills' own rule: not on a top, not on a wall, not on the
    // tile under one, where its crown would cover the wall's foot.
    auto is_hill = [](int x, int y) { return tilemap_cliff_elev_at(x, y) > 0 || tilemap_face_at(x, y); };
    int hill = 0, hill_on_drawn = 0, hill_trees = 0, hill_at[4][2];
    for (int dy = 0; dy < TOWN_H; dy++)
        for (int dx = 0; dx < TOWN_W; dx++) {
            int x = tx + dx, y = ty + dy;
            hill += is_hill(x, y);
            if (g_map.overlay[y][x] == TILE_TREE && (is_hill(x, y) || tilemap_face_at(x, y - 1))) hill_trees++;
            // the town's own: a street, the deck, its art (sheet rows from
            // TOWN1_ART_ROW0) or its signpost (sheet cell 0,0) -- not a
            // graveyard's yard fence reaching in from outside
            int ov = g_map.overlay[y][x];
            if (g_map.tiles[y][x] < TILE_TOWN0_BASE && ov != TILE_TOWN0_BASE &&
                ov < TILE_TOWN0_BASE + TOWN1_ART_ROW0 * TOWN0_SHEET_COLS) continue;
            bool touched = false;
            for (int j = -1; j <= 1; j++)
                for (int i = -1; i <= 1; i++) touched |= is_hill(x + i, y + j);
            if (touched && hill_on_drawn < 4) { hill_at[hill_on_drawn][0] = x; hill_at[hill_on_drawn][1] = y; }
            hill_on_drawn += touched;
        }
    // The deck whole: every cell of the wharf that stands over water laid, in
    // the ground or over it. One left out is a hole in the deck's side with
    // the sea showing through -- which is what a shed's roof made of the face
    // behind it, taking the tile's overlay for itself. The wharf is found by
    // its lighthouse, whose cells (sheet columns 80-85) are nowhere else.
    int deck_gaps = 0;
    {
        int ox = 0, oy = 0;
        bool found = false;
        for (int n = 0; n < wf.w * wf.h && !found; n++) {
            int col = (wf.art[n] - 6) % TOWN0_SHEET_COLS;
            if (!wf.art[n] || col < 80 || col > 85) continue;
            for (int y = 0; y < MAP_HEIGHT && !found; y++)
                for (int x = 0; x < MAP_WIDTH && !found; x++)
                    if (g_map.overlay[y][x] == TILE_TOWN0_BASE + wf.art[n] - 6) {
                        ox = x - n % wf.w; oy = y - n / wf.w;
                        found = true;
                    }
        }
        if (!found) deck_gaps = -1;
        for (int n = 0; found && n < wf.w * wf.h; n++) {
            int x = ox + n % wf.w, y = oy + n / wf.w;
            if (!wf.cell[n] || x < 0 || y < 0 || x >= MAP_WIDTH || y >= MAP_HEIGHT) continue;
            deck_gaps += g_map.tiles[y][x] == TILE_WATER && g_map.overlay[y][x] != TILE_TOWN0_BASE + wf.cell[n] - 6;
        }
    }
    // The way in. The world's roads come to the town by its gate: the end of
    // Main Street on the landward side (town_gate in src/tilemap.cpp), the
    // street carried on to the footprint's edge and a road laid straight out
    // from it. So the street has to reach the edge there, and no road may lie
    // inside the town -- it used to cut through the woods to the middle. How
    // much road hangs off the gate is counted: none is a town on ground no
    // road could reach, which is said, not failed.
    // And nothing of a graveyard's yard inside the town either: its fence, its
    // wall, or the path it is floored with (the town lays no TILE_PATH).
    const bool gate_west = side == 1 || (side >= 2 && tx + TOWN_W / 2 > MAP_WIDTH / 2);
    const int gate_x = gate_west ? tx - 1 : tx + TOWN_W, gate_y = ty + TOWN1_MAIN_Y;
    const int edge_x = gate_west ? tx : tx + TOWN_W - 1;
    const bool street_at_edge = g_map.tiles[gate_y][edge_x]     == TILE_TOWN0_BASE + 7 * TOWN0_SHEET_COLS + 6 &&
                                g_map.tiles[gate_y + 1][edge_x] == TILE_TOWN0_BASE + 8 * TOWN0_SHEET_COLS + 6;
    int road_in_town = 0, yard_in_town = 0, gate_road = 0;
    const int yard_marks[2] = { TILE_TOWN0_BASE + (YARD_FENCE_SHEET_ROW + 1) * TOWN0_SHEET_COLS + YARD_FENCE_SHEET_COL,
                                TILE_TOWN0_BASE + (YARD_WALL_SHEET_ROW + 1) * TOWN0_SHEET_COLS + YARD_WALL_SHEET_COL };
    for (int dy = 0; dy < TOWN_H; dy++)
        for (int dx = 0; dx < TOWN_W; dx++) {
            int x = tx + dx, y = ty + dy, ov = g_map.overlay[y][x];
            road_in_town += g_map.route[y][x] != ROUTE_NONE;
            yard_in_town += ov == yard_marks[0] || ov == yard_marks[1] || g_map.tiles[y][x] == TILE_PATH;
        }
    if (gate_x >= 0 && gate_x < MAP_WIDTH && g_map.route[gate_y][gate_x] == ROUTE_ROAD) {
        // the road joined to the gate: route tiles and decks, four ways
        static unsigned char seen[MAP_HEIGHT][MAP_WIDTH];
        static int stack[MAP_HEIGHT * MAP_WIDTH];
        memset(seen, 0, sizeof seen);
        int top = 0;
        stack[top++] = gate_y * MAP_WIDTH + gate_x;
        seen[gate_y][gate_x] = 1;
        while (top) {
            int q = stack[--top], x = q % MAP_WIDTH, y = q / MAP_WIDTH;
            gate_road++;
            static const int D[4][2] = { {1, 0}, {-1, 0}, {0, 1}, {0, -1} };
            for (auto& d : D) {
                int nx = x + d[0], ny = y + d[1];
                if (nx < 0 || ny < 0 || nx >= MAP_WIDTH || ny >= MAP_HEIGHT || seen[ny][nx]) continue;
                if (g_map.route[ny][nx] == ROUTE_NONE && g_map.tiles[ny][nx] != TILE_ROAD_BRIDGE) continue;
                seen[ny][nx] = 1;
                stack[top++] = ny * MAP_WIDTH + nx;
            }
        }
    }
    // The country's bridges are boardwalks (lay_bridge in src/tilemap.cpp):
    // every tile of a deck carries a cell of its drawing, every deck has track
    // at two ends, and the feet get from one end to the others over it -- the
    // real feet (can_occupy), kept to the tiles the deck is drawn on and the
    // track tiles against them, so no way round counts. A deck is its bridge
    // tiles and the tiles its drawing lies on, joined four ways; an end is
    // the track tiles against it that touch.
    int decks = 0, deck_bare = 0, deck_lone = 0, deck_blocked = 0, fault_at[4] = { 0, 0, 0, 0 };
    {
        static unsigned char seen[MAP_HEIGHT][MAP_WIDTH];
        memset(seen, 0, sizeof seen);
        auto is_deck = [](int t) { return t == TILE_ROAD_BRIDGE || t == TILE_WASTE_BRIDGE; };
        auto is_art = [](int ov) {
            int n = ov - (TILE_TOWN0_BASE + TOWN1_DECK_ROW0 * TOWN0_SHEET_COLS);
            return n >= 0 && n < TOWN1_DECK_ROWS * TOWN0_SHEET_COLS;
        };
        static const int D[4][2] = { {1, 0}, {-1, 0}, {0, 1}, {0, -1} };
        std::vector<int> comp, bank, queue;
        std::vector<unsigned char> part, went;
        for (int y0 = 1; y0 < MAP_HEIGHT - 1; y0++)
            for (int x0 = 1; x0 < MAP_WIDTH - 1; x0++) {
                if (seen[y0][x0] || !is_deck(g_map.tiles[y0][x0])) continue;
                comp.assign(1, y0 * MAP_WIDTH + x0);
                bank.clear();
                seen[y0][x0] = 1;
                decks++;
                int bx0 = x0, bx1 = x0, by0 = y0, by1 = y0;
                bool edge = false;                          // against the map's edge: not walked (the seam)
                for (size_t h = 0; h < comp.size(); h++) {
                    int x = comp[h] % MAP_WIDTH, y = comp[h] / MAP_WIDTH;
                    deck_bare += is_deck(g_map.tiles[y][x]) && !is_art(g_map.overlay[y][x]);
                    for (auto& d : D) {
                        int nx = x + d[0], ny = y + d[1];
                        if (nx < 1 || ny < 1 || nx >= MAP_WIDTH - 1 || ny >= MAP_HEIGHT - 1) { edge = true; continue; }
                        if (nx < bx0) bx0 = nx;
                        if (nx > bx1) bx1 = nx;
                        if (ny < by0) by0 = ny;
                        if (ny > by1) by1 = ny;
                        if (is_deck(g_map.tiles[ny][nx]) || is_art(g_map.overlay[ny][nx])) {
                            if (!seen[ny][nx]) { seen[ny][nx] = 1; comp.push_back(ny * MAP_WIDTH + nx); }
                        } else if (g_map.route[ny][nx] != ROUTE_NONE) bank.push_back(ny * MAP_WIDTH + nx);
                    }
                }
                if (edge) continue;
                bx0 = bx0 > 3 ? bx0 - 3 : 0; by0 = by0 > 3 ? by0 - 3 : 0;
                bx1 = bx1 < MAP_WIDTH - 4 ? bx1 + 3 : MAP_WIDTH - 1; by1 = by1 < MAP_HEIGHT - 4 ? by1 + 3 : MAP_HEIGHT - 1;
                // part: 1 the deck, 2.. its ends
                const int tw = bx1 - bx0 + 1, th = by1 - by0 + 1;
                part.assign((size_t)tw * th, 0);
                auto P = [&](int x, int y) -> unsigned char& { return part[(size_t)(y - by0) * tw + (x - bx0)]; };
                for (int c : comp) P(c % MAP_WIDTH, c / MAP_WIDTH) = 1;
                // an end is all of its track near the deck, not only the tiles
                // touching it: two scraps of one bank's track are one end
                for (int y = by0; y <= by1; y++)
                    for (int x = bx0; x <= bx1; x++)
                        if (!P(x, y) && g_map.route[y][x] != ROUTE_NONE) P(x, y) = 255;
                int ends = 0;
                for (int c : bank) {
                    if (P(c % MAP_WIDTH, c / MAP_WIDTH) != 255) continue;
                    ends++;
                    queue.assign(1, c);
                    P(c % MAP_WIDTH, c / MAP_WIDTH) = (unsigned char)(1 + ends);
                    for (size_t h = 0; h < queue.size(); h++)
                        for (int dy = -1; dy <= 1; dy++)
                            for (int dx = -1; dx <= 1; dx++) {
                                int nx = queue[h] % MAP_WIDTH + dx, ny = queue[h] / MAP_WIDTH + dy;
                                if (nx < bx0 || nx > bx1 || ny < by0 || ny > by1 || P(nx, ny) != 255) continue;
                                P(nx, ny) = (unsigned char)(1 + ends);
                                queue.push_back(ny * MAP_WIDTH + nx);
                            }
                }
                // No track against it at all is a fault. One end only is not
                // looked into: it is nearly always a deck over the tip of a
                // pool whose two banks' tracks meet round it, which reads here
                // as one end -- so a deck with track at one end alone passes.
                bool fault = ends < 1;
                unsigned got = 0;                           // the ends the feet reached, as bits
                deck_lone += fault;
                if (ends >= 2) {
                    // The feet's centre on a 4 px grid, from every place in an
                    // end: each end has to reach another. (Not all of them
                    // from the first: two decks whose drawings touch are one
                    // deck here, four ends, and each is crossed on its own.)
                    const int S = 4, gw = tw * TILE_SIZE / S, gh = th * TILE_SIZE / S;
                    auto fits = [&](int i, int j) {
                        float cx = bx0 * TILE_SIZE + i * S + S / 2, cy = by0 * TILE_SIZE + j * S + S / 2;
                        return can_occupy(&g_map, cx - (HB_X1 + HB_X2) / 2, cy - (HB_Y1 + HB_Y2) / 2, tilemap_pixel_solid);
                    };
                    auto part_at = [&](int i, int j) { return part[(size_t)(j * S / TILE_SIZE) * tw + i * S / TILE_SIZE]; };
                    unsigned joined = 0;                    // the ends known to reach another
                    for (int from = 2; from <= 1 + ends && from < 31; from++) {
                        if (joined >> from & 1) continue;
                        went.assign((size_t)gw * gh, 0);
                        queue.clear();
                        for (int j = 0; j < gh; j++)
                            for (int i = 0; i < gw; i++)
                                if (part_at(i, j) == from && fits(i, j)) { went[(size_t)j * gw + i] = 1; queue.push_back(j * gw + i); }
                        unsigned reached = 1u << from;
                        for (size_t h = 0; h < queue.size(); h++)
                            for (auto& d : D) {
                                int i = queue[h] % gw + d[0], j = queue[h] / gw + d[1];
                                if (i < 0 || j < 0 || i >= gw || j >= gh || went[(size_t)j * gw + i] || !part_at(i, j)) continue;
                                went[(size_t)j * gw + i] = 1;
                                if (!fits(i, j)) continue;
                                reached |= 1u << (part_at(i, j) < 31 ? part_at(i, j) : 31);
                                queue.push_back(j * gw + i);
                            }
                        reached &= ~(1u << 31);
                        if (reached != 1u << from) joined |= reached;
                    }
                    for (int e = 2; e <= 1 + ends && e < 31 && !fault; e++) fault = !(joined >> e & 1);
                    got = joined >> 2;
                    deck_blocked += fault;
                }
                if (fault && deck_lone + deck_blocked == 1) {
                    fault_at[0] = x0; fault_at[1] = y0; fault_at[2] = ends; fault_at[3] = (int)got;
                }
            }
    }
    // The country's landmarks ("Landmarks" in src/tilemap.cpp): every one whole
    // -- each stamped cell holding its drawing, on dry open ground, off the
    // roads and outside the town -- and its cache come at from the tile in
    // front of it. And what they are for: how much of the land is far from
    // anything, counted without them and with them. "Anything" is a landmark,
    // a dungeon's entrance, or a tile of a town, village or castle; far is
    // more than LM_FAR tiles by the grid (about forty seconds' walk), and
    // LM_NEAR is half that.
    const int LM_FAR = 150, LM_NEAR = 75, LM_KINDS = (int)(sizeof LANDMARK_KINDS / sizeof *LANDMARK_KINDS);
    int lm_bad = 0, lm_shut = 0, lm_kind[16] = {}, lm_drawn[16] = {}, lm_bad_at[4] = { 0, 0, 0, 0 };   // x, y, the tile there, its route
    double far_without = 0, far_with = 0, near_without = 0, near_with = 0;
    {
        for (int i = 0; i < g_map.num_landmarks; i++) {
            const LandmarkPlacement& l = g_map.landmarks[i];
            const LandmarkKind& k = LANDMARK_KINDS[l.kind];
            lm_kind[l.kind < 16 ? l.kind : 15]++;
            bool bad = l.kind >= LM_KINDS;
            const int cache = TILE_TOWN0_BASE + CHEST_ROW * TOWN0_SHEET_COLS + CHEST_COL;   // the chest, shut
            bad |= g_map.overlay[l.y + k.cache_y][l.x + k.cache_x] != cache;
            int drawn = 0;                                  // its cells that hold its drawing: every landmark of a kind has as many
            for (int cy = 0; cy < k.h && !bad; cy++)
                for (int cx = 0; cx < k.w && !bad; cx++) {
                    int x = l.x + cx, y = l.y + cy, t = g_map.tiles[y][x];
                    if (g_map.overlay[y][x] != TILE_TOWN0_BASE + (k.row + cy) * TOWN0_SHEET_COLS + k.col + cx) continue;
                    drawn++;
                    bad = g_map.route[y][x] != ROUTE_NONE
                       || (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SAND && t != TILE_SNOW && t != TILE_WASTELAND)
                       || (x >= tx && x < tx + TOWN_W && y >= ty && y < ty + TOWN_H);
                    if (bad && !lm_bad) { lm_bad_at[0] = x; lm_bad_at[1] = y; lm_bad_at[2] = t; lm_bad_at[3] = g_map.route[y][x]; }
                }
            if (bad && !lm_bad && !lm_bad_at[0]) { lm_bad_at[0] = l.x + k.cache_x; lm_bad_at[1] = l.y + k.cache_y; lm_bad_at[2] = -1; }
            if (!lm_drawn[l.kind < 16 ? l.kind : 15]) lm_drawn[l.kind < 16 ? l.kind : 15] = drawn;
            bad |= drawn != lm_drawn[l.kind < 16 ? l.kind : 15];
            lm_bad += bad;
            lm_shut += !tilemap_is_walkable(&g_map, l.x + k.cache_x, l.y + k.h);
        }
        static unsigned short dist[MAP_HEIGHT][MAP_WIDTH];
        static int queue[MAP_HEIGHT * MAP_WIDTH];
        for (int with = 0; with < 2; with++) {
            memset(dist, 0xFF, sizeof dist);
            int head = 0, tail = 0;
            auto source = [&](int x, int y) {
                if (x < 0 || y < 0 || x >= MAP_WIDTH || y >= MAP_HEIGHT || dist[y][x] == 0) return;
                dist[y][x] = 0;
                queue[tail++] = y * MAP_WIDTH + x;
            };
            for (int y = 0; y < MAP_HEIGHT; y++)
                for (int x = 0; x < MAP_WIDTH; x++) {
                    int t = g_map.tiles[y][x];
                    if (t == TILE_BLUEPRINT || t == TILE_VILLAGE_PLACEHOLDER || t == TILE_CASTLE_PLACEHOLDER || t >= TILE_TOWN0_BASE)
                        source(x, y);
                }
            for (int i = 0; i < g_map.num_dungeon_entrances; i++) source(g_map.dungeon_entrances[i].x, g_map.dungeon_entrances[i].y);
            for (int i = 0; with && i < g_map.num_landmarks; i++) source(g_map.landmarks[i].x, g_map.landmarks[i].y);
            static const int D[4][2] = { {1, 0}, {-1, 0}, {0, 1}, {0, -1} };
            while (head < tail) {
                int q = queue[head++], x = q % MAP_WIDTH, y = q / MAP_WIDTH;
                if (dist[y][x] > LM_FAR) continue;              // far is far: no need to count on
                for (auto& d : D) {
                    int nx = x + d[0], ny = y + d[1];
                    if (nx < 0 || ny < 0 || nx >= MAP_WIDTH || ny >= MAP_HEIGHT || dist[ny][nx] != 0xFFFF) continue;
                    dist[ny][nx] = (unsigned short)(dist[y][x] + 1);
                    queue[tail++] = ny * MAP_WIDTH + nx;
                }
            }
            long land = 0, far = 0, near = 0;
            for (int y = 0; y < MAP_HEIGHT; y++)
                for (int x = 0; x < MAP_WIDTH; x++) {
                    int t = g_map.tiles[y][x];
                    if (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SAND && t != TILE_SNOW && t != TILE_WASTELAND) continue;
                    land++;
                    far += dist[y][x] > LM_FAR;
                    near += dist[y][x] > LM_NEAR;
                }
            (with ? far_with : far_without) = land ? 100.0 * far / land : 0.0;
            (with ? near_with : near_without) = land ? 100.0 * near / land : 0.0;
        }
    }
    bool art_ok = art == art_want && !art_flat && !walled && !hill_on_drawn && !hill_trees && !deck_gaps
               && street_at_edge && !road_in_town && !yard_in_town && !deck_bare && !deck_lone && !deck_blocked
               && !lm_bad && !lm_shut;

    // Where the town ended up is the requirement, and it is the whole of it.
    // A footprint with cliff or river under it is worth saying out loud, but a
    // town that levelled some rock to stand on the coast is in the right place;
    // one sitting inland in a meadow is not. The shore search only settles for
    // rough ground when no clean window exists -- see its relaxed path.
    bool ok = (hi == COAST_REACH) && (dry == 0) && !wet_inland && wharf_ok && art_ok;
    printf("seed %-6u ocean %c  town1 (%4d,%4d)  reach %3d-%3d  boardwalk %3d cells, %3d on land, "
           "lighthouse end %d on land, tip %3d past the shore  %s\n",
           seed, "WENS"[side], tx, ty, lo, hi, deck, deck_dry, tip_dry, tip_past, ok ? "ok" : "FAIL");
    printf("             buildings: %d cells of %d, %d flat, %d things, %d that cannot be walked up to\n",
           art, art_want, art_flat, things, walled);
    printf("             hills: %d tiles inside the town, %d drawn tiles with a hill on or against them, "
           "%d trees on or under one\n", hill, hill_on_drawn, hill_trees);
    for (int i = 0; i < walled && i < 4; i++) {
        int id = g_map.overlay[walled_at[i][1]][walled_at[i][0]] - TILE_TOWN0_BASE;
        printf("             nothing walks up to the front of the art at (%d,%d), sheet cell %d,%d\n",
               walled_at[i][0], walled_at[i][1], id % TOWN0_SHEET_COLS, id / TOWN0_SHEET_COLS);
    }
    printf("             roads: gate to the %s, street %s the town's edge, %d tiles of road joined to it; "
           "%d road tiles and %d yard tiles inside the town\n", gate_west ? "west" : "east",
           street_at_edge ? "reaches" : "DOES NOT REACH", gate_road, road_in_town, yard_in_town);
    printf("             bridges: %d decks, %d deck tiles with no drawing, %d decks with no track against them, "
           "%d the feet cannot cross\n", decks, deck_bare, deck_lone, deck_blocked);
    {
        // what the router says it laid: each with BRIDGE_RUN tiles of straight
        // track at both ends, but for those a branch could not otherwise reach
        extern int s_bridges_laid, s_bridges_short;
        printf("             run-ups: %d bridges laid with %d tiles of straight track each side, %d more with a short one\n",
               s_bridges_laid - s_bridges_short, BRIDGE_RUN, s_bridges_short);
    }
    printf("             landmarks: %d (by kind:", g_map.num_landmarks);
    for (int k = 0; k < LM_KINDS && k < 16; k++) printf(" %d", lm_kind[k]);
    printf("), %d badly placed, %d whose cache cannot be come at", lm_bad, lm_shut);
    if (g_map.num_landmarks) printf("; the first at (%d,%d)", g_map.landmarks[0].x, g_map.landmarks[0].y);
    if (lm_bad) printf("; the first bad one at (%d,%d): tile %d (-1: its cache is not there), route %d",
                       lm_bad_at[0], lm_bad_at[1], lm_bad_at[2], lm_bad_at[3]);
    printf("\n             empty land: over %d tiles from anything %.1f%% without the landmarks, %.1f%% with; "
           "over %d tiles %.1f%% without, %.1f%% with\n", LM_NEAR, near_without, near_with, LM_FAR, far_without, far_with);
    if (deck_blocked || deck_lone)
        printf("             the first deck at fault is at (%d,%d): %d ends, the feet reached (as bits) %x\n",
               fault_at[0], fault_at[1], fault_at[2], fault_at[3]);
    for (int i = 0; i < hill_on_drawn && i < 4; i++) {
        int x = hill_at[i][0], y = hill_at[i][1];
        int id = (g_map.overlay[y][x] >= TILE_TOWN0_BASE ? g_map.overlay[y][x] : g_map.tiles[y][x]) - TILE_TOWN0_BASE;
        printf("             a hill on or against the drawn tile at (%d,%d), sheet cell %d,%d\n",
               x, y, id % TOWN0_SHEET_COLS, id / TOWN0_SHEET_COLS);
    }
    if (deck_gaps)
        printf("             %d cells of the deck over water were not laid (-1: no lighthouse to find it by)\n", deck_gaps);
    if (!deck)
        printf("             no boardwalk was laid at all\n");
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
               "%d near town 0, %d headland, %d unclean, %d kept, %d coastal\n",
               g_tally.windows, g_tally.no_coast, g_tally.bounds, g_tally.near_town0,
               g_tally.headland, g_tally.unclean, g_tally.kept, g_tally.coastal);
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
