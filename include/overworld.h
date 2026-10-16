#ifndef OVERWORLD_H
#define OVERWORLD_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "resource_node.h"
#include "tilemap.h"
#include "combat.h"

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

    // Weapon swing/throw state -- see combat.h. Shared machinery with
    // every dungeon (DungeonPlayer, include/dungeon.h).
    WeaponSwingState swing;

    // On the raft: it holds the course it was launched on -- the way the
    // player walked onto the water -- with no steering, until the feet reach
    // land, or it runs into something it cannot land on, where it waits for a
    // new push off. The player stands still on it.
    bool  sailing;
    float sail_dx, sail_dy;   // unit course
    float sail_t;             // seconds since this push off

} Overworld;

// Aboard the boat (Player::at_sea), how fast it goes: half again a walk.
constexpr float BOAT_SPEED = PLAYER_WALK_SPEED * 1.5f;

void overworld_init(Overworld* ow, Player* player, float x, float y);
// out_harvest, if given, is filled with everything this frame's swing struck —
// one entry per node or tile, since a scythe sweep hits several at once.
// cam is needed only to retire a thrown object once it leaves the view; it is
// read, never modified, and may be null if nothing is in flight.
// Arriving outside: stood before the middle of the house door that opens
// interior_id, or of the way in of the entrance at tile (tx, ty), a pixel clear
// of its hitbox and facing out (stand_clear, collision.h).
void overworld_stand_before_door(Overworld* ow, Player* player, const Tilemap* map, int interior_id);
// Before door `idx` of map->doors: the one walked into, whichever room it opens
// (a village's doors open the start town's rooms, so the room says nothing).
void overworld_stand_before_door_idx(Overworld* ow, Player* player, const Tilemap* map, int idx);
void overworld_stand_before_entrance(Overworld* ow, Player* player, const Tilemap* map, int tx, int ty);
// Whether feet centred at (feet_x, feet_y) are in a dungeon entrance's way in.
bool overworld_entrance_at(const Tilemap* map, float feet_x, float feet_y);
void overworld_update(Overworld* ow, Player* player, const Input* in, float dt,
                      ResourceNodeList* resources, Tilemap* map, const Camera* cam,
                      bool noclip = false, HarvestResult* out_harvest = nullptr);

// Draw the player sprite at any world position — used in all game states.
// `frame` is the sheet frame to draw instead of the walk's: a swing frame
// while a weapon is in use (WeaponSwingState::body_frame), -1 for the walk.
void player_draw(const Player* player, float world_x, float world_y,
                 const Camera* cam, SDL_Renderer* ren, SDL_Texture* sprite, int frame = -1);

// Draw whatever the weapon is doing right now — a sweeping blade, a stab, or
// a thrown object in flight. Does nothing when idle.
void overworld_draw_swing(const Overworld* ow, const Camera* cam, SDL_Renderer* ren);

#endif
