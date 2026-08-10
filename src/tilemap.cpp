#include "tilemap.h"
#include "core.h"
#include <SDL2/SDL_image.h>
#include "resource_node.h"
#include "towns.h"
#include "castles.h"
#include <stdint.h>
#include <climits>
#include <math.h>
#include <string.h>
#include <algorithm>
#include <unordered_map>
#include <vector>
#include <array>
#include <atomic>
#ifdef _WIN32
  #define WIN32_LEAN_AND_MEAN
  #define NOMINMAX
  #include <windows.h>
#else
  #include <pthread.h>
#endif

static std::atomic<bool> s_gen_cancel{false};
// Diagnostics for the wasteland trail router; a probe reads these.
int s_trail_edges = 0, s_trail_unroutable = 0, s_trail_tooshort = 0;
void tilemap_cancel_gen()       { s_gen_cancel = true; }
void tilemap_reset_gen_cancel() { s_gen_cancel = false; }

// ---------------------------------------------------------------------------
// Embedded 8x8 bitmap glyphs — one byte per row, MSB = leftmost pixel
// With TILE_SIZE=32, each bit renders as a 4x4 block.
// ---------------------------------------------------------------------------
static const uint8_t glyph_grass[8]  = {0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00}; // '.'
static const uint8_t glyph_path[8]   = {0x00,0x00,0x00,0x18,0x18,0x08,0x10,0x00}; // ','
static const uint8_t glyph_tree[8]        = {0xFE,0xFE,0x18,0x18,0x18,0x18,0x18,0x18}; // 'T'
static const uint8_t glyph_dead_tree[8]   = {0x66,0x3C,0x18,0x18,0x18,0x18,0x18,0x00}; // bare branches
// Tall tree (two stacked tree tiles): top = canopy, bottom = trunk
static const uint8_t glyph_water[8]  = {0x62,0x94,0x08,0x62,0x94,0x08,0x62,0x94}; // '~'
static const uint8_t glyph_bridge[8] = {0xFF,0x00,0xFF,0x00,0xFF,0x00,0xFF,0x00}; // planks
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
// Dungeon entrance archetypes
static const uint8_t glyph_dungeon_cave[8]    = {0x3C,0x7E,0xFF,0xFF,0xFF,0xFF,0x00,0x00}; // rocky arch, open below
static const uint8_t glyph_dungeon_ruins[8]   = {0xDB,0xFF,0xDB,0x00,0xDB,0xFF,0xDB,0x00}; // broken pillars
static const uint8_t glyph_dungeon_grave[8]   = {0x18,0x18,0xFF,0xFF,0x18,0x18,0x00,0x3C}; // cross + mound
static const uint8_t glyph_dungeon_oasis[8]   = {0x3C,0x42,0x99,0xBD,0xBD,0x99,0x42,0x3C}; // ring w/ interior
static const uint8_t glyph_dungeon_pyramid[8] = {0x18,0x18,0x3C,0x3C,0x7E,0xFF,0xFF,0x00}; // layered triangle
static const uint8_t glyph_dungeon_henge[8]   = {0x42,0xA5,0x81,0x00,0x00,0x81,0xA5,0x42}; // stones in ring
static const uint8_t glyph_dungeon_tree[8]    = {0x18,0x3C,0x7E,0xFF,0xFF,0x7E,0x3C,0x18}; // wide canopy+trunk
static const uint8_t glyph_dungeon_tree_trunk[8] = {0x7E,0x81,0x81,0x81,0x81,0x81,0x7E,0x00}; // tree trunk silhouette

struct TileStyle {
    uint8_t bg_r, bg_g, bg_b;
    uint8_t fg_r, fg_g, fg_b;
    const uint8_t* glyph;
};

static const TileStyle tile_styles[] = 
{
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
    // Dungeon entrance archetypes — all render as solid black squares (same as
    // TILE_DUNGEON) so they stand out clearly on the minimap.
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_CAVE         (63)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_RUINS        (64)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_GRAVEYARD_SM (65)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_GRAVEYARD_LG (66)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_OASIS        (67)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_PYRAMID      (68)
    {  0,   0,   0,    0,   0,   0, glyph_dungeon }, // TILE_DUNGEON_STONEHENGE   (69)
    { 40,  20,   5, 200, 120,  50, glyph_dungeon_tree_trunk }, // TILE_DUNGEON_LARGE_TREE   (70)
    { 40,  30,  20, 100,  80,  55, glyph_dead_tree         }, // TILE_DEAD_TREE             (71)
    { 62,  28,  14, 100,  60,  35, glyph_path              }, // TILE_WASTE_TRAIL           (72)
    { 84,  52,  26, 140,  96,  52, glyph_bridge            }, // TILE_WASTE_BRIDGE          (73)
    // East faces and north back-faces, same brown gradient as the west faces
    // they were split out of.
    {100,  65,  25,  140,  90,  40, glyph_cliff_side }, // TILE_CLIFF_SIDE_E_1 (74)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_side }, // TILE_CLIFF_SIDE_E_2 (75)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_side }, // TILE_CLIFF_SIDE_E_3 (76)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_side }, // TILE_CLIFF_SIDE_E_4 (77)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_side }, // TILE_CLIFF_SIDE_E_5 (78)
    {100,  65,  25,  140,  90,  40, glyph_cliff_side }, // TILE_CLIFF_BACK_1   (79)
    { 90,  58,  22,  130,  82,  36, glyph_cliff_side }, // TILE_CLIFF_BACK_2   (80)
    { 80,  52,  20,  120,  74,  32, glyph_cliff_side }, // TILE_CLIFF_BACK_3   (81)
    { 70,  46,  18,  110,  66,  28, glyph_cliff_side }, // TILE_CLIFF_BACK_4   (82)
    { 60,  40,  16,  100,  58,  24, glyph_cliff_side }, // TILE_CLIFF_BACK_5   (83)
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
static const int TILE_CACHE_SIZE = 84; // TILE_CLIFF_BACK_5 + 1
// Every id below TILE_TOWN0_BASE draws from tile_styles and gets a cached
// texture, so the three have to agree. They are three separate edits when a
// tile is added and it is the second one that gets forgotten, which shows up
// as a tile drawn from whatever is off the end of the table.
static_assert(NUM_TILE_STYLES == TILE_CACHE_SIZE,
              "tile_styles needs one entry per tile id below TILE_TOWN0_BASE");
static_assert(TILE_CACHE_SIZE == TILE_TOWN0_BASE,
              "TILE_CACHE_SIZE must cover exactly the non-sheet tile ids");
static SDL_Texture* s_tile_tex[TILE_CACHE_SIZE] = {};
static SDL_Texture* s_town0_tex          = nullptr;
static SDL_Texture* s_overworld0_tex     = nullptr;
// Biome edge fringes — see "Biome edge" below. Indexed by an eight-bit map of
// which surrounding tiles hold the other biome, so the mask depends on the
// whole neighbourhood rather than on one side at a time. That is what lets a
// corner round off instead of meeting at a right angle.
static const int EDGE_VARIANTS = 2;
static SDL_Texture* s_edge_tex[256][EDGE_VARIANTS] = {};
// Water is drawn differently: a crisp outline and a solid band of shallows on
// the land side of it. Its surface texture comes from the sheet cell itself.
// Variant-indexed like the fringe: the waterline carries a per-pixel jitter, so
// without a per-tile choice of pattern that jitter would repeat every tile.
static SDL_Texture* s_fill_tex[256][EDGE_VARIANTS]      = {};  // the body, hard-edged
static SDL_Texture* s_shore_out_tex[256][EDGE_VARIANTS] = {};  // shallows outside it
static SDL_Texture* s_shore_in_tex[256][EDGE_VARIANTS]  = {};  // shallows inside it

// ---------------------------------------------------------------------------

static bool in_bounds(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

// Generation tracing. Worldgen runs two dozen passes over the whole map, so
// when a shape in the finished world looks wrong there is no reading your way
// back to which pass made it. Defining GEN_TRACE lets a probe snapshot the grid
// at every stage boundary and diff consecutive pairs; without it this compiles
// to nothing and the shipping build is unchanged.
#ifdef GEN_TRACE
void gen_trace_stage(const Tilemap* map, const char* stage);
#define GEN_STAGE(map, name) gen_trace_stage((map), (name))
#else
#define GEN_STAGE(map, name) ((void)0)
#endif

// Ground an overlay must not stand in or overhang. Kept as a plain tile test
// rather than going through the biome table because worldgen calls it millions
// of times; if a new liquid tile is added it needs listing in both places.
static inline bool tile_id_is_liquid(int t) {
    return t == TILE_WATER || t == TILE_RIVER || t == TILE_HUB
        || t == TILE_POND  || t == TILE_LAVA;
}

// Trees, rocks and ore are drawn as if rooted in their tile, and the waterline
// is smoothed, so water rounds into tiles whose own id is still land. An
// overlay one tile from water can therefore overlap it, and only a clear 3x3
// guarantees a bank.
static bool overlay_site_dry(const Tilemap* map, int tx, int ty) {
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++) {
            int nx = tx + dx, ny = ty + dy;
            if (in_bounds(nx, ny) && tile_id_is_liquid(map->tiles[ny][nx])) return false;
        }
    return true;
}

// Trail, and the bridge that carries it over lava. Nothing destroyable stands
// on either: the overlays are cleared as the trail is painted over them, and
// the nodes placed later — gravestones, which are scattered when the player
// first comes near a graveyard — ask this before choosing a tile.
static inline bool tile_id_is_trail(int t) {
    return t == TILE_WASTE_TRAIL || t == TILE_WASTE_BRIDGE;
}

// Sweep the overlays after generation rather than testing at each placement:
// ponds and streams are carved after the trees are scattered, so a placement
// test would pass and then be overtaken by the water arriving beside it.
static void clear_overlays_near_liquid(Tilemap* map) {
    for (int y = 0; y < MAP_HEIGHT; y++) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int ov = map->overlay[y][x];
            if (ov == 0) continue;
            bool dry = overlay_site_dry(map, x, y);
            // A tree's canopy is drawn one tile up, so that tile needs the same
            // clearance or the crown hangs out over the water.
            if (dry && (ov == TILE_TREE || ov == TILE_DEAD_TREE) && y > 0)
                dry = overlay_site_dry(map, x, y - 1);
            if (!dry) map->overlay[y][x] = 0;
        }
    }
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
// A channel that can genuinely change direction.
//
// march_stream below advances one tile along a fixed primary axis every single
// step and only offsets the other one, so whatever it draws is a function of
// that axis: it can bend, but it can never doubleback, loop, or set off
// somewhere new. Widening its jitter just makes a wigglier straight line, which
// is exactly what lava looked like. This carries a heading and turns it
// instead, so the channel is free to go anywhere.
//
// The turn is smoothed rather than drawn fresh each step: an unsmoothed one
// would jitter about its heading and cancel out, where a persistent turn holds
// through a dozen steps and comes out as a sweeping bend.
static void march_wander(Tilemap* map, int sx, int sy, float angle,
                         unsigned int seed, int guard_cx, int guard_cy, int guard_r,
                         int brush_r, int max_steps, float turn_rate,
                         int target, int place)
{
    float fx = (float)sx, fy = (float)sy, turn = 0.0f;
    for (int i = 0; i < max_steps; i++) {
        seed = seed * 1664525u + 1013904223u;
        float kick = (float)((seed >> 16) % 2001u) / 1000.0f - 1.0f;   // -1 .. 1
        turn = turn * 0.92f + kick * turn_rate;
        angle += turn;
        fx += cosf(angle);
        fy += sinf(angle);
        int ix = (int)fx, iy = (int)fy;
        if (ix < 1 || iy < 1 || ix >= MAP_WIDTH - 1 || iy >= MAP_HEIGHT - 1) break;
        paint_stream_brush(map, ix, iy, brush_r, guard_cx, guard_cy, guard_r, target, place);
    }
}

