#include "collision.h"

bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid) {
    return !tile_solid(map, x + HB_X1, y + HB_Y1)
        && !tile_solid(map, x + HB_X2, y + HB_Y1)
        && !tile_solid(map, x + HB_X1, y + HB_Y2)
        && !tile_solid(map, x + HB_X2, y + HB_Y2);
}

