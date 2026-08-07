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

    // Swing in progress — either a blade turning around the player (sweep) or
    // one driving straight ahead (thrust), striking what it passes over.
    // swing_t is seconds in, or negative when nothing is swinging. The weapon
    // is remembered so switching mid-swing can't change what is already moving.
    float      swing_t;
    float      swing_angle;    // sweep: starting bearing. thrust: direction.
    float      swing_len;      // thrust only: how far this one drives
    WeaponType swing_weapon;

    // Seconds left rooted in place by a heavy weapon's swing. See
    // weapon_freeze_seconds(). Zero when free to move.
    float      freeze_t;

    // The one thrown object in flight, if any. It travels until it meets
    // something harvestable or leaves the screen, then is gone.
    int        throw_live;
    float      throw_x, throw_y;
    float      throw_dx, throw_dy;   // unit direction
    WeaponType throw_weapon;

} Overworld;

// Seconds of cooldown a swing with this weapon sets. Sweeps and thrusts can use
// their own animation as the cooldown and throws scale the fire rate, so this is
// the one place that resolves it — the swing and the HUD bar both read it, which
// is what stops the bar from describing a cooldown the weapon doesn't have.
float weapon_cooldown_seconds(WeaponType w);

void overworld_init(Overworld* ow, Player* player, float x, float y);
// out_harvest, if given, is filled with everything this frame's swing struck —
// one entry per node or tile, since a scythe sweep hits several at once.
// cam is needed only to retire a thrown object once it leaves the view; it is
// read, never modified, and may be null if nothing is in flight.
void overworld_update(Overworld* ow, Player* player, const Input* in, float dt,
                      ResourceNodeList* resources, Tilemap* map, const Camera* cam,
                      bool noclip = false, HarvestResult* out_harvest = nullptr);

// Draw the player sprite at any world position — used in all game states.
void player_draw(const Player* player, float world_x, float world_y,
                 const Camera* cam, SDL_Renderer* ren, SDL_Texture* sprite);

// Draw whatever the weapon is doing right now — a sweeping blade, a thrust, or
// a thrown object in flight. Does nothing when idle.
void overworld_draw_swing(const Overworld* ow, const Camera* cam, SDL_Renderer* ren);

#endif
