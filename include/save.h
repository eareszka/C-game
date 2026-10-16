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
// ponytail: the world itself is not saved -- it regrows from the seed, so
// harvested nodes, broken gravestones and dungeon maps come back; their
// chests stay open (the records above). Add a flags block here when bosses and
// quests need one, and bump SAVE_VERSION.
bool save_write(unsigned seed, float x, float y, const Player& p,
                const uint8_t explored[EXPLORE_H][EXPLORE_W]);
// False with no file, or one this build did not write (another version, cut
// short): such a save is refused, never misread.
bool save_read(unsigned* seed, float* x, float* y, Player* p,
               uint8_t explored[EXPLORE_H][EXPLORE_W]);

#endif
