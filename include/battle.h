#ifndef BATTLE_H
#define BATTLE_H

#include <SDL2/SDL.h>
#include "input.h"
#include "entity.h"

// ── Weapon types ──────────────────────────────────────────────────────────────

enum WeaponType {
    WEAPON_DAGGER,
    WEAPON_LONGSWORD,
    WEAPON_SPEAR,
    WEAPON_AXE,
};

struct ProjectileProfile {
    float speed;      // pixels per second
    float damage;     // damage per hit
    float fire_rate;  // volleys per second
    int   count;      // bullets per volley
    float spread;     // total arc in degrees (0 = single straight shot)
    float radius;     // visual + hitbox radius in pixels
};

ProjectileProfile weapon_profile(WeaponType type);

// ── Arena ─────────────────────────────────────────────────────────────────────

static const int ARENA_W  = 640;
static const int ARENA_H  = 480;
static const int ENEMY_X  = 320;  // fixed enemy position
static const int ENEMY_Y  = 160;
static const int ENEMY_R  = 24;   // enemy hitbox radius
static const int PLAYER_R = 12;   // player hitbox radius — adjust to taste

// ── Bullet pools ──────────────────────────────────────────────────────────────

#define MAX_PLAYER_BULLETS 64
#define MAX_ENEMY_BULLETS  256

struct Bullet {
    float x, y;
    float vx, vy;
    float radius;
    float damage;
    bool  active;
};

// ── Phases ────────────────────────────────────────────────────────────────────

enum BattlePhase {
    BATTLE_PHASE_FIGHTING,
    BATTLE_PHASE_VICTORY,
    BATTLE_PHASE_DEFEAT,
};

// ── Internal state ────────────────────────────────────────────────────────────

struct BattlePlayer {
    float x, y;
    float hp, max_hp;
    float iframes;      // invincibility seconds remaining after a hit
    float fire_timer;   // countdown to next volley
    ProjectileProfile weapon;

    // sprite animation — mirrors overworld state
    int   facing;        // 0=down 3=up 6=left 8=right
    int   facing_locked; // set when firing, cleared on movement key press
    int   anim_step;
    float anim_timer;
    int   is_moving;
};

struct BattleEnemy {
    float hp, max_hp;
    float fire_timer;   // countdown to next volley
    int   spd, iq, luck;
};

// ── Main struct ───────────────────────────────────────────────────────────────

struct Battle {
    BattlePhase  phase;
    BattlePlayer bp;
    BattleEnemy  be;
    Player*      player;  // written back on exit

    Bullet player_bullets[MAX_PLAYER_BULLETS];
    Bullet enemy_bullets[MAX_ENEMY_BULLETS];
};

// ── API ───────────────────────────────────────────────────────────────────────

void battle_start(Battle* b, Player* player, const Enemy* enemy, WeaponType weapon);
void battle_update(Battle* b, const Input* in, float dt);
void battle_draw(const Battle* b, SDL_Renderer* ren, SDL_Texture* player_sprite);

#endif
