#ifndef ENEMY_H
#define ENEMY_H

struct BulletSpawn {
    float vx, vy;
    float radius;
    float damage;
};

class Enemy {
public:
    float x, y;
    float hp, max_hp;
    float fire_timer;

    Enemy(float x, float y, float hp)
        : x(x), y(y), hp(hp), max_hp(hp), fire_timer(1.5f) {}
    virtual ~Enemy() = default;

    // seconds between volleys
    virtual float fire_interval() const = 0;
    // fills out[] with bullets to spawn; returns count (max_out is 32)
    virtual int fire(float px, float py, BulletSpawn out[], int max_out) = 0;
    // optional per-frame update (tracking, movement, etc.)
    virtual void update(float /*dt*/, float /*px*/, float /*py*/) {}
    virtual const char* name() const = 0;

    bool is_alive() const { return hp > 0.0f; }
    void take_damage(float dmg) { hp -= dmg; if (hp < 0.0f) hp = 0.0f; }
};

// Creates enemy by id (0–49); caller owns the pointer.
Enemy* enemy_create(int enemy_id);

// Reseed enemy RNG so patterns vary between encounters.
void seed_enemy_rng(unsigned int seed);

#endif
