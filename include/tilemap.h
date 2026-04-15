#ifndef TILEMAP_H
#define TILEMAP_H

#include <SDL2/SDL.h>
#include "camera.h"

#define MAP_WIDTH  3000
#define MAP_HEIGHT 3000
#define TILE_SIZE  32

enum TileId {
    TILE_GRASS   = 0,
    TILE_PATH    = 1,
    TILE_TREE    = 2,
    TILE_WATER   = 3,
    TILE_CLIFF   = 4,  // elevation 1 (lowest)
    TILE_ROCK    = 5,
    TILE_RIVER   = 6,
    TILE_HUB     = 7,
    TILE_CLIFF_2      = 8,  // elevation 2
    TILE_CLIFF_3      = 9,  // elevation 3
    TILE_CLIFF_4      = 10, // elevation 4
    TILE_CLIFF_5      = 11, // elevation 5 (highest)
    TILE_CLIFF_EDGE_1 = 12, // south face: drop from elev 1 → 0
    TILE_CLIFF_EDGE_2 = 13, // south face: drop from elev 2 → 1
    TILE_CLIFF_EDGE_3 = 14, // south face: drop from elev 3 → 2
    TILE_CLIFF_EDGE_4 = 15, // south face: drop from elev 4 → 3
    TILE_CLIFF_EDGE_5 = 16, // south face: drop from elev 5 → 4
    TILE_SAND         = 17, // desert biome ground
    TILE_SNOW         = 18, // snow biome (map edges)
    TILE_WASTELAND    = 19, // wasteland biome (map edges)
    TILE_LAVA         = 20, // lava pools/streams inside wasteland
    TILE_MEADOW       = 21, // open plains biome (sparse trees)
    TILE_POND         = 22, // small water features inside meadows
    TILE_GOLD_ORE     = 23, // gold ore vein — spawns at high elevation / in caves
    // Snow-biome cliff variants (body only — edges stay brown)
    TILE_CLIFF_SNOW_1 = 24,
    TILE_CLIFF_SNOW_2 = 25,
    TILE_CLIFF_SNOW_3 = 26,
    TILE_CLIFF_SNOW_4 = 27,
    TILE_CLIFF_SNOW_5 = 28,
    // Wasteland-biome cliff variants (body only — edges stay brown)
    TILE_CLIFF_WASTE_1 = 29,
    TILE_CLIFF_WASTE_2 = 30,
    TILE_CLIFF_WASTE_3 = 31,
    TILE_CLIFF_WASTE_4 = 32,
    TILE_CLIFF_WASTE_5 = 33,
    // East/west side-face tiles (one per elevation layer, same brown gradient as edges)
    TILE_CLIFF_SIDE_1 = 34,
    TILE_CLIFF_SIDE_2 = 35,
    TILE_CLIFF_SIDE_3 = 36,
    TILE_CLIFF_SIDE_4 = 37,
    TILE_CLIFF_SIDE_5 = 38,
    // SW outer corner (where south face meets west/east side face at bottom-left)
    TILE_CLIFF_CORNER_SW_1 = 39,
    TILE_CLIFF_CORNER_SW_2 = 40,
    TILE_CLIFF_CORNER_SW_3 = 41,
    TILE_CLIFF_CORNER_SW_4 = 42,
    TILE_CLIFF_CORNER_SW_5 = 43,
    // SE outer corner (where south face meets east/west side face at bottom-right)
    TILE_CLIFF_CORNER_SE_1 = 44,
    TILE_CLIFF_CORNER_SE_2 = 45,
    TILE_CLIFF_CORNER_SE_3 = 46,
    TILE_CLIFF_CORNER_SE_4 = 47,
    TILE_CLIFF_CORNER_SE_5 = 48,
    // NW inner corner (concave: where north back-face meets west side-face)
    TILE_CLIFF_CORNER_NW_1 = 49,
    TILE_CLIFF_CORNER_NW_2 = 50,
    TILE_CLIFF_CORNER_NW_3 = 51,
    TILE_CLIFF_CORNER_NW_4 = 52,
    TILE_CLIFF_CORNER_NW_5 = 53,
    // NE inner corner (concave: where north back-face meets east side-face)
    TILE_CLIFF_CORNER_NE_1 = 54,
    TILE_CLIFF_CORNER_NE_2 = 55,
    TILE_CLIFF_CORNER_NE_3 = 56,
    TILE_CLIFF_CORNER_NE_4 = 57,
    TILE_CLIFF_CORNER_NE_5 = 58,
    // Dungeon entrance (4x4 tile stamp, solid dark archway)
    TILE_DUNGEON = 59,
    // Blueprint placeholder — marks unconfigured cells inside a town footprint
    TILE_BLUEPRINT = 60,
    // Village placeholder — orange/black checkerboard until sprites are added
    TILE_VILLAGE_PLACEHOLDER = 61,
    // Castle placeholder — black/white checkerboard until sprites are added
    TILE_CASTLE_PLACEHOLDER = 62,
    // Dungeon entrance variants — one per archetype, replaces generic TILE_DUNGEON
    TILE_DUNGEON_CAVE         = 63,
    TILE_DUNGEON_RUINS        = 64,
    TILE_DUNGEON_GRAVEYARD_SM = 65,
    TILE_DUNGEON_GRAVEYARD_LG = 66,
    TILE_DUNGEON_OASIS        = 67,
    TILE_DUNGEON_PYRAMID      = 68,
    TILE_DUNGEON_STONEHENGE   = 69,
    TILE_DUNGEON_LARGE_TREE   = 70,
};

