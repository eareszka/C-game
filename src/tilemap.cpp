#include "fc_palette.h"
#include "tilemap.h"
#include "dungeon_kinds.h"
#include "dungeon.h"         // material_min_difficulty, for the guarantee pass
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
// Reset at every route_network call, so after generation these describe the
// last network routed -- the roads. How many places were asked for, and how
// many of them had ground close enough to start a route from.
int s_route_nodes = 0, s_route_anchors = 0, s_route_lone = 0;
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
    { 92,  74,  44,  150, 124,  80, glyph_path       }, // TILE_ROAD           (82)
    { 78,  62,  40,  128, 104,  70, glyph_path       }, // TILE_ROAD_BRIDGE    (83)
};

static const int NUM_TILE_STYLES = (int)(sizeof(tile_styles) / sizeof(tile_styles[0]));

// Twenty tiles of clearance around every river and sea tile, computed once
// after rivers are placed and shared between phase1 and phase2. The cliff pass
// reads it to keep cliffs off the water; the stream, pond, lava and trail
// passes read it to keep their features off the water too. It says NOTHING
// about cliffs. It was called cliff_blocked for years, and two passes took the
// name at its word and used it as the cliff mask -- which is how lava pools and
// trails came to be laid under the cliff faces. The question "is a wall drawn
// over this tile" is tilemap_face_at().
static bool  water_keepout[MAP_HEIGHT][MAP_WIDTH];
// Within CLIFF_NEAR tiles of any cliff: a plateau top or a drawn face. Built
// once the cliffs are placed (build_cliff_near), read by the stream brush so a
// lava pool or a pond keeps a strip of open ground between itself and the
// rock. Lava laid hard against a plateau's rim reads, from above, as lava on
// the plateau -- the rim art is the edge seen from above, and a pool touching
// it looks like it spills over it.
static uint8_t s_cliff_near[MAP_HEIGHT][MAP_WIDTH];
static const int CLIFF_NEAR = 2;
// Snow dilated by the biome fixup's reach: whether a row has snow within
// SNOW_BUFFER columns, before the second axis is folded in. Map-sized and it
// does not outlive the pass that fills it, but generation runs once and off the
// main thread, so it lives here rather than on a stack that has to carry it —
// the same reason as the cliff grids above.
static unsigned char s_biome_near[MAP_HEIGHT][MAP_WIDTH];
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
static const int TILE_CACHE_SIZE = 84; // TILE_ROAD_BRIDGE + 1
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
// The cave art darkened by dither for what lies outside the player's view.
static SDL_Texture* s_town_dim_tex       = nullptr;
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

// Inside the array. Only for the passes that walk the whole map, or that mean
// the array's edge and not the world's; anything asking after a neighbour or
// an offset goes through in_world() below, which knows two of the edges join.
static bool in_bounds(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

// Which axis joins, as phase 1 chose it. A file static beside the map's own
// field because the drawing and collision helpers are static and take no map,
// and the tools that link this file build one world at a time.
static int s_wrap_axis = WRAP_X;

int wrap_x(int x) {
    if (s_wrap_axis != WRAP_X) return x;
    x %= MAP_WIDTH;
    return x < 0 ? x + MAP_WIDTH : x;
}
int wrap_y(int y) {
    if (s_wrap_axis != WRAP_Y) return y;
    y %= MAP_HEIGHT;
    return y < 0 ? y + MAP_HEIGHT : y;
}
bool in_world(int* x, int* y) {
    if (s_wrap_axis == WRAP_X) {
        *x = wrap_x(*x);
        return *y >= 0 && *y < MAP_HEIGHT;
    }
    *y = wrap_y(*y);
    return *x >= 0 && *x < MAP_WIDTH;
}
int wrap_dx(int dx) {
    if (s_wrap_axis != WRAP_X) return dx;
    dx %= MAP_WIDTH;
    if (dx >  MAP_WIDTH / 2) dx -= MAP_WIDTH;
    if (dx <= -MAP_WIDTH / 2) dx += MAP_WIDTH;
    return dx;
}
int wrap_dy(int dy) {
    if (s_wrap_axis != WRAP_Y) return dy;
    dy %= MAP_HEIGHT;
    if (dy >  MAP_HEIGHT / 2) dy -= MAP_HEIGHT;
    if (dy <= -MAP_HEIGHT / 2) dy += MAP_HEIGHT;
    return dy;
}
float wrap_dpx(float dx) {
    if (s_wrap_axis != WRAP_X) return dx;
    const float W = (float)MAP_WIDTH * TILE_SIZE;
    dx = fmodf(dx, W);
    if (dx >  W * 0.5f) dx -= W;
    if (dx <= -W * 0.5f) dx += W;
    return dx;
}
float wrap_dpy(float dy) {
    if (s_wrap_axis != WRAP_Y) return dy;
    const float H = (float)MAP_HEIGHT * TILE_SIZE;
    dy = fmodf(dy, H);
    if (dy >  H * 0.5f) dy -= H;
    if (dy <= -H * 0.5f) dy += H;
    return dy;
}
float wrap_px(float px) {
    if (s_wrap_axis != WRAP_X) return px;
    const float W = (float)MAP_WIDTH * TILE_SIZE;
    px = fmodf(px, W);
    return px < 0.0f ? px + W : px;
}
float wrap_py(float py) {
    if (s_wrap_axis != WRAP_Y) return py;
    const float H = (float)MAP_HEIGHT * TILE_SIZE;
    py = fmodf(py, H);
    return py < 0.0f ? py + H : py;
}
static inline bool wrapx() { return s_wrap_axis == WRAP_X; }
static inline bool wrapy() { return s_wrap_axis == WRAP_Y; }

// A margin kept off the edges of the map along one axis: as given on the
// hard-border axis, none on the joined one, where the edge is only the seam and
// anything may stand beside it. A footprint still may not straddle the seam --
// the arrays are canonical, and every stamp writes its rectangle straight in --
// so these margins are the whole of the rule on both axes: a footprint starting
// at or after the low margin and ending at or before the high one.
static inline int margin_x(int m) { return wrapx() ? 0 : m; }
static inline int margin_y(int m) { return wrapy() ? 0 : m; }
// A random start for a footprint `w` long on an axis `size` long, keeping
// `m` off both ends where that axis has ends.
static inline int roll_span(unsigned int r, int size, int w, int m) {
    return m + (int)(r % (unsigned)(size - w - 2 * m + 1));
}

// One step of a marcher along an axis. On the joined axis it goes through
// the seam; on the other it reports having left the world. The secondary
// axis of a marcher is held off the border row on the hard axis, as it
// always was, and simply wraps on the joined one.
static bool march_primary(int* v, int size, bool wraps) {
    if (!wraps) return *v >= 0 && *v < size;
    *v %= size;
    if (*v < 0) *v += size;
    return true;
}
static void march_secondary(int* v, int size, bool wraps) {
    if (wraps) { *v %= size; if (*v < 0) *v += size; return; }
    if (*v < 1)        *v = 1;
    if (*v >= size - 1) *v = size - 2;
}

// Generation tracing. Worldgen runs two dozen passes over the whole map, so
// when a shape in the finished world looks wrong there is no reading your way
// back to which pass made it. Defining GEN_TRACE lets a probe snapshot the grid
// at every stage boundary and diff consecutive pairs; without it this compiles
// to nothing and the shipping build is unchanged.
#ifdef GEN_TRACE
void gen_trace_stage(const Tilemap* map, const char* stage);
#define GEN_STAGE(map, name) gen_trace_stage((map), (name))
// The same arrangement for the coastal town's shore search: it reports what it
// rejected and why, so a probe can tell a world with no usable coast from a
// filter throwing away a coast that was there. See ShoreTally in tilemap.h.
void gen_trace_shore(const ShoreTally* tally);
#define GEN_SHORE(tally) gen_trace_shore(&(tally))
#else
#define GEN_STAGE(map, name) ((void)0)
#define GEN_SHORE(tally)     ((void)0)
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
            if (in_world(&nx, &ny) && tile_id_is_liquid(map->tiles[ny][nx])) return false;
        }
    return true;
}

