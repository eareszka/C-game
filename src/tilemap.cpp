#include "tilemap.h"
#include "towns.h"
#include "castles.h"
#include <stdint.h>
#include <math.h>
#include <string.h>
#include <algorithm>
#include <unordered_map>
#include <vector>
#include <array>
#include <pthread.h>

// ---------------------------------------------------------------------------
// Embedded 8x8 bitmap glyphs — one byte per row, MSB = leftmost pixel
// With TILE_SIZE=32, each bit renders as a 4x4 block.
// ---------------------------------------------------------------------------
static const uint8_t glyph_grass[8]  = {0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00}; // '.'
static const uint8_t glyph_path[8]   = {0x00,0x00,0x00,0x18,0x18,0x08,0x10,0x00}; // ','
static const uint8_t glyph_tree[8]        = {0xFE,0xFE,0x18,0x18,0x18,0x18,0x18,0x18}; // 'T'
// Tall tree (two stacked tree tiles): top = canopy, bottom = trunk
static const uint8_t glyph_tall_tree_top[8] = {0x18,0x3C,0x7E,0xFF,0xFF,0x7E,0x18,0x18};
static const uint8_t glyph_tall_tree_bot[8] = {0x18,0x18,0x18,0x18,0x18,0x18,0x3C,0x66};
static const uint8_t glyph_water[8]  = {0x62,0x94,0x08,0x62,0x94,0x08,0x62,0x94}; // '~'
static const uint8_t glyph_cliff[8]      = {0x24,0x7E,0x24,0x24,0x7E,0x24,0x00,0x00}; // '#'
static const uint8_t glyph_rock[8]       = {0x3C,0x42,0x81,0x81,0x81,0x42,0x3C,0x00}; // 'o'
static const uint8_t glyph_cliff_edge[8] = {0xFF,0x00,0xFF,0x00,0xFF,0x00,0xFF,0xFF}; // horizontal strata
static const uint8_t glyph_sand[8]       = {0x00,0x08,0x00,0x40,0x00,0x10,0x00,0x02}; // sparse dots
static const uint8_t glyph_snow[8]       = {0x10,0x54,0x38,0xFE,0x38,0x54,0x10,0x00}; // snowflake
static const uint8_t glyph_wasteland[8]  = {0x00,0x24,0x00,0x92,0x00,0x48,0x00,0x00}; // sparse cracks
static const uint8_t glyph_lava[8]       = {0x10,0x38,0x7C,0xFE,0x7C,0x38,0x10,0x00}; // flame diamond
static const uint8_t glyph_meadow[8]     = {0x00,0x28,0x10,0x28,0x00,0x10,0x00,0x00}; // scattered flowers
static const uint8_t glyph_pond[8]       = {0x62,0x94,0x08,0x62,0x94,0x08,0x62,0x94}; // wavy water
static const uint8_t glyph_gold_ore[8]  = {0x08,0x1C,0x3E,0x7F,0x3E,0x1C,0x08,0x00}; // diamond gem
// Cliff face — side and corner glyphs share the same brown palette as cliff_edge.
// Side: vertical stripes (transposed strata), solid bottom row.
// SW corner: left half = vertical stripes, right half = horizontal stripes.
// SE corner: right half = vertical stripes, left half = horizontal stripes.
// NW inner corner (concave): upper-right = back face (horiz stripes), lower-left = side face (vert stripes).
// NE inner corner (concave): upper-left = back face (horiz stripes), lower-right = side face (vert stripes).
static const uint8_t glyph_cliff_side[8]      = {0xAA,0xAA,0xAA,0xAA,0xAA,0xAA,0xAA,0xFF};
static const uint8_t glyph_cliff_corner_sw[8] = {0xAF,0xA0,0xAF,0xA0,0xAF,0xA0,0xAF,0xFF};
static const uint8_t glyph_cliff_corner_se[8] = {0xFA,0x0A,0xFA,0x0A,0xFA,0x0A,0xFA,0xFF};
static const uint8_t glyph_cliff_corner_nw[8] = {0x00,0x0F,0x00,0x0F,0xAF,0xA0,0xAF,0xFF};
static const uint8_t glyph_cliff_corner_ne[8] = {0x00,0xF0,0x00,0xF0,0xFA,0x0A,0xFA,0xFF};
// Dungeon entrance: solid black rectangle (bg=black, glyph all-off so only bg shows)
static const uint8_t glyph_dungeon[8]         = {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00};
// Blueprint placeholder: bright magenta checkerboard — unmissable while designing
static const uint8_t glyph_blueprint[8]       = {0xAA,0x55,0xAA,0x55,0xAA,0x55,0xAA,0x55};

struct TileStyle {
    uint8_t bg_r, bg_g, bg_b;
    uint8_t fg_r, fg_g, fg_b;
    const uint8_t* glyph;
};

static const TileStyle tile_styles[] = {
    { 34,  85,  34,  100, 200, 100, glyph_grass  }, // TILE_GRASS
    {120, 100,  60,  180, 155,  90, glyph_path   }, // TILE_PATH
    {  0,  40,   0,    0, 140,   0, glyph_tree   }, // TILE_TREE
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_WATER  (blue ocean)
    { 50,  50,  50,  160, 160, 160, glyph_cliff  }, // TILE_CLIFF   elev 1
    { 75,  65,  55,  155, 135, 115, glyph_rock   }, // TILE_ROCK
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_RIVER  (blue, same as ocean)
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_HUB    (blue, same as ocean)
    { 75,  72,  68,  180, 178, 174, glyph_cliff  }, // TILE_CLIFF_2 elev 2
    {100,  95,  88,  195, 192, 186, glyph_cliff  }, // TILE_CLIFF_3 elev 3
    {125, 118, 108,  210, 206, 198, glyph_cliff  }, // TILE_CLIFF_4 elev 4
    {155, 145, 132,  225, 220, 212, glyph_cliff      }, // TILE_CLIFF_5   elev 5
    {100,  65,  25,  140,  90,  40, glyph_cliff_edge }, // TILE_CLIFF_EDGE_1
    { 90,  58,  22,  130,  82,  36, glyph_cliff_edge }, // TILE_CLIFF_EDGE_2
    { 80,  52,  20,  120,  74,  32, glyph_cliff_edge }, // TILE_CLIFF_EDGE_3
    { 70,  46,  18,  110,  66,  28, glyph_cliff_edge }, // TILE_CLIFF_EDGE_4
    { 60,  40,  16,  100,  58,  24, glyph_cliff_edge }, // TILE_CLIFF_EDGE_5
    {195, 165,  90,  215, 190, 120, glyph_sand      }, // TILE_SAND
    {220, 235, 255,  180, 210, 240, glyph_snow      }, // TILE_SNOW
    { 65,  55,  45,   90,  78,  65, glyph_wasteland }, // TILE_WASTELAND
    {180,  50,   0,  255, 140,   0, glyph_lava      }, // TILE_LAVA
    { 80, 160,  40,  255, 220,  50, glyph_meadow    }, // TILE_MEADOW
    { 30,  90, 200,   80, 160, 255, glyph_pond      }, // TILE_POND
    { 60,  55,  50,  255, 210,  40, glyph_gold_ore  }, // TILE_GOLD_ORE
    // Snow cliff variants — icy blue-grey rock, lighter at higher elevations
    {130, 160, 195,  190, 215, 240, glyph_cliff }, // TILE_CLIFF_SNOW_1  (24)
    {122, 152, 188,  182, 208, 235, glyph_cliff }, // TILE_CLIFF_SNOW_2  (25)
    {114, 144, 180,  174, 200, 228, glyph_cliff }, // TILE_CLIFF_SNOW_3  (26)
    {106, 136, 173,  166, 192, 221, glyph_cliff }, // TILE_CLIFF_SNOW_4  (27)
    { 98, 128, 165,  158, 184, 214, glyph_cliff }, // TILE_CLIFF_SNOW_5  (28)
    // Wasteland cliff variants — charred dark rock, slightly redder at higher elevations
    { 52,  38,  28,   80,  60,  44, glyph_cliff }, // TILE_CLIFF_WASTE_1 (29)
    { 60,  44,  32,   90,  68,  50, glyph_cliff }, // TILE_CLIFF_WASTE_2 (30)
    { 68,  50,  36,  100,  76,  56, glyph_cliff }, // TILE_CLIFF_WASTE_3 (31)
    { 76,  56,  40,  110,  84,  62, glyph_cliff }, // TILE_CLIFF_WASTE_4 (32)
    { 85,  62,  44,  120,  92,  68, glyph_cliff }, // TILE_CLIFF_WASTE_5 (33)
    // Side face — vertical strata, same brown gradient as the south-face edge tiles
    {100,  65,  25,  140,  90,  40, glyph_cliff_side }, // TILE_CLIFF_SIDE_1 (34)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_side }, // TILE_CLIFF_SIDE_2 (35)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_side }, // TILE_CLIFF_SIDE_3 (36)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_side }, // TILE_CLIFF_SIDE_4 (37)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_side }, // TILE_CLIFF_SIDE_5 (38)
    // SW outer corner
    {100,  65,  25,  140,  90,  40, glyph_cliff_corner_sw }, // TILE_CLIFF_CORNER_SW_1 (39)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_corner_sw }, // TILE_CLIFF_CORNER_SW_2 (40)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_corner_sw }, // TILE_CLIFF_CORNER_SW_3 (41)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_corner_sw }, // TILE_CLIFF_CORNER_SW_4 (42)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_corner_sw }, // TILE_CLIFF_CORNER_SW_5 (43)
    // SE outer corner
    {100,  65,  25,  140,  90,  40, glyph_cliff_corner_se }, // TILE_CLIFF_CORNER_SE_1 (44)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_corner_se }, // TILE_CLIFF_CORNER_SE_2 (45)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_corner_se }, // TILE_CLIFF_CORNER_SE_3 (46)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_corner_se }, // TILE_CLIFF_CORNER_SE_4 (47)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_corner_se }, // TILE_CLIFF_CORNER_SE_5 (48)
    // NW inner corner
    {100,  65,  25,  140,  90,  40, glyph_cliff_corner_nw }, // TILE_CLIFF_CORNER_NW_1 (49)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_corner_nw }, // TILE_CLIFF_CORNER_NW_2 (50)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_corner_nw }, // TILE_CLIFF_CORNER_NW_3 (51)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_corner_nw }, // TILE_CLIFF_CORNER_NW_4 (52)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_corner_nw }, // TILE_CLIFF_CORNER_NW_5 (53)
    // NE inner corner
    {100,  65,  25,  140,  90,  40, glyph_cliff_corner_ne }, // TILE_CLIFF_CORNER_NE_1 (54)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_corner_ne }, // TILE_CLIFF_CORNER_NE_2 (55)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_corner_ne }, // TILE_CLIFF_CORNER_NE_3 (56)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_corner_ne }, // TILE_CLIFF_CORNER_NE_4 (57)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_corner_ne }, // TILE_CLIFF_CORNER_NE_5 (58)
    // Dungeon entrance — solid black
    {  0,   0,   0,   0,   0,   0, glyph_dungeon          }, // TILE_DUNGEON           (59)
    // Blueprint placeholder — magenta checkerboard (towns)
    { 80,   0,  80, 255,   0, 255, glyph_blueprint        }, // TILE_BLUEPRINT         (60)
    // Village placeholder — orange/black checkerboard
    {  0,   0,   0, 255, 140,   0, glyph_blueprint        }, // TILE_VILLAGE_PLACEHOLDER (61)
    // Castle placeholder — black/white checkerboard
    {  0,   0,   0, 255, 255, 255, glyph_blueprint        }, // TILE_CASTLE_PLACEHOLDER  (62)
};

static const int NUM_TILE_STYLES = (int)(sizeof(tile_styles) / sizeof(tile_styles[0]));

// Shared between phase1 and phase2 — computed once after rivers are placed.
static bool  cliff_blocked[MAP_HEIGHT][MAP_WIDTH];
static float s_cliff_dir_x, s_cliff_dir_y, s_cliff_dir_len;
static float s_cliff_ref_x, s_cliff_ref_y;

// Hit / jitter state — defined here so tilemap_draw can access them
// Value is the SDL performance-counter timestamp when the jitter started.
// Using absolute start time (not a countdown) makes shake immune to dt spikes.
static const float JITTER_DUR = 0.22f; // seconds
static std::unordered_map<uint32_t, Uint64> s_tile_jitter;
static inline uint32_t tile_key(int x, int y) {
    return (uint32_t)y * MAP_WIDTH + (uint32_t)x;
}

// Pre-rendered tile texture cache — eliminates thousands of per-frame draw calls.
// Each entry is a TILE_SIZE×TILE_SIZE texture with the tile's bg+glyph baked in.
// Index matches TileId enum. Filled by tilemap_init_tile_cache().
static const int TILE_CACHE_SIZE = 63; // TILE_CASTLE_PLACEHOLDER + 1
static SDL_Texture* s_tile_tex[TILE_CACHE_SIZE] = {};
static SDL_Texture* s_tall_tree_top_tex = nullptr;
static SDL_Texture* s_tall_tree_bot_tex  = nullptr;

// ---------------------------------------------------------------------------

