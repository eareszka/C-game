#ifndef ENEMY_H
#define ENEMY_H

#include "entity.h"

struct BulletSpawn {
    float vx, vy;
    float radius;
    float damage;
    bool  bouncing       = false;
    bool  spawner        = false;
    float spawn_interval = 0.0f;
};

struct WeaponMults {
    float knife, club, dagger, axe, halberd, katana, scythe;
};

class Enemy {
public:
    float x, y;
    float hp, max_hp;
    float fire_timer;
    WeaponMults mults;

    Enemy(float x, float y, float hp, WeaponMults m)
        : x(x), y(y), hp(hp), max_hp(hp), fire_timer(1.5f), mults(m) {}
    virtual ~Enemy() = default;

    virtual float fire_interval() const = 0;
    virtual int   fire(float px, float py, BulletSpawn out[], int max_out) = 0;
    virtual void  update(float /*dt*/, float /*px*/, float /*py*/) {}
    virtual const char* name() const = 0;

    float damage_mult(WeaponType wt) const {
        switch (wt) {
            case WEAPON_KNIFE:   return mults.knife;
            case WEAPON_CLUB:    return mults.club;
            case WEAPON_DAGGER:  return mults.dagger;
            case WEAPON_AXE:     return mults.axe;
            case WEAPON_HALBERD: return mults.halberd;
            case WEAPON_KATANA:  return mults.katana;
            case WEAPON_SCYTHE:  return mults.scythe;
            default:             return 1.0f;
        }
    }

    bool is_alive() const { return hp > 0.0f; }
    void take_damage(float dmg) { hp -= dmg; if (hp < 0.0f) hp = 0.0f; }
};

// Creates enemy by id (0–49); caller owns the pointer.
Enemy* enemy_create(int enemy_id);

// Reseed enemy RNG so patterns vary between encounters.
void seed_enemy_rng(unsigned int seed);

#endif