// `trace`, when given, collects points along the path at intervals. Branches
// start from one of those, which is what turns a scatter of separate streams
// into a network that joins up.
static void march_stream(Tilemap* map, int sx, int sy,
                         float dir_x, float dir_y, unsigned int seed,
                         int guard_cx, int guard_cy, int guard_r,
                         int brush_r, int max_steps, int jitter_range,
                         int target, int place,
                         std::vector<std::pair<int,int>>* trace = nullptr)
{
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y)/fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x)/fabsf(dir_y) : 0.0f);
    float acc = 0.0f, smooth_j = 0.0f, drift = 0.0f;
    int steps = 0;
    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        float kick = (float)((int)(seed >> 16) % (2*jitter_range+1) - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        // Integrate the bias instead of truncating it. Truncating threw the
        // meander away: smoothing this heavily leaves a value whose spread is
        // well under one tile, so the cast rounded it to zero nearly every step
        // and the stream ran dead straight — jitter_range was doing nothing.
        // Accumulating turns that sub-tile bias into a step once it adds up to
        // a whole tile, which is what makes the path wander and keeps it smooth
        // while it does.
        drift += smooth_j;
        int jitter = (int)drift;
        drift -= (float)jitter;
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
        // Only where the stream actually laid something down: a point out on
        // bare grass is no use as a junction.
        if (trace && (steps % 10) == 0 && in_bounds(rx, ry) && map->tiles[ry][rx] == place)
            trace->push_back({ rx, ry });
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
// Canvas value encoding: 0=blank, 1=grass, 2=path, 3=hub, 4=water, 5=tree, >=6=sprite.
static void stamp_town_blueprint(Tilemap* map, int town_idx, int tx, int ty) {
    const int (*layout)[TOWN_W] = all_towns[town_idx];

    for (int dy = 0; dy < TOWN_H; dy++) {
        for (int dx = 0; dx < TOWN_W; dx++) {
            int val = layout[dy][dx];
            if (val == 0) continue;
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;

            int tile = -1;
            if (val == 5) {
                map->overlay[wy][wx] = TILE_TREE;
                continue;
            } else if (val == 1) { tile = TILE_GRASS;
            } else if (val == 2) { tile = TILE_PATH;
            } else if (val == 3) { tile = TILE_HUB;
            } else if (val == 4) { tile = TILE_WATER;
            } else if (val >= 6) {
                tile = TILE_TOWN0_BASE + (val - 6);
                // Left door tile of a building sprite → register an interior door.
                // val 1288: stone house (2-wide door), val 1294: white house.
                int interior_id = (val == 1288) ? 0 : (val == 1294) ? 1 : -1;
                if (interior_id >= 0 && map->num_doors < MAX_INTERIOR_DOORS)
                    map->doors[map->num_doors++] = { wx, wy, 2, interior_id };
            }
            if (tile < 0) continue;
            map->tiles[wy][wx]   = tile;
            map->overlay[wy][wx] = 0;
        }
    }
    // Stamp collision layer
    const char** coll_layout = all_towns_coll[town_idx];
    for (int dy = 0; dy < TOWN_H && coll_layout[dy]; dy++) {
        const char* row = coll_layout[dy];
        int row_len = (int)strlen(row);
        for (int dx = 0; dx < TOWN_W; dx++) {
            char c = (dx < row_len) ? row[dx] : '.';
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            if (c == '#') map->coll[wy][wx] = 1;
        }
    }
    // Stamp depth layer
    const char** depth_rows = (town_idx == 0) ? town_0_depth
                            : (town_idx == 1) ? town_1_depth
                            :                   town_2_depth;
    for (int dy = 0; dy < TOWN_H && depth_rows[dy]; dy++) {
        const char* row = depth_rows[dy];
        int row_len = (int)strlen(row);
        for (int dx = 0; dx < TOWN_W; dx++) {
            char c = (dx < row_len) ? row[dx] : '.';
            int wx = tx + dx, wy = ty + dy;
            if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
            if (c == '#') map->depth_layer[wy][wx] = 1;
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

// The wasteland citadel stands inside a ring of lava with no way across it, so
// reaching it waits on an item that lets you cross. That only holds if the ring
// is unbroken, which is what these three numbers and the way it is drawn are
// for: a gap of one tile anywhere would undo the whole thing.
static const int MOAT_RADIUS = 20;   // from the middle of the castle to the middle of the ring
static const int MOAT_WOBBLE = 4;    // how far in and out the ring wanders
static const int MOAT_HALF   = 2;    // half the channel's width, so five tiles across
// Everything the ring can reach, with a tile to spare. Used well away from here
// to keep trails from bridging it.
static const int MOAT_REACH  = MOAT_RADIUS + MOAT_WOBBLE + MOAT_HALF + 2;

// Drawn as a ring of overlapping blobs rather than as a band between two radii.
// A band has to decide, tile by tile, whether each one is inside it, and a
// wobble that changes faster than the shell it is cutting leaves a hole. Blobs
// cannot: consecutive centres here are a sixth of a tile apart and each blob is
// two across, so the painted run is unbroken by construction, and it closes on
// itself because the radius is built from harmonics of the angle — periodic, so
// the last step meets the first exactly.
static void stamp_castle_moat(Tilemap* map, int tx, int ty, unsigned int seed) {
    float ccx = tx + CASTLE_W * 0.5f, ccy = ty + CASTLE_H * 0.5f;
    // Amplitudes summing to MOAT_WOBBLE, so the ring's radius stays inside the
    // range the reach above is worked out from however the phases land.
    static const float SHARE[3] = { 0.5f, 0.3f, 0.2f };
    float ph[3];
    unsigned int s = seed ^ 0x1A7A0A7Au;
    for (int k = 0; k < 3; k++) {
        s = s * 1664525u + 1013904223u;
        ph[k] = (float)((s >> 16) & 0xFFFFu) / 65536.0f * 6.28318f;
    }
    const int STEPS = 1024;
    for (int i = 0; i < STEPS; i++) {
        float th = 6.28318f * (float)i / (float)STEPS;
        float r = (float)MOAT_RADIUS;
        for (int k = 0; k < 3; k++)
            r += MOAT_WOBBLE * SHARE[k] * sinf((float)(k + 1) * th + ph[k]);
        int px = (int)(ccx + cosf(th) * r);
        int py = (int)(ccy + sinf(th) * r);
        for (int dy = -MOAT_HALF; dy <= MOAT_HALF; dy++)
            for (int dx = -MOAT_HALF; dx <= MOAT_HALF; dx++) {
                if (dx*dx + dy*dy > MOAT_HALF*MOAT_HALF + 1) continue;
                int nx = px + dx, ny = py + dy;
                if (!in_bounds(nx, ny)) continue;
                // Over whatever is there — the ring has to be closed, and a
                // stretch of it declining to paint because the wasteland ran
                // out is exactly the gap this is guarding against. Not over the
                // castle: the geometry keeps well clear of the walls, and this
                // is here so that stays true if the numbers are ever changed.
                if (map->tiles[ny][nx] == TILE_CASTLE_PLACEHOLDER) continue;
                map->tiles[ny][nx]   = TILE_LAVA;
                map->overlay[ny][nx] = 0;
            }
    }
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
    map->num_doors = 0;

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

    // Fixed cave dungeon — world pixel (47936, 50329), tile (1498, 1572).
    // Stamped in phase 1 so it's visible immediately on load.
    {
        const int fcx = 1498, fcy = 1572;
        map->tiles[fcy][fcx]   = TILE_DUNGEON_CAVE;
        map->overlay[fcy][fcx] = 0;
        float fdx = (float)(fcx - MAP_WIDTH  / 2);
        float fdy = (float)(fcy - MAP_HEIGHT / 2);
        float dist     = sqrtf(fdx*fdx + fdy*fdy);
        float max_dist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                               (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
        float difficulty = ((dist / max_dist) + 3.0f / 5.0f) * 0.5f;
        map->dungeon_entrances[0] = { fcx, fcy, 0, DUNGEON_ENT_CAVE, 3, difficulty, 0, -1 };
        map->num_dungeon_entrances = 1;
    }

    // Fixed graveyard dungeon — world pixel (46816, 47082), tile (1463, 1471).
    // Stamped in phase 1 so it's visible immediately on load.
    {
        const int gx = 1463, gy = 1471;
        map->tiles[gy][gx]   = TILE_DUNGEON_GRAVEYARD_SM;
        map->overlay[gy][gx] = 0;
        float gdx = (float)(gx - MAP_WIDTH  / 2);
        float gdy = (float)(gy - MAP_HEIGHT / 2);
        float dist     = sqrtf(gdx*gdx + gdy*gdy);
        float max_dist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                               (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
        float difficulty = ((dist / max_dist) + 0.0f / 5.0f) * 0.5f;
        map->dungeon_entrances[1] = { gx, gy, 0, DUNGEON_ENT_GRAVEYARD_SM, 0, difficulty, 0, -1 };
        map->num_dungeon_entrances = 2;
    }

    // Phase 1's region is on screen before phase 2 finishes, so it clears its
    // own banks rather than waiting for the sweep at the end of generation.
    clear_overlays_near_liquid(map);
}

// ---------------------------------------------------------------------------
// Dungeon entrance helpers — used by the placement pass in phase2.
// ---------------------------------------------------------------------------

// Returns 0 for non-cliff tiles; 1–5 for cliff top tiles (all biome variants).
static int cliff_level_of(int tile_id) {
    switch (tile_id) {
        case TILE_CLIFF:       case TILE_CLIFF_SNOW_1: case TILE_CLIFF_WASTE_1: return 1;
        case TILE_CLIFF_2:     case TILE_CLIFF_SNOW_2: case TILE_CLIFF_WASTE_2: return 2;
        case TILE_CLIFF_3:     case TILE_CLIFF_SNOW_3: case TILE_CLIFF_WASTE_3: return 3;
        case TILE_CLIFF_4:     case TILE_CLIFF_SNOW_4: case TILE_CLIFF_WASTE_4: return 4;
        case TILE_CLIFF_5:     case TILE_CLIFF_SNOW_5: case TILE_CLIFF_WASTE_5: return 5;
        default: return 0;
    }
}

// Returns the biome TileId at (tx, ty).
// TILE_SNOW=snow, TILE_WASTELAND=wasteland, TILE_SAND=desert,
// TILE_TREE=forest (grass base but tree-heavy), TILE_GRASS=flat (default).
// For brown cliff tops the surrounding 8-tile radius is sampled to infer biome.
static int biome_of(const Tilemap* map, int tx, int ty) {
    int base = map->tiles[ty][tx];

    // Biome-specific cliff variants resolve immediately
    if (base >= TILE_CLIFF_SNOW_1  && base <= TILE_CLIFF_SNOW_5)  return TILE_SNOW;
    if (base >= TILE_CLIFF_WASTE_1 && base <= TILE_CLIFF_WASTE_5) return TILE_WASTELAND;

    // Flat biome tiles resolve immediately
    if (base == TILE_SNOW)                           return TILE_SNOW;
    if (base == TILE_WASTELAND || base == TILE_LAVA) return TILE_WASTELAND;
    if (base == TILE_SAND)                           return TILE_SAND;

    // For grass/meadow/brown-cliff: scan neighbors to distinguish forest vs flat
    // and (for brown cliffs) find the dominant surrounding biome.
    int snow_cnt = 0, waste_cnt = 0, sand_cnt = 0, flat_cnt = 0, tree_ovl_cnt = 0;
    const int R = 8;
    for (int dy = -R; dy <= R; dy++) {
        for (int dx = -R; dx <= R; dx++) {
            if (dx == 0 && dy == 0) continue;
            int nx = tx + dx, ny = ty + dy;
            if (nx < 0 || ny < 0 || nx >= MAP_WIDTH || ny >= MAP_HEIGHT) continue;
            int t = map->tiles[ny][nx];
            if (t == TILE_SNOW || (t >= TILE_CLIFF_SNOW_1  && t <= TILE_CLIFF_SNOW_5))  snow_cnt++;
            else if (t == TILE_WASTELAND || t == TILE_LAVA ||
                     (t >= TILE_CLIFF_WASTE_1 && t <= TILE_CLIFF_WASTE_5))               waste_cnt++;
            else if (t == TILE_SAND)                                                      sand_cnt++;
            else if (t == TILE_GRASS || t == TILE_MEADOW || t == TILE_PATH) {
                flat_cnt++;
                if (map->overlay[ny][nx] == TILE_TREE) tree_ovl_cnt++;
            }
        }
    }

    // For brown cliff tops, let the dominant surrounding biome win
    bool is_brown_cliff = (base == TILE_CLIFF  || base == TILE_CLIFF_2 ||
                           base == TILE_CLIFF_3 || base == TILE_CLIFF_4 ||
                           base == TILE_CLIFF_5);
    if (is_brown_cliff) {
        if (snow_cnt  > waste_cnt && snow_cnt  > sand_cnt && snow_cnt  > flat_cnt) return TILE_SNOW;
        if (waste_cnt > sand_cnt  && waste_cnt > flat_cnt)                          return TILE_WASTELAND;
        if (sand_cnt  > flat_cnt)                                                   return TILE_SAND;
        // fall through to forest vs flat check
    }

    // Forest if ≥40% of flat neighbors carry a tree overlay
    if (flat_cnt > 0 && tree_ovl_cnt * 10 >= flat_cnt * 4) return TILE_TREE;

    return TILE_GRASS; // default flat
}

// Picks an entrance type for the given biome + mountain flag.
// Also sets out_size (0=small, 1=large) — fixed for most types, random for Cave/Ruins.
// rng_seed is passed by value; advances internally without disturbing the caller's RNG.
static DungeonEntranceType pick_entrance_type(int biome, bool is_mountain,
                                               unsigned int rng_seed, int& out_size) {
    DungeonEntranceType pool[8];
    int pool_sz = 0;
    auto add = [&](DungeonEntranceType t) { pool[pool_sz++] = t; };

    switch (biome) {
        case TILE_SNOW:
            add(DUNGEON_ENT_RUINS);
            add(DUNGEON_ENT_GRAVEYARD_LG);
            break;
        case TILE_WASTELAND:
            add(DUNGEON_ENT_RUINS);
            add(DUNGEON_ENT_CAVE);
            break;
        case TILE_SAND:
            if (!is_mountain) add(DUNGEON_ENT_OASIS);   // oasis removed on mountain
            add(DUNGEON_ENT_PYRAMID);
            break;
        case TILE_TREE: { // forest: 50% large tree, 25% small graveyard, 25% large graveyard
            int roll = (int)((rng_seed >> 16) & 3); // 0-3
            if (!is_mountain && (roll == 0 || roll == 1)) {
                out_size = 0; return DUNGEON_ENT_LARGE_TREE;
            } else if (roll == 2) {
                out_size = 0; return DUNGEON_ENT_GRAVEYARD_SM;
            } else {
                out_size = 1; return DUNGEON_ENT_GRAVEYARD_LG;
            }
        }
        default: // flat (grass/meadow)
            add(DUNGEON_ENT_GRAVEYARD_SM);
            add(DUNGEON_ENT_GRAVEYARD_LG);
            // Stonehenge is rare: ~1-in-8 flat dungeons add it to the pool
            rng_seed = rng_seed * 1664525u + 1013904223u;
            if ((rng_seed >> 16) % 8 == 0) add(DUNGEON_ENT_STONEHENGE);
            break;
    }

    // Mountain modifier: add Cave if not already present
    if (is_mountain) {
        bool has_cave = false;
        for (int i = 0; i < pool_sz; i++)
            if (pool[i] == DUNGEON_ENT_CAVE) { has_cave = true; break; }
        if (!has_cave) add(DUNGEON_ENT_CAVE);
    }

    if (pool_sz == 0) add(DUNGEON_ENT_CAVE); // should never happen

    rng_seed = rng_seed * 1664525u + 1013904223u;
    DungeonEntranceType type = pool[(rng_seed >> 16) % (unsigned)pool_sz];

    // Derive size — fixed for most types, random for Cave and Ruins
    switch (type) {
        case DUNGEON_ENT_GRAVEYARD_SM: out_size = 0; break;
        case DUNGEON_ENT_OASIS:        out_size = 0; break;
        case DUNGEON_ENT_GRAVEYARD_LG: out_size = 1; break;
        case DUNGEON_ENT_PYRAMID:      out_size = 1; break;
        case DUNGEON_ENT_STONEHENGE:   out_size = 1; break;
        case DUNGEON_ENT_LARGE_TREE:   out_size = 0; break;
        default: // CAVE and RUINS vary
            rng_seed = rng_seed * 1664525u + 1013904223u;
            out_size = (int)((rng_seed >> 16) & 1);
            break;
    }

    return type;
}

// Stamps decorative tiles/overlays around a placed dungeon entrance.
// Uses existing tile primitives as a "temp" visual so each type is readable on the overworld:
//   graveyard → rock tombstones,  stonehenge → rock ring,  pyramid → sand clearing,
//   oasis → pond neighbors,       large tree → tree overlays,  ruins → scattered debris.
// cave has no surround — it sits embedded in a clifftop.
static void stamp_dungeon_surround(Tilemap* map, DungeonEntranceType type, int ex, int ey, int sz) {
    // Only paint on flat biome tiles — skip water, cliffs, structures, other entrances.
    auto safe_base = [&](int tx, int ty, int tile_id) {
        if (tx < 2 || ty < 2 || tx >= MAP_WIDTH-2 || ty >= MAP_HEIGHT-2) return;
        if (tx >= ex && tx < ex+sz && ty >= ey && ty < ey+sz) return;
        int base = map->tiles[ty][tx];
        if (base != TILE_GRASS && base != TILE_MEADOW && base != TILE_PATH &&
            base != TILE_SAND  && base != TILE_SNOW   && base != TILE_WASTELAND) return;
        map->tiles[ty][tx]   = tile_id;
        map->overlay[ty][tx] = 0;
    };
    auto safe_ovl = [&](int tx, int ty, int ovl_id) {
        if (tx < 2 || ty < 2 || tx >= MAP_WIDTH-2 || ty >= MAP_HEIGHT-2) return;
        if (tx >= ex && tx < ex+sz && ty >= ey && ty < ey+sz) return;
        int base = map->tiles[ty][tx];
        if (base != TILE_GRASS && base != TILE_MEADOW && base != TILE_PATH &&
            base != TILE_SAND  && base != TILE_SNOW   && base != TILE_WASTELAND) return;
        map->overlay[ty][tx] = ovl_id;
    };

    switch (type) {
        case DUNGEON_ENT_GRAVEYARD_SM:
            // Small path clearing — gravestones are spawned as resource nodes later.
            // Stamp a 5×5 patch of path tiles so the clearing is visible before spawn.
            //for (int dy = -2; dy <= 2; dy++)
                //for (int dx = -2; dx <= 2; dx++)
                    //safe_base(ex+dx, ey+dy, TILE_PATH);
            break;

        case DUNGEON_ENT_GRAVEYARD_LG: {
            // Placeholder parallelogram fence — 1:1 diagonal (north wall shifted
            // right by H tiles vs south wall).  To be replaced with proper art later.
            //
            //   N: (L+H, T) ────[gate]──────── (R+H, T)
            //        \                             \
            //   S: (L, B) ──────────────────── (R, B)   (fully closed)
            //
            // Centre the north fence on the mausoleum (ex, ex+1) so the entrance
            // sits in the middle of the top row rather than the far-left corner.
            // South fence is 18 tiles wide; H=14 gives the 1:1 diagonal shear.
            //   north fence  lx_at(T) = ex-8 .. ex+9  (mausoleum centred)
            //   south fence  lx_at(B) = ex-22 .. ex-5
            const int L = ex - 22, R = ex - 5;  // south fence extents
            const int T = ey - 1,  B = ey + 13; // north/south row (H = 14)

            auto lx_at = [&](int ty) { return L + (B - ty); };
            auto rx_at = [&](int ty) { return R + (B - ty); };

            // Interior PATH fill
            for (int ty = T + 1; ty < B; ty++)
                for (int tx = lx_at(ty) + 1; tx < rx_at(ty); tx++)
                    safe_base(tx, ty, TILE_PATH);

            // North fence — 2-tile gate centred on the mausoleum entrance
                int nl = lx_at(T), nr = rx_at(T);
                //int gate_l = (nl + nr) / 2;
                for (int tx = nl; tx <= nr; tx++) 
                {
                    safe_ovl(tx, T, TILE_ROCK);
                }

            // South fence — 2-tile gate centred on the south fence
            {
                int sl = lx_at(B), sr = rx_at(B);
                int gate_l = (sl + sr) / 2;
                for (int tx = sl; tx <= sr; tx++) {
                    bool is_gate = (tx == gate_l || tx == gate_l + 1);
                    if (!is_gate) safe_ovl(tx, B, TILE_ROCK);
                }
            }

            // Left and right diagonal fence walls
            for (int ty = T; ty <= B; ty++) {
                safe_ovl(lx_at(ty), ty, TILE_ROCK);
                safe_ovl(rx_at(ty), ty, TILE_ROCK);
            }
            break;
        }

        case DUNGEON_ENT_STONEHENGE: {
            // 8 standing stones in a ring at radius 3 around the 2×2 center
            int ccx = ex + sz/2, ccy = ey + sz/2;
            const int ox[8] = { 0, 2, 3, 2, 0,-2,-3,-2};
            const int oy[8] = {-3,-2, 0, 2, 3, 2, 0,-2};
            for (int i = 0; i < 8; i++)
                safe_ovl(ccx + ox[i], ccy + oy[i], TILE_ROCK);
            break;
        }

        case DUNGEON_ENT_PYRAMID:
            // Desert clearing — 3-tile border of sand around the 2×2 entrance
            for (int dy = -3; dy < sz+3; dy++)
                for (int dx = -3; dx < sz+3; dx++)
                    safe_base(ex+dx, ey+dy, TILE_ROCK);
            break;

        case DUNGEON_ENT_OASIS:
            // Pond tiles at four cardinal neighbors of the 1×1 entrance
            safe_base(ex,   ey-1, TILE_POND);
            safe_base(ex,   ey+1, TILE_POND);
            safe_base(ex-1, ey,   TILE_POND);
            safe_base(ex+1, ey,   TILE_POND);
            break;

        case DUNGEON_ENT_LARGE_TREE:
            // Same as other dungeons — no special surround, just the entrance tile
            break;

        case DUNGEON_ENT_RUINS:
            // Scattered rock debris around the entrance
            safe_ovl(ex-2,    ey,      TILE_ROCK);
            safe_ovl(ex+sz+1, ey+sz-1, TILE_ROCK);
            safe_ovl(ex,      ey-2,    TILE_ROCK);
            safe_ovl(ex+sz-1, ey+sz+1, TILE_ROCK);
            break;

        default: // CAVE — no surround, already embedded in clifftop terrain
            break;
    }
}

// Maps entrance type to the tile ID stamped on the overworld.
static int entrance_tile_id(DungeonEntranceType type) {
    switch (type) {
        case DUNGEON_ENT_CAVE:         return TILE_DUNGEON_CAVE;
        case DUNGEON_ENT_RUINS:        return TILE_DUNGEON_RUINS;
        case DUNGEON_ENT_GRAVEYARD_SM: return TILE_DUNGEON_GRAVEYARD_SM;
        case DUNGEON_ENT_GRAVEYARD_LG: return TILE_DUNGEON_GRAVEYARD_LG;
        case DUNGEON_ENT_OASIS:        return TILE_DUNGEON_OASIS;
        case DUNGEON_ENT_PYRAMID:      return TILE_DUNGEON_PYRAMID;
        case DUNGEON_ENT_STONEHENGE:   return TILE_DUNGEON_STONEHENGE;
        case DUNGEON_ENT_LARGE_TREE:   return TILE_DUNGEON_LARGE_TREE;
        default:                       return TILE_DUNGEON;
    }
}

void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed) {
    // Run at idle priority so this thread doesn't compete with the game loop
#ifdef _WIN32
    // Windows has no SCHED_IDLE; lowest priority is the closest equivalent
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_LOWEST);
#else
    struct sched_param sp = {0};
    pthread_setschedparam(pthread_self(), SCHED_IDLE, &sp);
#endif

    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // Pick which edge the ocean occupies (0=W, 1=E, 2=N, 3=S)
    unsigned int side_seed = seed ^ 0x5EA5EDEEu;
    side_seed = side_seed * 1664525u + 1013904223u;
    int ocean_side = (int)((side_seed >> 16) % 4);

    GEN_STAGE(map, "before Ocean");
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

    GEN_STAGE(map, "before Rivers");
    // --- Rivers ---
    if (s_gen_cancel) return;
    const float PI = 3.14159265f;
    int guard_r = TOWN_W / 2, brush_r = 6;
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
        int sx = cx + (int)(dx * (TOWN_W / 2)), sy = cy + (int)(dy * (TOWN_W / 2));
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

    GEN_STAGE(map, "before Cliff gradient direction");
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

    GEN_STAGE(map, "before Cliff blocked prepass");
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

    GEN_STAGE(map, "before Biome pass");
    // --- Biome pass: plains / desert / snow / wasteland ---
    if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Biome smoothing");
    // --- Biome smoothing: eliminate tiny isolated patches ---
    if (s_gen_cancel) return;
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
            if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Biome adjacency fixup");
    // --- Biome adjacency fixup ---
    // Rule 1: TILE_SAND cannot be adjacent to TILE_SNOW.
    // Rule 2: TILE_SNOW can only be adjacent to TILE_GRASS or TILE_MEADOW (among biome tiles).
    // Any SAND within SNOW_BUFFER tiles of snow is converted to TILE_MEADOW,
    // creating a wide meadow/forest transition zone between the two biomes.
    {
        const int SNOW_BUFFER = 50;
        for (int y = SNOW_BUFFER; y < MAP_HEIGHT - SNOW_BUFFER; y++) {
            if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Post-fixup biome smoothing");
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
            if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Minimum biome patch enforcement");
    // --- Minimum biome patch enforcement ---
    if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Cliffs");
    // --- Cliffs ---
    if (s_gen_cancel) return;
    // Biomes are fully settled above; place_cliffs reads the biome under each tile
    // and selects the matching cliff variant (snow/wasteland/plain) directly.
    place_cliffs(map, seed, cx, cy, hw, hw*hw, MAP_WIDTH * MAP_WIDTH);

    GEN_STAGE(map, "before Cliff edge pass");
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

    GEN_STAGE(map, "before Cliff side/corner pass");
    // --- Cliff side/corner pass ---
    // East/west faces and outer (convex) corners.
    // Run bottom-to-top so higher-elevation cliffs overwrite lower-elevation placements
    // at shared positions, mirroring the south-face pass ordering.
    {
        // West and east faces are mirrors of each other in the art, and the
        // north rim is a different thing again, so each gets its own tile.
        static const int side_tile[] = {
            0,
            TILE_CLIFF_SIDE_1, TILE_CLIFF_SIDE_2, TILE_CLIFF_SIDE_3,
            TILE_CLIFF_SIDE_4, TILE_CLIFF_SIDE_5,
        };
        static const int side_tile_e[] = {
            0,
            TILE_CLIFF_SIDE_E_1, TILE_CLIFF_SIDE_E_2, TILE_CLIFF_SIDE_E_3,
            TILE_CLIFF_SIDE_E_4, TILE_CLIFF_SIDE_E_5,
        };
        static const int back_tile[] = {
            0,
            TILE_CLIFF_BACK_1, TILE_CLIFF_BACK_2, TILE_CLIFF_BACK_3,
            TILE_CLIFF_BACK_4, TILE_CLIFF_BACK_5,
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
                        map->tiles[ey][x+1] = side_tile_e[E];
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
                map->tiles[y-1][x] = back_tile[E];
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

    GEN_STAGE(map, "before Trees");
    // --- Trees ---
    if (s_gen_cancel) return;
    // TILE_GRASS = spotty dense forest (coarse cluster noise → dense patches + clearings)
    // TILE_MEADOW = open plains (~5% trees)
    {
        const int FG = 20; // forest cluster grid size
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                if (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SNOW) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                int n = tile_noise(x, y, (int)seed ^ 7);
                if (t == TILE_MEADOW) {
                    if (n > 32400) map->overlay[y][x] = TILE_TREE;
                } else if (t == TILE_SNOW) {
                    // Thin brush: only inside forest clusters, sparser than temperate forest
                    int gx = x/FG, gy = y/FG;
                    float fx = (float)(x%FG)/FG, fy = (float)(y%FG)/FG;
                    float top = tile_noise(gx,gy,(int)seed^0xF05) + fx*(tile_noise(gx+1,gy,(int)seed^0xF05)-tile_noise(gx,gy,(int)seed^0xF05));
                    float bot = tile_noise(gx,gy+1,(int)seed^0xF05) + fx*(tile_noise(gx+1,gy+1,(int)seed^0xF05)-tile_noise(gx,gy+1,(int)seed^0xF05));
                    int cluster = (int)(top + fy*(bot-top));
                    if (cluster > 20000 && n > 16000)
                        map->overlay[y][x] = TILE_TREE;
                } else {
                    int gx = x/FG, gy = y/FG;
                    float fx = (float)(x%FG)/FG, fy = (float)(y%FG)/FG;
                    float top = tile_noise(gx,gy,(int)seed^0xF04) + fx*(tile_noise(gx+1,gy,(int)seed^0xF04)-tile_noise(gx,gy,(int)seed^0xF04));
                    float bot = tile_noise(gx,gy+1,(int)seed^0xF04) + fx*(tile_noise(gx+1,gy+1,(int)seed^0xF04)-tile_noise(gx,gy+1,(int)seed^0xF04));
                    int cluster = (int)(top + fy*(bot-top));
                    if (n > ((cluster > 16000) ? 5000 : 32400))
                        map->overlay[y][x] = TILE_TREE;
                }
            }
        }
    }

    GEN_STAGE(map, "before Rocks");
    // --- Rocks (after cliffs for same reason) ---
    {
        unsigned int s = seed ^ 0xDEAD1;
        for (int i = 0; i < 40000; i++) {
            s = s * 1664525u + 1013904223u;
            int x = 1 + (int)((s >> 16) % (MAP_WIDTH  - 2));
            s = s * 1664525u + 1013904223u;
            int y = 1 + (int)((s >> 16) % (MAP_HEIGHT - 2));
            int ddx = x - cx, ddy = y - cy;
            if (ddx*ddx + ddy*ddy <= hw*hw) continue;
            if (map->tiles[y][x] == TILE_GRASS && map->overlay[y][x] == 0) map->overlay[y][x] = TILE_ROCK;
        }
    }

    GEN_STAGE(map, "before Rocks at elevation");
    // --- Rocks at elevation (density scales with cliff level) ---
    {
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                int threshold;
                if      (t == TILE_CLIFF   || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1) threshold = 29491; // ~10%
                else if (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2) threshold = 27163; // ~17%
                else if (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) threshold = 24575; // ~25%
                else if (t == TILE_CLIFF_4 || t == TILE_CLIFF_SNOW_4 || t == TILE_CLIFF_WASTE_4) threshold = 21954; // ~33%
                else if (t == TILE_CLIFF_5 || t == TILE_CLIFF_SNOW_5 || t == TILE_CLIFF_WASTE_5) threshold = 19660; // ~40%
                else continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                if (tile_noise(x, y, (int)seed ^ 0xC1FFE) > threshold)
                    map->overlay[y][x] = TILE_ROCK;
            }
        }
    }

    GEN_STAGE(map, "before Gold ore at high elevation");
    // --- Gold ore at high elevation (cliff 3+) for all biomes ---
    {
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                int t = map->tiles[y][x];
                int threshold;
                if      (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) threshold = 32127; // ~2%
                else if (t == TILE_CLIFF_4 || t == TILE_CLIFF_SNOW_4 || t == TILE_CLIFF_WASTE_4) threshold = 31784; // ~3%
                else if (t == TILE_CLIFF_5 || t == TILE_CLIFF_SNOW_5 || t == TILE_CLIFF_WASTE_5) threshold = 31129; // ~5%
                else continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                if (tile_noise(x, y, (int)seed ^ 0x4E1DA9) > threshold)
                    map->overlay[y][x] = TILE_GOLD_ORE;
            }
        }
    }

    GEN_STAGE(map, "before Lava streams and pools inside wasteland");
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
            // Long enough for several bends to play out. At this turn rate the
            // heading holds a curve for roughly a dozen steps, so a short
            // channel would end mid-bend and read as a bent line.
            int len = 140 + (int)((ls >> 16) % 260);
            march_wander(map, lx, ly, angle, ls,
                         cx, cy, guard_r, 1, len, 0.035f, TILE_WASTELAND, TILE_LAVA);
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

    GEN_STAGE(map, "before Dead trees scattered in wasteland");
    // --- Dead trees scattered in wasteland (~2%) ---
    {
        for (int y = 1; y < MAP_HEIGHT - 1; y++) {
            for (int x = 1; x < MAP_WIDTH - 1; x++) {
                if (map->tiles[y][x] != TILE_WASTELAND) continue;
                if (cliff_blocked[y][x]) continue;
                if (map->overlay[y][x] != 0) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                if (tile_noise(x, y, (int)seed ^ 0xDEAD7) > 32200)
                    map->overlay[y][x] = TILE_DEAD_TREE;
            }
        }
    }

    GEN_STAGE(map, "before Pond streams and pools inside meadows");
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

    GEN_STAGE(map, "before Biome guarantee pass");
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
        return (bt >= TILE_CLIFF_EDGE_1   && bt <= TILE_CLIFF_EDGE_5)     // 12-16: south drop
            || (bt >= TILE_CLIFF_SIDE_1   && bt <= TILE_CLIFF_CORNER_NE_5) // 34-58: west sides/corners
            || (bt >= TILE_CLIFF_SIDE_E_1 && bt <= TILE_CLIFF_BACK_5);     // 74-83: east sides, back faces
    };

    GEN_STAGE(map, "before Towns 1-3");
    // --- Towns 1-3 ---
    if (s_gen_cancel) return;
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

    GEN_STAGE(map, "before Villages");
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

    GEN_STAGE(map, "before Castles");
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
                bool all_flat_elev5 = true;
                for (int cdy = 0; cdy < CASTLE_H && all_flat_elev5; cdy++)
                    for (int cdx = 0; cdx < CASTLE_W && all_flat_elev5; cdx++) {
                        int bt = map->tiles[ty+cdy][tx+cdx];
                        if (bt != TILE_CLIFF_5 && bt != TILE_CLIFF_SNOW_5 && bt != TILE_CLIFF_WASTE_5)
                            all_flat_elev5 = false;
                    }
                if (!all_flat_elev5) continue;
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
            // Everything the ring will lie on, and a two-tile skirt outside it,
            // has to be this biome's own ground — which is what MOAT_REACH is:
            // the ring's outer edge plus two. A site that fails this is one
            // where the lava runs off the wasteland and into the grass, or up
            // the side of a mountain, which is what the wasteland's cliffs are.
            //
            // Towns and villages are already stamped by now and castles 0 and 1
            // are placed above, so their tiles are on the map for this to see.
            // What comes after — dungeon entrances, then the trails — keeps
            // clear of the moat's reach on its own account.
            auto moat_site_clear = [&](int mx, int my) {
                for (int dy = -MOAT_REACH; dy <= MOAT_REACH; dy++)
                    for (int dx = -MOAT_REACH; dx <= MOAT_REACH; dx++) {
                        if (dx*dx + dy*dy > MOAT_REACH * MOAT_REACH) continue;
                        int nx = mx + dx, ny = my + dy;
                        if (!in_bounds(nx, ny)) return false;
                        int t = map->tiles[ny][nx];
                        if (t != TILE_WASTELAND && t != TILE_LAVA) return false;
                    }
                return true;
            };

            bool placed = false;
            if (!lava_tiles.empty()) {
                // A third pass, and only if the first two find nowhere at all:
                // it drops the requirement above rather than leave the world
                // without its citadel. Nothing in the seeds tried has needed
                // it — a wasteland with lava in it has room for a ring
                // somewhere — but "no castle" is the worse failure of the two.
                for (int pass = 0; pass < 3 && !placed; pass++) {
                    unsigned int ls = seed ^ 0xA55A001Bu;
                    ls = ls * 1664525u + 1013904223u;
                    int start = (int)((ls >> 16) % (unsigned)lava_tiles.size());
                    for (int i = 0; i < (int)lava_tiles.size() && !placed; i++) {
                        int idx = (start + i) % (int)lava_tiles.size();
                        int tx = lava_tiles[idx].first  - CASTLE_W / 2;
                        int ty = lava_tiles[idx].second - CASTLE_H / 2;
                        if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                        // Room for the whole moat, not just the castle. Placed
                        // against the edge of the world, the ring runs off it
                        // and the citadel ends up walled by the map boundary on
                        // that side instead of by lava — sealed, but only by
                        // accident, and it reads as a moat someone forgot to
                        // finish.
                        if (tx + CASTLE_W / 2 - MOAT_REACH < 0 ||
                            ty + CASTLE_H / 2 - MOAT_REACH < 0 ||
                            tx + CASTLE_W / 2 + MOAT_REACH >= MAP_WIDTH ||
                            ty + CASTLE_H / 2 + MOAT_REACH >= MAP_HEIGHT) continue;
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
                        if (pass >= 1 && waste_count * 4 < CASTLE_W * CASTLE_H * 3) continue;
                        // Last because it is the dearest: a couple of thousand
                        // tiles per candidate, where the tests above turn most
                        // of them away after a handful.
                        if (pass < 2 && !moat_site_clear(tx + CASTLE_W / 2,
                                                         ty + CASTLE_H / 2)) continue;
                        stamp_castle_blueprint(map, 2, tx, ty);
                        stamp_castle_moat(map, tx, ty, seed);
                        placed = true;
                    }
                }
            }
        }
    }

    GEN_STAGE(map, "before Dungeon entrances");
    // --- Dungeon entrances ---
    if (s_gen_cancel) return;
    // Each entrance derives its type (and therefore interior architecture) from the
    // biome at its placement position.  Mountain elevation (cliff ≥ 3) acts as a
    // modifier: adds Cave to the pool, removes Oasis and Large Tree.
    // Difficulty is the straight average of distance-from-center (0–1) and
    // elevation (0–1), computed once at world gen and stored on the entrance.
    // Grid-cell shuffle + MIN_DIST keeps all entrances well separated.
    {
        const int TARGET   = 300;
        const int MIN_DIST = 130; // minimum tile distance between any two top-left corners
        const int CELL     = 150; // one entrance attempted per CELL×CELL region
        const int MARGIN   = 6;   // clearance from map edges

        const int GW = (MAP_WIDTH  + CELL - 1) / CELL;
        const int GH = (MAP_HEIGHT + CELL - 1) / CELL;

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
                        // Allow flat biome tiles and cliff tops at level ≥ 3 (mountain)
                        bool cliff_top = (cliff_level_of(base) >= 3);
                        if (!cliff_top &&
                            base != TILE_GRASS     && base != TILE_MEADOW &&
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
            // And anywhere the wasteland citadel's moat reaches. An entrance
            // stamp writes over whatever is under it, so one landing on the
            // ring would cut a walkable gap through the one thing that is
            // supposed to have none — and one landing inside the ring would be
            // a dungeon nobody can reach until they can cross lava.
            if (map->castles[2].x >= 0) {
                int mx = map->castles[2].x + CASTLE_W / 2;
                int my = map->castles[2].y + CASTLE_H / 2;
                int nx = (ex + sz / 2) - mx, ny = (ey + sz / 2) - my;
                int keep = MOAT_REACH + sz;
                if (nx*nx + ny*ny <= keep * keep) return false;
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
                // Determine biome and cliff level at this position
                int base_tile = map->tiles[ey][ex];
                int cliff_lvl = cliff_level_of(base_tile);
                bool is_mtn   = (cliff_lvl >= 3);
                int biome     = biome_of(map, ex, ey);

                // Pick entrance type — also determines size for fixed-size archetypes
                int ent_size;
                es = es * 1664525u + 1013904223u;
                DungeonEntranceType ent_type = pick_entrance_type(biome, is_mtn, es, ent_size);
                int sz = ent_size + 1; // 1 = small, 2 = large

                if (!door_ok(ex, ey, sz)) continue;

                // Difficulty: straight average of distance-from-center and elevation
                float fdx      = (float)(ex - MAP_WIDTH  / 2);
                float fdy      = (float)(ey - MAP_HEIGHT / 2);
                float dist     = sqrtf(fdx*fdx + fdy*fdy);
                float max_dist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                                       (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
                float difficulty = ((dist / max_dist) + (float)cliff_lvl / 5.0f) * 0.5f;

                // GRAVEYARD_SM: entrance tile stays hidden under the biome tile.
                // It is revealed when the player destroys the hidden gravestone resource node.
                // All other types stamp their dungeon tile immediately.
                if (ent_type != DUNGEON_ENT_GRAVEYARD_SM) {
                    int tile_id = entrance_tile_id(ent_type);
                    for (int r = 0; r < sz; r++)
                        for (int c = 0; c < sz; c++) {
                            map->tiles[ey + r][ex + c]   = tile_id;
                            map->overlay[ey + r][ex + c] = 0;
                        }
                }
                stamp_dungeon_surround(map, ent_type, ex, ey, sz);
                map->dungeon_entrances[map->num_dungeon_entrances++] = {
                    ex, ey, ent_size, ent_type, cliff_lvl, difficulty, 0, -1
                };
                break;
            }
        }
    }

    // ── Link ~25% of dungeons to their closest compatible neighbour ───────
    {
        int n = map->num_dungeon_entrances;
        // partner_idx already initialised to -1 above.

        // Shuffled processing order — deterministic from seed.
        uint32_t lrng = seed ^ 0xC0FFEE42u;
        auto lnext = [&]() -> uint32_t {
            lrng = lrng * 1664525u + 1013904223u;
            return (lrng >> 16) & 0x7FFF;
        };

        std::vector<int> order(n);
        for (int i = 0; i < n; i++) order[i] = i;
        for (int i = n - 1; i > 0; i--) {
            int j = (int)(lnext() % (unsigned)(i + 1));
            std::swap(order[i], order[j]);
        }

        // Dungeons within this tile radius of the map center stay solo
        // so the starting area doesn't have confusing cross-dungeon connections.
        const int START_ZONE_R = 300;

        auto near_start = [&](const DungeonEntrance* e) {
            int ddx = e->x - cx, ddy = e->y - cy;
            return ddx*ddx + ddy*ddy < START_ZONE_R * START_ZONE_R;
        };

        for (int oi = 0; oi < n; oi++) {
            int i = order[oi];
            DungeonEntrance* ei = &map->dungeon_entrances[i];
            if (ei->partner_idx != -1) continue;  // already paired
            if (near_start(ei)) continue;          // solo in starting area

            // Find closest unlinked compatible neighbour.
            int best_j = -1, best_d2 = INT_MAX;
            for (int j = 0; j < n; j++) {
                if (j == i) continue;
                DungeonEntrance* ej = &map->dungeon_entrances[j];
                if (ej->partner_idx != -1) continue;
                if (near_start(ej)) continue;      // don't pair into starting area
                // Compatible: same type, or SM↔LG graveyard.
                bool compat = (ei->type == ej->type);
                if (!compat) {
                    bool ai = (ei->type == DUNGEON_ENT_GRAVEYARD_SM ||
                               ei->type == DUNGEON_ENT_GRAVEYARD_LG);
                    bool aj = (ej->type == DUNGEON_ENT_GRAVEYARD_SM ||
                               ej->type == DUNGEON_ENT_GRAVEYARD_LG);
                    compat = ai && aj;
                }
                if (!compat) continue;
                int dx = ei->x - ej->x, dy = ei->y - ej->y;
                int d2 = dx*dx + dy*dy;
                if (d2 < best_d2) { best_d2 = d2; best_j = j; }
            }

            if (best_j < 0) continue;

            // Accept with 25% probability so ~25% of all dungeons end up linked.
            if (lnext() % 4 != 0) continue;

            ei->partner_idx = best_j;
            map->dungeon_entrances[best_j].partner_idx = i;
        }
    }

    GEN_STAGE(map, "before Wasteland trails");
    // --- Wasteland trails between dungeons ---
    // Paths worn between the dungeon mouths of a wasteland, so the biome reads
    // as somewhere people go rather than somewhere with routes drawn on it. A
    // wasteland with fewer than two dungeons gets nothing: there is nothing to
    // connect.
    //
    // Runs at the very end because dungeon entrances are the last thing placed.
    // Everything the trail has to route around — cliffs, towns — and everything
    // it clears out of its way or bridges over is already on the map by now.
    //
    // The dungeons of a region are joined by a minimum spanning tree, so every
    // one is reachable and no pair is linked twice. A chain visiting them in
    // turn would double back across the region; a tree branches the way tracks
    // between places actually do.
    {
        // Asked for rather than required: the
        // router gives it up a tile at a time until a way through appears, so
        // this is how far from the border a trail would like to run, not how
        // far it must. Three was enough to stop trails tracing the rim but left
        // them well inside it — routed at a mean of five tiles' clearance where
        // the wasteland's own mean was nine — because a shortest path still
        // hugs the inside of a bend once it is clear of the margin.
        const int EDGE_CLEARANCE = 6;      // tiles the trail would rather keep from the border
        const int ENDPOINT_FREE  = 10;     // radius around a dungeon where that is waived
        const int ANCHOR_SEARCH  = 8;      // how far off a dungeon to find ground
        const int DX4[4] = {1,-1,0,0}, DY4[4] = {0,0,1,-1};
        std::vector<uint8_t> seen((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<uint8_t> incomp((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<uint8_t> nearedge((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<int> prev((size_t)MAP_WIDTH * MAP_HEIGHT, -1);
        // How many tiles of lava the route has crossed to reach this one, so a
        // crossing can be cut off once it is longer than a bridge should be.
        std::vector<uint8_t> runlen((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        // And how much ground it still owes before it may cross again. Two
        // crossings back to back meet at a corner and fuse into one L-shaped
        // deck, which is neither three wide nor going one way.
        std::vector<uint8_t> cool((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<int> comp, route, touched, path, rimq;
        unsigned int ts = seed ^ 0x7A11D0u;

        // A bridge is a straight run and nothing else: one direction, three
        // tiles wide, and short. So lava is not ground the route wanders over —
        // it is a gap the route may step across in one move, in a straight line
        // and only where the crossing is brief. Anything wider is gone around.
        //
        // Letting the route treat lava as ordinary ground, which is what it did
        // before, gave crossings that curved with the trail and sprawled wider
        // than the trail at every turn, because the brush was sweeping a
        // wandering line over a channel rather than laying a span across it.
        const int BRIDGE_MAX = 10;   // longest crossing, in tiles of lava
        const int BRIDGE_GAP = 4;    // ground a route must cover between crossings

        // The citadel's moat is the one lava no bridge may span. Crossing it
        // would hand over the way in that the ring exists to withhold.
        const CastlePlacement& citadel = map->castles[2];
        int moat_cx = citadel.x + CASTLE_W / 2, moat_cy = citadel.y + CASTLE_H / 2;
        auto in_moat = [&](int x, int y) {
            if (citadel.x < 0) return false;
            int dx = x - moat_cx, dy = y - moat_cy;
            return dx*dx + dy*dy <= MOAT_REACH * MOAT_REACH;
        };
        auto is_lava = [&](int x, int y) {
            int t = map->tiles[y][x];
            return t == TILE_LAVA || t == TILE_WASTE_BRIDGE;
        };
        // Lava a bridge is allowed to cross.
        auto spannable = [&](int x, int y) {
            return is_lava(x, y) && !in_moat(x, y);
        };

        // Ground a trail can be laid on. Cliffs are excluded here rather than
        // left to the brush: routing over ground that cannot be painted tears
        // a hole in the trail, and mountains are to be gone around anyway.
        auto is_region = [&](int x, int y) {
            int t = map->tiles[y][x];
            if (t != TILE_WASTELAND && t != TILE_WASTE_TRAIL) return false;
            if (cliff_blocked[y][x]) return false;
            if (abs(x - cx) <= guard_r && abs(y - cy) <= guard_r) return false;
            return true;
        };

        // Is there a crossing from ground at (x,y) straight out along d — over
        // nothing but spannable lava, landing on ground no more than
        // BRIDGE_MAX tiles away? Returns where it lands, or -1.
        //
        // Used to work out what belongs to the same wasteland, where all that
        // matters is whether a route could get across. The route itself does
        // not step this way; it walks the channel a tile at a time, so that
        // crossing costs what it is worth.
        auto span_from = [&](int x, int y, int d) {
            int nx = x + DX4[d], ny = y + DY4[d];
            if (!in_bounds(nx, ny) || !spannable(nx, ny)) return -1;
            for (int k = 1; k <= BRIDGE_MAX; k++) {
                nx += DX4[d]; ny += DY4[d];
                if (!in_bounds(nx, ny)) return -1;
                if (spannable(nx, ny)) continue;
                return is_region(nx, ny) ? ny * MAP_WIDTH + nx : -1;
            }
            return -1;
        };

        for (int y0 = 0; y0 < MAP_HEIGHT && !s_gen_cancel; y0++) {
            for (int x0 = 0; x0 < MAP_WIDTH; x0++) {
                size_t i0 = (size_t)y0 * MAP_WIDTH + x0;
                if (seen[i0] || !is_region(x0, y0)) continue;

                comp.clear();
                comp.push_back((int)i0);
                seen[i0] = 1;
                for (size_t h = 0; h < comp.size(); h++) {
                    int qx = comp[h] % MAP_WIDTH, qy = comp[h] / MAP_WIDTH;
                    // Ground across a bridgeable channel belongs to the same
                    // wasteland: it is somewhere a trail can get to, so the
                    // dungeons either side of a narrow channel are joined to
                    // each other rather than each getting a trail of its own.
                    // Across a channel too wide to bridge they are not, and the
                    // two sides are two regions — which is right, since there
                    // is no way between them.
                    for (int d = 0; d < 4; d++) {
                        int sp = span_from(qx, qy, d);
                        if (sp < 0 || seen[sp]) continue;
                        seen[sp] = 1;
                        comp.push_back(sp);
                    }
                    for (int d = 0; d < 4; d++) {
                        int nx = qx + DX4[d], ny = qy + DY4[d];
                        if (!in_bounds(nx, ny)) continue;
                        size_t ni = (size_t)ny * MAP_WIDTH + nx;
                        if (seen[ni] || !is_region(nx, ny)) continue;
                        seen[ni] = 1;
                        comp.push_back((int)ni);
                    }
                }
                for (int c : comp) incomp[c] = 1;

                // An entrance stamp overwrites the ground it sits on, so the
                // dungeon tile itself is not part of the region. Anchor to the
                // nearest walkable tile of this wasteland instead, and if there
                // is none within reach the dungeon belongs to somewhere else.
                //
                // Not to lava, near as it might be: an anchor is where a trail
                // begins, and one out in a channel would start it on a stretch
                // of bridge going nowhere.
                std::vector<int> anchors;
                for (int i = 0; i < map->num_dungeon_entrances; i++) {
                    int ex = map->dungeon_entrances[i].x;
                    int ey = map->dungeon_entrances[i].y;
                    int best = -1, bestd = INT_MAX;
                    for (int dy = -ANCHOR_SEARCH; dy <= ANCHOR_SEARCH; dy++)
                        for (int dx = -ANCHOR_SEARCH; dx <= ANCHOR_SEARCH; dx++) {
                            int nx = ex + dx, ny = ey + dy;
                            if (!in_bounds(nx, ny)) continue;
                            size_t ni = (size_t)ny * MAP_WIDTH + nx;
                            if (!incomp[ni] || is_lava(nx, ny)) continue;
                            int dd = dx*dx + dy*dy;
                            if (dd < bestd) { bestd = dd; best = (int)ni; }
                        }
                    if (best >= 0) anchors.push_back(best);
                }

                std::vector<std::pair<int,int>> edges;
                if (anchors.size() >= 2) {
                    // Minimum spanning tree over the dungeons, by Prim: grow
                    // the tree one dungeon at a time, always taking the nearest
                    // one still outside it.
                    std::vector<bool> intree(anchors.size(), false);
                    intree[0] = true;
                    for (size_t added = 1; added < anchors.size(); added++) {
                        int ba = -1, bb = -1; double bestd = 1e18;
                        for (size_t a = 0; a < anchors.size(); a++) {
                            if (!intree[a]) continue;
                            int ax = anchors[a] % MAP_WIDTH, ay = anchors[a] / MAP_WIDTH;
                            for (size_t b = 0; b < anchors.size(); b++) {
                                if (intree[b]) continue;
                                int bx = anchors[b] % MAP_WIDTH, by = anchors[b] / MAP_WIDTH;
                                double dd = (double)(ax-bx)*(ax-bx) + (double)(ay-by)*(ay-by);
                                if (dd < bestd) { bestd = dd; ba = (int)a; bb = (int)b; }
                            }
                        }
                        if (bb < 0) break;
                        intree[bb] = true;
                        edges.push_back({ anchors[ba], anchors[bb] });
                    }
                } else if (anchors.size() == 1) {
                    // A lone dungeon has nothing to join. Rather than leave the
                    // wasteland bare, run its path out toward the point furthest
                    // away — a track leading somewhere from the mouth. Pairing
                    // it with a dungeon in another wasteland is not an option:
                    // a trail cannot leave the biome to get there.
                    //
                    // The literal furthest point of an elongated wasteland
                    // almost always sits right against its outer border, which
                    // made the route to it run along that border for most of
                    // its length instead of just ending out in the waste. Only
                    // consider points with a clearance ring of the same
                    // component around them, so the target — and the path
                    // approaching it — stays away from the edge.
                    //
                    // The same ring the route wants, so the target is somewhere
                    // the route can reach without giving that up. A smaller one
                    // let the target sit up a narrow arm or spit, and a route
                    // has no way to travel a five-wide arm except along its
                    // edge, however much clearance it would rather have.
                    const int EDGE_MARGIN = EDGE_CLEARANCE;
                    int a = anchors[0];
                    int ax = a % MAP_WIDTH, ay = a / MAP_WIDTH;
                    auto is_deep = [&](int px2, int py2) {
                        for (int dy = -EDGE_MARGIN; dy <= EDGE_MARGIN; dy++)
                            for (int dx = -EDGE_MARGIN; dx <= EDGE_MARGIN; dx++) {
                                int nx = px2 + dx, ny = py2 + dy;
                                if (!in_bounds(nx, ny)) return false;
                                if (!incomp[(size_t)ny * MAP_WIDTH + nx]) return false;
                            }
                        return true;
                    };
                    int pick = -1; long bestd = -1;
                    for (int c : comp) {
                        int px2 = c % MAP_WIDTH, py2 = c / MAP_WIDTH;
                        if (is_lava(px2, py2)) continue;   // no track ends mid-bridge
                        if (!is_deep(px2, py2)) continue;
                        long dd = (long)(px2-ax)*(px2-ax) + (long)(py2-ay)*(py2-ay);
                        if (dd > bestd) { bestd = dd; pick = c; }
                    }
                    if (pick < 0) {
                        // No point has full clearance — a thin sliver of a
                        // wasteland. Fall back to the plain furthest point
                        // rather than leave the lone dungeon without a trail.
                        for (int c : comp) {
                            int px2 = c % MAP_WIDTH, py2 = c / MAP_WIDTH;
                            if (is_lava(px2, py2)) continue;
                            long dd = (long)(px2-ax)*(px2-ax) + (long)(py2-ay)*(py2-ay);
                            if (dd > bestd) { bestd = dd; pick = c; }
                        }
                    }
                    if (pick >= 0) edges.push_back({ a, pick });
                }

                if (!edges.empty()) {
                    // Tiles of *this* wasteland. The smoothing and the paint
                    // fallback below have to ask this rather than is_region:
                    // is_region accepts any wasteland, so a point drifting
                    // across a thin barrier into the neighbouring one passes
                    // it, the fallback is skipped, and paint_trail then refuses
                    // the tile for not belonging here — leaving a silent gap
                    // that breaks the trail in two.
                    auto in_this = [&](int x, int y) {
                        return in_bounds(x, y) && incomp[(size_t)y * MAP_WIDTH + x];
                    };

                    // Keep the route off the wasteland's own border, for the
                    // same reason it is kept off lava. A shortest path through
                    // a curved region hugs the inside of the bend, so the
                    // clearance around the target was not enough on its own:
                    // the route reaching a target well out in the waste still
                    // ran along the rim for most of its length.
                    //
                    // How far in each tile is, up to EDGE_CLEARANCE, by growing
                    // the rim inward that many times: 1 for a tile against the
                    // border, 0 for anything deeper than the margin. It is a
                    // depth rather than a flag because the router gives the
                    // margin up a tile at a time — banning tiles outright would
                    // cost a narrow arm of a wasteland the rule altogether,
                    // since every tile in a five-wide neck is within three of
                    // the border and there would be no way through at all.
                    //
                    // With the drift clamped to two tiles and a radius-one
                    // brush, a route three tiles in leaves the painted trail
                    // clear of the border at worst.
                    //
                    // Lava is not the border for this purpose, whatever the
                    // routing graph thinks of it. The margin exists to keep the
                    // trail off the edge of the biome, and a channel running
                    // through the middle of one is not that — treating it as
                    // border would push the route six tiles clear of every
                    // shore and leave it unable to reach a crossing at all.
                    rimq.clear();
                    for (int c : comp) {
                        int qx = c % MAP_WIDTH, qy = c / MAP_WIDTH;
                        bool onrim = false;
                        for (int dy = -1; dy <= 1 && !onrim; dy++)
                            for (int dx = -1; dx <= 1; dx++) {
                                int nx = qx + dx, ny = qy + dy;
                                if (in_this(nx, ny)) continue;
                                if (in_bounds(nx, ny) && is_lava(nx, ny)) continue;
                                onrim = true; break;
                            }
                        if (onrim) { nearedge[c] = 1; rimq.push_back(c); }
                    }
                    for (int depth = 1, lo = 0, hi = (int)rimq.size();
                         depth < EDGE_CLEARANCE; depth++, lo = hi, hi = (int)rimq.size()) {
                        for (int h = lo; h < hi; h++) {
                            int qx = rimq[h] % MAP_WIDTH, qy = rimq[h] / MAP_WIDTH;
                            for (int dy = -1; dy <= 1; dy++)
                                for (int dx = -1; dx <= 1; dx++) {
                                    int nx = qx + dx, ny = qy + dy;
                                    if (!in_this(nx, ny)) continue;
                                    size_t ni = (size_t)ny * MAP_WIDTH + nx;
                                    if (nearedge[ni]) continue;
                                    nearedge[ni] = (uint8_t)(depth + 1);
                                    rimq.push_back((int)ni);
                                }
                        }
                    }

                    auto paint_trail = [&](int ix, int iy) {
                        // Radius one, so the stroke is three tiles at its
                        // narrowest and only widens where it turns. Three is
                        // the floor worth having: the nine-slice needs a row
                        // down the middle with trail either side to put its
                        // fill in, and at two wide every tile is a border.
                        for (int by = -1; by <= 1; by++)
                            for (int bx = -1; bx <= 1; bx++) {
                                if (bx*bx + by*by > 1) continue;
                                int px2 = ix + bx, py2 = iy + by;
                                if (!in_bounds(px2, py2)) continue;
                                size_t pi = (size_t)py2 * MAP_WIDTH + px2;
                                // Never bleed into a neighbouring wasteland
                                // across a thin barrier: that leaves a scrap of
                                // trail somewhere it was not asked for.
                                if (!incomp[pi]) continue;
                                if (map->tiles[py2][px2] != TILE_WASTELAND) continue;
                                map->tiles[py2][px2] = TILE_WASTE_TRAIL;
                                // Nothing grows on a trail. Trees, dead trees,
                                // rocks and ore are all scattered long before
                                // the route through them is known, so they are
                                // cleared here rather than tested for at
                                // placement — the same reason the overlays
                                // beside water are swept afterwards.
                                map->overlay[py2][px2] = 0;
                            }
                    };

                    // One tile's worth of bridge: the three across the span, and
                    // nothing else. The trail brush cannot do this — it is a
                    // diamond swept along a line that bends, so it would round
                    // the bridge's corners off and widen its mouth wherever the
                    // trail turned to meet it. Here the deck is laid square
                    // across the direction of travel and only over lava, so a
                    // crossing is three wide from end to end whatever the trail
                    // either side of it is doing.
                    //
                    // `axis` is 0 for a span running east-west, 1 north-south.
                    auto paint_span = [&](int ix, int iy, int axis) {
                        for (int k = -1; k <= 1; k++) {
                            int px2 = ix + (axis == 1 ? k : 0);
                            int py2 = iy + (axis == 0 ? k : 0);
                            if (!in_bounds(px2, py2)) continue;
                            if (map->tiles[py2][px2] != TILE_LAVA) continue;
                            if (in_moat(px2, py2)) continue;
                            map->tiles[py2][px2]   = TILE_WASTE_BRIDGE;
                            map->overlay[py2][px2] = 0;
                        }
                    };

                    for (auto& e : edges) {
                        int from = e.first, to = e.second;
                        s_trail_edges++;
                        // Two dungeons close enough to share an anchor: there
                        // is nothing to route, and they are already joined.
                        if (from == to) { paint_trail(from % MAP_WIDTH, from / MAP_WIDTH); continue; }

                        // Route through the region rather than straight at the
                        // target: a straight run leaves the wasteland wherever
                        // it bends and paints nothing out there.
                        //
                        // Each attempt gives up a tile of the border margin,
                        // down to none, rather than leave the pair unjoined.
                        // Dropping it in one go would put a route that only
                        // needed to squeeze through one neck back against the
                        // rim for its whole length.
                        //
                        // The border rule is waived near either end. A dungeon
                        // can sit anywhere, including hard against the rim, and
                        // a route that may not start within three tiles of the
                        // border would fail outright and fall through to the
                        // attempt that hugs it for its whole length.
                        int fex = from % MAP_WIDTH, fey = from / MAP_WIDTH;
                        int tex = to   % MAP_WIDTH, tey = to   / MAP_WIDTH;
                        auto near_end = [&](int x, int y) {
                            return (abs(x - fex) <= ENDPOINT_FREE && abs(y - fey) <= ENDPOINT_FREE)
                                || (abs(x - tex) <= ENDPOINT_FREE && abs(y - tey) <= ENDPOINT_FREE);
                        };
                        bool found = false;
                        path.clear();
                        for (int margin = EDGE_CLEARANCE; margin >= 0 && !found; margin--) {
                            route.clear();
                            route.push_back(from);
                            prev[from] = from;
                            touched.push_back(from);
                            for (size_t h = 0; h < route.size() && !found; h++) {
                                int qx = route[h] % MAP_WIDTH, qy = route[h] / MAP_WIDTH;
                                // Vary which direction is tried first. Every
                                // shortest path here is the same length, and a
                                // fixed order always picks the same one: run
                                // east as far as possible, then turn. That came
                                // out looking like a circuit board.
                                ts = ts * 1664525u + 1013904223u;
                                int rot = (int)((ts >> 16) & 3u);
                                // Once out over lava there is only one way to
                                // go: on in the same direction, until ground.
                                // The direction is not remembered anywhere — it
                                // is where this tile was entered from, which is
                                // what prev already says.
                                //
                                // Crossing tile by tile rather than in one jump
                                // is what keeps a bridge from being a shortcut.
                                // A span counted as a single step cost the same
                                // as one pace whatever its length, so the search
                                // took every crossing it could find and the
                                // wasteland came out stitched with bridges.
                                // Stepped over, ten tiles of lava cost ten paces
                                // and a trail only crosses where crossing is
                                // genuinely the shorter way.
                                bool on_lava = is_lava(qx, qy);
                                int fixed_d = -1;
                                if (on_lava) {
                                    int p = prev[route[h]];
                                    int ddx = qx - p % MAP_WIDTH, ddy = qy - p / MAP_WIDTH;
                                    for (int d = 0; d < 4; d++)
                                        if (DX4[d] == ddx && DY4[d] == ddy) fixed_d = d;
                                }
                                for (int k = 0; k < 4 && !found; k++) {
                                    int d = on_lava ? fixed_d : ((k + rot) & 3);
                                    if (d < 0) break;
                                    int nx = qx + DX4[d], ny = qy + DY4[d];
                                    if (in_bounds(nx, ny)) {
                                        int ni = ny * MAP_WIDTH + nx;
                                        int run = on_lava ? runlen[route[h]] : 0;
                                        bool ok = false;
                                        if (incomp[ni]) {
                                            ok = true;                 // ground, either side
                                        } else if (spannable(nx, ny) && run < BRIDGE_MAX
                                                   && (on_lava || cool[route[h]] == 0)) {
                                            ok = true;                 // another tile of channel
                                        }
                                        if (ok && prev[ni] == -1 &&
                                            !(nearedge[ni] && nearedge[ni] <= margin
                                              && ni != to && !near_end(nx, ny))) {
                                            prev[ni] = route[h];
                                            runlen[ni] = incomp[ni] ? 0 : (uint8_t)(run + 1);
                                            // Landing from a crossing starts the
                                            // debt; walking pays it off a tile
                                            // at a time.
                                            cool[ni] = incomp[ni]
                                                ? (on_lava ? (uint8_t)BRIDGE_GAP
                                                           : (uint8_t)(cool[route[h]] ? cool[route[h]] - 1 : 0))
                                                : 0;
                                            touched.push_back(ni);
                                            route.push_back(ni);
                                            if (ni == to) { found = true; break; }
                                        }
                                    }
                                    if (on_lava) break;   // the one direction, and no other
                                }
                            }
                            if (found)
                                for (int cur = to; cur != from; cur = prev[cur])
                                    path.push_back(cur);
                            for (int t2 : touched) { prev[t2] = -1; runlen[t2] = 0; cool[t2] = 0; }
                            touched.clear();
                        }
                        if (!found) { s_trail_unroutable++; continue; }
                        std::reverse(path.begin(), path.end());
                        // Short paths are drawn too. Skipping them used to be
                        // the tidy option — the smoothing filter reads two
                        // points either side and has nothing to work with — but
                        // an unpainted link leaves the spanning tree in pieces
                        // a tile or two apart. Both loops below already guard
                        // their own bounds, so a short path simply passes
                        // through them unsmoothed.

                        // Smooth off the staircase, then drift the result
                        // sideways by a slowly changing amount so no stretch
                        // stays straight for long. A step that would leave the
                        // region is refused: checking only at the end is too
                        // late, because once a point has drifted out the later
                        // passes carry its neighbours after it.
                        std::vector<float> fxs(path.size()), fys(path.size());
                        for (size_t i = 0; i < path.size(); i++) {
                            fxs[i] = (float)(path[i] % MAP_WIDTH);
                            fys[i] = (float)(path[i] / MAP_WIDTH);
                        }

                        // Which points are on a bridge, and which way it runs:
                        // -1 for ground, 0 for a span going east-west, 1 for
                        // north-south. Taken from the tile rather than
                        // remembered from the search, so it does not matter how
                        // the path was put together.
                        //
                        // These points are pinned. Everything below moves the
                        // line about to take the ruled edge off it, and a bridge
                        // is the one part that has to stay ruled — the point of
                        // it is that it goes one way only. The ground either
                        // side of a span is pinned too, or the smoothing pulls
                        // the approach off the end of the deck.
                        std::vector<int8_t> span(path.size(), -1);
                        for (size_t i = 0; i < path.size(); i++) {
                            int px2 = path[i] % MAP_WIDTH, py2 = path[i] / MAP_WIDTH;
                            if (!is_lava(px2, py2)) continue;
                            size_t j = (i > 0) ? i - 1 : i + 1;
                            if (j >= path.size()) { span[i] = 0; continue; }
                            span[i] = (path[j] / MAP_WIDTH == py2) ? 0 : 1;
                        }
                        std::vector<uint8_t> pinned(path.size(), 0);
                        for (size_t i = 0; i < path.size(); i++) {
                            if (span[i] < 0) continue;
                            pinned[i] = 1;
                            if (i > 0) pinned[i-1] = 1;
                            if (i + 1 < path.size()) pinned[i+1] = 1;
                        }
                        for (int pass = 0; pass < 6; pass++) {
                            std::vector<float> nx2 = fxs, ny2 = fys;
                            for (size_t i = 2; i + 2 < path.size(); i++) {
                                if (pinned[i]) continue;
                                float sx2 = (fxs[i-2] + fxs[i-1]*2 + fxs[i]*3 + fxs[i+1]*2 + fxs[i+2]) / 9.0f;
                                float sy2 = (fys[i-2] + fys[i-1]*2 + fys[i]*3 + fys[i+1]*2 + fys[i+2]) / 9.0f;
                                if (in_this((int)sx2, (int)sy2)) {
                                    nx2[i] = sx2; ny2[i] = sy2;
                                }
                            }
                            fxs.swap(nx2); fys.swap(ny2);
                        }
                        float drift = 0.0f, dvel = 0.0f;
                        for (size_t i = 1; i + 1 < path.size(); i++) {
                            // A pinned point takes no drift, and the wander is
                            // wound back to nothing so it leaves the far end of
                            // a bridge as straight as it met the near one.
                            if (pinned[i]) { drift = 0.0f; dvel = 0.0f; continue; }
                            ts = ts * 1664525u + 1013904223u;
                            float kick = (float)((ts >> 16) % 2001u) / 1000.0f - 1.0f;
                            // Pull the wander back toward the centreline as it
                            // goes, not just clamp it: without a restoring
                            // force this is an integrated random walk, so its
                            // swing keeps growing with every extra step and a
                            // long path ends up far more distorted at its far
                            // end than near where it started. The spring term
                            // bounds the swing regardless of how long the path
                            // between two dungeons is, so the trail stays an
                            // even, gentle snake its whole length.
                            //
                            // How loose it is decides what the snake looks
                            // like. Stiff enough and the wander never gets
                            // anywhere: at 0.02 the swing settled around 0.7
                            // of a tile, well under the width of the trail
                            // itself, and long runs came out as ruled straight
                            // lines. This leaves it near a tile and a half,
                            // inside the clamp, and stretches a full swing out
                            // over some seventy tiles.
                            dvel = dvel * 0.94f + kick * 0.06f - drift * 0.008f;
                            drift += dvel;
                            if (drift >  2.0f) drift =  2.0f;
                            if (drift < -2.0f) drift = -2.0f;
                            float tx2 = fxs[i+1] - fxs[i-1], ty2 = fys[i+1] - fys[i-1];
                            float len2 = sqrtf(tx2*tx2 + ty2*ty2);
                            if (len2 < 0.001f) continue;
                            // Where the offset point is not somewhere a trail
                            // can go, shorten it rather than drop it. Refusing
                            // it outright left the point on the routed line
                            // while its neighbours stood a full drift away, and
                            // the brush, which draws between consecutive
                            // centres, filled that jump in solid — a bulge
                            // several tiles across in exactly the places the
                            // drift gets refused most, along the border and
                            // around lava. Backing off keeps the line
                            // continuous, so it leans away from the obstacle
                            // instead of jumping off it.
                            //
                            // The drift itself is wound back to what was
                            // accepted, or the spring would spend the next
                            // dozen steps hauling a value the line never took
                            // back toward the centre.
                            float taken = 0.0f;
                            for (float s = 1.0f; s > 0.0f; s -= 0.25f) {
                                float px2 = fxs[i] - ty2 / len2 * drift * s;
                                float py2 = fys[i] + tx2 / len2 * drift * s;
                                int ix = (int)px2, iy = (int)py2;
                                if (!in_this(ix, iy)) continue;
                                fxs[i] = px2; fys[i] = py2;
                                taken = s;
                                break;
                            }
                            drift *= taken;
                        }

                        // Draw between consecutive centres rather than stamping
                        // at each: smoothing and drift move points by a few
                        // tiles, and where one is carried out of the region it
                        // falls back to the routed original — a jump wide
                        // enough that two brush marks no longer overlap.
                        int lastx = -1, lasty = -1;
                        for (size_t i = 0; i < path.size(); i++) {
                            // A span point is laid where the route put it, deck
                            // only, and takes no part in the joining-up below:
                            // interpolating onto or off a bridge would step
                            // diagonally across the deck and cut its corners.
                            if (span[i] >= 0) {
                                paint_span(path[i] % MAP_WIDTH, path[i] / MAP_WIDTH, span[i]);
                                lastx = -1;
                                continue;
                            }
                            int ix = (int)fxs[i], iy = (int)fys[i];
                            if (!in_this(ix, iy)) {
                                ix = path[i] % MAP_WIDTH;
                                iy = path[i] / MAP_WIDTH;
                            }
                            if (lastx < 0) {
                                paint_trail(ix, iy);
                            } else {
                                int dxs = ix - lastx, dys = iy - lasty;
                                int steps = (abs(dxs) > abs(dys)) ? abs(dxs) : abs(dys);
                                if (steps < 1) steps = 1;
                                for (int s = 1; s <= steps; s++)
                                    paint_trail(lastx + dxs * s / steps,
                                                lasty + dys * s / steps);
                            }
                            lastx = ix; lasty = iy;
                        }
                    }
                }
                for (int c : comp) { incomp[c] = 0; nearedge[c] = 0; }
            }
        }
    }
    // The citadel's moat, laid again over whatever has happened since it was
    // first drawn. It is stamped when the castle is placed, because everything
    // after that needs to see the lava — the trail router reads it, and the
    // entrances keep away from it — but a stamp is only as good as the last
    // thing to write those tiles, and plenty of passes between there and here
    // write tiles without asking what was underneath. One four-tile entrance
    // across the ring is a doorway.
    //
    // Drawing it twice from the same seed costs a thousand steps and makes the
    // ring the last word rather than the first, so the invariant holds no
    // matter what is added to generation later: there is no way to the castle
    // that does not cross lava.
    if (map->castles[2].x >= 0)
        stamp_castle_moat(map, map->castles[2].x, map->castles[2].y, seed);

    // Last, after every pond, stream and town stamp has had its say.
    clear_overlays_near_liquid(map);
    GEN_STAGE(map, "final");
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

// Defined with the rest of the ground-cover code, but needs the sheet surface
// while init still has it loaded.
static void build_edge_textures(SDL_Renderer* renderer, SDL_Surface* sheet);

void tilemap_init_tile_cache(SDL_Renderer* renderer) {
    for (int i = 0; i < TILE_CACHE_SIZE && i < NUM_TILE_STYLES; i++) {
        SDL_Surface* surf = make_tile_surf(&tile_styles[i]);
        if (!surf) continue;
        s_tile_tex[i] = SDL_CreateTextureFromSurface(renderer, surf);
        SDL_FreeSurface(surf);
    }
    {
        SDL_Surface* surf = IMG_Load("assets/tileset.png");
        if (!surf) { printf("tileset.png not found: %s\n", SDL_GetError()); }
        else {
            SDL_SetColorKey(surf, SDL_TRUE, SDL_MapRGB(surf->format, 255, 0, 0));
            s_town0_tex = SDL_CreateTextureFromSurface(renderer, surf);
            if (s_town0_tex) SDL_SetTextureBlendMode(s_town0_tex, SDL_BLENDMODE_BLEND);
        }
        // Runs whether or not the sheet loaded: the biomes with no art take
        // their colour from tile_styles either way.
        build_edge_textures(renderer, surf);
        if (surf) SDL_FreeSurface(surf);
    }
    {
        SDL_Surface* surf = IMG_Load("assets/overworld_0.png");
        if (!surf) { printf("overworld_0.png not found: %s\n", SDL_GetError()); }
        else {
            SDL_SetColorKey(surf, SDL_TRUE, SDL_MapRGB(surf->format, 255, 0, 0));
            s_overworld0_tex = SDL_CreateTextureFromSurface(renderer, surf);
            SDL_FreeSurface(surf);
            if (s_overworld0_tex) SDL_SetTextureBlendMode(s_overworld0_tex, SDL_BLENDMODE_BLEND);
        }
    }
}

SDL_Texture* tilemap_get_town_tex(void) { return s_town0_tex; }

void tilemap_free_tile_cache(void) {
    for (int i = 0; i < TILE_CACHE_SIZE; i++) {
        if (s_tile_tex[i]) { SDL_DestroyTexture(s_tile_tex[i]); s_tile_tex[i] = nullptr; }
    }
    for (int c = 0; c < 256; c++) {
        for (int v = 0; v < EDGE_VARIANTS; v++)
            if (s_edge_tex[c][v]) { SDL_DestroyTexture(s_edge_tex[c][v]); s_edge_tex[c][v] = nullptr; }
        for (int v = 0; v < EDGE_VARIANTS; v++) {
            SDL_Texture** water[] = { &s_fill_tex[c][v], &s_shore_out_tex[c][v],
                                      &s_shore_in_tex[c][v] };
            for (int i = 0; i < 3; i++)
                if (*water[i]) { SDL_DestroyTexture(*water[i]); *water[i] = nullptr; }
        }
    }
    if (s_town0_tex)          { SDL_DestroyTexture(s_town0_tex);          s_town0_tex          = nullptr; }
    if (s_overworld0_tex)     { SDL_DestroyTexture(s_overworld0_tex);     s_overworld0_tex     = nullptr; }
}

// Helper: copy a cached tile texture to the screen, falling back to immediate draw.
static void blit_tile(SDL_Renderer* renderer, int tile_id,
                      int screen_x, int screen_y, int draw_size) {
    if (tile_id >= TILE_OW0_BASE && s_overworld0_tex) {
        int idx = tile_id - TILE_OW0_BASE;
        int col = idx % TOWN0_SHEET_COLS;
        int row = idx / TOWN0_SHEET_COLS;
        SDL_Rect src = { col * 16, row * 16, 16, 16 };
        SDL_Rect dst = { screen_x, screen_y, draw_size, draw_size };
        SDL_RenderCopy(renderer, s_overworld0_tex, &src, &dst);
    } else if (tile_id >= TILE_TOWN0_BASE && s_town0_tex) {
        int idx = tile_id - TILE_TOWN0_BASE;
        int col = idx % TOWN0_SHEET_COLS;
        int row = idx / TOWN0_SHEET_COLS;
        SDL_Rect src = { col * 16, row * 16, 16, 16 };
        SDL_Rect dst = { screen_x, screen_y, draw_size, draw_size };
        SDL_RenderCopy(renderer, s_town0_tex, &src, &dst);
    } else if (tile_id >= 0 && tile_id < TILE_CACHE_SIZE && s_tile_tex[tile_id]) {
        SDL_Rect dst = { screen_x, screen_y, draw_size, draw_size };
        SDL_RenderCopy(renderer, s_tile_tex[tile_id], NULL, &dst);
    } else {
        draw_tile_ascii(renderer, tile_id, screen_x, screen_y, draw_size);
    }
}

// ── Ground cover variants ───────────────────────────────────────────────────
// Blocks of six 16px cells in assets/tileset.png, one per biome. Which cell a
// tile draws is purely a draw-time choice: the map still stores TILE_GRASS,
// TILE_SAND and the rest, so collision, the minimap and worldgen are untouched.
//
// The blocks do not all lay out the same way, so a cover says which kind it is
// and the picker follows the matching rule:
//
//   TUFTS  rows 2-3, three columns — grass at 18-20, meadow at 21-23, snow at
//          24-26. Cells 1 and 2 are one clump spanning two tiles and have to
//          stay together left to right; 3, 4 and 5 are lone tufts; 6 is plain.
//   DUNES  rows 0-1, cols 21-23 — cells 1 to 4 are one dune oval spread over a
//          2x2 and have to stay square and aligned; 5 and 6 are open sand.
//   ONE    a single cell that simply repeats, for water and lava.
static constexpr int sheet_cell(int col, int row) {
    return TILE_TOWN0_BASE + row * TOWN0_SHEET_COLS + col;
}

enum CoverKind { COVER_TUFTS, COVER_DUNES, COVER_SCATTER, COVER_NINESLICE, COVER_ONE };

struct GroundCover {
    CoverKind kind;
    int v[8];      // the shaped cells; what they mean depends on kind
    int nv;        // how many of them this cover actually uses
    int plain;     // the featureless cell, and what the biome's colour samples
    int flat;      // stand-in tile when the sheet failed to load
};

static constexpr GroundCover cover_tufts(int clump_l, int clump_r, int tuft_a,
                                         int tuft_b, int tuft_c, int plain, int flat) {
    return { COVER_TUFTS, { clump_l, clump_r, tuft_a, tuft_b, tuft_c }, 5, plain, flat };
}
// Dune cells in reading order: top-left, top-right, bottom-left, bottom-right,
// then the speckled open sand. `plain` is the bare cell.
static constexpr GroundCover cover_dunes(int tl, int tr, int bl, int br,
                                         int speckled, int plain, int flat) {
    return { COVER_DUNES, { tl, tr, bl, br, speckled }, 5, plain, flat };
}
// Loose variants of one ground, no shape spanning more than a tile: pick per
// tile and be done.
static constexpr GroundCover cover_scatter(int a, int b, int plain, int flat) {
    return { COVER_SCATTER, { a, b }, 2, plain, flat };
}
// A hand-drawn nine-slice: the eight border cells in reading order, with the
// centre as the plain fill. The tile picks its cell from which of its four
// neighbours are the same cover, so the border lands on the tile grid — square
// and laid-by-hand, rather than the smoothed outline the coverage field draws.
static constexpr GroundCover cover_nineslice(int tl, int t, int tr,
                                             int l,  int c, int r,
                                             int bl, int b, int br, int flat) {
    return { COVER_NINESLICE, { tl, t, tr, l, r, bl, b, br }, 8, c, flat };
}
static constexpr GroundCover cover_single(int cell, int flat) {
    return { COVER_ONE, { cell }, 0, cell, flat };
}

static constexpr GroundCover COVER_GRASS = cover_tufts(
    sheet_cell(18, 2), sheet_cell(19, 2),
    sheet_cell(20, 2), sheet_cell(18, 3), sheet_cell(19, 3),
    sheet_cell(20, 3), TILE_GRASS);
// Same six roles three columns right: mint base, pink blossoms.
static constexpr GroundCover COVER_MEADOW = cover_tufts(
    sheet_cell(21, 2), sheet_cell(22, 2),
    sheet_cell(23, 2), sheet_cell(21, 3), sheet_cell(22, 3),
    sheet_cell(23, 3), TILE_MEADOW);
// Three further right: white base, gold detail. Pixel for pixel the grass
// block's shapes recoloured, so the six roles line up exactly.
static constexpr GroundCover COVER_SNOW = cover_tufts(
    sheet_cell(24, 2), sheet_cell(25, 2),
    sheet_cell(26, 2), sheet_cell(24, 3), sheet_cell(25, 3),
    sheet_cell(26, 3), TILE_SNOW);
// Desert: the dune spans cols 21-22 over rows 0-1, with the two open sands
// stacked in col 23.
static constexpr GroundCover COVER_DESERT = cover_dunes(
    sheet_cell(21, 0), sheet_cell(22, 0),
    sheet_cell(21, 1), sheet_cell(22, 1),
    sheet_cell(23, 0), sheet_cell(23, 1), TILE_SAND);
// Wasteland: just the main cell at col 25 row 4. The two spotty variants either
// side of it are drawn but unused — each carries a large light patch, and even
// sparingly they read as blotches rather than as texture.
static constexpr GroundCover COVER_WASTE = cover_single(sheet_cell(25, 4), TILE_WASTELAND);
// The trail worn through it, drawn from the hand-cut nine-slice at cols 24-26
// rows 5-7. Its borders come out of the art and sit on the tile grid, which is
// the point: square corners that look laid down rather than eroded.
static constexpr GroundCover COVER_TRAIL = cover_nineslice(
    sheet_cell(24, 5), sheet_cell(25, 5), sheet_cell(26, 5),
    sheet_cell(24, 6), sheet_cell(25, 6), sheet_cell(26, 6),
    sheet_cell(24, 7), sheet_cell(25, 7), sheet_cell(26, 7), TILE_WASTE_TRAIL);
// Water: one tile, carrying its own ripples, and it repeats seamlessly.
static constexpr GroundCover COVER_WATER = cover_single(sheet_cell(14, 0), TILE_WATER);
// Lava, one cell to its right, same idea: dark base with its own hot speckle.
static constexpr GroundCover COVER_LAVA  = cover_single(sheet_cell(15, 0), TILE_LAVA);

// ── Biome edge ──────────────────────────────────────────────────────────────
// Where two biomes meet the join is one straight line along the tile grid,
// which reads as a cut. Instead each tile scatters its neighbour's colour into
// the pixels nearest it, thinning inward, the way Mother 1 runs grass into
// desert: the shape of the border stays smooth and the only fine detail is a
// dotted fringe a few pixels deep.
//
// Smoothness comes from treating the tile grid as a field rather than as a set
// of sides. Each pixel asks how much of the surrounding neighbourhood is the
// other biome, weighted by distance. Along a straight run the two sides balance
// exactly on the tile line, so it stays straight; at a corner the surrounding
// tiles outvote it and the boundary curves. Nothing wanders, which is what
// separates this from a hand-wobbled line — the shape is the map's own shape,
// smoothed.
//
// The fringe is the only randomness. In the narrow band where coverage is
// undecided a pixel is lit by chance, with the odds tracking coverage, so the
// dots crowd at the boundary and peter out either side. Both tiles compute the
// same field from the same neighbourhood, so they agree about where the border
// lies and their fringes interlock instead of fighting.
//
// The tile keeps its own tufts underneath — this paints over a few pixels, it
// does not replace the tile. Generated rather than drawn into the sheet, so it
// stays in step with the palette and a new biome needs no new art.
static const float EDGE_KERNEL_R = 1.6f;   // smoothing radius, in tiles
static const float EDGE_FRINGE   = 0.10f;  // half-width of the undecided band
// Coverage, not pixels: the field falls about 0.03 per pixel across a straight
// shore, so this lands the shallows at one pixel. 0.07 is where it becomes two.
static const float SHORE_BAND    = 0.05f;
// A perfectly smooth waterline looks poured rather than worn. This nudges where
// the line falls, per pixel, by well under a pixel's worth of coverage — enough
// to rough it up without letting it wander off the shape the field describes.
static const float SHORE_JITTER  = 0.025f;

// Biomes that take part. Order is only a tie-break: the field decides which
// biome owns a pixel, and it is symmetric, so neither side of a border gives
// way. Liquids are in — the same treatment gives shorelines, riverbanks and the
// rim of a lava pool. Cliffs stay out; a cliff is a change in height rather than
// in ground, and wants real edge art rather than a softened outline.
//
// This is drawing only. Collision still reads the tile grid, so the walkable
// line and the drawn waterline disagree by the few pixels the fringe covers.
// A biome can cover several tile ids. Ocean, river, hub and pond are one water
// as far as edges go: they are the same blue, and treating them apart would put
// a border where a river runs into the sea and have it fringe against itself.
// A biome may also name a shore colour. Where one is set, both sides of that
// biome's borders fringe in it instead of in each other's ground colour: water
// gets a pale rim that reads as shallows and holds the waterline apart from
// whatever it runs along, rather than blue crumbling into green.
//
// The pale is tinted blue rather than pure white on purpose — snow is very near
// white already, and an untinted rim would vanish along a snow coast.
// Three independent questions, one flag each:
//
//   hard_edge  the boundary is a clean outline rather than two grounds
//              stippled together, and it follows the smoothed field instead of
//              the tile grid.
//   own_edges  the biome's own art already draws its borders, so nothing is
//              laid over them — no stipple, no outline. The wasteland trail is
//              a nine-slice and would otherwise get a second border on top of
//              the one it is drawn with.
//   solid      you cannot walk into it, and collision reads that same outline
//              so the edge you see is the edge you hit.
//   shore      a band drawn alongside the outline, in the given colour.
//
// Water is all three. Lava is hard-edged and solid with no shallows — a pale
// rim would read as surf, and molten rock has none. A wasteland trail is
// hard-edged so it reads as a worn path, but it is ground you walk on, which is
// why these cannot be one flag.
#define MAX_BIOME_TILES 4
struct GroundBiome {
    int tiles[MAX_BIOME_TILES];  // TileIds this biome paints, -1 padded
    const GroundCover* cover;    // sheet block, or null for biomes with no art yet
    bool hard_edge;              // crisp outline, taken from the field
    bool solid;                  // impassable, and collision follows that outline
    bool own_edges;              // borders come from the art; add nothing
    uint8_t r, g, b;             // plain colour, filled in at load
    int sr, sg, sb;              // shore colour, or -1 for none
};
static GroundBiome s_biomes[] = {
    { { TILE_GRASS,     -1, -1, -1 },                  &COVER_GRASS,  false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_MEADOW,    -1, -1, -1 },                  &COVER_MEADOW, false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_SAND,      -1, -1, -1 },                  &COVER_DESERT, false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_WASTELAND, -1, -1, -1 },                  &COVER_WASTE,  false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_WASTE_TRAIL, -1, -1, -1 },                &COVER_TRAIL,  false, false, true,  0,0,0,  -1,  -1,  -1 },
    { { TILE_SNOW,      -1, -1, -1 },                  &COVER_SNOW,   false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_WATER, TILE_RIVER, TILE_HUB, TILE_POND }, &COVER_WATER,  true,  true,  false, 0,0,0, 220, 240, 255 },
    { { TILE_LAVA,      -1, -1, -1 },                  &COVER_LAVA,   true,  true,  false, 0,0,0,  -1,  -1,  -1 },
};
static const int NUM_GROUND_BIOMES = (int)(sizeof(s_biomes) / sizeof(s_biomes[0]));

// Index into s_biomes, or -1 for a tile that takes no part in biome edges.
static int biome_at(const Tilemap* map, int x, int y) {
    if (!in_bounds(x, y)) return -1;
    int t = map->tiles[y][x];
    if (t >= TILE_TOWN0_BASE) return 0;  // town cells paint grass behind themselves
    for (int i = 0; i < NUM_GROUND_BIOMES; i++)
        for (int j = 0; j < MAX_BIOME_TILES && s_biomes[i].tiles[j] >= 0; j++)
            if (s_biomes[i].tiles[j] == t) return i;
    return -1;
}

// Which block a tile draws its ground from, or null if it draws no ground.
static const GroundCover* tile_cover(const Tilemap* map, int x, int y) {
    int b = biome_at(map, x, y);
    return b < 0 ? nullptr : s_biomes[b].cover;
}

static inline unsigned int cover_hash(int x, int y, unsigned int salt);

// Neighbour ordering for a config byte: bit 0 is N, then clockwise.
static const int EDGE_NB[8][2] = {
    {0,-1}, {1,-1}, {1,0}, {1,1}, {0,1}, {-1,1}, {-1,0}, {-1,-1}
};

// Coverage of `other` at one pixel: the eight neighbours plus this tile, each
// weighted by how near its centre is, normalised to 0..1. Smoothing a binary
// tile grid this way is what rounds the corners — a run of straight edge stays
// straight because the two sides balance exactly on the tile line, while at a
// corner the surrounding tiles outvote it and the boundary curves.
static float edge_coverage(int config, int px, int py) {
    float u = (px + 0.5f) / 16.0f, v = (py + 0.5f) / 16.0f;
    float num = 0.0f, den = 0.0f;
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            float ex = u - (dx + 0.5f), ey = v - (dy + 0.5f);
            float t = 1.0f - (ex * ex + ey * ey) / (EDGE_KERNEL_R * EDGE_KERNEL_R);
            if (t <= 0.0f) continue;
            float w = t * t;
            den += w;
            if (dx == 0 && dy == 0) continue;      // this tile is never the other biome
            for (int i = 0; i < 8; i++)
                if (EDGE_NB[i][0] == dx && EDGE_NB[i][1] == dy) {
                    if (config & (1 << i)) num += w;
                    break;
                }
        }
    }
    return den > 0.0f ? num / den : 0.0f;
}

// Ground-to-ground mask: solid where the other biome clearly owns the pixel,
// clear where it clearly does not, and stippled in between. The stipple is the
// only high-frequency detail in the transition — it thins out with coverage,
// which is what turns the boundary into a dotted fringe a few pixels deep
// rather than a drawn line.
static void edge_mask(int config, int variant, bool* on) {
    for (int py = 0; py < 16; py++) {
        for (int px = 0; px < 16; px++) {
            float f = edge_coverage(config, px, py);
            bool lit;
            if      (f >= 0.5f + EDGE_FRINGE) lit = true;
            else if (f <= 0.5f - EDGE_FRINGE) lit = false;
            else {
                float p = (f - (0.5f - EDGE_FRINGE)) / (2.0f * EDGE_FRINGE);
                unsigned int h = cover_hash(px, py, 0xF2149E00u + (unsigned int)variant);
                lit = (float)(h % 1000u) / 1000.0f < p;
            }
            on[py * 16 + px] = lit;
        }
    }
}

// Where the waterline falls at one pixel. Half coverage, roughed up a little so
// the line is worn rather than poured. Both the masks and the collision test go
// through here, which is what keeps the shore you see and the shore you can
// walk to the same shore — the jitter would pull them apart otherwise.
static inline float shore_threshold(int px, int py, int variant) {
    unsigned int h = cover_hash(px, py, 0x54093E00u + (unsigned int)variant);
    return 0.5f + SHORE_JITTER * ((float)(h % 2001u) / 1000.0f - 1.0f);
}

// Solid mask for a window around that line, used to build the water treatment
// out of the same field. A waterline is not a fringe: it is a clean outline
// with shallows alongside, so these are hard-edged rather than stippled. The
// bounds are offsets from the threshold, so the shallows follow the outline
// wherever the jitter puts it instead of drifting off it.
//   0, +big  — the other biome's own body, giving the outline
//   -S, 0    — the band just outside it
//   0, +S    — the band just inside it
// Which of the last two a tile wants depends on which side of the water it is
// on: the shallows always sit on the land side, so a tile standing in water
// takes the inner band and one on the bank takes the outer.
static void band_mask(int config, int variant, float lo_off, float hi_off, bool* on) {
    for (int py = 0; py < 16; py++) {
        for (int px = 0; px < 16; px++) {
            float f = edge_coverage(config, px, py);
            float t = shore_threshold(px, py, variant);
            on[py * 16 + px] = (f >= t + lo_off && f < t + hi_off);
        }
    }
}

// Masks are white where the neighbouring biome laps over, clear elsewhere, and
// get colour-modulated at draw time — so one set serves every pair of biomes
// rather than needing a set per pair.
static SDL_Texture* mask_texture(SDL_Renderer* renderer, const bool* on) {
    SDL_Surface* out = SDL_CreateRGBSurfaceWithFormat(0, 16, 16, 32, SDL_PIXELFORMAT_RGBA32);
    if (!out) return nullptr;
    uint32_t* dp = (uint32_t*)out->pixels;
    int dpitch = out->pitch / 4;
    uint32_t lit   = SDL_MapRGBA(out->format, 255, 255, 255, 255);
    uint32_t clear = SDL_MapRGBA(out->format, 0, 0, 0, 0);
    for (int py = 0; py < 16; py++)
        for (int px = 0; px < 16; px++)
            dp[py * dpitch + px] = on[py * 16 + px] ? lit : clear;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(renderer, out);
    if (tex) SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND);
    SDL_FreeSurface(out);
    return tex;
}

static void build_edge_textures(SDL_Renderer* renderer, SDL_Surface* sheet) {
    // Each biome's plain colour: the commonest colour in its plain cell where it
    // has art, otherwise the flat style colour the tile already draws with.
    // Commonest rather than any one pixel — water's cell carries ripples, and
    // sampling its centre would have taken whatever happened to be there.
    SDL_Surface* src = sheet ? SDL_ConvertSurfaceFormat(sheet, SDL_PIXELFORMAT_RGBA32, 0) : nullptr;
    for (int i = 0; i < NUM_GROUND_BIOMES; i++) {
        GroundBiome* b = &s_biomes[i];
        if (b->cover && src) {
            int idx = b->cover->plain - TILE_TOWN0_BASE;
            int cx = (idx % TOWN0_SHEET_COLS) * 16, cy = (idx / TOWN0_SHEET_COLS) * 16;
            const uint32_t* sp = (const uint32_t*)src->pixels;
            int spitch = src->pitch / 4;
            uint32_t best = 0; int best_n = 0;
            for (int py = 0; py < 16; py++) {
                for (int px = 0; px < 16; px++) {
                    uint32_t c = sp[(cy + py) * spitch + cx + px];
                    int n = 0;
                    for (int qy = 0; qy < 16; qy++)
                        for (int qx = 0; qx < 16; qx++)
                            if (sp[(cy + qy) * spitch + cx + qx] == c) n++;
                    if (n > best_n) { best_n = n; best = c; }
                }
            }
            uint8_t a;
            SDL_GetRGBA(best, src->format, &b->r, &b->g, &b->b, &a);
        } else if (b->tiles[0] >= 0 && b->tiles[0] < NUM_TILE_STYLES) {
            b->r = tile_styles[b->tiles[0]].bg_r;
            b->g = tile_styles[b->tiles[0]].bg_g;
            b->b = tile_styles[b->tiles[0]].bg_b;
        }
    }
    if (src) SDL_FreeSurface(src);

    // 256 neighbourhoods, but only the ones with a neighbour in them can ever be
    // asked for; config 0 stays null and is skipped at draw time.
    bool on[16 * 16];
    for (int config = 1; config < 256; config++) {
        for (int v = 0; v < EDGE_VARIANTS; v++) {
            edge_mask(config, v, on);
            s_edge_tex[config][v] = mask_texture(renderer, on);
            band_mask(config, v, 0.0f, 2.0f, on);
            s_fill_tex[config][v] = mask_texture(renderer, on);
            band_mask(config, v, -SHORE_BAND, 0.0f, on);
            s_shore_out_tex[config][v] = mask_texture(renderer, on);
            band_mask(config, v, 0.0f, SHORE_BAND, on);
            s_shore_in_tex[config][v] = mask_texture(renderer, on);
        }
    }
}

static inline unsigned int cover_hash(int x, int y, unsigned int salt) {
    unsigned int h = (unsigned int)x * 73856093u ^ (unsigned int)y * 19349663u ^ salt;
    h ^= h >> 13; h *= 1274126177u; h ^= h >> 16;
    return h;
}

// Raw chance a clump begins at this tile. A start claims two tiles and is
// suppressed beside another start, so ~8% here lands near 15% of the field
// under clumps: 2 * p * (1-p) with p = 0.08.
static const unsigned int COVER_CLUMP_PCT = 8;
static inline bool cover_clump_raw(int x, int y) {
    return (cover_hash(x, y, 0x9e3779b9u) % 100u) < COVER_CLUMP_PCT;
}

static int tuft_variant(const Tilemap* map, int x, int y, const GroundCover* cover) {
    // Right half first: a start beside a start is suppressed, which is what
    // stops a run of raw starts from emitting a right half with no left half.
    // Both halves also have to sit on the same cover, or the pair straddles a
    // biome edge and a green half ends up against a pink one. The edge lip does
    // not enter into it — a lipped tile still draws its own variant underneath.
    auto pairs_with = [&](int nx) { return tile_cover(map, nx, y) == cover; };
    bool left_starts = x > 0 && pairs_with(x - 1)
                             && cover_clump_raw(x - 1, y)
                             && !(x > 1 && cover_clump_raw(x - 2, y));
    if (left_starts) return cover->v[1];
    if (cover_clump_raw(x, y) && !(x > 0 && cover_clump_raw(x - 1, y))
                              && pairs_with(x + 1))
        return cover->v[0];

    // Of the tiles left over, ~53% plain and the rest split between the three
    // tufts, which comes out near the intended 45/40/15 plain/tuft/clump mix.
    unsigned int v = cover_hash(x, y, 0x85ebca6bu) % 100u;
    if (v < 53) return cover->plain;
    if (v < 69) return cover->v[2];
    if (v < 85) return cover->v[3];
    return cover->v[4];
}

// Raw chance a dune begins at this tile. A dune claims four tiles and starts
// are suppressed where they would overlap, so the ground actually covered comes
// out around three times this — 2 here leaves the desert mostly open sand.
static const unsigned int COVER_DUNE_PCT = 2;
static inline bool cover_dune_raw(int x, int y) {
    return (cover_hash(x, y, 0xD0E5A17Du) % 100u) < COVER_DUNE_PCT;
}

// A dune is one oval spread across a 2x2, so unlike a tuft it has to stay
// square and aligned — a stray quarter reads as a smear, not a dune.
//
// A start claims (x,y) and the three cells right and below, so two starts
// within one tile of each other on both axes would overlap. Where they do, the
// one earlier in reading order wins. That test is a pure function of the hash
// field, so every tile reaches the same answer without depending on scan order.
// It is slightly conservative — a start can be suppressed by a raw neighbour
// that was itself suppressed — which costs a few dunes and no correctness.
static bool cover_dune_start(const Tilemap* map, int x, int y, const GroundCover* cover) {
    if (!cover_dune_raw(x, y)) return false;
    // All four cells have to be drawing this same cover, or the dune runs off
    // the edge of the desert and leaves part of an oval on the grass. The
    // origin included: this is asked of neighbouring tiles too, and one of
    // those sitting on grass would otherwise anchor a dune it cannot draw.
    if (tile_cover(map, x,     y)     != cover) return false;
    if (tile_cover(map, x + 1, y)     != cover) return false;
    if (tile_cover(map, x,     y + 1) != cover) return false;
    if (tile_cover(map, x + 1, y + 1) != cover) return false;
    for (int dy = -1; dy <= 1; dy++)
        for (int dx = -1; dx <= 1; dx++) {
            bool earlier = (dy < 0) || (dy == 0 && dx < 0);
            if (earlier && cover_dune_raw(x + dx, y + dy)) return false;
        }
    return true;
}

static int dune_variant(const Tilemap* map, int x, int y, const GroundCover* cover) {
    // At most one of these four can be a start — two starts that close would
    // overlap, and the suppression above rules that out — so no tile is ever
    // claimed by two dunes.
    if (cover_dune_start(map, x,     y,     cover)) return cover->v[0];
    if (cover_dune_start(map, x - 1, y,     cover)) return cover->v[1];
    if (cover_dune_start(map, x,     y - 1, cover)) return cover->v[2];
    if (cover_dune_start(map, x - 1, y - 1, cover)) return cover->v[3];

    // Everything else is open sand, speckled or bare.
    return (cover_hash(x, y, 0x5A4D0000u) % 100u) < 40u ? cover->v[4] : cover->plain;
}

// Mostly plain, with the loose variants sprinkled in and split evenly between
// them. Kept sparse on purpose: these variants carry a large light patch each,
// so even one tile in ten reads as a blotchy field rather than as texture.
static const unsigned int COVER_SCATTER_PCT = 8;   // share of tiles that get a variant
static int scatter_variant(int x, int y, const GroundCover* cover) {
    unsigned int v = cover_hash(x, y, 0x5CA77E00u) % 100u;
    if (v >= COVER_SCATTER_PCT || cover->nv <= 0) return cover->plain;
    return cover->v[(int)v * cover->nv / (int)COVER_SCATTER_PCT];
}

// Pick the border cell from which sides face something else. Corners are tested
// before edges, since a corner tile has two sides exposed and would otherwise
// match an edge first.
//
// Two opposite sides exposed at once — a stretch only one tile wide — has no
// cell in a nine-slice; that falls through to the single-edge tests and comes
// out as one border with the other missing. Keeping trails wider than a tile is
// what avoids it.
static int nineslice_variant(const Tilemap* map, int x, int y, const GroundCover* cover) {
    auto same = [&](int nx, int ny) { return tile_cover(map, nx, ny) == cover; };
    bool n = same(x, y - 1), s = same(x, y + 1);
    bool w = same(x - 1, y), e = same(x + 1, y);

    if (!n && !w) return cover->v[0];
    if (!n && !e) return cover->v[2];
    if (!s && !w) return cover->v[5];
    if (!s && !e) return cover->v[7];
    if (!n) return cover->v[1];
    if (!s) return cover->v[6];
    if (!w) return cover->v[3];
    if (!e) return cover->v[4];
    return cover->plain;
}

// ── Cliff art ───────────────────────────────────────────────────────────────
// Hand-drawn at cols 27-29, rows 0-4 of the sheet, as one closed silhouette:
//
//     NW   back   NE          row 0
//     W    top    E           rows 1-3, three variants of the same band
//     SW   south  SE          row 4
//
// The three middle rows are the same band drawn three times over, so a long
// face or a wide plateau picks between them per tile instead of repeating one
// cell into a visible stripe.
//
// It lines up with where generation already puts each piece: the plateau body
// takes the middle, and the rim tiles it lays around the body — back face one
// row north, side faces down each flank, south face below, corners on the
// diagonals — take the eight around it. So there is nothing to work out at
// draw time beyond which row a middle cell should use; the tile id already
// says which of the nine it is.
static const int CLIFF_ART_COL = 27;   // leftmost column of the block
static const int CLIFF_ART_ROW = 0;    // topmost row

// Only elevation 1 is drawn so far. The rest take the same art until their own
// blocks exist; the shade that tells the layers apart comes from tile_styles
// and is applied over the top of it.
static int cliff_art_cell(int x, int y, int t) {
    if (!s_town0_tex) return -1;
    auto band = [&](int col) {
        // 1, 2 or 3 — one of the three middle rows.
        return sheet_cell(col, CLIFF_ART_ROW + 1 + (int)(cover_hash(x, y, 0xC11FF000u) % 3u));
    };
    const int L = CLIFF_ART_COL, M = CLIFF_ART_COL + 1, R = CLIFF_ART_COL + 2;
    const int TOP = CLIFF_ART_ROW, BOT = CLIFF_ART_ROW + 4;

    // Plateau surface, whichever biome it belongs to: the art draws one top and
    // all three families use it.
    if (t == TILE_CLIFF || (t >= TILE_CLIFF_2 && t <= TILE_CLIFF_5)) return band(M);
    if (t >= TILE_CLIFF_SNOW_1  && t <= TILE_CLIFF_SNOW_5)  return band(M);
    if (t >= TILE_CLIFF_WASTE_1 && t <= TILE_CLIFF_WASTE_5) return band(M);

    if (t >= TILE_CLIFF_SIDE_1   && t <= TILE_CLIFF_SIDE_5)   return band(L);
    if (t >= TILE_CLIFF_SIDE_E_1 && t <= TILE_CLIFF_SIDE_E_5) return band(R);
    if (t >= TILE_CLIFF_BACK_1   && t <= TILE_CLIFF_BACK_5)   return sheet_cell(M, TOP);
    if (t >= TILE_CLIFF_EDGE_1   && t <= TILE_CLIFF_EDGE_5)   return sheet_cell(M, BOT);

    // The corners. Generation lays SW and SE at the foot of a side face and NW
    // and NE on the diagonal above it, which is where the silhouette's four
    // rounded corners belong.
    if (t >= TILE_CLIFF_CORNER_SW_1 && t <= TILE_CLIFF_CORNER_SW_5) return sheet_cell(L, BOT);
    if (t >= TILE_CLIFF_CORNER_SE_1 && t <= TILE_CLIFF_CORNER_SE_5) return sheet_cell(R, BOT);
    if (t >= TILE_CLIFF_CORNER_NW_1 && t <= TILE_CLIFF_CORNER_NW_5) return sheet_cell(L, TOP);
    if (t >= TILE_CLIFF_CORNER_NE_1 && t <= TILE_CLIFF_CORNER_NE_5) return sheet_cell(R, TOP);
    return -1;
}

// What shows through the corners. Those four cells key their outside corner out
// to nothing, so something has to be under them, and it should be the ground
// the cliff is standing in rather than a fixed guess — grass behind a snowfield
// cliff would read as a hole. Nearest neighbour that is not itself cliff.
static const GroundCover* cliff_under_cover(const Tilemap* map, int x, int y) {
    static const int NB[8][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{-1,1},{1,-1},{-1,-1}};
    for (int i = 0; i < 8; i++) {
        int nx = x + NB[i][0], ny = y + NB[i][1];
        if (!in_bounds(nx, ny)) continue;
        if (cliff_art_cell(nx, ny, map->tiles[ny][nx]) >= 0) continue;
        const GroundCover* c = tile_cover(map, nx, ny);
        if (c) return c;
    }
    return nullptr;
}

static int cover_variant(const Tilemap* map, int x, int y, const GroundCover* cover) {
    if (!s_town0_tex) return cover->flat;  // sheet missing — keep the flat tile
    switch (cover->kind) {
        case COVER_ONE:       return cover->plain;
        case COVER_DUNES:     return dune_variant(map, x, y, cover);
        case COVER_SCATTER:   return scatter_variant(x, y, cover);
        case COVER_NINESLICE: return nineslice_variant(map, x, y, cover);
        default:              return tuft_variant(map, x, y, cover);
    }
}

// Which neighbouring biomes reach into this tile, and the neighbourhood shape
// each of them makes. Kept apart from the drawing so the decision can be
// inspected without a renderer.
//
// Every distinct neighbouring biome is handled separately, so a tile in a
// three-biome corner fringes each of them in its own colour rather than having
// to settle on one. Precedence does not come into it: the field is symmetric,
// so wherever this tile scatters a neighbour's colour inward, that neighbour is
// scattering this tile's colour back the other way by the same amount.
#define MAX_EDGE_NEIGHBOURS 4
struct EdgeFringe {
    int count;
    int biome[MAX_EDGE_NEIGHBOURS];   // index into s_biomes
    int config[MAX_EDGE_NEIGHBOURS];  // which of the eight neighbours hold it
    int variant;
};

static void biome_fringe(const Tilemap* map, int x, int y, EdgeFringe* out) {
    out->count = 0;
    out->variant = 0;
    int mine = biome_at(map, x, y);
    if (mine < 0) return;
    out->variant = (int)(cover_hash(x, y, 0xF7149E00u) % EDGE_VARIANTS);

    for (int i = 0; i < 8; i++) {
        int b = biome_at(map, x + EDGE_NB[i][0], y + EDGE_NB[i][1]);
        if (b < 0 || b == mine) continue;
        int slot = -1;
        for (int j = 0; j < out->count; j++)
            if (out->biome[j] == b) { slot = j; break; }
        if (slot < 0) {
            if (out->count == MAX_EDGE_NEIGHBOURS) continue;  // more than four meeting here
            slot = out->count++;
            out->biome[slot] = b;
            out->config[slot] = 0;
        }
        out->config[slot] |= 1 << i;
    }
}

static inline bool biome_hard_edge(int b) { return b >= 0 && s_biomes[b].hard_edge; }
static inline bool biome_own_edges(int b) { return b >= 0 && s_biomes[b].own_edges; }
static inline bool biome_solid(int b)     { return b >= 0 && s_biomes[b].solid; }
static inline bool biome_has_shore(int b) { return b >= 0 && s_biomes[b].sr >= 0; }

// What gets laid over a tile at its borders, in order. Kept apart from the
// drawing so the decision can be inspected without a renderer.
//
// Two treatments. Ground against ground interleaves: a stippled fringe in the
// neighbour's own colour, dots crowding the boundary and petering out. Anything
// against water instead gets a hard outline plus a band of shallows, because a
// waterline wants to read as an edge rather than as two grounds mixing.
//
// The shallows always sit on the land side of that line. Which band gives that
// depends on where the tile stands: on the bank it is the ring just outside the
// water, and standing in the water it is the ring just inside the land that
// rounds into the tile. Both sides work from the same field, so the two halves
// meet as one continuous band.
enum EdgeMaskKind { MASK_FRINGE, MASK_FILL, MASK_SHORE_OUT, MASK_SHORE_IN };
struct EdgeLayer {
    int kind;
    int config;   // which surrounding tiles hold the other biome
    int variant;  // stipple pattern for a fringe, jitter pattern for a waterline
    uint8_t r, g, b;
};
#define MAX_EDGE_LAYERS (MAX_EDGE_NEIGHBOURS * 2)
struct EdgeLayers { int count; EdgeLayer v[MAX_EDGE_LAYERS]; };

static void push_layer(EdgeLayers* out, int kind, int config, int variant,
                       uint8_t r, uint8_t g, uint8_t b) {
    if (out->count >= MAX_EDGE_LAYERS) return;
    EdgeLayer* l = &out->v[out->count++];
    l->kind = kind; l->config = config; l->variant = variant;
    l->r = r; l->g = g; l->b = b;
}

static void biome_edge_layers(const Tilemap* map, int x, int y, EdgeLayers* out) {
    out->count = 0;
    int mine = biome_at(map, x, y);
    if (mine < 0) return;
    EdgeFringe fr;
    biome_fringe(map, x, y, &fr);

    for (int i = 0; i < fr.count; i++) {
        int other = fr.biome[i], cfg = fr.config[i];
        const GroundBiome& o = s_biomes[other];

        // One of the pair draws its own border, so leave the join alone rather
        // than laying a second one over the top of it.
        if (biome_own_edges(mine) || biome_own_edges(other)) continue;

        if (!biome_hard_edge(mine) && !biome_hard_edge(other)) {
            push_layer(out, MASK_FRINGE, cfg, fr.variant, o.r, o.g, o.b);
            continue;
        }
        push_layer(out, MASK_FILL, cfg, fr.variant, o.r, o.g, o.b);

        // Shallows only where the liquid in question has them. Lava is a liquid
        // with no shore colour, so it takes the outline and nothing more.
        bool other_hard = biome_hard_edge(other);
        int shore_of = other_hard ? other : mine;
        if (biome_has_shore(shore_of)) {
            const GroundBiome& s = s_biomes[shore_of];
            push_layer(out, other_hard ? MASK_SHORE_OUT : MASK_SHORE_IN,
                       cfg, fr.variant, (uint8_t)s.sr, (uint8_t)s.sg, (uint8_t)s.sb);
        }
    }
}

// Paint them. Runs after the tile has drawn itself, so everything here goes
// over the top — the tile keeps its tufts.
static void draw_biome_edges(SDL_Renderer* renderer, const Tilemap* map, int x, int y,
                             int sx, int sy, int size) {
    EdgeLayers ls;
    biome_edge_layers(map, x, y, &ls);
    SDL_Rect dst = { sx, sy, size, size };

    for (int i = 0; i < ls.count; i++) {
        const EdgeLayer& l = ls.v[i];
        SDL_Texture* t = nullptr;
        switch (l.kind) {
            case MASK_FRINGE:    t = s_edge_tex[l.config][l.variant];      break;
            case MASK_FILL:      t = s_fill_tex[l.config][l.variant];      break;
            case MASK_SHORE_OUT: t = s_shore_out_tex[l.config][l.variant]; break;
            default:             t = s_shore_in_tex[l.config][l.variant]; break;
        }
        if (!t) continue;
        SDL_SetTextureColorMod(t, l.r, l.g, l.b);
        SDL_RenderCopy(renderer, t, NULL, &dst);
    }
}

// depth_pass=false: draw all tiles except depth-marked ones.
// depth_pass=true:  draw only depth-marked tiles (call after player_draw).
static void tilemap_draw_impl(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer,
                               bool depth_pass) {
    float z = cam->zoom;
    int draw_size = (int)(TILE_SIZE * z);
    if (draw_size < 1) draw_size = 1;

    int start_x = (int)(cam->x / TILE_SIZE);
    int start_y = (int)(cam->y / TILE_SIZE);
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
            bool is_depth = (map->depth_layer[y][x] != 0);
            int screen_x = (int)((x * TILE_SIZE - cam->x) * z);
            int screen_y = (int)((y * TILE_SIZE - cam->y) * z);

            // Helper: compute jitter offset for a tree tile
            auto tree_jox = [&](int tx, int ty2) -> int {
                auto jit = s_tile_jitter.find(tile_key(tx, ty2));
                if (jit == s_tile_jitter.end()) return 0;
                float elapsed = (float)((double)(SDL_GetPerformanceCounter() - jit->second)
                                        / SDL_GetPerformanceFrequency());
                return (int)(sinf(elapsed * 80.0f) * 4.0f * z);
            };

            // Helper: draw a 2-tile tree's canopy (top sprite) for the tile at (tx, ty2).
            // Canopy is rendered one tile above ty2 using dst_top.
            auto draw_tree_canopy = [&](int tx, int ty2, int sx, int sy) {
                uint32_t h = (uint32_t)(tx * 2654435761u ^ (uint32_t)ty2 * 40503u) & 3;
                bool is_snow = (map->tiles[ty2][tx] == TILE_SNOW);
                if (h == 0 && !is_snow) return; // solo tree — no canopy (snow trees are always 2-tile)
                int col;
                if (is_snow)      col = (h & 1) ? 19 : 18;
                else              col = (h == 3) ? 16 : 17;
                int jox = tree_jox(tx, ty2);
                SDL_Rect src_top = { col * 16, 0 * 16, 16, 16 };
                SDL_Rect dst_top = { sx + jox, sy, draw_size, draw_size };
                if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_top, &dst_top);
            };

            if (depth_pass) {
                // Depth pass: town tile only — grass already drawn in base pass, before player
                if (is_depth) blit_tile(renderer, map->tiles[y][x], screen_x, screen_y, draw_size);
                // Draw canopy for any 2-tile tree whose trunk is in the row below (y+1).
                if (y + 1 < MAP_HEIGHT && map->overlay[y+1][x] == TILE_TREE) {
                    draw_tree_canopy(x, y + 1, screen_x, screen_y);
                }
                if (y + 1 < MAP_HEIGHT && map->overlay[y+1][x] == TILE_DEAD_TREE) {
                    int jox = tree_jox(x, y+1);
                    SDL_Rect src_top = { 20 * 16, 0 * 16, 16, 16 };
                    SDL_Rect dst_top = { screen_x + jox, screen_y, draw_size, draw_size };
                    if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_top, &dst_top);
                }
                continue;
            }

            // Base pass: grass background drawn here (before player) for all town tiles
            {
                int tile_id = map->tiles[y][x];
                // A cliff draws as ground with its piece of the silhouette laid
                // over: the corners of that art are keyed out, and what belongs
                // behind them is the terrain the cliff stands in.
                int cliff_art = cliff_art_cell(x, y, tile_id);
                const GroundCover* cover = (cliff_art >= 0) ? cliff_under_cover(map, x, y)
                                                            : tile_cover(map, x, y);
                bool is_town = (tile_id >= TILE_TOWN0_BASE);
                if (cover)
                    blit_tile(renderer, cover_variant(map, x, y, cover), screen_x, screen_y, draw_size);
                else if (cliff_art < 0)
                    blit_tile(renderer, tile_id, screen_x, screen_y, draw_size);
                draw_biome_edges(renderer, map, x, y, screen_x, screen_y, draw_size);
                if (cliff_art >= 0)   blit_tile(renderer, cliff_art, screen_x, screen_y, draw_size);
                else if (is_town)     blit_tile(renderer, tile_id, screen_x, screen_y, draw_size);
            }
            if (is_depth) continue;

            // Draw overlay (trees, rocks, gold ore) on top
            int ov = map->overlay[y][x];
            if (ov == TILE_TREE) {
                // Each tree tile is fully independent.
                // Hash selects variant; snow tiles use a different sprite set (cols 18/19).
                uint32_t h = (uint32_t)(x * 2654435761u ^ (uint32_t)y * 40503u) & 3;
                bool is_snow = (map->tiles[y][x] == TILE_SNOW);
                int jox = tree_jox(x, y);
                int dx = screen_x + jox;

                if (is_snow) {
                    // Snow: trunk only — canopy drawn in depth pass
                    int col = (h & 1) ? 19 : 18;
                    SDL_Rect src_bot = { col * 16, 1 * 16, 16, 16 };
                    SDL_Rect dst_bot = { dx, screen_y, draw_size, draw_size };
                    if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_bot, &dst_bot);
                } else if (h == 0) {
                    // Solo tree: single tile, no canopy
                    SDL_Rect src = { 15 * 16, 1 * 16, 16, 16 };
                    SDL_Rect dst = { dx, screen_y, draw_size, draw_size };
                    if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src, &dst);
                } else {
                    // 2-tile tree: trunk only — canopy drawn in depth pass
                    int col = (h == 3) ? 16 : 17;
                    SDL_Rect src_bot = { col * 16, 1 * 16, 16, 16 };
                    SDL_Rect dst_bot = { dx, screen_y, draw_size, draw_size };
                    if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_bot, &dst_bot);
                }
            } else if (ov == TILE_DEAD_TREE) {
                // Always 2-tile tall. Trunk drawn here, canopy in depth pass above.
                int jox = tree_jox(x, y);
                SDL_Rect src_bot = { 20 * 16, 1 * 16, 16, 16 };
                SDL_Rect dst_bot = { screen_x + jox, screen_y, draw_size, draw_size };
                if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_bot, &dst_bot);
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