typedef enum {
    DUNGEON_ENT_CAVE         = 0,
    DUNGEON_ENT_RUINS        = 1,
    DUNGEON_ENT_GRAVEYARD_SM = 2,
    DUNGEON_ENT_GRAVEYARD_LG = 3,
    DUNGEON_ENT_OASIS        = 4,
    DUNGEON_ENT_PYRAMID      = 5,
    DUNGEON_ENT_STONEHENGE   = 6,
    DUNGEON_ENT_LARGE_TREE   = 7,
} DungeonEntranceType;

typedef struct {
    int x, y;                  // top-left tile coordinate of the entrance stamp
    int size;                  // 0 = small (1×1 tile), 1 = large (2×2 tiles)
    DungeonEntranceType type;  // entrance archetype — drives interior layout + skin
    int cliff_level;           // 0 = flat, 1–5 = elevation tier at placement
    float difficulty;          // 0.0–1.0: straight average of dist_norm and elev_norm
    int gravestones_spawned;   // GRAVEYARD_SM only: 0 until resource nodes are spawned
    int partner_idx;           // index into dungeon_entrances[] of connected partner, or -1
} DungeonEntrance;

typedef struct {
    int x, y;    // top-left tile coordinate where the town was stamped
    int index;   // which of the hand-crafted towns this is
} TownPlacement;

typedef struct {
    int x, y;    // top-left tile coordinate where the village was stamped
    int variant; // which of the village blueprint variants was used
} VillagePlacement;

typedef struct {
    int x, y;
    int type; // 0=ocean, 1=mountain, 2=lava, 3=dungeon (placed via dungeon diving)
} CastlePlacement;

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
    int overlay[MAP_HEIGHT][MAP_WIDTH]; // trees, rocks, gold ore — drawn on top of base tile
    float cliff_peak_x, cliff_peak_y; // debug: gradient peak for minimap dot
    DungeonEntrance dungeon_entrances[300];
    int num_dungeon_entrances;
    TownPlacement    towns[3];         // filled during phase2
    VillagePlacement villages[15];     // filled during phase2
    int num_villages;
    CastlePlacement  castles[4];       // [0-2] placed in phase2; [3] placed via dungeon diving
} Tilemap;

// Forward declare to avoid circular include — resource_node.h includes no tilemap types.
struct ResourceNodeList;

void tilemap_build_starting_area(Tilemap* map, unsigned int seed);
// Phase 1: core map + detail within PHASE_RADIUS of center (call before game loop)
void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed);
// Phase 2: detail outside PHASE_RADIUS (run on a background thread)
void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed);

void tilemap_update(float dt); // advance hit-jitter timers
void tilemap_draw(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer);

// Pre-render all tile types into small textures so tilemap_draw uses one RenderCopy
// per tile instead of ~65 RenderFillRect calls. Call once after creating the renderer.
void tilemap_init_tile_cache(SDL_Renderer* renderer);
void tilemap_free_tile_cache(void);

// Hit a tree or rock tile near (px, py) within `range` pixels.
// Tall trees (two stacked TILE_TREE) share an HP pool and require more hits.
// Destroys the tile(s) on depletion. Returns 1 if destroyed, 2 if hit, 0 if miss.
int tilemap_try_hit(Tilemap* map, float px, float py, int range, float* out_rx, float* out_ry);

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y);

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y);
// TileSolidFn-compatible wrapper: returns true if pixel (px,py) is on a non-walkable tile.
bool tilemap_pixel_solid(const void* map, float px, float py);

// GRAVEYARD_SM entrances hide their entrance tile under gravestones.
// Call this from the main thread (not the gen thread) when the player gets close.
// Scatters 5–10 RESOURCE_GRAVESTONE nodes; one hides the entrance tile.
// seed should be derived from the world seed + entrance position.
// GRAVEYARD_SM: hidden entrance under one of 5–10 randomly scattered gravestones.
void tilemap_spawn_graveyard_nodes(Tilemap* map, ResourceNodeList* resources,
                                   int entrance_idx, unsigned int seed);

// GRAVEYARD_LG: 10–20 organized gravestones around the visible mausoleum entrance.
void tilemap_spawn_graveyard_lg_nodes(Tilemap* map, ResourceNodeList* resources,
                                      int entrance_idx, unsigned int seed);

// Convert a minimap screen click (mx, my) to world pixel coords.
// Returns true if the click was inside the minimap area.
bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y);

#endif
