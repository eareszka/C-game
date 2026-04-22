#include "dungeon.h"
#include "collision.h"
#include "core.h"
#include <string.h>
#include <math.h>

// ── Color palettes per dungeon type ───────────────────────────────────────
struct DngPalette { SDL_Color wall, floor, entry, exit_; };

static const DngPalette PALETTES[8] = {
    // CAVE
    {{ 35, 30, 30,255},{ 65, 58, 55,255},{200,175, 40,255},{180, 45, 45,255}},
    // RUINS
    {{ 75, 65, 55,255},{110, 98, 82,255},{200,175, 40,255},{180, 45, 45,255}},
    // GRAVEYARD_SM
    {{ 32, 28, 45,255},{ 58, 52, 70,255},{200,175, 40,255},{100, 50,180,255}},
    // GRAVEYARD_LG
    {{ 28, 24, 40,255},{ 52, 47, 65,255},{200,175, 40,255},{100, 50,180,255}},
    // OASIS
    {{ 20, 75, 65,255},{ 38,115, 95,255},{200,175, 40,255},{ 30,190,170,255}},
    // PYRAMID
    {{115, 95, 42,255},{155,132, 68,255},{200,175, 40,255},{220,190, 50,255}},
    // STONEHENGE  — warm orange walls, near-black walkable corridors
    {{210,112, 20,255},{ 10,  5,  2,255},{200,175, 40,255},{ 80,110,200,255}},
    // LARGE_TREE
    {{ 20, 55, 18,255},{ 33, 85, 28,255},{200,175, 40,255},{ 55,200, 50,255}},
};

// ── ASCII chars per dungeon type [wall, floor] ────────────────────────────
struct DngAscii { char wall, floor; };
static const DngAscii ASCII_CHARS[8] = {
    {'#', '.'}, // CAVE
    {'+', ','}, // RUINS
    {'#', '.'}, // GRAVEYARD_SM
    {'#', '.'}, // GRAVEYARD_LG
    {'=', '.'}, // OASIS
    {'#', '.'}, // PYRAMID
    {'O', '.'}, // STONEHENGE
    {'*', '.'}, // LARGE_TREE
};

// ── LCG RNG ───────────────────────────────────────────────────────────────
static uint32_t rng_next(uint32_t* s) {
    *s = *s * 1664525u + 1013904223u;
    return (*s >> 16) & 0x7FFF;
}

// ── BSP room generator ────────────────────────────────────────────────────
#define MAX_BSP_NODES 127
#define MIN_PART      12   // smallest partition we'll attempt to split
#define MIN_ROOM       5   // smallest room dimension in tiles
#define ROOM_MARGIN    2   // gap between room edge and partition edge
#define CORR_W         2   // corridor width in tiles

// Per-generation BSP tuning (reset before each BSP run)
static int s_bsp_max_depth = 4;
static int s_bsp_min_part  = MIN_PART;

struct BSPNode {
    int x, y, w, h;       // partition bounds
    int lc, rc;            // child indices (-1 = leaf)
    int rx, ry, rw, rh;   // room (leaves only)
    int rcx, rcy;          // room centre (propagated up)
};

static BSPNode s_bsp[MAX_BSP_NODES];
static int     s_bsp_n;
static int     s_leaves[MAX_BSP_NODES];
static int     s_leaf_n;

// ── Cellular automata buffers (cave & tree generation) ────────────────────
static uint8_t  s_ca_buf[DMAP_H][DMAP_W];           // CA double-buffer
static uint8_t  s_ca_vis[DMAP_H][DMAP_W];           // flood-fill visited
static int32_t  s_ca_bfs[DMAP_W * DMAP_H];          // BFS queue  (y<<16|x)
static int16_t  s_ca_px[DMAP_H][DMAP_W];            // BFS parent col
static int16_t  s_ca_py[DMAP_H][DMAP_W];            // BFS parent row

static void collect_leaves(int idx) {
    if (s_bsp[idx].lc == -1) {
        if (s_leaf_n < MAX_BSP_NODES) s_leaves[s_leaf_n++] = idx;
        return;
    }
    collect_leaves(s_bsp[idx].lc);
    collect_leaves(s_bsp[idx].rc);
}

static void bsp_split(int idx, int depth, uint32_t* rng) {
    BSPNode* n = &s_bsp[idx];
    n->lc = n->rc = -1;

    bool can_w = n->w >= 2 * s_bsp_min_part;
    bool can_h = n->h >= 2 * s_bsp_min_part;

    if (s_bsp_n + 2 > MAX_BSP_NODES || depth >= s_bsp_max_depth || (!can_w && !can_h)) {
        // Leaf — place a room inside the partition
        int span_w = n->w - 2 * ROOM_MARGIN;
        int span_h = n->h - 2 * ROOM_MARGIN;
        if (span_w < MIN_ROOM) span_w = MIN_ROOM;
        if (span_h < MIN_ROOM) span_h = MIN_ROOM;

        int rw = MIN_ROOM + (int)(rng_next(rng) % (unsigned)(span_w - MIN_ROOM + 1));
        int rh = MIN_ROOM + (int)(rng_next(rng) % (unsigned)(span_h - MIN_ROOM + 1));

        int rx_off = ROOM_MARGIN
                   + (int)(rng_next(rng) % (unsigned)(n->w - 2*ROOM_MARGIN - rw + 1));
        int ry_off = ROOM_MARGIN
                   + (int)(rng_next(rng) % (unsigned)(n->h - 2*ROOM_MARGIN - rh + 1));

        n->rx  = n->x + rx_off;
        n->ry  = n->y + ry_off;
        n->rw  = rw;
        n->rh  = rh;
        n->rcx = n->rx + rw / 2;
        n->rcy = n->ry + rh / 2;
        return;
    }

    // Split the longer axis
    bool split_w = can_w && (!can_h || n->w >= n->h);
    int lc = s_bsp_n++, rc = s_bsp_n++;
    n->lc = lc; n->rc = rc;

    if (split_w) {
        int range = n->w - 2 * s_bsp_min_part;
        int split = s_bsp_min_part + (range > 0 ? (int)(rng_next(rng) % (unsigned)range) : 0);
        s_bsp[lc] = { n->x,         n->y, split,        n->h, -1, -1 };
        s_bsp[rc] = { n->x + split, n->y, n->w - split, n->h, -1, -1 };
    } else {
        int range = n->h - 2 * s_bsp_min_part;
        int split = s_bsp_min_part + (range > 0 ? (int)(rng_next(rng) % (unsigned)range) : 0);
        s_bsp[lc] = { n->x, n->y,         n->w, split,        -1, -1 };
        s_bsp[rc] = { n->x, n->y + split, n->w, n->h - split, -1, -1 };
    }

    bsp_split(lc, depth + 1, rng);
    bsp_split(rc, depth + 1, rng);

    // Propagate left child's centre up (corridor fallback)
    n->rcx = s_bsp[lc].rcx;
    n->rcy = s_bsp[lc].rcy;
}

static void carve_rect(DungeonMap* dmap, int x, int y, int w, int h, uint8_t tile) {
    if (tile != DNG_WALL) { if (w < 1) w = 1; if (h < 1) h = 1; }
    for (int dy = 0; dy < h; dy++)
        for (int dx = 0; dx < w; dx++) {
            int tx = x + dx, ty = y + dy;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// Oblique-projection parallelogram: row r shifts left by r tiles going down.
static void carve_parallelogram(DungeonMap* dmap, int x, int y, int w, int h, uint8_t tile) {
    if (tile != DNG_WALL) { if (w < 1) w = 1; if (h < 1) h = 1; }
    for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++) {
            int tx = x - r + c, ty = y + r;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// L-shaped corridor: horizontal leg at y1, vertical leg at x2.
static void carve_corridor(DungeonMap* dmap, int x1, int y1, int x2, int y2, int w = CORR_W) {
    if (x1 > x2) { int t; t=x1;x1=x2;x2=t; t=y1;y1=y2;y2=t; }
    carve_rect(dmap, x1, y1, x2 - x1 + w, w, DNG_FLOOR);
    int miny = y1 < y2 ? y1 : y2;
    int maxy = y1 > y2 ? y1 : y2;
    carve_rect(dmap, x2, miny, w, maxy - miny + w, DNG_FLOOR);
}

// Oblique L-shaped corridor for stonehenge-style dungeons:
// horizontal leg is a flat rectangle, vertical leg is a parallelogram
// (each row going down shifts left by 1 — matching oblique projection).
static void carve_oblique_corridor(DungeonMap* dmap, int x1, int y1, int x2, int y2) {
    if (x1 > x2) { int t; t=x1;x1=x2;x2=t; t=y1;y1=y2;y2=t; }
    // Horizontal leg — flat
    carve_rect(dmap, x1, y1, x2 - x1 + CORR_W, CORR_W, DNG_FLOOR);
    // Vertical leg — oblique parallelogram
    int miny = y1 < y2 ? y1 : y2;
    int maxy = y1 > y2 ? y1 : y2;
    carve_parallelogram(dmap, x2, miny, CORR_W, maxy - miny + CORR_W, DNG_FLOOR);
}

// ── Room-carving generator (river-style for caves and giant trees) ────────

static void paint_room_brush(DungeonMap* dmap, int ix, int iy, int room_rx, int room_ry) {
    for (int by = -room_ry; by <= room_ry; by++) {
        for (int bx = -room_rx; bx <= room_rx; bx++) {
            float nx = (room_rx > 0) ? (float)bx / room_rx : 0;
            float ny = (room_ry > 0) ? (float)by / room_ry : 0;
            if (nx*nx + ny*ny > 1.0f) continue;
            int px = ix + bx, py = iy + by;
            if (px >= 1 && px < DMAP_W-1 && py >= 1 && py < DMAP_H-1)
                dmap->tiles[py][px] = DNG_FLOOR;
        }
    }
}

static void paint_passage_brush(DungeonMap* dmap, int ix, int iy, int passage_w) {
    int half = passage_w / 2;
    for (int by = -half; by <= half; by++) {
        for (int bx = -half; bx <= half; bx++) {
            int px = ix + bx, py = iy + by;
            if (px >= 1 && px < DMAP_W-1 && py >= 1 && py < DMAP_H-1)
                dmap->tiles[py][px] = DNG_FLOOR;
        }
    }
}

static void march_room_path(DungeonMap* dmap, int sx, int sy,
                            float dir_x, float dir_y,
                            unsigned int seed,
                            int max_steps,
                            int jitter_range,
                            int room_min_rx, int room_max_rx,
                            int room_min_ry, int room_max_ry,
                            int passage_w,
                            int depth) {
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    int steps = 0;
    float smooth_j = 0.0f;
    int step_counter = 0;

    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(seed >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 2 || rx >= DMAP_W-2) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 2) ry = 2;
            if (ry >= DMAP_H-2) ry = DMAP_H - 3;
        } else {
            ry += sign_y;
            if (ry < 2 || ry >= DMAP_H-2) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 2) rx = 2;
            if (rx >= DMAP_W-2) rx = DMAP_W - 3;
        }

        seed = seed * 1664525u + 1013904223u;
        int room_rx = room_min_rx + (int)((seed >> 16) % (unsigned)(room_max_rx - room_min_rx + 1));
        seed = seed * 1664525u + 1013904223u;
        int room_ry = room_min_ry + (int)((seed >> 16) % (unsigned)(room_max_ry - room_min_ry + 1));

        paint_room_brush(dmap, rx, ry, room_rx, room_ry);

        seed = seed * 1664525u + 1013904223u;
        int passage_len = 3 + (int)((seed >> 16) % 6);
        for (int p = 1; p <= passage_len; p++) {
            if (primary_x) {
                paint_passage_brush(dmap, rx - sign_x * p, ry, passage_w);
            } else {
                paint_passage_brush(dmap, rx, ry - sign_y * p, passage_w);
            }
        }

        if (depth == 0 && step_counter > 3) {
            seed = seed * 1664525u + 1013904223u;
            if ((seed >> 16) % 1000 == 0) {
                seed = seed * 1664525u + 1013904223u;
                float side = ((seed >> 31) ? 1.0f : -1.0f);
                float offset = (30.0f + (float)((seed >> 16) % 40)) * 3.14159f / 180.0f;
                float base_angle = atan2f(dir_y, dir_x);
                float bangle = base_angle + side * offset;
                float bdx = cosf(bangle), bdy = sinf(bangle);

                seed = seed * 1664525u + 1013904223u;
                int blen = 15 + (int)((seed >> 16) % 25);

                march_room_path(dmap, rx, ry, bdx, bdy,
                                seed, blen, jitter_range,
                                room_min_rx/2, room_max_rx/2,
                                room_min_ry/2, room_max_ry/2,
                                passage_w/2 + 1, 1);
            }
        }
        step_counter++;
    }
}

