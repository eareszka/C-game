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
    TILE_CLIFF_2 = 8,  // elevation 2
    TILE_CLIFF_3 = 9,  // elevation 3
    TILE_CLIFF_4 = 10, // elevation 4
    TILE_CLIFF_5 = 11  // elevation 5 (highest)
};

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
    float cliff_peak_x, cliff_peak_y; // debug: gradient peak for minimap dot
} Tilemap;

void tilemap_build_starting_area(Tilemap* map, unsigned int seed);
// Phase 1: core map + detail within PHASE_RADIUS of center (call before game loop)
void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed);
// Phase 2: detail outside PHASE_RADIUS (run on a background thread)
void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed);

void tilemap_draw(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer);

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y);

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y);

// Convert a minimap screen click (mx, my) to world pixel coords.
// Returns true if the click was inside the minimap area.
bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y);

#endif
