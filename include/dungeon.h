#ifndef DUNGEON_H
#define DUNGEON_H

#include <SDL2/SDL.h>
#include <stdint.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "tilemap.h"   // DungeonEntranceType

#define DMAP_W    256
#define DMAP_H    256
#define DMAP_TILE 16

enum DungeonTile : uint8_t {
    DNG_WALL  = 0,
    DNG_FLOOR = 1,
    DNG_ENTRY = 2,   // spawn point / stairs back up
    DNG_EXIT  = 3,   // goal / stairs deeper
};

struct DungeonMap {
    uint8_t tiles[DMAP_H][DMAP_W];
    int entry_x, entry_y;
    int exit_x,  exit_y;
    DungeonEntranceType type;
    float difficulty;
};

struct DungeonPlayer {
    float x, y;
    float speed;
    int   at_exit;    // 1 if player centre is over DNG_EXIT tile
    int   at_entry;   // 1 if player centre is over DNG_ENTRY tile (exit back to overworld)
};

void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type,
                      float difficulty, unsigned int seed);
// Reposition DNG_ENTRY / DNG_EXIT so they face the overworld direction.
// exit_angle: angle (radians) pointing from the DNG_ENTRY portal toward the DNG_EXIT portal
// in overworld tile-space. Both tiles are moved to the floor tiles that best align with that axis.
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle);
// from_exit=0: spawn at DNG_ENTRY; from_exit=1: spawn at DNG_EXIT (connected entrance)
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit);
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, const DungeonMap* dmap, bool noclip = false);
void dungeon_draw(const DungeonMap* dmap, const Camera* cam, SDL_Renderer* ren);

#endif
