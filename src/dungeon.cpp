#include "dungeon.h"
#include "collision.h"
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
    for (int dy = 0; dy < h; dy++)
        for (int dx = 0; dx < w; dx++) {
            int tx = x + dx, ty = y + dy;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// Oblique-projection parallelogram: row r shifts left by r tiles going down.
static void carve_parallelogram(DungeonMap* dmap, int x, int y, int w, int h, uint8_t tile) {
    for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++) {
            int tx = x - r + c, ty = y + r;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// L-shaped corridor: horizontal leg at y1, vertical leg at x2.
static void carve_corridor(DungeonMap* dmap, int x1, int y1, int x2, int y2) {
    if (x1 > x2) { int t; t=x1;x1=x2;x2=t; t=y1;y1=y2;y2=t; }
    carve_rect(dmap, x1, y1, x2 - x1 + CORR_W, CORR_W, DNG_FLOOR);
    int miny = y1 < y2 ? y1 : y2;
    int maxy = y1 > y2 ? y1 : y2;
    carve_rect(dmap, x2, miny, CORR_W, maxy - miny + CORR_W, DNG_FLOOR);
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

// ── RUINS: grand cross-hallway + corner columns ───────────────────────────
static void decorate_ruins(DungeonMap* dmap, uint32_t* rng) {
    int hx = DMAP_W / 2 - 1;   // centre column (x=39)
    int hy = DMAP_H / 2 - 1;   // centre row    (y=39)

    // Cross-shaped grand hallway through the map.
    carve_rect(dmap,  2, hy, DMAP_W - 4, 3, DNG_FLOOR);  // east-west
    carve_rect(dmap, hx,  2, 3, DMAP_H - 4, DNG_FLOOR);  // north-south

    // Colonnade flanking the hallways (skip the crossing zone).
    int cross_lo = hx - 2, cross_hi = hx + 4;
    for (int px = 5; px < DMAP_W - 5; px += 6) {
        if (px >= cross_lo && px <= cross_hi) continue;
        place_obstacle(dmap, px, hy - 2, 3);
        place_obstacle(dmap, px, hy + 4, 3);
    }
    for (int py = 5; py < DMAP_H - 5; py += 6) {
        if (py >= cross_lo && py <= cross_hi) continue;
        place_obstacle(dmap, hx - 2, py, 3);
        place_obstacle(dmap, hx + 4, py, 3);
    }

    // Corner and mid-wall columns in each BSP room.
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        int rx = n->rx, ry = n->ry, rw = n->rw, rh = n->rh;
        if (rw < 6 || rh < 6) continue;

        int px1 = rx + 1, px2 = rx + rw - 2;
        int py1 = ry + 1, py2 = ry + rh - 2;
        place_obstacle(dmap, px1, py1, 3);
        place_obstacle(dmap, px2, py1, 3);
        place_obstacle(dmap, px1, py2, 3);
        place_obstacle(dmap, px2, py2, 3);

        // Extra mid-span columns for larger rooms.
        if (rw >= 12 && rh >= 12) {
            int pmx = (px1 + px2) / 2;
            int pmy = (py1 + py2) / 2;
            place_obstacle(dmap, pmx, py1, 3);
            place_obstacle(dmap, pmx, py2, 3);
            place_obstacle(dmap, px1, pmy, 3);
            place_obstacle(dmap, px2, pmy, 3);
        }

        // Occasional crumbled wall fragment.
        if (rw >= 10 && rh >= 8 && (rng_next(rng) % 3 == 0)) {
            int fx = rx + 3 + (int)(rng_next(rng) % (rw - 6));
            int fy = ry + 3 + (int)(rng_next(rng) % (rh - 6));
            int len = 2 + (int)(rng_next(rng) % 3);
            bool horiz = (rng_next(rng) % 2 == 0);
            for (int k = 0; k < len; k++) {
                if (horiz) place_obstacle(dmap, fx+k, fy,   3);
                else       place_obstacle(dmap, fx,   fy+k, 3);
            }
        }
    }

    // Grand hallway may have overwritten entry/exit — restore them.
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── GRAVEYARD SM: gravestone rows inside each room ────────────────────────
static void decorate_graveyard_sm(DungeonMap* dmap, uint32_t* rng) {
    (void)rng;
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        int rx = n->rx, ry = n->ry, rw = n->rw, rh = n->rh;
        if (rw < 6 || rh < 5) continue;

        // 1-tile headstones on a 2-tile grid.  Skip the centre row (rcy)
        // so the connecting corridor can always reach the room interior.
        for (int dy = 1; dy <= rh - 2; dy += 2) {
            if ((ry + dy) == n->rcy) continue;
            for (int dx = 2; dx <= rw - 3; dx += 2) {
                place_obstacle(dmap, rx+dx, ry+dy, 3);
            }
        }
    }
}

// ── GRAVEYARD LG: mausoleum crypt + denser grave sections ─────────────────
static void decorate_graveyard_lg(DungeonMap* dmap, uint32_t* rng) {
    (void)rng;
    // Pick the largest room for the central mausoleum.
    int largest_idx = 0, largest_area = 0;
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        int area = n->rw * n->rh;
        if (area > largest_area) { largest_area = area; largest_idx = i; }
    }

    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        int rx = n->rx, ry = n->ry, rw = n->rw, rh = n->rh;

        if (i == largest_idx && rw >= 9 && rh >= 9) {
            // Hollow inner rectangle = mausoleum walls, south gap for entry.
            int mx = rx + 2, my = ry + 2, mw = rw - 4, mh = rh - 4;
            for (int dy = 0; dy < mh; dy++) {
                for (int dx = 0; dx < mw; dx++) {
                    bool on_border = (dx==0 || dx==mw-1 || dy==0 || dy==mh-1);
                    if (!on_border) continue;
                    // Leave a 3-tile gap in the south wall for the door.
                    bool south_gap = (dy == mh-1 && abs(dx - mw/2) <= 1);
                    if (!south_gap)
                        place_obstacle(dmap, mx+dx, my+dy, 2);
                }
            }
        } else if (rw >= 5 && rh >= 4) {
            // Dense gravestone rows; keep rcy row as an aisle.
            for (int dy = 1; dy <= rh - 2; dy += 2) {
                if ((ry + dy) == n->rcy) continue;
                for (int dx = 1; dx <= rw - 2; dx += 2) {
                    place_obstacle(dmap, rx+dx, ry+dy, 2);
                }
            }
        }
    }
}

