#include "battle.h"
#include <SDL2/SDL.h>
#include <math.h>
#include <string.h>

static const float PI = 3.14159265f;

// ── RNG ───────────────────────────────────────────────────────────────────────

static unsigned int s_rng = 0xBEEF1234u;

static float frand() {
    s_rng = s_rng * 1664525u + 1013904223u;
    return (float)(s_rng >> 16) / 65536.0f; // [0, 1)
}

static float frand_range(float lo, float hi) {
    return lo + frand() * (hi - lo);
}

// ── Weapon profiles ───────────────────────────────────────────────────────────

ProjectileProfile weapon_profile(WeaponType type) {
    switch (type) {
        case WEAPON_DAGGER:
            // fast, small, rapid single shots
            return { 320.0f, 4.0f, 5.0f, 1, 0.0f, 3.0f };
        case WEAPON_LONGSWORD:
            // medium speed, fires in a short burst of 3
            return { 220.0f, 8.0f, 2.0f, 3, 20.0f, 4.0f };
        case WEAPON_SPEAR:
            // very fast, narrow, single piercing shot
            return { 480.0f, 12.0f, 1.5f, 1, 0.0f, 3.0f };
        case WEAPON_AXE:
            // slow, wide spread, high damage per bullet
            return { 160.0f, 15.0f, 1.0f, 5, 60.0f, 5.0f };
        default:
            return { 320.0f, 4.0f, 5.0f, 1, 0.0f, 3.0f };
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

static bool circles_overlap(float ax, float ay, float ar,
                             float bx, float by, float br) {
    float dx = ax - bx, dy = ay - by, rsum = ar + br;
    return dx*dx + dy*dy < rsum*rsum;
}

static void fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                      Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawColor(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(ren, &rect);
}

static void draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                               Uint8 r, Uint8 g, Uint8 b) {
    SDL_SetRenderDrawColor(ren, r, g, b, 255);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderDrawRect(ren, &rect);
}

static void draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
                     float cur, float max,
                     Uint8 fr, Uint8 fg, Uint8 fb) {
    fill_rect(ren, x, y, w, h, 30, 30, 30, 255);
    if (max > 0.0f && cur > 0.0f) {
        int filled = (int)(w * cur / max);
        if (filled > w) filled = w;
        fill_rect(ren, x, y, filled, h, fr, fg, fb, 255);
    }
    draw_rect_outline(ren, x, y, w, h, 160, 160, 160);
}

// ── Bullet spawning ───────────────────────────────────────────────────────────

static void spawn_player_bullet(Battle* b, float angle) {
    const ProjectileProfile& wp = b->bp.weapon;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = b->player_bullets[i];
        if (bl.active) continue;
        bl.x      = b->bp.x;
        bl.y      = b->bp.y;
        bl.vx     = cosf(angle) * wp.speed;
        bl.vy     = sinf(angle) * wp.speed;
        bl.radius = wp.radius;
        bl.damage = wp.damage;
        bl.active = true;
        return;
    }
}

static void spawn_enemy_bullet(Battle* b, float angle, float speed,
                                float radius, float damage) {
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = b->enemy_bullets[i];
        if (bl.active) continue;
        bl.x      = (float)ENEMY_X;
        bl.y      = (float)ENEMY_Y;
        bl.vx     = cosf(angle) * speed;
        bl.vy     = sinf(angle) * speed;
        bl.radius = radius;
        bl.damage = damage;
        bl.active = true;
        return;
    }
}

// ── Enemy fire patterns ───────────────────────────────────────────────────────
// Patterns scale with iq (complexity), spd (bullet speed), luck (randomness).