static bool in_bounds(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

// Simple deterministic LCG noise — returns 0..32767
static int tile_noise(int x, int y, int seed) {
    unsigned int n = (unsigned int)(x * 1619 + y * 31337 + seed * 3571);
    n = (n ^ (n >> 13)) * 1664525u + 1013904223u;
    return (int)((n >> 16) & 0x7FFF);
}

// Place `count` tiles of `type` on GRASS cells, seeded RNG
static void scatter(Tilemap* map, int type, int count, unsigned int seed) {
    for (int i = 0; i < count; i++) {
        seed = seed * 1664525u + 1013904223u;
        int x = 1 + (int)((seed >> 16) % (MAP_WIDTH  - 2));
        seed = seed * 1664525u + 1013904223u;
        int y = 1 + (int)((seed >> 16) % (MAP_HEIGHT - 2));
        if (map->tiles[y][x] == TILE_GRASS)
            map->tiles[y][x] = type;
    }
}

// Paints a filled circle brush at (ix, iy), skipping the guard zone.
static void paint_river_brush(Tilemap* map, int ix, int iy, int brush_r,
                              int guard_cx, int guard_cy, int guard_r)
{
    for (int by = -brush_r; by <= brush_r; by++) {
        for (int bx = -brush_r; bx <= brush_r; bx++) {
            if (bx*bx + by*by > brush_r*brush_r) continue;
            int px = ix + bx, py = iy + by;
            if (!in_bounds(px, py)) continue;
            if (abs(px - guard_cx) <= guard_r && abs(py - guard_cy) <= guard_r) continue;
            map->tiles[py][px] = TILE_RIVER;
        }
    }
}

// March a river from (sx,sy) in direction (dir_x,dir_y).
// Always advances 1 tile per step along the primary axis — guarantees the
// river reaches the map edge. Perpendicular axis gets ±4 random jitter,
// matching the style of the guaranteed west river.
// depth=0: main river (can spawn branches), depth=1: branch (no further branching)
static void march_river(Tilemap* map, int sx, int sy,
                        float dir_x, float dir_y,
                        unsigned int seed,
                        int guard_cx, int guard_cy, int guard_r,
                        int brush_r,
                        int max_steps,
                        int jitter_range,
                        int depth)
{
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float base_angle = atan2f(dir_y, dir_x);

    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    int steps = 0;
    float smooth_j = 0.0f;

    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(seed >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 0 || rx >= MAP_WIDTH) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 1)             ry = 1;
            if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT - 2;
        } else {
            ry += sign_y;
            if (ry < 0 || ry >= MAP_HEIGHT) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 1)            rx = 1;
            if (rx >= MAP_WIDTH-1) rx = MAP_WIDTH - 2;
        }

        paint_river_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r);

        // Very rarely spawn a thin branch off this river (main rivers only)
        if (depth == 0 && (seed >> 16) % 1000 == 0) {
            seed = seed * 1664525u + 1013904223u;
            // Branch veers off at ±25°–65° from the river's base direction
            float side    = ((seed >> 31) ? 1.0f : -1.0f);
            float offset  = (25.0f + (float)((seed >> 16) % 40)) * 3.14159f / 180.0f;
            float bangle  = base_angle + side * offset;
            float bdx = cosf(bangle), bdy = sinf(bangle);

            seed = seed * 1664525u + 1013904223u;
            int blen = 150 + (int)((seed >> 16) % 250); // 150..399 steps

            march_river(map, rx, ry, bdx, bdy,
                        seed, guard_cx, guard_cy, guard_r,
                        1, blen, jitter_range, 1);
        }
    }
}

// Generic short-stream brush: only overwrites `target` tile, never touches cliff_blocked.
static void paint_stream_brush(Tilemap* map, int ix, int iy, int brush_r,
                                int guard_cx, int guard_cy, int guard_r,
                                int target, int place)
{
    for (int by = -brush_r; by <= brush_r; by++) {
        for (int bx = -brush_r; bx <= brush_r; bx++) {
            if (bx*bx + by*by > brush_r*brush_r) continue;
            int px = ix+bx, py = iy+by;
            if (!in_bounds(px, py)) continue;
            if (abs(px-guard_cx) <= guard_r && abs(py-guard_cy) <= guard_r) continue;
            if (cliff_blocked[py][px]) continue;
            if (map->tiles[py][px] != target) continue;
            map->tiles[py][px] = place;
        }
    }
}

// Generic short meander — same march algorithm as rivers, no branching.
static void march_stream(Tilemap* map, int sx, int sy,
                         float dir_x, float dir_y, unsigned int seed,
                         int guard_cx, int guard_cy, int guard_r,
                         int brush_r, int max_steps, int jitter_range,
                         int target, int place)
{
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y)/fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x)/fabsf(dir_y) : 0.0f);
    float acc = 0.0f, smooth_j = 0.0f;
    int steps = 0;
    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        float kick = (float)((int)(seed >> 16) % (2*jitter_range+1) - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;
        if (primary_x) {
            rx += sign_x;
            if (rx < 0 || rx >= MAP_WIDTH) break;
            acc += ratio; int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 1) ry = 1; if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT-2;
        } else {
            ry += sign_y;
            if (ry < 0 || ry >= MAP_HEIGHT) break;
            acc += ratio; int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 1) rx = 1; if (rx >= MAP_WIDTH-1) rx = MAP_WIDTH-2;
        }
        paint_stream_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r, target, place);
    }
}

// March the west river as a single meandering channel, then fan it into
// 2-4 branches (delta) as it nears the ocean coast.
static void generate_delta_river(Tilemap* map, int sx, int sy,
                                  float dir_x, float dir_y,
                                  unsigned int seed,
                                  int guard_cx, int guard_cy, int guard_r,
                                  int brush_r, int jitter_range)
{
    const float PI = 3.14159265f;
    unsigned int s = seed;

    // Where (in x) to begin fanning — random per seed, well before the coast
    s = s * 1664525u + 1013904223u;
    int delta_x = 600 + (int)((s >> 16) % 400); // 600..999

    // --- Phase 1: single meandering river trunk ---
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    float smooth_j = 0.0f;

    for (int step = 0; step < MAP_WIDTH + MAP_HEIGHT; step++) {
        s = s * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(s >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 0 || rx >= MAP_WIDTH) { rx -= sign_x; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 1)             ry = 1;
            if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT - 2;
        } else {
            ry += sign_y;
            if (ry < 0 || ry >= MAP_HEIGHT) { ry -= sign_y; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 1)            rx = 1;
            if (rx >= MAP_WIDTH-1) rx = MAP_WIDTH - 2;
        }

        paint_river_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r);

        if (rx <= delta_x) break; // trunk done, start fanning
    }

    // --- Phase 2: fan into delta branches from (rx, ry) ---
    s = s * 1664525u + 1013904223u;
    int num_branches = 2 + (int)((s >> 16) % 3); // 2..4

    s = s * 1664525u + 1013904223u;
    float base_angle = atan2f(dir_y, dir_x);
    // Half-spread: 20°..39° so branches diverge visibly without going vertical
    float spread = (20.0f + (float)((s >> 16) % 20)) * PI / 180.0f;

    for (int b = 0; b < num_branches; b++) {
        // t goes -1..+1 across branches, giving symmetric fan
        float t = (num_branches <= 1) ? 0.0f
                : (float)b / (num_branches - 1) * 2.0f - 1.0f;
        float bangle = base_angle + t * spread;
        float bdx = cosf(bangle);
        float bdy = sinf(bangle);
        s = s * 1664525u + 1013904223u;
        march_river(map, rx, ry, bdx, bdy,
                    s, guard_cx, guard_cy, guard_r,
                    brush_r, MAP_WIDTH + MAP_HEIGHT, jitter_range, 1);
    }
}

// Tiles within this radius of center are generated in phase1.
// Outside is handled by phase2 on a background thread.
#define PHASE_RADIUS 500

static void place_cliffs(Tilemap* map, unsigned int seed,
                         int cx, int cy, int hw,
                         int min_r2, int max_r2)
{
    const int CLIFF_GRID      = 64;
    const int CLIFF_THRESHOLD = 30000;
    // Derive bounding box from max radius so we don't walk all 9M tiles.
    int max_r = (int)sqrtf((float)max_r2) + 1;
    int y_lo = (cy - max_r > 1)           ? cy - max_r : 1;
    int y_hi = (cy + max_r < MAP_HEIGHT-1) ? cy + max_r : MAP_HEIGHT - 1;
    int x_lo = (cx - max_r > 1)           ? cx - max_r : 1;
    int x_hi = (cx + max_r < MAP_WIDTH-1)  ? cx + max_r : MAP_WIDTH  - 1;
    for (int py = y_lo; py < y_hi; py++) {
        for (int px = x_lo; px < x_hi; px++) {
            int ddx = px - cx, ddy = py - cy;
            int r2  = ddx*ddx + ddy*ddy;
            if (r2 < min_r2 || r2 >= max_r2) continue;
            int cur_biome = map->tiles[py][px];
            if (cur_biome != TILE_GRASS && cur_biome != TILE_SNOW &&
                cur_biome != TILE_WASTELAND && cur_biome != TILE_SAND &&
                cur_biome != TILE_MEADOW) continue;
            if (cliff_blocked[py][px]) continue;
            if (r2 <= hw*hw) continue;

            int gx = px / CLIFF_GRID,  gy = py / CLIFF_GRID;
            float fx = (float)(px % CLIFF_GRID) / CLIFF_GRID;
            float fy = (float)(py % CLIFF_GRID) / CLIFF_GRID;

            int n00 = tile_noise(gx,   gy,   (int)seed ^ 0xC11F);
            int n10 = tile_noise(gx+1, gy,   (int)seed ^ 0xC11F);
            int n01 = tile_noise(gx,   gy+1, (int)seed ^ 0xC11F);
            int n11 = tile_noise(gx+1, gy+1, (int)seed ^ 0xC11F);

            float top  = n00 + fx * (n10 - n00);
            float bot  = n01 + fx * (n11 - n01);
            int smooth = (int)(top + fy * (bot - top));

            float proj = (((float)px - s_cliff_ref_x) * s_cliff_dir_x + ((float)py - s_cliff_ref_y) * s_cliff_dir_y) / s_cliff_dir_len;
            if (proj < 0.0f) proj = 0.0f;
            if (proj > 1.0f) proj = 1.0f;
            smooth += (int)(proj * 20000);

            static const int snow_cliff[]  = {0, TILE_CLIFF_SNOW_1,  TILE_CLIFF_SNOW_2,  TILE_CLIFF_SNOW_3,  TILE_CLIFF_SNOW_4,  TILE_CLIFF_SNOW_5};
            static const int waste_cliff[] = {0, TILE_CLIFF_WASTE_1, TILE_CLIFF_WASTE_2, TILE_CLIFF_WASTE_3, TILE_CLIFF_WASTE_4, TILE_CLIFF_WASTE_5};
            static const int plain_cliff[] = {0, TILE_CLIFF,         TILE_CLIFF_2,       TILE_CLIFF_3,       TILE_CLIFF_4,       TILE_CLIFF_5};

            int elev = 0;
            if      (smooth >= CLIFF_THRESHOLD + 16000) elev = 5;
            else if (smooth >= CLIFF_THRESHOLD + 12000) elev = 4;
            else if (smooth >= CLIFF_THRESHOLD +  8000) elev = 3;
            else if (smooth >= CLIFF_THRESHOLD +  4000) elev = 2;
            else if (smooth >= CLIFF_THRESHOLD)         elev = 1;

            if (elev > 0) {
                if      (cur_biome == TILE_SNOW)      map->tiles[py][px] = snow_cliff[elev];
                else if (cur_biome == TILE_WASTELAND) map->tiles[py][px] = waste_cliff[elev];
                else                                  map->tiles[py][px] = plain_cliff[elev];
            }
        }
    }
}

// Stamp a town blueprint onto the map at tile position (tx, ty).
// The entire footprint is pre-filled with TILE_BLUEPRINT so undesigned cells are visible.
// ' ' leaves the blueprint marker in place; 'T' goes into the overlay; everything else
// writes the base tile and clears the overlay.
static void stamp_town_blueprint(Tilemap* map, int town_idx, int tx, int ty) {
    // Pre-fill footprint with the blueprint marker
    for (int dy = 0; dy < TOWN_H; dy++) {
        for (int dx = 0; dx < TOWN_W; dx++) {
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            map->tiles[wy][wx]   = TILE_BLUEPRINT;
            map->overlay[wy][wx] = 0;
        }
    }
    // Stamp the actual blueprint chars on top
    const char** layout = all_towns[town_idx];
    for (int dy = 0; dy < TOWN_H; dy++) {
        const char* row = layout[dy];
        if (!row) break; // nullptr sentinel — remaining rows stay as blueprint marker
        int row_len = (int)strlen(row);
        for (int dx = 0; dx < TOWN_W; dx++) {
            char c = (dx < row_len) ? row[dx] : ' ';
            if (c == ' ') continue; // keep TILE_BLUEPRINT marker
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            if (c == 'T') {
                map->overlay[wy][wx] = TILE_TREE;
                continue;
            }
            int tile = -1;
            switch (c) {
                case '.': tile = TILE_GRASS; break;
                case ',': tile = TILE_PATH;  break;
                case 'H': tile = TILE_HUB;   break;
                case 'W': tile = TILE_WATER; break;
            }
            if (tile < 0) continue;
            map->tiles[wy][wx]   = tile;
            map->overlay[wy][wx] = 0;
        }
    }
    map->towns[town_idx] = { tx, ty, town_idx };
}

static void stamp_village_blueprint(Tilemap* map, int variant, int tx, int ty) {
    // Pre-fill footprint with the village placeholder (orange/black until sprites are added)
    for (int dy = 0; dy < VILLAGE_H; dy++)
        for (int dx = 0; dx < VILLAGE_W; dx++) {
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            map->tiles[wy][wx]   = TILE_VILLAGE_PLACEHOLDER;
            map->overlay[wy][wx] = 0;
        }
    const char** layout = all_villages[variant];
    for (int dy = 0; dy < VILLAGE_H; dy++) {
        const char* row = layout[dy];
        if (!row) break;
        int row_len = (int)strlen(row);
        for (int dx = 0; dx < VILLAGE_W; dx++) {
            char c = (dx < row_len) ? row[dx] : ' ';
            if (c == ' ') continue;
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            if (c == 'T') { map->overlay[wy][wx] = TILE_TREE; continue; }
            int tile = -1;
            switch (c) {
                case '.': tile = TILE_GRASS; break;
                case ',': tile = TILE_PATH;  break;
                case 'H': tile = TILE_HUB;   break;
                case 'W': tile = TILE_WATER; break;
            }
            if (tile < 0) continue;
            map->tiles[wy][wx]   = tile;
            map->overlay[wy][wx] = 0;
        }
    }
    int vi = map->num_villages++;
    map->villages[vi] = { tx, ty, variant };
}

static void stamp_castle_blueprint(Tilemap* map, int type, int tx, int ty) {
    for (int dy = 0; dy < CASTLE_H; dy++)
        for (int dx = 0; dx < CASTLE_W; dx++) {
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            map->tiles[wy][wx]   = TILE_CASTLE_PLACEHOLDER;
            map->overlay[wy][wx] = 0;
        }
    const char** layout = castle_blueprints[type];
    for (int dy = 0; dy < CASTLE_H; dy++) {
        const char* row = layout[dy];
        if (!row) break;
        int row_len = (int)strlen(row);
        for (int dx = 0; dx < CASTLE_W; dx++) {
            char c = (dx < row_len) ? row[dx] : ' ';
            if (c == ' ') continue;
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            if (c == 'T') { map->overlay[wy][wx] = TILE_TREE; continue; }
            int tile = -1;
            switch (c) {
                case '.': tile = TILE_GRASS; break;
                case ',': tile = TILE_PATH;  break;
                case 'H': tile = TILE_HUB;   break;
                case 'W': tile = TILE_WATER; break;
            }
            if (tile < 0) continue;
            map->tiles[wy][wx]   = tile;
            map->overlay[wy][wx] = 0;
        }
    }
    map->castles[type] = { tx, ty, type };
}