// A track, or the deck that carries it over a gap. Nothing destroyable stands
// on either: the overlays are cleared as the track is laid, and the nodes
// placed later — gravestones, which are scattered when the player first comes
// near a graveyard — ask this before choosing a tile.
//
// Two layers to ask, because a track is worn over ground that is still there
// while a deck replaces the surface outright.
static inline bool tile_is_route(const Tilemap* map, int x, int y) {
    if (map->route[y][x]) return true;
    int t = map->tiles[y][x];
    return t == TILE_WASTE_BRIDGE || t == TILE_ROAD_BRIDGE;
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
            if (dry && (ov == TILE_TREE || ov == TILE_DEAD_TREE))
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


// Paints a filled circle brush at (ix, iy), skipping the guard zone.
static void paint_river_brush(Tilemap* map, int ix, int iy, int brush_r,
                              int guard_cx, int guard_cy, int guard_r)
{
    for (int by = -brush_r; by <= brush_r; by++) {
        for (int bx = -brush_r; bx <= brush_r; bx++) {
            if (bx*bx + by*by > brush_r*brush_r) continue;
            int px = ix + bx, py = iy + by;
            if (!in_world(&px, &py)) continue;
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
            if (!march_primary(&rx, MAP_WIDTH, wrapx())) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            march_secondary(&ry, MAP_HEIGHT, wrapy());
        } else {
            ry += sign_y;
            if (!march_primary(&ry, MAP_HEIGHT, wrapy())) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            march_secondary(&rx, MAP_WIDTH, wrapx());
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

// Generic short-stream brush: only overwrites `target` tile, keeps off the
// water keep-out, and keeps CLIFF_NEAR tiles clear of any cliff. A face is
// drawn over ordinary ground, so the tile beneath it still matches `target`;
// painting it put a pool under the wall, showing through the band's ragged
// lower edge as lava (or water) lying in the cliff, and a pool laid against a
// rim looked poured over the plateau. Every stream, pool and pond goes through
// here -- march_wander paints with this brush -- so this is the one place.
static void paint_stream_brush(Tilemap* map, int ix, int iy, int brush_r,
                                int guard_cx, int guard_cy, int guard_r,
                                int target, int place)
{
    for (int by = -brush_r; by <= brush_r; by++) {
        for (int bx = -brush_r; bx <= brush_r; bx++) {
            if (bx*bx + by*by > brush_r*brush_r) continue;
            int px = ix+bx, py = iy+by;
            if (!in_world(&px, &py)) continue;
            if (abs(px-guard_cx) <= guard_r && abs(py-guard_cy) <= guard_r) continue;
            if (water_keepout[py][px]) continue;
            if (s_cliff_near[py][px]) continue;
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
        if (wrapx()) { if (fx < 0.0f) fx += MAP_WIDTH;  else if (fx >= MAP_WIDTH)  fx -= MAP_WIDTH;  }
        if (wrapy()) { if (fy < 0.0f) fy += MAP_HEIGHT; else if (fy >= MAP_HEIGHT) fy -= MAP_HEIGHT; }
        int ix = (int)fx, iy = (int)fy;
        if (!wrapx() && (ix < 1 || ix >= MAP_WIDTH  - 1)) break;
        if (!wrapy() && (iy < 1 || iy >= MAP_HEIGHT - 1)) break;
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
            if (!march_primary(&rx, MAP_WIDTH, wrapx())) break;
            acc += ratio; int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            march_secondary(&ry, MAP_HEIGHT, wrapy());
        } else {
            ry += sign_y;
            if (!march_primary(&ry, MAP_HEIGHT, wrapy())) break;
            acc += ratio; int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            march_secondary(&rx, MAP_WIDTH, wrapx());
        }
        paint_stream_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r, target, place);
        // Only where the stream actually laid something down: a point out on
        // bare grass is no use as a junction.
        if (trace && (steps % 10) == 0 && in_bounds(rx, ry) && map->tiles[ry][rx] == place)
            trace->push_back({ rx, ry });
    }
}

// March the ocean river as a single meandering channel, then fan it into
// 2-4 branches (delta) as it nears the ocean coast, whichever edge that is.
static void generate_delta_river(Tilemap* map, int sx, int sy,
                                  float dir_x, float dir_y,
                                  unsigned int seed, int ocean_side,
                                  int guard_cx, int guard_cy, int guard_r,
                                  int brush_r, int jitter_range)
{
    const float PI = 3.14159265f;
    unsigned int s = seed;

    // How far short of the ocean edge to begin fanning -- random per seed,
    // well before the coast. It used to be a column, which only meant
    // anything with the ocean to the west; the other three sides got a
    // trunk that ran into the sea without ever fanning.
    s = s * 1664525u + 1013904223u;
    int delta_depth = 600 + (int)((s >> 16) % 400); // 600..999

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
            if (!march_primary(&rx, MAP_WIDTH, wrapx())) { rx -= sign_x; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            march_secondary(&ry, MAP_HEIGHT, wrapy());
        } else {
            ry += sign_y;
            if (!march_primary(&ry, MAP_HEIGHT, wrapy())) { ry -= sign_y; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            march_secondary(&rx, MAP_WIDTH, wrapx());
        }

        paint_river_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r);

        int to_sea;
        switch (ocean_side) {
            case 0:  to_sea = rx;                  break;
            case 1:  to_sea = MAP_WIDTH  - 1 - rx; break;
            case 2:  to_sea = ry;                  break;
            default: to_sea = MAP_HEIGHT - 1 - ry; break;
        }
        if (to_sea <= delta_depth) break; // trunk done, start fanning
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

// The south wall was once the only part of a plateau the art painted — its other
// three sides a rim on the plateau's own edge tiles — so this id was the whole
// question of "is there rock here", and the passes that run after the wall is
// laid have to leave it alone.
static inline bool cliff_is_south_face(int t) {
    return t >= TILE_CLIFF_EDGE_1 && t <= TILE_CLIFF_EDGE_5;
}

// The elevation the contour asks for, before it is cleaned up, and one scratch
// grid for the cleanup. Both are the size of the map and neither outlives
// generation, but generation runs once and off the main thread, so they live
// here rather than on a stack that has to carry them.
static unsigned char s_cliff_elev[MAP_HEIGHT][MAP_WIDTH];

// Fill s_cliff_near: every tile within CLIFF_NEAR (Chebyshev) of a plateau top
// or a drawn face. Two separable passes rather than a 5x5 stamp per tile.
static bool cliff_bars_overlay(int x, int y);
static void build_cliff_near(void) {
    static uint8_t row_hit[MAP_HEIGHT][MAP_WIDTH];
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            uint8_t hit = 0;
            for (int dx = -CLIFF_NEAR; dx <= CLIFF_NEAR && !hit; dx++) {
                int nx = x + dx, ny = y;
                if (!in_world(&nx, &ny)) continue;
                if (s_cliff_elev[ny][nx] || tilemap_face_at(nx, ny)) hit = 1;
            }
            row_hit[y][x] = hit;
        }
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++) {
            uint8_t hit = 0;
            for (int dy = -CLIFF_NEAR; dy <= CLIFF_NEAR && !hit; dy++) {
                int nx = x, ny = y + dy;
                if (!in_world(&nx, &ny)) continue;
                if (row_hit[ny][nx]) hit = 1;
            }
            s_cliff_near[y][x] = hit;
        }
}
static unsigned char s_cliff_scratch[MAP_HEIGHT][MAP_WIDTH];
// The cave pass, counted: mountains walked, those with a sealed top (the
// only ones that roll), those that got a cave. For the census.
static int s_cave_seen = 0, s_cave_sealed = 0, s_cave_placed = 0;
static long s_cave_sealed_tiles = 0, s_cave_placed_tiles = 0;   // their raised tiles, for the mean size
// Which levels' walls close a tile, one bit per level: every tile an island
// put rock or line on. Worked out once, when the world is built, because
// every later pass and every frame drawn wants it.
//
// The top bit says something else, on the tiles of a plateau rather than its
// walls: the feet cannot walk up here from the flat. A plateau is closed at
// tile level by construction, but the ground is closed per pixel, and where a
// flank's foot meets the next lobe's back line inside one wall tile there is
// often a way through. Those stay as they are -- a way up on foot -- and the
// library says of each landform whether it has one (Island::open). The cave
// pass reads the bit: a cave carries the player between elevations, and a
// mountain whose every top can be walked onto needs none. Every reader of
// the wall bits masks them out, so the top bit rides along untouched.
static unsigned char s_cliff_face[MAP_HEIGHT][MAP_WIDTH];
static const unsigned char CLIFF_FACE_SEALED = 1 << 7;

// Where the highland lies: a field whose level sets put the islands where a
// range would be. It orders the placement below and nothing else -- no
// outline is cut from it any more. The grids divide the map so the lattice
// closes on the joined axis and the field is the same continuous thing
// across the seam as anywhere else.
static const int CLIFF_HIGH_G   = 60;   // how far apart the plateau country lies
static const int CLIFF_ROUGH_G  = 10;   // and the scale of the bites out of its edge
static const float CLIFF_ROUGH_AMP = 1.00f;  // how deep they bite
static const int CLIFF_GRAIN_G  = 6;
static_assert(MAP_WIDTH % CLIFF_HIGH_G == 0 && MAP_WIDTH % CLIFF_ROUGH_G == 0 && MAP_WIDTH % CLIFF_GRAIN_G == 0 &&
              MAP_HEIGHT % CLIFF_HIGH_G == 0 && MAP_HEIGHT % CLIFF_ROUGH_G == 0 && MAP_HEIGHT % CLIFF_GRAIN_G == 0,
              "the cliff noise grids must divide the map, or the field tears at the seam");
static const float CLIFF_GRAIN_AMP = 0.30f;
static const int CLIFF_LEVELS   = 3;    // besides the ground itself
static const float CLIFF_PEAK_LIFT = 9000.0f; // how much the range gathers to its peak

// How much of the eligible ground each level covers. Each is a good deal
// smaller than the one below, so the levels read as a hill rather than as a
// wedding cake, and the top one is rare enough to be worth climbing.
static const float CLIFF_LEVEL_PCT[CLIFF_LEVELS + 1] = { 0.0f, 0.22f, 0.10f, 0.035f };

// How many cave systems a world should hold: the cave rows of DUNGEON_KINDS
// add up to about this many. See the cave pass in the dungeon placement.
static const int CAVE_SYSTEMS_TARGET = 360;

// The elevated ground is a library of islands, stamped whole.
//
// Every one of them is made of the sprites of Mother 1's three island
// drawings (art/cliffs/islands/), and made of them the way she made the
// drawings: every 2x2 block of sprites in an island is a block one of the
// drawings contains, so every sprite, every seam and every corner is hers,
// pixel for pixel. The shapes are new -- tools/gen_islands.py grows them
// from the blocks -- and there are hundreds, no two alike. See islands.inc
// for the form of the library.
//
// Nothing about a hill is drawn by rule any more. A rule reads a shape and
// picks a piece for each tile, and no reading of the shape says which piece:
// the band's rock has a phase, its ends are caps, a side is a strip of
// pieces that go in one order, and a rule that got any of that wrong showed
// it at the seam. The island carries its own pieces, and the map carries,
// per tile, which cell of the sheet the island put there.
#include "islands.inc"
static unsigned short s_island_cell[MAP_HEIGHT][MAP_WIDTH];   // 0: nothing drawn
static int s_island_count = 0;                                 // islands stamped, all levels
static int s_island_sealed_count = 0;                          // mountains with a top no foot can reach
static long s_island_sealed_tiles = 0;                         // their raised tiles, all together

// The cave mouth: a rock mound with a dark opening, drawn over the foot of a
// south wall. Three cells wide and two tall on the sheet, from (21, 6) --
// art/structures/cave_mouth.aseprite, stamped by stamp_cave_mouth.py, which
// must agree with these. Its cells double as overlay ids (the sheet's ids,
// as sheet_cell() below numbers them): the base pass paints them after the
// cliff, so the wall shows round the mound and the opening covers the
// mouth tile's glyph.
static const int CAVE_MOUTH_COL = 21, CAVE_MOUTH_ROW = 6;
static const int CAVE_MOUTH_W = 3, CAVE_MOUTH_H = 2;
static constexpr int cave_mouth_cell(int dx, int dy) {
    return TILE_TOWN0_BASE + (CAVE_MOUTH_ROW + dy) * TOWN0_SHEET_COLS + (CAVE_MOUTH_COL + dx);
}
static inline bool is_cave_mouth_cell(int id) {
    for (int dy = 0; dy < CAVE_MOUTH_H; dy++)
        if (id >= cave_mouth_cell(0, dy) && id < cave_mouth_cell(CAVE_MOUTH_W, dy)) return true;
    return false;
}
static_assert(CLIFF_LEVELS < 7, "the wall bits must leave the sealed bit free");

// Open ground kept round every island, beyond the tile of margin the island
// carries itself, so that islands never touch and each is a distinct thing.
// The least of it, and then up to ISLAND_GAP_VARY more, rolled per island:
// one fixed gap packs islands of a size into rows and columns, which reads
// as a lattice from any distance. A storey's walls stand ISLAND_STOREY_GAP
// tiles of open top away from anything the island below has drawn: its rim,
// its line, another storey. Without that a storey's back line lands straight
// above the parent's front, and between the line and the teeth of the front
// there is a strip of ground a few pixels tall -- drawn, visibly walkable,
// and too thin for the feet. The drawings never put two walls that close;
// only the stamping could, so it may not.
static const int ISLAND_GAP        = 2;
static const int ISLAND_GAP_VARY   = 5;
static const int ISLAND_STOREY_GAP = 1;

// Whether a storey's drawn cell may stand at (x, y): the tile and every tile
// within ISLAND_STOREY_GAP of it is open top of the level below, by `clear`.
template <class Clear>
static bool storey_cell_stands(int x, int y, Clear clear) {
    for (int dy = -ISLAND_STOREY_GAP; dy <= ISLAND_STOREY_GAP; dy++)
        for (int dx = -ISLAND_STOREY_GAP; dx <= ISLAND_STOREY_GAP; dx++)
            if (!clear(x + dx, y + dy)) return false;
    return true;
}

// The five biomes the majority vote is taken over, and a tile's place in that
// list. Order is load-bearing: ties are broken towards the earlier entry, so
// this is the order the old inner loop searched in and it has to stay that way.
static const int BIOME_TILES[] = {
    TILE_GRASS, TILE_SAND, TILE_SNOW, TILE_WASTELAND, TILE_MEADOW
};
static const int NB = (int)(sizeof(BIOME_TILES) / sizeof(BIOME_TILES[0]));

static inline int biome_index(int t) {
    switch (t) {
        case TILE_GRASS:     return 0;
        case TILE_SAND:      return 1;
        case TILE_SNOW:      return 2;
        case TILE_WASTELAND: return 3;
        case TILE_MEADOW:    return 4;
        default:             return -1;
    }
}

// Dissolve biome patches too small to read, by giving every biome tile the
// commonest biome in the 7x7 around it, `passes` times over. Returns false if
// generation was cancelled part way.
//
// One function where there were two identical copies of the loop, differing
// only in how many passes they ran.
//
// The window is carried rather than gathered. Counting all forty-nine cells per
// tile, which is what this did, is a hundred and fifty operations to answer a
// question whose answer at the next tile along differs by two columns of seven
// — and at seventeen passes over nine million tiles that came to a fifth of the
// whole world build, twice. Instead each column keeps a running count over the
// rows in the window, and a running total slides along the row: a tile costs
// ten operations and a row costs two rows of column updates.
//
// The one thing that must not be lost is that this is a *sequential* filter.
// Each tile is decided from a window that already contains the new values of
// the tiles behind it — the pass reads and writes one grid. Gathering the
// counts from a copy of the grid instead is the obvious way to make this fast
// and it is a different filter: it would give a different world from the same
// seed. Hence the write-back below, which pushes every change straight into the
// column count and the running total, so both describe the grid as it is now
// rather than as it was when the row began.
static bool biome_majority_smooth(Tilemap* map, int passes)
{
    const int R = 3;                       // 7x7 window
    static int colcnt[MAP_WIDTH][NB];      // per column, counts over the window's rows
    static_assert(NB == 5, "colcnt and the count arrays below are sized for five biomes");

    // On the joined axis the filter runs the whole way round and the window
    // reads through the seam; on the hard-border axis it stops a window short
    // of the edge, as it did.
    const bool wx = wrapx(), wy = wrapy();
    const int  y0 = wy ? 0 : R, y1 = wy ? MAP_HEIGHT : MAP_HEIGHT - R;
    const int  x0 = wx ? 0 : R, x1 = wx ? MAP_WIDTH  : MAP_WIDTH  - R;

    for (int pass = 0; pass < passes; pass++) {
        if (s_gen_cancel) return false;

        memset(colcnt, 0, sizeof colcnt);
        for (int dy = -R; dy <= R; dy++) {
            int yy = wy ? wrap_y(y0 + dy) : y0 + dy;
            for (int x = 0; x < MAP_WIDTH; x++) {
                int b = biome_index(map->tiles[yy][x]);
                if (b >= 0) colcnt[x][b]++;
            }
        }

        for (int y = y0; y < y1; y++) {
            if (y > y0) {
                // The window drops the row above it and gains the row below.
                int oy = wy ? wrap_y(y - R - 1) : y - R - 1;
                int ny = wy ? wrap_y(y + R)     : y + R;
                for (int x = 0; x < MAP_WIDTH; x++) {
                    int o = biome_index(map->tiles[oy][x]);
                    if (o >= 0) colcnt[x][o]--;
                    int n = biome_index(map->tiles[ny][x]);
                    if (n >= 0) colcnt[x][n]++;
                }
            }

            int total[NB] = { 0, 0, 0, 0, 0 };
            for (int dx = -R; dx <= R; dx++) {
                int c = wx ? wrap_x(x0 + dx) : x0 + dx;
                for (int b = 0; b < NB; b++) total[b] += colcnt[c][b];
            }

            for (int x = x0; x < x1; x++) {
                if (x > x0) {
                    int oc = wx ? wrap_x(x - R - 1) : x - R - 1;
                    int nc = wx ? wrap_x(x + R)     : x + R;
                    for (int b = 0; b < NB; b++) {
                        total[b] -= colcnt[oc][b];
                        total[b] += colcnt[nc][b];
                    }
                }

                int cur = map->tiles[y][x];
                int cb  = biome_index(cur);
                if (cb < 0) continue;

                int best = 0;
                for (int b = 1; b < NB; b++)
                    if (total[b] > total[best]) best = b;

                if (best != cb) {
                    map->tiles[y][x] = BIOME_TILES[best];
                    colcnt[x][cb]--;  colcnt[x][best]++;
                    total[cb]--;      total[best]++;
                }
            }
        }
    }
    return true;
}

// Smooth value noise, with the two axes scaled apart. Sampling on a grid longer
// across than down stretches the field the same way, and a stretched field has
// level sets that run east-west — which is the whole trick the ridges rest on.
//
// Smoothstepped rather than straight bilinear: the linear form creases along
// every grid line, and a crease in the field is a kink in the ridge drawn from
// it.
static float cliff_value_noise(int px, int py, int gw, int gh, int s)
{
    int gx = px / gw, gy = py / gh;
    float fx = (float)(px % gw) / gw;
    float fy = (float)(py % gh) / gh;
    fx = fx * fx * (3.0f - 2.0f * fx);
    fy = fy * fy * (3.0f - 2.0f * fy);
    // The lattice closes on the joined axis: the grid divides the map there,
    // and the column past the last is the first.
    int gx1 = gx + 1, gy1 = gy + 1;
    if (wrapx() && gx1 * gw >= MAP_WIDTH)  gx1 = 0;
    if (wrapy() && gy1 * gh >= MAP_HEIGHT) gy1 = 0;
    float n00 = (float)tile_noise(gx,  gy,  s), n10 = (float)tile_noise(gx1, gy,  s);
    float n01 = (float)tile_noise(gx,  gy1, s), n11 = (float)tile_noise(gx1, gy1, s);
    float top = n00 + fx * (n10 - n00);
    float bot = n01 + fx * (n11 - n01);
    return top + fy * (bot - top);
}

// Which islands can stand on which, and where: storey j sits on island i
// at offset (ox, oy) when every cell j draws lands on a tile of i's first
// level where i draws nothing, with ISLAND_STOREY_GAP of the same all round
// it. Few islands can carry another -- the drawings' plateaus are small -- so
// this is worked out once, over the library, and the placement looks the
// answer up rather than rolling for it.
static const int STOREY_OPTS_CAP = 1 << 14;
static int  s_storey_start[ISLAND_COUNT + 1];
static int  s_storey_j[STOREY_OPTS_CAP], s_storey_ox[STOREY_OPTS_CAP], s_storey_oy[STOREY_OPTS_CAP];
static bool s_storey_built = false;

static void build_storey_table(void) {
    if (s_storey_built) return;
    int n = 0;
    for (int i = 0; i < ISLAND_COUNT; i++) {
        s_storey_start[i] = n;
        const Island& P = ISLANDS[i];
        for (int j = 0; j < ISLAND_COUNT && n < STOREY_OPTS_CAP; j++) {
            const Island& S = ISLANDS[j];
            if (S.w > P.w || S.h > P.h) continue;
            for (int oy = 0; oy <= P.h - S.h && n < STOREY_OPTS_CAP; oy++)
                for (int ox = 0; ox <= P.w - S.w && n < STOREY_OPTS_CAP; ox++) {
                    auto open_top = [&](int px, int py) {
                        return px >= 0 && py >= 0 && px < P.w && py < P.h &&
                               P.level[py * P.w + px] == 1 && !P.cells[py * P.w + px];
                    };
                    bool ok = true;
                    for (int y = 0; y < S.h && ok; y++)
                        for (int x = 0; x < S.w && ok; x++) {
                            if (!S.cells[y * S.w + x]) continue;
                            if (!storey_cell_stands(ox + x, oy + y, open_top)) ok = false;
                        }
                    if (ok) { s_storey_j[n] = j; s_storey_ox[n] = ox; s_storey_oy[n] = oy; n++; }
                }
        }
    }
    s_storey_start[ISLAND_COUNT] = n;
    s_storey_built = true;
}

static void place_cliffs(Tilemap* map, unsigned int seed,
                         int cx, int cy, int hw,
                         int min_r2, int max_r2)
{
    build_storey_table();
    int max_r = (int)sqrtf((float)max_r2) + 1;
    // The window: a row short of each hard border, and the whole of the joined
    // axis, where the border is no border and every pass below reads through
    // the seam with inwin().
    int y_lo = wrapy() ? 0          : ((cy - max_r > 1)            ? cy - max_r : 1);
    int y_hi = wrapy() ? MAP_HEIGHT : ((cy + max_r < MAP_HEIGHT-1) ? cy + max_r : MAP_HEIGHT - 1);
    int x_lo = wrapx() ? 0          : ((cx - max_r > 1)            ? cx - max_r : 1);
    int x_hi = wrapx() ? MAP_WIDTH  : ((cx + max_r < MAP_WIDTH-1)  ? cx + max_r : MAP_WIDTH  - 1);

    // The whole grids, not the window: a world rebuilt with the other axis
    // joined would otherwise keep the last world's border rows.
    memset(s_cliff_elev, 0, sizeof s_cliff_elev);
    memset(s_cliff_face, 0, sizeof s_cliff_face);
    memset(s_island_cell, 0, sizeof s_island_cell);

    auto inwin = [&](int* px, int* py) -> bool {
        if (wrapx()) *px = wrap_x(*px); else if (*px < x_lo || *px >= x_hi) return false;
        if (wrapy()) *py = wrap_y(*py); else if (*py < y_lo || *py >= y_hi) return false;
        return true;
    };

    auto eligible = [&](int px, int py) {
        int ddx = px - cx, ddy = py - cy;
        int r2  = ddx*ddx + ddy*ddy;
        if (r2 < min_r2 || r2 >= max_r2 || r2 <= hw*hw) return false;
        if (water_keepout[py][px]) return false;
        int b = map->tiles[py][px];
        return b == TILE_GRASS || b == TILE_SNOW || b == TILE_WASTELAND;
    };
    auto field = [&](int px, int py) {
        float base  = cliff_value_noise(px, py, CLIFF_HIGH_G,  CLIFF_HIGH_G,
                                        (int)seed ^ 0xC11F);
        float rough = cliff_value_noise(px, py, CLIFF_ROUGH_G, CLIFF_ROUGH_G,
                                        (int)seed ^ 0x5EED);
        float grain = cliff_value_noise(px, py, CLIFF_GRAIN_G, CLIFF_GRAIN_G,
                                        (int)seed ^ 0x9A17);
        float proj = (((float)px - s_cliff_ref_x) * s_cliff_dir_x +
                      ((float)py - s_cliff_ref_y) * s_cliff_dir_y) / s_cliff_dir_len;
        if (proj < 0.0f) proj = 0.0f;
        if (proj > 1.0f) proj = 1.0f;
        return base + CLIFF_ROUGH_AMP * (rough - 16384.0f)
                    + CLIFF_GRAIN_AMP * (grain - 16384.0f) + proj * CLIFF_PEAK_LIFT;
    };
    auto hash = [&](unsigned int a, unsigned int b, unsigned int c) -> unsigned int {
        unsigned int h = seed ^ (a * 0x9E3779B9u) ^ (b * 0x85EBCA6Bu) ^ (c * 0xC2B2AE35u);
        h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
        return h;
    };

    // How much ground there is to cover, sampled: the budgets are shares of it.
    GEN_STAGE(map, "cliff: stamp islands");
    long elig = 0;
    for (int py = y_lo; py < y_hi; py += 4)
        for (int px = x_lo; px < x_hi; px += 4)
            if (eligible(px, py)) elig++;
    elig *= 16;
    if (elig < 64 * 16) return;

    // An island fits at (ax, ay) -- its top-left tile -- on level L when the
    // whole of its box plus the gap is eligible ground with nothing drawn on
    // it, standing at the height the level is built on.
    auto fits = [&](const Island& I, int ax, int ay, int L, int gap) -> bool {
        for (int y = -gap; y < I.h + gap; y++)
            for (int x = -gap; x < I.w + gap; x++) {
                int px = ax + x, py = ay + y;
                if (!inwin(&px, &py)) return false;
                if (!eligible(px, py)) return false;
                bool own = y >= 0 && x >= 0 && y < I.h && x < I.w && I.cells[y * I.w + x];
                if (L == 1) {
                    // open country all round, with nothing drawn on it
                    if (s_island_cell[py][px] || s_cliff_elev[py][px] != 0) return false;
                } else {
                    // A storey's walls stand on the top below, where the
                    // island below drew nothing, and keep ISLAND_STOREY_GAP
                    // of that open top round them. Its own ground -- the
                    // margin it carries and the gap -- asks nothing more: the
                    // stamp writes only drawn cells, so the island below
                    // keeps its rim under the storey's margin, and the
                    // plateaus of the drawings are too small to hold a
                    // storey any other way.
                    if (own && !storey_cell_stands(px, py, [&](int qx, int qy) {
                            if (!inwin(&qx, &qy)) return false;
                            return !s_island_cell[qy][qx] && s_cliff_elev[qy][qx] == L - 1;
                        })) return false;
                }
            }
        return true;
    };
    // mountain_tiles is the raised area of the mountain this stamp belongs
    // to: the island's own top, or for a storey the top of the island it
    // stands on. The cave pass weighs a mountain's chance by it.
    auto stamp = [&](const Island& I, int ax, int ay, int L, int mountain_tiles) {
        bool under_sealed = false;     // standing on a top already sealed
        for (int y = 0; y < I.h; y++)
            for (int x = 0; x < I.w; x++) {
                int px = ax + x, py = ay + y;
                if (!inwin(&px, &py)) continue;
                int c = I.cells[y * I.w + x];
                if (c) {
                    s_island_cell[py][px] = (unsigned short)c;
                    // Nothing stands on a wall or in the scree at its foot:
                    // a tree set there earlier would be drawn over the rock.
                    map->overlay[py][px] = 0;
                    // Rock and line close the ground; the low bit of the face
                    // mask says so per level, and is what tilemap_face_at()
                    // and the walkability tests read. Scree draws and closes
                    // nothing: grains on open ground, to be walked among.
                    if (ISLAND_KIND[c]) {
                        s_cliff_face[py][px] |= (unsigned char)(1 << (L - 1));
                        // Nor on the tile under rock or line: a tree's crown
                        // rises into the tile above its own and would cover
                        // the foot of the wall or the line.
                        int bx = px, by = py + 1;
                        if (inwin(&bx, &by)) map->overlay[by][bx] = 0;
                    }
                }
                // A landform carries its own storeys: a tile's level is how
                // many heights it stands above the ground the landform is on.
                int lv = I.level[y * I.w + x];
                if (lv) {
                    int e = L - 1 + lv;
                    s_cliff_elev[py][px] = (unsigned char)(e > CLIFF_LEVELS ? CLIFF_LEVELS : e);
                    // A top the feet cannot reach from the flat is sealed, and
                    // the cave pass wants to know per mountain. A storey on an
                    // open top seals one; on a sealed top it adds nothing.
                    if (s_cliff_face[py][px] & CLIFF_FACE_SEALED) under_sealed = true;
                    if (!I.open) s_cliff_face[py][px] |= CLIFF_FACE_SEALED;
                }
            }
        if (!I.open && !under_sealed) {
            s_island_sealed_count++;
            s_island_sealed_tiles += mountain_tiles;
        }
    };

    // Level 1: anchors on a coarse grid over the window, taken in the order
    // of the field, highest first, so the islands gather where the range is
    // and thin out away from it. Each anchor rolls an island from the
    // library, hashed off the seed and the anchor so a world rebuilds the
    // same, and takes it if it fits. Until the level's share of the ground
    // is high, or the anchors run out.
    static int   anc_x[1 << 20], anc_y[1 << 20], anc_i[1 << 20];
    static float anc_s[1 << 20];
    const int ANC_CAP = (int)(sizeof anc_i / sizeof *anc_i);
    int na = 0;
    for (int py = y_lo; py < y_hi && na < ANC_CAP; py += 4)
        for (int px = x_lo; px < x_hi && na < ANC_CAP; px += 4) {
            if (!eligible(px, py)) continue;
            anc_x[na] = px; anc_y[na] = py; anc_i[na] = na;
            // a little hashed jitter, so the order is not a scanline where the field is flat
            anc_s[na] = field(px, py) + (float)(hash((unsigned)px, (unsigned)py, 1u) & 1023u);
            na++;
        }
    std::sort(anc_i, anc_i + na, [&](int a, int b) { return anc_s[a] > anc_s[b]; });

    // Which islands were placed, for the storeys above them to sit on.
    static int placed_x[1 << 16], placed_y[1 << 16], placed_i[1 << 16];
    const int PLACED_CAP = (int)(sizeof placed_i / sizeof *placed_i);
    int nplaced = 0;
    s_island_count = 0;
    s_island_sealed_count = 0;
    s_island_sealed_tiles = 0;

    long high = 0, want = (long)(CLIFF_LEVEL_PCT[1] * (float)elig);
    // The library is sorted largest first, in three classes. The anchors
    // are sorted by the field, highest first: the top of the order rolls
    // the large landforms, the middle the medium, the rest the small, so
    // the big country stands where the range is and the islands scatter
    // outward from it.
    for (int k = 0; k < na && high < want; k++) {
        int ax = anc_x[anc_i[k]], ay = anc_y[anc_i[k]];
        unsigned int h = hash((unsigned)ax, (unsigned)ay, 2u);
        int lo, hi;
        if      (k < na * 15 / 100 && ISLAND_LARGE0  > 0)              { lo = 0;              hi = ISLAND_LARGE0; }
        else if (k < na * 50 / 100 && ISLAND_MEDIUM0 > ISLAND_LARGE0)  { lo = ISLAND_LARGE0;  hi = ISLAND_MEDIUM0; }
        else                                                           { lo = ISLAND_MEDIUM0; hi = ISLAND_COUNT; }
        if (hi <= lo) { lo = 0; hi = ISLAND_COUNT; }
        int ii = lo + (int)(h % (unsigned)(hi - lo));
        const Island& I = ISLANDS[ii];
        // the anchor is the island's centre, so a hill sits on its peak
        int tx = ax - I.w / 2, ty = ay - I.h / 2;
        int gap = ISLAND_GAP + (int)(hash((unsigned)ax, (unsigned)ay, 5u) % (unsigned)(ISLAND_GAP_VARY + 1));
        if (!fits(I, tx, ty, 1, gap)) continue;
        stamp(I, tx, ty, 1, I.high_tiles);
        high += I.high_tiles;
        s_island_count++;
        if (nplaced < PLACED_CAP) { placed_x[nplaced] = tx; placed_y[nplaced] = ty; placed_i[nplaced] = ii; nplaced++; }
    }

    // The storeys: on each island placed, in the same order, one of the
    // islands that can stand on it, where it can -- see build_storey_table.
    // The tops are already where the range is highest, so the storeys climb
    // toward the peak, and a big island is the one that gets a second
    // height, because only a big top has room for one.
    for (int L = 2; L <= CLIFF_LEVELS; L++) {
        GEN_STAGE(map, "cliff: stamp islands");
        long got = 0, budget = (long)(CLIFF_LEVEL_PCT[L] * (float)elig);
        int last = nplaced;     // the storeys stamped in this pass are not tops for it
        for (int k = 0; k < last && got < budget; k++) {
            int pi = placed_i[k];
            int o0 = s_storey_start[pi], on = s_storey_start[pi + 1] - o0;
            if (!on) continue;
            unsigned int h = hash((unsigned)placed_x[k], (unsigned)placed_y[k], 16u * (unsigned)L);
            for (int t = 0; t < 4 && t < on; t++) {
                int o = o0 + (int)((h + (unsigned)t * 7919u) % (unsigned)on);
                int ii = s_storey_j[o];
                const Island& I = ISLANDS[ii];
                int tx = placed_x[k] + s_storey_ox[o], ty = placed_y[k] + s_storey_oy[o];
                if (!fits(I, tx, ty, L, 0)) continue;
                stamp(I, tx, ty, L, ISLANDS[pi].high_tiles);
                got += I.high_tiles;
                s_island_count++;
                if (nplaced < PLACED_CAP) { placed_x[nplaced] = tx; placed_y[nplaced] = ty; placed_i[nplaced] = ii; nplaced++; }
                break;
            }
        }
    }

    // A plateau's top is the biome's own ground; all that is written here is
    // how high it stands. The walls are not written to the map at all -- they
    // are drawn over whatever ground they fall on, which is the terrace below.
    static const int snow_c[]  = {0, TILE_CLIFF_SNOW_1,  TILE_CLIFF_SNOW_2,  TILE_CLIFF_SNOW_3};
    static const int waste_c[] = {0, TILE_CLIFF_WASTE_1, TILE_CLIFF_WASTE_2, TILE_CLIFF_WASTE_3};
    static const int plain_c[] = {0, TILE_CLIFF,         TILE_CLIFF_2,       TILE_CLIFF_3};
    for (int py = y_lo; py < y_hi; py++)
        for (int px = x_lo; px < x_hi; px++) {
            int L = s_cliff_elev[py][px];
            if (L <= 0) continue;
            if (L > CLIFF_LEVELS) L = CLIFF_LEVELS;
            int b = map->tiles[py][px];
            if      (b == TILE_SNOW)      map->tiles[py][px] = snow_c[L];
            else if (b == TILE_WASTELAND) map->tiles[py][px] = waste_c[L];
            else                          map->tiles[py][px] = plain_c[L];
        }
}

// Stamp a town blueprint onto the map at tile position (tx, ty).
// Canvas value encoding: 0=blank, 1=grass, 2=path, 3=hub, 4=water, 5=tree, >=6=sprite.
static void stamp_town_blueprint(Tilemap* map, int town_idx, int tx, int ty) {
    const int (*layout)[TOWN_W] = all_towns[town_idx];

    // Towns 1 and 2 have no interior yet -- their layout is 0 everywhere, and
    // 0 means "leave biome terrain unchanged", so with nothing pre-filled they
    // stamped as invisible: no marker on the minimap, and open country a road
    // was free to route straight through the middle of, the same as if no
    // town were there at all. Villages avoid this by pre-filling their
    // footprint with a placeholder before their layout goes on top; towns
    // never did. Pre-fill here too, so an undesigned town reads as a town.
    //
    // Town 0 is excluded: it has a real interior, and relies on 0 to leave
    // its round hub ring showing through the square footprint's corners.
    // Pre-filling those corners would paint over the ring it is meant to
    // show.
    if (town_idx != 0) {
        for (int dy = 0; dy < TOWN_H; dy++)
            for (int dx = 0; dx < TOWN_W; dx++) {
                int wx = tx + dx, wy = ty + dy;
                if (wx < 0 || wy < 0 || wx >= MAP_WIDTH || wy >= MAP_HEIGHT) continue;
                map->tiles[wy][wx]   = TILE_BLUEPRINT;
                map->overlay[wy][wx] = 0;
            }
    }

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

// `biome` is what the site read as before the stamp; the stamp erases it.
static void stamp_village_blueprint(Tilemap* map, int variant, int tx, int ty, int biome) {
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
    map->villages[vi] = { tx, ty, variant, biome };
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
                if (!in_world(&nx, &ny)) continue;
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
    // Which edge the ocean takes (0=W, 1=E, 2=N, 3=S), and with it which pair
    // of edges joins: the ocean and the edge across from it are the borders,
    // the other two wrap. Rolled here rather than in phase 2 so the runtime
    // has the shape of the world before the world is finished.
    unsigned int side_seed = seed ^ 0x5EA5EDEEu;
    side_seed = side_seed * 1664525u + 1013904223u;
    map->ocean_side = (int)((side_seed >> 16) % 4);
    map->wrap_axis  = (map->ocean_side <= 1) ? WRAP_Y : WRAP_X;
    s_wrap_axis     = map->wrap_axis;

    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // Sentinel: mark all castles as unplaced so the main thread sees -1 before phase 2 runs
    for (int i = 0; i < 4; i++) map->castles[i] = { -1, -1, i };

    // Grass fill (TILE_GRASS==0)
    memset(map->tiles, 0, sizeof(map->tiles));
    memset(map->overlay, 0, sizeof(map->overlay));
    memset(map->route,   0, sizeof(map->route));
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
        const int fcx = DNG_FIXED_CAVE_X, fcy = DNG_FIXED_CAVE_Y;
        map->tiles[fcy][fcx]   = TILE_DUNGEON_CAVE;
        map->overlay[fcy][fcx] = 0;
        float fdx = (float)(fcx - MAP_WIDTH  / 2);
        float fdy = (float)(fcy - MAP_HEIGHT / 2);
        float dist     = sqrtf(fdx*fdx + fdy*fdy);
        float max_dist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                               (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
        float difficulty = ((dist / max_dist) + 3.0f / 5.0f) * 0.5f;
        // Biome is TILE_GRASS by fiat: phase 1 runs before any biome is
        // painted, and the start stands on open ground in every world.
        map->dungeon_entrances[0] = { fcx, fcy, 0, DUNGEON_ENT_CAVE, 3, difficulty, 0, -1, -1, -1, TILE_GRASS };
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
        map->dungeon_entrances[1] = { gx, gy, 0, DUNGEON_ENT_GRAVEYARD_SM, 0, difficulty, 0, -1, -1, -1, TILE_GRASS };
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

// Which archetypes belong in a biome at all. This is the whole of what a biome
// decides; how OFTEN each one is drawn is not a property of the biome.
//
// It used to be: each biome carried its own weights, and rarity was whatever
// fell out of weight times biome area, a number nobody could read off and
// nothing could hold steady across worlds. Now every kind has one per-world
// target in DUNGEON_KINDS (include/dungeon_kinds.h), and pick_entrance_type
// draws among a site's native types in proportion to how far each still is
// from its target. The biome only says who is eligible.
//
// No cave here: cave systems are cut into mountains by their own pass, and
// every site that reaches this table is flat ground (hits_cliff rejects the
// rest), so the old "add a cave on a mountain" modifier could never fire.
//
// Oasis is native to snow as well as sand, and pyramid to open flat ground
// as well. Desert survives worldgen as one or two large blobs, so a world can
// simply have too little of it for either to reach its place in the order;
// snow is a fifth of every world and flat ground two thirds.
// stamp_dungeon_surround dresses a snow oasis differently.
static int build_entrance_pool(int biome, DungeonEntranceType* pool) {
    int pool_sz = 0;
    auto add = [&](DungeonEntranceType t) { pool[pool_sz++] = t; };

    switch (biome) {
        case TILE_SNOW:
            add(DUNGEON_ENT_RUINS);
            add(DUNGEON_ENT_GRAVEYARD_SM);
            add(DUNGEON_ENT_GRAVEYARD_LG);
            add(DUNGEON_ENT_OASIS);
            break;
        case TILE_WASTELAND:
            add(DUNGEON_ENT_RUINS);
            break;
        case TILE_SAND:
            add(DUNGEON_ENT_OASIS);
            add(DUNGEON_ENT_PYRAMID);
            break;
        case TILE_TREE:
            add(DUNGEON_ENT_LARGE_TREE);
            add(DUNGEON_ENT_GRAVEYARD_SM);
            add(DUNGEON_ENT_GRAVEYARD_LG);
            break;
        default: // flat (grass/meadow)
            add(DUNGEON_ENT_GRAVEYARD_SM);
            add(DUNGEON_ENT_GRAVEYARD_LG);
            add(DUNGEON_ENT_PYRAMID);
            add(DUNGEON_ENT_STONEHENGE);
            add(DUNGEON_ENT_CATACOMBS);
            break;
    }
    return pool_sz;
}

// Whether this archetype belongs in this biome at all. The guarantee pass uses
// it to keep a forced placement somewhere plausible before it resorts to
// anywhere at all.
static bool entrance_native_to_biome(int biome, DungeonEntranceType t) {
    DungeonEntranceType pool[DUNGEON_ENT_COUNT];
    int n = build_entrance_pool(biome, pool);
    for (int i = 0; i < n; i++) if (pool[i] == t) return true;
    return false;
}

// Footprint of an archetype: 0 = 1x1, 1 = 2x2. Fixed for most, random for the
// two that vary. Its own function because the guarantee pass needs a size for a
// type it chose rather than drew.
static int entrance_size_for(DungeonEntranceType type, unsigned int rng_seed) {
    switch (type) {
        case DUNGEON_ENT_GRAVEYARD_SM: return 0;
        case DUNGEON_ENT_OASIS:        return 0;
        case DUNGEON_ENT_GRAVEYARD_LG: return 1;
        case DUNGEON_ENT_PYRAMID:      return 1;
        case DUNGEON_ENT_STONEHENGE:   return 1;
        case DUNGEON_ENT_LARGE_TREE:   return 0;
        case DUNGEON_ENT_CATACOMBS:    return 1;
        default: // CAVE and RUINS vary
            rng_seed = rng_seed * 1664525u + 1013904223u;
            return (int)((rng_seed >> 16) & 1);
    }
}

// Draws an archetype for a site, or returns false if every type native to its
// biome has already reached its per-world target and the site should be left
// for another kind of ground.
//
// The weight of a native type is its RELATIVE deficit, (target - have) / target
// in thousandths. At the start of a world every weight is 1000 and the draw is
// uniform among the natives, which is what lets a biome-locked type (ruins,
// oasis, pyramid, the large tree) claim its share of the few sites it can use
// before the graveyards, native nearly everywhere, take them. As a type fills
// up on the ground it has plenty of, its weight falls and the sites it shares
// go to whichever native is furthest behind — so the counts chase the table's
// order as far as biome area allows, and a type at target stops being drawn at
// all rather than overshooting because its biome happened to be large.
//
// have_kind is indexed by DUNGEON_KINDS row. rng_seed is passed by value and
// advanced internally, as before.
static bool pick_entrance_type(int biome, const int* have_kind, unsigned int rng_seed,
                               DungeonEntranceType& out_type, int& out_size) {
    DungeonEntranceType pool[DUNGEON_ENT_COUNT];
    int w[DUNGEON_ENT_COUNT];
    int pool_sz = build_entrance_pool(biome, pool);
    int total_w = 0;
    for (int i = 0; i < pool_sz; i++) {
        int k = dungeon_kind_for_type(pool[i]);
        int target = DUNGEON_KINDS[k].target;
        int left = target - have_kind[k];
        w[i] = left > 0 ? left * 1000 / target : 0;
        total_w += w[i];
    }
    if (total_w == 0) return false;

    rng_seed = rng_seed * 1664525u + 1013904223u;
    int roll = (int)((rng_seed >> 16) % (unsigned)total_w);
    DungeonEntranceType type = pool[pool_sz - 1];   // last entry absorbs rounding
    for (int i = 0; i < pool_sz; i++) {
        roll -= w[i];
        if (roll < 0) { type = pool[i]; break; }
    }

    out_type = type;
    out_size = entrance_size_for(type, rng_seed);
    return true;
}

// The yard a graveyard of this kind stands in: fence width and height in tiles.
// stamp_dungeon_surround draws the fence from these and tilemap_spawn_graveyard_lg_nodes
// lays its rows of headstones out inside the same shape, so the two cannot
// disagree about where the walls are and leave stones standing in a hedge.
static void graveyard_yard_size(DungeonEntranceType type, int& span, int& H) {
    if (type == DUNGEON_ENT_CATACOMBS) { span = 30; H = 24; }
    else                               { span = 17; H = 14; }
}

// Stamps decorative tiles/overlays around a placed dungeon entrance.
// Uses existing tile primitives as a "temp" visual so each type is readable on the overworld:
//   graveyard → rock tombstones,  stonehenge → rock ring,  pyramid → sand clearing,
//   oasis → pond neighbors,       large tree → tree overlays,  ruins → scattered debris.
// cave has no surround — it sits embedded in a clifftop.
// biome is the site's biome_of() at placement (stored on the entrance record),
// for the archetypes whose exterior depends on where they stand.
static void stamp_dungeon_surround(Tilemap* map, DungeonEntranceType type, int biome,
                                   int ex, int ey, int sz) {
    // Only paint on flat biome tiles — skip water, cliffs, structures, other
    // entrances, and anything under a drawn cliff face (the ground beneath a
    // face is still a flat tile, so the id alone does not say).
    // The surround may spill over the seam; the footprint itself never does,
    // so it is tested in the unwrapped frame first and the tile is then read
    // through the wrap. Two tiles off each hard border, as before.
    auto surround_tile = [&](int& tx, int& ty) -> bool {
        if (tx >= ex && tx < ex+sz && ty >= ey && ty < ey+sz) return false;
        if (!in_world(&tx, &ty)) return false;
        if (!wrapx() && (tx < 2 || tx >= MAP_WIDTH-2))  return false;
        if (!wrapy() && (ty < 2 || ty >= MAP_HEIGHT-2)) return false;
        return true;
    };
    auto safe_base = [&](int tx, int ty, int tile_id) {
        if (!surround_tile(tx, ty)) return;
        if (tilemap_face_at(tx, ty)) return;
        int base = map->tiles[ty][tx];
        if (base != TILE_GRASS && base != TILE_MEADOW && base != TILE_PATH &&
            base != TILE_SAND  && base != TILE_SNOW   && base != TILE_WASTELAND) return;
        map->tiles[ty][tx]   = tile_id;
        map->overlay[ty][tx] = 0;
    };
    auto safe_ovl = [&](int tx, int ty, int ovl_id) {
        if (!surround_tile(tx, ty)) return;
        if (tilemap_face_at(tx, ty)) return;
        int base = map->tiles[ty][tx];
        if (base != TILE_GRASS && base != TILE_MEADOW && base != TILE_PATH &&
            base != TILE_SAND  && base != TILE_SNOW   && base != TILE_WASTELAND) return;
        map->overlay[ty][tx] = ovl_id;
    };

    // Placeholder parallelogram fence — 1:1 diagonal (north wall shifted right by
    // H tiles vs south wall). To be replaced with proper art later.
    //
    //   N: (L+H, T) ────[gate]──────── (R+H, T)
    //        \                             \
    //   S: (L, B) ──────────────────── (R, B)   (fully closed)
    //
    // `span` is the fence width and `H` its height; L falls out of centring the
    // north fence on the mausoleum (ex, ex+1) so the entrance sits in the middle
    // of the top row rather than at the far-left corner. Parameterised because
    // catacombs is the same yard at a larger size — the shear, the gate and the
    // fill are one description, not two that have to be kept in step.
    auto stamp_graveyard_yard = [&](int span, int H) {
        const int L = ex - span / 2 - H, R = L + span;   // south fence extents
        const int T = ey - 1,            B = T + H;      // north/south rows

        auto lx_at = [&](int ty) { return L + (B - ty); };
        auto rx_at = [&](int ty) { return R + (B - ty); };

        // Interior PATH fill
        for (int ty = T + 1; ty < B; ty++)
            for (int tx = lx_at(ty) + 1; tx < rx_at(ty); tx++)
                safe_base(tx, ty, TILE_PATH);

        // North fence — closed, the mausoleum itself is the way through
        for (int tx = lx_at(T); tx <= rx_at(T); tx++)
            safe_ovl(tx, T, TILE_ROCK);

        // South fence — 2-tile gate at its centre
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
    };

    switch (type) {
        case DUNGEON_ENT_GRAVEYARD_SM:
            // Small path clearing — gravestones are spawned as resource nodes later.
            // Stamp a 5×5 patch of path tiles so the clearing is visible before spawn.
            //for (int dy = -2; dy <= 2; dy++)
                //for (int dx = -2; dx <= 2; dx++)
                    //safe_base(ex+dx, ey+dy, TILE_PATH);
            break;

        case DUNGEON_ENT_GRAVEYARD_LG:
        case DUNGEON_ENT_CATACOMBS: {
            // The same yard either way; catacombs is simply a bigger one.
            int span, H;
            graveyard_yard_size(type, span, H);
            stamp_graveyard_yard(span, H);
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

        case DUNGEON_ENT_PYRAMID: {
            // A cleared court three tiles deep around the 2×2 entrance. It is
            // PATH, a ground tile: it used to be TILE_ROCK as a base tile,
            // which tile_ground_walkable does not list, so every pyramid stood
            // inside a solid ring nobody could cross. The same court on sand
            // and on open flat ground.
            const int lo = -3, hi = sz + 2;
            for (int dy = lo; dy <= hi; dy++)
                for (int dx = lo; dx <= hi; dx++)
                    safe_base(ex+dx, ey+dy, TILE_PATH);
            break;
        }

        case DUNGEON_ENT_OASIS:
            // Pond tiles at four cardinal neighbors of the 1×1 entrance. In
            // snow the pool is ringed with boulders on the diagonals — a
            // spring breaking through ice rather than a pool in the sand.
            // Placeholder dressing, like the graveyard fence above, until it
            // gets its own art.
            //
            // Two tiles out, not one: the sweep at the end of generation
            // (clear_overlays_near_liquid) strips anything standing beside
            // water, and every tile touching the entrance touches a pond.
            safe_base(ex,   ey-1, TILE_POND);
            safe_base(ex,   ey+1, TILE_POND);
            safe_base(ex-1, ey,   TILE_POND);
            safe_base(ex+1, ey,   TILE_POND);
            if (biome == TILE_SNOW) {
                safe_ovl(ex-2, ey-2, TILE_ROCK);
                safe_ovl(ex+2, ey-2, TILE_ROCK);
                safe_ovl(ex-2, ey+2, TILE_ROCK);
                safe_ovl(ex+2, ey+2, TILE_ROCK);
            }
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
        // Catacombs has no tile of its own and borrows the large graveyard's --
        // see the note on DUNGEON_ENT_CATACOMBS. The archetype is read from the
        // entrance record, so nothing downstream can tell the difference.
        case DUNGEON_ENT_CATACOMBS:    return TILE_DUNGEON_GRAVEYARD_LG;
        case DUNGEON_ENT_OASIS:        return TILE_DUNGEON_OASIS;
        case DUNGEON_ENT_PYRAMID:      return TILE_DUNGEON_PYRAMID;
        case DUNGEON_ENT_STONEHENGE:   return TILE_DUNGEON_STONEHENGE;
        case DUNGEON_ENT_LARGE_TREE:   return TILE_DUNGEON_LARGE_TREE;
        default:                       return TILE_DUNGEON;
    }
}

// Join a set of places with worn routes: a minimum spanning tree over them,
// each edge routed as the shortest branch from the track already laid to the
// place being joined — going round what it cannot cross and bridging what it
// can — then smoothed and drifted so it reads as a track rather than a line
// someone drew. The tree says who joins whom and in what order; the ground
// decides where the branch leaves the network (see the note at the edge loop).
//
// Extracted from the wasteland-trail pass so roads between settlements can use
// the same router. Everything biome-specific is a predicate the caller supplies:
//
//   is_region   ground a route may be laid on
//   is_lava     the gap it may bridge, including decks already laid
//   is_raw_gap  the tile a deck may be laid over
//   in_moat     where a crossing is forbidden outright
//   paintable   the ground the route may be laid over
//   spillable   the tile the stroke's OUTER edge may overwrite as well. The
//               route is planned on the middle tile of a three-wide track, and
//               the two beside it can easily fall outside the ground the route
//               was allowed to follow -- along the edge of the wasteland, most
//               of all. Refusing them there is what makes a track two wide, so
//               this is the ground it may lean onto instead.
//
// connect_all is how hard the caller wants the network held together, and the
// two callers want opposite things.
//
// Trails pass false. A wasteland with one dungeon still wants a track leading
// away from the mouth, so a lone node runs a stub out into the waste; and a
// spanning-tree edge that will not route is dropped, because a trail that
// cannot get there is a trail that was not meant to be.
//
// Roads pass true. A lone settlement does not want a road to nowhere -- a road
// goes *between* places -- so there is no stub. But a settlement left off the
// network is a settlement the player cannot drive to, so a dropped edge is
// retried against the next-nearest settlement across the break until the whole
// set is one network or nothing is left to try.
//
// The names are the wasteland's because the code is, unchanged, and renaming a
// six-hundred-line body is how a refactor that was meant to change nothing ends
// up changing something.
// Which edge painted each route tile, and which tiles more than one edge
// painted. A diagnostic for tools/shot.cpp's SHOT_TRAIL view, allocated only
// when ROUTE_OWNER_TRACE is set in the environment, so the game never pays for
// it. It exists because "is this wide stretch one stroke or two" cannot be
// answered from the finished route layer, and the two have different causes:
// one stroke too wide is the painter, two side by side is the planner.
static std::vector<uint16_t> g_route_owner;
static std::vector<uint8_t>  g_route_multi;
const uint8_t* tilemap_debug_route_multi() {
    return g_route_multi.empty() ? nullptr : g_route_multi.data();
}
const uint16_t* tilemap_debug_route_owner() {
    return g_route_owner.empty() ? nullptr : g_route_owner.data();
}

template <typename InRegion, typename IsGap, typename IsRawGap,
          typename Forbidden, typename Paintable, typename Spillable>
static void route_network(Tilemap* map, unsigned int route_seed,
                          const std::vector<std::pair<int,int>>& nodes,
                          InRegion is_region, IsGap is_lava, IsRawGap is_raw_gap,
                          Forbidden in_moat, Paintable paintable, Spillable spillable,
                          uint8_t route_kind, int bridge_tile,
                          int EDGE_CLEARANCE, int ENDPOINT_FREE, int ANCHOR_SEARCH,
                          int BRIDGE_MAX, int BRIDGE_GAP, bool connect_all)
{
        s_route_nodes = (int)nodes.size();
        s_route_anchors = 0;
        s_route_lone = 0;
        // Owners restart per network (edge numbers are per call); the
        // multi-edge marks accumulate across both, since a tile is a tile.
        if (getenv("ROUTE_OWNER_TRACE")) {
            g_route_owner.assign((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
            if (g_route_multi.empty()) g_route_multi.assign((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        }
        s_trail_edges = s_trail_unroutable = s_trail_tooshort = 0;
        // Asked for rather than required: the
        // router gives it up a tile at a time until a way through appears, so
        // this is how far from the border a trail would like to run, not how
        // far it must. Three was enough to stop trails tracing the rim but left
        // them well inside it — routed at a mean of five tiles' clearance where
        // the wasteland's own mean was nine — because a shortest path still
        // hugs the inside of a bend once it is clear of the margin.
        const int DX4[4] = {1,-1,0,0}, DY4[4] = {0,0,1,-1};
        std::vector<uint8_t> seen((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<uint8_t> incomp((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<uint8_t> nearedge((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<int> prev((size_t)MAP_WIDTH * MAP_HEIGHT, -1);
        // How many tiles of lava the route has crossed to reach this one, so a
        // crossing can be cut off once it is longer than a bridge should be.
        std::vector<uint8_t> runlen((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        // Whether the span so far has passed a tile with channel on both sides
        // across the travel: proof that it is crossing a channel and not just
        // stepping over a bulge in the bank. A landing without it is refused.
        std::vector<uint8_t> spanok((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        // And how much ground it still owes before it may cross again. Two
        // crossings back to back meet at a corner and fuse into one L-shaped
        // deck, which is neither three wide nor going one way.
        std::vector<uint8_t> cool((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        std::vector<int> comp, route, touched, path, rimq;
        // The track already laid that an edge may branch from: 2 on a tile a
        // branch may start from, 1 on a deck (walked through, never started
        // from), 0 elsewhere. nettouched is what to clear afterwards.
        // Bits 1-2: 2 on a tile a branch may end at, 1 on a deck (walked
        // through, never ended on). Bit 4: seen by the flood this edge, which
        // is separate so the flood can pass THROUGH a tile the other network
        // pre-marked without disturbing that mark -- otherwise two pieces of
        // trail joined only by a road could not see each other, and the next
        // node routed to the road sixty tiles away instead of the trail three
        // tiles away, side by side with it the whole way.
        std::vector<int> nettouched, netq;
        std::vector<uint8_t> onnet((size_t)MAP_WIDTH * MAP_HEIGHT, 0);
        // For a network that does not have to hold itself together (trails),
        // every tile the OTHER network laid is somewhere a branch may end: a
        // trail that reaches a road has arrived. Marked once and never
        // cleared -- the per-edge flood only touches tiles it found at zero.
        // Roads keep to their own network: their retries join two separate
        // pieces by reachability, and a foreign track would fake a join.
        if (!connect_all)
            for (int y = 0; y < MAP_HEIGHT; y++)
                for (int x = 0; x < MAP_WIDTH; x++)
                    if (map->route[y][x] != ROUTE_NONE && map->route[y][x] != route_kind)
                        onnet[(size_t)y * MAP_WIDTH + x] = 2;
        unsigned int ts = route_seed;

        // A bridge is a straight run and nothing else: one direction, three
        // tiles wide, and short. So lava is not ground the route wanders over —
        // it is a gap the route may step across in one move, in a straight line
        // and only where the crossing is brief. Anything wider is gone around.
        //
        // Letting the route treat lava as ordinary ground, which is what it did
        // before, gave crossings that curved with the trail and sprawled wider
        // than the trail at every turn, because the brush was sweeping a
        // wandering line over a channel rather than laying a span across it.

        // Lava a bridge is allowed to cross.
        auto spannable = [&](int x, int y) {
            return is_lava(x, y) && !in_moat(x, y);
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
            if (!in_world(&nx, &ny) || !spannable(nx, ny)) return -1;
            for (int k = 1; k <= BRIDGE_MAX; k++) {
                nx += DX4[d]; ny += DY4[d];
                if (!in_world(&nx, &ny)) return -1;
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
                        if (!in_world(&nx, &ny)) continue;
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
                for (size_t ni2 = 0; ni2 < nodes.size(); ni2++) {
                    int ex = nodes[ni2].first;
                    int ey = nodes[ni2].second;
                    int best = -1, bestd = INT_MAX;
                    for (int dy = -ANCHOR_SEARCH; dy <= ANCHOR_SEARCH; dy++)
                        for (int dx = -ANCHOR_SEARCH; dx <= ANCHOR_SEARCH; dx++) {
                            int nx = ex + dx, ny = ey + dy;
                            if (!in_world(&nx, &ny)) continue;
                            size_t ni = (size_t)ny * MAP_WIDTH + nx;
                            if (!incomp[ni] || is_lava(nx, ny)) continue;
                            int dd = dx*dx + dy*dy;
                            if (dd < bestd) { bestd = dd; best = (int)ni; }
                        }
                    if (best >= 0) anchors.push_back(best);
                }
                s_route_anchors += (int)anchors.size();
                if (anchors.size() == 1) s_route_lone++;

                // Endpoints as tiles, and the same edges as anchor indices. The
                // router works in tiles; holding the network together works in
                // anchors, because that is what has to end up in one piece.
                std::vector<std::pair<int,int>> edges, edge_idx;
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
                                double ddx = wrap_dx(ax - bx), ddy = wrap_dy(ay - by);
                                double dd = ddx*ddx + ddy*ddy;
                                if (dd < bestd) { bestd = dd; ba = (int)a; bb = (int)b; }
                            }
                        }
                        if (bb < 0) break;
                        intree[bb] = true;
                        edges.push_back({ anchors[ba], anchors[bb] });
                        edge_idx.push_back({ ba, bb });
                    }
                } else if (anchors.size() == 1 && !connect_all) {
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
                                if (!in_world(&nx, &ny)) return false;
                                if (!incomp[(size_t)ny * MAP_WIDTH + nx]) return false;
                            }
                        return true;
                    };
                    int pick = -1; long bestd = -1;
                    for (int c : comp) {
                        int px2 = c % MAP_WIDTH, py2 = c / MAP_WIDTH;
                        if (is_lava(px2, py2)) continue;   // no track ends mid-bridge
                        if (!is_deep(px2, py2)) continue;
                        long wdx = wrap_dx(px2 - ax), wdy = wrap_dy(py2 - ay), dd = wdx*wdx + wdy*wdy;
                        if (dd > bestd) { bestd = dd; pick = c; }
                    }
                    if (pick < 0) {
                        // No point has full clearance — a thin sliver of a
                        // wasteland. Fall back to the plain furthest point
                        // rather than leave the lone dungeon without a trail.
                        for (int c : comp) {
                            int px2 = c % MAP_WIDTH, py2 = c / MAP_WIDTH;
                            if (is_lava(px2, py2)) continue;
                            long wdx = wrap_dx(px2 - ax), wdy = wrap_dy(py2 - ay), dd = wdx*wdx + wdy*wdy;
                            if (dd > bestd) { bestd = dd; pick = c; }
                        }
                    }
                    // The far end is a point in the waste, not an anchor, so
                    // there is nothing for it to be joined to.
                    if (pick >= 0) { edges.push_back({ a, pick }); edge_idx.push_back({ 0, -1 }); }
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
                        return in_world(&x, &y) && incomp[(size_t)y * MAP_WIDTH + x];
                    };
                    // A gap tile at a position that may lie over the seam.
                    auto lava_at = [&](int x, int y) {
                        return in_world(&x, &y) && is_lava(x, y);
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
                                if (lava_at(nx, ny)) continue;
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
                                    // The depth spreads over the gap as well as
                                    // the ground. A channel is not a rim, but
                                    // a channel running INSIDE the clearance
                                    // band is inside the band, and leaving it
                                    // out gave the strict pass a loophole: the
                                    // ground beside a cliff was refused, the
                                    // lava beside it was not, so a route that
                                    // could have walked three tiles of bank
                                    // crossed the channel instead and joined
                                    // the network on the far side -- a second
                                    // deck four tiles from the first, at every
                                    // cave mouth a channel passes. Refused in
                                    // the strict pass, the crossing falls to
                                    // the lenient one, which takes the bank.
                                    if (!in_world(&nx, &ny)) continue;
                                    if (!in_this(nx, ny) && !spannable(nx, ny)) continue;
                                    size_t ni = (size_t)ny * MAP_WIDTH + nx;
                                    if (nearedge[ni]) continue;
                                    nearedge[ni] = (uint8_t)(depth + 1);
                                    rimq.push_back((int)ni);
                                }
                        }
                    }

                    size_t cur_edge = 0;   // which edge is painting, for the owner trace
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
                                if (!in_world(&px2, &py2)) continue;
                                size_t pi = (size_t)py2 * MAP_WIDTH + px2;
                                // Never bleed into a neighbouring wasteland
                                // across a thin barrier: that leaves a scrap of
                                // trail somewhere it was not asked for.
                                // The middle of the stroke is the tile the
                                // route was planned on and must be in the
                                // region; an outer tile may instead lean onto
                                // ground the route itself could not follow.
                                // Measured, that is where 70% of the trail's
                                // narrow stretches came from: the wasteland
                                // simply runs out under the edge of the track.
                                //
                                // It has to be TOUCHING the region to do it,
                                // which is what incomp was really guarding --
                                // not "stay off other ground" but "never step
                                // over a thin barrier into the next wasteland
                                // and leave a scrap of trail there".
                                if (!incomp[pi] || !paintable(px2, py2)) {
                                    if (!spillable(px2, py2)) continue;
                                    bool touches = false;
                                    for (int d = 0; d < 4 && !touches; d++) {
                                        touches = in_this(px2 + DX4[d], py2 + DY4[d]);
                                    }
                                    if (!touches) continue;
                                }
                                // The ground stays exactly what it was. A
                                // track is worn INTO a place, not laid instead
                                // of it, and keeping the tile is what lets the
                                // track know which ground it crosses and lets
                                // that ground draw underneath it.
                                map->route[py2][px2] = route_kind;
                                if (!(onnet[pi] & 3)) { onnet[pi] |= 2; nettouched.push_back(pi); }
                                if (!g_route_owner.empty()) {
                                    uint16_t o = g_route_owner[pi];
                                    if (o && o != (uint16_t)(cur_edge + 1)) g_route_multi[pi] = 1;
                                    g_route_owner[pi] = (uint16_t)(cur_edge + 1);
                                }
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
                            if (!in_world(&px2, &py2)) continue;
                            if (!is_raw_gap(px2, py2)) continue;
                            if (in_moat(px2, py2)) continue;
                            map->tiles[py2][px2]   = bridge_tile;
                            map->overlay[py2][px2] = 0;
                        }
                    };

                    // The spanning tree is a plan; this is what came of it.
                    // Disjoint sets over the anchors, joined only by an edge
                    // that actually routed, so "is the network in one piece"
                    // is a question with an answer rather than an assumption.
                    const int NA = (int)anchors.size();
                    std::vector<int> dsu(NA);
                    for (int i = 0; i < NA; i++) dsu[i] = i;
                    auto dsu_find = [&](int v) {
                        while (dsu[v] != v) { dsu[v] = dsu[dsu[v]]; v = dsu[v]; }
                        return v;
                    };
                    // Pairs already attempted, so a break that cannot be routed
                    // is not retried forever. Only roads keep this.
                    std::vector<uint8_t> tried;
                    int retries_left = 0;
                    if (connect_all) {
                        tried.assign((size_t)NA * NA, 0);
                        for (auto& p : edge_idx)
                            if (p.second >= 0) {
                                tried[(size_t)p.first * NA + p.second] = 1;
                                tried[(size_t)p.second * NA + p.first] = 1;
                            }
                        // One retry per anchor. Every success removes a set, so
                        // this is generous, and it caps the whole-map frontier
                        // searches a pathological map could ask for.
                        retries_left = NA;
                    }

                    // Called however an edge ends. It records what the edge did
                    // to the sets, and — once the planned edges are spent — asks
                    // for one more where the network is still in pieces.
                    auto finish_edge = [&](size_t ei, bool joined) {
                        int ia = edge_idx[ei].first, ib = edge_idx[ei].second;
                        if (joined && ib >= 0) {
                            int ra = dsu_find(ia), rb = dsu_find(ib);
                            if (ra != rb) dsu[ra] = rb;
                        }
                        if (ei + 1 != edges.size() || retries_left <= 0) return;
                        // Nearest pair still on opposite sides of a break. Going
                        // by distance again means the second attempt crosses the
                        // narrowest part of whatever stopped the first.
                        int ba = -1, bb = -1; double bestd = 1e18;
                        for (int a2 = 0; a2 < NA; a2++)
                            for (int b2 = a2 + 1; b2 < NA; b2++) {
                                if (tried[(size_t)a2 * NA + b2]) continue;
                                if (dsu_find(a2) == dsu_find(b2)) continue;
                                int ax2 = anchors[a2] % MAP_WIDTH, ay2 = anchors[a2] / MAP_WIDTH;
                                int bx2 = anchors[b2] % MAP_WIDTH, by2 = anchors[b2] / MAP_WIDTH;
                                double ddx = wrap_dx(ax2 - bx2), ddy = wrap_dy(ay2 - by2);
                                double dd = ddx*ddx + ddy*ddy;
                                if (dd < bestd) { bestd = dd; ba = a2; bb = b2; }
                            }
                        if (ba < 0) { retries_left = 0; return; }
                        tried[(size_t)ba * NA + bb] = 1;
                        tried[(size_t)bb * NA + ba] = 1;
                        retries_left--;
                        edges.push_back({ anchors[ba], anchors[bb] });
                        edge_idx.push_back({ ba, bb });
                    };

                    // Indexed, not ranged: finish_edge appends to `edges` as it
                    // goes, which would leave a reference dangling.
                    for (size_t ei = 0; ei < edges.size(); ei++) {
                        int from = edges[ei].first, to = edges[ei].second;
                        cur_edge = ei;
                        s_trail_edges++;
                        // Two dungeons close enough to share an anchor: there
                        // is nothing to route, and they are already joined.
                        if (from == to) {
                            paint_trail(from % MAP_WIDTH, from / MAP_WIDTH);
                            finish_edge(ei, true);
                            continue;
                        }

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

                        // An edge is a BRANCH off the track already laid, not
                        // a second full route from `from`. Every edge used to
                        // be routed and painted on its own, and the spanning
                        // tree made that ugly three ways at once: edges fanning
                        // out of one anchor shared their first stretch and
                        // painted it two or three times over (a wedge six or
                        // seven wide), edges heading the same way ran side by
                        // side a few tiles apart, and two of them crossing the
                        // same channel laid decks next to each other until the
                        // channel was one slab. All of it is one mistake — a
                        // track that already goes your way is not followed, it
                        // is duplicated — so this is one rule: the search
                        // runs from `to` outward and stops at the first tile
                        // of the network reachable from `from` that it
                        // touches, and the path it finds is the shortest
                        // branch from wherever that network comes closest. A
                        // road that meets a road joins it. (Searching from the
                        // node rather than seeding every network tile at
                        // distance zero finds the same branch and costs one
                        // source instead of thirty thousand; measured, the
                        // seeded form added three seconds to a world.)
                        //
                        // Reachable from `from`, not the whole network: an
                        // earlier edge that would not route leaves its node
                        // off the track, and a road retry joins two separate
                        // pieces. Branching from a piece `from` is not on
                        // would paint a stub that joins nothing to it. Decks
                        // are walked through so the far side of a bridge
                        // counts, but never started from: no branch begins
                        // mid-bridge.
                        //
                        // Track of EITHER kind counts. A trail that reaches a
                        // road has arrived: on the ground a worn track is a
                        // worn track, and a trail laid a tile beside a road
                        // rather than into it read as the two avoiding each
                        // other. Roads are laid before trails for this reason
                        // -- a side track branches off the main road, not the
                        // other way round -- and a trail can only meet a road
                        // where the road runs through its own region, so this
                        // never pulls a trail out of the wasteland.
                        nettouched.clear();
                        netq.clear();
                        auto net_visit = [&](int t, bool deck) {
                            if (onnet[t] & 4) return;                 // seen this flood
                            if (!(onnet[t] & 3)) { onnet[t] |= deck ? 1 : 2; nettouched.push_back(t); }
                            onnet[t] |= 4;
                            netq.push_back(t);
                        };
                        net_visit(from, false);
                        for (size_t h = 0; h < netq.size(); h++) {
                            int t = netq[h];
                            int qx = t % MAP_WIDTH, qy = t / MAP_WIDTH;
                            for (int d = 0; d < 4; d++) {
                                int nx = qx + DX4[d], ny = qy + DY4[d];
                                if (!in_world(&nx, &ny)) continue;
                                int ni = ny * MAP_WIDTH + nx;
                                int tt = map->tiles[ny][nx];
                                bool deck = tt == TILE_WASTE_BRIDGE || tt == TILE_ROAD_BRIDGE;
                                if (map->route[ny][nx] == ROUTE_NONE && !deck) continue;
                                net_visit(ni, deck);
                            }
                        }
                        // Already on the track: an earlier edge ran over this
                        // node's anchor. Nothing to route, and it is joined.
                        if (onnet[to] & 3) {
                            // ...unless it is `from` that has none yet (see
                            // lay_branch below): then the branch runs from it.
                            if (map->route[from / MAP_WIDTH][from % MAP_WIDTH] == ROUTE_NONE) {
                                onnet[to] |= 2;   // it is, whichever network laid it
                            } else {
                                for (int t : netq) onnet[t] &= 3;
                                for (int t : nettouched) onnet[t] = 0;
                                finish_edge(ei, true);
                                continue;
                            }
                        }

                        // Lay one branch: from `start` outward to the nearest
                        // tile of the network, smoothed, drifted and painted.
                        // Returns whether it routed. Called for `to`, and again
                        // for `from` when the first branch left it with no
                        // track: the root of a component is `from` of its first
                        // edge and `to` of none, and now that a branch may stop
                        // at a road instead of at `from`, the root can be left
                        // standing on bare ground.
                        auto lay_branch = [&](int start) -> bool {
                        int end_free = ENDPOINT_FREE;
                        auto near_end = [&](int x, int y) {
                            return (abs(wrap_dx(x - fex)) <= end_free && abs(wrap_dy(y - fey)) <= end_free)
                                || (abs(wrap_dx(x - tex)) <= end_free && abs(wrap_dy(y - tey)) <= end_free);
                        };
                        bool found = false;
                        int  hit   = -1;   // the network tile the branch reached
                        path.clear();
                        // Two attempts, strict then as before.
                        //
                        // The stroke is three tiles across and is refused any
                        // tile outside the region it belongs to, so a route lying
                        // against that region's edge comes out two wide with no
                        // complaint from anything. Measured over four worlds,
                        // that is where essentially every narrow stretch comes
                        // from: 88% of the road's run alongside a settlement
                        // footprint, and 70% of the trail's along the edge of the
                        // wasteland. Both were reached through the waivers below
                        // rather than in spite of them — the margin gives its
                        // clearance away one tile at a time down to nothing, and
                        // near_end() waives it outright, over a 24-tile box for a
                        // road, which is exactly the ground a settlement covers.
                        //
                        // So ask first for a route that keeps a tile of clearance
                        // and only claims the waiver right at its ends. Where no
                        // such route exists — a dungeon hard against the border, a
                        // settlement ringed by water — fall back to the old terms
                        // rather than leave the pair unjoined. Connectivity was
                        // never the thing that needed fixing.
                        for (int pass = 0; pass < 2 && !found; pass++) {
                        int margin_min = (pass == 0) ? 1 : 0;
                        end_free       = (pass == 0) ? 2 : ENDPOINT_FREE;
                        for (int margin = EDGE_CLEARANCE; margin >= margin_min && !found; margin--) {
                            // From the node being joined, out toward the track.
                            route.clear();
                            route.push_back(start);
                            prev[start] = start;
                            touched.push_back(start);
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
                                    int ddx = wrap_dx(qx - p % MAP_WIDTH), ddy = wrap_dy(qy - p / MAP_WIDTH);
                                    for (int d = 0; d < 4; d++)
                                        if (DX4[d] == ddx && DY4[d] == ddy) fixed_d = d;
                                }
                                for (int k = 0; k < 4 && !found; k++) {
                                    int d = on_lava ? fixed_d : ((k + rot) & 3);
                                    if (d < 0) break;
                                    int nx = qx + DX4[d], ny = qy + DY4[d];
                                    if (in_world(&nx, &ny)) {
                                        int ni = ny * MAP_WIDTH + nx;
                                        int run = on_lava ? runlen[route[h]] : 0;
                                        // Across the direction of travel.
                                        int sx = DY4[d], sy = DX4[d];
                                        auto both_sides = [&](int px, int py) {
                                            return lava_at(px + sx, py + sy) && lava_at(px - sx, py - sy);
                                        };
                                        bool ok = false;
                                        if (incomp[ni]) {
                                            // Ground. Landing from a span is
                                            // only allowed if the span crossed
                                            // a channel somewhere along it --
                                            // a route walking a bank used to
                                            // hop a one-tile bulge of lava and
                                            // leave a two-tile deck on the
                                            // shore for it. A channel crossed
                                            // square has lava either side on
                                            // every tile; crossed at an angle,
                                            // on its middle ones; a bulge on
                                            // none.
                                            ok = !on_lava || spanok[route[h]];
                                        } else if (spannable(nx, ny) && run < BRIDGE_MAX
                                                   && (on_lava || cool[route[h]] == 0)) {
                                            // Another tile of channel -- which
                                            // makes the tile being LEFT an
                                            // interior tile of the span, and an
                                            // interior tile has to have channel
                                            // on both sides across the direction
                                            // of travel. A span is a crossing.
                                            // Without this the search, which the
                                            // rim margin does not reach out over
                                            // lava, would run down a channel
                                            // along its bank for as long as a
                                            // bridge may be: a deck laid
                                            // lengthwise beside the shore, two
                                            // wide where the third column was
                                            // ground, turning corners with the
                                            // bank. Only the first and last tile
                                            // of a span may touch the bank,
                                            // which is what lets a straight
                                            // crossing still cut a channel that
                                            // runs at an angle.
                                            ok = !on_lava || both_sides(qx, qy);
                                        }
                                        // Keeping a tile of clearance from the
                                        // GAP as well as from the rim was tried
                                        // here and measured worse, so it is not
                                        // done. The rim scan skips lava so a
                                        // route can reach a channel and bridge
                                        // it, which does let a track lie hard
                                        // against one — a quarter of the trail's
                                        // narrow stretches. But the same
                                        // predicate is water for a road, and
                                        // asking roads to stand off every
                                        // shoreline pushed edge after edge into
                                        // the fallback below: roads went from 2.0%
                                        // narrow to 3.8% and their worst stretch
                                        // from 18 tiles to 77, to buy the trail
                                        // 0.7 of a point. Left alone deliberately.
                                        // The margin is never held against the
                                        // network itself: the track is wherever
                                        // it already is.
                                        if (ok && prev[ni] == -1 &&
                                            !(nearedge[ni] && nearedge[ni] <= margin
                                              && (onnet[ni] & 3) != 2 && !near_end(nx, ny))) {
                                            prev[ni] = route[h];
                                            runlen[ni] = incomp[ni] ? 0 : (uint8_t)(run + 1);
                                            spanok[ni] = incomp[ni] ? 0
                                                : (uint8_t)((on_lava ? spanok[route[h]] : 0) | (both_sides(nx, ny) ? 1 : 0));
                                            // Landing from a crossing starts the
                                            // debt; walking pays it off a tile
                                            // at a time.
                                            cool[ni] = incomp[ni]
                                                ? (on_lava ? (uint8_t)BRIDGE_GAP
                                                           : (uint8_t)(cool[route[h]] ? cool[route[h]] - 1 : 0))
                                                : 0;
                                            touched.push_back(ni);
                                            route.push_back(ni);
                                            if ((onnet[ni] & 3) == 2) { found = true; hit = ni; break; }
                                        }
                                    }
                                    if (on_lava) break;   // the one direction, and no other
                                }
                            }
                            // Walk the chain from the tile beside the network
                            // back to `to`: that is already the branch in
                            // painting order, network end first. The network
                            // tile itself is on the track and is not part of
                            // the branch, as `from` never was.
                            if (found)
                                for (int cur = prev[hit]; ; cur = prev[cur]) {
                                    path.push_back(cur);
                                    if (cur == start) break;
                                }
                            for (int t2 : touched) { prev[t2] = -1; runlen[t2] = 0; cool[t2] = 0; spanok[t2] = 0; }
                            touched.clear();
                        }
                        }
                        if (!found) return false;
                        // (The chain above is already network-to-node order.)
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
                        //
                        // In an unwrapped frame: each point is its predecessor
                        // plus the short step between them, so a branch that
                        // crosses the seam is one continuous line here rather
                        // than one that leaps the width of the world, and the
                        // painting below fills between neighbours and not
                        // across the map. Points are read back through the
                        // wrap wherever they are tested or painted.
                        std::vector<float> fxs(path.size()), fys(path.size());
                        for (size_t i = 0; i < path.size(); i++) {
                            int px2 = path[i] % MAP_WIDTH, py2 = path[i] / MAP_WIDTH;
                            if (i == 0) { fxs[i] = (float)px2; fys[i] = (float)py2; continue; }
                            int qx2 = path[i-1] % MAP_WIDTH, qy2 = path[i-1] / MAP_WIDTH;
                            fxs[i] = fxs[i-1] + (float)wrap_dx(px2 - qx2);
                            fys[i] = fys[i-1] + (float)wrap_dy(py2 - qy2);
                        }
                        const std::vector<float> ox = fxs, oy = fys;   // the routed line, unwrapped

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
                                if (in_this((int)floorf(sx2), (int)floorf(sy2))) {
                                    nx2[i] = sx2; ny2[i] = sy2;
                                }
                            }
                            fxs.swap(nx2); fys.swap(ny2);
                        }
                        // Displaced into a second pair of arrays, never in
                        // place. The offset is taken along the perpendicular
                        // to the chord between a point's two neighbours, and
                        // the chord has to be the SMOOTHED line's: with the
                        // previous point already moved two tiles sideways, the
                        // chord swung through forty-five degrees or more, the
                        // perpendicular swung with it, and the next point was
                        // thrown off in a different direction from the one
                        // before it. Consecutive centres then stood three tiles
                        // apart across the track, and the brush, which fills
                        // between consecutive centres, laid a band six or seven
                        // wide wherever the drift was near its clamp and three
                        // wide where it passed through zero — the swelling and
                        // narrowing that ran along every road.
                        std::vector<float> dxs = fxs, dys = fys;
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
                                int ix = (int)floorf(px2), iy = (int)floorf(py2);
                                if (!in_this(ix, iy)) continue;
                                dxs[i] = px2; dys[i] = py2;
                                taken = s;
                                break;
                            }
                            drift *= taken;
                        }
                        fxs.swap(dxs); fys.swap(dys);

                        // Draw between consecutive centres rather than stamping
                        // at each: smoothing and drift move points by a few
                        // tiles, and where one is carried out of the region it
                        // falls back to the routed original — a jump wide
                        // enough that two brush marks no longer overlap.
                        int lastx = 0, lasty = 0;
                        bool have_last = false;
                        for (size_t i = 0; i < path.size(); i++) {
                            // A span point is laid where the route put it, deck
                            // only, and takes no part in the joining-up below:
                            // interpolating onto or off a bridge would step
                            // diagonally across the deck and cut its corners.
                            if (span[i] >= 0) {
                                paint_span(path[i] % MAP_WIDTH, path[i] / MAP_WIDTH, span[i]);
                                have_last = false;
                                continue;
                            }
                            int ix = (int)floorf(fxs[i]), iy = (int)floorf(fys[i]);
                            if (!in_this(ix, iy)) {
                                ix = (int)ox[i];
                                iy = (int)oy[i];
                            }
                            if (!have_last) {
                                paint_trail(ix, iy);
                            } else {
                                int dxs = ix - lastx, dys = iy - lasty;
                                int steps = (abs(dxs) > abs(dys)) ? abs(dxs) : abs(dys);
                                if (steps < 1) steps = 1;
                                for (int s = 1; s <= steps; s++)
                                    paint_trail(lastx + dxs * s / steps,
                                                lasty + dys * s / steps);
                            }
                            lastx = ix; lasty = iy; have_last = true;
                        }
                        return true;
                        };

                        bool laid = lay_branch(to);
                        if (laid && map->route[from / MAP_WIDTH][from % MAP_WIDTH] == ROUTE_NONE)
                            lay_branch(from);
                        for (int t : netq) onnet[t] &= 3;
                        for (int t : nettouched) onnet[t] = 0;
                        if (!laid) { s_trail_unroutable++; finish_edge(ei, false); continue; }
                        finish_edge(ei, true);
                    }
                }
                for (int c : comp) { incomp[c] = 0; nearedge[c] = 0; }
                // The depth also sits on gap tiles outside comp; a channel is
                // shared with the wasteland across it.
                for (int c : rimq) nearedge[c] = 0;
            }
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

    // Which edge the ocean occupies (0=W, 1=E, 2=N, 3=S): phase 1's roll.
    const int ocean_side = map->ocean_side;
    // The interior the scatter passes work over: a row short of each hard
    // border, and the whole of the joined axis.
    const int ix0 = wrapx() ? 0 : 1, ix1 = wrapx() ? MAP_WIDTH  : MAP_WIDTH  - 1;
    const int iy0 = wrapy() ? 0 : 1, iy1 = wrapy() ? MAP_HEIGHT : MAP_HEIGHT - 1;

    GEN_STAGE(map, "before Ocean");
    // --- Ocean ---
    {
        static int coast_h[MAP_HEIGHT]; // used for W/E oceans (varies along Y)
        static int coast_v[MAP_WIDTH];  // used for N/S oceans (varies along X)

        // The coastline runs along the joined axis, so its smoothing goes
        // twice round the world and keeps the second lap: the first ends
        // where the second begins, and the shore meets itself at the seam.
        auto smooth_round = [](int* coast, int n) {
            static int raw[MAP_WIDTH > MAP_HEIGHT ? MAP_WIDTH : MAP_HEIGHT];
            for (int i = 0; i < n; i++) raw[i] = coast[i];
            float sc = (float)raw[0];
            for (int i = 1; i < 2 * n; i++) {
                sc = sc * 0.97f + (float)raw[i % n] * 0.03f;
                if (i >= n) coast[i % n] = (int)sc;
            }
        };
        if (ocean_side == 0 || ocean_side == 1) {
            for (int y = 0; y < MAP_HEIGHT; y++)
                coast_h[y] = 300 + (tile_noise(0, y, 999) % 120);
            smooth_round(coast_h, MAP_HEIGHT);
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
            smooth_round(coast_v, MAP_WIDTH);
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
                                 seed ^ (unsigned int)(i * 0x1111), ocean_side,
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
            } else if (wrapx() ? (fabsf(dx) >= fabsf(dy)) : (fabsf(dy) >= fabsf(dx))) {
                // Bound for a joined edge. There is no shore to end at, and
                // a river left to run would go round the world and back
                // through its own source; it crosses the seam and, some way
                // past it, peters out as the cliff-side rivers do.
                int dist = wrapx() ? (dx > 0.0f ? MAP_WIDTH  - sx : sx)
                                   : (dy > 0.0f ? MAP_HEIGHT - sy : sy);
                unsigned int ls = (seed ^ (unsigned int)(0x9999*(i+1))) * 1664525u + 1013904223u;
                max_steps = dist + 300 + (int)((ls >> 16) % 600);
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
        // The gradient runs straight from the ocean edge to the mountain
        // edge. It used to lean toward the peak, which put a slope across
        // the joined axis and a step in it at the seam; the peak still pulls
        // the wasteland toward itself, through peak_nearness below.
        s_cliff_dir_x   = (ocean_side == 0) ? 1.0f : (ocean_side == 1) ? -1.0f : 0.0f;
        s_cliff_dir_y   = (ocean_side == 2) ? 1.0f : (ocean_side == 3) ? -1.0f : 0.0f;
        s_cliff_dir_len = (ocean_side <= 1) ? (float)MAP_WIDTH : (float)MAP_HEIGHT;
    }

    GEN_STAGE(map, "before Cliff blocked prepass");
    // --- Cliff blocked prepass ---
    const int CLIFF_CLEAR = 20;
    memset(water_keepout, 0, sizeof(water_keepout));
    for (int y = 0; y < MAP_HEIGHT; y++) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int t = map->tiles[y][x];
            if (t != TILE_RIVER && t != TILE_WATER) continue;
            for (int by = y - CLIFF_CLEAR; by <= y + CLIFF_CLEAR; by++)
                for (int bx = x - CLIFF_CLEAR; bx <= x + CLIFF_CLEAR; bx++) {
                    int kx = bx, ky = by;
                    if (in_world(&kx, &ky)) water_keepout[ky][kx] = true;
                }
        }
    }

    GEN_STAGE(map, "before Biome pass");
    // --- Biome pass: plains / desert / snow / wasteland ---
    if (s_gen_cancel) return;
    // Desert: flat areas away from mountains. Snow/wasteland: map edges.
    {
        const int BIOME_GRID = 300;
        // Where desert starts before the mountain and the peak push it back.
        // It was 16383, the middle of the noise; the edge bands now reach
        // further into the low ground by the ocean, where desert lives, and
        // this is what gives it back the same share of the world it had.
        const int DESERT_BASE = 13000;
        static_assert(MAP_WIDTH % 300 == 0 && MAP_HEIGHT % 300 == 0, "the biome lattice must close on the joined axis");
        // The farthest a tile can be from the peak, the short way round: half
        // the joined axis and the whole of the other. It was the map's full
        // diagonal when nothing wrapped; measured the short way round, the old
        // scale left every tile nearer the peak than it used to be, and the
        // desert the peak suppresses all but vanished.
        const float max_dist2 = (float)MAP_WIDTH * (float)MAP_WIDTH * 1.25f;
        const float half_map  = (float)MAP_WIDTH * 0.5f;
        for (int y = iy0; y < iy1; y++) {
            for (int x = ix0; x < ix1; x++) {
                if (map->tiles[y][x] != TILE_GRASS) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;

                // Mountain-side projection (0=ocean side, 1=cliff side)
                float proj = (((float)x - s_cliff_ref_x) * s_cliff_dir_x +
                               ((float)y - s_cliff_ref_y) * s_cliff_dir_y) / s_cliff_dir_len;
                if (proj < 0.0f) proj = 0.0f;
                if (proj > 1.0f) proj = 1.0f;

                // Proximity to cliff peak, the short way round
                float dpx = (float)wrap_dx(x - (int)map->cliff_peak_x);
                float dpy = (float)wrap_dy(y - (int)map->cliff_peak_y);
                float peak_nearness = 1.0f - (dpx*dpx + dpy*dpy) / max_dist2;
                if (peak_nearness < 0.0f) peak_nearness = 0.0f;

                // Proximity to a hard edge (0=center, 1=edge). The joined
                // edges are not edges: nothing is near them.
                int me = wrapx() ? (y < MAP_HEIGHT-1-y ? y : MAP_HEIGHT-1-y)
                                 : (x < MAP_WIDTH-1-x  ? x : MAP_WIDTH-1-x);
                // Square-rooted so it covers the same share of the world at
                // each value as the four-edge measure did: two edges are half
                // the perimeter, and linear it gave snow half its ground.
                float edge_u = (float)me / half_map;
                float edge_nearness = edge_u < 1.0f ? sqrtf(1.0f - edge_u) : 0.0f;
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

                // Coarse biome noise helper. The lattice closes on the joined
                // axis -- the grid divides the map -- so the field is one
                // continuous thing across the seam.
                int gx = x / BIOME_GRID, gy = y / BIOME_GRID;
                int gx1 = (wrapx() && (gx + 1) * BIOME_GRID >= MAP_WIDTH)  ? 0 : gx + 1;
                int gy1 = (wrapy() && (gy + 1) * BIOME_GRID >= MAP_HEIGHT) ? 0 : gy + 1;
                float fx = (float)(x % BIOME_GRID) / BIOME_GRID;
                float fy = (float)(y % BIOME_GRID) / BIOME_GRID;
                auto bn = [&](unsigned int s) -> int {
                    float t = tile_noise(gx,gy,s)   + fx*(tile_noise(gx1,gy,s)  -tile_noise(gx,gy,s));
                    float b = tile_noise(gx,gy1,s)  + fx*(tile_noise(gx1,gy1,s) -tile_noise(gx,gy1,s));
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
                int desert_threshold = DESERT_BASE
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
    // 7 passes of the 7x7 majority vote. Only biome tiles participate;
    // structural tiles (water, cliff, rock, river) are left alone.
    if (!biome_majority_smooth(map, 7)) return;

    GEN_STAGE(map, "before Biome adjacency fixup");
    // --- Biome adjacency fixup ---
    // Rule 1: TILE_SAND cannot be adjacent to TILE_SNOW.
    // Rule 2: TILE_SNOW can only be adjacent to TILE_GRASS or TILE_MEADOW (among biome tiles).
    // Any SAND within SNOW_BUFFER tiles of snow is converted to TILE_MEADOW,
    // creating a wide meadow/forest transition zone between the two biomes.
    //
    // "Is there snow within fifty tiles" asked once for the whole map rather
    // than once per tile of desert. It used to be a 101x101 box scan per sand
    // tile — ten thousand reads to answer a question whose answer at the tile
    // next door differs by two columns of it — and it cost a fifth of the whole
    // build.
    //
    // The same answer, not a near one. Two things make the hoist exact. The
    // loop only ever writes MEADOW, and MEADOW is not SNOW, so nothing it does
    // can change the answer for a tile it has not reached yet; the predicate is
    // constant across the pass. And a Chebyshev reach is a square, so the
    // dilation separates into a pass along each axis, which is what turns
    // O(map * radius^2) into O(map).
    {
        const int SNOW_BUFFER = 50;

        // Along each row first: snow anywhere in [x-B, x+B]. Clamped at the map
        // edge, which the result never depends on — the apply loop below reads
        // only the interior, exactly as the box scan did.
        // On the joined axis the reach runs through the seam: a span that
        // crosses it is the end of the row plus the start of it.
        static int pre[MAP_WIDTH + 1];
        for (int y = 0; y < MAP_HEIGHT; y++) {
            pre[0] = 0;
            for (int x = 0; x < MAP_WIDTH; x++)
                pre[x + 1] = pre[x] + (map->tiles[y][x] == TILE_SNOW ? 1 : 0);
            for (int x = 0; x < MAP_WIDTH; x++) {
                int a = x - SNOW_BUFFER, b = x + SNOW_BUFFER, n;
                if (wrapx() && a < 0)                n = pre[b + 1] + pre[MAP_WIDTH] - pre[a + MAP_WIDTH];
                else if (wrapx() && b > MAP_WIDTH-1) n = pre[MAP_WIDTH] - pre[a] + pre[b + 1 - MAP_WIDTH];
                else {
                    if (a < 0) a = 0;
                    if (b > MAP_WIDTH - 1) b = MAP_WIDTH - 1;
                    n = pre[b + 1] - pre[a];
                }
                s_biome_near[y][x] = (unsigned char)(n > 0);
            }
        }

        // Then down the columns, as a window that gains a row and loses a row
        // rather than a per-column prefix sum: both are O(map), but this one
        // touches two whole rows in order instead of striding a column at a
        // time, and the row walk is the one the cache likes. The window is
        // filled with the rows either side of row 0 -- through the seam on
        // the joined axis, and only what exists on the other -- then slid.
        static int colcount[MAP_WIDTH];
        memset(colcount, 0, sizeof(colcount));
        auto row_in = [&](int r) -> int { if (wrapy()) return wrap_y(r); return (r >= 0 && r < MAP_HEIGHT) ? r : -1; };
        for (int dy = -SNOW_BUFFER; dy <= SNOW_BUFFER; dy++) {
            int r = row_in(dy);
            if (r >= 0) for (int x = 0; x < MAP_WIDTH; x++) colcount[x] += s_biome_near[r][x];
        }
        for (int cy = 0; cy < MAP_HEIGHT; cy++) {
            if (cy > 0) {
                int add = row_in(cy + SNOW_BUFFER), drop = row_in(cy - SNOW_BUFFER - 1);
                if (add  >= 0) for (int x = 0; x < MAP_WIDTH; x++) colcount[x] += s_biome_near[add][x];
                if (drop >= 0) for (int x = 0; x < MAP_WIDTH; x++) colcount[x] -= s_biome_near[drop][x];
            }
            // The interior only on the hard axis, exactly as the box scan did.
            if (!wrapy() && (cy < SNOW_BUFFER || cy >= MAP_HEIGHT - SNOW_BUFFER)) continue;
            if (s_gen_cancel) return;
            const int xa = wrapx() ? 0 : SNOW_BUFFER, xb = wrapx() ? MAP_WIDTH : MAP_WIDTH - SNOW_BUFFER;
            for (int x = xa; x < xb; x++) {
                if (map->tiles[cy][x] != TILE_SAND) continue;
                if (colcount[x] > 0) map->tiles[cy][x] = TILE_MEADOW;
            }
        }
    }

    GEN_STAGE(map, "before Post-fixup biome smoothing");
    // --- Post-fixup biome smoothing ---
    // Re-run majority vote after the adjacency fixup to dissolve thin strips of desert
    // or snow that were left orphaned when their neighbors were converted to meadow.
    if (!biome_majority_smooth(map, 10)) return;

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
                        if (!in_world(&nx, &ny)) continue;
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
                    if (!in_world(&nx, &ny)) continue;
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
    build_cliff_near();

    GEN_STAGE(map, "before Trees");
    // --- Trees ---
    if (s_gen_cancel) return;
    // TILE_GRASS = spotty dense forest (coarse cluster noise → dense patches + clearings)
    // TILE_MEADOW = open plains (~5% trees)
    //
    // Taken back out by 171cb26 along with the rock and the ore, and restored
    // here as it was but for the one test below, which it now needs and did not
    // then.
    //
    // A plateau's top looks after itself: it is written as TILE_CLIFF/_2/_3, or
    // its snow and wasteland families, and none of those are among the three
    // tiles this grows on. The face is the part that changed underneath it. When
    // this was written the drop was a tile in its own right, TILE_CLIFF_EDGE_*,
    // so growing on grass alone kept trees off it. The band is not written to the
    // map at all any more — it is drawn over whatever ground it lands on, and
    // that ground is still grass — so the old test puts a tree in the middle of
    // a wall, which is what it did on the south bend of every cliff.
    //
    // tilemap_face_at is the low bits of the face mask: every tile any part of
    // the cliff could close, which is more than the tiles the band draws from.
    // More is what is wanted. The ground under the sweep is shut to the player
    // whether or not rock is drawn on it, so a tree standing there is one nobody
    // can reach.
    {
        const int FG = 20; // forest cluster grid size; divides the map, so the lattice closes on the joined axis
        static_assert(MAP_WIDTH % 20 == 0 && MAP_HEIGHT % 20 == 0, "the forest lattice must close on the joined axis");
        for (int y = iy0; y < iy1; y++) {
            for (int x = ix0; x < ix1; x++) {
                int t = map->tiles[y][x];
                if (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SNOW) continue;
                if (cliff_bars_overlay(x, y)) continue;
                int ddx = x - cx, ddy = y - cy;
                if (ddx*ddx + ddy*ddy <= hw*hw) continue;
                int n = tile_noise(x, y, (int)seed ^ 7);
                if (t == TILE_MEADOW) {
                    if (n > 32400) map->overlay[y][x] = TILE_TREE;
                } else if (t == TILE_SNOW) {
                    // Thin brush: only inside forest clusters, sparser than temperate forest
                    int gx = x/FG, gy = y/FG;
                    int gx1 = (wrapx() && (gx+1)*FG >= MAP_WIDTH) ? 0 : gx+1, gy1 = (wrapy() && (gy+1)*FG >= MAP_HEIGHT) ? 0 : gy+1;
                    float fx = (float)(x%FG)/FG, fy = (float)(y%FG)/FG;
                    float top = tile_noise(gx,gy,(int)seed^0xF05) + fx*(tile_noise(gx1,gy,(int)seed^0xF05)-tile_noise(gx,gy,(int)seed^0xF05));
                    float bot = tile_noise(gx,gy1,(int)seed^0xF05) + fx*(tile_noise(gx1,gy1,(int)seed^0xF05)-tile_noise(gx,gy1,(int)seed^0xF05));
                    int cluster = (int)(top + fy*(bot-top));
                    if (cluster > 20000 && n > 16000)
                        map->overlay[y][x] = TILE_TREE;
                } else {
                    int gx = x/FG, gy = y/FG;
                    int gx1 = (wrapx() && (gx+1)*FG >= MAP_WIDTH) ? 0 : gx+1, gy1 = (wrapy() && (gy+1)*FG >= MAP_HEIGHT) ? 0 : gy+1;
                    float fx = (float)(x%FG)/FG, fy = (float)(y%FG)/FG;
                    float top = tile_noise(gx,gy,(int)seed^0xF04) + fx*(tile_noise(gx1,gy,(int)seed^0xF04)-tile_noise(gx,gy,(int)seed^0xF04));
                    float bot = tile_noise(gx,gy1,(int)seed^0xF04) + fx*(tile_noise(gx1,gy1,(int)seed^0xF04)-tile_noise(gx,gy1,(int)seed^0xF04));
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
            int x = ix0 + (int)((s >> 16) % (unsigned)(ix1 - ix0));
            s = s * 1664525u + 1013904223u;
            int y = iy0 + (int)((s >> 16) % (unsigned)(iy1 - iy0));
            int ddx = x - cx, ddy = y - cy;
            if (ddx*ddx + ddy*ddy <= hw*hw) continue;
            // Off the face for the same reason the trees are: the ground a band
            // is drawn over is still grass, so without this a boulder sits in
            // the middle of a wall.
            if (cliff_bars_overlay(x, y)) continue;
            if (map->tiles[y][x] == TILE_GRASS && map->overlay[y][x] == 0) map->overlay[y][x] = TILE_ROCK;
        }
    }

    GEN_STAGE(map, "before Rocks at elevation");
    // --- Rocks at elevation (density scales with cliff level) ---
    //
    // Off again. This came back while mountains were thin ridges, where a crest
    // two tiles wide had nothing but the overlay to tell it from the field it
    // ran through. A highland is acres wide again and reads by its band and its
    // outline, so the rock has nothing to add and forty percent coverage of it
    // buries the surface — which is what had it switched off the first time.
#if 0
    {
        for (int y = iy0; y < iy1; y++) {
            for (int x = ix0; x < ix1; x++) {
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
#endif

    GEN_STAGE(map, "before Gold ore at high elevation");
    // --- Gold ore at high elevation (cliff 3+) for all biomes ---
    //
    // Back on. This went off with the rock overlay when the cliffs were redrawn,
    // and unlike the rock it had no reason to: ore is two to five percent of the
    // tops it appears on, so it dots a plateau rather than carpeting it, and it
    // is the only source of HARVEST_ORE in the world. Switching it off did not
    // thin out a texture, it deleted a resource.
    {
        for (int y = iy0; y < iy1; y++) {
            for (int x = ix0; x < ix1; x++) {
                int t = map->tiles[y][x];
                int threshold;
                if      (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) threshold = 32127; // ~2%
                else if (t == TILE_CLIFF_4 || t == TILE_CLIFF_SNOW_4 || t == TILE_CLIFF_WASTE_4) threshold = 31784; // ~3%
                else if (t == TILE_CLIFF_5 || t == TILE_CLIFF_SNOW_5 || t == TILE_CLIFF_WASTE_5) threshold = 31129; // ~5%
                else continue;
                // High ground is not the same as ground with nothing drawn on
                // it. A level's band is drawn over the tops of every level below
                // it, so a tile that is a level-2 plateau by its own id can be
                // under the wall of the level-3 plateau behind it — and an ore
                // put there is embedded in the rock, which is where it appeared
                // on the bend of seed 463.
                if (cliff_bars_overlay(x, y)) continue;
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
            int lx = ix0 + (int)((ls >> 16) % (unsigned)(ix1 - ix0));
            ls = ls * 1664525u + 1013904223u;
            int ly = iy0 + (int)((ls >> 16) % (unsigned)(iy1 - iy0));
            if (map->tiles[ly][lx] != TILE_WASTELAND || water_keepout[ly][lx]) continue;
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
            int lx = ix0 + (int)((ls >> 16) % (unsigned)(ix1 - ix0));
            ls = ls * 1664525u + 1013904223u;
            int ly = iy0 + (int)((ls >> 16) % (unsigned)(iy1 - iy0));
            if (map->tiles[ly][lx] != TILE_WASTELAND || water_keepout[ly][lx]) continue;
            paint_stream_brush(map, lx, ly, 2, cx, cy, guard_r, TILE_WASTELAND, TILE_LAVA);
        }

    }

    GEN_STAGE(map, "before Dead trees scattered in wasteland");
    // --- Dead trees scattered in wasteland (~2%) ---
    {
        for (int y = iy0; y < iy1; y++) {
            for (int x = ix0; x < ix1; x++) {
                if (map->tiles[y][x] != TILE_WASTELAND) continue;
                // Off the water, and not under a wall -- two different masks.
                if (water_keepout[y][x]) continue;
                if (cliff_bars_overlay(x, y)) continue;
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
            int lx = ix0 + (int)((ps >> 16) % (unsigned)(ix1 - ix0));
            ps = ps * 1664525u + 1013904223u;
            int ly = iy0 + (int)((ps >> 16) % (unsigned)(iy1 - iy0));
            if (map->tiles[ly][lx] != TILE_MEADOW || water_keepout[ly][lx]) continue;
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
            int lx = ix0 + (int)((ps >> 16) % (unsigned)(ix1 - ix0));
            ps = ps * 1664525u + 1013904223u;
            int ly = iy0 + (int)((ps >> 16) % (unsigned)(iy1 - iy0));
            if (map->tiles[ly][lx] != TILE_MEADOW || water_keepout[ly][lx]) continue;
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
                    if (!in_world(&px,&py)) continue;
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
            // The hard edges only; the joined ones are not edges.
            int me = wrapx() ? (fy < MAP_HEIGHT-1-fy ? fy : MAP_HEIGHT-1-fy)
                             : (fx < MAP_WIDTH-1-fx  ? fx : MAP_WIDTH-1-fx);
            float u = (float)me/hm; float n = u < 1.0f ? sqrtf(1.0f-u) : 0.0f; return n>1.0f?1.0f:n;
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
            || (bt >= TILE_CLIFF_SIDE_E_1 && bt <= TILE_CLIFF_BACK_3);     // 74-81: east sides, back faces
    };

    GEN_STAGE(map, "before Towns 1-3");
    // --- Towns 1-3 ---
    if (s_gen_cancel) return;
    // Town 0 is already stamped in phase1 (player starts there).
    // Town 1: placed on the coastline, standing out over the water, position
    //         varies by seed.
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

        // How far the coastal town stands out past the waterline. Its
        // footprint is neither reshaped nor resized: the whole 156x156 simply
        // sits this much further out to sea than dry land begins.
        const int COAST_REACH = 30;

        // Which way the open sea lies. The ocean is a single band down one side
        // of the map — see the Ocean pass, which floods one edge and only one
        // — so this is one direction for the whole world, not something each
        // candidate has to work out from the water beside it.
        const int sea_dx = (ocean_side == 0) ? -1 : (ocean_side == 1) ? 1 : 0;
        const int sea_dy = (ocean_side == 2) ? -1 : (ocean_side == 3) ? 1 : 0;

        // Which side of the shifted footprint is the strip that hangs out to sea.
        // Everything else is the town proper.
        auto in_sea_strip = [&](int dx, int dy) -> bool {
            if (sea_dx < 0) return dx <  COAST_REACH;
            if (sea_dx > 0) return dx >= TOWN_W - COAST_REACH;
            if (sea_dy < 0) return dy <  COAST_REACH;
            return dy >= TOWN_H - COAST_REACH;
        };

        // What this window would cost to build on: every tile the town would
        // overwrite that is not ordinary ground. Sea is ordinary out in the
        // strip -- reaching over it is the whole point -- and a defect
        // anywhere else, along with river and cliff on either side.
        //
        // Counted rather than merely detected, because when no window is clean
        // the town still has to go somewhere, and the least bad coast is a
        // better answer than open country inland. `cap` stops the count once
        // the answer is past caring: the first pass only asks whether a window
        // is spotless, and pays for one tile rather than twenty-four thousand
        // to hear that it is not. One description of a bad tile either way --
        // this used to be a pair of boolean lambdas beside this counter, which
        // is two places to change the day sand or lava stops being ground.
        auto coastal_cost = [&](int tx, int ty, int cap) -> int {
            int bad = 0;
            for (int dy = 0; dy < TOWN_H; dy++)
                for (int dx = 0; dx < TOWN_W; dx++) {
                    int bt = map->tiles[ty+dy][tx+dx];
                    if (bt == TILE_WATER)      { if (!in_sea_strip(dx, dy)) bad++; }
                    else if (bt == TILE_RIVER) bad++;
                    else if (is_cliff(bt))     bad++;
                    if (bad > cap) return bad;
                }
            return bad;
        };

        // Last resort for either town: the first place on the map that will
        // take one at all.
        //
        // A town is 156x156 and footprint_ok wants every one of those 24336
        // tiles free of water, river and cliff, on a map where highland alone is
        // eight percent and scattered through everything. That is a demanding
        // ask, and both searches below used to answer "nowhere" by writing
        // {-1,-1} and moving on — a town silently absent from the world with
        // nothing saying so. There are meant to be three, always, so the search
        // widens instead of giving up.
        //
        // Coarse step because this only runs when the proper search has already
        // failed: it is the difference between a town in a slightly odd place
        // and no town.
        auto scan_any_footprint = [&](int& out_x, int& out_y, int min_dist, int upto) -> bool {
            for (int ty = margin_y(TOWN_H); ty + TOWN_H <= MAP_HEIGHT - margin_y(TOWN_H); ty += 8)
                for (int tx = margin_x(TOWN_W); tx + TOWN_W <= MAP_WIDTH - margin_x(TOWN_W); tx += 8) {
                    int ddx = tx - cx, ddy = ty - cy;
                    if (ddx*ddx + ddy*ddy <= (hw+TOWN_H)*(hw+TOWN_H)) continue;
                    bool far_enough = true;
                    for (int i = 0; i < upto && far_enough; i++) {
                        if (map->towns[i].x < 0) continue;
                        int ex = wrap_dx(map->towns[i].x - tx), ey = wrap_dy(map->towns[i].y - ty);
                        if (ex*ex + ey*ey < min_dist*min_dist) far_enough = false;
                    }
                    if (!far_enough) continue;
                    if (!footprint_ok(tx, ty)) continue;
                    out_x = tx; out_y = ty;
                    return true;
                }
            return false;
        };

        // -- Town 1: on the coast, reaching out over it --
        //
        // The coast is read rather than searched for. wl[] is the waterline,
        // one entry per line across it: how far in the open water reaches
        // before it stops. Counted inward from the map edge, so what it
        // measures is the ocean by construction — never a pond, never a
        // river, and never the ring of water town 0 stamps around the starting
        // island, whose far shore is otherwise indistinguishable from a coast.
        //
        // A town then falls out of a window of lines and one number: the
        // deepest the sea comes inland anywhere in that window. Put the town's
        // seaward edge COAST_REACH tiles out from there and it stands exactly
        // COAST_REACH tiles over the water at that line, and a little less
        // along the rest of its edge as the coastline wanders back out.
        //
        // This replaced a search for tiles on the waterline that hung a
        // footprint corner on each one. A corner is where it put the tile it
        // had found, so it quietly required the deepest point of the coast to
        // fall on the very first or very last line of the town — true on some
        // seeds, false on plenty of others, and the ones where it was false got
        // a town reaching a few tiles short or no coastal town at all. Asking
        // the coast its shape answers that for every window at once.
        {
            static int wl[MAP_HEIGHT];   // MAP_WIDTH == MAP_HEIGHT
            const int lines = (sea_dx != 0) ? MAP_HEIGHT : MAP_WIDTH;
            const int depth = (sea_dx != 0) ? MAP_WIDTH  : MAP_HEIGHT;
            for (int i = 0; i < lines; i++) {
                // Start on the wet edge of the map and walk inland, against the
                // way the sea lies.
                int x = (sea_dx > 0) ? MAP_WIDTH  - 1 : (sea_dx < 0) ? 0 : i;
                int y = (sea_dy > 0) ? MAP_HEIGHT - 1 : (sea_dy < 0) ? 0 : i;
                int n = 0;
                while (n < depth && map->tiles[y][x] == TILE_WATER) {
                    n++; x -= sea_dx; y -= sea_dy;
                }
                wl[i] = n;
            }

            std::vector<std::pair<int,int>> shore;      // windows with nothing wrong with them
            std::vector<std::pair<int,int>> any_coast;  // every window actually on the coast
            shore.reserve(lines);
            any_coast.reserve(lines);
            ShoreTally tally = {};
            tally.relaxed_cost = -1;   // set only if the relaxed path is taken
            const int span = (sea_dx != 0) ? TOWN_H : TOWN_W;
            for (int i0 = 0; i0 + span <= lines; i0++) {
                tally.windows++;
                int deepest = 0;
                for (int k = 0; k < span; k++)
                    if (wl[i0+k] > deepest) deepest = wl[i0+k];
                if (deepest == 0) { tally.no_coast++; continue; }  // no coast in this window

                int tx, ty;
                if      (sea_dx < 0) { tx = deepest - COAST_REACH;                        ty = i0; }
                else if (sea_dx > 0) { tx = MAP_WIDTH  - deepest + COAST_REACH - TOWN_W;  ty = i0; }
                else if (sea_dy < 0) { ty = deepest - COAST_REACH;                        tx = i0; }
                else                 { ty = MAP_HEIGHT - deepest + COAST_REACH - TOWN_H;  tx = i0; }

                // A town-width margin is kept off every map edge except the one
                // the sea is on. On that side the town is meant to end up at
                // the water, and the ocean band is usually far narrower than a
                // town is wide, so demanding the margin there demanded the sea
                // flood TOWN_W + COAST_REACH tiles inland before a coastal
                // town could exist at all -- an inland town's rule, applied to
                // the one town whose whole business is the edge of the map.
                // Requiring only that the footprint stay on the map leaves
                // exactly the condition that matters: deepest >= COAST_REACH,
                // or the strip would hang off the wet edge.
                // Along the joined axis -- which is the coast's own axis --
                // the only edge is the seam, and the town need only not
                // straddle it.
                const int lo_x = (sea_dx < 0) ? 0 : margin_x(TOWN_W);
                const int lo_y = (sea_dy < 0) ? 0 : margin_y(TOWN_H);
                const int hi_x = (sea_dx > 0) ? MAP_WIDTH  : MAP_WIDTH  - margin_x(TOWN_W);
                const int hi_y = (sea_dy > 0) ? MAP_HEIGHT : MAP_HEIGHT - margin_y(TOWN_H);
                if (tx < lo_x || ty < lo_y ||
                    tx + TOWN_W > hi_x || ty + TOWN_H > hi_y) { tally.bounds++; continue; }
                int ddx = tx - cx, ddy = ty - cy;
                if (ddx*ddx + ddy*ddy <= (hw+TOWN_H)*(hw+TOWN_H)) { tally.near_town0++; continue; }
                any_coast.push_back({tx, ty});
                if (coastal_cost(tx, ty, 0) > 0) { tally.unclean++; continue; }
                shore.push_back({tx, ty});
            }
            tally.kept    = (int)shore.size();
            tally.coastal = (int)any_coast.size();

            // Nothing clean, but there is a coast. Take the least bad window
            // rather than the fallback: a coastal town that is not on the coast
            // is in the wrong place, and a town that levelled some cliff to get
            // there is merely on awkward ground. The full count is only paid on
            // the seeds that need it -- where a clean window exists the cheap
            // early-outs above have already found it.
            if (shore.empty() && !any_coast.empty()) {
                // Kept rather than recomputed: this is the one path that pays
                // the full count, and asking twice would pay it twice.
                std::vector<int> cost(any_coast.size());
                int best = -1;
                for (size_t i = 0; i < any_coast.size(); i++) {
                    cost[i] = coastal_cost(any_coast[i].first, any_coast[i].second, INT_MAX);
                    if (best < 0 || cost[i] < best) best = cost[i];
                }
                for (size_t i = 0; i < any_coast.size(); i++)
                    if (cost[i] == best) shore.push_back(any_coast[i]);
                // Every window in `shore` cost `best`, so any of them says it.
                tally.relaxed_cost = best;
            }
            GEN_SHORE(tally);

            if (!shore.empty()) {
                unsigned int ts = seed ^ 0xC0A57001u;
                ts = ts * 1664525u + 1013904223u;
                int idx = (int)((ts >> 16) % (unsigned)shore.size());
                stamp_town_blueprint(map, 1, shore[idx].first, shore[idx].second);
            } else {
                // Reached only by a world with no coast a town can stand on at
                // all -- an ocean shallower than COAST_REACH everywhere along
                // it. Any coast at all is handled above, however rough, so this
                // is no longer the answer to "the coast was untidy". Better
                // inland than missing.
                int fx, fy;
                if (scan_any_footprint(fx, fy, 0, 1)) stamp_town_blueprint(map, 1, fx, fy);
                else                                  map->towns[1] = { -1, -1, 1 };
            }
        }

        // -- Town 2: random walkable location, far from towns 0 and 1 --
        {
            const int MIN_TOWN_DIST = 600;
            unsigned int ts = seed ^ 0xF4EE7002u;
            bool placed = false;
            for (int attempt = 0; attempt < 50000 && !placed; attempt++) {
                ts = ts * 1664525u + 1013904223u;
                int tx = roll_span(ts >> 16, MAP_WIDTH,  TOWN_W, margin_x(TOWN_W));
                ts = ts * 1664525u + 1013904223u;
                int ty = roll_span(ts >> 16, MAP_HEIGHT, TOWN_H, margin_y(TOWN_H));
                int ddx = tx - cx, ddy = ty - cy;
                if (ddx*ddx + ddy*ddy <= (hw+TOWN_H)*(hw+TOWN_H)) continue;
                if (!footprint_ok(tx, ty)) continue;
                bool far_enough = true;
                for (int i = 0; i < 2 && far_enough; i++) {
                    if (map->towns[i].x < 0) continue;
                    int ddx2 = wrap_dx(map->towns[i].x - tx);
                    int ddy2 = wrap_dy(map->towns[i].y - ty);
                    if (ddx2*ddx2 + ddy2*ddy2 < MIN_TOWN_DIST*MIN_TOWN_DIST)
                        far_enough = false;
                }
                if (!far_enough) continue;
                stamp_town_blueprint(map, 2, tx, ty);
                placed = true;
            }
            // Six hundred tiles of separation is a preference, not a
            // requirement. Loosen it a step at a time rather than lose the town,
            // and fall back to anywhere at all if even that finds nothing.
            if (!placed) {
                int fx, fy;
                const int relax[] = { 400, 250, 120, 0 };
                for (int r = 0; r < 4 && !placed; r++)
                    if (scan_any_footprint(fx, fy, relax[r], 2)) {
                        stamp_town_blueprint(map, 2, fx, fy);
                        placed = true;
                    }
            }
            if (!placed) map->towns[2] = { -1, -1, 2 };
        }
    }

    GEN_STAGE(map, "before Villages");
    // --- Villages ---
    // Twelve small settlements. Dungeons are allowed inside village
    // footprints: the stamp fills the footprint with the placeholder tile,
    // and door_ok accepts that tile.
    //
    // Where they stand is a preference with a floor, not luck and not a
    // quota. The rolls used to be uniform over the inland map with no biome
    // test, so a world's villages went wherever the dice fell and nothing
    // promised a snowfield or a desert one. Now every ground gets one first,
    // and each of the rest has its ground DRAWN from the table's weights --
    // the open flats most often, forest, desert and snow alike, the
    // wasteland least -- and is then given a site on that ground. Drawing
    // the ground first, rather than rolling a site and keeping it by its
    // ground, is what makes every split reachable: rolled sites fall two
    // thirds on the flats whatever the weights say, and a world with three
    // villages in the desert could never come up. Now it can, and the counts
    // differ from world to world; only the floor is fixed. The biome is what
    // biome_of() reads at the footprint's centre, before the stamp covers it.
    {
        struct VillageGround { int biome; int weight; };   // weight: share of the draws
        static const VillageGround GROUND[] = {
            { TILE_GRASS,    16 },   // open flat ground, meadow included
            { TILE_TREE,      4 },   // forest
            { TILE_SAND,      4 },
            { TILE_SNOW,      4 },
            { TILE_WASTELAND, 1 },
        };
        const int NG = (int)(sizeof(GROUND) / sizeof(GROUND[0]));
        const int TARGET_VILLAGES   = 12;
        const int MIN_VILLAGE_DIST  = 150; // village-to-village (TL corner distance)
        const int MIN_TOWN_VIL_DIST = 300; // village-to-town
        const int MARGIN = 450; // ocean band is up to ~420 tiles wide; keep villages inland
        static_assert(sizeof(map->villages) / sizeof(map->villages[0]) >= 12,
                      "the village array is smaller than TARGET_VILLAGES");

        // Ground a village can stand on: no water, no lava, no pond, no cliff
        // of any kind -- the tops by their ids, the faces by the mask, since a
        // face is drawn over ordinary ground and the id under it says nothing.
        auto village_footprint_ok = [&](int tx, int ty) -> bool {
            for (int dy = 0; dy < VILLAGE_H; dy++)
                for (int dx = 0; dx < VILLAGE_W; dx++) {
                    int bt = map->tiles[ty+dy][tx+dx];
                    if (bt == TILE_WATER || bt == TILE_RIVER ||
                        bt == TILE_LAVA  || bt == TILE_POND) return false;
                    if (is_cliff(bt)) return false;
                    if (tilemap_face_at(tx+dx, ty+dy)) return false;
                }
            return true;
        };
        auto ground_of = [&](int biome) {
            for (int g = 0; g < NG; g++) if (GROUND[g].biome == biome) return g;
            return 0;   // anything else counts as the flats
        };
        // Every test but the ground's, with the clearances as given so the
        // floor below can relax them.
        auto site_ok = [&](int tx, int ty, int vil_dist, int town_dist) -> bool {
            if (tx < margin_x(1) || ty < margin_y(1) ||
                tx + VILLAGE_W > MAP_WIDTH  - margin_x(2) ||
                ty + VILLAGE_H > MAP_HEIGHT - margin_y(2))
                return false;
            int ddx = tx - cx, ddy = ty - cy;
            if (ddx*ddx + ddy*ddy <= (hw+VILLAGE_H)*(hw+VILLAGE_H)) return false;  // the hub
            if (!village_footprint_ok(tx, ty)) return false;
            for (int i = 0; i < 3; i++) {
                if (map->towns[i].x < 0) continue;
                int dx2 = wrap_dx(map->towns[i].x - tx), dy2 = wrap_dy(map->towns[i].y - ty);
                if (dx2*dx2 + dy2*dy2 < town_dist*town_dist) return false;
            }
            for (int i = 0; i < map->num_villages; i++) {
                int dx2 = wrap_dx(map->villages[i].x - tx), dy2 = wrap_dy(map->villages[i].y - ty);
                if (dx2*dx2 + dy2*dy2 < vil_dist*vil_dist) return false;
            }
            return true;
        };
        auto site_biome = [&](int tx, int ty) {
            return biome_of(map, tx + VILLAGE_W / 2, ty + VILLAGE_H / 2);
        };

        map->num_villages = 0;
        unsigned int vs = seed ^ 0xA71B4C03u;
        // The inland margin is about the ocean, so it is kept only off the
        // hard borders; along the joined axis a village may stand anywhere
        // it fits, the seam included.
        auto roll_site = [&](int margin, int& tx, int& ty) {
            vs = vs * 1664525u + 1013904223u;
            tx = roll_span(vs >> 16, MAP_WIDTH,  VILLAGE_W, margin_x(margin));
            vs = vs * 1664525u + 1013904223u;
            ty = roll_span(vs >> 16, MAP_HEIGHT, VILLAGE_H, margin_y(margin));
        };
        auto place = [&](int tx, int ty, int biome) {
            vs = vs * 1664525u + 1013904223u;
            int variant = (int)((vs >> 16) % NUM_VILLAGE_VARIANTS);
            stamp_village_blueprint(map, variant, tx, ty, biome);
        };

        // A village on a given ground. Rolled first, so it lands somewhere as
        // random as the rest; if twenty thousand rolls never hit a footprint
        // that fits on that ground -- the wasteland is a fiftieth of the map,
        // and the coast biomes mostly lie outside the inland margin -- walk
        // the whole map in shuffled 150-tile cells for the first site that
        // fits, and if none fits at the usual clearances, again at half and
        // at a quarter: the earlier biome guarantee only promises a patch,
        // not a wide one. Returns whether it found anywhere at all.
        auto place_on = [&](int g) -> bool {
            int want = GROUND[g].biome;
            for (int attempt = 0; attempt < 20000; attempt++) {
                int tx, ty; roll_site(MARGIN, tx, ty);
                if (site_biome(tx, ty) != want) continue;
                if (!site_ok(tx, ty, MIN_VILLAGE_DIST, MIN_TOWN_VIL_DIST)) continue;
                place(tx, ty, want);
                return true;
            }
            const int CELL = 150, EDGE = 32;
            const int GW = (MAP_WIDTH - 2*EDGE) / CELL, GH = (MAP_HEIGHT - 2*EDGE) / CELL;
            std::vector<int> cells(GW * GH);
            for (int i = 0; i < GW * GH; i++) cells[i] = i;
            for (int i = GW * GH - 1; i > 0; i--) {
                vs = vs * 1664525u + 1013904223u;
                int j = (int)((vs >> 16) % (unsigned)(i + 1));
                std::swap(cells[i], cells[j]);
            }
            for (int relax = 0; relax < 3; relax++) {
                int vd = MIN_VILLAGE_DIST >> relax, td = MIN_TOWN_VIL_DIST >> relax;
                for (int ci : cells) {
                    int x0 = EDGE + (ci % GW) * CELL, y0 = EDGE + (ci / GW) * CELL;
                    for (int ty = y0; ty < y0 + CELL; ty += 3)
                        for (int tx = x0; tx < x0 + CELL; tx += 3) {
                            if (site_biome(tx, ty) != want) continue;
                            if (!site_ok(tx, ty, vd, td)) continue;
                            place(tx, ty, want);
                            return true;
                        }
                }
            }
            return false;
        };

        // The floor: one on each ground, before anything is drawn.
        for (int g = 0; g < NG; g++) place_on(g);

        // The rest: draw the ground by weight, then find it a site. A ground
        // with nowhere left to stand gives its draw to the flats rather than
        // leave the world a village short.
        int total_w = 0;
        for (int g = 0; g < NG; g++) total_w += GROUND[g].weight;
        while (map->num_villages < TARGET_VILLAGES) {
            vs = vs * 1664525u + 1013904223u;
            int roll = (int)((vs >> 16) % (unsigned)total_w), g = NG - 1;
            for (int i = 0; i < NG; i++) { roll -= GROUND[i].weight; if (roll < 0) { g = i; break; } }
            if (!place_on(g) && !place_on(ground_of(TILE_GRASS))) break;
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

        // -- Castle 1: mountain — nearest top-level footprint to cliff peak --
        // Collects all top-level plateau tiles, sorts by distance from
        // cliff_peak, then walks the sorted list — O(N log N) on just those
        // tiles rather than O((W+H)^2) ring expansion over the whole map.
        //
        // The top level is CLIFF_LEVELS, which is three. This asked for
        // elevation five, and elevation five is not a thing the world has: the
        // single site that writes a cliff body clamps its level to CLIFF_LEVELS,
        // so ids 4 and 5 of each family are never written and the list this
        // sorted was empty on every seed. The castle has therefore never once
        // placed, and map->castles[1] has always kept the {-1,-1} that phase1
        // leaves in it. Asking for the highest ground that exists is what makes
        // the feature do what its comment in include/castles.h says.
        {
            // cliff_peak is in tiles already. This divided it by TILE_SIZE
            // again, which put the target near the map's origin corner and
            // sent the castle to whatever high ground lay nearest THAT.
            float px = map->cliff_peak_x;
            float py = map->cliff_peak_y;

            // Open plateau surface, at one level. The tile id alone is not
            // enough: a level's band is drawn over the tops of the levels below
            // it, and the id of a tile says nothing about what lands on top of
            // it, so a footprint chosen on ids alone can sit half inside the
            // wall of the level above. tilemap_face_at is the low bits of the
            // face mask — every tile any part of a cliff could close.
            auto is_open_top = [&](int x, int y, int lvl) {
                return cliff_level_of(map->tiles[y][x]) == lvl && !tilemap_face_at(x, y);
            };

            // Walk down from the top of the world until a level can hold it.
            //
            // The top of the world alone is not enough ground. Level 3 exists on
            // every seed but it is small and ragged — measured across ten seeds,
            // between 900 and 6500 open tiles, and its largest square block of
            // open surface runs 10 to 14 tiles. A castle is 16x16, so it simply
            // does not fit, and asking only level 3 placed the castle on four
            // seeds in ten. Level 2 offers an 18x18 on every seed tried and
            // level 1 a 22x22, so stepping down finds a site essentially always
            // while still putting the castle on the highest ground that can
            // actually carry it — which is what "perched at the world's highest
            // peak" has to mean once the peak turns out to be a ridge.
            //
            // Widening the search instead — a smaller footprint, or allowing the
            // band to cross the walls — was the other way to make it fit, and
            // both change what the castle is rather than where it stands.
            for (int lvl = CLIFF_LEVELS; lvl >= 1 && map->castles[1].x < 0; lvl--) {
                std::vector<std::pair<float,std::pair<int,int>>> top_tiles;
                for (int y = 0; y < MAP_HEIGHT; y++) {
                    for (int x = 0; x < MAP_WIDTH; x++) {
                        if (!is_open_top(x, y, lvl)) continue;
                        float dx = wrap_dpx((x - px) * TILE_SIZE) / TILE_SIZE;
                        float dy2 = wrap_dpy((y - py) * TILE_SIZE) / TILE_SIZE;
                        top_tiles.push_back({ dx*dx + dy2*dy2, {x, y} });
                    }
                }
                std::sort(top_tiles.begin(), top_tiles.end());

                for (auto& entry : top_tiles) {
                    int tx = entry.second.first  - CASTLE_W / 2;
                    int ty = entry.second.second - CASTLE_H / 2;
                    if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                    bool all_flat = true;
                    for (int cdy = 0; cdy < CASTLE_H && all_flat; cdy++)
                        for (int cdx = 0; cdx < CASTLE_W && all_flat; cdx++)
                            if (!is_open_top(tx + cdx, ty + cdy, lvl)) all_flat = false;
                    if (!all_flat) continue;
                    stamp_castle_blueprint(map, 1, tx, ty);
                    break;
                }
            }

            // No plateau holds it. The islands are Mother 1's, a dozen or
            // two tiles across with plateaus smaller than that, and the
            // library has no square of open top sixteen tiles on a side --
            // the drawings' walls cannot close round one. So the castle
            // stands on the flat among the islands instead, as near the
            // peak as open ground allows: the highest country there is,
            // if not the highest ground. Rings out from the peak, the
            // footprint's corner stepping four tiles at a time.
            if (map->castles[1].x < 0) {
                auto is_open_flat = [&](int x, int y) {
                    if (!in_world(&x, &y)) return false;
                    int t = map->tiles[y][x];
                    return (t == TILE_GRASS || t == TILE_SNOW || t == TILE_WASTELAND)
                        && !s_cliff_elev[y][x] && !tilemap_face_at(x, y) && !water_keepout[y][x];
                };
                int pcx = (int)px, pcy = (int)py;
                if (pcx < 0) pcx = 0; if (pcx >= MAP_WIDTH)  pcx = MAP_WIDTH - 1;
                if (pcy < 0) pcy = 0; if (pcy >= MAP_HEIGHT) pcy = MAP_HEIGHT - 1;
                bool done = false;
                for (int r = 0; r < MAP_WIDTH / 2 + MAP_HEIGHT / 2 && !done; r += 4) {
                    for (int dy = -r; dy <= r && !done; dy += 4)
                        for (int dx = -r; dx <= r && !done; dx += 4) {
                            if (dx != -r && dx != r && dy != -r && dy != r) continue;   // the ring only
                            int tx = pcx + dx - CASTLE_W / 2, ty = pcy + dy - CASTLE_H / 2;
                            if (tx < 0 || ty < 0 || tx + CASTLE_W > MAP_WIDTH || ty + CASTLE_H > MAP_HEIGHT) continue;
                            bool ok = true;
                            for (int cdy = 0; cdy < CASTLE_H && ok; cdy++)
                                for (int cdx = 0; cdx < CASTLE_W && ok; cdx++)
                                    if (!is_open_flat(tx + cdx, ty + cdy)) ok = false;
                            if (!ok) continue;
                            stamp_castle_blueprint(map, 1, tx, ty);
                            done = true;
                        }
                }
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
                        if (!in_world(&nx, &ny)) return false;
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
                        // The seam is not an edge: a ring may run over it.
                        if ((!wrapx() && (tx + CASTLE_W / 2 - MOAT_REACH < 0 ||
                                          tx + CASTLE_W / 2 + MOAT_REACH >= MAP_WIDTH)) ||
                            (!wrapy() && (ty + CASTLE_H / 2 - MOAT_REACH < 0 ||
                                          ty + CASTLE_H / 2 + MOAT_REACH >= MAP_HEIGHT))) continue;
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
    // biome at its placement position, drawn among that biome's native types by
    // how far each is from its per-world target (include/dungeon_kinds.h).
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
        // `min_lvl` is the lowest plateau storey whose top may carry a door, and
        // `near_from` is the first entrance index the MIN_DIST test applies to.
        //
        // Both exist for the cave systems and both default to today's behaviour.
        // A cave's mouths sit on the tops of levels 1 and 2 as well as 3, and
        // they sit on one mountain a few tiles apart — so against each other
        // MIN_DIST is exactly the wrong question, while against every entrance
        // placed before the system started it is still the right one. Passing
        // the index the system began at says that in one number.
        // `allow_tree` lets the footprint stand on ordinary forest trees. Only
        // the large tree asks for it: it IS a tree, so the ones it replaces
        // are the point rather than an obstacle, and without this a forest
        // that is 85% trees has almost nowhere to put one.
        auto door_ok_ex = [&](int ex, int ey, int sz, int min_lvl, int near_from,
                              bool allow_tree = false) -> bool {
            if (ex < margin_x(MARGIN) || ey < margin_y(MARGIN) ||
                ex + sz + margin_x(MARGIN) > MAP_WIDTH ||
                ey + sz + margin_y(MARGIN) > MAP_HEIGHT)
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
                        // Allow flat biome tiles and cliff tops at or above min_lvl
                        int blvl = cliff_level_of(base);
                        bool cliff_top = (blvl >= min_lvl && blvl > 0);
                        if (!cliff_top &&
                            base != TILE_GRASS     && base != TILE_MEADOW &&
                            base != TILE_SAND      && base != TILE_SNOW   &&
                            base != TILE_WASTELAND) return false;
                        int ovl = map->overlay[ty][tx];
                        if (ovl != 0 && !(allow_tree && ovl == TILE_TREE)) return false;
                    }
                }
            }
            for (int i = 0; i < near_from && i < map->num_dungeon_entrances; i++) {
                // A cave system is one dungeon with several ways in, so its
                // mouths do not each reserve a dungeon's worth of map. Counting
                // them separately is what emptied the world: two hundred mouths
                // times a 130-tile exclusion is most of the land, and ordinary
                // dungeons fell from about 290 to 170. They are still kept clear
                // by the sixteen-tile cliff keep-out, which every mouth sits
                // inside by construction.
                if (map->dungeon_entrances[i].cave_anchor_x >= 0) continue;
                int ddx = wrap_dx(map->dungeon_entrances[i].x - ex);
                int ddy = wrap_dy(map->dungeon_entrances[i].y - ey);
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
                int nx = wrap_dx((ex + sz / 2) - mx), ny = wrap_dy((ey + sz / 2) - my);
                int keep = MOAT_REACH + sz;
                if (nx*nx + ny*ny <= keep * keep) return false;
            }
            return true;
        };
        // Every ordinary entrance: level-3 tops only, and MIN_DIST against all.
        auto door_ok = [&](int ex, int ey, int sz, DungeonEntranceType t) -> bool {
            return door_ok_ex(ex, ey, sz, 3, map->num_dungeon_entrances,
                              t == DUNGEON_ENT_LARGE_TREE);
        };

        // ── Cave systems ────────────────────────────────────────────────────
        //
        // A mountain gets one cave, with a mouth cut into the foot of its
        // level-1 south wall and another on the top of each storey it has. All
        // of them open the same interior, because the seed is taken from the
        // landform rather than from each mouth — see cave_anchor_x in
        // include/tilemap.h and the branch in src/main.cpp.

        // Whether an entrance would sit in a hill rather than beside one.
        //
        // This was a sixteen-tile keep-out, and it was doing far more than the
        // job it was added for. Highland is about eight percent of the map, so a
        // sixteen-tile skirt round every scrap of it reserved something like a
        // quarter of the world: every one of six hundred hills became the centre
        // of a zone where nothing could spawn, while only eighty of them had a
        // cave. That is what made the place read as barren.
        //
        // What the rule is actually for is narrower. An entrance must not end up
        // inside the hill, and must not end up behind the wall hanging off it —
        // the band is never written to the map, so ground under a face still
        // reads TILE_GRASS and passes every test door_ok makes. Ask those two
        // questions and nothing else: s_cliff_elev for the hill itself, and
        // tilemap_face_at, which is the low face bits and answers exactly "is a
        // wall drawn on this tile". A graveyard may stand at the foot of a cliff
        // again; it just may not stand in one.
        auto hits_cliff = [&](int ex, int ey, int sz) -> bool {
            for (int py = ey; py < ey + sz; py++)
                for (int px = ex; px < ex + sz; px++) {
                    if (px < 0 || py < 0 || px >= MAP_WIDTH || py >= MAP_HEIGHT) continue;
                    if (s_cliff_elev[py][px]) return true;
                    if (tilemap_face_at(px, py)) return true;
                }
            return false;
        };

        // Which landforms already carry a cave. s_cliff_scratch is dead by this
        // point in generation — the last pass to touch it was inside
        // place_cliffs — so it is free to mark up, and marking the landform's
        // own tiles is what makes "one system per mountain" true by
        // construction rather than by a distance test.
        s_cave_seen = s_cave_sealed = s_cave_placed = 0;
        s_cave_sealed_tiles = s_cave_placed_tiles = 0;
        for (int py = 0; py < MAP_HEIGHT; py++)
            for (int px = 0; px < MAP_WIDTH; px++)
                s_cliff_scratch[py][px] = 0;

        static int cave_cells[1 << 20];
        const int CAVE_CAP = (int)(sizeof cave_cells / sizeof *cave_cells);

        // The foot of the south wall below a plateau tile: the last row of
        // rock under it, or -1 where the wall below is not rock at all.
        // Bounded, since a band is a few rows deep, so this is a short walk
        // and not a search.
        auto rock_at = [&](int fx, int fy) -> bool {
            int c = (fx >= 0 && fy >= 0 && fx < MAP_WIDTH && fy < MAP_HEIGHT) ? (int)s_island_cell[fy][fx] : 0;
            return c && ISLAND_KIND[c] == 1;
        };
        auto face_foot = [&](int fx, int fy) -> int {
            int foot = -1;
            for (int d = 0; d <= 4; d++) {
                int ty = fy + d;
                if (ty >= MAP_HEIGHT || !rock_at(fx, ty)) break;
                foot = ty;
            }
            return foot;
        };

        // Cut a cave system into the mountain nearest (sx,sy), if there is one
        // worth cutting. Returns whether it placed anything.
        // Take one landform, decide whether it carries a cave, and cut the
        // mouths if it does. (bx,by) is any unvisited highland tile of it.
        auto cave_place = [&](Tilemap* m, int bx, int by) -> bool {
            // Walk the whole landform. Eight-connected, as the region cleanups
            // in place_cliffs are, so "one mountain" means the same thing here
            // as it does there. Marking every cell is what makes one system per
            // mountain true by construction rather than by a distance test.
            int n = 0, head = 0, top_lvl = 0, ax = bx, ay = by;
            bool holds_castle = false, sealed = false;
            s_cave_seen++;
            // The castle stamps map->tiles but never s_cliff_elev, so its
            // footprint is still part of the landform as far as this walk is
            // concerned — which is what lets the mountain be recognised as the
            // one the castle stands on.
            int c1x = m->castles[1].x, c1y = m->castles[1].y;
            cave_cells[n++] = by * MAP_WIDTH + bx;
            s_cliff_scratch[by][bx] = 1;
            while (head < n) {
                int v = cave_cells[head++], vy = v / MAP_WIDTH, vx = v % MAP_WIDTH;
                if (s_cliff_elev[vy][vx] > top_lvl) top_lvl = s_cliff_elev[vy][vx];
                if (s_cliff_face[vy][vx] & CLIFF_FACE_SEALED) sealed = true;
                if (vy < ay || (vy == ay && vx < ax)) { ax = vx; ay = vy; }
                if (c1x >= 0 && vx >= c1x && vx < c1x + CASTLE_W &&
                                vy >= c1y && vy < c1y + CASTLE_H) holds_castle = true;
                for (int dy = -1; dy <= 1; dy++)
                    for (int dx = -1; dx <= 1; dx++) {
                        int px = vx + dx, py = vy + dy;
                        if (!in_world(&px, &py)) continue;
                        if (!s_cliff_elev[py][px] || s_cliff_scratch[py][px]) continue;
                        s_cliff_scratch[py][px] = 1;
                        if (n < CAVE_CAP) cave_cells[n++] = py * MAP_WIDTH + px;
                    }
            }
            // A cave carries the player between elevations. Every top of this
            // mountain has a way up on foot -- the library says so of the
            // landform, per pixel of its walls -- so there is nothing here to
            // carry them between, and no cave.
            if (!sealed) return false;
            s_cave_sealed++;
            s_cave_sealed_tiles += n;

            // Whether this mountain has a cave, by how many storeys it carries:
            // every three-storey mountain, half of the rest. Hashed off the world seed
            // and the landform's own anchor rather than drawn from the placement
            // RNG, so the answer is the same however the rolls around it fall,
            // and the same on every rebuild of the seed.
            //
            // And the mountain holding castle 1 always has one, whatever it
            // rolled: the cave is how the player gets up to the castle.
            unsigned int h = (unsigned int)seed
                           ^ ((unsigned int)ax * 0x9E3779B9u)
                           ^ ((unsigned int)ay * 0x85EBCA6Bu);
            h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12;
            int pct = (int)((h >> 8) % 10000u);
            // The chance grows with the mountain: its raised tiles over the
            // raised tiles of every sealed mountain, times CAVE_SYSTEMS_TARGET,
            // so the caves add up to the target over the world -- which is
            // what the kinds table asks of it, and no more: at half of the
            // mountains, the caves alone filled MAX_DUNGEON_ENTRANCES and every
            // other kind was starved -- and a tableland is far likelier to
            // carry one than a knoll. In hundredths of a percent: a share of
            // a few percent would lose a third of itself to whole-percent
            // rounding.
            long long want = s_island_sealed_tiles > 0
                           ? (10000LL * CAVE_SYSTEMS_TARGET * n) / s_island_sealed_tiles : 5000;
            if (want < 1) want = 1;
            if (want > 10000 || top_lvl >= 3) want = 10000;
            if (pct >= want && !holds_castle) return false;

            int first = m->num_dungeon_entrances;

            // The way in: the mouth, drawn over the foot of a level-1 south
            // wall -- a plateau tile with rock straight below it, the band
            // hanging off the island's edge. The mouth is three cells wide
            // and two tall, and the whole of it lies on rock: the middle
            // column is the one found, the columns either side must carry the
            // same wall to the same foot, and the ground under all three is
            // walkable, so the opening in the bottom middle can be walked
            // into. (mx, my) is that opening; the sprite's top-left is one
            // column left and one row up.
            int mx = -1, my = -1;
            for (int i = 0; i < n && mx < 0; i++) {
                int lx = cave_cells[i] % MAP_WIDTH, ly = cave_cells[i] / MAP_WIDTH;
                if (s_cliff_elev[ly][lx] != 1) continue;          // level-1 top only
                if (ly + 1 >= MAP_HEIGHT || s_cliff_elev[ly+1][lx] >= 1) continue;
                if (lx - 1 < 0 || lx + 1 >= MAP_WIDTH) continue;

                int foot = face_foot(lx, ly + 1);
                if (foot < 0) continue;
                if (foot - 1 <= ly) continue;                      // needs two rows of wall to sit on
                bool ok = true;
                for (int c = -1; c <= 1 && ok; c++) {
                    // the same foot in every column, and rock on both rows above it
                    if (face_foot(lx + c, ly + 1) != foot) ok = false;
                    else if (!rock_at(lx + c, foot - 1) || !rock_at(lx + c, foot)) ok = false;
                    // and ground you can walk up to it on, all along the sprite
                    else if (foot + 1 >= MAP_HEIGHT || !tilemap_is_walkable(map, lx + c, foot + 1)) ok = false;
                }
                if (!ok) continue;

                if (!door_ok_ex(lx, foot, 1, 1, first)) continue;
                mx = lx; my = foot;
            }
            if (mx < 0) return false;   // no south wall to put a mouth in

            float fdx = (float)(mx - MAP_WIDTH / 2), fdy = (float)(my - MAP_HEIGHT / 2);
            float mdist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                                (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
            // One difficulty for the whole system: the mouths open the same
            // cave, and difficulty is carried into its loot.
            float cave_diff = ((sqrtf(fdx*fdx + fdy*fdy) / mdist) + (float)top_lvl / 5.0f) * 0.5f;

            // Stamping a mouth: the tile, and then the cliff's own collision
            // bits cleared off it. The band is solid per pixel and is tested
            // before the tile id is ever looked at, so without this the player
            // is walled out of the mouth they are standing in.
            auto stamp_mouth = [&](int tx, int ty, int size, int lvl) {
                int s = size + 1;
                for (int r = 0; r < s; r++)
                    for (int c = 0; c < s; c++) {
                        m->tiles[ty + r][tx + c]   = TILE_DUNGEON_CAVE;
                        m->overlay[ty + r][tx + c] = 0;
                        s_island_cell[ty + r][tx + c] = 0;
                        s_cliff_face[ty + r][tx + c] &=
                            (unsigned char)~((1 << CLIFF_LEVELS) - 1);
                    }
                m->dungeon_entrances[m->num_dungeon_entrances++] = {
                    tx, ty, size, DUNGEON_ENT_CAVE, lvl, cave_diff, 0, -1, ax, ay,
                    biome_of(m, tx, ty)
                };
            };

            // The ground mouth: the opening is one tile, cut as above, and the
            // mound is laid over it and the five wall tiles round it as an
            // overlay. Those five keep their wall -- drawn and solid per pixel
            // -- so the rock the player sees beside the opening is rock.
            stamp_mouth(mx, my, 0, 1);
            for (int dy = 0; dy < CAVE_MOUTH_H; dy++)
                for (int dx = 0; dx < CAVE_MOUTH_W; dx++)
                    m->overlay[my - 1 + dy][mx - 1 + dx] = cave_mouth_cell(dx, dy);
            s_cave_placed++;
            s_cave_placed_tiles += n;

            // And one on the top of every storey the mountain has.
            for (int L = 1; L <= top_lvl; L++) {
                for (int i = 0; i < n; i++) {
                    int tx = cave_cells[i] % MAP_WIDTH, ty = cave_cells[i] / MAP_WIDTH;
                    if (cliff_level_of(m->tiles[ty][tx]) != L) continue;
                    if (tilemap_face_at(tx, ty)) continue;
                    if (!door_ok_ex(tx, ty, 1, 1, first)) continue;
                    stamp_mouth(tx, ty, 0, L);
                    break;
                }
            }
            return true;
        };

        // Every mountain, once, before any ordinary dungeon is rolled. Placing
        // the caves first is what lets the rolls keep MIN_DIST away from the
        // mouths rather than the other way round.
        for (int py = 0; py < MAP_HEIGHT; py++)
            for (int px = 0; px < MAP_WIDTH; px++) {
                if (s_cliff_scratch[py][px] || !s_cliff_elev[py][px]) continue;
                if (map->num_dungeon_entrances + 4 > MAX_DUNGEON_ENTRANCES) continue;
                cave_place(map, px, py);
            }

        // The ordinary rolls get their own budget. num_dungeon_entrances counts
        // the cave mouths too by now, so testing it against TARGET directly
        // would let a world full of mountains spend the whole allowance on
        // caves and leave no graveyards anywhere.
        // How many of each kind this world holds so far, by DUNGEON_KINDS row.
        // The draw reads it to weight each site's natives by how far they are
        // from target; place_entrance is the only writer, so the count and the
        // record can't disagree. Cave rows stay 0 here — cave systems are cut
        // by the pass above and never drawn — and the guarantee pass recounts
        // everything from the records anyway.
        int have_kind[DUNGEON_KIND_COUNT] = {0};

        // Stamp the ground, decorate around it, and record the entrance. Shared
        // by the ordinary rolls and the guarantee pass below so the two cannot
        // drift apart on what placing a dungeon means. The aggregate below is
        // positional and there are three more of them in this file — see the
        // warning on DungeonEntrance in tilemap.h.
        auto place_entrance = [&](int ex, int ey, DungeonEntranceType ent_type,
                                  int ent_size, int cliff_lvl, int biome) {
            int sz = ent_size + 1;

            // Difficulty: straight average of distance-from-center and elevation
            float fdx      = (float)(ex - MAP_WIDTH  / 2);
            float fdy      = (float)(ey - MAP_HEIGHT / 2);
            float dist     = sqrtf(fdx*fdx + fdy*fdy);
            float max_dist = sqrtf((float)(MAP_WIDTH/2)*(MAP_WIDTH/2) +
                                   (float)(MAP_HEIGHT/2)*(MAP_HEIGHT/2));
            float difficulty = ((dist / max_dist) + (float)cliff_lvl / 5.0f) * 0.5f;

            // GRAVEYARD_SM: entrance tile stays hidden under the biome tile.
            // It is revealed when the player destroys the hidden gravestone
            // resource node. All other types stamp their dungeon tile now.
            // Pairing has not run yet at this point; the one it links gets
            // stamped open there, where whether it has a partner is known.
            if (ent_type != DUNGEON_ENT_GRAVEYARD_SM) {
                int tile_id = entrance_tile_id(ent_type);
                for (int r = 0; r < sz; r++)
                    for (int c = 0; c < sz; c++) {
                        map->tiles[ey + r][ex + c]   = tile_id;
                        map->overlay[ey + r][ex + c] = 0;
                    }
            }
            stamp_dungeon_surround(map, ent_type, biome, ex, ey, sz);
            map->dungeon_entrances[map->num_dungeon_entrances++] = {
                ex, ey, ent_size, ent_type, cliff_lvl, difficulty, 0, -1, -1, -1, biome
            };
            int k = dungeon_kind_for_type(ent_type);
            if (k >= 0) have_kind[k]++;
        };

        const int ordinary_first = map->num_dungeon_entrances;

        for (int ci : cells) {
            if (map->num_dungeon_entrances - ordinary_first >= TARGET) break;
            if (map->num_dungeon_entrances >= MAX_DUNGEON_ENTRANCES) break;
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
                int biome     = biome_of(map, ex, ey);

                // Pick entrance type — also determines size for fixed-size
                // archetypes. No draw at all when everything native here is
                // already at target: the next attempt may land on other ground.
                DungeonEntranceType ent_type;
                int ent_size;
                es = es * 1664525u + 1013904223u;
                if (!pick_entrance_type(biome, have_kind, es, ent_type, ent_size)) continue;
                int sz = ent_size + 1; // 1 = small, 2 = large

                // In a hill, not beside one. See hits_cliff.
                if (hits_cliff(ex, ey, sz)) continue;

                if (!door_ok(ex, ey, sz, ent_type)) continue;

                place_entrance(ex, ey, ent_type, ent_size, cliff_lvl, biome);
                break;
            }
        }

        // ── Guarantee every KIND exists somewhere ─────────────────────
        // Which kinds a world gets is decided by which biomes its cells
        // happen to land in, and biome area is luck: measured across 32
        // worlds, three had no pyramid or no oasis at all. Desert survives
        // worldgen only as one or two large blobs (MIN_BIOME_AREA), and a
        // world's 400 cells can simply miss them. A world short a kind is
        // short a whole kind of dungeon, so anything that came out at zero is
        // placed here. Counted over the procedural records only: phase 1's
        // fixed pair would otherwise make a cave and a small graveyard
        // trivially present, which is not the question.
        //
        // A kind is a DUNGEON_KINDS row, so the seven cave materials are
        // seven things to guarantee. A material is a band of cave difficulty,
        // and the rarest band is a few percent of a world's systems — some
        // worlds grow none. There is no mountain to cut a new cave into on
        // demand, so a missing material takes over an existing system
        // instead: the one whose difficulty is nearest the band, moved to the
        // band's bottom edge on every mouth it has. Deterministic, no RNG.
        // Systems with two or more mouths are preferred because a single
        // mouth can be partnered later, and a pair opens at the HARDER end's
        // difficulty (dungeon_wiring_for), which would undo the move.
        //
        // For a non-cave kind: two rounds, and the split is the point. The
        // first considers only sites the type is native to, so a backfilled
        // oasis still stands in desert or snow whenever such a site is free.
        // The second drops that and takes any site that will hold it, which
        // is what makes this a guarantee rather than an attempt — it runs only
        // for a type with nowhere natural left to go.
        {
            int have[DUNGEON_KIND_COUNT] = {0};
            for (int i = DNG_FIXED_ENTRANCES; i < map->num_dungeon_entrances; i++) {
                int k = dungeon_kind_of(&map->dungeon_entrances[i]);
                if (k >= 0) have[k]++;
            }

            unsigned int bs = seed ^ 0x5EEDBAC7u;
            for (int k = 0; k < DUNGEON_KIND_COUNT; k++) {
                if (have[k]) continue;
                const DungeonKindDef& kind = DUNGEON_KINDS[k];

                if (kind.type == DUNGEON_ENT_CAVE) {
                    Material want_m = (Material)kind.material;
                    float lo = material_min_difficulty(want_m);
                    int best = -1; float best_d = 0.0f; bool best_multi = false;
                    for (int i = DNG_FIXED_ENTRANCES; i < map->num_dungeon_entrances; i++) {
                        const DungeonEntrance& e = map->dungeon_entrances[i];
                        if (e.type != DUNGEON_ENT_CAVE || e.cave_anchor_x < 0) continue;
                        // First mouth of its system only: the others carry the
                        // same anchor and difficulty and would tie with it.
                        bool first = true, multi = false;
                        for (int j = DNG_FIXED_ENTRANCES; j < map->num_dungeon_entrances; j++) {
                            if (j == i) continue;
                            const DungeonEntrance& o = map->dungeon_entrances[j];
                            if (o.cave_anchor_x != e.cave_anchor_x ||
                                o.cave_anchor_y != e.cave_anchor_y) continue;
                            multi = true;
                            if (j < i) { first = false; break; }
                        }
                        if (!first) continue;
                        float d = fabsf(e.difficulty - lo);
                        if (best < 0 || (multi && !best_multi) ||
                            (multi == best_multi && d < best_d)) {
                            best = i; best_d = d; best_multi = multi;
                        }
                    }
                    if (best < 0) continue;   // a world with no cave system at all
                    const DungeonEntrance& b = map->dungeon_entrances[best];
                    for (int j = DNG_FIXED_ENTRANCES; j < map->num_dungeon_entrances; j++) {
                        DungeonEntrance& o = map->dungeon_entrances[j];
                        if (o.cave_anchor_x == b.cave_anchor_x &&
                            o.cave_anchor_y == b.cave_anchor_y)
                            o.difficulty = lo;
                    }
                    have[k]++;
                    continue;
                }

                DungeonEntranceType want = kind.type;
                bool placed = false;
                for (int round = 0; round < 2 && !placed; round++) {
                    for (int tries = 0; tries < 4000 && !placed; tries++) {
                        if (map->num_dungeon_entrances >= MAX_DUNGEON_ENTRANCES) break;
                        bs = bs * 1664525u + 1013904223u;
                        int ex = margin_x(MARGIN) + (int)((bs >> 16) % (unsigned)(MAP_WIDTH  - 2*margin_x(MARGIN)));
                        bs = bs * 1664525u + 1013904223u;
                        int ey = margin_y(MARGIN) + (int)((bs >> 16) % (unsigned)(MAP_HEIGHT - 2*margin_y(MARGIN)));

                        int cliff_lvl = cliff_level_of(map->tiles[ey][ex]);
                        bs = bs * 1664525u + 1013904223u;
                        int ent_size = entrance_size_for(want, bs);
                        int sz = ent_size + 1;

                        // Cheapest rejections first: the biome scan is 289 tile
                        // reads and door_ok walks every entrance placed so far.
                        if (hits_cliff(ex, ey, sz)) continue;
                        int biome = biome_of(map, ex, ey);
                        if (round == 0 && !entrance_native_to_biome(biome, want)) continue;
                        if (!door_ok(ex, ey, sz, want)) continue;

                        place_entrance(ex, ey, want, ent_size, cliff_lvl, biome);
                        placed = true;
                    }
                }
            }
        }
    }

    // ── Link a share of every archetype to its closest compatible neighbour ─
    //
    // The share is taken PER ARCHETYPE, as a quota of sites that may end up
    // linked. It used to be a single 25% coin flip per dungeon, and that made a
    // type's chance of a partner scale with its own scarcity twice over: a rare
    // archetype has few compatible sites to find, and each site got exactly one
    // roll and was never revisited. Measured over ten worlds that left the two
    // rarest — stonehenge and catacombs, six-odd sites apiece against eight
    // hundred caves — at 28% linked with three worlds in ten containing no
    // linked stonehenge at all, while the common types drifted up to 43%: the
    // flip fired once per site but a site could also be CHOSEN by a later one,
    // and only a type with hundreds of sites gets that second chance often.
    //
    // A quota says the thing the coin flip was trying to say and says it the
    // same way for every archetype. LINK_SHARE is 0.40 rather than the 0.25 the
    // flip was written for because 0.40 is what the flip actually produced for
    // the types numerous enough for the retries to work — common archetypes keep
    // the density they had, and the scarce ones come up to meet them.
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

        // A mountain with several mouths is already a network of ways in and
        // out of one cave, and a pair link on top of that is a second, louder
        // claim on the same thing: the interior seed comes from the mountain's
        // anchor so every mouth opens one cave, and the binding gives every
        // mouth its own way out, so neither has anywhere left to put a partner.
        // The link was not merely unused -- it used to win the seed, and a
        // partnered mouth opened a different cave from its own siblings. Rather
        // than leave a partner_idx sitting in the data that nothing acts on,
        // such a mouth is not offered for pairing at all. A cave with one mouth
        // pairs like anything else.
        //
        // Counted once here rather than asked per candidate: the scan below is
        // already quadratic in the entrance count and this need not be.
        std::vector<int> system_mouths(n, 1);
        for (int i = 0; i < n; i++) {
            const DungeonEntrance* ei = &map->dungeon_entrances[i];
            if (ei->cave_anchor_x < 0) continue;
            int cnt = 0;
            for (int j = 0; j < n; j++) {
                const DungeonEntrance* ej = &map->dungeon_entrances[j];
                if (ej->cave_anchor_x == ei->cave_anchor_x &&
                    ej->cave_anchor_y == ei->cave_anchor_y) cnt++;
            }
            system_mouths[i] = cnt;
        }

        auto pairable = [&](int idx) {
            const DungeonEntrance* e = &map->dungeon_entrances[idx];
            if (near_start(e)) return false;
            if (system_mouths[idx] >= 2) return false;
            return true;
        };

        // How much of each archetype ends up linked.
        const float LINK_SHARE = 0.40f;

        // Quota of linked SITES per archetype, not of pairs: a link across two
        // scales of the graveyard family spends one from each of the two, so a
        // cross-scale pair cannot quietly overdraw either type's share.
        int quota[DUNGEON_ENT_COUNT] = {0};
        {
            int eligible[DUNGEON_ENT_COUNT] = {0};
            for (int i = 0; i < n; i++) {
                const DungeonEntrance* e = &map->dungeon_entrances[i];
                int t = (int)e->type;
                if (t < 0 || t >= DUNGEON_ENT_COUNT) continue;
                if (!pairable(i)) continue;
                eligible[t]++;
            }
            for (int t = 0; t < DUNGEON_ENT_COUNT; t++) {
                quota[t] = (int)((float)eligible[t] * LINK_SHARE + 0.5f);
                // Two is what one link costs, so an archetype the share rounds
                // below that has no partner anywhere in the world however many
                // sites it grew. Floor at a single link for anything with two
                // sites to spend it on — that is the whole of what a rare
                // archetype needs and it is the same sentence for all nine.
                if (eligible[t] >= 2 && quota[t] < 2) quota[t] = 2;
            }
        }

        for (int oi = 0; oi < n; oi++) {
            int i = order[oi];
            DungeonEntrance* ei = &map->dungeon_entrances[i];
            if (ei->partner_idx != -1) continue;  // already paired
            if (!pairable(i)) continue;            // starting area, or a cave system
            if (quota[(int)ei->type] <= 0) continue;   // this archetype has had its share

            // Find closest unlinked compatible neighbour.
            int best_j = -1, best_d2 = INT_MAX;
            for (int j = 0; j < n; j++) {
                if (j == i) continue;
                DungeonEntrance* ej = &map->dungeon_entrances[j];
                if (ej->partner_idx != -1) continue;
                if (!pairable(j)) continue;        // same two reasons, from the other end
                // Compatible: same type, or any two of the graveyard family,
                // which pair across their three scales.
                bool compat = (ei->type == ej->type) ||
                              (dungeon_is_graveyard(ei->type) &&
                               dungeon_is_graveyard(ej->type));
                if (!compat) continue;
                // Same-type pairing spends two of one quota, so the partner has
                // to be affordable alongside the site already being spent for.
                int need = (ej->type == ei->type) ? 2 : 1;
                if (quota[(int)ej->type] < need) continue;
                int dx = wrap_dx(ei->x - ej->x), dy = wrap_dy(ei->y - ej->y);
                int d2 = dx*dx + dy*dy;
                if (d2 < best_d2) { best_d2 = d2; best_j = j; }
            }

            if (best_j < 0) continue;

            DungeonEntrance* ej = &map->dungeon_entrances[best_j];
            quota[(int)ei->type]--;
            quota[(int)ej->type]--;

            ei->partner_idx = best_j;
            ej->partner_idx = i;
        }

        // A small graveyard hides its mouth under one of its gravestones, and
        // the player is meant to find it by breaking one. That is a fine way IN
        // and no way at all to arrive: coming up the tunnel from its partner
        // put you on open ground with nothing to walk back into, and about half
        // of every catacombs link ends at one of these. A linked one is stamped
        // open here instead — the far end of a passage has to look like a way
        // through from both sides. Solo ones keep the gravestone over the door.
        for (int i = 0; i < n; i++) {
            DungeonEntrance* e = &map->dungeon_entrances[i];
            if (e->type != DUNGEON_ENT_GRAVEYARD_SM || e->partner_idx < 0) continue;
            map->tiles[e->y][e->x]   = TILE_DUNGEON_GRAVEYARD_SM;
            map->overlay[e->y][e->x] = 0;
        }
    }

    // Roads before trails, on purpose: a trail that reaches a road joins it
    // (route_network branches off track of either kind), and a side track
    // branches off the main road, not the main road off a side track. Only the
    // order changed; the moat below is still the last thing to write tiles.
    GEN_STAGE(map, "before Roads");
    // --- Roads between the settlements ---
    //
    // The world is not short of things to find — a cave or a dungeon lies within
    // sixty tiles of anywhere — but nothing lay *between* them, so the fourteen
    // settlements outside the start sat alone on open ground with nothing
    // relating one to another and the place read as items scattered on a
    // field. A road gives travel a direction to follow and takes the player
    // past what they would otherwise walk by.
    //
    // Same router as the wasteland trails: a spanning tree over the settlements,
    // each edge a shortest path that goes round the mountains and bridges the
    // water, then worn into a track rather than ruled as a line.
    //
    // Town 0 is left out of that tree on purpose. It sits on the hub at map
    // centre, ringed by TILE_HUB out to MOAT_REACH, and that ring is not open
    // ground or bridgeable water to road_region/road_gap below — no route can
    // land on it or cross it. Leaving it out of the node list as well means no
    // edge is even aimed at it, so no road runs up to the ring and stops; the
    // starting island and the water around it stay untouched by the network,
    // not just unreachable through it.
    if (!s_gen_cancel) {
        // A road wants less clearance from the edge of its region than a trail
        // does — the "region" here is all the open ground in the world, and its
        // border is the coast and the foot of every cliff, which is exactly
        // where a road has business going.
        const int ROAD_EDGE_CLEARANCE = 2;
        const int ROAD_ENDPOINT_FREE  = 24;   // settlements are wide; let it reach them
        // How far the search walks from a settlement's centre to find open
        // ground to start from. A town is 156 across, so its centre is 78 tiles
        // deep already. Kept generous rather than trimmed to that, since town 0
        // is the one settlement that would need more -- it sits behind its own
        // hub ring -- and it costs nothing to leave the margin sized for a
        // settlement this search will never actually be run on.
        const int ROAD_ANCHOR_SEARCH  = 120;
        // Ten is what a lava stream inside one wasteland needs. Rivers and lake
        // arms are wider than that, and this is the number that decides which
        // settlements are even in the same region: the flood joins ground across
        // a crossing it could build, so anything wider cuts the map in two and
        // the spanning tree is built over the pieces separately. At ten, four
        // seeds gave three to seven separate networks and settlements with no
        // road at all. This is how long a bridge may be, and therefore how much
        // water counts as passable.
        const int ROAD_BRIDGE_MAX = 24;
        // Ground a route must cover between one crossing and the next. Scaling
        // it with the longer span looked right and measured worse -- at ten,
        // two seeds of twenty-two grew a fused deck instead of one, because the
        // cooldown only governs one route's own crossings and what actually
        // fuses is two different roads reaching the same water beside each
        // other. Where three roads meet at a crossing their decks still merge
        // into a slab; it reads as a wide bridge head rather than a fault, and
        // narrowing it would mean refusing deck tiles a road needs to land on.
        const int ROAD_BRIDGE_GAP = 4;

        const CastlePlacement& citadel2 = map->castles[2];
        int mcx = citadel2.x + CASTLE_W / 2, mcy = citadel2.y + CASTLE_H / 2;
        auto road_forbidden = [&](int x, int y) {
            if (citadel2.x < 0) return false;
            int dx = wrap_dx(x - mcx), dy = wrap_dy(y - mcy);
            return dx*dx + dy*dy <= MOAT_REACH * MOAT_REACH;
        };
        // Water is the gap a road bridges, lava is not: a road over a lava
        // channel is a different thing and the wasteland has its own trails.
        auto road_gap = [&](int x, int y) {
            int t = map->tiles[y][x];
            return t == TILE_WATER || t == TILE_RIVER || t == TILE_ROAD_BRIDGE;
        };
        auto road_raw_gap = [&](int x, int y) {
            int t = map->tiles[y][x];
            return t == TILE_WATER || t == TILE_RIVER;
        };
        // Ground a road may run on: open country, and nothing that is already
        // something. Cliffs are excluded outright — a road cannot climb a wall,
        // and a plateau is only enterable from its north side.
        auto road_region = [&](int x, int y) {
            int t = map->tiles[y][x];
            if (t != TILE_GRASS && t != TILE_MEADOW && t != TILE_SAND &&
                t != TILE_SNOW  && t != TILE_WASTELAND &&
                map->route[y][x] != ROUTE_ROAD) return false;
            if (s_cliff_elev[y][x] || tilemap_face_at(x, y)) return false;
            return true;
        };
        // The route stays off the faces (road_region), but the stroke is
        // three wide and its outer tiles land wherever the brush puts them --
        // under a wall, if the route runs a tile from one. Not there.
        auto road_paint_over = [&](int x, int y) {
            int t = map->tiles[y][x];
            if (tilemap_face_at(x, y)) return false;
            return t == TILE_GRASS || t == TILE_MEADOW || t == TILE_SAND ||
                   t == TILE_SNOW  || t == TILE_WASTELAND;
        };

        // Aim at the middle of each settlement. There is nothing better to aim
        // at: every village blueprint is empty and so are towns 1 and 2, so they
        // stamp a placeholder block and no interior. The anchor search then
        // walks out to the nearest open ground, which for a town is its own
        // edge — which is where a road should stop anyway.
        //
        // Town 0 starts the loop at 1, not 0: see the note above the router
        // call for why the starting island is not a node here.
        std::vector<std::pair<int,int>> places;
        for (int i = 1; i < 3; i++)
            if (map->towns[i].x >= 0)
                places.push_back({ map->towns[i].x + TOWN_W / 2,
                                   map->towns[i].y + TOWN_H / 2 });
        for (int i = 0; i < map->num_villages; i++)
            places.push_back({ map->villages[i].x + VILLAGE_W / 2,
                               map->villages[i].y + VILLAGE_H / 2 });

        route_network(map, seed ^ 0x20AD5u, places,
                      road_region, road_gap, road_raw_gap, road_forbidden,
                      road_paint_over, road_paint_over,
                      ROUTE_ROAD, TILE_ROAD_BRIDGE,
                      ROAD_EDGE_CLEARANCE, ROAD_ENDPOINT_FREE, ROAD_ANCHOR_SEARCH,
                      ROAD_BRIDGE_MAX, ROAD_BRIDGE_GAP, true);
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
        const int EDGE_CLEARANCE = 6;      // tiles the trail would rather keep from the border
        const int ENDPOINT_FREE  = 10;     // radius around a dungeon where that is waived
        const int ANCHOR_SEARCH  = 8;      // how far off a dungeon to find ground
        // Ground a trail must cover between one crossing and the next. Four
        // let a trail through a braid of lava streams lay a deck every few
        // tiles -- three or four bridges in a row where the channels ran
        // side by side, which reads as a cluster of bridges rather than a
        // track that happens to cross water. At ten the search has to find a
        // stretch between channels wide enough to walk, or go round.
        const int TRAIL_BRIDGE_GAP = 10;

        // The citadel's moat is the one lava no bridge may span. Crossing it
        // would hand over the way in that the ring exists to withhold.
        const CastlePlacement& citadel = map->castles[2];
        int moat_cx = citadel.x + CASTLE_W / 2, moat_cy = citadel.y + CASTLE_H / 2;
        auto in_moat = [&](int x, int y) {
            if (citadel.x < 0) return false;
            int dx = wrap_dx(x - moat_cx), dy = wrap_dy(y - moat_cy);
            return dx*dx + dy*dy <= MOAT_REACH * MOAT_REACH;
        };
        auto is_lava = [&](int x, int y) {
            int t = map->tiles[y][x];
            return t == TILE_LAVA || t == TILE_WASTE_BRIDGE;
        };

        // Ground a trail can be laid on. Cliffs are excluded here rather than
        // left to the brush: routing over ground that cannot be painted tears
        // a hole in the trail, and mountains are to be gone around anyway.
        auto is_region = [&](int x, int y) {
            int t = map->tiles[y][x];
            // Wasteland, or a stretch of trail already worn across it: a later
            // edge follows a track that is going its way rather than laying a
            // second one beside it. That used to be read off the tile the trail
            // had overwritten; it lives in its own layer now.
            if (t != TILE_WASTELAND && map->route[y][x] != ROUTE_TRAIL) return false;
            if (water_keepout[y][x]) return false;
            // A wall is drawn over the tile: not ground a track can run on,
            // whatever the tile id underneath says. Plateau tops carry their
            // own ids and are excluded by the test above; the faces are the
            // part that needs asking for. Left out of the region they are
            // rim, so the clearance margin keeps the route off them rather
            // than the brush clipping against them.
            if (tilemap_face_at(x, y)) return false;
            if (abs(x - cx) <= guard_r && abs(y - cy) <= guard_r) return false;
            return true;
        };

        // The deck goes over raw lava only, and the trail over bare wasteland.
        auto raw_lava  = [&](int x, int y) { return map->tiles[y][x] == TILE_LAVA; };
        auto paint_over = [&](int x, int y) { return map->tiles[y][x] == TILE_WASTELAND; };

        // Where the wasteland runs out under the edge of the track, let that
        // edge lean onto the ordinary ground beside it rather than stop dead --
        // a worn path spreads across a boundary, it does not narrow at one.
        // Everything a trail is routed around stays excluded: cliffs, water,
        // lava, structures, the hub, and any route already laid.
        auto spill_over = [&](int x, int y) {
            int t = map->tiles[y][x];
            if (t != TILE_GRASS && t != TILE_MEADOW &&
                t != TILE_SAND  && t != TILE_SNOW) return false;
            if (water_keepout[y][x]) return false;
            if (tilemap_face_at(x, y)) return false;
            if (abs(x - cx) <= guard_r && abs(y - cy) <= guard_r) return false;
            return true;
        };

        // Only entrances a trail can actually deliver the player to: ones with
        // level, walkable ground against their footprint. A cave system opens
        // a mouth on top of every storey as well as one cut into the foot of
        // its wall, and the top mouths used to be nodes too. They cannot be
        // reached from the ground, and their anchors -- the nearest wasteland
        // tile -- sat at the mountain's foot, so the trail led the player up to
        // a wall with nothing there. The test is the ground, not the record's
        // cliff_level: the foot mouth is cut INTO the level-1 wall and carries
        // that level, yet you walk into it from the flat.
        //
        // The tile it finds is where the trail is aimed: the approach, not
        // the entrance's top-left corner. Aimed at the corner, the anchor
        // search took the nearest wasteland tile to that corner, which for a
        // mouth cut into a wall is the tile BESIDE it, and the spur ended
        // next to the door instead of at it. The ring is walked south row
        // first because a wall mouth is entered from the south; for an
        // entrance standing on open ground any side is as good as another.
        auto on_ground = [&](const DungeonEntrance& e, int& ax, int& ay) {
            int s = e.size + 1;
            // Sides in order: south row, north row, west column, east column.
            // The rows take the corners; the columns only the tiles between.
            for (int side = 0; side < 4; side++) {
                for (int k = -1; k <= s; k++) {
                    int dx, dy;
                    if (side < 2) { dy = side == 0 ? s : -1; dx = k; }
                    else          { dx = side == 2 ? -1 : s; dy = k; if (k < 0 || k >= s) continue; }
                    int nx = e.x + dx, ny = e.y + dy;
                    if (!in_world(&nx, &ny)) continue;
                    if (s_cliff_elev[ny][nx] || tilemap_face_at(nx, ny)) continue;
                    if (!tilemap_is_walkable(map, nx, ny)) continue;
                    ax = nx; ay = ny;
                    return true;
                }
            }
            return false;
        };
        std::vector<std::pair<int,int>> nodes;
        for (int i = 0; i < map->num_dungeon_entrances; i++) {
            const DungeonEntrance& e = map->dungeon_entrances[i];
            int ax, ay;
            if (!on_ground(e, ax, ay)) continue;
            nodes.push_back({ ax, ay });
        }

        route_network(map, seed ^ 0x7A11D0u, nodes,
                      is_region, is_lava, raw_lava, in_moat, paint_over, spill_over,
                      ROUTE_TRAIL, TILE_WASTE_BRIDGE,
                      EDGE_CLEARANCE, ENDPOINT_FREE, ANCHOR_SEARCH, 10, TRAIL_BRIDGE_GAP, false);
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
    fc_draw_color(renderer, s->bg_r, s->bg_g, s->bg_b, 255);
    SDL_Rect bg = { screen_x, screen_y, draw_size, draw_size };
    SDL_RenderFillRect(renderer, &bg);

    // Draw glyph only when tiles are big enough to be readable
    const int scale = draw_size / 8;
    if (scale < 1) return;
    fc_draw_color(renderer, s->fg_r, s->fg_g, s->fg_b, 255);
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


// Paint one tile type into an SDL_Surface using the same bg+glyph logic as draw_tile_ascii.
// Works on any SDL2 backend — no render-to-texture needed.
static SDL_Surface* make_tile_surf(const TileStyle* s) {
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(
        0, TILE_SIZE, TILE_SIZE, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return nullptr;
    // On the palette like everything else drawn -- see fc_palette.h.
    SDL_Color bg = fc_snap(s->bg_r, s->bg_g, s->bg_b), fg = fc_snap(s->fg_r, s->fg_g, s->fg_b);
    SDL_FillRect(surf, NULL, SDL_MapRGB(surf->format, bg.r, bg.g, bg.b));
    const int scale = TILE_SIZE / 8;
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (s->glyph[row] & (0x80u >> col)) {
                SDL_Rect px = { col * scale, row * scale, scale, scale };
                SDL_FillRect(surf, &px, SDL_MapRGB(surf->format, fg.r, fg.g, fg.b));
            }
        }
    }
    return surf;
}


// Defined with the rest of the ground-cover code, but needs the sheet surface
// while init still has it loaded.
static void build_edge_textures(SDL_Renderer* renderer, SDL_Surface* sheet);
// The same, for the cliff: the ground it closes is read back off the pixels it
// draws, so those pixels have to be kept somewhere the main thread can see.
static void cliff_build_solid(SDL_Surface* sheet);

// The cave art as it looks outside the player's view: dimmed, and on the
// palette. It used to be a colour multiply to 30%, which is a colour for every
// colour the art has and none of them FC World's. Now 11 of every 16 pixels go
// black by fc_bayer() rank and the rest keep their own colour, so the dim is
// as dark as it was and every pixel of it is still one of the 64. The cave art
// is all in the sheet's first rows (tools/gen_cave_tiles.py BLOCK_ROWS), so
// only those are copied; coordinates match the sheet's.
static const int DIM_ROWS = 8;
static SDL_Texture* build_dim_texture(SDL_Renderer* renderer, SDL_Surface* sheet) {
    SDL_Surface* s = SDL_ConvertSurfaceFormat(sheet, SDL_PIXELFORMAT_RGBA32, 0);
    if (!s) return nullptr;
    int h = DIM_ROWS * 16 < s->h ? DIM_ROWS * 16 : s->h;
    SDL_Surface* d = SDL_CreateRGBSurfaceWithFormat(0, s->w, h, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Texture* tex = nullptr;
    if (d) {
        for (int y = 0; y < h; y++) {
            const unsigned char* sp = (const unsigned char*)s->pixels + (size_t)y * s->pitch;
            unsigned char* dp = (unsigned char*)d->pixels + (size_t)y * d->pitch;
            for (int x = 0; x < s->w; x++) {
                const unsigned char* p = sp + x * 4;
                unsigned char* q = dp + x * 4;
                bool key = p[0] == 255 && p[1] == 0 && p[2] == 0;
                bool dark = !key && fc_bayer(x, y) >= 5;
                q[0] = dark ? 0 : p[0]; q[1] = dark ? 0 : p[1]; q[2] = dark ? 0 : p[2];
                q[3] = key ? 0 : 255;
            }
        }
        tex = SDL_CreateTextureFromSurface(renderer, d);
        if (tex) SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND);
        SDL_FreeSurface(d);
    }
    SDL_FreeSurface(s);
    return tex;
}

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
        cliff_build_solid(surf);
        if (surf) s_town_dim_tex = build_dim_texture(renderer, surf);
        if (surf) SDL_FreeSurface(surf);
    }
}

SDL_Texture* tilemap_get_town_tex(void) { return s_town0_tex; }
SDL_Texture* tilemap_get_town_dim_tex(void) { return s_town_dim_tex; }

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
    if (s_town_dim_tex)       { SDL_DestroyTexture(s_town_dim_tex);       s_town_dim_tex       = nullptr; }
}

// Helper: copy a cached tile texture to the screen, falling back to immediate draw.
static void blit_tile(SDL_Renderer* renderer, int tile_id,
                      int screen_x, int screen_y, int draw_size) {
    if (tile_id >= TILE_TOWN0_BASE && s_town0_tex) {
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

// A ladder of covers, one shade paler per storey, used to live here for grass,
// snow and waste alike. It was there because a plateau whose top draws exactly
// what the country around it draws was held to be invisible — and it did work,
// but by making height read as a change of biome. The reference settles the
// question the other way: the plateau there is pixel for pixel the same grass
// as the field below it, and what says it is high is the band of rock on its
// edge and the beaded line along its back. Those now carry it, so the ladder
// is gone; cliff_top_cover() hands back the plain cover for the biome.
//
// The cells it drew from are still in the sheet at rows 12-14.

// The trail worn through it, drawn from the hand-cut nine-slice at cols 24-26
// rows 5-7. Its borders come out of the art and sit on the tile grid, which is
// the point: square corners that look laid down rather than eroded.
static constexpr GroundCover COVER_TRAIL = cover_nineslice(
    sheet_cell(24, 5), sheet_cell(25, 5), sheet_cell(26, 5),
    sheet_cell(24, 6), sheet_cell(25, 6), sheet_cell(26, 6),
    sheet_cell(24, 7), sheet_cell(25, 7), sheet_cell(26, 7), TILE_WASTE_TRAIL);
// The road between settlements. Drawn as ground with its own borders, the way
// the wasteland trail is, and deliberately not the way TILE_PATH is: that one is
// town-blueprint decoration with no cover and no biome row, so it renders as a
// flat ASCII square with a comma on it and would read as a placeholder beside
// the sheet art of every other ground.
//
// Sharing the trail's nine-slice until a road is drawn. A road and a worn track
// are the same idea, so it reads correctly meanwhile; give it cells of its own
// and only these two lines change.
static constexpr GroundCover COVER_ROAD = cover_nineslice(
    sheet_cell(24, 5), sheet_cell(25, 5), sheet_cell(26, 5),
    sheet_cell(24, 6), sheet_cell(25, 6), sheet_cell(26, 6),
    sheet_cell(24, 7), sheet_cell(25, 7), sheet_cell(26, 7), TILE_ROAD);
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
// The pale is tinted blue rather than pure white on purpose -- snow is very near
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
    { { TILE_ROAD,      -1, -1, -1 },                  &COVER_ROAD,   false, false, true,  0,0,0,  -1,  -1,  -1 },
    { { TILE_SNOW,      -1, -1, -1 },                  &COVER_SNOW,   false, false, false, 0,0,0,  -1,  -1,  -1 },
    { { TILE_WATER, TILE_RIVER, TILE_HUB, TILE_POND }, &COVER_WATER,  true,  true,  false, 0,0,0, 220, 240, 255 },
    { { TILE_LAVA,      -1, -1, -1 },                  &COVER_LAVA,   true,  true,  false, 0,0,0,  -1,  -1,  -1 },
};
static const int NUM_GROUND_BIOMES = (int)(sizeof(s_biomes) / sizeof(s_biomes[0]));

// Index into s_biomes, or -1 for a tile that takes no part in biome edges.
static int biome_at(const Tilemap* map, int x, int y) {
    if (!in_world(&x, &y)) return -1;
    int t = map->tiles[y][x];
    if (t >= TILE_TOWN0_BASE) return 0;  // town cells paint grass behind themselves
    // A plateau top is the ground it is a plateau of -- the same grass, snow
    // or waste as the field below, standing higher (cliff_top_cover draws it
    // so). Left out of the biome table it took no part in biome edges, and
    // two tops of different ground met at a hard staircase where the flat
    // ground beside them mixed with a fringe. biome_fringe keeps a top from
    // blending with the ground below its rim by comparing elevation.
    if (t == TILE_CLIFF || (t >= TILE_CLIFF_2 && t <= TILE_CLIFF_5))   t = TILE_GRASS;
    else if (t >= TILE_CLIFF_SNOW_1  && t <= TILE_CLIFF_SNOW_5)        t = TILE_SNOW;
    else if (t >= TILE_CLIFF_WASTE_1 && t <= TILE_CLIFF_WASTE_5)       t = TILE_WASTELAND;
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
            const TileStyle& st = tile_styles[b->tiles[0]];
            SDL_Color c = fc_snap(st.bg_r, st.bg_g, st.bg_b);
            b->r = c.r; b->g = c.g; b->b = c.b;
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
    // The raw roll is read at the canonical tile, so the two tiles either side
    // of the seam agree about which of them starts the pair.
    auto raw = [&](int nx) { int ny = y; return in_world(&nx, &ny) && cover_clump_raw(nx, ny); };
    bool left_starts = pairs_with(x - 1) && raw(x - 1) && !raw(x - 2);
    if (left_starts) return cover->v[1];
    if (raw(x) && !raw(x - 1) && pairs_with(x + 1))
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
    if (!in_world(&x, &y) || !cover_dune_raw(x, y)) return false;
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
            int nx = x + dx, ny = y + dy;
            if (earlier && in_world(&nx, &ny) && cover_dune_raw(nx, ny)) return false;
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
// Per-biome trail banks: the master nine-slice recoloured once per ground a
// track can run over, laid out left to right from TRAIL_BANK_COL0 by
// tools/gen_trail_tiles.py. Because sheet_cell() is base + row*256 + col, a bank
// is a constant added to whatever cell the picker chose — the same trick the
// cave materials use. KEEP IN SYNC with that script's MASTER_COL0 / OUT_COL0 /
// BANK_COLS and the order of its BIOMES list.
static const int TRAIL_MASTER_COL0 = 24;
static const int TRAIL_MASTER_ROW0 = 5;
static const int TRAIL_BANK_COL0   = 68;
static const int TRAIL_BANK_COLS   = 3;
enum TrailBank { TB_GRASS = 0, TB_MEADOW, TB_SAND, TB_WASTELAND, TB_SNOW, TB_COUNT };
// Where a track crosses from one ground to another its bank changes at a tile
// boundary, and that used to be a hard cut across the stroke. The seam cells
// are each bank's nine-slice cut to a dither that is half dense along one
// side of the cell and fades across it; drawn over the tile of the OTHER bank
// on the side facing this one, the two tiles either side of the change each
// carry half of a two-tile gradient. Baked by tools/gen_trail_tiles.py at
// SEAM_COL0, four 3x3 blocks per bank in TrailSeamSide order; KEEP IN SYNC.
static const int TRAIL_SEAM_COL0   = 83;
enum TrailSeamSide { TS_NORTH = 0, TS_SOUTH, TS_WEST, TS_EAST, TS_COUNT };

// Which ground this stretch of track is worn through. The track no longer
// overwrites what it was laid on, so this is simply the tile underneath -- it
// used to be a 7x7 vote over the neighbours, because the answer had been thrown
// away at worldgen and had to be guessed back.
static int trail_bank_at(const Tilemap* map, int x, int y) {
    switch (map->tiles[y][x]) {
        case TILE_GRASS:     return TB_GRASS;
        case TILE_MEADOW:    return TB_MEADOW;
        case TILE_SAND:      return TB_SAND;
        case TILE_SNOW:      return TB_SNOW;
        case TILE_WASTELAND: return TB_WASTELAND;
        // Ground with no bank of its own -- a town square, a cliff top. The
        // wasteland bank is the master's own colours, so this draws what the
        // track always did rather than nothing.
        default:             return TB_WASTELAND;
    }
}

// Which of the nine cells a track tile shows, from its neighbours in the route
// layer. Same shape as nineslice_variant below, but a track is no longer a
// ground cover, so that function's pointer-identity test cannot answer it.
//
// A neighbour of EITHER kind counts as the same track. The two networks are
// different things to the router -- trails join dungeons, roads join
// settlements -- but on the ground a worn track is a worn track, and where a
// road runs into a trail or crosses one the two should read as one surface
// meeting, not as two strips each drawing its border against the other. Both
// draw from the same nine-slice in the bank of the ground beneath them, so
// once the border is gone the join is invisible.
static int route_variant(const Tilemap* map, int x, int y, const GroundCover* cover) {
    auto same = [&](int nx, int ny) {
        return in_world(&nx, &ny) && map->route[ny][nx] != ROUTE_NONE;
    };
    bool n = same(x, y - 1), so = same(x, y + 1);
    bool w = same(x - 1, y), e  = same(x + 1, y);

    if (!n && !w) return cover->v[0];
    if (!n && !e) return cover->v[2];
    if (!so && !w) return cover->v[5];
    if (!so && !e) return cover->v[7];
    if (!n)  return cover->v[1];
    if (!so) return cover->v[6];
    if (!w)  return cover->v[3];
    if (!e)  return cover->v[4];
    return cover->plain;
}

// The cell a track tile draws: its nine-slice piece, shifted into the bank for
// the ground it runs over.
static int route_cell(const Tilemap* map, int x, int y) {
    const GroundCover* rc = (map->route[y][x] == ROUTE_ROAD) ? &COVER_ROAD : &COVER_TRAIL;
    return route_variant(map, x, y, rc)
         + trail_bank_at(map, x, y) * TRAIL_BANK_COLS
         + TRAIL_BANK_COL0 - TRAIL_MASTER_COL0;
}

// The seam cells a track tile draws over its own: one per side whose
// neighbour is track on different ground, in that neighbour's bank and this
// tile's nine-slice position. Returns how many were written to `out`.
static int route_seam_cells(const Tilemap* map, int x, int y, int* out) {
    const GroundCover* rc = (map->route[y][x] == ROUTE_ROAD) ? &COVER_ROAD : &COVER_TRAIL;
    int v    = route_variant(map, x, y, rc) - TILE_TOWN0_BASE;
    int vcol = v % TOWN0_SHEET_COLS - TRAIL_MASTER_COL0;
    int vrow = v / TOWN0_SHEET_COLS - TRAIL_MASTER_ROW0;
    int mine = trail_bank_at(map, x, y);
    static const int SDX[TS_COUNT] = { 0, 0, -1, 1 };
    static const int SDY[TS_COUNT] = { -1, 1, 0, 0 };
    int n = 0;
    for (int s = 0; s < TS_COUNT; s++) {
        int nx = x + SDX[s], ny = y + SDY[s];
        if (!in_world(&nx, &ny) || map->route[ny][nx] == ROUTE_NONE) continue;
        int theirs = trail_bank_at(map, nx, ny);
        if (theirs == mine) continue;
        out[n++] = sheet_cell(TRAIL_SEAM_COL0 + (theirs * TS_COUNT + s) * TRAIL_BANK_COLS + vcol,
                              TRAIL_MASTER_ROW0 + vrow);
    }
    return n;
}

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
// Which layer a plateau tile is, or 0 for anything that is not plateau surface.
static int cliff_body_elev(int t) {
    switch (t) {
        case TILE_CLIFF:   case TILE_CLIFF_SNOW_1: case TILE_CLIFF_WASTE_1: return 1;
        case TILE_CLIFF_2: case TILE_CLIFF_SNOW_2: case TILE_CLIFF_WASTE_2: return 2;
        case TILE_CLIFF_3: case TILE_CLIFF_SNOW_3: case TILE_CLIFF_WASTE_3: return 3;
        case TILE_CLIFF_4: case TILE_CLIFF_SNOW_4: case TILE_CLIFF_WASTE_4: return 4;
        case TILE_CLIFF_5: case TILE_CLIFF_SNOW_5: case TILE_CLIFF_WASTE_5: return 5;
        default: return 0;
    }
}
static bool cliff_is_face_tile(int t) {
    return (t >= TILE_CLIFF_EDGE_1   && t <= TILE_CLIFF_EDGE_5)
        || (t >= TILE_CLIFF_SIDE_1   && t <= TILE_CLIFF_CORNER_NE_5)
        || (t >= TILE_CLIFF_SIDE_E_1 && t <= TILE_CLIFF_BACK_3);
}



// Returned instead of a cell for the ring of tiles around a plateau that
// generation fills with side, back and corner faces. The art puts the whole
// outline on the plateau's own edge tiles, so there is nothing left for the
// ring to draw: giving it anything made every plateau read a tile wider than
// it is.
//
// The ring still exists and is still impassable, so a cliff is walled as it
// always was; it just draws as the ground it stands in. Which does mean the
// wall is a tile further out than the drawn edge.
static const int CLIFF_ART_HIDDEN = -2;

// The islands' sprites -- see tools/gen_islands.py, which bakes them into
// the sheet from art/cliffs/islands/: one cell per distinct sprite of
// Mother 1's three island drawings and their mirror images, sprite i at row
// ISLAND_ROW0 + i / 256, column i % 256. A tile draws the cell the island
// stamped on it, s_island_cell, and nothing else: there are no cases and no
// variants to pick, because the island already chose every piece.
static inline int island_sheet_cell(int cell) {
    return sheet_cell(cell % TOWN0_SHEET_COLS, ISLAND_ROW0 + cell / TOWN0_SHEET_COLS);
}

// The cliff read back as ground rather than as a picture: one bit per pixel of
// every sprite, so that what closes the ground is the rock that was drawn and
// not the tile the rock happened to land in.
//
// The two are half a tile apart and always were. The line runs through the
// middle of its tile and the band's teeth bite into the top of theirs, and
// the ground was closed a tile at a time -- so up to half a tile of grass
// along every edge was walled off. Measured before this, in art pixels:
// coming down from the north the ground stopped the player 12.7 short of the
// rock, from the west 6.8, from the east 4.0, from the south 3.2. All
// positive, all invisible wall.
//
// Read off the sheet: the sprites are drawn by hand, so there is nothing else
// to work them out from, and the pixels are already there.
static unsigned short s_cliff_ink[ISLAND_SPRITES][16];
// Whether there are any pixels to read. Without the sheet there is no cliff on
// screen either, but there is still one in the ground, and an empty mask would
// quietly open every plateau. So say so, and fall back to the coarse answer.
static bool s_cliff_ink_ready = false;

// Fill the nicks out of one cell's edge: grow it a pixel, then shrink it back.
//
// A closing, and deliberately not an opening as well. The silhouette is toothed
// on purpose — a column of brown standing two or three pixels proud of the ones
// beside it, with a wedge of black driven down between them, which is what
// makes a face read as rock rather than as a torn edge. Walked along, the
// notch between two of those is a two-pixel slot for the feet to drop into
// and be held by. Growing then
// shrinking fills every slot that narrow and moves nothing wider, and because a
// closing can only ever add, it cannot rub out the beaded line, which is one
// pixel across and is the whole of the drop at the back of a height.
//
// What lies outside the cell is unknown — the tile next door draws a different
// sprite — so it is taken as empty when growing and as full when shrinking, which
// is the pair that leaves the cell's own border alone. Seams therefore do not
// move, and the sixteenth of the edge that lands on one goes unsmoothed.
static void cliff_close_cell(unsigned short* c) {
    unsigned short g[16];
    for (int y = 0; y < 16; y++) {
        unsigned short r = c[y];
        g[y] = (unsigned short)(r | (r << 1) | (r >> 1)
                                 | c[y > 0 ? y - 1 : y] | c[y < 15 ? y + 1 : y]);
    }
    for (int y = 0; y < 16; y++) {
        unsigned short r = g[y];
        c[y] = (unsigned short)(r & (unsigned short)((r << 1) | 1u)
                                  & (unsigned short)((r >> 1) | 0x8000u)
                                  & g[y > 0 ? y - 1 : y] & g[y < 15 ? y + 1 : y]);
    }
}

static void cliff_build_solid(SDL_Surface* sheet) {
    memset(s_cliff_ink, 0, sizeof s_cliff_ink);
    s_cliff_ink_ready = false;
    if (!sheet) return;
    SDL_Surface* s = SDL_ConvertSurfaceFormat(sheet, SDL_PIXELFORMAT_RGBA32, 0);
    if (!s) return;
    for (int i = 1; i < ISLAND_SPRITES; i++) {
        int row = ISLAND_ROW0 + i / TOWN0_SHEET_COLS, col = i % TOWN0_SHEET_COLS;
        int y0 = row * 16, x0 = col * 16;
        if (y0 + 16 > s->h || x0 + 16 > s->w) break;
        for (int py = 0; py < 16; py++) {
            const unsigned char* rowp =
                (const unsigned char*)s->pixels + (size_t)(y0 + py) * s->pitch;
            unsigned short bits = 0;
            for (int px = 0; px < 16; px++) {
                // RGBA32 is byte order, so this reads the same either way
                // round. Everything the cliff drew is brown or ink; what it
                // left alone is the sheet's key, and shows the ground.
                const unsigned char* p = rowp + (size_t)(x0 + px) * 4;
                if (!(p[0] == 255 && p[1] == 0 && p[2] == 0))
                    bits |= (unsigned short)(1u << px);
            }
            s_cliff_ink[i][py] = bits;
        }
        cliff_close_cell(s_cliff_ink[i]);
    }
    SDL_FreeSurface(s);
    s_cliff_ink_ready = true;
}

// The cell the cliff draws over a tile, or 0 for none. Ground of a plateau
// is the ground at the bottom of it, pixel for pixel, as the drawings have
// it; what says it is high is the band hanging off its edge and the line
// along its back, and those are cells of the island stamped there.
static inline int cliff_cell_at(int x, int y) {
    return in_world(&x, &y) ? (int)s_island_cell[y][x] : 0;
}

// Up to six cells to draw over the tile's ground, in order. One, now: the
// island's cell. The count and the array are kept because the renderer was
// written for a stack of cases and still walks one.
static int cliff_art_layers(const Tilemap* map, int x, int y, int t, int out[6]) {
    if (!s_town0_tex) return 0;
    (void)map; (void)t;
    int c = cliff_cell_at(x, y);
    if (!c) return 0;
    out[0] = island_sheet_cell(c);
    return 1;
}

// Whether the cliff closes this pixel of this tile.
//
// What is drawn is what closes, and nothing else is. That is the whole rule:
// the cell the tile draws, asked whether it drew anything at this pixel --
// so the edge the player is stopped at is the edge they can see, pixel for
// pixel, rather than the tile that edge fell in. The scree is not tested and
// must not be: grains lying on open country below the foot of a wall,
// spilled there precisely so that you can walk among them.
static bool cliff_pixel_solid(int x, int y, int ax, int ay) {
    // No sheet, no pixels to be exact about: close the tile whole, which is
    // what this did before there was anything finer to say.
    if (!s_cliff_ink_ready) return true;
    int c = cliff_cell_at(x, y);
    if (!c || !ISLAND_KIND[c]) return false;
    return (s_cliff_ink[c][ay] >> ax) & 1;
}

// The ground a plateau's surface is made of. Each of the three cliff families
// belongs to a biome and that is the whole point of having three: the rim is
// drawn over grass, snow or waste rather than over a colour of its own.
//
// Every level of a family draws the *same* ground, deliberately. The tinted
// per-level covers this used to return said "you are one storey up" by making
// the grass yellower, and the reference says the opposite as plainly as it can:
// the top of the plateau there is pixel for pixel the grass at the bottom of
// it. What tells you the ground is high is the band of rock hanging off its
// edge and the beaded line along its back — not a change of colour, which at
// this size reads as a different biome rather than as a different height.
static const GroundCover* cliff_top_cover(int t) {
    if (t >= TILE_CLIFF_SNOW_1  && t <= TILE_CLIFF_SNOW_5)  return &COVER_SNOW;
    if (t >= TILE_CLIFF_WASTE_1 && t <= TILE_CLIFF_WASTE_5) return &COVER_WASTE;
    return &COVER_GRASS;
}

// What shows through the keyed-out corners, and what the hidden ring draws as.
// It should be the ground the cliff is standing in rather than a fixed guess —
// grass behind a snowfield cliff would read as a hole.
//
// A ring tile is level with whatever is on the far side of it from its own
// plateau, so that is asked first. Where two plateaus sit against each other
// the ground on that side is the lower one's surface, and taking the nearest
// non-cliff neighbour instead ran a strip of grass down between them.


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
        int nx = x + EDGE_NB[i][0], ny = y + EDGE_NB[i][1];
        // Only ground on the same level mixes. Across a rim the wall is what
        // separates the two, and the rock art draws that join.
        if (in_world(&nx, &ny) && s_cliff_elev[ny][nx] != s_cliff_elev[y][x]) continue;
        int b = biome_at(map, nx, ny);
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

// A neighbour's fringe is painted in its plain colour at any height. It used
// to be worked out through the elevation wash, so a dot matched its biome's
// washed surface a tile away; a storey is a dither of palette colours now, so
// the plain colour is already the surface's own, and it is on the palette.
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
        // The masks are white and hard-edged, so a palette colour here comes
        // out on screen exactly.
        SDL_Color c = fc_snap(l.r, l.g, l.b);
        SDL_SetTextureColorMod(t, c.r, c.g, c.b);
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

    int start_x = (int)floorf(cam->x / TILE_SIZE);
    int start_y = (int)floorf(cam->y / TILE_SIZE);
    int tiles_wide = (int)(cam->screen_w / z / TILE_SIZE) + 2;
    int tiles_tall = (int)(cam->screen_h / z / TILE_SIZE) + 2;
    int end_x = start_x + tiles_wide;
    int end_y = start_y + tiles_tall;

    // Clamped on the hard-border axis only. On the wrap axis the view runs
    // straight over the seam: the loop walks the unwrapped range, places each
    // tile by its unwrapped coordinate, and reads it by its canonical one.
    if (s_wrap_axis != WRAP_X) {
        if (start_x < 0)        start_x = 0;
        if (end_x > MAP_WIDTH)  end_x = MAP_WIDTH;
    }
    if (s_wrap_axis != WRAP_Y) {
        if (start_y < 0)        start_y = 0;
        if (end_y > MAP_HEIGHT) end_y = MAP_HEIGHT;
    }

    for (int uy = start_y; uy < end_y; uy++) {
        for (int ux = start_x; ux < end_x; ux++) {
            const int x = wrap_x(ux), y = wrap_y(uy);
            bool is_depth = (map->depth_layer[y][x] != 0);
            int screen_x = (int)((ux * TILE_SIZE - cam->x) * z);
            int screen_y = (int)((uy * TILE_SIZE - cam->y) * z);

            // Helper: compute jitter offset for a tree tile
            // Which sheet column a tree draws from: two kinds on ordinary
            // ground (cols 16, 17), two conifers on snow (18, 19), half and
            // half by position. The canopy (row 0) and the trunk (row 1) are
            // drawn in different passes and must agree, so both ask here.
            auto tree_col = [&](int tx, int ty2) -> int {
                uint32_t h = (uint32_t)(tx * 2654435761u ^ (uint32_t)ty2 * 40503u) & 1;
                bool is_snow = (map->tiles[ty2][tx] == TILE_SNOW);
                return is_snow ? (h ? 19 : 18) : (h ? 16 : 17);
            };
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
                int col = tree_col(tx, ty2);
                int jox = tree_jox(tx, ty2);
                SDL_Rect src_top = { col * 16, 0 * 16, 16, 16 };
                SDL_Rect dst_top = { sx + jox, sy, draw_size, draw_size };
                if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_top, &dst_top);
            };

            if (depth_pass) {
                // Depth pass: town tile only — grass already drawn in base pass, before player
                if (is_depth) blit_tile(renderer, map->tiles[y][x], screen_x, screen_y, draw_size);
                // Draw canopy for any 2-tile tree whose trunk is in the row below (y+1).
                int bx = x, by = y + 1;
                bool below = in_world(&bx, &by);
                if (below && map->overlay[by][bx] == TILE_TREE) {
                    draw_tree_canopy(bx, by, screen_x, screen_y);
                }
                if (below && map->overlay[by][bx] == TILE_DEAD_TREE) {
                    int jox = tree_jox(bx, by);
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
                int layers[6];
                int n_layers = cliff_art_layers(map, x, y, tile_id, layers);
                bool is_ring  = (n_layers == CLIFF_ART_HIDDEN);
                bool is_body  = (cliff_body_elev(tile_id) > 0);
                // Open ground can carry one piece of cliff art — the arch over a
                // one-tile tip, which lands on the cell above the tip. It keeps
                // its own cover: it is still the field it always was, with a
                // piece of outline laid over the bottom of it.
                bool is_cliff = is_ring || is_body
                             || (n_layers > 0 && cliff_is_face_tile(tile_id));
                if (is_ring) n_layers = 0;
                // A plateau's surface is its biome's ground; everything else its
                // own cover.
                //
                // There used to be a third arm here, for a cliff that is not a
                // plateau body — a ring, or a face written into the map as a
                // tile — which hunted outward for the ground it was level with.
                // Neither can happen any more. A ring needs cliff_art_layers()
                // to answer CLIFF_ART_HIDDEN and it only ever answers 0 to 6,
                // and a face has not been a tile since the band became something
                // drawn over whatever it lands on. is_cliff is still read below.
                const GroundCover* cover = is_body ? cliff_top_cover(tile_id)
                                                   : tile_cover(map, x, y);
                bool is_town = (tile_id >= TILE_TOWN0_BASE);
                if (cover)
                    blit_tile(renderer, cover_variant(map, x, y, cover), screen_x, screen_y, draw_size);
                else if (!is_cliff)
                    blit_tile(renderer, tile_id, screen_x, screen_y, draw_size);
                // The fringe of neighbouring ground goes on after the haze
                // below -- except under a track, which has to cover it and
                // takes the haze itself, so there it goes on now.
                bool track = map->route[y][x] != ROUTE_NONE;
                if (track)
                    draw_biome_edges(renderer, map, x, y, screen_x, screen_y, draw_size);
                // The track, worn over that ground and over its fringe. Drawn
                // here rather than written into the tile, so the ground keeps
                // drawing underneath: the seam between two biomes now runs on
                // beneath a road instead of being erased by it, and shows
                // through wherever the track's own art is keyed out.
                if (track) {
                    blit_tile(renderer, route_cell(map, x, y), screen_x, screen_y, draw_size);
                    // Then the blend toward any neighbouring track on other
                    // ground, so the bank change spreads across two tiles
                    // instead of cutting at one boundary.
                    int seam[TS_COUNT];
                    int ns = route_seam_cells(map, x, y, seam);
                    for (int i = 0; i < ns; i++)
                        blit_tile(renderer, seam[i], screen_x, screen_y, draw_size);
                }
                if (!track)
                    draw_biome_edges(renderer, map, x, y, screen_x, screen_y, draw_size);
                for (int li = 0; li < n_layers; li++)
                    blit_tile(renderer, layers[li], screen_x, screen_y, draw_size);
                if (!is_cliff && is_town) blit_tile(renderer, tile_id, screen_x, screen_y, draw_size);
                // A cave mouth is cut into a wall, so it has to be painted over
                // the wall. Every other tile is drawn before the cliff layers,
                // which is right for ground the band falls across and wrong for
                // the one hole that is supposed to show through it.
                if (tile_id == TILE_DUNGEON ||
                    (tile_id >= TILE_DUNGEON_CAVE && tile_id <= TILE_DUNGEON_LARGE_TREE))
                    blit_tile(renderer, tile_id, screen_x, screen_y, draw_size);
                // The cave mouth's mound lies over the wall and over that
                // glyph: its key pixels let the band through round it.
                if (is_cave_mouth_cell(map->overlay[y][x]))
                    blit_tile(renderer, map->overlay[y][x], screen_x, screen_y, draw_size);
            }
            if (is_depth) continue;

            // Draw overlay (trees, rocks, gold ore) on top
            int ov = map->overlay[y][x];
            if (is_cave_mouth_cell(ov)) {
                // already painted, over the cliff, above
            } else if (ov == TILE_TREE) {
                // Each tree tile is fully independent.
                // Every tree is two tiles tall: the trunk here, the canopy in
                // the depth pass above. tree_col() picks the kind.
                int jox = tree_jox(x, y);
                SDL_Rect src_bot = { tree_col(x, y) * 16, 1 * 16, 16, 16 };
                SDL_Rect dst_bot = { screen_x + jox, screen_y, draw_size, draw_size };
                if (s_town0_tex) SDL_RenderCopy(renderer, s_town0_tex, &src_bot, &dst_bot);
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

// ── Public: debug tile-grid overlay ─────────────────────────────────────────
// Same idea as dungeon.cpp's version -- one box per TILE_SIZE cell in view --
// but the label here is the tileset (col,row) a tile draws from rather than
// its world (tx,ty), since that's the coordinate system assets/tileset.png
// edits are actually made in. Exact for anything stored directly as a
// TOWN0 sheet id (cliffs, roads, buildings, dungeon entrances). Ground
// cover (grass, sand, snow...) picks its exact cell per-position at draw
// time via GroundCover variants rather than from tile_id directly, so those
// fall back to the stored id's own naive col,row, which won't always be the
// specific variant actually drawn there.
void tilemap_draw_debug_grid(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer) {
    float z   = cam->zoom;
    int   tsz = (int)(TILE_SIZE * z);
    if (tsz < 1) tsz = 1;

    int tx0 = (int)floorf(cam->x / TILE_SIZE) - 1;
    int ty0 = (int)floorf(cam->y / TILE_SIZE) - 1;
    int tx1 = tx0 + (int)(cam->screen_w / tsz) + 3;
    int ty1 = ty0 + (int)(cam->screen_h / tsz) + 3;
    // Clamped on the hard-border axis only, as the tile draw is: the cells
    // are placed unwrapped and their labels read from the canonical tile.
    if (s_wrap_axis != WRAP_X) {
        if (tx0 < 0) tx0 = 0;
        if (tx1 > MAP_WIDTH)  tx1 = MAP_WIDTH;
    }
    if (s_wrap_axis != WRAP_Y) {
        if (ty0 < 0) ty0 = 0;
        if (ty1 > MAP_HEIGHT) ty1 = MAP_HEIGHT;
    }

    fc_draw_color(renderer, 0, 255, 0, 110);
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    for (int ty = ty0; ty < ty1; ty++) {
        for (int tx = tx0; tx < tx1; tx++) {
            int sx = (int)((tx * TILE_SIZE - cam->x) * z);
            int sy = (int)((ty * TILE_SIZE - cam->y) * z);
            SDL_Rect r = { sx, sy, tsz, tsz };
            SDL_RenderDrawRect(renderer, &r);
        }
    }
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);

    if (tsz >= 24) {   // labels need room; skip them at small zoom rather than smear illegible text
        for (int ty = ty0; ty < ty1; ty++) {
            for (int tx = tx0; tx < tx1; tx++) {
                int sx = (int)((tx * TILE_SIZE - cam->x) * z);
                int sy = (int)((ty * TILE_SIZE - cam->y) * z);
                int tile_id = map->tiles[wrap_y(ty)][wrap_x(tx)];
                char buf[16];
                if (tile_id >= TILE_TOWN0_BASE) {
                    int idx = tile_id - TILE_TOWN0_BASE;
                    SDL_snprintf(buf, sizeof(buf), "%d:%d", idx % TOWN0_SHEET_COLS, idx / TOWN0_SHEET_COLS);
                } else {
                    SDL_snprintf(buf, sizeof(buf), "ID%d", tile_id);
                }
                draw_text(renderer, buf, sx + 1, sy + 1, 1, 60, 255, 60);
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
        // Both tables used to stop here, so anything past 62 sampled as grass.
        // A road network is most of what a map is for, so it wins its block
        // outright: three tiles wide sampled every few tiles would vanish more
        // often than not at any lower priority.
        0, 0, 0, 0, 0, 0, 0, 0,                                                   // 63-70: dungeon markers → hidden
        0,                                                                         // 71: DEAD_TREE → hidden
        3, 3,                                                                      // 72-73: waste trail and its deck
        0, 0, 0, 0, 0,                                                            // 74-78: legacy east sides → unused
        0, 0, 0,                                                                   // 79-81: legacy backs → unused
        3, 3,                                                                      // 82-83: ROAD, ROAD_BRIDGE
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
        { 30,  90,  30, 255}, // DUNGEON_CAVE         (63) → hidden
        { 30,  90,  30, 255}, // DUNGEON_RUINS        (64) → hidden
        { 30,  90,  30, 255}, // DUNGEON_GRAVEYARD_SM (65) → hidden
        { 30,  90,  30, 255}, // DUNGEON_GRAVEYARD_LG (66) → hidden
        { 30,  90,  30, 255}, // DUNGEON_OASIS        (67) → hidden
        { 30,  90,  30, 255}, // DUNGEON_PYRAMID      (68) → hidden
        { 30,  90,  30, 255}, // DUNGEON_STONEHENGE   (69) → hidden
        { 30,  90,  30, 255}, // DUNGEON_LARGE_TREE   (70) → hidden
        { 30,  90,  30, 255}, // DEAD_TREE            (71) → hidden
        { 95,  72,  48, 255}, // WASTE_TRAIL          (72)
        {120,  95,  65, 255}, // WASTE_BRIDGE         (73)
        { 30,  90,  30, 255}, // CLIFF_SIDE_E_1       (74) → unused
        { 30,  90,  30, 255}, // CLIFF_SIDE_E_2       (75) → unused
        { 30,  90,  30, 255}, // CLIFF_SIDE_E_3       (76) → unused
        { 30,  90,  30, 255}, // CLIFF_SIDE_E_4       (77) → unused
        { 30,  90,  30, 255}, // CLIFF_SIDE_E_5       (78) → unused
        { 30,  90,  30, 255}, // CLIFF_BACK_1         (79) → unused
        { 30,  90,  30, 255}, // CLIFF_BACK_2         (80) → unused
        { 30,  90,  30, 255}, // CLIFF_BACK_3         (81) → unused
        {150, 110,  70, 255}, // ROAD                 (82) → light track, reads over forest
        {185, 150, 105, 255}, // ROAD_BRIDGE          (83) → lighter deck over water
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
                    // A track is no longer written into the tile, so sample its
                    // layer too — at the priority the table already gives it,
                    // which is the highest there is and deliberately so: three
                    // tiles wide sampled every few tiles would vanish more often
                    // than not at anything lower.
                    if (map->route[by][bx])
                        id = (map->route[by][bx] == ROUTE_ROAD) ? TILE_ROAD : TILE_WASTE_TRAIL;
                    if (id >= 0 && id < NUM_MM_COLORS && tile_priority[id] > best_pri) {
                        best_pri = tile_priority[id];
                        best_id  = id;
                    }
                }
            }
            SDL_Color c = tile_colors[best_id];
            fc_draw_color(renderer, c.r, c.g, c.b, 255);
            SDL_Rect r = { ox + x / step, oy + y / step, 1, 1 };
            SDL_RenderFillRect(renderer, &r);
        }
    }

    // villages — 3×3 orange dot centered on footprint
    for (int i = 0; i < map->num_villages; i++) {
        if (map->villages[i].x < 0) continue;
        int vx = ox + (map->villages[i].x + VILLAGE_W / 2) / step;
        int vy = oy + (map->villages[i].y + VILLAGE_H / 2) / step;
        fc_draw_color(renderer, 255, 140, 0, 255);
        SDL_Rect vdot = { vx - 1, vy - 1, 3, 3 };
        SDL_RenderFillRect(renderer, &vdot);
    }

    // castles — 4×4 white dot centered on footprint
    for (int i = 0; i < 4; i++) {
        if (map->castles[i].x < 0) continue;
        int cax = ox + (map->castles[i].x + CASTLE_W / 2) / step;
        int cay = oy + (map->castles[i].y + CASTLE_H / 2) / step;
        fc_draw_color(renderer, 255, 255, 255, 255);
        SDL_Rect cdot = { cax - 2, cay - 2, 4, 4 };
        SDL_RenderFillRect(renderer, &cdot);
    }

    // dungeons — 3×3 red dot centered on entrance
    for (int i = 0; i < map->num_dungeon_entrances; i++) {
        const DungeonEntrance* e = &map->dungeon_entrances[i];
        int dx = ox + (e->x + 1) / step;
        int dy = oy + (e->y + 1) / step;
        fc_draw_color(renderer, 255, 0, 0, 255);
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
        fc_draw_color(renderer, 0, 255, 255, 255);
    else
        fc_draw_color(renderer, 255, 255, 255, 255);
    SDL_Rect dot = { px - 2, py - 2, 5, 5 };
    SDL_RenderFillRect(renderer, &dot);

    // red 5×5 dot for cliff gradient peak (debug)
    //int peakdot_x = ox + (int)(map->cliff_peak_x) / step;
    //int peakdot_y = oy + (int)(map->cliff_peak_y) / step;
    //fc_draw_color(renderer, 255, 0, 0, 255);
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
        int ax = tx, ay = ty - 1;
        bool paired = in_world(&ax, &ay) && map->overlay[ay][ax] == TILE_TREE;
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

// The tile box `r` pixels around a point. Clamped only on the hard-border
// axis: on the wrap axis it is walked unwrapped, so every distance measured in
// it is in one frame, and each tile is read through in_world().
static void tile_box(float px, float py, int r,
                     int* tx0, int* ty0, int* tx1, int* ty1) {
    *tx0 = (int)floorf((px - r) / TILE_SIZE);
    *ty0 = (int)floorf((py - r) / TILE_SIZE);
    *tx1 = (int)floorf((px + r) / TILE_SIZE);
    *ty1 = (int)floorf((py + r) / TILE_SIZE);
    if (s_wrap_axis != WRAP_X) {
        if (*tx0 < 0)          *tx0 = 0;
        if (*tx1 >= MAP_WIDTH) *tx1 = MAP_WIDTH - 1;
    }
    if (s_wrap_axis != WRAP_Y) {
        if (*ty0 < 0)           *ty0 = 0;
        if (*ty1 >= MAP_HEIGHT) *ty1 = MAP_HEIGHT - 1;
    }
}

// A harvestable tile at an unwrapped position, with its canonical index.
static bool harvestable_at(const Tilemap* map, int ux, int uy, int* tx, int* ty) {
    *tx = ux; *ty = uy;
    return in_world(tx, ty) && tile_is_harvestable(map->overlay[*ty][*tx]);
}

int tilemap_sweep(Tilemap* map, float px, float py, float radius,
                  float start_ang, float rel0, float rel1,
                  WeaponType weapon, HarvestResult* out) {
    int tx0, ty0, tx1, ty1;
    tile_box(px, py, (int)radius, &tx0, &ty0, &tx1, &ty1);

    int struck = 0;
    for (int uy = ty0; uy <= ty1; uy++) {
        for (int ux = tx0; ux <= tx1; ux++) {
            int tx, ty;
            if (!harvestable_at(map, ux, uy, &tx, &ty)) continue;
            float cx = (ux + 0.5f) * TILE_SIZE;
            float cy = (uy + 0.5f) * TILE_SIZE;
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

float tilemap_first_along(const Tilemap* map, float px, float py,
                          float angle, float half_width, float max_reach) {
    int tx0, ty0, tx1, ty1;
    tile_box(px, py, (int)max_reach + TILE_SIZE, &tx0, &ty0, &tx1, &ty1);

    float best = -1.0f;
    for (int uy = ty0; uy <= ty1; uy++) {
        for (int ux = tx0; ux <= tx1; ux++) {
            int tx, ty;
            if (!harvestable_at(map, ux, uy, &tx, &ty)) continue;
            float cx = (ux + 0.5f) * TILE_SIZE;
            float cy = (uy + 0.5f) * TILE_SIZE;
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
    tile_box(px, py, (int)to + TILE_SIZE, &tx0, &ty0, &tx1, &ty1);

    int struck = 0;
    for (int uy = ty0; uy <= ty1; uy++) {
        for (int ux = tx0; ux <= tx1; ux++) {
            int tx, ty;
            if (!harvestable_at(map, ux, uy, &tx, &ty)) continue;
            float cx = (ux + 0.5f) * TILE_SIZE;
            float cy = (uy + 0.5f) * TILE_SIZE;
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
    int tx, ty;
    if (!harvestable_at(map, (int)floorf(x / TILE_SIZE), (int)floorf(y / TILE_SIZE), &tx, &ty))
        return 0;
    tilemap_strike(map, tx, ty, weapon, out);
    return 1;
}

int tilemap_try_hit(Tilemap* map, float px, float py, int range,
                    WeaponType weapon, HarvestResult* out) {
    int tx0, ty0, tx1, ty1;
    tile_box(px, py, range, &tx0, &ty0, &tx1, &ty1);

    // A sweeping weapon takes everything in the box; anything else takes only
    // the nearest tile, which is the original single-target behaviour.
    if (weapon_sweeps(weapon)) {
        int struck = 0;
        for (int uy = ty0; uy <= ty1; uy++) {
            for (int ux = tx0; ux <= tx1; ux++) {
                int tx, ty;
                if (!harvestable_at(map, ux, uy, &tx, &ty)) continue;
                tilemap_strike(map, tx, ty, weapon, out);
                struck++;
            }
        }
        return struck;
    }

    float best_dist2 = (float)(range * range) * 2.0f + 1.0f;
    int best_tx = -1, best_ty = -1;
    for (int uy = ty0; uy <= ty1; uy++) {
        for (int ux = tx0; ux <= tx1; ux++) {
            int tx, ty;
            if (!harvestable_at(map, ux, uy, &tx, &ty)) continue;
            float dx = (ux + 0.5f) * TILE_SIZE - px;
            float dy = (uy + 0.5f) * TILE_SIZE - py;
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

// Whether a tile is one the cliff reaches. Exposed so a probe can check the one
// rule the terrain must never break: every such tile belongs to the edge of
// something raised.
//
// One bit per level: every tile an island put rock or line on. The exact
// answer, per pixel, is cliff_pixel_solid(); this is the coarse one.
bool tilemap_face_at(int x, int y) {
    return in_world(&x, &y) && (s_cliff_face[y][x] & ((1 << CLIFF_LEVELS) - 1)) != 0;
}

// Whether a tree or a rock may not stand on a tile because of the cliff: on
// a wall, or on the tile under one, where a crown rising into the tile above
// would cover the foot of the wall or its line.
static bool cliff_bars_overlay(int x, int y) {
    return tilemap_face_at(x, y) || tilemap_face_at(x, y - 1);
}

int tilemap_cliff_elev_at(int x, int y) {
    return in_world(&x, &y) ? (int)s_cliff_elev[y][x] : 0;
}

bool tilemap_cliff_sealed_at(int x, int y) {
    return in_world(&x, &y) && (s_cliff_face[y][x] & CLIFF_FACE_SEALED) != 0;
}

void tilemap_debug_cave_tally(int* seen, int* sealed, int* placed,
                              long* sealed_tiles, long* placed_tiles) {
    if (seen)         *seen         = s_cave_seen;
    if (sealed)       *sealed       = s_cave_sealed;
    if (placed)       *placed       = s_cave_placed;
    if (sealed_tiles) *sealed_tiles = s_cave_sealed_tiles;
    if (placed_tiles) *placed_tiles = s_cave_placed_tiles;
}

// What the island drew on the tile, reduced to the one thing a tile-by-tile
// check wants to know: rock, line, or nothing.
char tilemap_cliff_draw_at(int x, int y) {
    if (!in_world(&x, &y)) return ' ';
    int c = s_island_cell[y][x];
    if (!c) return '.';
    return ISLAND_KIND[c] == 1 ? 'R' : ISLAND_KIND[c] == 2 ? 'L' : '.';
}

// There is no facing any more: the island decided which way each wall looks
// when it was drawn. Kept for the tools that print it.
float tilemap_cliff_facing_at(int x, int y) {
    (void)x; (void)y;
    return -2.0f;
}

// Whether the tile's own ground can be stood on, with nothing said about what
// is drawn over it. Split out because the cliff has two answers — a coarse one
// per tile and an exact one per pixel — and they want the same ground under
// them.
static bool tile_ground_walkable(const Tilemap* map, int tile_x, int tile_y) {
    switch (map->tiles[tile_y][tile_x]) {
        case TILE_GRASS:
        case TILE_PATH:
        case TILE_SAND:
        case TILE_SNOW:
        case TILE_WASTELAND:
        case TILE_WASTE_TRAIL:
        case TILE_WASTE_BRIDGE:
        case TILE_ROAD:
        case TILE_ROAD_BRIDGE:
        case TILE_MEADOW:
        // Elevated terrain top surfaces — the top of a plateau is walked on,
        // like any other ground. A cliff face has no id of its own to list
        // beside them: it is drawn over whatever terrace it falls on, so the
        // ground under one is still grass, and what closes it is the art.
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
            // Sheet tiles are walkable unless the editor marked them as solid
            if (map->tiles[tile_y][tile_x] >= TILE_TOWN0_BASE &&
                map->tiles[tile_y][tile_x] <= TILE_TOWN0_END)
                return map->coll[tile_y][tile_x] == 0;
            return false;
    }
}

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y) {
    if (!in_world(&tile_x, &tile_y)) return false;

    // The cliff, coarsely: any tile it reaches is refused whole. That is a good
    // deal more ground than it actually closes — the exact answer is per pixel
    // and lives in cliff_pixel_solid() — but this is what a caller holding
    // nothing but a tile can be told, and being wrong the safe way is what such
    // a caller wants. It is also why nothing here reads the tile's own id
    // first: a face is drawn over whatever terrace it falls on, so the ground
    // beneath one is still grass and would answer yes.
    if (s_cliff_face[tile_y][tile_x] & ((1 << CLIFF_LEVELS) - 1)) return false;

    return tile_ground_walkable(map, tile_x, tile_y);
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
    // Canonical first: the hitbox's samples run over the seam as the player
    // does, and the sub-tile arithmetic below wants the pixel and its tile in
    // the same frame. Off the hard border is solid; that is the border.
    px = wrap_px(px);
    py = wrap_py(py);
    int tx = (int)floorf(px / TILE_SIZE);
    int ty = (int)floorf(py / TILE_SIZE);
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

    // The cliff is drawn along a contour through the middle of a cell too, and
    // is asked the same way the water is: which pixel, not which tile. The
    // whole-tile answer is half a tile out along every edge and most of a tile
    // out down a flank, and it is out the same way every time — outward, into
    // the grass — so the player is walled off from ground they can see is clear.
    // tilemap_is_walkable() is deliberately not the question asked here: it
    // gives the coarse answer, which would close the tile again.
    if (s_cliff_face[ty][tx] & ((1 << CLIFF_LEVELS) - 1)) {
        int ax = (int)((px - tx * TILE_SIZE) * 16.0f / TILE_SIZE);
        int ay = (int)((py - ty * TILE_SIZE) * 16.0f / TILE_SIZE);
        if (ax < 0) ax = 0; else if (ax > 15) ax = 15;
        if (ay < 0) ay = 0; else if (ay > 15) ay = 15;
        if (cliff_pixel_solid(tx, ty, ax, ay)) return true;
    }

    int mine  = biome_at(map, tx, ty);
    int owner = field_owner_at(map, tx, ty, px, py);
    bool mine_is_solid = biome_solid(mine);

    if (biome_solid(owner)) return true;
    // A solid tile whose pixel the field gave to walkable ground is standable; asking
    // tile_ground_walkable here would call the whole tile solid and undo that.
    if (!mine_is_solid && !tile_ground_walkable(map, tx, ty)) return true;

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
    //
    // Skipped on a linked graveyard: worldgen stamps that mouth open so the
    // partner's tunnel has something to come up into, and a stone standing on
    // an open door hides a way in that is no longer hidden. Its share of the
    // handful goes to the scatter below instead, so the yard is not a stone
    // short for having a passage under it.
    int placed = 0;
    if (e->partner_idx < 0) {
        resource_nodes_add_gravestone(resources,
            (float)(e->x * TILE_SIZE), (float)(e->y * TILE_SIZE),
            1, TILE_DUNGEON_GRAVEYARD_SM, e->x, e->y);
        placed = 1;
    }

    // Scatter the remaining gravestones in a ~3-tile radius around the entrance.
    const int RADIUS = 3;
    for (int attempt = 0; attempt < 80 && placed < count; attempt++) {
        rng = rng * 1664525u + 1013904223u;
        int dx = (int)((rng >> 16) % (unsigned)(RADIUS * 2 + 1)) - RADIUS;
        rng = rng * 1664525u + 1013904223u;
        int dy = (int)((rng >> 16) % (unsigned)(RADIUS * 2 + 1)) - RADIUS;
        if (dx == 0 && dy == 0) continue; // entrance position is already taken

        // Canonical, so a stone beside the seam lands on the far side of it.
        int tx = e->x + dx, ty = e->y + dy;
        if (!in_world(&tx, &ty)) continue;
        if (!tilemap_is_walkable(map, tx, ty)) continue;
        // Same bank clearance the overlays get — a gravestone standing in
        // the shallows reads as a mistake rather than as a graveyard.
        if (!overlay_site_dry(map, tx, ty)) continue;
        if (tile_is_route(map, tx, ty)) continue;

        // Reject if another gravestone is already at this tile
        float wx = (float)(tx * TILE_SIZE), wy = (float)(ty * TILE_SIZE);
        bool conflict = false;
        for (int i = 0; i < resources->count; i++) {
            const ResourceNode* n = &resources->nodes[i];
            if (n->type != RESOURCE_GRAVESTONE) continue;
            if (fabsf(wrap_dpx(n->x - wx)) < (float)TILE_SIZE * 0.5f &&
                fabsf(wrap_dpy(n->y - wy)) < (float)TILE_SIZE * 0.5f) {
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
    // Both visible-yard scales come here; only GRAVEYARD_SM, which hides its
    // entrance under a scattered handful instead, has a spawner of its own.
    if (e->type == DUNGEON_ENT_GRAVEYARD_SM ||
        !dungeon_is_graveyard(e->type) || e->gravestones_spawned) return;
    e->gravestones_spawned = 1;

    unsigned int rng = seed
        ^ ((unsigned int)e->x * 73856093u)
        ^ ((unsigned int)e->y * 19349663u);

    // Candidate slots on a 2-tile grid inside the fence, generated from the same
    // yard dimensions the fence itself is drawn from rather than from a second
    // hand-written table -- the rows shear one tile left per row south, exactly
    // as the parallelogram walls do, so a bigger yard needs no new numbers.
    int span, H;
    graveyard_yard_size(e->type, span, H);
    const int rows = (H - 2) / 2;
    const int cols = span / 2 - 2;
    const int MAX_SLOTS = 256;
    static int slots[MAX_SLOTS][2];
    int nslots = 0;
    for (int r = 0; r < rows && nslots < MAX_SLOTS; r++) {
        int dy = 2 + r * 2;
        for (int c = 0; c < cols && nslots < MAX_SLOTS; c++) {
            slots[nslots][0] = -(span / 2) - (dy - 2) + c * 2;
            slots[nslots][1] = dy;
            nslots++;
        }
    }

    // Fill half to three quarters of the slots, so a yard reads as tended rather
    // than packed. Written as a fraction of the slots so it scales with the yard:
    // at the large yard's 36 this is exactly the 18-28 it has always placed.
    rng = rng * 1664525u + 1013904223u;
    int count = nslots / 2 + (int)((rng >> 16) % (unsigned)(nslots / 4 + 2));
    if (count > nslots) count = nslots;

    // Fisher-Yates shuffle of slot indices so the selection is random
    static int order[MAX_SLOTS];
    for (int i = 0; i < nslots; i++) order[i] = i;
    for (int i = nslots - 1; i > 0; i--) {
        rng = rng * 1664525u + 1013904223u;
        int j = (int)((rng >> 16) % (unsigned)(i + 1));
        int tmp = order[i]; order[i] = order[j]; order[j] = tmp;
    }

    for (int i = 0; i < count; i++) {
        int dx = slots[order[i]][0];
        int dy = slots[order[i]][1];
        // Canonical, so a stone beside the seam lands on the far side of it.
        int tx = e->x + dx, ty = e->y + dy;
        if (!in_world(&tx, &ty)) continue;
        if (!tilemap_is_walkable(map, tx, ty)) continue;
        // Same bank clearance the overlays get — a gravestone standing in
        // the shallows reads as a mistake rather than as a graveyard.
        if (!overlay_site_dry(map, tx, ty)) continue;
        if (tile_is_route(map, tx, ty)) continue;
        resource_nodes_add_gravestone(resources,
            (float)(tx * TILE_SIZE), (float)(ty * TILE_SIZE),
            0, 0, -1, -1);
    }
}