void tilemap_draw_base(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer, float) {
    tilemap_draw_impl(map, cam, renderer, false);
}

void tilemap_draw_depth(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer, float) {
    tilemap_draw_impl(map, cam, renderer, true);
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

    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
    draw_nes_panel(renderer, ox - 4, oy - 4, mw + 8, mh + 8);

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

    // dungeons — 3×3 red dot centered on entrance
    for (int i = 0; i < map->num_dungeon_entrances; i++) {
        const DungeonEntrance* e = &map->dungeon_entrances[i];
        int dx = ox + (e->x + 1) / step;
        int dy = oy + (e->y + 1) / step;
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
        SDL_Rect ddot = { dx - 1, dy - 1, 3, 3 };
        SDL_RenderFillRect(renderer, &ddot);
    }

    // Player — a flashing 5×5 square. It alternates between two bright colours
    // rather than blinking to nothing, so the marker never disappears on a map
    // you opened to find yourself, and the movement is what catches the eye.
    // Bigger and animated also tells it apart from the static white 4×4 castles.
    int px = ox + (int)(player_x / TILE_SIZE) / step;
    int py = oy + (int)(player_y / TILE_SIZE) / step;
    if ((SDL_GetTicks() / MINIMAP_FLASH_MS) & 1)
        SDL_SetRenderDrawColor(renderer, 0, 255, 255, 255);
    else
        SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect dot = { px - 2, py - 2, 5, 5 };
    SDL_RenderFillRect(renderer, &dot);

    // red 5×5 dot for cliff gradient peak (debug)
    //int peakdot_x = ox + (int)(map->cliff_peak_x) / step;
    //int peakdot_y = oy + (int)(map->cliff_peak_y) / step;
    //SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
    //SDL_Rect peak_dot = { peakdot_x - 2, peakdot_y - 2, 5, 5 };
    //SDL_RenderFillRect(renderer, &peak_dot);

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
    if (t == TILE_ROCK)      return 3;
    if (t == TILE_GOLD_ORE)  return 5;
    if (t == TILE_DEAD_TREE) return 3;
    if (t == TILE_TREE) {
        bool paired = (ty > 0 && map->overlay[ty-1][tx] == TILE_TREE);
        return paired ? 4 : 2;
    }
    return 0;
}

