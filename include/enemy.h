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
    bool  homing         = false;
    float homing_timer   = 0.0f;  // seconds before homing turns off; 0 = never
    // A mine: sits where it was dropped for `delay` seconds, then launches at
    // the player at launch_speed, launch_off radians off the line to them.
    float delay          = 0.0f;
    float launch_speed   = 0.0f;
    float launch_off     = 0.0f;
    // A boomerang: `accel` px/s^2 along its first heading -- negative slows
    // it, stops it, and brings it back the way it came, until the enemy
    // swallows it.
    float accel          = 0.0f;
    // With min_speed set, `accel` only slows it -- down to min_speed, then
    // on at that -- instead of turning it back: a shot that eases off as it
    // nears the player.
    float min_speed      = 0.0f;
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
    // 0..1 through a wing-flapping flight, or -1 when not flying: the battle
    // plays the enemy's flap sheet (EnemySheet::flap) across it.
    virtual float flap_phase() const { return -1.0f; }
    // A Facing to draw it in -- the way it is running -- or -1 to face the
    // player as usual.
    virtual int   move_facing() const { return -1; }
    // True to idle on the alternate idle sheet (EnemySheet::alt) instead --
    // the same animation in another pose, like Paoxiao with its eye shut.
    virtual bool  alt_pose() const { return false; }
    // Called each time its idle animation reaches frame 2 -- the breath
    // frame, for a creature whose idle breathes fire -- so a volley can leave
    // exactly as the sprite shows it. Returns the bullets, like fire().
    virtual int   breathe(float /*px*/, float /*py*/, BulletSpawn /*out*/[], int /*max_out*/) { return 0; }
    // Damage for touching its body (whole HP bars, like a bullet's); 0 for
    // an enemy that is harmless to touch.
    virtual float contact_damage() const { return 0.0f; }
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

// The monster part enemy_id drops when beaten.
MonsterPart enemy_part(int enemy_id);

// The colour enemy_id's bullets are drawn in.
SDL_Color enemy_bullet_color(int enemy_id);

// Reseed enemy RNG so patterns vary between encounters.
void seed_enemy_rng(unsigned int seed);

#endif
