#ifndef BATTLE_H
#define BATTLE_H

#include <SDL2/SDL.h>
#include "input.h"
#include "entity.h"
#include "enemy.h"

// ── Weapon types ──────────────────────────────────────────────────────────────

struct ProjectileProfile {
    float speed;
    float damage;
    float fire_rate;
    int   count;
    float spread;
    float radius;
};

ProjectileProfile weapon_profile(WeaponType type);

// ── Arena constants ────────────────────────────────────────────────────────────

static const int ARENA_W  = 640;
static const int ARENA_H  = 480;
static const int ENEMY_X  = 320;
static const int ENEMY_Y  = 160;
static const int ENEMY_R  = 24;
static const int PLAYER_R = 12;

#define MAX_PLAYER_BULLETS 64
#define MAX_ENEMY_BULLETS  256

// ── Bullet ────────────────────────────────────────────────────────────────────

struct Bullet {
    float x, y;
    float vx, vy;
    float radius;
    float damage;
    bool  active;
    bool  bouncing;
    int   bounces;        // wall hits; deleted at 3
    bool  spawner;        // orange orb — emits sub-bullets while in flight
    float spawn_timer;
    float spawn_interval;
};

// ── Phase ─────────────────────────────────────────────────────────────────────

enum BattlePhase {
    BATTLE_PHASE_FIGHTING,
    BATTLE_PHASE_VICTORY,
    BATTLE_PHASE_DEFEAT,
};

// ── Player in battle ──────────────────────────────────────────────────────────

struct BattlePlayer {
    float x, y;
    float hp, max_hp;
    float iframes;
    float fire_timer;
    ProjectileProfile weapon;
};

// ── Battle scene ──────────────────────────────────────────────────────────────

class BattleScene {
public:
    BattleScene(Player* player, int enemy_id, WeaponType weapon);
    ~BattleScene();

    void update(const Input* in, float dt);
    void draw(SDL_Renderer* ren, SDL_Texture* player_sprite) const;

    BattlePhase get_phase() const { return _phase; }
    bool is_done() const { return _phase != BATTLE_PHASE_FIGHTING; }

private:
    BattlePhase  _phase;
    BattlePlayer _bp;
    Enemy*       _enemy;
    Player*      _player_ref;
    WeaponType   _weapon_type;
    bool         _tab_open;
    Bullet       _player_bullets[MAX_PLAYER_BULLETS];
    Bullet       _enemy_bullets[MAX_ENEMY_BULLETS];

    void _update_movement(const Input* in, float dt);
    void _update_player_fire(const Input* in, float dt);
    void _update_enemy(float dt);
    void _move_bullets(float dt);
    void _check_collisions();
    void _spawn_player_bullet(float angle);
    void _spawn_enemy_bullet(const BulletSpawn& bs);
    void _spawn_bullet_at(float ox, float oy, const BulletSpawn& bs);

    static void _fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                            Uint8 r, Uint8 g, Uint8 b, Uint8 a);
    static void _draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                                    Uint8 r, Uint8 g, Uint8 b);
    static void _draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
                          float cur, float max,
                          Uint8 fr, Uint8 fg, Uint8 fb);
};

#endif