static bool tile_is_harvestable(int t) {
    return t == TILE_TREE || t == TILE_DEAD_TREE || t == TILE_ROCK || t == TILE_GOLD_ORE;
}

static HarvestTarget tile_target(int t) {
    if (t == TILE_TREE || t == TILE_DEAD_TREE) return HARVEST_TREE;
    if (t == TILE_ROCK)                        return HARVEST_ROCK;
    if (t == TILE_GOLD_ORE)                    return HARVEST_ORE;
    return HARVEST_OTHER;
}

static int tile_award(int t) {
    if (t == TILE_TREE || t == TILE_DEAD_TREE) return (int)RESOURCE_TREE;
    if (t == TILE_ROCK)                        return (int)RESOURCE_ROCK;
    if (t == TILE_GOLD_ORE)                    return (int)RESOURCE_GOLD;
    return -1;
}

// Strike one tile. Returns 1 if it was destroyed.
static int tilemap_strike(Tilemap* map, int tx, int ty, WeaponType weapon, HarvestResult* out) {
    int t = map->overlay[ty][tx];
    uint32_t key = tile_key(tx, ty);

    auto it = s_tile_hp.find(key);
    int hp = (it == s_tile_hp.end()) ? tile_max_hp(map, tx, ty) : it->second;
    hp -= weapon_harvest_damage(weapon, tile_target(t));

    float cx = (tx + 0.5f) * TILE_SIZE;
    float cy = (ty + 0.5f) * TILE_SIZE;

    if (hp <= 0) {
        s_tile_hp.erase(key);
        s_tile_jitter.erase(key);
        map->overlay[ty][tx] = 0;
        harvest_add(out, cx, cy, tile_award(t), 1);
        return 1;
    }

    s_tile_hp[key] = hp;
    s_tile_jitter[key] = SDL_GetPerformanceCounter();
    harvest_add(out, cx, cy, tile_award(t), 0);
    return 0;
}

