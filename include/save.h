#ifndef SAVE_H
#define SAVE_H

#include "entity.h"
#include "tilemap.h"   // EXPLORE_W/H

// The one save file, save.dat beside the game: the world's seed, where the
// player stands on the overworld, the Player whole, and how much of the map
// they have explored, which landmarks they have opened (the map's own bits,
// tilemap_landmarks_opened: read here into the map, written from it), and
// which dungeons' chests (dungeon_chest_records).
// Written only from the TAB menu's SAVE.
// The world itself is not saved -- it regrows from the seed -- but what the
// player took out of it is (include/persist.h, since version 18): harvested
// tiles, broken gravestones and oilblooms, and each dungeon's beaten enemies
// and broken nodes, all laid back over the regrown world. Chests stay open
// (the records above), and the story's flags are kept. Bump SAVE_VERSION for
// any new block.
bool save_write(unsigned seed, float x, float y, const Player& p,
                const uint8_t explored[EXPLORE_H][EXPLORE_W]);
// False with no file, or one this build did not write (another version, cut
// short): such a save is refused, never misread.
bool save_read(unsigned* seed, float* x, float* y, Player* p,
               uint8_t explored[EXPLORE_H][EXPLORE_W]);
// True after a save_read that refused the file because it was played in
// another world (WORLDGEN_VERSION, tilemap.h): the title says so.
bool save_refused_old_world(void);

#endif
