#pragma once

using TileSolidFn = bool (*)(const void* map, float px, float py);
bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid);