static void carve_room_layout(DungeonMap* dmap, DungeonEntranceType type, unsigned int seed) {
    int num_paths;
    int room_min_rx, room_max_rx, room_min_ry, room_max_ry;
    int passage_w;

    if (type == DUNGEON_ENT_CAVE) {
        num_paths = 3 + (int)((seed >> 16) % 3);
        room_min_rx = 4; room_max_rx = 10;
        room_min_ry = 3; room_max_ry = 8;
        passage_w = 3;
    } else {
        num_paths = 2 + (int)((seed >> 16) % 2);
        room_min_rx = 5; room_max_rx = 12;
        room_min_ry = 4; room_max_ry = 10;
        passage_w = 3;
    }

    int sx = DMAP_W / 2;
    int sy = DMAP_H / 2;

    float base_angle = 0.0f;
    for (int p = 0; p < num_paths; p++) {
        seed = seed * 1664525u + 1013904223u;
        float angle = base_angle + ((float)p / num_paths) * 2.0f * 3.14159f;
        seed = seed * 1664525u + 1013904223u;
        angle += ((float)((int)(seed >> 16) % 40) - 20.0f) * 3.14159f / 180.0f;
        float dx = cosf(angle);
        float dy = sinf(angle);

        seed = seed * 1664525u + 1013904223u;
        int path_len = 20 + (int)((seed >> 16) % 30);

        paint_room_brush(dmap, sx, sy, room_max_rx, room_max_ry);

        march_room_path(dmap, sx, sy, dx, dy,
                        seed, path_len, 3,
                        room_min_rx, room_max_rx,
                        room_min_ry, room_max_ry,
                        passage_w, 0);
    }

    dmap->entry_x = sx;
    dmap->entry_y = sy;
    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    int exit_offset_x = (int)(cosf(base_angle) * 15);
    int exit_offset_y = (int)(sinf(base_angle) * 15);
    dmap->exit_x = sx + exit_offset_x;
    dmap->exit_y = sy + exit_offset_y;
    if (dmap->exit_x < 1) dmap->exit_x = 1;
    if (dmap->exit_x >= DMAP_W) dmap->exit_x = DMAP_W - 1;
    if (dmap->exit_y < 1) dmap->exit_y = 1;
    if (dmap->exit_y >= DMAP_H) dmap->exit_y = DMAP_H - 1;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_EXIT;
}

static void carve_hybrid_layout(DungeonMap* dmap, unsigned int seed) {
    int sx = DMAP_W / 2;
    int sy = DMAP_H / 2;

    seed = seed * 1664525u + 1013904223u;
    int num_paths = 4 + (int)((seed >> 16) % 3);

    for (int p = 0; p < num_paths; p++) {
        seed = seed * 1664525u + 1013904223u;
        float angle = ((float)p / num_paths) * 2.0f * 3.14159f;
        seed = seed * 1664525u + 1013904223u;
        angle += ((float)((int)(seed >> 16) % 30) - 15.0f) * 3.14159f / 180.0f;
        float dx = cosf(angle);
        float dy = sinf(angle);

        seed = seed * 1664525u + 1013904223u;
        int path_len = 15 + (int)((seed >> 16) % 20);

        march_room_path(dmap, sx, sy, dx, dy,
                       seed, path_len, 2,
                       4, 8, 3, 6,
                       2, 0);
    }

    int bsp_margin = 15;
    s_bsp_n = 1;
    memset(s_bsp, 0, sizeof(s_bsp));
    s_bsp[0] = { bsp_margin, bsp_margin,
                 DMAP_W - 2*bsp_margin - 1, DMAP_H - 2*bsp_margin - 1,
                 -1, -1 };
    bsp_split(0, 0, &seed);

    s_leaf_n = 0;
    collect_leaves(0);

    for (int i = 1; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        if (n->rx > 0 && n->ry > 0) {
            carve_rect(dmap, n->rx, n->ry, n->rw, n->rh, DNG_FLOOR);
        }
    }

    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* a = &s_bsp[s_leaves[i]];
        BSPNode* b = &s_bsp[s_leaves[(i + 1) % s_leaf_n]];
        if (a->rcx > 0 && b->rcx > 0) {
            carve_corridor(dmap, a->rcx, a->rcy, b->rcx, b->rcy);
        }
    }

    dmap->entry_x = sx;
    dmap->entry_y = sy;
    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    int exit_dist = 20;
    seed = seed * 1664525u + 1013904223u;
    float exit_angle = ((seed >> 16) % 100) * 3.14159f / 50.0f;
    dmap->exit_x = sx + (int)(cosf(exit_angle) * exit_dist);
    dmap->exit_y = sy + (int)(sinf(exit_angle) * exit_dist);
    if (dmap->exit_x < 1) dmap->exit_x = 1;
    if (dmap->exit_x >= DMAP_W) dmap->exit_x = DMAP_W - 1;
    if (dmap->exit_y < 1) dmap->exit_y = 1;
    if (dmap->exit_y >= DMAP_H) dmap->exit_y = DMAP_H - 1;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_EXIT;
}

// ── Decoration helpers ────────────────────────────────────────────────────

// True if any tile within a Chebyshev radius r of (cx,cy) is ENTRY or EXIT.
static bool near_special_tile(const DungeonMap* dmap, int cx, int cy, int r) {
    for (int dy = -r; dy <= r; dy++)
        for (int dx = -r; dx <= r; dx++) {
            int x = cx+dx, y = cy+dy;
            if (x < 0 || x >= DMAP_W || y < 0 || y >= DMAP_H) continue;
            uint8_t t = dmap->tiles[y][x];
            if (t == DNG_ENTRY || t == DNG_EXIT) return true;
        }
    return false;
}

// Count walkable tiles within a square radius.
static int count_floor_in_radius(const DungeonMap* dmap, int cx, int cy, int r) {
    int cnt = 0;
    for (int dy = -r; dy <= r; dy++)
        for (int dx = -r; dx <= r; dx++) {
            int x = cx+dx, y = cy+dy;
            if (x < 0 || x >= DMAP_W || y < 0 || y >= DMAP_H) continue;
            uint8_t t = dmap->tiles[y][x];
            if (t == DNG_FLOOR || t == DNG_ENTRY || t == DNG_EXIT) cnt++;
        }
    return cnt;
}

// Place a wall on a floor tile only if far enough from entry/exit.
static void place_obstacle(DungeonMap* dmap, int x, int y, int safety_r) {
    if (x < 1 || x >= DMAP_W-1 || y < 1 || y >= DMAP_H-1) return;
    if (dmap->tiles[y][x] != DNG_FLOOR) return;
    if (safety_r > 0 && near_special_tile(dmap, x, y, safety_r)) return;
    dmap->tiles[y][x] = DNG_WALL;
}

// ── CAVE: stalactite / stalagmite pillar clusters ─────────────────────────
static void decorate_cave(DungeonMap* dmap, uint32_t* rng) {
    int attempts = 300, placed = 0;
    while (attempts-- > 0 && placed < 60) {
        int x = 3 + (int)(rng_next(rng) % (DMAP_W - 6));
        int y = 3 + (int)(rng_next(rng) % (DMAP_H - 6));
        if (dmap->tiles[y][x] != DNG_FLOOR) continue;
        if (near_special_tile(dmap, x, y, 4)) continue;
        // Only place in fairly open areas so passages remain clear.
        if (count_floor_in_radius(dmap, x, y, 3) < 28) continue;
        dmap->tiles[y][x] = DNG_WALL;
        // 45% chance: grow into a small cluster.
        if (rng_next(rng) % 20 < 9) {
            int dx = (int)(rng_next(rng) % 3) - 1;
            int dy = (int)(rng_next(rng) % 3) - 1;
            place_obstacle(dmap, x+dx, y+dy, 4);
        }
        // 20% chance: one more tile.
        if (rng_next(rng) % 20 < 4) {
            int dx = (int)(rng_next(rng) % 3) - 1;
            int dy = (int)(rng_next(rng) % 3) - 1;
            place_obstacle(dmap, x+dx, y+dy, 4);
        }
        placed++;
    }
}

// ── LARGE TREE: gnarled root tendrils ────────────────────────────────────
static void decorate_large_tree(DungeonMap* dmap, uint32_t* rng) {
    for (int i = 0; i < 35; i++) {
        int x = 4 + (int)(rng_next(rng) % (DMAP_W - 8));
        int y = 4 + (int)(rng_next(rng) % (DMAP_H - 8));
        if (dmap->tiles[y][x] != DNG_FLOOR) continue;
        if (near_special_tile(dmap, x, y, 4)) continue;
        // Require an open area so we don't block narrow passages.
        if (count_floor_in_radius(dmap, x, y, 3) < 30) continue;

        // Short root tendril: 2-4 tiles in one axis direction.
        int len = 2 + (int)(rng_next(rng) % 3);
        int dir = rng_next(rng) % 4;
        static const int ddx[4] = {1,-1,0,0};
        static const int ddy[4] = {0,0,1,-1};
        for (int k = 0; k < len; k++) {
            int tx = x + ddx[dir]*k, ty = y + ddy[dir]*k;
            if (dmap->tiles[ty][tx] != DNG_FLOOR) break;
            if (count_floor_in_radius(dmap, tx, ty, 2) < 12) break;
            place_obstacle(dmap, tx, ty, 4);
        }
    }
}

// ── RUINS: Brogue-style room accretion ────────────────────────────────────
//
// 1. Place a seed room at map centre.
// 2. Collect perimeter: floor tiles that border a wall, plus outward direction.
// 3. Pick a random perimeter entry, generate a room stamp, align a "door" face
//    on the stamp with the perimeter point (optionally preceded by a hallway),
//    validate no overlap with existing floor, then carve hallway + stamp.
// 4. Repeat for N rooms, then place exit at the farthest floor tile from entry.

#define RNS_DIM   24      // max room-stamp dimension (tiles)
#define RNP_CAP   12000   // perimeter-entry buffer capacity
#define RNS_SCALE  4      // world tiles per logical stamp cell (each cell = 4×4 tiles)

struct RnPerim { int16_t x, y; int8_t dx, dy; };

static uint8_t s_rns[RNS_DIM][RNS_DIM];   // current room stamp (1 = floor)
static int     s_rns_w, s_rns_h;
static RnPerim s_rnp[RNP_CAP];             // dungeon perimeter entries
static int     s_rnp_n;

