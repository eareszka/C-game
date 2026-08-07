#ifndef OVERWORLD_H
#define OVERWORLD_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "resource_node.h"
#include "tilemap.h"

typedef struct Overworld {
    float x, y;
    float speed;

    // Set each frame — 1 if the player's feet are on a dungeon entrance tile.
    // main.cpp reads this to trigger dungeon entry on keypress.
    int at_dungeon_entrance;
    DungeonEntranceType dungeon_type;   // valid when at_dungeon_entrance == 1
    float dungeon_difficulty;           // valid when at_dungeon_entrance == 1

    // Set each frame — 1 if the player is standing at a building door.
    int at_interior_door;
    int interior_door_idx;              // index into map->doors, valid when at_interior_door == 1

    float tool_cd;   // seconds remaining before next resource hit is allowed

    // Scythe swing: a blade making one full clockwise turn around the player,
    // striking what it passes over rather than everything at once. sweep_t is
    // seconds into that turn, or negative when no swing is running.
    float sweep_t;
    float sweep_start;   // bearing the blade set off from, radians

} Overworld;

// One full turn of the scythe, and how far the blade reaches. SWEEP_SECONDS
// doubles as the scythe's cooldown, so a held key spins continuously with no
// dead time between turns — it overrides the weapon profile's fire rate.
#define SWEEP_SECONDS 0.45f
#define SWEEP_RADIUS  80.0f

void overworld_init(Overworld* ow, Player* player, float x, float y);
// out_harvest, if given, is filled with everything this frame's swing struck —
// one entry per node or tile, since a scythe sweep hits several at once.
void overworld_update(Overworld* ow, Player* player, const Input* in, float dt,
                      ResourceNodeList* resources, Tilemap* map, bool noclip = false,
                      HarvestResult* out_harvest = nullptr);

// Draw the player sprite at any world position — used in all game states.
void player_draw(const Player* player, float world_x, float world_y,
                 const Camera* cam, SDL_Renderer* ren, SDL_Texture* sprite);

// Draw the scythe blade and its trail mid-swing. Does nothing when idle.
void overworld_draw_sweep(const Overworld* ow, const Camera* cam, SDL_Renderer* ren);

#endif