static void enemy_fire(Battle* b) {
    float px = b->bp.x, py = b->bp.y;
    int   iq   = b->be.iq;
    int   spd  = b->be.spd;
    int   luck = b->be.luck;

    float bspd         = 80.0f + spd * 7.0f;
    float luck_jitter  = luck * 0.015f;  // radians of random wobble per luck point
    float aim          = atan2f(py - ENEMY_Y, px - ENEMY_X);

    auto jitter = [&]() { return frand_range(-luck_jitter, luck_jitter); };

    if (iq <= 3) {
        // single aimed shot
        spawn_enemy_bullet(b, aim + jitter(), bspd, 4.0f, 1.0f);

    } else if (iq <= 6) {
        // 3-way spread aimed at player
        for (int i = -1; i <= 1; i++)
            spawn_enemy_bullet(b, aim + i * 0.28f + jitter(), bspd, 4.0f, 1.0f);

    } else if (iq <= 9) {
        // aimed shot + 6-bullet ring
        spawn_enemy_bullet(b, aim + jitter(), bspd * 1.1f, 4.0f, 1.2f);
        for (int i = 0; i < 6; i++) {
            float a = i * (PI * 2.0f / 6.0f) + jitter();
            spawn_enemy_bullet(b, a, bspd * 0.7f, 4.0f, 0.8f);
        }

    } else {
        // 3-way fast aimed + full 8-bullet ring
        for (int i = -1; i <= 1; i++)
            spawn_enemy_bullet(b, aim + i * 0.22f + jitter(), bspd * 1.2f, 4.0f, 1.5f);
        for (int i = 0; i < 8; i++) {
            float a = i * (PI * 2.0f / 8.0f) + jitter();
            spawn_enemy_bullet(b, a, bspd * 0.85f, 4.0f, 1.0f);
        }
    }
}

// ── API ───────────────────────────────────────────────────────────────────────

void battle_start(Battle* b, Player* player, const Enemy* enemy, WeaponType weapon) {
    memset(b, 0, sizeof(*b));
    s_rng ^= SDL_GetTicks();  // seed RNG from time so patterns vary per battle

    b->phase  = BATTLE_PHASE_FIGHTING;
    b->player = player;

    // Player
    b->bp.x      = (float)ARENA_W / 2.0f;
    b->bp.y      = (float)ARENA_H - 80.0f;
    b->bp.hp     = (float)player->stats.hp;
    b->bp.max_hp = (float)player->stats.max_hp;
    b->bp.weapon = weapon_profile(weapon);

    // Enemy
    b->be.hp     = (float)enemy->stats.hp;
    b->be.max_hp = (float)enemy->stats.max_hp;
    b->be.spd    = enemy->stats.spd;
    b->be.iq     = enemy->stats.iq;
    b->be.luck   = enemy->stats.luck;

    // First shot fires after a short grace period
    float shoot_cd   = 2.0f - b->be.iq * 0.08f;
    if (shoot_cd < 0.5f) shoot_cd = 0.5f;
    b->be.fire_timer = 1.5f;  // grace period before first volley
}

