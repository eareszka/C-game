#ifndef PERSIST_H
#define PERSIST_H

#include <stdint.h>
#include <stdio.h>

// What the player has taken out of the world, for good: nothing grows back
// and no beaten enemy returns (the user). The world itself still regrows from
// its seed; these are applied over it, and saved (src/save.cpp).
//
//   tiles:     every overworld tile key (tile_key, y * MAP_WIDTH + x) whose
//              harvestable overlay was destroyed, and every tile a destroyed
//              gravestone stood on.
//   oilblooms: a bit per oilbloom site (tilemap_spawn_oilbloom's index).
//   dungeons:  per dungeon (its interior seed, as DungeonChestRecord), a bit
//              per spawner whose enemy was beaten, and a bit per dungeon_rocks
//              node broken (ore veins, opened chests' wood).
//
// Read by the phase-2 world thread while the game records, so every call
// takes one lock.

struct DungeonDeadRecord { uint32_t seed, pad; uint64_t spawners; uint64_t nodes; };

void persist_clear(void);

void persist_tile_add(uint32_t key);
bool persist_tile_has(uint32_t key);
// Each recorded tile key, under the lock; fn must not call back in here.
void persist_tiles_each(void (*fn)(uint32_t key, void* ctx), void* ctx);

void persist_oilbloom_add(int site);
bool persist_oilbloom_has(int site);

void persist_spawner_beaten(uint32_t dungeon_seed, int spawner);
void persist_node_broken(uint32_t dungeon_seed, int node);
// The dungeon's record, or all-zero when it has none.
DungeonDeadRecord persist_dungeon(uint32_t dungeon_seed);

// The save's block: counts, then the lists. False on a short or bad read.
bool persist_write(FILE* f);
bool persist_read(FILE* f);

#endif