void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed) {
    (void)seed;
    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // Sentinel: mark all castles as unplaced so the main thread sees -1 before phase 2 runs
    for (int i = 0; i < 4; i++) map->castles[i] = { -1, -1, i };

    // Grass fill (TILE_GRASS==0)
    memset(map->tiles, 0, sizeof(map->tiles));
    memset(map->overlay, 0, sizeof(map->overlay));

    // Hub ring — cleared by the starting town stamp below
    int ring_inner = hw - 12, ring_outer = hw + 12;
    for (int dy = -(hw+15); dy <= (hw+15); dy++)
        for (int dx = -(hw+15); dx <= (hw+15); dx++) {
            int d2 = dx*dx + dy*dy;
            if (d2 >= ring_inner*ring_inner && d2 <= ring_outer*ring_outer)
                map->tiles[cy + dy][cx + dx] = TILE_HUB;
        }

    // Town 0 — starting town, centred over the hub, same every seed.
    // Must be ready before the game loop so the player has ground to stand on.
    stamp_town_blueprint(map, 0, cx - TOWN_W / 2, cy - TOWN_H / 2);
}

void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed) {
    // Run at idle priority so this thread doesn't compete with the game loop
    struct sched_param sp = {0};
    pthread_setschedparam(pthread_self(), SCHED_IDLE, &sp);

    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // Pick which edge the ocean occupies (0=W, 1=E, 2=N, 3=S)
    unsigned int side_seed = seed ^ 0x5EA5EDEEu;
    side_seed = side_seed * 1664525u + 1013904223u;
    int ocean_side = (int)((side_seed >> 16) % 4);

    // --- Ocean ---
    {
        static int coast_h[MAP_HEIGHT]; // used for W/E oceans (varies along Y)
        static int coast_v[MAP_WIDTH];  // used for N/S oceans (varies along X)

        if (ocean_side == 0 || ocean_side == 1) {
            for (int y = 0; y < MAP_HEIGHT; y++)
                coast_h[y] = 300 + (tile_noise(0, y, 999) % 120);
            float sc = (float)coast_h[0];
            for (int y = 1; y < MAP_HEIGHT; y++) {
                sc = sc * 0.97f + (float)coast_h[y] * 0.03f;
                coast_h[y] = (int)sc;
            }
            for (int y = 0; y < MAP_HEIGHT; y++) {
                int depth = coast_h[y];
                if (ocean_side == 0) { // west
                    for (int x = 0; x <= depth; x++)
                        map->tiles[y][x] = TILE_WATER;
                } else { // east
                    for (int x = MAP_WIDTH - 1 - depth; x < MAP_WIDTH; x++)
                        map->tiles[y][x] = TILE_WATER;
                }
            }
        } else {
            for (int x = 0; x < MAP_WIDTH; x++)
                coast_v[x] = 300 + (tile_noise(x, 0, 999) % 120);
            float sc = (float)coast_v[0];
            for (int x = 1; x < MAP_WIDTH; x++) {
                sc = sc * 0.97f + (float)coast_v[x] * 0.03f;
                coast_v[x] = (int)sc;
            }
            for (int x = 0; x < MAP_WIDTH; x++) {
                int depth = coast_v[x];
                if (ocean_side == 2) { // north
                    for (int y = 0; y <= depth; y++)
                        map->tiles[y][x] = TILE_WATER;
                } else { // south
                    for (int y = MAP_HEIGHT - 1 - depth; y < MAP_HEIGHT; y++)
                        map->tiles[y][x] = TILE_WATER;
                }
            }
        }
    }

    // --- Rivers ---
    const float PI = 3.14159265f;
    int guard_r = hw - 1, brush_r = 6;
    unsigned int cnt_seed = seed * 1664525u + 1013904223u;
    int num_rivers = 5 + (int)((cnt_seed >> 16) % 6);
    cnt_seed = cnt_seed * 1664525u + 1013904223u;
    float global_offset = (cnt_seed >> 16) / (float)0x10000 * 2.0f * PI;
    float spoke_step = 2.0f * PI / num_rivers;

    // Angle pointing from hub toward the ocean side
    float ocean_angle;
    switch (ocean_side) {
        case 0: ocean_angle =  PI;         break; // west
        case 1: ocean_angle =  0.0f;       break; // east
        case 2: ocean_angle = -PI * 0.5f;  break; // north
        default:ocean_angle =  PI * 0.5f;  break; // south
    }

    // The spoke closest to the ocean direction becomes the delta river
    int ocean_idx = 0; float best_ocean = 999.0f;
    for (int i = 0; i < num_rivers; i++) {
        float base = global_offset + i * spoke_step;
        float d = fabsf(fmodf(fabsf(base - ocean_angle), 2.0f * PI));
        if (d > PI) d = 2.0f * PI - d;
        if (d < best_ocean) { best_ocean = d; ocean_idx = i; }
    }
    for (int i = 0; i < num_rivers; i++) {
        float base = global_offset + i * spoke_step;
        unsigned int ps = (seed ^ (unsigned int)(0x3333*(i+1))) * 1664525u + 1013904223u;
        float perturb = ((int)(ps >> 16) % 1000 - 500) / 500.0f * spoke_step * 0.35f;
        float angle = base + perturb;
        while (angle >  PI) angle -= 2.0f * PI;
        while (angle < -PI) angle += 2.0f * PI;
        float dx = cosf(angle), dy = sinf(angle);
        int sx = cx + (int)(dx * hw), sy = cy + (int)(dy * hw);
        unsigned int js = (seed ^ (unsigned int)(0x7777*(i+1))) * 1664525u + 1013904223u;
        int jitter_range = (3 + (int)((js >> 16) % 3)) * 6;
        if (i == ocean_idx) {
            generate_delta_river(map, sx, sy, dx, dy,
                                 seed ^ (unsigned int)(i * 0x1111),
                                 cx, cy, guard_r, brush_r, jitter_range);
        } else {
            int max_steps;
            // Rivers heading toward the cliff side (opposite ocean) cut off early
            bool toward_cliff;
            switch (ocean_side) {
                case 0: toward_cliff = (fabsf(dx) >= fabsf(dy) && dx > 0.0f); break; // cliff=E
                case 1: toward_cliff = (fabsf(dx) >= fabsf(dy) && dx < 0.0f); break; // cliff=W
                case 2: toward_cliff = (fabsf(dy) >= fabsf(dx) && dy > 0.0f); break; // cliff=S
                default:toward_cliff = (fabsf(dy) >= fabsf(dx) && dy < 0.0f); break; // cliff=N
            }
            if (toward_cliff) {
                int dist;
                switch (ocean_side) {
                    case 0: dist = MAP_WIDTH  - sx; break;
                    case 1: dist = sx;              break;
                    case 2: dist = MAP_HEIGHT - sy; break;
                    default:dist = sy;              break;
                }
                int half    = dist / 2;
                int three_q = dist * 3 / 4;
                unsigned int ls = (seed ^ (unsigned int)(0x9999*(i+1))) * 1664525u + 1013904223u;
                max_steps = half + (int)((ls >> 16) % (three_q - half + 1));
            } else {
                max_steps = MAP_WIDTH + MAP_HEIGHT;
            }
            march_river(map, sx, sy, dx, dy,
                        seed ^ (unsigned int)(i * 0x1111), cx, cy, guard_r, brush_r,
                        max_steps, jitter_range, 0);
        }
    }

    // --- Cliff gradient direction ---
    // Cliffs are dense on the side opposite the ocean.
    {
        unsigned int gs = seed ^ 0xB00B5EED;
        gs = gs * 1664525u + 1013904223u;
        int cliff_side = (ocean_side + 2) % 4; // opposite of ocean

        float peak_x, peak_y;
        float rand01 = (float)((gs >> 16) & 0xFFFF) / (float)0xFFFF;
        switch (cliff_side) {
            case 1: // east — pick along right edge
                peak_x = (float)MAP_WIDTH;
                peak_y = rand01 * MAP_HEIGHT;
                break;
            case 0: // west — pick along left edge
                peak_x = 0.0f;
                peak_y = rand01 * MAP_HEIGHT;
                break;
            case 2: // north — pick along top edge
                peak_x = rand01 * MAP_WIDTH;
                peak_y = 0.0f;
                break;
            default: // south — pick along bottom edge
                peak_x = rand01 * MAP_WIDTH;
                peak_y = (float)MAP_HEIGHT;
                break;
        }

        // Reference point: center of the ocean-side boundary
        switch (ocean_side) {
            case 0: s_cliff_ref_x = 0.0f;              s_cliff_ref_y = MAP_HEIGHT * 0.5f; break;
            case 1: s_cliff_ref_x = (float)MAP_WIDTH;  s_cliff_ref_y = MAP_HEIGHT * 0.5f; break;
            case 2: s_cliff_ref_x = MAP_WIDTH * 0.5f;  s_cliff_ref_y = 0.0f;              break;
            default:s_cliff_ref_x = MAP_WIDTH * 0.5f;  s_cliff_ref_y = (float)MAP_HEIGHT; break;
        }

        map->cliff_peak_x = peak_x;
        map->cliff_peak_y = peak_y;
        float dir_x = peak_x - s_cliff_ref_x, dir_y = peak_y - s_cliff_ref_y;
        s_cliff_dir_len = sqrtf(dir_x*dir_x + dir_y*dir_y);
        s_cliff_dir_x = dir_x / s_cliff_dir_len;
        s_cliff_dir_y = dir_y / s_cliff_dir_len;
    }

    // --- Cliff blocked prepass ---
    const int CLIFF_CLEAR = 20;
    memset(cliff_blocked, 0, sizeof(cliff_blocked));
    for (int y = 0; y < MAP_HEIGHT; y++) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int t = map->tiles[y][x];
            if (t != TILE_RIVER && t != TILE_WATER) continue;
            int y0 = y - CLIFF_CLEAR > 0         ? y - CLIFF_CLEAR : 0;
            int y1 = y + CLIFF_CLEAR < MAP_HEIGHT ? y + CLIFF_CLEAR : MAP_HEIGHT - 1;
            int x0 = x - CLIFF_CLEAR > 0         ? x - CLIFF_CLEAR : 0;
            int x1 = x + CLIFF_CLEAR < MAP_WIDTH  ? x + CLIFF_CLEAR : MAP_WIDTH  - 1;
            for (int by = y0; by <= y1; by++)
                for (int bx = x0; bx <= x1; bx++)
                    cliff_blocked[by][bx] = true;
        }
    }

    // --- Biome pass: plains / desert / snow / wasteland ---
    // Desert: flat areas away from mountains. Snow/wasteland: map edges.
    {
        const int BIOME_GRID = 300;
        const float max_dist2 = (float)MAP_WIDTH * (float)MAP_WIDTH * 2.0f;
        const float half_map  = (float)MAP_WIDTH * 0.5f;
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                if (map->tiles[y][x] != TILE_GRASS) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;

                // Mountain-side projection (0=ocean side, 1=cliff side)
                float proj = (((float)x - s_cliff_ref_x) * s_cliff_dir_x +
                               ((float)y - s_cliff_ref_y) * s_cliff_dir_y) / s_cliff_dir_len;
                if (proj < 0.0f) proj = 0.0f;
                if (proj > 1.0f) proj = 1.0f;

                // Proximity to cliff peak
                float dpx = (float)x - map->cliff_peak_x;
                float dpy = (float)y - map->cliff_peak_y;
                float peak_nearness = 1.0f - (dpx*dpx + dpy*dpy) / max_dist2;
                if (peak_nearness < 0.0f) peak_nearness = 0.0f;

                // Proximity to any map edge (0=center, 1=edge)
                int me = x < y ? x : y;
                int rx = MAP_WIDTH-1-x, ry = MAP_HEIGHT-1-y;
                if (rx < me) me = rx;
                if (ry < me) me = ry;
                float edge_nearness = 1.0f - (float)me / half_map;
                if (edge_nearness < 0.0f) edge_nearness = 0.0f;
                if (edge_nearness > 1.0f) edge_nearness = 1.0f;

                // Proximity to the ocean edge (0=far, 1=ocean side)
                float ocean_dist;
                switch (ocean_side) {
                    case 0: ocean_dist = (float)x;              break; // west
                    case 1: ocean_dist = (float)(MAP_WIDTH-1-x);  break; // east
                    case 2: ocean_dist = (float)y;              break; // north
                    default:ocean_dist = (float)(MAP_HEIGHT-1-y); break; // south
                }
                float ocean_nearness = 1.0f - ocean_dist / half_map;
                if (ocean_nearness < 0.0f) ocean_nearness = 0.0f;
                if (ocean_nearness > 1.0f) ocean_nearness = 1.0f;

                // Coarse biome noise helper
                int gx = x / BIOME_GRID, gy = y / BIOME_GRID;
                float fx = (float)(x % BIOME_GRID) / BIOME_GRID;
                float fy = (float)(y % BIOME_GRID) / BIOME_GRID;
                auto bn = [&](unsigned int s) -> int {
                    float t = tile_noise(gx,gy,s)     + fx*(tile_noise(gx+1,gy,s)    -tile_noise(gx,gy,s));
                    float b = tile_noise(gx,gy+1,s)   + fx*(tile_noise(gx+1,gy+1,s)  -tile_noise(gx,gy+1,s));
                    return (int)(t + fy*(b - t));
                };

                int noise1 = bn((unsigned int)(seed ^ 0xDE5E7u));    // desert vs plains
                int noise2 = bn((unsigned int)(seed ^ 0xED6E1Du));   // snow vs wasteland
                int noise3 = bn((unsigned int)(seed ^ 0xFA4EEFu));   // edge zone selector

                // Edge biomes: threshold drops steeply near edges
                // center(0): need noise3>30000 (~8%); full edge(1): need noise3>5000 (~85%)
                int edge_threshold = 30000 - (int)(edge_nearness * edge_nearness * 25000);
                if (noise3 > edge_threshold) {
                    // Snow: occupies upper noise2 range, suppressed near ocean
                    int snow_threshold = 16383 + (int)(ocean_nearness * ocean_nearness * 16000);
                    bool is_snow = noise2 > snow_threshold;

                    // Wasteland: rare by default, boosted near cliff peak, impossible near ocean
                    // Occupies only the bottom slice of noise2 (below waste_threshold)
                    // so it is always the rarest biome.
                    bool can_waste = ocean_nearness < 0.35f;
                    int waste_threshold = 5000 + (int)(peak_nearness * peak_nearness * 12000);
                    bool is_waste = can_waste && !is_snow && noise2 < waste_threshold;

                    if (is_snow)  map->tiles[y][x] = TILE_SNOW;
                    else if (is_waste) map->tiles[y][x] = TILE_WASTELAND;
                    // else: middle noise2 range or ocean edge — stays TILE_GRASS
                    continue;
                }

                // Desert vs plains: suppressed near mountains and cliff peak
                int desert_threshold = 16383
                    + (int)(proj * proj * 14000)
                    + (int)(peak_nearness * peak_nearness * 14000);
                int noise4 = bn((unsigned int)(seed ^ 0xC0FFEEu)); // dense forest vs meadow
                if (noise1 > desert_threshold)
                    map->tiles[y][x] = TILE_SAND;
                else if (noise4 > 16383)
                    map->tiles[y][x] = TILE_MEADOW; // open plains
                // else stays TILE_GRASS (dense forest)
            }
        }
    }

    // --- Biome smoothing: eliminate tiny isolated patches ---
    // 3 passes of 5x5 majority vote. Only biome tiles (grass/sand/snow/waste/meadow)
    // participate; structural tiles (water, cliff, rock, river) are left alone.
    {
        static const int BIOME_TILES[] = {
            TILE_GRASS, TILE_SAND, TILE_SNOW, TILE_WASTELAND, TILE_MEADOW
        };
        static const int NB = (int)(sizeof(BIOME_TILES)/sizeof(BIOME_TILES[0]));
        auto is_biome = [](int t) {
            return t == TILE_GRASS || t == TILE_SAND || t == TILE_SNOW
                || t == TILE_WASTELAND || t == TILE_MEADOW;
        };
        const int R = 3; // 5x5 window (radius 2)
        for (int pass = 0; pass < 7; pass++) {
            for (int y = R; y < MAP_HEIGHT - R; y++) {
                for (int x = R; x < MAP_WIDTH - R; x++) {
                    int cur = map->tiles[y][x];
                    if (!is_biome(cur)) continue;
                    int counts[5] = {0,0,0,0,0};
                    for (int dy2 = -R; dy2 <= R; dy2++)
                        for (int dx2 = -R; dx2 <= R; dx2++) {
                            int t = map->tiles[y+dy2][x+dx2];
                            for (int b = 0; b < NB; b++)
                                if (t == BIOME_TILES[b]) { counts[b]++; break; }
                        }
                    int best = 0;
                    for (int b = 1; b < NB; b++)
                        if (counts[b] > counts[best]) best = b;
                    map->tiles[y][x] = BIOME_TILES[best];
                }
            }
        }
    }

    // --- Biome adjacency fixup ---
    // Rule 1: TILE_SAND cannot be adjacent to TILE_SNOW.
    // Rule 2: TILE_SNOW can only be adjacent to TILE_GRASS or TILE_MEADOW (among biome tiles).
    // Any SAND within SNOW_BUFFER tiles of snow is converted to TILE_MEADOW,
    // creating a wide meadow/forest transition zone between the two biomes.
    {
        const int SNOW_BUFFER = 50;
        for (int y = SNOW_BUFFER; y < MAP_HEIGHT - SNOW_BUFFER; y++) {
            for (int x = SNOW_BUFFER; x < MAP_WIDTH - SNOW_BUFFER; x++) {
                if (map->tiles[y][x] != TILE_SAND) continue;
                bool near_snow = false;
                for (int dy2 = -SNOW_BUFFER; dy2 <= SNOW_BUFFER && !near_snow; dy2++)
                    for (int dx2 = -SNOW_BUFFER; dx2 <= SNOW_BUFFER && !near_snow; dx2++)
                        if (map->tiles[y+dy2][x+dx2] == TILE_SNOW) near_snow = true;
                if (near_snow)
                    map->tiles[y][x] = TILE_MEADOW;
            }
        }
    }

    // --- Post-fixup biome smoothing ---
    // Re-run majority vote after the adjacency fixup to dissolve thin strips of desert
    // or snow that were left orphaned when their neighbors were converted to meadow.
    {
        static const int BIOME_TILES[] = {
            TILE_GRASS, TILE_SAND, TILE_SNOW, TILE_WASTELAND, TILE_MEADOW
        };
        static const int NB = (int)(sizeof(BIOME_TILES)/sizeof(BIOME_TILES[0]));
        auto is_biome = [](int t) {
            return t == TILE_GRASS || t == TILE_SAND || t == TILE_SNOW
                || t == TILE_WASTELAND || t == TILE_MEADOW;
        };
        const int R = 3;
        for (int pass = 0; pass < 10; pass++) {
            for (int y = R; y < MAP_HEIGHT - R; y++) {
                for (int x = R; x < MAP_WIDTH - R; x++) {
                    int cur = map->tiles[y][x];
                    if (!is_biome(cur)) continue;
                    int counts[5] = {0,0,0,0,0};
                    for (int dy2 = -R; dy2 <= R; dy2++)
                        for (int dx2 = -R; dx2 <= R; dx2++) {
                            int t = map->tiles[y+dy2][x+dx2];
                            for (int b = 0; b < NB; b++)
                                if (t == BIOME_TILES[b]) { counts[b]++; break; }
                        }
                    int best = 0;
                    for (int b = 1; b < NB; b++)
                        if (counts[b] > counts[best]) best = b;
                    map->tiles[y][x] = BIOME_TILES[best];
                }
            }
        }
    }

    // --- Minimum biome patch enforcement ---
    // Flood-fill connected components; absorb any component smaller than
    // MIN_BIOME_AREA tiles into its most common neighboring biome.
    {
        const int MIN_BIOME_AREA = 10000; // ~100×100

        auto is_biome_tile = [](int t) {
            return t == TILE_GRASS || t == TILE_SAND || t == TILE_SNOW
                || t == TILE_WASTELAND || t == TILE_MEADOW;
        };

        static const int BIOME_TILES[5] = {
            TILE_GRASS, TILE_SAND, TILE_SNOW, TILE_WASTELAND, TILE_MEADOW
        };
        static const int DX[4] = {1,-1,0,0};
        static const int DY[4] = {0,0,1,-1};

        // label: -1 = unvisited biome, -2 = non-biome, >=0 = component id
        std::vector<int> label(MAP_HEIGHT * MAP_WIDTH);
        std::vector<int> bfs_q(MAP_HEIGHT * MAP_WIDTH);
#define LABEL(y,x) label[(y)*MAP_WIDTH+(x)]

        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++)
                LABEL(y,x) = is_biome_tile(map->tiles[y][x]) ? -1 : -2;

        struct Comp { int tile; int size; };
        std::vector<Comp> comps;

        // Flood fill to label all components
        int next_id = 0;
        for (int y0 = 0; y0 < MAP_HEIGHT; y0++) {
            for (int x0 = 0; x0 < MAP_WIDTH; x0++) {
                if (LABEL(y0,x0) != -1) continue;
                int tile = map->tiles[y0][x0];
                int qhead = 0, qtail = 0;
                LABEL(y0,x0) = next_id;
                bfs_q[qtail++] = y0 * MAP_WIDTH + x0;
                while (qhead < qtail) {
                    int idx = bfs_q[qhead++];
                    int qx = idx % MAP_WIDTH, qy = idx / MAP_WIDTH;
                    for (int d = 0; d < 4; d++) {
                        int nx = qx + DX[d], ny = qy + DY[d];
                        if (nx < 0 || nx >= MAP_WIDTH || ny < 0 || ny >= MAP_HEIGHT) continue;
                        if (LABEL(ny,nx) != -1) continue;
                        if (map->tiles[ny][nx] != tile) continue;
                        LABEL(ny,nx) = next_id;
                        bfs_q[qtail++] = ny * MAP_WIDTH + nx;
                    }
                }
                comps.push_back({tile, qtail});
                next_id++;
            }
        }

        // Single scan: accumulate neighbor-biome counts for each small component
        std::vector<std::array<int,5>> nbr(next_id);
        for (auto& a : nbr) a.fill(0);

        for (int y = 0; y < MAP_HEIGHT; y++) {
            for (int x = 0; x < MAP_WIDTH; x++) {
                int cid = LABEL(y,x);
                if (cid < 0 || comps[cid].size >= MIN_BIOME_AREA) continue;
                for (int d = 0; d < 4; d++) {
                    int nx = x + DX[d], ny = y + DY[d];
                    if (nx < 0 || nx >= MAP_WIDTH || ny < 0 || ny >= MAP_HEIGHT) continue;
                    if (LABEL(ny,nx) == cid) continue;
                    int nt = map->tiles[ny][nx];
                    for (int b = 0; b < 5; b++)
                        if (nt == BIOME_TILES[b]) { nbr[cid][b]++; break; }
                }
            }
        }

        // Determine replacement tile for each small component
        std::vector<int> repl(next_id, -1);
        for (int cid = 0; cid < next_id; cid++) {
            if (comps[cid].size >= MIN_BIOME_AREA) continue;
            int best_b = 0;
            for (int b = 1; b < 5; b++)
                if (nbr[cid][b] > nbr[cid][best_b]) best_b = b;
            repl[cid] = (nbr[cid][best_b] > 0) ? BIOME_TILES[best_b] : comps[cid].tile;
        }

        // Apply replacements
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int cid = LABEL(y,x);
                if (cid >= 0 && repl[cid] >= 0)
                    map->tiles[y][x] = repl[cid];
            }