void battle_update(Battle* b, const Input* in, float dt) {
    if (b->phase != BATTLE_PHASE_FIGHTING) return;

    // ── Player movement + facing + animation ──────────────────────────────────
    {
        const float PSPEED     = 160.0f;
        const float MARGIN     = 16.0f;
        const float ANIM_SPEED = 0.20f;
        float mx = 0, my = 0;

        // a newly pressed movement key unlocks facing (same as overworld)
        if (input_pressed(in, SDL_SCANCODE_LEFT)  || input_pressed(in, SDL_SCANCODE_A) ||
            input_pressed(in, SDL_SCANCODE_RIGHT) || input_pressed(in, SDL_SCANCODE_D) ||
            input_pressed(in, SDL_SCANCODE_UP)    || input_pressed(in, SDL_SCANCODE_W) ||
            input_pressed(in, SDL_SCANCODE_DOWN)  || input_pressed(in, SDL_SCANCODE_S))
            b->bp.facing_locked = 0;

        if (input_down(in, SDL_SCANCODE_LEFT)  || input_down(in, SDL_SCANCODE_A)) { mx -= 1.0f; if (!b->bp.facing_locked) b->bp.facing = 6; }
        if (input_down(in, SDL_SCANCODE_RIGHT) || input_down(in, SDL_SCANCODE_D)) { mx += 1.0f; if (!b->bp.facing_locked) b->bp.facing = 8; }
        if (input_down(in, SDL_SCANCODE_UP)    || input_down(in, SDL_SCANCODE_W)) { my -= 1.0f; if (!b->bp.facing_locked) b->bp.facing = 3; }
        if (input_down(in, SDL_SCANCODE_DOWN)  || input_down(in, SDL_SCANCODE_S)) { my += 1.0f; if (!b->bp.facing_locked) b->bp.facing = 0; }

        b->bp.is_moving = (mx != 0.0f || my != 0.0f) ? 1 : 0;

        if (mx != 0.0f && my != 0.0f) { mx *= 0.7071f; my *= 0.7071f; }

        b->bp.x += mx * PSPEED * dt;
        b->bp.y += my * PSPEED * dt;

        if (b->bp.x < MARGIN)           b->bp.x = MARGIN;
        if (b->bp.x > ARENA_W - MARGIN) b->bp.x = ARENA_W - MARGIN;
        if (b->bp.y < MARGIN)           b->bp.y = MARGIN;
        if (b->bp.y > ARENA_H - MARGIN) b->bp.y = ARENA_H - MARGIN;

        if (b->bp.is_moving) {
            b->bp.anim_timer += dt;
            if (b->bp.anim_timer >= ANIM_SPEED) {
                b->bp.anim_timer = 0.0f;
                b->bp.anim_step  = (b->bp.anim_step + 1) % 4;
            }
        } else {
            b->bp.anim_step  = 0;
            b->bp.anim_timer = 0.0f;
        }
    }

    // ── Player fire on interact (Space / Z), gated by fire_rate cooldown ────────
    {
        b->bp.fire_timer -= dt;
        bool pressed = input_pressed(in, SDL_SCANCODE_SPACE) ||
                       input_pressed(in, SDL_SCANCODE_Z);
        if (pressed && b->bp.fire_timer <= 0.0f) {
            // face toward enemy on the dominant axis, same as resource-hit logic
            float ddx = ENEMY_X - b->bp.x;
            float ddy = ENEMY_Y - b->bp.y;
            b->bp.facing        = (ddx*ddx >= ddy*ddy) ? (ddx >= 0.0f ? 8 : 6)
                                                        : (ddy >= 0.0f ? 0 : 3);
            b->bp.facing_locked = 1;

            const ProjectileProfile& wp = b->bp.weapon;
            float base_angle = atan2f(ENEMY_Y - b->bp.y, ENEMY_X - b->bp.x);
            float step = (wp.count > 1)
                         ? (wp.spread * PI / 180.0f) / (wp.count - 1)
                         : 0.0f;
            float start = base_angle - step * (wp.count - 1) * 0.5f;
            for (int i = 0; i < wp.count; i++)
                spawn_player_bullet(b, start + i * step);
            b->bp.fire_timer = 1.0f / wp.fire_rate;
        }
    }

    // ── Enemy fire ────────────────────────────────────────────────────────────
    {
        b->be.fire_timer -= dt;
        if (b->be.fire_timer <= 0.0f) {
            enemy_fire(b);
            float cd = 2.0f - b->be.iq * 0.08f;
            if (cd < 0.45f) cd = 0.45f;
            b->be.fire_timer = cd;
        }
    }

    // ── Move player bullets, check enemy collision ────────────────────────────
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = b->player_bullets[i];
        if (!bl.active) continue;
        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;

        if (bl.x < 0 || bl.x > ARENA_W || bl.y < 0 || bl.y > ARENA_H) {
            bl.active = false;
            continue;
        }
        if (circles_overlap(bl.x, bl.y, bl.radius,
                             (float)ENEMY_X, (float)ENEMY_Y, (float)ENEMY_R)) {
            b->be.hp -= bl.damage;
            if (b->be.hp < 0.0f) b->be.hp = 0.0f;
            bl.active = false;
        }
    }

    // ── Move enemy bullets, check player collision ────────────────────────────
    {
        float px = b->bp.x, py = b->bp.y;
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
            Bullet& bl = b->enemy_bullets[i];
            if (!bl.active) continue;
            bl.x += bl.vx * dt;
            bl.y += bl.vy * dt;

            if (bl.x < 0 || bl.x > ARENA_W || bl.y < 0 || bl.y > ARENA_H) {
                bl.active = false;
                continue;
            }
            if (b->bp.iframes <= 0.0f &&
                circles_overlap(bl.x, bl.y, bl.radius, px, py, (float)PLAYER_R)) {
                b->bp.hp -= bl.damage;
                if (b->bp.hp < 0.0f) b->bp.hp = 0.0f;
                b->bp.iframes = 1.5f;
                bl.active = false;
            }
        }
    }

    // ── Invincibility frames ──────────────────────────────────────────────────
    if (b->bp.iframes > 0.0f) b->bp.iframes -= dt;

    // ── Win / lose check ──────────────────────────────────────────────────────
    if (b->be.hp <= 0.0f) {
        b->player->stats.hp = (int)b->bp.hp;
        b->phase = BATTLE_PHASE_VICTORY;
    } else if (b->bp.hp <= 0.0f) {
        b->player->stats.hp = 0;
        b->phase = BATTLE_PHASE_DEFEAT;
    }
}

