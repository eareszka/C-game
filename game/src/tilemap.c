#include "tilemap.h"

static bool in_bounds(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

void tilemap_build_starting_area(Tilemap* map) {
    int x, y;

    // Fill everything with grass
    for (y = 0; y < MAP_HEIGHT; y++) {
        for (x = 0; x < MAP_WIDTH; x++) {
            map->tiles[y][x] = TILE_GRASS;
        }
    }

    // Border cliffs
    for (x = 0; x < MAP_WIDTH; x++) {
        map->tiles[0][x] = TILE_CLIFF;
        map->tiles[MAP_HEIGHT - 1][x] = TILE_CLIFF;
    }
    for (y = 0; y < MAP_HEIGHT; y++) {
        map->tiles[y][0] = TILE_CLIFF;
        map->tiles[y][MAP_WIDTH - 1] = TILE_CLIFF;
    }

    // Simple horizontal path through the middle
    int path_y = MAP_HEIGHT / 2;
    for (x = 2; x < MAP_WIDTH - 2; x++) {
        map->tiles[path_y][x] = TILE_PATH;
    }

    // Vertical path connecting downward
    for (y = path_y; y < MAP_HEIGHT - 3; y++) {
        map->tiles[y][8] = TILE_PATH;
    }

    // Trees cluster top-left
    for (y = 3; y <= 8; y++) {
        for (x = 3; x <= 7; x++) {
            if ((x + y) % 2 == 0) {
                map->tiles[y][x] = TILE_TREE;
            }
        }
    }

    // Water pond right side
    for (y = 6; y <= 10; y++) {
        for (x = 28; x <= 33; x++) {
            map->tiles[y][x] = TILE_WATER;
        }
    }

    // A few cliff chunks for shape
    for (x = 14; x <= 18; x++) {
        map->tiles[5][x] = TILE_CLIFF;
    }

    for (y = 18; y <= 23; y++) {
        map->tiles[y][20] = TILE_CLIFF;
    }

    // Leave path openings in borders if desired
    map->tiles[path_y][0] = TILE_PATH;
    map->tiles[path_y][MAP_WIDTH - 1] = TILE_PATH;
}

void tilemap_draw(const Tilemap* map, const Tileset* ts,
                  const Camera* cam, SDL_Renderer* renderer) {
    int x, y;
    for (y = 0; y < MAP_HEIGHT; y++) {
        for (x = 0; x < MAP_WIDTH; x++) {
            int world_x = x * TILE_SIZE;
            int world_y = y * TILE_SIZE;

            int screen_x = world_x - (int)cam->x;
            int screen_y = world_y - (int)cam->y;

            tileset_draw_tile(ts, renderer, map->tiles[y][x], screen_x, screen_y);
        }
    }
}

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y) {
    if (!in_bounds(tile_x, tile_y)) {
        return false;
    }

    int tile = map->tiles[tile_y][tile_x];

    switch (tile) {
        case TILE_GRASS:
        case TILE_PATH:
            return true;

        case TILE_TREE:
        case TILE_WATER:
        case TILE_CLIFF:
        default:
            return false;
    }
}