#undef LABEL
    }

    // --- Cliffs ---
    // Biomes are fully settled above; place_cliffs reads the biome under each tile
    // and selects the matching cliff variant (snow/wasteland/plain) directly.
    place_cliffs(map, seed, cx, cy, hw, hw*hw, MAP_WIDTH * MAP_WIDTH);

    // --- Cliff edge pass (bottom-to-top so each drop level gets its own edge) ---
    // For each tile, if the tile directly south is at lower elevation, place a
    // south-facing edge tile there showing the dirt face of the cliff.
    auto cliff_elev = [](int t) -> int {
        switch (t) {
            case TILE_CLIFF:        case TILE_CLIFF_SNOW_1: case TILE_CLIFF_WASTE_1: return 1;
            case TILE_CLIFF_2:      case TILE_CLIFF_SNOW_2: case TILE_CLIFF_WASTE_2: return 2;
            case TILE_CLIFF_3:      case TILE_CLIFF_SNOW_3: case TILE_CLIFF_WASTE_3: return 3;
            case TILE_CLIFF_4:      case TILE_CLIFF_SNOW_4: case TILE_CLIFF_WASTE_4: return 4;
            case TILE_CLIFF_5:      case TILE_CLIFF_SNOW_5: case TILE_CLIFF_WASTE_5: return 5;
            default:                return 0;
        }
    };
    static const int edge_tile[] = {
        0,                  // unused (no drop from elev 0)
        TILE_CLIFF_EDGE_1,  // drop from elev 1
        TILE_CLIFF_EDGE_2,  // drop from elev 2
        TILE_CLIFF_EDGE_3,  // drop from elev 3
        TILE_CLIFF_EDGE_4,  // drop from elev 4
        TILE_CLIFF_EDGE_5,  // drop from elev 5
    };
    for (int y = MAP_HEIGHT - 2; y >= 0; y--) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int elev_here  = cliff_elev(map->tiles[y][x]);
            int elev_below = cliff_elev(map->tiles[y+1][x]);
            if (elev_here <= elev_below) continue;
            // Only require connectivity at cliff→grass drops to suppress stray specks.
            // Between elevation layers the lower layer is always wide, so no check needed.
            if (elev_below == 0) {
                bool connected = (x > 0            && cliff_elev(map->tiles[y][x-1]) >= elev_here)
                              || (x < MAP_WIDTH - 1 && cliff_elev(map->tiles[y][x+1]) >= elev_here)
                              || (y > 0             && cliff_elev(map->tiles[y-1][x]) >= elev_here);
                if (!connected) continue;
            }
            for (int d = 1; d <= elev_here; d++) {
                int ey = y + d;
                if (ey >= MAP_HEIGHT) break;
                if (cliff_elev(map->tiles[ey][x]) >= elev_here) break;
                map->tiles[ey][x] = edge_tile[elev_here];
            }
        }
    }

    // --- Cliff side/corner pass ---
    // East/west faces and outer (convex) corners.
    // Run bottom-to-top so higher-elevation cliffs overwrite lower-elevation placements
    // at shared positions, mirroring the south-face pass ordering.
    {
        static const int side_tile[] = {
            0,
            TILE_CLIFF_SIDE_1, TILE_CLIFF_SIDE_2, TILE_CLIFF_SIDE_3,
            TILE_CLIFF_SIDE_4, TILE_CLIFF_SIDE_5,
        };
        static const int corner_sw[] = {
            0,
            TILE_CLIFF_CORNER_SW_1, TILE_CLIFF_CORNER_SW_2, TILE_CLIFF_CORNER_SW_3,
            TILE_CLIFF_CORNER_SW_4, TILE_CLIFF_CORNER_SW_5,
        };
        static const int corner_se[] = {
            0,
            TILE_CLIFF_CORNER_SE_1, TILE_CLIFF_CORNER_SE_2, TILE_CLIFF_CORNER_SE_3,
            TILE_CLIFF_CORNER_SE_4, TILE_CLIFF_CORNER_SE_5,
        };

        for (int y = MAP_HEIGHT - 2; y >= 0; y--) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int E = cliff_elev(map->tiles[y][x]);
                if (E == 0) continue;

                // West face: cliff at (x,y) drops to lower ground at (x-1,y).
                // Side tiles go at (x-1, y+d) for d in [0,E), corner at (x-1, y+E).
                if (cliff_elev(map->tiles[y][x-1]) < E) {
                    bool full = true;
                    for (int d = 0; d < E; d++) {
                        int ey = y + d;
                        if (ey >= MAP_HEIGHT)             { full = false; break; }
                        if (cliff_elev(map->tiles[ey][x-1]) >= E) { full = false; break; }
                        map->tiles[ey][x-1] = side_tile[E];
                    }
                    if (full) {
                        int cy = y + E;
                        if (cy < MAP_HEIGHT && cliff_elev(map->tiles[cy][x-1]) == 0)
                            map->tiles[cy][x-1] = corner_sw[E];
                    }
                }

                // East face: cliff at (x,y) drops to lower ground at (x+1,y).
                if (cliff_elev(map->tiles[y][x+1]) < E) {
                    bool full = true;
                    for (int d = 0; d < E; d++) {
                        int ey = y + d;
                        if (ey >= MAP_HEIGHT)             { full = false; break; }
                        if (cliff_elev(map->tiles[ey][x+1]) >= E) { full = false; break; }
                        map->tiles[ey][x+1] = side_tile[E];
                    }
                    if (full) {
                        int cy = y + E;
                        if (cy < MAP_HEIGHT && cliff_elev(map->tiles[cy][x+1]) == 0)
                            map->tiles[cy][x+1] = corner_se[E];
                    }
                }
            }
        }

        // North/back face: one side tile at (x, y-1) per northward layer drop.
        // Run top-to-bottom so higher-elevation cliffs overwrite lower ones.
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 0; x < MAP_WIDTH; x++) {
                int E = cliff_elev(map->tiles[y][x]);
                if (E == 0) continue;
                if (cliff_elev(map->tiles[y-1][x]) >= E) continue;
                map->tiles[y-1][x] = side_tile[E];
            }
        }

        // Inner (concave) back corners: placed at (x-1, y-1) and (x+1, y-1) when a
        // cliff drops both west/east AND north simultaneously.  These fill the gap
        // where the north back-face meets the west or east side-face from the inside.
        static const int corner_nw[] = {
            0,
            TILE_CLIFF_CORNER_NW_1, TILE_CLIFF_CORNER_NW_2, TILE_CLIFF_CORNER_NW_3,
            TILE_CLIFF_CORNER_NW_4, TILE_CLIFF_CORNER_NW_5,
        };
        static const int corner_ne[] = {
            0,
            TILE_CLIFF_CORNER_NE_1, TILE_CLIFF_CORNER_NE_2, TILE_CLIFF_CORNER_NE_3,
            TILE_CLIFF_CORNER_NE_4, TILE_CLIFF_CORNER_NE_5,
        };
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int E = cliff_elev(map->tiles[y][x]);
                if (E == 0) continue;

                bool drops_west  = cliff_elev(map->tiles[y][x-1]) < E;
                bool drops_east  = cliff_elev(map->tiles[y][x+1]) < E;
                bool drops_north = cliff_elev(map->tiles[y-1][x]) < E;

                if (drops_west && drops_north) {
                    int px = x - 1, py = y - 1;
                    if (cliff_elev(map->tiles[py][px]) < E)
                        map->tiles[py][px] = corner_nw[E];
                }
                if (drops_east && drops_north) {
                    int px = x + 1, py = y - 1;
                    if (cliff_elev(map->tiles[py][px]) < E)
                        map->tiles[py][px] = corner_ne[E];
                }
            }
        }
    }

    // --- Trees ---
    // TILE_GRASS = spotty dense forest (coarse cluster noise → dense patches + clearings)
    // TILE_MEADOW = open plains (~5% trees)
    {
        const int FG = 20; // forest cluster grid size
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                if (t != TILE_GRASS && t != TILE_MEADOW) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                int n = tile_noise(x, y, (int)seed ^ 7);
                if (t == TILE_MEADOW) {
                    if (n > 31000) map->overlay[y][x] = TILE_TREE;
                } else {
                    int gx = x/FG, gy = y/FG;
                    float fx = (float)(x%FG)/FG, fy = (float)(y%FG)/FG;
                    float top = tile_noise(gx,gy,(int)seed^0xF04) + fx*(tile_noise(gx+1,gy,(int)seed^0xF04)-tile_noise(gx,gy,(int)seed^0xF04));
                    float bot = tile_noise(gx,gy+1,(int)seed^0xF04) + fx*(tile_noise(gx+1,gy+1,(int)seed^0xF04)-tile_noise(gx,gy+1,(int)seed^0xF04));
                    int cluster = (int)(top + fy*(bot-top));
                    if (n > ((cluster > 16000) ? 5000 : 30500))
                        map->overlay[y][x] = TILE_TREE;
                }
            }
        }
    }

    // --- Rocks (after cliffs for same reason) ---
    {
        unsigned int s = seed ^ 0xDEAD1;
        for (int i = 0; i < 72000; i++) {
            s = s * 1664525u + 1013904223u;
            int x = 1 + (int)((s >> 16) % (MAP_WIDTH  - 2));
            s = s * 1664525u + 1013904223u;
            int y = 1 + (int)((s >> 16) % (MAP_HEIGHT - 2));
            int ddx = x - cx, ddy = y - cy;
            if (ddx*ddx + ddy*ddy <= hw*hw) continue;
            if (map->tiles[y][x] == TILE_GRASS && map->overlay[y][x] == 0) map->overlay[y][x] = TILE_ROCK;
        }
    }

    // --- Rocks at elevation (density scales with cliff level) ---
    {
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                int threshold;
                if      (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1) threshold = 27851; // ~15%
                else if (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2) threshold = 24575; // ~25%
                else if (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) threshold = 21298; // ~35%
                else if (t == TILE_CLIFF_4 || t == TILE_CLIFF_SNOW_4 || t == TILE_CLIFF_WASTE_4) threshold = 18022; // ~45%
                else if (t == TILE_CLIFF_5 || t == TILE_CLIFF_SNOW_5 || t == TILE_CLIFF_WASTE_5) threshold = 14745; // ~55%
                else continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                if (tile_noise(x, y, (int)seed ^ 0xC1FFE) > threshold)
                    map->overlay[y][x] = TILE_ROCK;
            }
        }
    }

    // --- Gold ore at high elevation (cliff 3+), rarer than rocks ---
    {
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                int threshold;
                if      (t == TILE_CLIFF_3) threshold = 32127; // ~2%
                else if (t == TILE_CLIFF_4) threshold = 31784; // ~3%
                else if (t == TILE_CLIFF_5) threshold = 31129; // ~5%
                else continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                if (tile_noise(x, y, (int)seed ^ 0x4E1DA9) > threshold)
                    map->overlay[y][x] = TILE_GOLD_ORE;
            }
        }
    }

    // --- Lava streams and pools inside wasteland ---
    {
        unsigned int ls = seed ^ 0x1A4A1u;
        for (int i = 0; i < 1200; i++) {
            ls = ls * 1664525u + 1013904223u;
            int lx = 1 + (int)((ls >> 16) % (MAP_WIDTH  - 2));
            ls = ls * 1664525u + 1013904223u;
            int ly = 1 + (int)((ls >> 16) % (MAP_HEIGHT - 2));
            if (map->tiles[ly][lx] != TILE_WASTELAND || cliff_blocked[ly][lx]) continue;
            ls = ls * 1664525u + 1013904223u;
            float angle = (float)((ls >> 16) & 0xFFFF) / 65536.0f * 6.28318f;
            ls = ls * 1664525u + 1013904223u;
            int len = 15 + (int)((ls >> 16) % 55);
            march_stream(map, lx, ly, cosf(angle), sinf(angle), ls,
                         cx, cy, guard_r, 1, len, 5, TILE_WASTELAND, TILE_LAVA);
        }
        ls = ls ^ 0xB00B5u;
        for (int i = 0; i < 400; i++) {
            ls = ls * 1664525u + 1013904223u;
            int lx = 1 + (int)((ls >> 16) % (MAP_WIDTH  - 2));
            ls = ls * 1664525u + 1013904223u;
            int ly = 1 + (int)((ls >> 16) % (MAP_HEIGHT - 2));
            if (map->tiles[ly][lx] != TILE_WASTELAND || cliff_blocked[ly][lx]) continue;
            paint_stream_brush(map, lx, ly, 2, cx, cy, guard_r, TILE_WASTELAND, TILE_LAVA);
        }
    }

    // --- Pond streams and pools inside meadows ---
    {
        unsigned int ps = seed ^ 0xF0D5u;
        for (int i = 0; i < 1200; i++) {
            ps = ps * 1664525u + 1013904223u;
            int lx = 1 + (int)((ps >> 16) % (MAP_WIDTH  - 2));
            ps = ps * 1664525u + 1013904223u;
            int ly = 1 + (int)((ps >> 16) % (MAP_HEIGHT - 2));
            if (map->tiles[ly][lx] != TILE_MEADOW || cliff_blocked[ly][lx]) continue;
            ps = ps * 1664525u + 1013904223u;
            float angle = (float)((ps >> 16) & 0xFFFF) / 65536.0f * 6.28318f;
            ps = ps * 1664525u + 1013904223u;
            int len = 15 + (int)((ps >> 16) % 55);
            march_stream(map, lx, ly, cosf(angle), sinf(angle), ps,
                         cx, cy, guard_r, 1, len, 5, TILE_MEADOW, TILE_POND);
        }
        ps = ps ^ 0xA0D5u;
        for (int i = 0; i < 400; i++) {
            ps = ps * 1664525u + 1013904223u;
            int lx = 1 + (int)((ps >> 16) % (MAP_WIDTH  - 2));
            ps = ps * 1664525u + 1013904223u;
            int ly = 1 + (int)((ps >> 16) % (MAP_HEIGHT - 2));
            if (map->tiles[ly][lx] != TILE_MEADOW || cliff_blocked[ly][lx]) continue;
            paint_stream_brush(map, lx, ly, 2, cx, cy, guard_r, TILE_MEADOW, TILE_POND);
        }
    }

    // --- Biome guarantee pass: ensure every biome appears at least once ---
    {
        bool has_sand=false, has_snow=false, has_waste=false, has_lava=false, has_meadow=false;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++)
                switch (map->tiles[y][x]) {
                    case TILE_SAND:      has_sand   = true; break;
                    case TILE_SNOW:      has_snow   = true; break;
                    case TILE_WASTELAND: has_waste  = true; break;
                    case TILE_LAVA:      has_lava   = true; break;
                    case TILE_MEADOW:    has_meadow = true; break;
                    default: break;
                }

        const float hm = (float)MAP_WIDTH * 0.5f;
        const int   FR = 10;

        auto stamp = [&](int fx, int fy, int tile_id, int r, int replace_id) {
            for (int dy = -r; dy <= r; dy++)
                for (int dx = -r; dx <= r; dx++) {
                    if (dx*dx+dy*dy > r*r) continue;
                    int px = fx+dx, py = fy+dy;
                    if (!in_bounds(px,py)) continue;
                    if (map->tiles[py][px] == replace_id) map->tiles[py][px] = tile_id;
                }
        };
        auto ocean_near = [&](int fx, int fy) -> float {
            float od; switch (ocean_side) {
                case 0: od=(float)fx; break; case 1: od=(float)(MAP_WIDTH-1-fx); break;
                case 2: od=(float)fy; break; default: od=(float)(MAP_HEIGHT-1-fy); break;
            }
            float n = 1.0f - od/hm; return n < 0.0f ? 0.0f : n;
        };
        auto edge_near = [&](int fx, int fy) -> float {
            int me = fx<fy?fx:fy, re=MAP_WIDTH-1-fx, rb=MAP_HEIGHT-1-fy;
            if (re<me) me=re; if (rb<me) me=rb;
            float n = 1.0f-(float)me/hm; return n<0.0f?0.0f:(n>1.0f?1.0f:n);
        };
        auto mtn_proj = [&](int fx, int fy) -> float {
            float p=(((float)fx-s_cliff_ref_x)*s_cliff_dir_x+((float)fy-s_cliff_ref_y)*s_cliff_dir_y)/s_cliff_dir_len;
            return p<0.0f?0.0f:(p>1.0f?1.0f:p);
        };
        auto force = [&](int tile_id, int replace_id, int r, unsigned int fseed, auto cond) -> bool {
            for (int attempt = 0; attempt < 8000; attempt++) {
                fseed = fseed*1664525u+1013904223u;
                int fx = r+(int)((fseed>>16)%(MAP_WIDTH-2*r));
                fseed = fseed*1664525u+1013904223u;
                int fy = r+(int)((fseed>>16)%(MAP_HEIGHT-2*r));
                if (map->tiles[fy][fx] != replace_id) continue;
                int ddx=fx-cx, ddy=fy-cy;
                if (ddx*ddx+ddy*ddy <= hw*hw) continue;
                if (!cond(fx,fy)) continue;
                stamp(fx,fy,tile_id,r,replace_id); return true;
            }
            return false;
        };

        if (!has_sand)
            force(TILE_SAND, TILE_GRASS, FR, seed^0xF04CE5u,
                  [&](int fx,int fy){ return mtn_proj(fx,fy)<0.55f && ocean_near(fx,fy)<0.35f; });
        if (!has_meadow)
            force(TILE_MEADOW, TILE_GRASS, FR, seed^0x4EAD07u,
                  [&](int fx,int fy){ return mtn_proj(fx,fy)<0.55f && ocean_near(fx,fy)<0.35f; });
        if (!has_snow)
            force(TILE_SNOW, TILE_GRASS, FR, seed^0x5E04u,
                  [&](int fx,int fy){ return edge_near(fx,fy)>0.35f && ocean_near(fx,fy)<0.35f; });
        if (!has_waste) {
            bool placed = force(TILE_WASTELAND, TILE_GRASS, FR, seed^0xA5E1Du,
                  [&](int fx,int fy){ return edge_near(fx,fy)>0.35f && ocean_near(fx,fy)<0.35f; });
            if (placed) {
                force(TILE_LAVA, TILE_WASTELAND, FR/3, seed^0xA5E1Du,
                      [&](int,int){ return true; });
                has_lava = true;
            }
        }
        if (!has_lava) {
            unsigned int fs = seed^0xB005u;
            for (int attempt = 0; attempt < 15000; attempt++) {
                fs = fs*1664525u+1013904223u; int fx=(int)((fs>>16)%MAP_WIDTH);
                fs = fs*1664525u+1013904223u; int fy=(int)((fs>>16)%MAP_HEIGHT);
                if (map->tiles[fy][fx] != TILE_WASTELAND) continue;
                stamp(fx,fy,TILE_LAVA,4,TILE_WASTELAND); break;
            }
        }
    }

    // Covers all cliff tile families: basic, edge, snow, wasteland, side, corners.
    auto is_cliff = [](int bt) -> bool {
        return (bt >= TILE_CLIFF        && bt <= TILE_CLIFF_5)           // 4-11
            || (bt >= TILE_CLIFF_EDGE_1 && bt <= TILE_CLIFF_EDGE_5)     // 12-16
            || (bt >= TILE_CLIFF_SNOW_1 && bt <= TILE_CLIFF_CORNER_NE_5); // 24-58
    };
    // Slope-only subset: edge faces, side faces, and corner transitions.
    // These are the "side of a mountain" tiles — not flat ground.
    auto is_cliff_slope = [](int bt) -> bool {
        return (bt >= TILE_CLIFF_EDGE_1 && bt <= TILE_CLIFF_EDGE_5)     // 12-16: south drop
            || (bt >= TILE_CLIFF_SIDE_1 && bt <= TILE_CLIFF_CORNER_NE_5); // 34-58: sides/corners
    };

    // --- Towns 1-3 ---
    // Town 0 is already stamped in phase1 (player starts there).
    // Town 1: placed on the coastline, position varies by seed.
    // Town 2: random walkable location, far from towns 0 and 1.
    {
        auto footprint_ok = [&](int tx, int ty) -> bool {
            for (int dy = 0; dy < TOWN_H; dy++)
                for (int dx = 0; dx < TOWN_W; dx++) {
                    int bt = map->tiles[ty+dy][tx+dx];
                    if (bt == TILE_WATER || bt == TILE_RIVER) return false;
                    if (is_cliff(bt)) return false;
                }
            return true;
        };

        // -- Town 1: on the coast --
        // Helper: try all 4 footprint corners relative to a candidate tile and
        // push any that pass footprint_ok + centre exclusion into `shore`.
        auto try_shore_origins = [&](std::vector<std::pair<int,int>>& shore, int x, int y) {
            const int ox[4] = { x, x - TOWN_W + 1, x,              x - TOWN_W + 1 };
            const int oy[4] = { y, y,               y - TOWN_H + 1, y - TOWN_H + 1 };
            for (int k = 0; k < 4; k++) {
                int tx = ox[k], ty = oy[k];
                if (tx < TOWN_W || ty < TOWN_H ||
                    tx + TOWN_W > MAP_WIDTH  - TOWN_W ||
                    ty + TOWN_H > MAP_HEIGHT - TOWN_H) continue;
                int ddx = tx - cx, ddy = ty - cy;
                if (ddx*ddx + ddy*ddy <= (hw+TOWN_H)*(hw+TOWN_H)) continue;
                if (!footprint_ok(tx, ty)) continue;
                shore.push_back({tx, ty});
            }
        };

        {
            std::vector<std::pair<int,int>> shore;
            shore.reserve(4096);

            // Pass 1: tiles immediately adjacent to water
            for (int y = TOWN_H; y < MAP_HEIGHT - TOWN_H; y++) {
                for (int x = TOWN_W; x < MAP_WIDTH - TOWN_W; x++) {
                    int t = map->tiles[y][x];
                    if (t != TILE_GRASS && t != TILE_SAND &&
                        t != TILE_MEADOW && t != TILE_SNOW) continue;
                    if (!(map->tiles[y-1][x] == TILE_WATER ||
                          map->tiles[y+1][x] == TILE_WATER ||
                          map->tiles[y][x-1] == TILE_WATER ||
                          map->tiles[y][x+1] == TILE_WATER)) continue;
                    try_shore_origins(shore, x, y);
                }
            }

            // Pass 2 fallback: tiles within 30 tiles of water (catches seeds
            // where cliffs back the beach and pass 1 finds nothing)
            if (shore.empty()) {
                for (int y = TOWN_H; y < MAP_HEIGHT - TOWN_H; y++) {
                    for (int x = TOWN_W; x < MAP_WIDTH - TOWN_W; x++) {
                        int t = map->tiles[y][x];
                        if (t != TILE_GRASS && t != TILE_SAND &&
                            t != TILE_MEADOW && t != TILE_SNOW) continue;
                        bool near_water = false;
                        for (int r = 1; r <= 30 && !near_water; r++) {
                            if (y-r >= 0           && map->tiles[y-r][x] == TILE_WATER) near_water = true;
                            if (y+r < MAP_HEIGHT   && map->tiles[y+r][x] == TILE_WATER) near_water = true;
                            if (x-r >= 0           && map->tiles[y][x-r] == TILE_WATER) near_water = true;
                            if (x+r < MAP_WIDTH    && map->tiles[y][x+r] == TILE_WATER) near_water = true;
                        }
                        if (!near_water) continue;
                        try_shore_origins(shore, x, y);
                    }
                }
            }

            if (!shore.empty()) {
                unsigned int ts = seed ^ 0xC0A57001u;
                ts = ts * 1664525u + 1013904223u;
                int idx = (int)((ts >> 16) % (unsigned)shore.size());
                stamp_town_blueprint(map, 1, shore[idx].first, shore[idx].second);
            } else {
                map->towns[1] = { -1, -1, 1 };
            }
        }

        // -- Town 2: random walkable location, far from towns 0 and 1 --
        {
            const int MIN_TOWN_DIST = 600;
            unsigned int ts = seed ^ 0xF4EE7002u;
            bool placed = false;
            for (int attempt = 0; attempt < 50000 && !placed; attempt++) {
                ts = ts * 1664525u + 1013904223u;
                int tx = TOWN_W + (int)((ts >> 16) % (unsigned)(MAP_WIDTH  - 2*TOWN_W));
                ts = ts * 1664525u + 1013904223u;
                int ty = TOWN_H + (int)((ts >> 16) % (unsigned)(MAP_HEIGHT - 2*TOWN_H));
                int ddx = tx - cx, ddy = ty - cy;
                if (ddx*ddx + ddy*ddy <= (hw+TOWN_H)*(hw+TOWN_H)) continue;
                if (!footprint_ok(tx, ty)) continue;
                bool far_enough = true;
                for (int i = 0; i < 2 && far_enough; i++) {
                    if (map->towns[i].x < 0) continue;
                    int ddx2 = map->towns[i].x - tx;
                    int ddy2 = map->towns[i].y - ty;
                    if (ddx2*ddx2 + ddy2*ddy2 < MIN_TOWN_DIST*MIN_TOWN_DIST)
                        far_enough = false;
                }
                if (!far_enough) continue;
                stamp_town_blueprint(map, 2, tx, ty);
                placed = true;
            }
            if (!placed) map->towns[2] = { -1, -1, 2 };
        }
    }

    // --- Villages ---
    // 10-15 small settlements scattered across the map.
    // Dungeons are allowed inside village footprints (no tile pre-fill, so
    // underlying terrain stays and door_ok accepts it normally).
    {
        const int TARGET_VILLAGES   = 12;
        const int MIN_VILLAGE_DIST  = 150; // village-to-village (TL corner distance)
        const int MIN_TOWN_VIL_DIST = 300; // village-to-town
        const int MARGIN = 450; // ocean band is up to ~420 tiles wide; keep villages inland

        auto village_footprint_ok = [&](int tx, int ty) -> bool {
            for (int dy = 0; dy < VILLAGE_H; dy++)
                for (int dx = 0; dx < VILLAGE_W; dx++) {
                    int bt = map->tiles[ty+dy][tx+dx];
                    if (bt == TILE_WATER || bt == TILE_RIVER) return false;
                    if (is_cliff(bt)) return false;
                }
            return true;
        };

        map->num_villages = 0;
        unsigned int vs = seed ^ 0xA71B4C03u;

        for (int attempt = 0; map->num_villages < TARGET_VILLAGES && attempt < 200000; attempt++) {
            vs = vs * 1664525u + 1013904223u;
            int tx = MARGIN + (int)((vs >> 16) % (unsigned)(MAP_WIDTH  - 2*MARGIN));
            vs = vs * 1664525u + 1013904223u;
            int ty = MARGIN + (int)((vs >> 16) % (unsigned)(MAP_HEIGHT - 2*MARGIN));

            // Stay outside the center hub area
            int ddx = tx - cx, ddy = ty - cy;
            if (ddx*ddx + ddy*ddy <= (hw+VILLAGE_H)*(hw+VILLAGE_H)) continue;

            if (!village_footprint_ok(tx, ty)) continue;

            // Far from all towns
            bool ok = true;
            for (int i = 0; i < 3 && ok; i++) {
                if (map->towns[i].x < 0) continue;
                int dx2 = map->towns[i].x - tx, dy2 = map->towns[i].y - ty;
                if (dx2*dx2 + dy2*dy2 < MIN_TOWN_VIL_DIST*MIN_TOWN_VIL_DIST) ok = false;
            }
            if (!ok) continue;

            // Far from all existing villages
            for (int i = 0; i < map->num_villages && ok; i++) {
                int dx2 = map->villages[i].x - tx, dy2 = map->villages[i].y - ty;
                if (dx2*dx2 + dy2*dy2 < MIN_VILLAGE_DIST*MIN_VILLAGE_DIST) ok = false;
            }
            if (!ok) continue;

            vs = vs * 1664525u + 1013904223u;
            int variant = (int)((vs >> 16) % NUM_VILLAGE_VARIANTS);
            stamp_village_blueprint(map, variant, tx, ty);
        }
    }

    // --- Castles ---
    // castle[3] (dungeon) is left at {-1,-1,3} — placed externally via dungeon diving.
    {
        // -- Castle 0: ocean — all-water footprint inside the ocean band --
        {
            const int BAND = 520; // ocean is ~300-420 tiles wide; 520 gives safe margin
            bool placed = false;
            unsigned int cs = seed ^ 0xCA5710E1u;
            for (int attempt = 0; attempt < 200000 && !placed; attempt++) {
                cs = cs * 1664525u + 1013904223u; int r1 = (int)((cs >> 16) % (unsigned)MAP_WIDTH);
                cs = cs * 1664525u + 1013904223u; int r2 = (int)((cs >> 16) % (unsigned)MAP_HEIGHT);
                int tx, ty;
                if      (ocean_side == 0) { tx = r1 % (BAND - CASTLE_W);                              ty = r2 % (MAP_HEIGHT - CASTLE_H); }
                else if (ocean_side == 1) { tx = MAP_WIDTH  - BAND + r1 % (BAND - CASTLE_W);          ty = r2 % (MAP_HEIGHT - CASTLE_H); }
                else if (ocean_side == 2) { tx = r1 % (MAP_WIDTH - CASTLE_W);                         ty = r2 % (BAND - CASTLE_H); }
                else                      { tx = r1 % (MAP_WIDTH - CASTLE_W); ty = MAP_HEIGHT - BAND + r2 % (BAND - CASTLE_H); }
                if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                bool all_water = true;
                for (int dy = 0; dy < CASTLE_H && all_water; dy++)
                    for (int dx = 0; dx < CASTLE_W && all_water; dx++)
                        if (map->tiles[ty+dy][tx+dx] != TILE_WATER) all_water = false;
                if (!all_water) continue;
                stamp_castle_blueprint(map, 0, tx, ty);
                placed = true;
            }
        }

        // -- Castle 1: mountain — nearest elevation-5 footprint to cliff peak --
        // Collects all elevation-5 tiles, sorts by distance from cliff_peak,
        // then walks the sorted list — O(N log N) on just the elev-5 tiles rather
        // than O((W+H)^2) ring expansion over the whole map.
        {
            float px = map->cliff_peak_x / TILE_SIZE;
            float py = map->cliff_peak_y / TILE_SIZE;

            std::vector<std::pair<float,std::pair<int,int>>> elev5_tiles;
            for (int y = 0; y < MAP_HEIGHT; y++) {
                for (int x = 0; x < MAP_WIDTH; x++) {
                    int t = map->tiles[y][x];
                    if (t != TILE_CLIFF_5 && t != TILE_CLIFF_SNOW_5 && t != TILE_CLIFF_WASTE_5) continue;
                    float dx = x - px, dy2 = y - py;
                    elev5_tiles.push_back({ dx*dx + dy2*dy2, {x, y} });
                }
            }
            std::sort(elev5_tiles.begin(), elev5_tiles.end());

            for (auto& entry : elev5_tiles) {
                int tx = entry.second.first  - CASTLE_W / 2;
                int ty = entry.second.second - CASTLE_H / 2;
                if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                bool water_free = true;
                int elev5_count = 0;
                for (int cdy = 0; cdy < CASTLE_H && water_free; cdy++)
                    for (int cdx = 0; cdx < CASTLE_W; cdx++) {
                        int bt = map->tiles[ty+cdy][tx+cdx];
                        if (bt == TILE_WATER || bt == TILE_RIVER) { water_free = false; break; }
                        if (bt == TILE_CLIFF_5 || bt == TILE_CLIFF_SNOW_5 || bt == TILE_CLIFF_WASTE_5) elev5_count++;
                    }
                if (!water_free || elev5_count * 2 < CASTLE_W * CASTLE_H) continue;
                stamp_castle_blueprint(map, 1, tx, ty);
                break;
            }
        }

        // -- Castle 2: lava/wasteland --
        // Pass 0 (strict): entire footprint must be wasteland/lava.
        // Pass 1 (relaxed): fallback for seeds where wasteland is all uneven —
        //   accepts >= 75% wasteland/lava with no water.
        {
            std::vector<std::pair<int,int>> lava_tiles;
            for (int y = 0; y < MAP_HEIGHT; y++)
                for (int x = 0; x < MAP_WIDTH; x++)
                    if (map->tiles[y][x] == TILE_LAVA)
                        lava_tiles.push_back({x, y});
            bool placed = false;
            if (!lava_tiles.empty()) {
                for (int pass = 0; pass < 2 && !placed; pass++) {
                    unsigned int ls = seed ^ 0xA55A001Bu;
                    ls = ls * 1664525u + 1013904223u;
                    int start = (int)((ls >> 16) % (unsigned)lava_tiles.size());
                    for (int i = 0; i < (int)lava_tiles.size() && !placed; i++) {
                        int idx = (start + i) % (int)lava_tiles.size();
                        int tx = lava_tiles[idx].first  - CASTLE_W / 2;
                        int ty = lava_tiles[idx].second - CASTLE_H / 2;
                        if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                        int waste_count = 0; bool valid = true;
                        for (int dy = 0; dy < CASTLE_H && valid; dy++)
                            for (int dx = 0; dx < CASTLE_W && valid; dx++) {
                                int bt = map->tiles[ty+dy][tx+dx];
                                if (bt == TILE_WATER || bt == TILE_RIVER) { valid = false; break; }
                                if (is_cliff_slope(bt))                    { valid = false; break; }
                                if (bt == TILE_WASTELAND || bt == TILE_LAVA) waste_count++;
                                else if (pass == 0) { valid = false; break; }
                            }
                        if (!valid) continue;
                        if (pass == 1 && waste_count * 4 < CASTLE_W * CASTLE_H * 3) continue;
                        stamp_castle_blueprint(map, 2, tx, ty);
                        placed = true;
                    }
                }
            }
        }
    }

    // --- Dungeon entrances ---
    // 300 entrances spread across the map.  Each is randomly either:
    //   small (size=0): 1×1 tile stamp
    //   large (size=1): 2×2 tile stamp
    // Size is stored on the entrance and will drive what structure spawns later.
    // Grid-cell shuffle + MIN_DIST keeps all entrances well separated.
    {
        const int TARGET   = 300;
        const int MIN_DIST = 130; // minimum tile distance between any two top-left corners
        const int CELL     = 150; // one entrance attempted per CELL×CELL region
        const int MARGIN   = 6;   // clearance from map edges

        const int GW = (MAP_WIDTH  + CELL - 1) / CELL;
        const int GH = (MAP_HEIGHT + CELL - 1) / CELL;

        map->num_dungeon_entrances = 0;
        unsigned int es = seed ^ 0xD06E0015u;

        // Fisher-Yates shuffle of cell indices so placement isn't grid-aligned
        std::vector<int> cells;
        cells.reserve(GW * GH);
        for (int i = 0; i < GW * GH; i++) cells.push_back(i);
        for (int i = (int)cells.size() - 1; i > 0; i--) {
            es = es * 1664525u + 1013904223u;
            int j = (int)((es >> 16) % (unsigned)(i + 1));
            std::swap(cells[i], cells[j]);
        }

        // Returns true if a sz×sz stamp at (ex,ey) is valid ground, outside hub, far from others.
        auto door_ok = [&](int ex, int ey, int sz) -> bool {
            if (ex < MARGIN || ey < MARGIN ||
                ex + sz + MARGIN > MAP_WIDTH ||
                ey + sz + MARGIN > MAP_HEIGHT)
                return false;
            for (int dy = 0; dy < sz; dy++) {
                for (int dx = 0; dx < sz; dx++) {
                    int tx = ex + dx, ty = ey + dy;
                    int ddx = tx - cx, ddy = ty - cy;
                    if (ddx*ddx + ddy*ddy <= hw*hw) return false;
                    int base = map->tiles[ty][tx];
                    if (base == TILE_VILLAGE_PLACEHOLDER) {
                        // Villages allow dungeon entrances
                    } else if (base == TILE_BLUEPRINT || base == TILE_CASTLE_PLACEHOLDER) {
                        return false; // towns and castles don't
                    } else {
                        if (base != TILE_GRASS     && base != TILE_MEADOW &&
                            base != TILE_SAND      && base != TILE_SNOW   &&
                            base != TILE_WASTELAND) return false;
                        if (map->overlay[ty][tx] != 0) return false;
                    }
                }
            }
            for (int i = 0; i < map->num_dungeon_entrances; i++) {
                int ddx = map->dungeon_entrances[i].x - ex;
                int ddy = map->dungeon_entrances[i].y - ey;
                if (ddx*ddx + ddy*ddy < MIN_DIST * MIN_DIST) return false;
            }
            // Reject positions inside any town footprint
            for (int i = 0; i < 3; i++) {
                if (map->towns[i].x < 0) continue;
                int tw = map->towns[i].x, th = map->towns[i].y;
                if (ex + sz > tw && ex < tw + TOWN_W &&
                    ey + sz > th && ey < th + TOWN_H) return false;
            }
            // Reject positions inside any castle footprint
            for (int i = 0; i < 4; i++) {
                if (map->castles[i].x < 0) continue;
                int cax = map->castles[i].x, cay = map->castles[i].y;
                if (ex + sz > cax && ex < cax + CASTLE_W &&
                    ey + sz > cay && ey < cay + CASTLE_H) return false;
            }
            return true;
        };

        for (int ci : cells) {
            if (map->num_dungeon_entrances >= TARGET) break;
            int cellx = (ci % GW) * CELL;
            int celly = (ci / GW) * CELL;
            for (int attempt = 0; attempt < 12; attempt++) {
                es = es * 1664525u + 1013904223u;
                int ex = cellx + (int)((es >> 16) % (unsigned)CELL);
                es = es * 1664525u + 1013904223u;
                int ey = celly + (int)((es >> 16) % (unsigned)CELL);
                // ~50% small (1×1), ~50% large (2×2)
                es = es * 1664525u + 1013904223u;
                int sz = ((es >> 16) & 1) ? 2 : 1;
                if (!door_ok(ex, ey, sz)) continue;
                for (int dy = 0; dy < sz; dy++)
                    for (int dx = 0; dx < sz; dx++) {
                        map->tiles[ey + dy][ex + dx] = TILE_DUNGEON;
                        map->overlay[ey + dy][ex + dx] = 0;
                    }
                // size field: 0=small(1×1), 1=large(2×2)
                map->dungeon_entrances[map->num_dungeon_entrances++] = {ex, ey, sz - 1};
                break;
            }
        }
    }
}