// ── Drawing ───────────────────────────────────────────────────────────────────

void battle_draw(const Battle* b, SDL_Renderer* ren, SDL_Texture* player_sprite) {
    // background
    fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 8, 8, 18, 255);

    // arena border
    draw_rect_outline(ren, 4, 4, ARENA_W - 8, ARENA_H - 8, 60, 60, 100);

    // ── Enemy ─────────────────────────────────────────────────────────────────
    {
        int ex = ENEMY_X, ey = ENEMY_Y;
        int hw = ENEMY_R + 4;
        Uint8 pulse = (b->phase == BATTLE_PHASE_FIGHTING) ? 200 : 80;
        fill_rect(ren, ex - hw, ey - hw, hw*2, hw*2, 40, pulse, 40, 255);
        draw_rect_outline(ren, ex - hw, ey - hw, hw*2, hw*2, 80, 255, 80);

        // enemy HP bar above sprite
        draw_bar(ren, ex - 60, ey - hw - 14, 120, 8,
                 b->be.hp, b->be.max_hp, 220, 60, 60);
    }

    // ── Player bullets (yellow) ───────────────────────────────────────────────
    SDL_SetRenderDrawColor(ren, 255, 230, 50, 255);
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        const Bullet& bl = b->player_bullets[i];
        if (!bl.active) continue;
        int r = (int)bl.radius;
        SDL_Rect rect = { (int)bl.x - r, (int)bl.y - r, r*2, r*2 };
        SDL_RenderFillRect(ren, &rect);
    }

    // ── Enemy bullets (orange-red) ────────────────────────────────────────────
    SDL_SetRenderDrawColor(ren, 255, 80, 30, 255);
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Bullet& bl = b->enemy_bullets[i];
        if (!bl.active) continue;
        int r = (int)bl.radius;
        SDL_Rect rect = { (int)bl.x - r, (int)bl.y - r, r*2, r*2 };
        SDL_RenderFillRect(ren, &rect);
    }

    // ── Player sprite (flickers during iframes) ───────────────────────────────
    {
        bool visible = b->bp.iframes <= 0.0f ||
                       ((int)(b->bp.iframes * 10.0f) % 2 == 0);
        if (visible) {
            int px = (int)b->bp.x, py = (int)b->bp.y;
            if (player_sprite) {
                static const int down_cycle[4]  = {1, 0, 2, 0};
                static const int up_cycle[4]    = {4, 3, 5, 3};
                static const int left_cycle[2]  = {7, 6};
                static const int right_cycle[2] = {9, 8};

                int facing = b->bp.facing;
                int step   = b->bp.anim_step;
                int frame;
                if      (facing >= 8) frame = b->bp.is_moving ? right_cycle[step % 2] : facing;
                else if (facing >= 6) frame = b->bp.is_moving ? left_cycle[step % 2]  : facing;
                else if (facing >= 3) frame = b->bp.is_moving ? up_cycle[step]         : facing;
                else                  frame = b->bp.is_moving ? down_cycle[step]       : facing;

                SDL_Rect src = { frame * 16, 0, 16, 24 };
                SDL_Rect dst = { px - 16, py - 24, 32, 48 };
                SDL_RenderCopy(ren, player_sprite, &src, &dst);
            } else {
                fill_rect(ren, px - 6, py - 6, 12, 12, 220, 220, 255, 255);
            }
            // hitbox outline — cyan rect, edit PLAYER_R in battle.h to resize
            draw_rect_outline(ren, px - PLAYER_R, py - PLAYER_R,
                              PLAYER_R*2, PLAYER_R*2, 0, 255, 255);
        }

        // player HP bar at bottom
        draw_bar(ren, ARENA_W/2 - 80, ARENA_H - 18, 160, 10,
                 b->bp.hp, b->bp.max_hp, 60, 200, 60);
    }

    // ── Victory / defeat overlay ──────────────────────────────────────────────
    if (b->phase == BATTLE_PHASE_VICTORY) {
        fill_rect(ren, 160, 180, 320, 70, 10, 60, 10, 220);
        draw_rect_outline(ren, 160, 180, 320, 70, 80, 255, 80);
    } else if (b->phase == BATTLE_PHASE_DEFEAT) {
        fill_rect(ren, 160, 180, 320, 70, 70, 5, 5, 220);
        draw_rect_outline(ren, 160, 180, 320, 70, 255, 50, 50);
    }
}
