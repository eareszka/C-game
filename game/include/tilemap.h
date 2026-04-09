#ifndef TILEMAP_H
#define TILEMAP_H

#include <SDL2/SDL.h>
#include "camera.h"

#define MAP_WIDTH  3000
#define MAP_HEIGHT 3000
#define TILE_SIZE  32

enum TileId {
    TILE_GRASS  = 0,
    TILE_PATH   = 1,
    TILE_TREE   = 2,
    TILE_WATER  = 3,
    TILE_CLIFF  = 4,
    TILE_ROCK   = 5,
    TILE_RIVER  = 6,
    TILE_HUB    = 7
};

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
} Tilemap;

void tilemap_build_starting_area(Tilemap* map, unsigned int seed);

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