static void draw_tile_ascii(SDL_Renderer* renderer, int tile_id,
    int screen_x, int screen_y, int draw_size) {
    if (tile_id < 0 || tile_id >= NUM_TILE_STYLES) return;

    const TileStyle* s = &tile_styles[tile_id];

    // Fill background
    SDL_SetRenderDrawColor(renderer, s->bg_r, s->bg_g, s->bg_b, 255);
    SDL_Rect bg = { screen_x, screen_y, draw_size, draw_size };
    SDL_RenderFillRect(renderer, &bg);

    // Draw glyph only when tiles are big enough to be readable
    const int scale = draw_size / 8;
    if (scale < 1) return;
    SDL_SetRenderDrawColor(renderer, s->fg_r, s->fg_g, s->fg_b, 255);
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (s->glyph[row] & (0x80u >> col)) {
                SDL_Rect px = {
                    screen_x + col * scale,
                    screen_y + row * scale,
                    scale, scale
                };
                SDL_RenderFillRect(renderer, &px);
            }
        }
    }
}

static void draw_glyph_only(SDL_Renderer* renderer, const uint8_t* glyph,
                             uint8_t fr, uint8_t fg_col, uint8_t fb,
                             int screen_x, int screen_y, int draw_size) {
    const int scale = draw_size / 8;
    if (scale < 1) return;
    SDL_SetRenderDrawColor(renderer, fr, fg_col, fb, 255);
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (glyph[row] & (0x80u >> col)) {
                SDL_Rect px = {
                    screen_x + col * scale,
                    screen_y + row * scale,
                    scale, scale
                };
                SDL_RenderFillRect(renderer, &px);
            }
        }
    }
}

