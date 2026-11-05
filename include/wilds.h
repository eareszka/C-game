#ifndef WILDS_H
#define WILDS_H

#include <stdint.h>
#include "tilemap.h"

// The wilds: enemy packs out in the country, away from the roads (the user,
// 2026-10-27: "the player isnt really incentivized to go off the trail").
// The world is cut into WILD_CHUNK-tile squares and each holds one pack or
// none, the same every time for a seed. None near a road, a trail, a town or
// the start; past that the odds and the pack's size climb with the distance
// to the nearest track, and its tier with the distance out (as a dungeon's).
// The game lets a square's pack loose as it comes near the screen
// (src/main.cpp); a member beaten is beaten for good (persist.h).
#define WILD_CHUNK     24
#define WILD_CHUNKS_X  ((MAP_WIDTH  + WILD_CHUNK - 1) / WILD_CHUNK)
#define WILD_CHUNKS_Y  ((MAP_HEIGHT + WILD_CHUNK - 1) / WILD_CHUNK)
#define WILD_PACK_MAX  3
// Tiles from a track inside which nothing waits, and the distance at which
// the wilds are at their thickest.
#define WILD_ROAD_CLEAR 10
#define WILD_ROAD_DEEP  80

struct WildPack {
    int   n;                       // 0: the square holds nothing
    float x[WILD_PACK_MAX], y[WILD_PACK_MAX];   // each member's middle, world pixels
    int   enemy[WILD_PACK_MAX];
    int   road;                    // tiles to the nearest track (capped)
    float difficulty;              // 0..1, as a dungeon's
};

// The pack square (cx, cy) holds. Asks only the finished map, so call it on
// ground phase 2 has laid.
void wild_pack(const Tilemap* map, unsigned seed, int cx, int cy, WildPack* out);
// Tiles from (tx, ty) to the nearest road or trail, by the square ring it lies
// on; cap if there is none within cap.
int wild_road_distance(const Tilemap* map, int tx, int ty, int cap);
// A member's one number: what its win is kept by (persist_wild_*).
inline uint32_t wild_key(int cx, int cy, int slot) {
    return ((uint32_t)cy * WILD_CHUNKS_X + (uint32_t)cx) * WILD_PACK_MAX + (uint32_t)slot;
}

#endif
