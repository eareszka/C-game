#ifndef COMBAT_H
#define COMBAT_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "resource_node.h"

struct Tilemap;   // optional tile-based harvest target -- only the overworld has one

// Player-controlled weapon swing/thrust/throw state: everything about what
// the equipped weapon is doing right now. Embedded by both Overworld
// (include/overworld.h) and DungeonPlayer (include/dungeon.h), since the
// overworld and every dungeon share this mechanic completely -- only what
// they can strike differs (resource nodes plus world tiles, vs. resource
// nodes alone).
struct WeaponSwingState {
    float      tool_cd      = 0.0f;    // seconds before the next hit is allowed
    float      swing_t      = -1.0f;   // seconds into the current swing; -1 = idle
    float      swing_angle  = 0.0f;    // sweep: starting bearing. thrust: direction.
    float      swing_len    = 0.0f;    // thrust only: how far this one drives
    WeaponType swing_weapon = WEAPON_KNIFE;

    float      freeze_t     = 0.0f;    // seconds left rooted by a heavy weapon's swing

    int        throw_live   = 0;       // the one thrown object in flight, if any
    float      throw_x = 0.0f, throw_y = 0.0f;
    float      throw_dx = 0.0f, throw_dy = 0.0f;   // unit direction
    WeaponType throw_weapon = WEAPON_KNIFE;
};

// Seconds of cooldown a swing with this weapon sets. Sweeps and thrusts can use
// their own animation as the cooldown and throws scale the fire rate, so this is
// the one place that resolves it -- the swing and any HUD bar both read it, which
// is what stops the bar from describing a cooldown the weapon doesn't have.
float weapon_cooldown_seconds(WeaponType w);

// Bearing the player is looking, matching the frame ranges player_draw uses.
// World y grows downward, so down is +PI/2 and up is -PI/2.
float facing_angle(int facing);

// Attack trigger, plus advancing an already-running swing/thrust/throw, for
// one frame. hx,hy is the player's harvest-hitbox centre. tiles is the
// overworld's tile-based harvest system; pass null wherever there is none
// (every dungeon), and every tile_* strike is skipped. attack_blocked
// suppresses only the *trigger* (e.g. standing at a door/entrance prompt) --
// a swing or throw already in flight still advances regardless. cam is used
// only to retire a thrown object once it leaves view, and may be null.
//
// out must not be null: pass a scratch HarvestResult if the caller has no use
// for the result itself. Every hit this frame is appended to it, and this
// call also credits player->inventory for each one before returning.
void weapon_swing_update(WeaponSwingState* ws, Player* player, const Input* in, float dt,
                         float hx, float hy, ResourceNodeList* resources, Tilemap* tiles,
                         const Camera* cam, bool attack_blocked, HarvestResult* out);

// Ticks freeze_t down by dt if a heavy swing is still rooting the player, and
// reports whether movement should be suppressed this frame. Callers that read
// movement input should skip the read (and clear is_moving) whenever this
// returns true, the same way a completed swing frees movement again next frame.
bool weapon_swing_frozen_tick(WeaponSwingState* ws, Player* player, float dt);

// Draw whatever ws is doing right now -- a sweeping blade, a thrust, or a
// thrown object in flight -- centred on the player's harvest-hitbox at
// (px,py). Does nothing when idle.
void weapon_swing_draw(const WeaponSwingState* ws, float px, float py,
                       const Camera* cam, SDL_Renderer* ren);

#endif
