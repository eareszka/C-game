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
    TILE_CLIFF_WASTE_5 = 33
};

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
    int overlay[MAP_HEIGHT][MAP_WIDTH]; // trees, rocks, gold ore — drawn on top of base tile
    float cliff_peak_x, cliff_peak_y; // debug: gradient peak for minimap dot
} Tilemap;

void tilemap_build_starting_area(Tilemap* map, unsigned int seed);
// Phase 1: core map + detail within PHASE_RADIUS of center (call before game loop)
void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed);
// Phase 2: detail outside PHASE_RADIUS (run on a background thread)
void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed);

void tilemap_update(float dt); // advance hit-jitter timers
void tilemap_draw(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer);

// Hit a tree or rock tile near (px, py) within `range` pixels.
// Tall trees (two stacked TILE_TREE) share an HP pool and require more hits.
// Destroys the tile(s) on depletion. Returns 1 if destroyed, 2 if hit, 0 if miss.
int tilemap_try_hit(Tilemap* map, float px, float py, int range, float* out_rx, float* out_ry);

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y);

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y);

// Convert a minimap screen click (mx, my) to world pixel coords.
// Returns true if the click was inside the minimap area.
bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y);

#endif
