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
} Player;

typedef struct {
    Stats stats;
    int enemy_id;
} Enemy;

#endif
