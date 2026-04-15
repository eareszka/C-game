#ifndef ENTITY_H
#define ENTITY_H

#include "input.h"

typedef struct {
    int max_hp;
    int hp;

    int max_spd;
    int spd;

    int max_mag;
    int mag;

    int max_attack;
    int attack;

    int max_luck;
    int luck;

    int max_iq;
    int iq;

    int exp; //total or gained after ene killed
} Stats;

typedef struct {
    Stats stats;
    int level;

    // Visual/animation state — shared across all game states
    int   width, height;    // sprite size in pixels (32x48)
    int   facing;           // idle frame: 0=down 3=up 6=left 8=right
    int   facing_locked;    // true after a hit/action until next direction key
    int   anim_step;
    float anim_timer;
    int   is_moving;

    // Last-pressed direction for resolving opposing key conflicts
    int   last_hdir;        // -1=left, +1=right
    int   last_vdir;        // -1=up,   +1=down
} Player;

// Reads WASD/arrow keys, resolves opposing keys via last-pressed,
// updates player facing/is_moving/last_hdir/last_vdir.
// Outputs normalized dx/dy (not yet scaled by speed).
void player_read_input(Player* player, const Input* in, float* out_dx, float* out_dy);

// Advances the walk animation. Call after movement with the desired frame duration.
void player_animate(Player* player, float dt, float anim_speed);

typedef struct {
    Stats stats;
    int enemy_id;
} Enemy;

#endif