int tilemap_sweep(Tilemap* map, float px, float py, float radius,
                  float start_ang, float rel0, float rel1,
                  WeaponType weapon, HarvestResult* out) {
    int r = (int)radius;
    int tx0 = (int)((px - r) / TILE_SIZE); if (tx0 < 0) tx0 = 0;
    int ty0 = (int)((py - r) / TILE_SIZE); if (ty0 < 0) ty0 = 0;
    int tx1 = (int)((px + r) / TILE_SIZE); if (tx1 >= MAP_WIDTH)  tx1 = MAP_WIDTH  - 1;
    int ty1 = (int)((py + r) / TILE_SIZE); if (ty1 >= MAP_HEIGHT) ty1 = MAP_HEIGHT - 1;

    int struck = 0;
    for (int ty = ty0; ty <= ty1; ty++) {
        for (int tx = tx0; tx <= tx1; tx++) {
            if (!tile_is_harvestable(map->overlay[ty][tx])) continue;
            float cx = (tx + 0.5f) * TILE_SIZE;
            float cy = (ty + 0.5f) * TILE_SIZE;
            float dx = cx - px, dy = cy - py;
            if (dx*dx + dy*dy > radius * radius) continue;
            float rel = sweep_relative_angle(start_ang, dx, dy);
            if (rel < rel0 || rel >= rel1) continue;
            tilemap_strike(map, tx, ty, weapon, out);
            struck++;
        }
    }
    return struck;
}

