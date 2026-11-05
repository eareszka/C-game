#pragma once
#include <functional>
#include <stdint.h>
#include <unordered_map>
#include <vector>
#include "resident_path.h"

// A walking chaser's way to the player (the user, 2026-10-28: "they should try
// go find the path to the player. if the enemy is at an unaccesable area such
// as an island/different elevation they shouldnt chase").
//
// The ground is asked on a lattice of points CHASE_STEP apart, half an
// overworld or dungeon tile (the narrowest slot the art makes is that wide,
// collision.h), a step between two of them by the point midway. What it
// answers is kept in a ChaseCache, one a map: the ground does not move, and a
// pack round one spot asks after the same points again and again. Clear it
// when the map changes (another dungeon, another world).
struct ChaseCache {
    std::unordered_map<uint64_t, uint8_t> fit;
    void clear() { fit.clear(); }
};

// The way from the chaser at (sx, sy) to the player at (px, py), searched only
// inside the box (half_w, half_h) round the player -- the chase's own range,
// past which it would lose them anyway -- so a way round a whole mountain is no
// way. fits(x, y): whether the chaser's feet, centred there, may stand. The
// route is waypoints in straight runs, from after (sx, sy) to (px, py), left
// empty unless there is one.
//
// budget: how many points of ground not yet in the cache one search may ask
// (a few microseconds each). Past it the search stops UNSURE; what it asked is
// kept, so the same search a frame later goes further, and a first look over
// open country is spread over a few frames rather than stalling one.
enum ChaseWay { CHASE_UNSURE = -1, CHASE_NONE = 0, CHASE_WAY = 1 };
// The game's budget a frame (src/main.cpp chase_aim; tools/chasecheck.cpp times it).
static const int CHASE_ASKS = 800;
ChaseWay chase_route(ChaseCache* cache, float sx, float sy, float px, float py, float half_w, float half_h,
                     const std::function<bool(float, float)>& fits, std::vector<ResidentPoint>& route,
                     int budget = 1 << 30);

// Whether the straight walk from (sx, sy) to (px, py) fits all the way, asked
// every few pixels (the feet are wider than the gap between asks).
bool chase_straight(float sx, float sy, float px, float py, const std::function<bool(float, float)>& fits);