// Paint one tile type into an SDL_Surface using the same bg+glyph logic as draw_tile_ascii.
// Works on any SDL2 backend — no render-to-texture needed.
static SDL_Surface* make_tile_surf(const TileStyle* s) {
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(
        0, TILE_SIZE, TILE_SIZE, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return nullptr;
    SDL_FillRect(surf, NULL, SDL_MapRGB(surf->format, s->bg_r, s->bg_g, s->bg_b));
    const int scale = TILE_SIZE / 8;
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (s->glyph[row] & (0x80u >> col)) {
                SDL_Rect px = { col * scale, row * scale, scale, scale };
                SDL_FillRect(surf, &px, SDL_MapRGB(surf->format, s->fg_r, s->fg_g, s->fg_b));
            }
        }
    }
    return surf;
}

static SDL_Surface* make_glyph_surf(uint8_t bg_r, uint8_t bg_g, uint8_t bg_b,
                                    uint8_t fg_r, uint8_t fg_g, uint8_t fg_b,
                                    const uint8_t* glyph) {
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(
        0, TILE_SIZE, TILE_SIZE, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return nullptr;
    SDL_FillRect(surf, NULL, SDL_MapRGB(surf->format, bg_r, bg_g, bg_b));
    const int scale = TILE_SIZE / 8;
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (glyph[row] & (0x80u >> col)) {
                SDL_Rect px = { col * scale, row * scale, scale, scale };
                SDL_FillRect(surf, &px, SDL_MapRGB(surf->format, fg_r, fg_g, fg_b));
            }
        }
    }
    return surf;
}