// Tile bounds of the box that could contain anything within `reach` of (px,py).
static void thrust_tile_bounds(float px, float py, float reach,
                               int* tx0, int* ty0, int* tx1, int* ty1) {
    int r = (int)reach + TILE_SIZE;
    *tx0 = (int)((px - r) / TILE_SIZE); if (*tx0 < 0) *tx0 = 0;
    *ty0 = (int)((py - r) / TILE_SIZE); if (*ty0 < 0) *ty0 = 0;
    *tx1 = (int)((px + r) / TILE_SIZE); if (*tx1 >= MAP_WIDTH)  *tx1 = MAP_WIDTH  - 1;
    *ty1 = (int)((py + r) / TILE_SIZE); if (*ty1 >= MAP_HEIGHT) *ty1 = MAP_HEIGHT - 1;
}

float tilemap_first_along(const Tilemap* map, float px, float py,
                          float angle, float half_width, float max_reach) {
    int tx0, ty0, tx1, ty1;
    thrust_tile_bounds(px, py, max_reach, &tx0, &ty0, &tx1, &ty1);

    float best = -1.0f;
    for (int ty = ty0; ty <= ty1; ty++) {
        for (int tx = tx0; tx <= tx1; tx++) {
            if (!tile_is_harvestable(map->overlay[ty][tx])) continue;
            float cx = (tx + 0.5f) * TILE_SIZE;
            float cy = (ty + 0.5f) * TILE_SIZE;
            float along, side;
            thrust_project(angle, cx - px, cy - py, &along, &side);
            if (along < 0.0f || along > max_reach) continue;
            if (side < -half_width || side > half_width) continue;
            if (best < 0.0f || along < best) best = along;
        }
    }
    return best;
}