// ── PYRAMID: procgen nested-chamber layout (south-to-north spine) ────────
static void carve_pyramid_layout(DungeonMap* dmap, uint32_t* rng) {
    // Spine x-coordinate — slight per-seed shift so the pyramid is never
    // perfectly centred the same way twice.
    int cx = DMAP_W / 2 + (int)(rng_next(rng) % 9) - 4;   // 36..44

    // Layer sizes — varied per seed, bounded so everything fits in DMAP
    int vest_h    = 7  + (int)(rng_next(rng) % 4);   // 7..10
    int vest_w    = 22 + (int)(rng_next(rng) % 12);  // 22..33
    int gallery_h = 9  + (int)(rng_next(rng) % 6);   // 9..14
    int ant_h     = 7  + (int)(rng_next(rng) % 4);   // 7..10
    int ant_w     = 16 + (int)(rng_next(rng) % 8);   // 16..23
    int bg_h      = 8  + (int)(rng_next(rng) % 5);   // 8..12  (bent-gallery height)
    int bg_jog    = 7  + (int)(rng_next(rng) % 5);   // 7..11  (horizontal jog)
    int bg_off    = 3  + (int)(rng_next(rng) % 5);   // 3..7   (bent offset from cx)
    int bur_h     = 9  + (int)(rng_next(rng) % 5);   // 9..13
    int bur_w     = 32 + (int)(rng_next(rng) % 14);  // 32..45
    int alc_w     = 5  + (int)(rng_next(rng) % 4);   // 5..8
    int alc_h     = 3  + (int)(rng_next(rng) % 2);   // 3..4

    // Y positions computed bottom-to-top
    int entry_y = DMAP_H - 8;
    int vest_y  = entry_y - vest_h - 1;
    int gall_y  = vest_y  - gallery_h;
    int ant_y   = gall_y  - ant_h;
    int bg_top  = ant_y   - bg_h;
    int bur_y   = bg_top  - 3 - bur_h;     // 3-tile gap for horizontal jog
    if (bur_y < 3) { bur_y = 3; bur_h = bg_top - 3 - bur_y; if (bur_h < 5) bur_h = 5; }

    // Clamp x extents to map bounds
    int vest_x = cx - vest_w / 2;  if (vest_x < 2) vest_x = 2;
    int ant_x  = cx - ant_w  / 2;  if (ant_x  < 2) ant_x  = 2;
    int bur_x  = cx - bur_w  / 2;  if (bur_x  < 2) bur_x  = 2;
    if (vest_x + vest_w > DMAP_W - 2) vest_w = DMAP_W - 2 - vest_x;
    if (ant_x  + ant_w  > DMAP_W - 2) ant_w  = DMAP_W - 2 - ant_x;
    if (bur_x  + bur_w  > DMAP_W - 2) bur_w  = DMAP_W - 2 - bur_x;

    // ── Carve passages south → north ─────────────────────────────────────

    // Entry corridor
    carve_rect(dmap, cx-1, vest_y + vest_h, 3,
               entry_y - (vest_y + vest_h) + 1, DNG_FLOOR);

    // Vestibule
    carve_rect(dmap, vest_x, vest_y, vest_w, vest_h, DNG_FLOOR);

    // Dead-end alcoves
    int alc_y  = vest_y + (vest_h - alc_h) / 2;
    int east_x = vest_x + vest_w;
    int west_x = vest_x - alc_w;
    if (east_x + alc_w < DMAP_W - 1) carve_rect(dmap, east_x, alc_y, alc_w, alc_h, DNG_FLOOR);
    if (west_x >= 1)                  carve_rect(dmap, west_x, alc_y, alc_w, alc_h, DNG_FLOOR);

    // Grand gallery (vertical passage)
    carve_rect(dmap, cx-1, gall_y, 3, gallery_h + 1, DNG_FLOOR);

    // Antechamber
    carve_rect(dmap, ant_x, ant_y, ant_w, ant_h, DNG_FLOOR);

    // Bent gallery — leg 1: vertical north of antechamber
    int bg_spine = cx - bg_off;
    if (bg_spine < 2) bg_spine = 2;
    carve_rect(dmap, bg_spine - 1, bg_top + 3, 3, ant_y - (bg_top + 3), DNG_FLOOR);

    // Bent gallery — leg 2: westward horizontal jog
    int jog_wx = bg_spine - bg_jog;
    if (jog_wx < 2) jog_wx = 2;
    carve_rect(dmap, jog_wx, bg_top, bg_spine - jog_wx + 2, 3, DNG_FLOOR);

    // Bent gallery — leg 3: vertical north into burial chamber
    carve_rect(dmap, jog_wx, bur_y + bur_h,
               3, bg_top - (bur_y + bur_h) + 1, DNG_FLOOR);

    // Burial chamber
    carve_rect(dmap, bur_x, bur_y, bur_w, bur_h, DNG_FLOOR);

    // ── Pillar rows in burial chamber ─────────────────────────────────────
    int ps = 3 + (int)(rng_next(rng) % 3);   // pillar spacing 3..5
    for (int px = bur_x + 3; px <= bur_x + bur_w - 4; px += ps) {
        place_obstacle(dmap, px, bur_y + 2,           2);
        place_obstacle(dmap, px, bur_y + bur_h - 3,   2);
    }

    // Pillar pairs flanking antechamber corridor entry
    place_obstacle(dmap, ant_x + 2,           ant_y + 2,           2);
    place_obstacle(dmap, ant_x + 2,           ant_y + ant_h - 3,   2);
    place_obstacle(dmap, ant_x + ant_w - 3,   ant_y + 2,           2);
    place_obstacle(dmap, ant_x + ant_w - 3,   ant_y + ant_h - 3,   2);

    // ── Entry & exit set LAST ─────────────────────────────────────────────
    dmap->entry_x = cx;
    dmap->entry_y = entry_y;
    dmap->exit_x  = jog_wx + 1;
    dmap->exit_y  = bur_y + 2;
    if (dmap->exit_x >= DMAP_W) dmap->exit_x = DMAP_W - 2;

    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── OASIS: BSP rooms + circular pool, corridors carved after pool ─────────
static void carve_oasis_layout(DungeonMap* dmap, uint32_t* rng) {
    s_bsp_max_depth = 4;
    s_bsp_min_part  = MIN_PART;

    s_bsp_n = 1;
    memset(s_bsp, 0, sizeof(s_bsp));
    s_bsp[0] = { 1, 1, DMAP_W - 2, DMAP_H - 2, -1, -1 };
    bsp_split(0, 0, rng);
    s_leaf_n = 0;
    collect_leaves(0);

    // Carve BSP rooms first.
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        carve_rect(dmap, n->rx, n->ry, n->rw, n->rh, DNG_FLOOR);
    }

    int cx = DMAP_W / 2, cy = DMAP_H / 2;

    // Open a large circular clearing around the oasis centre.
    for (int dy = -10; dy <= 10; dy++) {
        for (int dx = -10; dx <= 10; dx++) {
            if (sqrtf((float)(dx*dx + dy*dy)) > 10.0f) continue;
            int tx = cx+dx, ty = cy+dy;
            if (tx >= 1 && tx < DMAP_W-1 && ty >= 1 && ty < DMAP_H-1)
                dmap->tiles[ty][tx] = DNG_FLOOR;
        }
    }

    // Central pool: impassable water (wall tiles) within radius 4.5.
    for (int dy = -5; dy <= 5; dy++) {
        for (int dx = -5; dx <= 5; dx++) {
            if (sqrtf((float)(dx*dx + dy*dy)) > 4.5f) continue;
            int tx = cx+dx, ty = cy+dy;
            if (tx >= 1 && tx < DMAP_W-1 && ty >= 1 && ty < DMAP_H-1)
                if (dmap->tiles[ty][tx] == DNG_FLOOR)
                    dmap->tiles[ty][tx] = DNG_WALL;
        }
    }

    // Corridors AFTER the pool — they will cut through pool edges if needed,
    // guaranteeing every room is reachable.
    for (int i = 0; i + 1 < s_leaf_n; i++) {
        BSPNode* a = &s_bsp[s_leaves[i]];
        BSPNode* b = &s_bsp[s_leaves[i + 1]];
        carve_corridor(dmap, a->rcx, a->rcy, b->rcx, b->rcy);
    }

    // Entry / exit in outermost rooms.
    BSPNode* first = &s_bsp[s_leaves[0]];
    BSPNode* last  = &s_bsp[s_leaves[s_leaf_n - 1]];
    dmap->entry_x = first->rcx; dmap->entry_y = first->rcy;
    dmap->exit_x  = last->rcx;  dmap->exit_y  = last->rcy;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;

    // Palm clusters scattered in the oasis ring (radius 6–22).
    for (int k = 0; k < 20; k++) {
        int px = 2 + (int)(rng_next(rng) % (DMAP_W - 4));
        int py = 2 + (int)(rng_next(rng) % (DMAP_H - 4));
        float d = sqrtf((float)((px-cx)*(px-cx) + (py-cy)*(py-cy)));
        if (d < 6.0f || d > 22.0f) continue;
        if (dmap->tiles[py][px] != DNG_FLOOR) continue;
        if (near_special_tile(dmap, px, py, 3)) continue;
        dmap->tiles[py][px] = DNG_WALL;
        // 50% chance: one neighbouring tile forms a small frond cluster.
        if (rng_next(rng) % 2 == 0) {
            const int offsets[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
            int dir = rng_next(rng) % 4;
            place_obstacle(dmap, px+offsets[dir][0], py+offsets[dir][1], 3);
        }
    }
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
#define SHG_STEP_X   4
#define SHG_STEP_Y   4
#define SHG_SKEW_X   4
#define SHG_STAMP_W  4
#define SHG_STAMP_H  4

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

    int origin_x = 104, origin_y = 5;
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

// ── Public: generate ──────────────────────────────────────────────────────
void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type,
                      float difficulty, unsigned int seed) {
    memset(dmap->tiles, DNG_WALL, sizeof(dmap->tiles));
    dmap->type       = type;
    dmap->difficulty = difficulty;

    uint32_t rng = seed ^ ((uint32_t)type * 0xBEEF1234u);

    // ── Organic cave: branching elliptical caverns + stalactite clusters ──
    if (type == DUNGEON_ENT_CAVE) {
        carve_room_layout(dmap, type, rng);
        decorate_cave(dmap, &rng);
        clear_portal_surroundings(dmap);
        return;
    }

    // ── Giant tree: large organic lobes + root tendrils ───────────────────
    if (type == DUNGEON_ENT_LARGE_TREE) {
        carve_room_layout(dmap, type, rng);
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

    // ── BSP-based types: tune depth/min_part per theme ───────────────────
    s_bsp_max_depth = 4;
    s_bsp_min_part  = MIN_PART;

    if (type == DUNGEON_ENT_RUINS) {
        // Fewer, larger rooms — feels like a roomy ancient structure.
        s_bsp_max_depth = 3;
        s_bsp_min_part  = 16;
    } else if (type == DUNGEON_ENT_GRAVEYARD_SM) {
        // Many small chambers — cramped, claustrophobic graveyard.
        s_bsp_max_depth = 5;
        s_bsp_min_part  = 10;
    }

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

    // Type-specific decoration using BSP room data (still valid in s_bsp/s_leaves)
    if      (type == DUNGEON_ENT_RUINS)        decorate_ruins(dmap, &rng);
    else if (type == DUNGEON_ENT_GRAVEYARD_SM) decorate_graveyard_sm(dmap, &rng);
    else if (type == DUNGEON_ENT_GRAVEYARD_LG) decorate_graveyard_lg(dmap, &rng);

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
                           float dt, const DungeonMap* dmap, bool noclip) {
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
}

// ── public: draw dungeon tiles ────────────────────────────────────────────
void dungeon_draw(const DungeonMap* dmap, const Camera* cam, SDL_Renderer* ren) {
    float z   = cam->zoom;
    int   tsz = (int)(DMAP_TILE * z);
    if (tsz < 1) tsz = 1;

    int ci = (int)dmap->type;
    if (ci < 0 || ci > 7) ci = 0;
    const DngPalette& pal = PALETTES[ci];

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
            const SDL_Color* c;
            switch (dmap->tiles[ty][tx]) {
                case DNG_FLOOR: c = &pal.floor; break;
                case DNG_ENTRY: c = &pal.entry; break;
                case DNG_EXIT:  c = &pal.exit_;  break;
                default:        c = &pal.wall;  break;
            }
            int sx = (int)((tx * DMAP_TILE - cam->x) * z);
            int sy = (int)((ty * DMAP_TILE - cam->y) * z);
            SDL_Rect r = { sx, sy, tsz, tsz };
            SDL_SetRenderDrawColor(ren, c->r, c->g, c->b, 255);
            SDL_RenderFillRect(ren, &r);
        }
    }
}