void tilemap_init_tile_cache(SDL_Renderer* renderer) {
    for (int i = 0; i < TILE_CACHE_SIZE && i < NUM_TILE_STYLES; i++) {
        SDL_Surface* surf = make_tile_surf(&tile_styles[i]);
        if (!surf) continue;
        s_tile_tex[i] = SDL_CreateTextureFromSurface(renderer, surf);
        SDL_FreeSurface(surf);
    }
    SDL_Surface* top_surf = make_glyph_surf(0, 40, 0, 0, 140, 0, glyph_tall_tree_top);
    SDL_Surface* bot_surf = make_glyph_surf(0, 40, 0, 0, 140, 0, glyph_tall_tree_bot);
    if (top_surf) { s_tall_tree_top_tex = SDL_CreateTextureFromSurface(renderer, top_surf); SDL_FreeSurface(top_surf); }
    if (bot_surf) { s_tall_tree_bot_tex  = SDL_CreateTextureFromSurface(renderer, bot_surf); SDL_FreeSurface(bot_surf); }
}

void tilemap_free_tile_cache(void) {
    for (int i = 0; i < TILE_CACHE_SIZE; i++) {
        if (s_tile_tex[i]) { SDL_DestroyTexture(s_tile_tex[i]); s_tile_tex[i] = nullptr; }
    }
    if (s_tall_tree_top_tex) { SDL_DestroyTexture(s_tall_tree_top_tex); s_tall_tree_top_tex = nullptr; }
    if (s_tall_tree_bot_tex)  { SDL_DestroyTexture(s_tall_tree_bot_tex);  s_tall_tree_bot_tex  = nullptr; }
}

// Helper: copy a cached tile texture to the screen, falling back to immediate draw.
static void blit_tile(SDL_Renderer* renderer, int tile_id,
                      int screen_x, int screen_y, int draw_size) {
    if (tile_id >= 0 && tile_id < TILE_CACHE_SIZE && s_tile_tex[tile_id]) {
        SDL_Rect dst = { screen_x, screen_y, draw_size, draw_size };
        SDL_RenderCopy(renderer, s_tile_tex[tile_id], NULL, &dst);
    } else {
        draw_tile_ascii(renderer, tile_id, screen_x, screen_y, draw_size);
    }
}

