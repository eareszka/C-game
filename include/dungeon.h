#ifndef DUNGEON_H
#define DUNGEON_H

#include <SDL2/SDL.h>
#include <stdint.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "tilemap.h"   // DungeonEntranceType

#define DMAP_W          768
#define DMAP_H          512
#define DMAP_TILE       32
#define DUNGEON_FOV_RADIUS  12   // visible tile radius around player

enum DungeonTile : uint8_t {
    DNG_WALL  = 0,
    DNG_FLOOR = 1,
    DNG_ENTRY = 2,   // spawn point / stairs back up
    DNG_EXIT  = 3,   // goal / stairs deeper
};

struct DungeonMap {
    uint8_t tiles[DMAP_H][DMAP_W];
    uint8_t explored[DMAP_H][DMAP_W];  // 0=never seen, 1=seen at least once
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
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle);
// from_exit=0: spawn at DNG_ENTRY; from_exit=1: spawn at DNG_EXIT (connected entrance)
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit);
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, DungeonMap* dmap, bool noclip = false);
void dungeon_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                  const Camera* cam, SDL_Renderer* ren, bool show_all = false);
void dungeon_minimap_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                          SDL_Renderer* ren, int screen_w, int screen_h,
                          bool show_all = false);

#endif