int tilemap_thrust(Tilemap* map, float px, float py, float angle,
                   float half_width, float from, float to,
                   WeaponType weapon, HarvestResult* out) {
    int tx0, ty0, tx1, ty1;
    thrust_tile_bounds(px, py, to, &tx0, &ty0, &tx1, &ty1);

    int struck = 0;
    for (int ty = ty0; ty <= ty1; ty++) {
        for (int tx = tx0; tx <= tx1; tx++) {
            if (!tile_is_harvestable(map->overlay[ty][tx])) continue;
            float cx = (tx + 0.5f) * TILE_SIZE;
            float cy = (ty + 0.5f) * TILE_SIZE;
            float along, side;
            thrust_project(angle, cx - px, cy - py, &along, &side);
            if (along < from || along >= to) continue;
            if (side < -half_width || side > half_width) continue;
            tilemap_strike(map, tx, ty, weapon, out);
            struck++;
        }
    }
    return struck;
}

int tilemap_strike_point(Tilemap* map, float x, float y,
                         WeaponType weapon, HarvestResult* out) {
    int tx = (int)(x / TILE_SIZE);
    int ty = (int)(y / TILE_SIZE);
    if (tx < 0 || tx >= MAP_WIDTH || ty < 0 || ty >= MAP_HEIGHT) return 0;
    if (!tile_is_harvestable(map->overlay[ty][tx])) return 0;
    tilemap_strike(map, tx, ty, weapon, out);
    return 1;
}