void tilemap_draw(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer) {
    float z = cam->zoom;
    int draw_size = (int)(TILE_SIZE * z);
    if (draw_size < 1) draw_size = 1;

    int start_x = (int)(cam->x / TILE_SIZE);
    int start_y = (int)(cam->y / TILE_SIZE);
    // How many tiles fit on screen at this zoom level
    int tiles_wide = (int)(cam->screen_w / z / TILE_SIZE) + 2;
    int tiles_tall = (int)(cam->screen_h / z / TILE_SIZE) + 2;
    int end_x = start_x + tiles_wide;
    int end_y = start_y + tiles_tall;

    if (start_x < 0)         start_x = 0;
    if (start_y < 0)         start_y = 0;
    if (end_x > MAP_WIDTH)   end_x = MAP_WIDTH;
    if (end_y > MAP_HEIGHT)  end_y = MAP_HEIGHT;

    for (int y = start_y; y < end_y; y++) {
        for (int x = start_x; x < end_x; x++) {
            int screen_x = (int)((x * TILE_SIZE - cam->x) * z);
            int screen_y = (int)((y * TILE_SIZE - cam->y) * z);
            // Draw base tile
            blit_tile(renderer, map->tiles[y][x], screen_x, screen_y, draw_size);

            // Draw overlay (trees, rocks, gold ore) on top
            int ov = map->overlay[y][x];
            if (ov == TILE_TREE) {
                bool tree_above = (y > 0            && map->overlay[y-1][x] == TILE_TREE);
                bool tree_below = (y < MAP_HEIGHT-1 && map->overlay[y+1][x] == TILE_TREE);

                // Jitter offset — shake horizontally on hit
                int jox = 0;
                {
                    auto jit = s_tile_jitter.find(tile_key(x, y));
                    if (jit != s_tile_jitter.end()) {
                        float elapsed = (float)((double)(SDL_GetPerformanceCounter() - jit->second)
                                                / SDL_GetPerformanceFrequency());
                        jox = (int)(sinf(elapsed * 80.0f) * 4.0f * z);
                    }
                }
                int dx = screen_x + jox;

                if (tree_above) {
                    // Bottom of tall pair: trunk here, canopy drawn into tile above
                    SDL_Rect dst_bot = { dx, screen_y, draw_size, draw_size };
                    SDL_Rect dst_top = { dx, screen_y - draw_size, draw_size, draw_size };
                    if (s_tall_tree_bot_tex) {
                        SDL_RenderCopy(renderer, s_tall_tree_bot_tex, NULL, &dst_bot);
                    } else {
                        SDL_SetRenderDrawColor(renderer, 0, 40, 0, 255);
                        SDL_RenderFillRect(renderer, &dst_bot);
                        draw_glyph_only(renderer, glyph_tall_tree_bot, 0, 140, 0, dx, screen_y, draw_size);
                    }
                    if (s_tall_tree_top_tex) {
                        SDL_RenderCopy(renderer, s_tall_tree_top_tex, NULL, &dst_top);
                    } else {
                        draw_glyph_only(renderer, glyph_tall_tree_top, 0, 140, 0, dx, screen_y - draw_size, draw_size);
                    }
                } else if (!tree_below) {
                    // Single tree — s_tile_tex[TILE_TREE] has the same bg+glyph
                    SDL_Rect dst = { dx, screen_y, draw_size, draw_size };
                    if (s_tile_tex[TILE_TREE]) {
                        SDL_RenderCopy(renderer, s_tile_tex[TILE_TREE], NULL, &dst);
                    } else {
                        SDL_SetRenderDrawColor(renderer, 0, 40, 0, 255);
                        SDL_RenderFillRect(renderer, &dst);
                        draw_glyph_only(renderer, glyph_tree, 0, 140, 0, dx, screen_y, draw_size);
                    }
                } else {
                    // Top of tall pair: bg only (glyph is drawn when processing the tile below)
                    SDL_SetRenderDrawColor(renderer, 0, 40, 0, 255);
                    SDL_Rect bg = { dx, screen_y, draw_size, draw_size };
                    SDL_RenderFillRect(renderer, &bg);
                }
            } else if (ov != 0) {
                // Rocks, gold ore — draw over base with optional jitter
                int draw_x = screen_x;
                if (ov == TILE_ROCK) {
                    auto jit = s_tile_jitter.find(tile_key(x, y));
                    if (jit != s_tile_jitter.end()) {
                        float elapsed = (float)((double)(SDL_GetPerformanceCounter() - jit->second)
                                                / SDL_GetPerformanceFrequency());
                        draw_x += (int)(sinf(elapsed * 80.0f) * 4.0f * z);
                    }
                }
                blit_tile(renderer, ov, draw_x, screen_y, draw_size);
            }
        }
    }
}

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y)
{
    // Pick a step size so the minimap fits within 80% of the screen
    int max_dim = (screen_w < screen_h ? screen_w : screen_h) * 4 / 5;
    int step = 1;
    while (MAP_WIDTH / step > max_dim || MAP_HEIGHT / step > max_dim)
        step++;
    const int mw = (MAP_WIDTH  / step);
    const int mh = (MAP_HEIGHT / step);
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    // semi-transparent dark background
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 180);
    SDL_Rect bg = { ox - 4, oy - 4, mw + 8, mh + 8 };
    SDL_RenderFillRect(renderer, &bg);

    // Priority order for block sampling: higher = wins over lower tiles in block.
    // TREE and ROCK have priority 0 so they render as grass (not drawn separately).
    static const int tile_priority[] = {
        0, 0, 0, 2, 1, 0, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, // 0-22: GRASS..POND
        0,                                                                         // 23: GOLD_ORE → hidden
        1, 1, 1, 1, 1,                                                            // 24-28: snow cliffs
        1, 1, 1, 1, 1,                                                            // 29-33: wasteland cliffs
        0, 0, 0, 0, 0,                                                            // 34-38: side tiles → hidden
        0, 0, 0, 0, 0,                                                            // 39-43: SW corners → hidden
        0, 0, 0, 0, 0,                                                            // 44-48: SE corners → hidden
        0, 0, 0, 0, 0,                                                            // 49-53: NW inner corners → hidden
        0, 0, 0, 0, 0,                                                            // 54-58: NE inner corners → hidden
        2,                                                                         // 59: DUNGEON → always show
        2,                                                                         // 60: BLUEPRINT → always show
        2,                                                                         // 61: VILLAGE_PLACEHOLDER → always show
        2,                                                                         // 62: CASTLE_PLACEHOLDER → always show
    };
    static const SDL_Color tile_colors[] = {
        { 30,  90,  30, 255}, // GRASS  (dark green = dense forest)
        { 30,  90,  30, 255}, // PATH   → grass
        { 20,  70,  20, 255}, // TREE   → darker green
        { 30,  90, 200, 255}, // WATER
        {100,  95,  88, 255}, // CLIFF   elev 1
        { 30,  90,  30, 255}, // ROCK   → grass
        { 30,  90, 200, 255}, // RIVER
        { 30,  90, 200, 255}, // HUB
        {120, 113, 104, 255}, // CLIFF_2 elev 2
        {140, 132, 120, 255}, // CLIFF_3 elev 3
        {160, 150, 136, 255}, // CLIFF_4 elev 4
        {180, 168, 152, 255}, // CLIFF_5 elev 5
        { 60, 160,  60, 255}, // CLIFF_EDGE_1 → hidden (grass)
        { 60, 160,  60, 255}, // CLIFF_EDGE_2 → hidden
        { 60, 160,  60, 255}, // CLIFF_EDGE_3 → hidden
        { 60, 160,  60, 255}, // CLIFF_EDGE_4 → hidden
        { 60, 160,  60, 255}, // CLIFF_EDGE_5 → hidden
        {200, 170,  95, 255}, // SAND
        {220, 235, 255, 255}, // SNOW
        { 65,  55,  45, 255}, // WASTELAND
        {200,  70,   0, 255}, // LAVA
        { 80, 160,  40, 255}, // MEADOW
        { 30,  90, 200, 255}, // POND
        { 60,  55,  50, 255}, // GOLD_ORE → hidden (dark)
        {130, 160, 195, 255}, // CLIFF_SNOW_1  (24)
        {122, 152, 188, 255}, // CLIFF_SNOW_2  (25)
        {114, 144, 180, 255}, // CLIFF_SNOW_3  (26)
        {106, 136, 173, 255}, // CLIFF_SNOW_4  (27)
        { 98, 128, 165, 255}, // CLIFF_SNOW_5  (28)
        { 52,  38,  28, 255}, // CLIFF_WASTE_1 (29)
        { 60,  44,  32, 255}, // CLIFF_WASTE_2 (30)
        { 68,  50,  36, 255}, // CLIFF_WASTE_3 (31)
        { 76,  56,  40, 255}, // CLIFF_WASTE_4 (32)
        { 85,  62,  44, 255}, // CLIFF_WASTE_5 (33)
        { 60, 160,  60, 255}, // CLIFF_SIDE_1    (34) → hidden
        { 60, 160,  60, 255}, // CLIFF_SIDE_2    (35) → hidden
        { 60, 160,  60, 255}, // CLIFF_SIDE_3    (36) → hidden
        { 60, 160,  60, 255}, // CLIFF_SIDE_4    (37) → hidden
        { 60, 160,  60, 255}, // CLIFF_SIDE_5    (38) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SW_1 (39) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SW_2 (40) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SW_3 (41) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SW_4 (42) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SW_5 (43) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SE_1 (44) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SE_2 (45) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SE_3 (46) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SE_4 (47) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_SE_5 (48) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NW_1 (49) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NW_2 (50) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NW_3 (51) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NW_4 (52) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NW_5 (53) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NE_1 (54) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NE_2 (55) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NE_3 (56) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NE_4 (57) → hidden
        { 60, 160,  60, 255}, // CLIFF_CORNER_NE_5 (58) → hidden
        {  5,   0,  15, 255}, // DUNGEON              (59) → dark purple dot
        {255,   0, 255, 255}, // BLUEPRINT            (60) → bright magenta
        {255, 140,   0, 255}, // VILLAGE_PLACEHOLDER  (61) → orange
        {255, 255, 255, 255}, // CASTLE_PLACEHOLDER   (62) → white
    };
    static const int NUM_MM_COLORS = (int)(sizeof(tile_colors) / sizeof(tile_colors[0]));

    for (int y = 0; y < MAP_HEIGHT; y += step) {
        for (int x = 0; x < MAP_WIDTH; x += step) {
            // Scan the full step×step block, keep highest-priority tile
            int best_id = TILE_GRASS;
            int best_pri = -1;
            int x1 = x + step < MAP_WIDTH  ? x + step : MAP_WIDTH;
            int y1 = y + step < MAP_HEIGHT ? y + step : MAP_HEIGHT;
            for (int by = y; by < y1; by++) {
                for (int bx = x; bx < x1; bx++) {
                    int id = map->tiles[by][bx];
                    if (id >= 0 && id < NUM_MM_COLORS && tile_priority[id] > best_pri) {
                        best_pri = tile_priority[id];
                        best_id  = id;
                    }
                }
            }
            SDL_Color c = tile_colors[best_id];
            SDL_SetRenderDrawColor(renderer, c.r, c.g, c.b, 255);
            SDL_Rect r = { ox + x / step, oy + y / step, 1, 1 };
            SDL_RenderFillRect(renderer, &r);
        }
    }

    // villages — 3×3 orange dot centered on footprint
    for (int i = 0; i < map->num_villages; i++) {
        if (map->villages[i].x < 0) continue;
        int vx = ox + (map->villages[i].x + VILLAGE_W / 2) / step;
        int vy = oy + (map->villages[i].y + VILLAGE_H / 2) / step;
        SDL_SetRenderDrawColor(renderer, 255, 140, 0, 255);
        SDL_Rect vdot = { vx - 1, vy - 1, 3, 3 };
        SDL_RenderFillRect(renderer, &vdot);
    }

    // castles — 4×4 white dot centered on footprint
    for (int i = 0; i < 4; i++) {
        if (map->castles[i].x < 0) continue;
        int cax = ox + (map->castles[i].x + CASTLE_W / 2) / step;
        int cay = oy + (map->castles[i].y + CASTLE_H / 2) / step;
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
        SDL_Rect cdot = { cax - 2, cay - 2, 4, 4 };
        SDL_RenderFillRect(renderer, &cdot);
    }

    // white 3×3 dot for player position
    int px = ox + (int)(player_x / TILE_SIZE) / step;
    int py = oy + (int)(player_y / TILE_SIZE) / step;
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect dot = { px - 1, py - 1, 3, 3 };
    SDL_RenderFillRect(renderer, &dot);

    // red 5×5 dot for cliff gradient peak (debug)
    int peakdot_x = ox + (int)(map->cliff_peak_x) / step;
    int peakdot_y = oy + (int)(map->cliff_peak_y) / step;
    SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
    SDL_Rect peak_dot = { peakdot_x - 2, peakdot_y - 2, 5, 5 };
    SDL_RenderFillRect(renderer, &peak_dot);

    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
}

bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y)
{
    // Mirror the step/offset calculation from minimap_draw exactly
    int max_dim = (screen_w < screen_h ? screen_w : screen_h) * 4 / 5;
    int step = 1;
    while (MAP_WIDTH / step > max_dim || MAP_HEIGHT / step > max_dim)
        step++;
    const int mw = MAP_WIDTH  / step;
    const int mh = MAP_HEIGHT / step;
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    // Check the click is inside the minimap rectangle
    if (mx < ox || mx >= ox + mw || my < oy || my >= oy + mh)
        return false;

    int tile_x = (mx - ox) * step;
    int tile_y = (my - oy) * step;
    *out_world_x = (float)(tile_x * TILE_SIZE);
    *out_world_y = (float)(tile_y * TILE_SIZE);
    return true;
}

// ---------------------------------------------------------------------------
// Tile hit / destruction
// ---------------------------------------------------------------------------
// Only tracks tiles that have taken at least one hit (memory-efficient).
static std::unordered_map<uint32_t, int> s_tile_hp;

// Returns the bottom-tile key and HP for a tree/rock at (tx,ty).
// For tall trees the bottom tile is the key so both tiles share the same pool.
static int tile_max_hp(const Tilemap* map, int tx, int ty) {
    int t = map->overlay[ty][tx];
    if (t == TILE_ROCK)     return 3;
    if (t == TILE_GOLD_ORE) return 5;
    if (t == TILE_TREE) {
        // "bottom" tile has tree above it
        bool paired = (ty > 0 && map->overlay[ty-1][tx] == TILE_TREE);
        return paired ? 4 : 2;
    }
    return 0;
}

int tilemap_try_hit(Tilemap* map, float px, float py, int range, float* out_rx, float* out_ry) {
    int tx0 = (int)((px - range) / TILE_SIZE); if (tx0 < 0) tx0 = 0;
    int ty0 = (int)((py - range) / TILE_SIZE); if (ty0 < 0) ty0 = 0;
    int tx1 = (int)((px + range) / TILE_SIZE); if (tx1 >= MAP_WIDTH)  tx1 = MAP_WIDTH  - 1;
    int ty1 = (int)((py + range) / TILE_SIZE); if (ty1 >= MAP_HEIGHT) ty1 = MAP_HEIGHT - 1;

    // Find closest hittable tile within range
    float best_dist2 = (float)(range * range) * 2.0f + 1.0f;
    int best_tx = -1, best_ty = -1;
    for (int ty = ty0; ty <= ty1; ty++) {
        for (int tx = tx0; tx <= tx1; tx++) {
            int t = map->overlay[ty][tx];
            if (t != TILE_TREE && t != TILE_ROCK && t != TILE_GOLD_ORE) continue;
            float dx = (tx + 0.5f) * TILE_SIZE - px;
            float dy = (ty + 0.5f) * TILE_SIZE - py;
            float d2 = dx*dx + dy*dy;
            if (d2 < best_dist2) { best_dist2 = d2; best_tx = tx; best_ty = ty; }
        }
    }
    if (best_tx < 0) return 0;

    if (out_rx) *out_rx = (best_tx + 0.5f) * TILE_SIZE;
    if (out_ry) *out_ry = (best_ty + 0.5f) * TILE_SIZE;

    int tx = best_tx, ty = best_ty;
    int t = map->overlay[ty][tx];

    // Normalize to the bottom tile of a tall-tree pair
    int key_tx = tx, key_ty = ty;
    bool is_tall = false;
    if (t == TILE_TREE) {
        bool above = (ty > 0            && map->overlay[ty-1][tx] == TILE_TREE);
        bool below = (ty+1 < MAP_HEIGHT && map->overlay[ty+1][tx] == TILE_TREE);
        is_tall = above || below;
        if (below && !above) key_ty = ty + 1; // hit the top tile — key to bottom
    }

    uint32_t key = tile_key(key_tx, key_ty);
    int max_hp = tile_max_hp(map, key_tx, key_ty);

    auto it = s_tile_hp.find(key);
    int hp = (it == s_tile_hp.end()) ? max_hp : it->second;
    hp--;

    if (hp <= 0) {
        s_tile_hp.erase(key);
        s_tile_jitter.erase(key);
        if (is_tall) s_tile_jitter.erase(tile_key(key_tx, key_ty - 1));
        // Clear overlay — base tile is always correct underneath
        map->overlay[key_ty][key_tx] = 0;
        if (is_tall && key_ty > 0 && map->overlay[key_ty-1][key_tx] == TILE_TREE)
            map->overlay[key_ty-1][key_tx] = 0;
        return 1; // destroyed
    }

    s_tile_hp[key] = hp;
    // Trigger jitter on both tiles of a tall pair — store start timestamp
    Uint64 now = SDL_GetPerformanceCounter();
    s_tile_jitter[key] = now;
    if (is_tall && key_ty > 0)
        s_tile_jitter[tile_key(key_tx, key_ty - 1)] = now;
    return 2; // hit but not destroyed
}

void tilemap_update(float /*dt*/) {
    Uint64 now  = SDL_GetPerformanceCounter();
    double freq = (double)SDL_GetPerformanceFrequency();
    for (auto it = s_tile_jitter.begin(); it != s_tile_jitter.end(); ) {
        float elapsed = (float)((double)(now - it->second) / freq);
        if (elapsed >= JITTER_DUR) it = s_tile_jitter.erase(it);
        else ++it;
    }
}

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y) {
    if (!in_bounds(tile_x, tile_y)) return false;

    switch (map->tiles[tile_y][tile_x]) {
        case TILE_GRASS:
        case TILE_PATH:
        case TILE_SAND:
        case TILE_SNOW:
        case TILE_WASTELAND:
        case TILE_MEADOW:
            return true;
        default:
            return false;
    }
}
