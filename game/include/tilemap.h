#ifndef TILEMAP_H
#define TILEMAP_H

#include <SDL2/SDL.h>
#include <stdbool.h>
#include "tileset.h"
#include "camera.h"

#define MAP_WIDTH  100
#define MAP_HEIGHT 80
#define TILE_SIZE  32

enum TileId {
    TILE_GRASS  = 0,
    TILE_PATH   = 1,
    TILE_TREE   = 2,
    TILE_WATER  = 3,
    TILE_CLIFF  = 4
};

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
} Tilemap;

void tilemap_build_starting_area(Tilemap* map);

void tilemap_draw(const Tilemap* map, const Tileset* ts,
                  const Camera* cam, SDL_Renderer* renderer);

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y);

#endif