// Generate a random room stamp: rectangle (50%), L-shape (30%), cross (20%).
// Logical cells here — each cell is RNS_SCALE×RNS_SCALE tiles in world space.
static void rns_gen(uint32_t* rng) {
    memset(s_rns, 0, sizeof(s_rns));
    int shape = rng_next(rng) % 10;

    if (shape < 5) {
        // Rectangle: 3..6 cells = 12..24 world tiles per side
        s_rns_w = 3 + (int)(rng_next(rng) % 4);
        s_rns_h = 3 + (int)(rng_next(rng) % 4);
        for (int y = 0; y < s_rns_h; y++)
            for (int x = 0; x < s_rns_w; x++)
                s_rns[y][x] = 1;

    } else if (shape < 8) {
        // L-shape: body 3..5 cells, arm 2..4 cells
        int w1 = 3 + (int)(rng_next(rng) % 3);
        int h1 = 3 + (int)(rng_next(rng) % 3);
        int w2 = 2 + (int)(rng_next(rng) % 3);
        int h2 = 2 + (int)(rng_next(rng) % 3);
        int corner = rng_next(rng) % 4;

        int ox2, oy2;
        switch (corner) {
            case 0:  ox2 = 0;        oy2 = h1;       break;  // below-left
            case 1:  ox2 = w1 - w2;  oy2 = h1;       break;  // below-right
            case 2:  ox2 = w1;       oy2 = 0;         break;  // right-top
            default: ox2 = w1;       oy2 = h1 - h2;   break;  // right-bottom
        }
        if (ox2 < 0) ox2 = 0;
        if (oy2 < 0) oy2 = 0;

        s_rns_w = (w1 > ox2 + w2) ? w1 : ox2 + w2;
        s_rns_h = (h1 > oy2 + h2) ? h1 : oy2 + h2;
        if (s_rns_w > RNS_DIM) s_rns_w = RNS_DIM;
        if (s_rns_h > RNS_DIM) s_rns_h = RNS_DIM;

        for (int y = 0; y < h1 && y < s_rns_h; y++)
            for (int x = 0; x < w1 && x < s_rns_w; x++)
                s_rns[y][x] = 1;
        for (int y = oy2; y < oy2 + h2 && y < s_rns_h; y++)
            for (int x = ox2; x < ox2 + w2 && x < s_rns_w; x++)
                s_rns[y][x] = 1;

    } else {
        // Cross / plus: arm 2..4 cells, bar width 1..2 cells
        int arm = 2 + (int)(rng_next(rng) % 3);
        int hw  = 1 + (int)(rng_next(rng) % 2);

        int total = 2 * arm;
        if (total > RNS_DIM) total = RNS_DIM;
        s_rns_w = total; s_rns_h = total;

        int mid = total / 2;
        int hy0 = mid - hw / 2, hy1 = mid + (hw + 1) / 2;
        int hx0 = mid - hw / 2, hx1 = mid + (hw + 1) / 2;
        for (int y = hy0; y >= 0 && y < hy1 && y < total; y++)
            for (int x = 0; x < total; x++)
                s_rns[y][x] = 1;
        for (int x = hx0; x >= 0 && x < hx1 && x < total; x++)
            for (int y = 0; y < total; y++)
                s_rns[y][x] = 1;
    }
}

// Scan the dungeon and fill s_rnp with all floor→wall perimeter entries.
static void rnp_collect(const DungeonMap* dmap) {
    static const int DX[4] = { 0, 1, 0, -1 };
    static const int DY[4] = { -1, 0, 1,  0 };
    s_rnp_n = 0;
    for (int ty = 1; ty < DMAP_H - 1; ty++) {
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            for (int d = 0; d < 4; d++) {
                if (s_rnp_n >= RNP_CAP) break;
                int nx = tx + DX[d], ny = ty + DY[d];
                if (dmap->tiles[ny][nx] == DNG_WALL) {
                    s_rnp[s_rnp_n].x  = (int16_t)tx;
                    s_rnp[s_rnp_n].y  = (int16_t)ty;
                    s_rnp[s_rnp_n].dx = (int8_t)DX[d];
                    s_rnp[s_rnp_n].dy = (int8_t)DY[d];
                    s_rnp_n++;
                }
            }
        }
    }
}

// Try to attach s_rns to the dungeon. hlen = hallway tiles before the stamp.
// Returns true if a valid placement was found and carved.
static bool rn_attach(DungeonMap* dmap, int hlen, uint32_t* rng) {
    if (s_rnp_n == 0) return false;

    int door_sx[RNS_DIM * RNS_DIM], door_sy[RNS_DIM * RNS_DIM];

    int max_tries = (s_rnp_n < 200) ? s_rnp_n : 200;
    for (int attempt = 0; attempt < max_tries; attempt++) {
        int pi  = (int)(rng_next(rng) % (unsigned)s_rnp_n);
        int pdx = s_rnp[pi].dx, pdy = s_rnp[pi].dy;
        int px  = s_rnp[pi].x,  py  = s_rnp[pi].y;

        // Attachment point: RNS_SCALE world tiles per logical step.
        int attach_wx = px + pdx * RNS_SCALE * (1 + hlen);
        int attach_wy = py + pdy * RNS_SCALE * (1 + hlen);

        // Door candidates: stamp floor tiles whose "back" (–pdx, –pdy) is
        // outside the stamp or a wall tile within the stamp.
        int door_n = 0;
        for (int sy = 0; sy < s_rns_h; sy++) {
            for (int sx = 0; sx < s_rns_w; sx++) {
                if (!s_rns[sy][sx]) continue;
                int bx = sx - pdx, by = sy - pdy;
                bool back_open = (bx >= 0 && bx < s_rns_w &&
                                  by >= 0 && by < s_rns_h && s_rns[by][bx]);
                if (!back_open) {
                    door_sx[door_n] = sx;
                    door_sy[door_n] = sy;
                    door_n++;
                }
            }
        }
        if (door_n == 0) continue;

        int di  = (int)(rng_next(rng) % (unsigned)door_n);
        int dsx = door_sx[di], dsy = door_sy[di];

        // Stamp world origin: door cell (dsx, dsy) aligns with attachment point.
        int wo_x = attach_wx - dsx * RNS_SCALE;
        int wo_y = attach_wy - dsy * RNS_SCALE;

        // Validate: every stamp cell's RNS_SCALE×RNS_SCALE block must be
        // in-bounds and entirely wall (no overlap with existing floor).
        bool valid = true;
        for (int sy = 0; sy < s_rns_h && valid; sy++) {
            for (int sx = 0; sx < s_rns_w && valid; sx++) {
                if (!s_rns[sy][sx]) continue;
                int bx0 = wo_x + sx * RNS_SCALE;
                int by0 = wo_y + sy * RNS_SCALE;
                for (int by = 0; by < RNS_SCALE && valid; by++) {
                    for (int bx = 0; bx < RNS_SCALE && valid; bx++) {
                        int wx = bx0 + bx, wy = by0 + by;
                        if (wx < 2 || wx >= DMAP_W - 2 || wy < 2 || wy >= DMAP_H - 2)
                            { valid = false; }
                        else if (dmap->tiles[wy][wx] != DNG_WALL)
                            { valid = false; }
                    }
                }
            }
        }
        if (!valid) continue;

        // Carve hallway + doorway as a single rectangle (RNS_SCALE wide).
        int gl = RNS_SCALE * (1 + hlen);
        int gx, gy, gw, gh;
        if (pdx != 0) {
            gx = (pdx > 0) ? px + 1 : px - gl;
            gy = py;  gw = gl;  gh = RNS_SCALE;
        } else {
            gx = px;
            gy = (pdy > 0) ? py + 1 : py - gl;
            gw = RNS_SCALE;  gh = gl;
        }
        carve_rect(dmap, gx, gy, gw, gh, DNG_FLOOR);

        // Carve stamp: each logical cell → RNS_SCALE×RNS_SCALE tile block.
        for (int sy = 0; sy < s_rns_h; sy++)
            for (int sx = 0; sx < s_rns_w; sx++)
                if (s_rns[sy][sx])
                    carve_rect(dmap,
                               wo_x + sx * RNS_SCALE, wo_y + sy * RNS_SCALE,
                               RNS_SCALE, RNS_SCALE, DNG_FLOOR);

        return true;
    }
    return false;
}

// Seed room → accretion loop → exit at farthest floor tile.
static void carve_ruins_layout(DungeonMap* dmap, uint32_t* rng) {
    int cx = DMAP_W / 2, cy = DMAP_H / 2;

    // Seed room at centre.
    int seed_w = 14, seed_h = 14;
    carve_rect(dmap, cx - seed_w / 2, cy - seed_h / 2, seed_w, seed_h, DNG_FLOOR);

    dmap->entry_x = cx; dmap->entry_y = cy;
    dmap->tiles[cy][cx] = DNG_ENTRY;

    // Accretion loop.
    int num_rooms = 28 + (int)(rng_next(rng) % 13);  // 28..40
    for (int r = 0; r < num_rooms; r++) {
        rns_gen(rng);
        rnp_collect(dmap);
        int hlen = (int)(rng_next(rng) % 4);  // 0..3 hallway cells (0..12 world tiles)
        rn_attach(dmap, hlen, rng);
    }

    // Exit: farthest floor tile from entry by Manhattan distance.
    int best_dist = -1;
    dmap->exit_x = cx; dmap->exit_y = cy;
    for (int ty = 1; ty < DMAP_H - 1; ty++) {
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            if (tx == dmap->entry_x && ty == dmap->entry_y) continue;
            int dist = abs(tx - dmap->entry_x) + abs(ty - dmap->entry_y);
            if (dist > best_dist) {
                best_dist = dist;
                dmap->exit_x = tx;
                dmap->exit_y = ty;
            }
        }
    }

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── GRAVEYARD: roguelike square rooms ────────────────────────────────────
#define GY_MAX_ROOMS 24
struct GyRoom { int x, y, w, h; };
static GyRoom s_gy_rooms[GY_MAX_ROOMS];
static int    s_gy_room_n;

