#pragma once
#include <functional>
#include <vector>
#include <cstddef>
struct ResidentPoint { float x,y; };
struct Tilemap;
// Town 0's door into this room (map->doors index), -1 if none.
int resident_town_door(const Tilemap* map,int interior);
// Where someone stands just outside that door, and just inside the room: sprite origins.
ResidentPoint resident_outside(const Tilemap* map,int door);
ResidentPoint resident_entry(int interior);
// Outdoors, keeping to the trail: a straight walk over the grass from start
// to the nearest trail point it can reach (within 16 tiles; past that, a
// grass search to the nearest trail point), the trail itself (only trail
// cells are searched, so it is quick), and the same off it to target.
// route ends at target and starts after start (route_start), as
// resident_find_route's does.
bool resident_trail_route(const Tilemap* map,ResidentPoint start,ResidentPoint target,
    std::vector<ResidentPoint>& route,ResidentPoint& route_start,size_t& next_point);
// Straight over any ground, trail or not: the shortest walk (searched round
// both ends, a coarse grid first). Same route contract as above.
bool resident_grass_route(const Tilemap* map,ResidentPoint start,ResidentPoint target,
    std::vector<ResidentPoint>& route,ResidentPoint& route_start,size_t& next_point);
bool resident_find_route(ResidentPoint start,ResidentPoint target,int step,int ox,int oy,int w,int h,
    bool rejoin,const std::function<bool(ResidentPoint)>& fits,
    const std::function<bool(ResidentPoint,ResidentPoint,bool)>& segment,
    std::vector<ResidentPoint>& route,ResidentPoint& route_start,size_t& next_point,
    const std::function<float(ResidentPoint)>& weight=nullptr);   // a step's cost multiplier (>= 1), e.g. off the trail
// Whether every position a straight walk from a to b stands at fits: each
// whole-pixel cell the line crosses is asked once (feet fit exactly when their
// floored pixel does), so no corner of a diagonal is skipped as sampling does.
bool resident_way_fits(ResidentPoint a,ResidentPoint b,const std::function<bool(ResidentPoint)>& fits);
// Walk a found route up to `budget` pixels, facing along each leg. Whether it moved.
bool resident_follow_route(const std::vector<ResidentPoint>& route,size_t& next_point,ResidentPoint route_start,
    float& x,float& y,int& facing,float budget);
