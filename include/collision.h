#pragma once

constexpr int HB_X1 = 10;  // left edge
constexpr int HB_X2 = 26;  // right edge
constexpr int HB_Y1 = 30;  // top of feet
constexpr int HB_Y2 = 46;  // bottom of feet

using TileSolidFn = bool (*)(const void* map, float px, float py);

bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid);