static void carve_graveyard_layout(DungeonMap* dmap, bool large, uint32_t* rng) {
    int area_w, area_h, num_target, room_min, room_max, hall_w;
    if (large) {
        area_w = 340; area_h = 250;
        num_target = 10 + (int)(rng_next(rng) % 5);  // 10–14
        room_min = 16; room_max = 24;
        hall_w   = 5;
    } else {
        area_w = 160; area_h = 120;
        num_target = 6  + (int)(rng_next(rng) % 4);  // 6–9
        room_min = 10; room_max = 16;
        hall_w   = 4;
    }

    int area_x = (DMAP_W - area_w) / 2;
    int area_y = (DMAP_H - area_h) / 2;
    int gap    = hall_w + 3;  // visible wall between rooms

    s_gy_room_n = 0;
    int attempts = num_target * 20;
    while (s_gy_room_n < num_target && attempts-- > 0) {
        int rw = room_min + (int)(rng_next(rng) % (unsigned)(room_max - room_min + 1));
        int rh = room_min + (int)(rng_next(rng) % (unsigned)(room_max - room_min + 1));
        if (area_w <= rw || area_h <= rh) continue;
        int rx = area_x + (int)(rng_next(rng) % (unsigned)(area_w - rw));
        int ry = area_y + (int)(rng_next(rng) % (unsigned)(area_h - rh));

        bool ok = true;
        for (int i = 0; i < s_gy_room_n && ok; i++) {
            GyRoom* r = &s_gy_rooms[i];
            if (rx < r->x + r->w + gap && rx + rw + gap > r->x &&
                ry < r->y + r->h + gap && ry + rh + gap > r->y)
                ok = false;
        }
        if (!ok) continue;

        s_gy_rooms[s_gy_room_n++] = {rx, ry, rw, rh};
        carve_rect(dmap, rx, ry, rw, rh, DNG_FLOOR);
    }

    // Sort rooms left-to-right so connections form a readable path.
    for (int i = 0; i < s_gy_room_n - 1; i++)
        for (int j = i + 1; j < s_gy_room_n; j++)
            if ((s_gy_rooms[j].x + s_gy_rooms[j].w/2) <
                (s_gy_rooms[i].x + s_gy_rooms[i].w/2)) {
                GyRoom t = s_gy_rooms[i]; s_gy_rooms[i] = s_gy_rooms[j]; s_gy_rooms[j] = t;
            }

    // Connect consecutive rooms with Z-shaped wall-to-wall corridors.
    // Each corridor exits through a room's wall face (not its centre) so
    // you see a clear doorway with solid wall on either side — matching
    // the classic roguelike look.
    int hw2 = hall_w / 2;
    for (int i = 0; i + 1 < s_gy_room_n; i++) {
        GyRoom* a = &s_gy_rooms[i];
        GyRoom* b = &s_gy_rooms[i + 1];
        int acx = a->x + a->w/2, acy = a->y + a->h/2;
        int bcx = b->x + b->w/2, bcy = b->y + b->h/2;
        int dx = bcx - acx, dy = bcy - acy;

        if (abs(dx) >= abs(dy)) {
            // Horizontal primary — rooms sorted left→right, so dx ≥ 0.
            int ax_wall = a->x + a->w;          // right face of A
            int bx_wall = b->x;                 // left  face of B
            int mid_x   = (ax_wall + bx_wall) / 2;

            int ay = acy - hw2;
            int by = bcy - hw2;
            if (ay < a->y)              ay = a->y;
            if (ay + hall_w > a->y + a->h) ay = a->y + a->h - hall_w;
            if (by < b->y)              by = b->y;
            if (by + hall_w > b->y + b->h) by = b->y + b->h - hall_w;

            // Leg 1: exit A's right wall horizontally to mid_x
            carve_rect(dmap, ax_wall, ay, mid_x - ax_wall + hall_w, hall_w, DNG_FLOOR);
            // Bend: vertical connector between ay and by
            int lo = (ay < by) ? ay : by;
            int hi = (ay > by) ? ay + hall_w : by + hall_w;
            carve_rect(dmap, mid_x, lo, hall_w, hi - lo, DNG_FLOOR);
            // Leg 2: from mid_x into B's left wall
            carve_rect(dmap, mid_x, by, bx_wall - mid_x + hall_w, hall_w, DNG_FLOOR);
        } else {
            // Vertical primary
            int ay_wall = (dy >= 0) ? a->y + a->h : a->y;
            int by_wall = (dy >= 0) ? b->y         : b->y + b->h;
            int mid_y   = (ay_wall + by_wall) / 2;

            int ax = acx - hw2;
            int bx = bcx - hw2;
            if (ax < a->x)              ax = a->x;
            if (ax + hall_w > a->x + a->w) ax = a->x + a->w - hall_w;
            if (bx < b->x)              bx = b->x;
            if (bx + hall_w > b->x + b->w) bx = b->x + b->w - hall_w;

            int lo = (ax < bx) ? ax : bx;
            int hi = (ax > bx) ? ax + hall_w : bx + hall_w;

            if (dy >= 0) {
                carve_rect(dmap, ax, ay_wall, hall_w, mid_y - ay_wall + hall_w, DNG_FLOOR);
                carve_rect(dmap, lo, mid_y,   hi - lo, hall_w, DNG_FLOOR);
                carve_rect(dmap, bx, mid_y,   hall_w, by_wall - mid_y + hall_w, DNG_FLOOR);
            } else {
                carve_rect(dmap, bx, by_wall, hall_w, mid_y - by_wall + hall_w, DNG_FLOOR);
                carve_rect(dmap, lo, mid_y,   hi - lo, hall_w, DNG_FLOOR);
                carve_rect(dmap, ax, mid_y,   hall_w, ay_wall - mid_y + hall_w, DNG_FLOOR);
            }
        }
    }

    if (s_gy_room_n == 0) return;
    GyRoom* first = &s_gy_rooms[0];
    GyRoom* last  = &s_gy_rooms[s_gy_room_n - 1];
    dmap->entry_x = first->x + first->w / 2;
    dmap->entry_y = first->y + first->h / 2;
    dmap->exit_x  = last->x  + last->w  / 2;
    dmap->exit_y  = last->y  + last->h  / 2;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── PYRAMID: simple node-and-leaf procgen ────────────────────────────────
//
// Every node is an identical rectangle.  Every leaf (corridor) starts at
// the centre of a node and goes in one cardinal direction (up/down/left/right)
// to place a new node at the far end.  No diagonals, no L-bends.

#define PYR_MAX_NODES 24

struct PyrNode { int cx, cy, parent, depth; };

static PyrNode s_pnodes[PYR_MAX_NODES];
static int     s_pnn;

static void carve_pyramid_layout(DungeonMap* dmap, uint32_t* rng) {
    s_pnn = 0;

    // Fixed node size (same for every room)
    const int RW = 12 + (int)(rng_next(rng) % 4);   // 12-15 tiles wide
    const int RH = 8  + (int)(rng_next(rng) % 3);   // 8-10 tiles tall
    const int CL = 8  + (int)(rng_next(rng) % 8);   // corridor length 8-15

    const int max_depth = 3 + (int)(rng_next(rng) % 2);  // 3-4 levels

    // ── 1. Build tree via BFS ─────────────────────────────────────────────
    // Root near map centre.
    s_pnodes[s_pnn++] = {
        DMAP_W/2 + (int)(rng_next(rng) % 20) - 10,
        DMAP_H/2 + (int)(rng_next(rng) % 20) - 10,
        -1, 0
    };

    int bfs[PYR_MAX_NODES];
    int bh = 0, bt = 0;
    bfs[bt++] = 0;

    // Each node tracks which 4 directions (0=U,1=D,2=L,3=R) it has used.
    uint8_t used[PYR_MAX_NODES] = {};   // bit 0=U, 1=D, 2=L, 3=R

    while (bh < bt && s_pnn < PYR_MAX_NODES - 1) {
        int ni  = bfs[bh++];
        PyrNode& nd = s_pnodes[ni];
        if (nd.depth >= max_depth) continue;

        // Try all 4 directions in a random order
        int dirs[4] = {0,1,2,3};
        for (int d = 3; d > 0; d--) {
            int j = rng_next(rng) % (d+1);
            int t = dirs[d]; dirs[d] = dirs[j]; dirs[j] = t;
        }

        // How many children this node should attempt: 2 for root, 1-2 otherwise
        int want = (nd.depth == 0) ? 2 : 1 + (int)(rng_next(rng) % 2);
        int got  = 0;

        for (int d = 0; d < 4 && got < want && s_pnn < PYR_MAX_NODES - 1; d++) {
            int dir = dirs[d];
            if (used[ni] & (1 << dir)) continue;

            // New node centre depends on direction
            int ncx = nd.cx, ncy = nd.cy;
            switch (dir) {
                case 0: ncy -= RH + CL; break;   // up
                case 1: ncy += RH + CL; break;   // down
                case 2: ncx -= RW + CL; break;   // left
                case 3: ncx += RW + CL; break;   // right
            }

            // Bounds check
            if (ncx - RW/2 < 3 || ncx + RW/2 >= DMAP_W-3) continue;
            if (ncy - RH/2 < 3 || ncy + RH/2 >= DMAP_H-3) continue;

            // Overlap check against all existing nodes
            bool ok = true;
            for (int k = 0; k < s_pnn && ok; k++)
                if (abs(s_pnodes[k].cx-ncx) < RW+CL/2 &&
                    abs(s_pnodes[k].cy-ncy) < RH+CL/2)
                    ok = false;
            if (!ok) continue;

            used[ni] |= (1 << dir);
            // Block the opposite direction in the new child so it can't double-back
            int opp[4] = {1,0,3,2};
            s_pnodes[s_pnn] = { ncx, ncy, ni, nd.depth + 1 };
            used[s_pnn]     = (1 << opp[dir]);
            bfs[bt++]       = s_pnn++;
            got++;
        }
    }

    // ── 2. Carve rooms (shifted 4 tiles up from node centre) ─────────────
    for (int i = 0; i < s_pnn; i++) {
        int rx = s_pnodes[i].cx - RW/2, ry = s_pnodes[i].cy - RH/2 - 4;
        carve_rect(dmap, rx, ry, RW, RH, DNG_FLOOR);
    }

    // ── 3. Carve corridors (straight, from parent centre to child centre) ─
    for (int i = 1; i < s_pnn; i++) {
        PyrNode& ch = s_pnodes[i];
        PyrNode& pa = s_pnodes[ch.parent];
        int cvx = pa.cx - CORR_W/2;
        int cvy = pa.cy - CORR_W/2;

        if (ch.cx == pa.cx) {
            // vertical — centred on shared cx
            int y0 = (pa.cy < ch.cy) ? pa.cy : ch.cy;
            int y1 = (pa.cy > ch.cy) ? pa.cy : ch.cy;
            carve_rect(dmap, cvx, y0, CORR_W, y1 - y0, DNG_FLOOR);
        } else {
            // horizontal — centred on shared cy
            int x0 = (pa.cx < ch.cx) ? pa.cx : ch.cx;
            int x1 = (pa.cx > ch.cx) ? pa.cx : ch.cx;
            carve_rect(dmap, x0, cvy, x1 - x0, CORR_W, DNG_FLOOR);
        }
    }

    // ── 4. Portals ────────────────────────────────────────────────────────
    int exit_i = 0;
    for (int i = 1; i < s_pnn; i++)
        if (s_pnodes[i].depth > s_pnodes[exit_i].depth) exit_i = i;

    // Portals at the geometric centre of their node's room (room is shifted -4 in y).
    dmap->entry_x = s_pnodes[0].cx;
    dmap->entry_y = s_pnodes[0].cy - 4;
    dmap->exit_x  = s_pnodes[exit_i].cx;
    dmap->exit_y  = s_pnodes[exit_i].cy - 4;

    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

static void ca_ensure_connectivity(DungeonMap* dmap, int entry_x, int entry_y); // forward decl

// ── OASIS: radial biome, 128×128 ─────────────────────────────────────────
//
// Algorithm:
//  1. Three organic growth rings (sinusoidally distorted annuli) centred on
//     a circular impassable water source.
//  2. Curved radial paths pierce every ring, connecting water-edge to outer wall.
//  3. Optional localised BSP micro-structures (small rooms) seeded in the
//     mid/outer ring at random angles.
//  4. Palm obstacle clusters scattered across ring floors.
//  5. Connectivity fix; entry at inner ring, exit at farthest walkable tile.
static void carve_oasis_layout(DungeonMap* dmap, uint32_t* rng) {
    int cx = DMAP_W/2, cy = DMAP_H/2;
    const int OAS_R = 64;   // half-side → 128×128 region

    // ── Layered organic growth rings ──────────────────────────────────────
    // Each ring is an annulus whose inner/outer edges are each independently
    // distorted by a sinusoid: edge(angle) = base ± amp*sin(freq*angle+phase).
    struct OasRing {
        float rmin, rmax;          // base radii
        float amp;                  // distortion amplitude (tiles)
        float freq;                 // angular frequency (cycles per 2π)
        float phase_in, phase_out;  // phase offsets for inner/outer edge
    };
    OasRing rings[3];

    // Base ring geometry
    rings[0] = { 10.f, 19.f, 2.2f, 5.f, 0.f, 0.f };   // inner shore
    rings[1] = { 22.f, 31.f, 2.8f, 4.f, 0.f, 0.f };   // mid ring
    rings[2] = { 34.f, 43.f, 3.0f, 6.f, 0.f, 0.f };   // outer ring

    // Randomise phase offsets so every seed looks different.
    for (int ri = 0; ri < 3; ri++) {
        rings[ri].phase_in  = (float)(rng_next(rng) % 628) * 0.01f;
        rings[ri].phase_out = (float)(rng_next(rng) % 628) * 0.01f;
    }

    for (int y = cy - OAS_R + 1; y < cy + OAS_R - 1; y++) {
        for (int x = cx - OAS_R + 1; x < cx + OAS_R - 1; x++) {
            if (x < 1 || x >= DMAP_W-1 || y < 1 || y >= DMAP_H-1) continue;
            float dx = (float)(x - cx), dy = (float)(y - cy);
            float r   = sqrtf(dx*dx + dy*dy);
            float ang = atan2f(dy, dx);
            for (int ri = 0; ri < 3; ri++) {
                float rlo = rings[ri].rmin + rings[ri].amp * sinf(rings[ri].freq * ang + rings[ri].phase_in);
                float rhi = rings[ri].rmax + rings[ri].amp * sinf(rings[ri].freq * ang + rings[ri].phase_out);
                if (r >= rlo && r < rhi) { dmap->tiles[y][x] = DNG_FLOOR; break; }
            }
        }
    }

    // ── Curved radial connective paths ────────────────────────────────────
    // Each path sweeps from just outside the water core (r=9) to the outer
    // ring edge (r=44) with a sinusoidal angular deviation — piercing all
    // ring walls to guarantee ring-to-ring connectivity.
    int num_paths = 4 + (int)(rng_next(rng) % 3);   // 4–6
    for (int p = 0; p < num_paths; p++) {
        float base_ang = (float)p / num_paths * 2.f * 3.14159f;
        base_ang += ((float)(rng_next(rng) % 40) - 20.f) * 3.14159f / 180.f;
        float curve_amp  = ((float)(rng_next(rng) % 30) - 15.f) * 3.14159f / 180.f;
        float curve_freq = 1.5f + (float)(rng_next(rng) % 20) * 0.1f;

        int steps = 80;
        for (int s = 0; s <= steps; s++) {
            float t   = (float)s / steps;
            float rad = 9.f + t * 35.f;   // r=9 → r=44
            float ang = base_ang + curve_amp * sinf(t * 3.14159f * curve_freq);
            int px = cx + (int)(cosf(ang) * rad);
            int py = cy + (int)(sinf(ang) * rad);
            // 2×2 brush minimum
            for (int dy2 = 0; dy2 <= 1; dy2++)
                for (int dx2 = 0; dx2 <= 1; dx2++) {
                    int tx = px+dx2, ty = py+dy2;
                    if (tx>=1&&tx<DMAP_W-1&&ty>=1&&ty<DMAP_H-1)
                        dmap->tiles[ty][tx] = DNG_FLOOR;
                }
        }
    }

    // ── Central water source (painted last — overwrites any floor) ────────
    for (int dy = -9; dy <= 9; dy++)
        for (int dx = -9; dx <= 9; dx++) {
            if (sqrtf((float)(dx*dx+dy*dy)) >= 8.5f) continue;
            int tx = cx+dx, ty = cy+dy;
            if (tx>=1&&tx<DMAP_W-1&&ty>=1&&ty<DMAP_H-1)
                dmap->tiles[ty][tx] = DNG_WALL;
        }

    // ── Localised BSP micro-structures (optional, 60 % chance each) ──────
    // Small rectangular rooms seeded at random angles in the mid/outer ring.
    int num_micro = 2 + (int)(rng_next(rng) % 3);   // 2–4 attempts
    for (int m = 0; m < num_micro; m++) {
        if (rng_next(rng) % 10 < 4) continue;   // 60 % chance
        float ang = (float)(rng_next(rng) % 628) * 0.01f;
        float rad = 24.f + (float)(rng_next(rng) % 16);   // r 24–40
        int mx = cx + (int)(cosf(ang) * rad);
        int my = cy + (int)(sinf(ang) * rad);
        int rw = 5 + (int)(rng_next(rng) % 5);   // 5–9
        int rh = 4 + (int)(rng_next(rng) % 4);   // 4–7
        carve_rect(dmap, mx - rw/2, my - rh/2, rw, rh, DNG_FLOOR);
    }

    // ── Palm obstacle clusters in ring floor areas ────────────────────────
    for (int k = 0; k < 25; k++) {
        int px = cx - OAS_R + 2 + (int)(rng_next(rng) % (OAS_R*2 - 4));
        int py = cy - OAS_R + 2 + (int)(rng_next(rng) % (OAS_R*2 - 4));
        float d = sqrtf((float)((px-cx)*(px-cx)+(py-cy)*(py-cy)));
        if (d < 10.f || d > 44.f) continue;
        if (dmap->tiles[py][px] != DNG_FLOOR) continue;
        if (near_special_tile(dmap, px, py, 3)) continue;
        dmap->tiles[py][px] = DNG_WALL;
        if (rng_next(rng) % 2 == 0) {
            const int off[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
            place_obstacle(dmap, px+off[rng_next(rng)%4][0], py+off[rng_next(rng)%4][1], 3);
        }
    }

    // ── Entry: inner ring accessible tile; exit: farthest walkable tile ───
    dmap->entry_x = cx; dmap->entry_y = cy - 12;
    if (dmap->tiles[cy-12][cx] == DNG_WALL) {
        for (int r = 1; r < 20; r++) {
            bool found = false;
            for (int dy = -r; dy <= r && !found; dy++)
                for (int dx = -r; dx <= r && !found; dx++) {
                    if (abs(dx)!=r && abs(dy)!=r) continue;
                    int tx = cx+dx, ty = cy-12+dy;
                    if (tx<1||tx>=DMAP_W-1||ty<1||ty>=DMAP_H-1) continue;
                    if (dmap->tiles[ty][tx] != DNG_WALL) {
                        dmap->entry_x = tx; dmap->entry_y = ty; found = true;
                    }
                }
            if (found) break;
        }
    }
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;

    ca_ensure_connectivity(dmap, dmap->entry_x, dmap->entry_y);

    int best = -1;
    dmap->exit_x = dmap->entry_x; dmap->exit_y = dmap->entry_y;
    for (int ty = 1; ty < DMAP_H-1; ty++)
        for (int tx = 1; tx < DMAP_W-1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            int d = abs(tx - dmap->entry_x) + abs(ty - dmap->entry_y);
            if (d > best) { best = d; dmap->exit_x = tx; dmap->exit_y = ty; }
        }

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── STONEHENGE: procgen logical maze projected into oblique space ─────────
//
// We generate a normal procgen maze in a hidden logical grid, add loops
// and chambers, then project it into world space with an oblique transform.
//
// Logical cell (u, v) -> world tile:
//
//     world_x = origin_x + u * SHG_STEP_X - v * SHG_SKEW_X
//     world_y = origin_y + v * SHG_STEP_Y
//

#define SHG_W       27
#define SHG_H       27
#define SHG_STEP_X   12
#define SHG_STEP_Y   12
#define SHG_SKEW_X   12 //keep propertional to step
#define SHG_STAMP_W  12
#define SHG_STAMP_H  12

enum { SHG_CELL_WALL = 0, SHG_CELL_FLOOR = 1 };

static bool shg_in_bounds(int x, int y) {
    return x >= 0 && x < SHG_W && y >= 0 && y < SHG_H;
}
static bool shg_is_inner_odd_cell(int x, int y) {
    return x > 0 && x < SHG_W-1 && y > 0 && y < SHG_H-1 && (x&1) && (y&1);
}
static void shg_clear(uint8_t grid[SHG_H][SHG_W]) {
    for (int y = 0; y < SHG_H; y++)
        for (int x = 0; x < SHG_W; x++)
            grid[y][x] = SHG_CELL_WALL;
}
static void shg_set_floor(uint8_t grid[SHG_H][SHG_W], int x, int y) {
    if (shg_in_bounds(x, y)) grid[y][x] = SHG_CELL_FLOOR;
}

static void shg_generate_maze(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    int stack_x[SHG_W * SHG_H], stack_y[SHG_W * SHG_H], top = 0;
    static const int DIRS[4][2] = {{0,-2},{2,0},{0,2},{-2,0}};
    shg_set_floor(grid, 1, 1);
    stack_x[top] = 1; stack_y[top] = 1; top++;
    while (top > 0) {
        int cx = stack_x[top-1], cy = stack_y[top-1];
        int order[4] = {0,1,2,3};
        for (int i = 3; i > 0; i--) {
            int j = (int)(rng_next(rng) % (unsigned)(i+1));
            int t = order[i]; order[i] = order[j]; order[j] = t;
        }
        bool moved = false;
        for (int i = 0; i < 4; i++) {
            int dx = DIRS[order[i]][0], dy = DIRS[order[i]][1];
            int nx = cx+dx, ny = cy+dy;
            if (!shg_is_inner_odd_cell(nx, ny)) continue;
            if (grid[ny][nx] == SHG_CELL_FLOOR) continue;
            shg_set_floor(grid, cx+dx/2, cy+dy/2);
            shg_set_floor(grid, nx, ny);
            stack_x[top] = nx; stack_y[top] = ny; top++;
            moved = true; break;
        }
        if (!moved) top--;
    }
}

static void shg_add_loops(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    int attempts = 18 + (int)(rng_next(rng) % 10);
    for (int i = 0; i < attempts; i++) {
        int x = 1 + (int)(rng_next(rng) % (SHG_W-2));
        int y = 1 + (int)(rng_next(rng) % (SHG_H-2));
        if (grid[y][x] != SHG_CELL_WALL) continue;
        bool horiz = (x>0 && x<SHG_W-1 && grid[y][x-1]==SHG_CELL_FLOOR && grid[y][x+1]==SHG_CELL_FLOOR);
        bool vert  = (y>0 && y<SHG_H-1 && grid[y-1][x]==SHG_CELL_FLOOR && grid[y+1][x]==SHG_CELL_FLOOR);
        if (horiz || vert) grid[y][x] = SHG_CELL_FLOOR;
    }
}

static void shg_add_chambers(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    int chambers = 4 + (int)(rng_next(rng) % 4);
    for (int c = 0; c < chambers; c++) {
        int cw = 3 + 2*(int)(rng_next(rng) % 3);
        int ch = 3 + 2*(int)(rng_next(rng) % 3);
        int x  = 1 + (int)(rng_next(rng) % (SHG_W - cw - 1));
        int y  = 1 + (int)(rng_next(rng) % (SHG_H - ch - 1));
        for (int yy = y; yy < y+ch; yy++)
            for (int xx = x; xx < x+cw; xx++)
                grid[yy][xx] = SHG_CELL_FLOOR;
    }
}

static void shg_force_outer_routes(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    (void)rng;
    for (int x = 1; x < SHG_W-1; x++) grid[1][x] = SHG_CELL_FLOOR;
    for (int y = 1; y < SHG_H-1; y++) grid[y][1] = SHG_CELL_FLOOR;
    int yb = SHG_H/2;
    for (int x = 3; x < SHG_W-3; x++) grid[yb][x] = SHG_CELL_FLOOR;
    int xb = SHG_W/2;
    for (int y = 3; y < SHG_H-3; y++) grid[y][xb] = SHG_CELL_FLOOR;
}

static void shg_logical_to_world(int origin_x, int origin_y,
                                 int u, int v, int* wx, int* wy) {
    *wx = origin_x + u * SHG_STEP_X - v * SHG_SKEW_X;
    *wy = origin_y + v * SHG_STEP_Y;
}

static void shg_rasterize(DungeonMap* dmap,
                          uint8_t grid[SHG_H][SHG_W],
                          int origin_x, int origin_y) {
    for (int v = 0; v < SHG_H; v++)
        for (int u = 0; u < SHG_W; u++)
            if (grid[v][u] == SHG_CELL_FLOOR)
                carve_parallelogram(dmap, origin_x + u*SHG_STEP_X - v*SHG_SKEW_X,
                                    origin_y + v*SHG_STEP_Y,
                                    SHG_STAMP_W, SHG_STAMP_H, DNG_FLOOR);
}

static void shg_pick_portals(uint8_t grid[SHG_H][SHG_W],
                             int* entry_u, int* entry_v,
                             int* exit_u,  int* exit_v) {
    int eu = 1, ev = 1;
    bool found = false;
    for (int y = 0; y < SHG_H && !found; y++)
        for (int x = 0; x < SHG_W; x++)
            if (grid[y][x] == SHG_CELL_FLOOR) { eu=x; ev=y; found=true; break; }
    int fu = eu, fv = ev, best = -1;
    for (int y = 0; y < SHG_H; y++)
        for (int x = 0; x < SHG_W; x++) {
            if (grid[y][x] != SHG_CELL_FLOOR) continue;
            int dist = abs(x-eu) + abs(y-ev);
            if (dist > best) { best=dist; fu=x; fv=y; }
        }
    *entry_u=eu; *entry_v=ev; *exit_u=fu; *exit_v=fv;
}

static void carve_stonehenge_layout(DungeonMap* dmap, uint32_t* rng) {
    uint8_t grid[SHG_H][SHG_W];
    shg_clear(grid);
    shg_generate_maze(grid, rng);
    shg_add_loops(grid, rng);

    int origin_x = 384, origin_y = 74;
    shg_rasterize(dmap, grid, origin_x, origin_y);

    int entry_u, entry_v, exit_u, exit_v;
    shg_pick_portals(grid, &entry_u, &entry_v, &exit_u, &exit_v);

    shg_logical_to_world(origin_x, origin_y, entry_u, entry_v,
                         &dmap->entry_x, &dmap->entry_y);
    shg_logical_to_world(origin_x, origin_y, exit_u, exit_v,
                         &dmap->exit_x, &dmap->exit_y);

    dmap->entry_x += 1; dmap->entry_y += 1;
    dmap->exit_x  += 1; dmap->exit_y  += 1;

    auto clamp_portal = [](int v, int lo, int hi) { return v<lo?lo:v>hi?hi:v; };
    dmap->entry_x = clamp_portal(dmap->entry_x, 1, DMAP_W-2);
    dmap->entry_y = clamp_portal(dmap->entry_y, 1, DMAP_H-2);
    dmap->exit_x  = clamp_portal(dmap->exit_x,  1, DMAP_W-2);
    dmap->exit_y  = clamp_portal(dmap->exit_y,  1, DMAP_H-2);

    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── STONEHENGE decoration: standing-stone rings in open chambers ──────────
// Scans the already-generated layout for open floor areas and stamps
// circular rings of wall tiles (standing stones) with the oblique skew
// that matches the stonehenge projection (-1 x per world y step).
static void decorate_stonehenge(DungeonMap* dmap, uint32_t* rng) {
    int placed   = 0;
    int attempts = 500;
    while (attempts-- > 0 && placed < 6) {
        int cx = 5 + (int)(rng_next(rng) % (DMAP_W - 10));
        int cy = 5 + (int)(rng_next(rng) % (DMAP_H - 10));
        if (dmap->tiles[cy][cx] != DNG_FLOOR) continue;
        if (near_special_tile(dmap, cx, cy, 6)) continue;
        // Require a reasonably open area so the ring has room to breathe.
        if (count_floor_in_radius(dmap, cx, cy, 5) < 50) continue;

        float ring_r    = 3.0f + (float)(rng_next(rng) % 3);  // 3..5 tiles
        int   num_stones = 7   + (int)(rng_next(rng) % 5);    // 7..11 stones
        int   ring_placed = 0;
        for (int s = 0; s < num_stones; s++) {
            float angle  = (float)s / (float)num_stones * 2.0f * 3.14159f;
            float raw_dx = cosf(angle) * ring_r;
            float raw_dy = sinf(angle) * ring_r;
            // Oblique skew: world-x shifts -1 per world-y (SHG_SKEW_X / SHG_STEP_Y = 1)
            int wx = cx + (int)(raw_dx - raw_dy);
            int wy = cy + (int)(raw_dy);
            if (wx < 2 || wx >= DMAP_W - 2 || wy < 2 || wy >= DMAP_H - 2) continue;
            if (dmap->tiles[wy][wx] != DNG_FLOOR) continue;
            if (near_special_tile(dmap, wx, wy, 2)) continue;
            dmap->tiles[wy][wx] = DNG_WALL;
            ring_placed++;
        }
        if (ring_placed >= 4) placed++;
    }

    // Restore portals in case any stone landed on them.
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── Portal clearing ───────────────────────────────────────────────────────
// Carves a 3×3 floor area around each portal so the player never spawns
// inside or immediately adjacent to a wall.
static void clear_portal_surroundings(DungeonMap* dmap) {
    int px[2] = { dmap->entry_x, dmap->exit_x  };
    int py[2] = { dmap->entry_y, dmap->exit_y  };
    for (int p = 0; p < 2; p++) {
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int tx = px[p] + dx, ty = py[p] + dy;
                if (tx < 0 || tx >= DMAP_W || ty < 0 || ty >= DMAP_H) continue;
                if (dmap->tiles[ty][tx] == DNG_WALL)
                    dmap->tiles[ty][tx] = DNG_FLOOR;
            }
        }
    }
    // Restore portal tiles in case they were adjacent to each other.
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── CELLULAR AUTOMATA: cave and tree interior generation ──────────────────
//
// Steps:
//  1. Seed the map with random wall/floor noise at a chosen fill ratio.
//  2. Run N passes of the standard cave CA rule:
//       cell → wall  if it has ≥ 5 wall neighbours (Moore); floor otherwise.
//  3. Connectivity post-pass: multi-source BFS from the main (entry-reachable)
//     region expands through ALL tiles.  The first non-main floor tile found
//     is the closest island; we trace the BFS parent chain back and carve
//     every wall along that path to floor.  Repeat until fully connected.

// Count wall tiles in the Moore neighbourhood; out-of-bounds counts as wall.
static int ca_wall_count(const DungeonMap* dmap, int x, int y) {
    int walls = 0;
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++) {
            if (dx == 0 && dy == 0) continue;
            int nx = x+dx, ny = y+dy;
            if (nx < 0 || nx >= DMAP_W || ny < 0 || ny >= DMAP_H) { walls++; continue; }
            if (dmap->tiles[ny][nx] != DNG_FLOOR) walls++;
        }
    return walls;
}

// One CA pass: cell becomes wall if it has ≥ wall_thresh wall neighbours.
static void ca_step(DungeonMap* dmap, int wall_thresh) {
    for (int y = 0; y < DMAP_H; y++) {
        for (int x = 0; x < DMAP_W; x++) {
            if (x == 0 || x == DMAP_W-1 || y == 0 || y == DMAP_H-1) {
                s_ca_buf[y][x] = DNG_WALL; continue;
            }
            int w = ca_wall_count(dmap, x, y);
            s_ca_buf[y][x] = (w >= wall_thresh) ? DNG_WALL : DNG_FLOOR;
        }
    }
    memcpy(dmap->tiles, s_ca_buf, sizeof(dmap->tiles));
}

// 4-connected flood fill from (sx,sy) marking reachable floor in s_ca_vis.
static void ca_flood_fill(const DungeonMap* dmap, int sx, int sy) {
    static const int DX[4] = {1,-1,0,0};
    static const int DY[4] = {0,0,1,-1};
    int head = 0, tail = 0;
    s_ca_vis[sy][sx] = 1;
    s_ca_bfs[tail++] = (sy << 16) | sx;
    while (head < tail) {
        int cell = s_ca_bfs[head++];
        int x = cell & 0xFFFF, y = (cell >> 16) & 0xFFFF;
        for (int d = 0; d < 4; d++) {
            int nx = x+DX[d], ny = y+DY[d];
            if (nx < 0 || nx >= DMAP_W || ny < 0 || ny >= DMAP_H) continue;
            if (dmap->tiles[ny][nx] == DNG_WALL) continue;
            if (s_ca_vis[ny][nx]) continue;
            s_ca_vis[ny][nx] = 1;
            s_ca_bfs[tail++] = (ny << 16) | nx;
        }
    }
}

// Connect all disconnected floor islands to the region containing (entry_x,entry_y).
// Uses multi-source BFS expanding through any tile so it finds the shortest tunnel.
static void ca_ensure_connectivity(DungeonMap* dmap, int entry_x, int entry_y) {
    static const int DX[4] = {1,-1,0,0};
    static const int DY[4] = {0,0,1,-1};

    // Guarantee entry tile is walkable.
    if (dmap->tiles[entry_y][entry_x] == DNG_WALL)
        dmap->tiles[entry_y][entry_x] = DNG_FLOOR;

    for (;;) {
        // Re-flood-fill to find the current main (entry-connected) region.
        memset(s_ca_vis, 0, sizeof(s_ca_vis));
        ca_flood_fill(dmap, entry_x, entry_y);

        // Locate the first unreachable floor tile (any island).
        int island_x = -1, island_y = -1;
        for (int y = 1; y < DMAP_H-1 && island_x < 0; y++)
            for (int x = 1; x < DMAP_W-1 && island_x < 0; x++)
                if (!s_ca_vis[y][x] && dmap->tiles[y][x] != DNG_WALL)
                    { island_x = x; island_y = y; }

        if (island_x < 0) break;   // fully connected

        // Multi-source BFS from every main-region tile through ALL tiles.
        // s_ca_buf reused as the per-BFS visited array (uint8_t, same dims).
        memset(s_ca_buf, 0, sizeof(s_ca_buf));
        int head = 0, tail = 0;
        for (int y = 1; y < DMAP_H-1; y++)
            for (int x = 1; x < DMAP_W-1; x++)
                if (s_ca_vis[y][x]) {
                    s_ca_buf[y][x] = 1;
                    s_ca_px[y][x]  = (int16_t)x;
                    s_ca_py[y][x]  = (int16_t)y;
                    s_ca_bfs[tail++] = (y << 16) | x;
                }

        int found = -1;
        while (head < tail) {
            int cell = s_ca_bfs[head++];
            int x = cell & 0xFFFF, y = (cell >> 16) & 0xFFFF;
            // Island reached: floor tile outside main region.
            if (!s_ca_vis[y][x] && dmap->tiles[y][x] != DNG_WALL)
                { found = cell; break; }
            for (int d = 0; d < 4; d++) {
                int nx = x+DX[d], ny = y+DY[d];
                if (nx < 0 || nx >= DMAP_W || ny < 0 || ny >= DMAP_H) continue;
                if (s_ca_buf[ny][nx]) continue;
                s_ca_buf[ny][nx] = 1;
                s_ca_px[ny][nx]  = (int16_t)x;
                s_ca_py[ny][nx]  = (int16_t)y;
                s_ca_bfs[tail++] = (ny << 16) | nx;
            }
        }

        if (found < 0) break;   // bounded map should never reach here

        // Carve the parent-chain path from island back to main region.
        // Use a 2×2 brush so the tunnel is at least 32 px wide (2 tiles).
        int px = found & 0xFFFF, py = (found >> 16) & 0xFFFF;
        while (!s_ca_vis[py][px]) {
            for (int dy2 = 0; dy2 <= 1; dy2++)
                for (int dx2 = 0; dx2 <= 1; dx2++) {
                    int tx = px+dx2, ty = py+dy2;
                    if (tx>=1&&tx<DMAP_W-1&&ty>=1&&ty<DMAP_H-1)
                        dmap->tiles[ty][tx] = DNG_FLOOR;
                }
            int nx = s_ca_px[py][px], ny = s_ca_py[py][px];
            px = nx; py = ny;
        }
    }
}

// Paint an irregular blob seed: a small core circle plus 3–5 randomly
// offset satellite lobes.  The overlapping circles produce a spiky amoeba
// shape that CA then smooths into an organic chamber (not a circle).
static void paint_cave_blob(DungeonMap* dmap, int cx, int cy, int base_r, uint32_t* rng) {
    // Core — half the declared radius so it doesn't dominate the shape.
    int core_r = base_r / 2 + 1;
    for (int dy = -core_r; dy <= core_r; dy++)
        for (int dx = -core_r; dx <= core_r; dx++) {
            if (dx*dx + dy*dy > core_r*core_r) continue;
            int tx = cx+dx, ty = cy+dy;
            if (tx>=1&&tx<DMAP_W-1&&ty>=1&&ty<DMAP_H-1)
                dmap->tiles[ty][tx] = DNG_FLOOR;
        }
    // Satellite lobes at random angles and distances.
    int num_lobes = 3 + (int)(rng_next(rng) % 3);   // 3–5
    for (int l = 0; l < num_lobes; l++) {
        float angle = (float)(rng_next(rng) % 628) * 0.01f;   // 0–2π
        int   dist  = base_r / 3 + (int)(rng_next(rng) % (base_r * 2 / 3 + 1));
        int   lx    = cx + (int)(cosf(angle) * dist);
        int   ly    = cy + (int)(sinf(angle) * dist);
        int   lr    = base_r / 4 + (int)(rng_next(rng) % (base_r / 2 + 1));
        lx = lx < 1 ? 1 : (lx >= DMAP_W-1 ? DMAP_W-2 : lx);
        ly = ly < 1 ? 1 : (ly >= DMAP_H-1 ? DMAP_H-2 : ly);
        for (int dy = -lr; dy <= lr; dy++)
            for (int dx = -lr; dx <= lr; dx++) {
                if (dx*dx + dy*dy > lr*lr) continue;
                int tx = lx+dx, ty = ly+dy;
                if (tx>=1&&tx<DMAP_W-1&&ty>=1&&ty<DMAP_H-1)
                    dmap->tiles[ty][tx] = DNG_FLOOR;
            }
    }
}

// ── CAVE CA generator — Guided Generation ────────────────────────────────
//
// Irregular blob seeds are placed along a winding spine and pre-connected
// with 2-tile corridors; CA then smooths the blobs into organic chambers.
static void carve_cave_ca(DungeonMap* dmap, uint32_t* rng) {
    int cx = DMAP_W/2, cy = DMAP_H/2;
    const int CAVE_R = 64;   // half-side → 128×128 tile region (matches tree)

    // ── Place seed chambers along a winding spine inside the 128×128 box ──
    const int MAX_CH = 10;
    int num_ch = 6 + (int)(rng_next(rng) % 4);   // 6–9 chambers
    int ch_x[MAX_CH], ch_y[MAX_CH], ch_r[MAX_CH];

    // Keep seeds 10 tiles from the box edge so blobs don't spill outside.
    int x0 = cx - CAVE_R + 10, x1 = cx + CAVE_R - 10;
    int sy = cy + (int)(rng_next(rng) % 41) - 20;

    for (int i = 0; i < num_ch; i++) {
        ch_x[i] = x0 + i * (x1 - x0) / (num_ch - 1);
        sy += (int)(rng_next(rng) % 41) - 20;
        if (sy < cy - CAVE_R + 10) sy = cy - CAVE_R + 10;
        if (sy > cy + CAVE_R - 10) sy = cy + CAVE_R - 10;
        ch_y[i] = sy;
        ch_r[i] = 8 + (int)(rng_next(rng) % 7);  // radius 8–14
    }

    // Carve irregular blob seeds.
    for (int i = 0; i < num_ch; i++)
        paint_cave_blob(dmap, ch_x[i], ch_y[i], ch_r[i], rng);

    // Sparse background noise confined to the 128×128 box.
    for (int y = cy - CAVE_R + 1; y < cy + CAVE_R - 1; y++)
        for (int x = cx - CAVE_R + 1; x < cx + CAVE_R - 1; x++)
            if (dmap->tiles[y][x] == DNG_WALL && rng_next(rng) % 100 < 22)
                dmap->tiles[y][x] = DNG_FLOOR;

    // Carve 2-wide L-shaped corridors between consecutive chambers.
    for (int i = 0; i+1 < num_ch; i++) {
        int ax = ch_x[i], ay = ch_y[i];
        int bx = ch_x[i+1], by = ch_y[i+1];
        int x0 = ax < bx ? ax : bx, x1 = ax < bx ? bx : ax;
        int y0 = ay < by ? ay : by, y1 = ay < by ? by : ay;
        // Horizontal leg at ay.
        for (int x = x0; x <= x1+1; x++) {
            if (x>=1&&x<DMAP_W-1&&ay  >=1&&ay  <DMAP_H-1) dmap->tiles[ay  ][x] = DNG_FLOOR;
            if (x>=1&&x<DMAP_W-1&&ay+1>=1&&ay+1<DMAP_H-1) dmap->tiles[ay+1][x] = DNG_FLOOR;
        }
        // Vertical leg at bx.
        for (int y = y0; y <= y1+1; y++) {
            if (bx  >=1&&bx  <DMAP_W-1&&y>=1&&y<DMAP_H-1) dmap->tiles[y][bx  ] = DNG_FLOOR;
            if (bx+1>=1&&bx+1<DMAP_W-1&&y>=1&&y<DMAP_H-1) dmap->tiles[y][bx+1] = DNG_FLOOR;
        }
    }

    // 4 CA smoothing passes — smooths circle edges without merging distant chambers.
    for (int i = 0; i < 4; i++) ca_step(dmap, 5);

    // Entry at first chamber.
    dmap->entry_x = ch_x[0]; dmap->entry_y = ch_y[0];
    if (dmap->tiles[ch_y[0]][ch_x[0]] == DNG_WALL) {
        for (int r = 1; r < 20; r++) {
            bool found = false;
            for (int dy = -r; dy <= r && !found; dy++)
                for (int dx = -r; dx <= r && !found; dx++) {
                    if (abs(dx) != r && abs(dy) != r) continue;
                    int tx = ch_x[0]+dx, ty = ch_y[0]+dy;
                    if (tx<1||tx>=DMAP_W-1||ty<1||ty>=DMAP_H-1) continue;
                    if (dmap->tiles[ty][tx] != DNG_WALL) {
                        dmap->entry_x = tx; dmap->entry_y = ty; found = true;
                    }
                }
            if (found) break;
        }
    }
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;

    ca_ensure_connectivity(dmap, dmap->entry_x, dmap->entry_y);

    // Exit: farthest walkable tile from entry by Manhattan distance.
    int best = -1;
    dmap->exit_x = dmap->entry_x; dmap->exit_y = dmap->entry_y;
    for (int ty = 1; ty < DMAP_H-1; ty++)
        for (int tx = 1; tx < DMAP_W-1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            int d = abs(tx - dmap->entry_x) + abs(ty - dmap->entry_y);
            if (d > best) { best = d; dmap->exit_x = tx; dmap->exit_y = ty; }
        }

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── LARGE TREE CA generator ───────────────────────────────────────────────
// Confines the initial noise to an oval mask so the interior looks like a
// hollow tree trunk; the CA then carves organic chambers inside it.
static void carve_tree_ca(DungeonMap* dmap, uint32_t* rng) {
    int cx = DMAP_W/2, cy = DMAP_H/2;
    const int TREE_R = 32;   // half-side of 64×64 tile region

    // Inside the 128×128 square: only 30 % walls → very open interior with
    // thin organic wall clusters after smoothing (many more cells visited
    // than the guided cave).  Outside: solid wall = bark border.
    for (int y = 1; y < DMAP_H-1; y++) {
        for (int x = 1; x < DMAP_W-1; x++) {
            if (abs(x - cx) >= TREE_R || abs(y - cy) >= TREE_R)
                dmap->tiles[y][x] = DNG_WALL;
            else
                dmap->tiles[y][x] = (rng_next(rng) % 100 < 50) ? DNG_WALL : DNG_FLOOR;
        }
    }

    // 3 smoothing passes — fewer passes preserve more open space.
    for (int i = 0; i < 3; i++) ca_step(dmap, 5);

    // Entry: nearest floor tile to centre.
    dmap->entry_x = cx; dmap->entry_y = cy;
    if (dmap->tiles[cy][cx] == DNG_WALL) {
        for (int r = 1; r < 40; r++) {
            bool found = false;
            for (int dy = -r; dy <= r && !found; dy++)
                for (int dx = -r; dx <= r && !found; dx++) {
                    if (abs(dx) != r && abs(dy) != r) continue;
                    int tx = cx+dx, ty = cy+dy;
                    if (tx<1||tx>=DMAP_W-1||ty<1||ty>=DMAP_H-1) continue;
                    if (dmap->tiles[ty][tx] != DNG_WALL) {
                        dmap->entry_x = tx; dmap->entry_y = ty; found = true;
                    }
                }
            if (found) break;
        }
    }
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;

    ca_ensure_connectivity(dmap, dmap->entry_x, dmap->entry_y);

    // Exit: farthest walkable tile from entry by Manhattan distance.
    int best = -1;
    dmap->exit_x = dmap->entry_x; dmap->exit_y = dmap->entry_y;
    for (int ty = 1; ty < DMAP_H-1; ty++)
        for (int tx = 1; tx < DMAP_W-1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            int d = abs(tx - dmap->entry_x) + abs(ty - dmap->entry_y);
            if (d > best) { best = d; dmap->exit_x = tx; dmap->exit_y = ty; }
        }

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── Public: generate ──────────────────────────────────────────────────────
void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type,
                      float difficulty, unsigned int seed) {
    memset(dmap->tiles,    DNG_WALL, sizeof(dmap->tiles));
    memset(dmap->explored, 0,        sizeof(dmap->explored));
    dmap->type       = type;
    dmap->difficulty = difficulty;

    uint32_t rng = seed ^ ((uint32_t)type * 0xBEEF1234u);

    // ── Cave: cellular automata + stalactite clusters ────────────────────
    if (type == DUNGEON_ENT_CAVE) {
        carve_cave_ca(dmap, &rng);
        decorate_cave(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Giant tree: cellular automata (oval mask) + root tendrils ────────
    if (type == DUNGEON_ENT_LARGE_TREE) {
        carve_tree_ca(dmap, &rng);
        decorate_large_tree(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Stonehenge: procgen oblique maze + standing-stone rings ──────────
    if (type == DUNGEON_ENT_STONEHENGE) {
        carve_stonehenge_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Pyramid: hand-crafted linear nested chambers ─────────────────────
    if (type == DUNGEON_ENT_PYRAMID) {
        carve_pyramid_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Oasis: BSP + circular pool (corridors carved after pool) ─────────
    if (type == DUNGEON_ENT_OASIS) {
        carve_oasis_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Graveyard SM: small roguelike rooms ──────────────────────────────
    if (type == DUNGEON_ENT_GRAVEYARD_SM) {
        carve_graveyard_layout(dmap, false, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Graveyard LG: large roguelike rooms ──────────────────────────────
    if (type == DUNGEON_ENT_GRAVEYARD_LG) {
        carve_graveyard_layout(dmap, true, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Ruins: Brogue-style room accretion ───────────────────────────────
    if (type == DUNGEON_ENT_RUINS) {
        carve_ruins_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── BSP-based types ───────────────────────────────────────────────────
    s_bsp_max_depth = 4;
    s_bsp_min_part  = MIN_PART;

    s_bsp_n = 1;
    memset(s_bsp, 0, sizeof(s_bsp));
    s_bsp[0] = { 1, 1, DMAP_W - 2, DMAP_H - 2, -1, -1 };
    bsp_split(0, 0, &rng);

    s_leaf_n = 0;
    collect_leaves(0);

    // Carve rooms
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        carve_rect(dmap, n->rx, n->ry, n->rw, n->rh, DNG_FLOOR);
    }

    // Connect consecutive rooms with corridors
    for (int i = 0; i + 1 < s_leaf_n; i++) {
        BSPNode* a = &s_bsp[s_leaves[i]];
        BSPNode* b = &s_bsp[s_leaves[i + 1]];
        carve_corridor(dmap, a->rcx, a->rcy, b->rcx, b->rcy);
    }

    // Entry in first room, exit in last room
    BSPNode* first = &s_bsp[s_leaves[0]];
    BSPNode* last  = &s_bsp[s_leaves[s_leaf_n - 1]];
    dmap->entry_x = first->rcx; dmap->entry_y = first->rcy;
    dmap->exit_x  = last->rcx;  dmap->exit_y  = last->rcy;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;

    clear_portal_surroundings(dmap);
}

// ── Public: orient portals to match overworld direction ───────────────────
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle) {
    // Direction vectors: exit side points along exit_angle, entry is opposite.
    float ex_dx = cosf(exit_angle), ex_dy = sinf(exit_angle);

    float cx = DMAP_W * 0.5f, cy = DMAP_H * 0.5f;

    // First pass: find best exit tile (highest projection onto exit direction).
    float best_exit_score  = -1e30f;
    int   best_exit_tx     = dmap->exit_x,  best_exit_ty  = dmap->exit_y;

    // Second pass: find best entry tile (highest projection onto entry = -exit direction),
    // excluding the tile already claimed for exit.
    float best_entry_score = -1e30f;
    int   best_entry_tx    = dmap->entry_x, best_entry_ty = dmap->entry_y;

    for (int ty = 0; ty < DMAP_H; ty++) {
        for (int tx = 0; tx < DMAP_W; tx++) {
            uint8_t t = dmap->tiles[ty][tx];
            if (t == DNG_WALL) continue;
            float rx = (float)tx - cx, ry = (float)ty - cy;
            float score = rx * ex_dx + ry * ex_dy;
            if (score > best_exit_score) {
                best_exit_score = score;
                best_exit_tx = tx; best_exit_ty = ty;
            }
        }
    }

    for (int ty = 0; ty < DMAP_H; ty++) {
        for (int tx = 0; tx < DMAP_W; tx++) {
            if (tx == best_exit_tx && ty == best_exit_ty) continue;
            uint8_t t = dmap->tiles[ty][tx];
            if (t == DNG_WALL) continue;
            float rx = (float)tx - cx, ry = (float)ty - cy;
            float score = -(rx * ex_dx + ry * ex_dy); // opposite direction
            if (score > best_entry_score) {
                best_entry_score = score;
                best_entry_tx = tx; best_entry_ty = ty;
            }
        }
    }

    // Clear old special tiles, then place at the new positions.
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;

    dmap->exit_x  = best_exit_tx;  dmap->exit_y  = best_exit_ty;
    dmap->entry_x = best_entry_tx; dmap->entry_y = best_entry_ty;

    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    clear_portal_surroundings(dmap);
}

// ── Public: player init ───────────────────────────────────────────────────
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit) {
    int spawn_tx = from_exit ? dmap->exit_x  : dmap->entry_x;
    int spawn_ty = from_exit ? dmap->exit_y  : dmap->entry_y;
    dp->x        = (float)(spawn_tx * DMAP_TILE);
    dp->y        = (float)(spawn_ty * DMAP_TILE + DMAP_TILE / 2 - 24);
    dp->speed    = 150.0f;
    dp->at_exit  = 0;
    dp->at_entry = 0;

    // Reset animation state on the shared player
    player->facing        = 0;
    player->facing_locked = 0;
    player->anim_step     = 0;
    player->anim_timer    = 0.0f;
    player->is_moving     = 0;
}

// ── Tile collision ─────────────────────────────────────────────────────────
static bool tile_solid(const void* map, float px, float py) {
    const DungeonMap* dmap = static_cast<const DungeonMap*>(map);

    int tx = (int)(px / DMAP_TILE);
    int ty = (int)(py / DMAP_TILE);
    if (tx < 0 || tx >= DMAP_W || ty < 0 || ty >= DMAP_H) return true;
    return dmap->tiles[ty][tx] == DNG_WALL;
}


// ── Public: player update ─────────────────────────────────────────────────
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, DungeonMap* dmap, bool noclip) {
    float anim_speed;

    float dx, dy;
    player_read_input(player, in, &dx, &dy);

    if (input_down(in, SDL_SCANCODE_LSHIFT))
        { dp->speed = 300.0f; anim_speed = 0.10f; }
    else
        { dp->speed = 150.0f; anim_speed = 0.20f; }

    if (dx != 0.0f || dy != 0.0f) {
        float nx = dp->x + dx * dp->speed * dt;
        float ny = dp->y + dy * dp->speed * dt;
        float px = dp->x, py = dp->y;
        if (noclip || can_occupy(dmap, nx, dp->y, tile_solid)) dp->x = nx;
        if (noclip || can_occupy(dmap, dp->x, ny, tile_solid)) dp->y = ny;
        if (dp->x == px && dp->y == py) player->is_moving = 0;
    }

    // detect which special tile (entry or exit) the player is standing on.
    float cx = dp->x + (HB_X1 + HB_X2) * 0.5f;
    float cy = dp->y + (HB_Y1 + HB_Y2) * 0.5f;
    int tx = (int)(cx / DMAP_TILE);
    int ty = (int)(cy / DMAP_TILE);
    if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H) {
        uint8_t t    = dmap->tiles[ty][tx];
        dp->at_exit  = (t == DNG_EXIT)  ? 1 : 0;
        dp->at_entry = (t == DNG_ENTRY) ? 1 : 0;
    } else {
        dp->at_exit  = 0;
        dp->at_entry = 0;
    }

    player_animate(player, dt, anim_speed);
    const int explored_r = 30;

    // ── Exploration: mark tiles near player as explored ──────────────────
    int ptx = (int)((dp->x + (HB_X1 + HB_X2) * 0.5f) / DMAP_TILE);
    int pty = (int)((dp->y + (HB_Y1 + HB_Y2) * 0.5f) / DMAP_TILE);
    for (int fdy = -explored_r; fdy <= explored_r; fdy++)
        for (int fdx = -230; fdx <= explored_r; fdx++) {
            if (fdx*fdx + fdy*fdy > explored_r*explored_r) continue;
            int ttx = ptx + fdx, tty = pty + fdy;
            if (ttx >= 0 && ttx < DMAP_W && tty >= 0 && tty < DMAP_H)
                dmap->explored[tty][ttx] = 1;
        }
}

// ── public: draw dungeon tiles ────────────────────────────────────────────
// Visibility model:
//   unexplored              → skip (black background shows through)
//   explored, outside FOV   → 30 % brightness (dim memory)
//   explored, FOV edge      → soft linear ramp 30 %→100 % over last 2 tiles
//   explored, full FOV      → 100 % brightness
void dungeon_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                  const Camera* cam, SDL_Renderer* ren, bool show_all) {
    float z   = cam->zoom;
    int   tsz = (int)(DMAP_TILE * z);
    if (tsz < 1) tsz = 1;

    int ci = (int)dmap->type;
    if (ci < 0 || ci > 7) ci = 0;
    const DngPalette& pal    = PALETTES[ci];
    const DngAscii&   ascii  = ASCII_CHARS[ci];
    int scale = tsz / 8;
    if (scale < 1) scale = 1;
    int coff = (tsz - 8 * scale) / 2;   // centering offset within tile

    // visible tile range
    int tx0 = (int)(cam->x / DMAP_TILE) - 1;
    int ty0 = (int)(cam->y / DMAP_TILE) - 1;
    int tx1 = tx0 + (int)(cam->screen_w / tsz) + 3;
    int ty1 = ty0 + (int)(cam->screen_h / tsz) + 3;
    if (tx0 < 0)       tx0 = 0;
    if (ty0 < 0)       ty0 = 0;
    if (tx1 > DMAP_W)  tx1 = DMAP_W;
    if (ty1 > DMAP_H)  ty1 = DMAP_H;

    for (int ty = ty0; ty < ty1; ty++) {
        for (int tx = tx0; tx < tx1; tx++) {
            if (!show_all && !dmap->explored[ty][tx]) continue;   // unexplored → black

            uint8_t tile = dmap->tiles[ty][tx];

            // Outline walls: skip wall tiles not adjacent to any open tile (all except stonehenge)
            if (tile == DNG_WALL && dmap->type != DUNGEON_ENT_STONEHENGE) {
                bool border = false;
                for (int ny = ty-1; ny <= ty+1 && !border; ny++)
                    for (int nx = tx-1; nx <= tx+1 && !border; nx++)
                        if (nx>=0 && nx<DMAP_W && ny>=0 && ny<DMAP_H)
                            if (dmap->tiles[ny][nx] != DNG_WALL)
                                border = true;
                if (!border) continue;
            }

            const SDL_Color* c;
            switch (tile) {
                case DNG_FLOOR: c = &pal.floor; break;
                case DNG_ENTRY: c = &pal.entry; break;
                case DNG_EXIT:  c = &pal.exit_;  break;
                default:        c = &pal.wall;  break;
            }
            int r = c->r;
            int g = c->g;
            int b = c->b;

            int sx = (int)((tx * DMAP_TILE - cam->x) * z);
            int sy = (int)((ty * DMAP_TILE - cam->y) * z);

            bool is_shg_wall = (dmap->type == DUNGEON_ENT_STONEHENGE) && (tile == DNG_WALL);
            int wall_h = is_shg_wall ? 2 * tsz : 0;
            SDL_Rect rect = { sx, sy - wall_h, tsz, tsz + wall_h };
            SDL_SetRenderDrawColor(ren, r, g, b, 255);
            SDL_RenderFillRect(ren, &rect);

            // ASCII char overlay
            char ch; Uint8 cr, cg, cb;
            switch (tile) {
                case DNG_FLOOR:
                    ch = ascii.floor;
                    cr = c->r / 2; cg = c->g / 2; cb = c->b / 2;
                    break;
                case DNG_ENTRY:
                    ch = '<';
                    cr = 255; cg = 240; cb = 80;
                    break;
                case DNG_EXIT:
                    ch = '>';
                    cr = 255; cg = 100; cb = 100;
                    break;
                default: // wall
                    ch = ascii.wall;
                    cr = (Uint8)((c->r + 255) / 2);
                    cg = (Uint8)((c->g + 255) / 2);
                    cb = (Uint8)((c->b + 255) / 2);
                    break;
            }
            char buf[2] = {ch, '\0'};
            draw_text(ren, buf, sx + coff, sy + coff, scale, cr, cg, cb);
        }
    }

    // Second pass (stonehenge only): redraw path tiles over tall wall extensions.
    if (dmap->type == DUNGEON_ENT_STONEHENGE) {
        for (int ty = ty0; ty < ty1; ty++) {
            for (int tx = tx0; tx < tx1; tx++) {
                uint8_t tile = dmap->tiles[ty][tx];
                if (tile == DNG_WALL) continue;
                if (!show_all && !dmap->explored[ty][tx]) continue;

                const SDL_Color* c;
                switch (tile) {
                    case DNG_ENTRY: c = &pal.entry; break;
                    case DNG_EXIT:  c = &pal.exit_;  break;
                    default:        c = &pal.floor;  break;
                }
                int sx = (int)((tx * DMAP_TILE - cam->x) * z);
                int sy = (int)((ty * DMAP_TILE - cam->y) * z);
                SDL_Rect rect = { sx, sy, tsz, tsz };
                SDL_SetRenderDrawColor(ren, c->r, c->g, c->b, 255);
                SDL_RenderFillRect(ren, &rect);

                char ch; Uint8 cr, cg, cb;
                switch (tile) {
                    case DNG_ENTRY: ch = '<'; cr=255; cg=240; cb=80; break;
                    case DNG_EXIT:  ch = '>'; cr=255; cg=100; cb=100; break;
                    default:
                        ch = ascii.floor;
                        cr = c->r / 2; cg = c->g / 2; cb = c->b / 2;
                        break;
                }
                char buf[2] = {ch, '\0'};
                draw_text(ren, buf, sx + coff, sy + coff, scale, cr, cg, cb);
            }
        }
    }
}

// ── Public: minimap overlay ───────────────────────────────────────────────
void dungeon_minimap_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                          SDL_Renderer* ren, int screen_w, int screen_h,
                          bool show_all) {
    // Scale so minimap fits within 80% of the smaller screen dimension.
    int max_dim = (screen_w < screen_h ? screen_w : screen_h) * 4 / 5;
    int step = 1;
    while (DMAP_W / step > max_dim || DMAP_H / step > max_dim)
        step++;

    int mw = DMAP_W / step;
    int mh = DMAP_H / step;
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    int ci = (int)dmap->type;
    if (ci < 0 || ci > 7) ci = 0;
    const DngPalette& pal = PALETTES[ci];

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    draw_nes_panel(ren, ox - 4, oy - 4, mw + 8, mh + 8);

    // Draw one pixel per explored dungeon tile only
    for (int ty = 0; ty < DMAP_H; ty += step) {
        for (int tx = 0; tx < DMAP_W; tx += step) {
            if (!show_all && !dmap->explored[ty][tx]) continue;
            uint8_t tile = dmap->tiles[ty][tx];
            const SDL_Color* c;
            switch (tile) {
                case DNG_FLOOR: c = &pal.floor; break;
                case DNG_ENTRY: c = &pal.entry; break;
                case DNG_EXIT:  c = &pal.exit_; break;
                default:        c = &pal.wall;  break;
            }
            SDL_SetRenderDrawColor(ren, c->r, c->g, c->b, 255);
            SDL_RenderDrawPoint(ren, ox + tx / step, oy + ty / step);
        }
    }

    // Player dot — 3×3 white square
    int px = ox + (int)(dplayer->x / DMAP_TILE) / step;
    int py = oy + (int)(dplayer->y / DMAP_TILE) / step;
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
    SDL_Rect dot = { px - 1, py - 1, 3, 3 };
    SDL_RenderFillRect(ren, &dot);

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}