int tilemap_try_hit(Tilemap* map, float px, float py, int range,
                    WeaponType weapon, HarvestResult* out) {
    int tx0 = (int)((px - range) / TILE_SIZE); if (tx0 < 0) tx0 = 0;
    int ty0 = (int)((py - range) / TILE_SIZE); if (ty0 < 0) ty0 = 0;
    int tx1 = (int)((px + range) / TILE_SIZE); if (tx1 >= MAP_WIDTH)  tx1 = MAP_WIDTH  - 1;
    int ty1 = (int)((py + range) / TILE_SIZE); if (ty1 >= MAP_HEIGHT) ty1 = MAP_HEIGHT - 1;

    // A sweeping weapon takes everything in the box; anything else takes only
    // the nearest tile, which is the original single-target behaviour.
    if (weapon_sweeps(weapon)) {
        int struck = 0;
        for (int ty = ty0; ty <= ty1; ty++) {
            for (int tx = tx0; tx <= tx1; tx++) {
                if (!tile_is_harvestable(map->overlay[ty][tx])) continue;
                tilemap_strike(map, tx, ty, weapon, out);
                struck++;
            }
        }
        return struck;
    }

    float best_dist2 = (float)(range * range) * 2.0f + 1.0f;
    int best_tx = -1, best_ty = -1;
    for (int ty = ty0; ty <= ty1; ty++) {
        for (int tx = tx0; tx <= tx1; tx++) {
            if (!tile_is_harvestable(map->overlay[ty][tx])) continue;
            float dx = (tx + 0.5f) * TILE_SIZE - px;
            float dy = (ty + 0.5f) * TILE_SIZE - py;
            float d2 = dx*dx + dy*dy;
            if (d2 < best_dist2) { best_dist2 = d2; best_tx = tx; best_ty = ty; }
        }
    }
    if (best_tx < 0) return 0;

    tilemap_strike(map, best_tx, best_ty, weapon, out);
    return 1;
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
        case TILE_WASTE_TRAIL:
        case TILE_WASTE_BRIDGE:
        case TILE_MEADOW:
        // Elevated terrain top surfaces — walkable plateau; cliff FACE tiles are not listed here
        case TILE_CLIFF:        case TILE_CLIFF_2:      case TILE_CLIFF_3:
        case TILE_CLIFF_4:      case TILE_CLIFF_5:
        case TILE_CLIFF_SNOW_1: case TILE_CLIFF_SNOW_2: case TILE_CLIFF_SNOW_3:
        case TILE_CLIFF_SNOW_4: case TILE_CLIFF_SNOW_5:
        case TILE_CLIFF_WASTE_1: case TILE_CLIFF_WASTE_2: case TILE_CLIFF_WASTE_3:
        case TILE_CLIFF_WASTE_4: case TILE_CLIFF_WASTE_5:
        // Town/village/castle footprints — part of the overworld, fully walkable
        case TILE_BLUEPRINT:
        case TILE_VILLAGE_PLACEHOLDER:
        case TILE_CASTLE_PLACEHOLDER:
        // Dungeon entrance tiles — player must be able to walk onto them
        case TILE_DUNGEON:
        case TILE_DUNGEON_CAVE:
        case TILE_DUNGEON_RUINS:
        case TILE_DUNGEON_GRAVEYARD_SM:
        case TILE_DUNGEON_GRAVEYARD_LG:
        case TILE_DUNGEON_OASIS:
        case TILE_DUNGEON_PYRAMID:
        case TILE_DUNGEON_STONEHENGE:
        case TILE_DUNGEON_LARGE_TREE:
            return true;
        default:
            // Town/overworld sheet tiles are walkable unless the editor marked them as solid
            if ((map->tiles[tile_y][tile_x] >= TILE_TOWN0_BASE &&
                 map->tiles[tile_y][tile_x] <= TILE_TOWN0_END) ||
                (map->tiles[tile_y][tile_x] >= TILE_OW0_BASE &&
                 map->tiles[tile_y][tile_x] <= TILE_OW0_END))
                return map->coll[tile_y][tile_x] == 0;
            return false;
    }
}

// Which biome the smoothed field hands this pixel to. Only the hard-edged
// liquid treatment counts: a stippled ground fringe is two grounds mixing and
// moves no line, so it owns nothing. Matches the order the layers paint in, so
// the answer here is the colour on screen.
static int field_owner_at(const Tilemap* map, int tx, int ty, float px, float py) {
    int mine = biome_at(map, tx, ty);
    if (mine < 0) return -1;
    EdgeFringe fr;
    biome_fringe(map, tx, ty, &fr);
    if (fr.count == 0) return mine;

    int ax = (int)((px - tx * TILE_SIZE) * 16.0f / TILE_SIZE);
    int ay = (int)((py - ty * TILE_SIZE) * 16.0f / TILE_SIZE);
    if (ax < 0) ax = 0; else if (ax > 15) ax = 15;
    if (ay < 0) ay = 0; else if (ay > 15) ay = 15;

    // Half coverage flat — deliberately not shore_threshold's jittered line.
    // The roughness is there to make the bank look worn, and a hitbox that
    // followed it would catch on bumps too small to see. The two therefore
    // disagree, but only ever inside the jitter band: under a pixel, and always
    // hugging the drawn line rather than wandering off it.
    int owner = mine;
    for (int i = 0; i < fr.count; i++) {
        if (!biome_hard_edge(mine) && !biome_hard_edge(fr.biome[i])) continue;
        if (edge_coverage(fr.config[i], ax, ay) >= 0.5f) owner = fr.biome[i];
    }
    return owner;
}

bool tilemap_pixel_solid(const void* vmap, float px, float py) {
    const Tilemap* map = static_cast<const Tilemap*>(vmap);
    int tx = (int)(px / TILE_SIZE);
    int ty = (int)(py / TILE_SIZE);
    if (!in_bounds(tx, ty)) return true;

    // Solid ground cover — water and lava — is drawn along the smoothed field
    // rather than the tile grid, so their collision reads that same field.
    // Without this the edge you can see and the edge you can walk to disagree
    // by up to half a tile wherever the outline rounds a corner, which is very
    // visible against a hard edge. Everything else keeps the tile-grid answer.
    // A bridge is the exception, and has to be tested before the field: it is
    // a deck laid over lava, so lava reaches into it from every side and the
    // field would hand most of its pixels to something solid. The deck is
    // walkable to its tile edges — that is the whole point of it — and it is
    // the one tile the drawn edge is not the walkable one.
    if (map->tiles[ty][tx] == TILE_WASTE_BRIDGE) return false;

    int mine  = biome_at(map, tx, ty);
    int owner = field_owner_at(map, tx, ty, px, py);
    bool mine_is_solid = biome_solid(mine);

    if (biome_solid(owner)) return true;
    // A solid tile whose pixel the field gave to walkable ground is standable; asking
    // tilemap_is_walkable here would call the whole tile solid and undo that.
    if (!mine_is_solid && !tilemap_is_walkable(map, tx, ty)) return true;

    // Trees, rocks, and gold ore live in the overlay — they're also solid.
    int ov = map->overlay[ty][tx];
    return ov == TILE_TREE || ov == TILE_DEAD_TREE || ov == TILE_ROCK || ov == TILE_GOLD_ORE;
}

void tilemap_spawn_graveyard_nodes(Tilemap* map, ResourceNodeList* resources,
                                   int entrance_idx, unsigned int seed) {
    DungeonEntrance* e = &map->dungeon_entrances[entrance_idx];
    if (e->type != DUNGEON_ENT_GRAVEYARD_SM || e->gravestones_spawned) return;
    e->gravestones_spawned = 1;

    // Per-entrance RNG so every graveyard has a unique layout
    unsigned int rng = seed
        ^ ((unsigned int)e->x * 73856093u)
        ^ ((unsigned int)e->y * 19349663u);

    // Count: 5–10 gravestones
    rng = rng * 1664525u + 1013904223u;
    int count = 5 + (int)((rng >> 16) % 6);

    // The hidden entrance gravestone sits directly on the entrance tile.
    // Pixel position: top-left of the tile.
    resource_nodes_add_gravestone(resources,
        (float)(e->x * TILE_SIZE), (float)(e->y * TILE_SIZE),
        1, TILE_DUNGEON_GRAVEYARD_SM, e->x, e->y);

    // Scatter the remaining gravestones in a ~3-tile radius around the entrance.
    int placed = 1;
    const int RADIUS = 3;
    for (int attempt = 0; attempt < 80 && placed < count; attempt++) {
        rng = rng * 1664525u + 1013904223u;
        int dx = (int)((rng >> 16) % (unsigned)(RADIUS * 2 + 1)) - RADIUS;
        rng = rng * 1664525u + 1013904223u;
        int dy = (int)((rng >> 16) % (unsigned)(RADIUS * 2 + 1)) - RADIUS;
        if (dx == 0 && dy == 0) continue; // entrance position is already taken

        int tx = e->x + dx, ty = e->y + dy;
        if (!tilemap_is_walkable(map, tx, ty)) continue;
        // Same bank clearance the overlays get — a gravestone standing in
        // the shallows reads as a mistake rather than as a graveyard.
        if (!overlay_site_dry(map, tx, ty)) continue;
        if (tile_id_is_trail(map->tiles[ty][tx])) continue;

        // Reject if another gravestone is already at this tile
        float wx = (float)(tx * TILE_SIZE), wy = (float)(ty * TILE_SIZE);
        bool conflict = false;
        for (int i = 0; i < resources->count; i++) {
            const ResourceNode* n = &resources->nodes[i];
            if (n->type != RESOURCE_GRAVESTONE) continue;
            if (fabsf(n->x - wx) < (float)TILE_SIZE * 0.5f &&
                fabsf(n->y - wy) < (float)TILE_SIZE * 0.5f) {
                conflict = true;
                break;
            }
        }
        if (conflict) continue;

        resource_nodes_add_gravestone(resources, wx, wy, 0, 0, -1, -1);
        placed++;
    }
}

void tilemap_spawn_graveyard_lg_nodes(Tilemap* map, ResourceNodeList* resources,
                                      int entrance_idx, unsigned int seed) {
    DungeonEntrance* e = &map->dungeon_entrances[entrance_idx];
    if (e->type != DUNGEON_ENT_GRAVEYARD_LG || e->gravestones_spawned) return;
    e->gravestones_spawned = 1;

    unsigned int rng = seed
        ^ ((unsigned int)e->x * 73856093u)
        ^ ((unsigned int)e->y * 19349663u);

    // 36 candidate slots in 6 rows × 6 cols.
    // Each row shifts 2 tiles left per 2-tile step south, tracking the
    // parallelogram walls.  Columns are centred on the mausoleum (ex+0.5).
    static const int slots[36][2] = {
        { -8, 2}, {-6, 2}, {-4, 2}, {-2, 2}, { 0, 2}, { 2, 2},
        {-10, 4}, {-8, 4}, {-6, 4}, {-4, 4}, {-2, 4}, { 0, 4},
        {-12, 6}, {-10, 6}, {-8, 6}, {-6, 6}, {-4, 6}, {-2, 6},
        {-14, 8}, {-12, 8}, {-10, 8}, {-8, 8}, {-6, 8}, {-4, 8},
        {-16,10}, {-14,10}, {-12,10}, {-10,10}, {-8,10}, {-6,10},
        {-18,12}, {-16,12}, {-14,12}, {-12,12}, {-10,12}, {-8,12},
    };

    // Count: 18–28
    rng = rng * 1664525u + 1013904223u;
    int count = 18 + (int)((rng >> 16) % 11);

    // Fisher-Yates shuffle of slot indices so the selection is random
    int order[36];
    for (int i = 0; i < 36; i++) order[i] = i;
    for (int i = 35; i > 0; i--) {
        rng = rng * 1664525u + 1013904223u;
        int j = (int)((rng >> 16) % (unsigned)(i + 1));
        int tmp = order[i]; order[i] = order[j]; order[j] = tmp;
    }

    for (int i = 0; i < count; i++) {
        int dx = slots[order[i]][0];
        int dy = slots[order[i]][1];
        int tx = e->x + dx, ty = e->y + dy;
        if (!tilemap_is_walkable(map, tx, ty)) continue;
        // Same bank clearance the overlays get — a gravestone standing in
        // the shallows reads as a mistake rather than as a graveyard.
        if (!overlay_site_dry(map, tx, ty)) continue;
        if (tile_id_is_trail(map->tiles[ty][tx])) continue;
        resource_nodes_add_gravestone(resources,
            (float)(tx * TILE_SIZE), (float)(ty * TILE_SIZE),
            0, 0, -1, -1);
    }
}
