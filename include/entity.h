#ifndef ENTITY_H
#define ENTITY_H

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
} Player;

typedef struct {
    Stats stats;
    int enemy_id;
} Enemy;

#endif
