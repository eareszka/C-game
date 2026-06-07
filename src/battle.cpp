#include "battle.h"
#include "core.h"
#include <SDL2/SDL.h>
#include <math.h>
#include <string.h>

static const float PI  = 3.14159265f;
static const float TAU = 6.28318530f;

// ── Weapon profiles ───────────────────────────────────────────────────────────

ProjectileProfile weapon_profile(WeaponType type) {
    // {speed, damage, fire_rate, count, spread_deg, radius}
    switch (type) {
        case WEAPON_KNIFE:   return { 280.0f,  8.0f, 1.8f, 1,  0.0f, 3.0f };
        case WEAPON_CLUB:    return { 140.0f, 14.0f, 0.8f, 1,  0.0f, 7.0f };
        case WEAPON_DAGGER:  return { 320.0f,  6.0f, 2.2f, 1,  0.0f, 3.0f };
        case WEAPON_AXE:     return { 160.0f, 18.0f, 0.7f, 5, 60.0f, 5.0f };
        case WEAPON_HALBERD: return { 500.0f, 16.0f, 0.6f, 1,  0.0f, 4.0f };
        case WEAPON_KATANA:  return { 240.0f, 13.0f, 1.4f, 2, 15.0f, 4.0f };
        case WEAPON_SCYTHE:  return { 200.0f, 17.0f, 0.9f, 3, 30.0f, 4.0f };
        default:             return { 320.0f,  6.0f, 2.2f, 1,  0.0f, 3.0f };
    }
}

static const char* weapon_name(WeaponType type) {
    switch (type) {
        case WEAPON_KNIFE:   return "KNIFE";
        case WEAPON_CLUB:    return "CLUB";
        case WEAPON_DAGGER:  return "DAGGER";
        case WEAPON_AXE:     return "AXE";
        case WEAPON_HALBERD: return "HALBERD";
        case WEAPON_KATANA:  return "KATANA";
        case WEAPON_SCYTHE:  return "SCYTHE";
        default:             return "UNKNOWN";
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

static bool circles_overlap(float ax, float ay, float ar,
                             float bx, float by, float br) {
    float dx = ax - bx, dy = ay - by, rsum = ar + br;
    return dx*dx + dy*dy < rsum*rsum;
}

// ── BattleScene ───────────────────────────────────────────────────────────────

BattleScene::BattleScene(Player* player, int enemy_id, WeaponType weapon) {
    memset(_player_bullets, 0, sizeof(_player_bullets));
    memset(_enemy_bullets,  0, sizeof(_enemy_bullets));

    _phase       = BATTLE_PHASE_FIGHTING;
    _player_ref  = player;
    _weapon_type = weapon;
    _tab_open    = false;

    _bp = {};
    _bp.x      = ARENA_W * 0.5f;
    _bp.y      = ARENA_H - 80.0f;
    _bp.hp     = (float)player->stats.hp;
    _bp.max_hp = (float)player->stats.max_hp;
    _bp.weapon = weapon_profile(weapon);

    seed_enemy_rng((unsigned int)SDL_GetTicks());
    _enemy = enemy_create(enemy_id);
}

BattleScene::~BattleScene() {
    delete _enemy;
}

// ── update ────────────────────────────────────────────────────────────────────

void BattleScene::update(const Input* in, float dt) {
    if (input_pressed(in, SDL_SCANCODE_TAB) && _phase == BATTLE_PHASE_FIGHTING)
        _tab_open = !_tab_open;

    if (_phase != BATTLE_PHASE_FIGHTING || _tab_open) return;

    _update_movement(in, dt);
    _update_player_fire(in, dt);
    _update_enemy(dt);
    _move_bullets(dt);
    _check_collisions();

    if (_bp.iframes > 0.0f) _bp.iframes -= dt;

    if (!_enemy->is_alive()) {
        _player_ref->stats.hp = (int)_bp.hp;
        _phase = BATTLE_PHASE_VICTORY;
    } else if (_bp.hp <= 0.0f) {
        _player_ref->stats.hp = 0;
        _phase = BATTLE_PHASE_DEFEAT;
    }
}

void BattleScene::_update_movement(const Input* in, float dt) {
    const float PSPEED     = 160.0f;
    const float MARGIN     = 16.0f;
    const float ANIM_SPEED = input_down(in, SDL_SCANCODE_LSHIFT) ? 0.10f : 0.20f;

    float mx, my;
    player_read_input(_player_ref, in, &mx, &my);
    _bp.x += mx * PSPEED * dt;
    _bp.y += my * PSPEED * dt;

    if (_bp.x < MARGIN)           _bp.x = MARGIN;
    if (_bp.x > ARENA_W - MARGIN) _bp.x = ARENA_W - MARGIN;
    if (_bp.y < MARGIN)           _bp.y = MARGIN;
    if (_bp.y > ARENA_H - MARGIN) _bp.y = ARENA_H - MARGIN;

    player_animate(_player_ref, dt, ANIM_SPEED);
}

void BattleScene::_update_player_fire(const Input* in, float dt) {
    _bp.fire_timer -= dt;
    bool pressed = input_down(in, SDL_SCANCODE_SPACE) ||
                   input_down(in, SDL_SCANCODE_Z);

    if (pressed && _bp.fire_timer <= 0.0f) {
        float ddx = _enemy->x - _bp.x;
        float ddy = _enemy->y - _bp.y;
        _player_ref->facing = (ddx*ddx >= ddy*ddy)
            ? (ddx >= 0.0f ? 8 : 6)
            : (ddy >= 0.0f ? 0 : 3);
        _player_ref->facing_locked = 1;

        const ProjectileProfile& wp = _bp.weapon;
        float base = atan2f(_enemy->y - _bp.y, _enemy->x - _bp.x);
        float step  = (wp.count > 1) ? (wp.spread * PI / 180.0f) / (wp.count - 1) : 0.0f;
        float start = base - step * (wp.count - 1) * 0.5f;
        for (int i = 0; i < wp.count; i++)
            _spawn_player_bullet(start + i * step);
        _bp.fire_timer = 1.0f / wp.fire_rate;
    }
}

void BattleScene::_update_enemy(float dt) {
    _enemy->update(dt, _bp.x, _bp.y);
    _enemy->fire_timer -= dt;
    if (_enemy->fire_timer <= 0.0f) {
        BulletSpawn spawns[32];
        int count = _enemy->fire(_bp.x, _bp.y, spawns, 32);
        for (int i = 0; i < count; i++)
            _spawn_enemy_bullet(spawns[i]);
        _enemy->fire_timer = _enemy->fire_interval();
    }
}

void BattleScene::_move_bullets(float dt) {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;
        if (bl.x < 0 || bl.x > ARENA_W || bl.y < 0 || bl.y > ARENA_H)
            bl.active = false;
    }

    // Collect orb spawn positions so we don't modify the array while iterating.
    struct OrbSpawn { float x, y; };
    OrbSpawn orb_pending[32];
    int n_orb = 0;

    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;

        if (bl.spawner) {
            bl.spawn_timer -= dt;
            if (bl.spawn_timer <= 0.0f && n_orb < 32) {
                orb_pending[n_orb++] = { bl.x, bl.y };
                bl.spawn_timer = bl.spawn_interval;
            }
            if (bl.x < -20 || bl.x > ARENA_W + 20 ||
                bl.y < -20 || bl.y > ARENA_H + 20)
                bl.active = false;
        } else if (bl.bouncing) {
            float r = bl.radius;
            if (bl.x - r < 0)       { bl.x = r;           bl.vx =  fabsf(bl.vx); bl.bounces++; }
            if (bl.x + r > ARENA_W) { bl.x = ARENA_W - r; bl.vx = -fabsf(bl.vx); bl.bounces++; }
            if (bl.y - r < 0)       { bl.y = r;           bl.vy =  fabsf(bl.vy); bl.bounces++; }
            if (bl.y + r > ARENA_H) { bl.y = ARENA_H - r; bl.vy = -fabsf(bl.vy); bl.bounces++; }
            if (bl.bounces >= 3) bl.active = false;
        } else {
            if (bl.x < 0 || bl.x > ARENA_W || bl.y < 0 || bl.y > ARENA_H)
                bl.active = false;
        }
    }

    // Emit 8-way ring from each orb that ticked.
    for (int p = 0; p < n_orb; p++) {
        for (int i = 0; i < 8; i++) {
            float a = i * (TAU / 8.0f);
            BulletSpawn sub;
            sub.vx = cosf(a) * 130.0f;
            sub.vy = sinf(a) * 130.0f;
            sub.radius = 3.5f;
            sub.damage = 1.0f;
            _spawn_bullet_at(orb_pending[p].x, orb_pending[p].y, sub);
        }
    }
}

void BattleScene::_check_collisions() {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        if (circles_overlap(bl.x, bl.y, bl.radius,
                            _enemy->x, _enemy->y, (float)ENEMY_R)) {
            _enemy->take_damage(bl.damage * _enemy->damage_mult(_weapon_type));
            bl.active = false;
        }
    }
    if (_bp.iframes > 0.0f) return;
    float px = _bp.x, py = _bp.y;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (circles_overlap(bl.x, bl.y, bl.radius, px, py, (float)PLAYER_R)) {
            _bp.hp -= bl.damage;
            if (_bp.hp < 0.0f) _bp.hp = 0.0f;
            _bp.iframes = 1.5f;
            bl.active = false;
        }
    }
}

void BattleScene::_spawn_player_bullet(float angle) {
    const ProjectileProfile& wp = _bp.weapon;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (bl.active) continue;
        bl.x = _bp.x; bl.y = _bp.y;
        bl.vx = cosf(angle) * wp.speed;
        bl.vy = sinf(angle) * wp.speed;
        bl.radius = wp.radius;
        bl.damage = wp.damage;
        bl.active = true;
        return;
    }
}

void BattleScene::_spawn_bullet_at(float ox, float oy, const BulletSpawn& bs) {
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (bl.active) continue;
        bl.x = ox; bl.y = oy;
        bl.vx = bs.vx; bl.vy = bs.vy;
        bl.radius = bs.radius;
        bl.damage = bs.damage;
        bl.bouncing       = bs.bouncing;
        bl.bounces        = 0;
        bl.spawner        = bs.spawner;
        bl.spawn_interval = bs.spawn_interval;
        bl.spawn_timer    = bs.spawn_interval;
        bl.active         = true;
        return;
    }
}

void BattleScene::_spawn_enemy_bullet(const BulletSpawn& bs) {
    _spawn_bullet_at(_enemy->x, _enemy->y, bs);
}

// ── Drawing helpers ───────────────────────────────────────────────────────────

void BattleScene::_fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                               Uint8 r, Uint8 g, Uint8 b, Uint8 a) {
    SDL_SetRenderDrawColor(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(ren, &rect);
}

void BattleScene::_draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                                      Uint8 r, Uint8 g, Uint8 b) {
    SDL_SetRenderDrawColor(ren, r, g, b, 255);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderDrawRect(ren, &rect);
}

void BattleScene::_draw_bar(SDL_Renderer* ren, int x, int y, int w, int h,
                             float cur, float max, Uint8 fr, Uint8 fg, Uint8 fb) {
    _fill_rect(ren, x, y, w, h, 0, 0, 0, 255);
    if (max > 0.0f && cur > 0.0f) {
        int filled = (int)(w * cur / max);
        if (filled > w) filled = w;
        _fill_rect(ren, x, y, filled, h, fr, fg, fb, 255);
    }
    _draw_rect_outline(ren, x, y, w, h, 255, 255, 255);
}

// ── draw ──────────────────────────────────────────────────────────────────────

void BattleScene::draw(SDL_Renderer* ren, SDL_Texture* player_sprite) const {
    _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, 255);
    _draw_rect_outline(ren, 4, 4, ARENA_W - 8, ARENA_H - 8, 255, 255, 255);

    // Enemy
    {
        int ex = (int)_enemy->x, ey = (int)_enemy->y;
        int hw = ENEMY_R + 4;
        Uint8 pulse = (_phase == BATTLE_PHASE_FIGHTING) ? 200 : 80;
        _fill_rect(ren, ex - hw, ey - hw, hw*2, hw*2, 40, pulse, 40, 255);
        _draw_rect_outline(ren, ex - hw, ey - hw, hw*2, hw*2, 80, 255, 80);
        _draw_bar(ren, ex - 60, ey - hw - 14, 120, 8,
                  _enemy->hp, _enemy->max_hp, 220, 60, 60);
        const char* nm = _enemy->name();
        draw_text(ren, nm, ex - text_width(nm, 1)/2, ey - hw - 24, 1, 220, 220, 220);
    }

    // Player bullets — yellow
    SDL_SetRenderDrawColor(ren, 255, 230, 50, 255);
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        const Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        int r = (int)bl.radius;
        SDL_Rect rect = { (int)bl.x - r, (int)bl.y - r, r*2, r*2 };
        SDL_RenderFillRect(ren, &rect);
    }

    // Enemy bullets — orange-red (normal), blue (bouncing), bright orange (orb)
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (bl.spawner)
            SDL_SetRenderDrawColor(ren, 255, 140, 0, 255);
        else if (bl.bouncing)
            SDL_SetRenderDrawColor(ren, 60, 140, 255, 255);
        else
            SDL_SetRenderDrawColor(ren, 255, 80, 30, 255);
        int r = (int)bl.radius;
        SDL_Rect rect = { (int)bl.x - r, (int)bl.y - r, r*2, r*2 };
        SDL_RenderFillRect(ren, &rect);
    }

    // Player sprite (flickers during iframes)
    {
        bool visible = _bp.iframes <= 0.0f ||
                       ((int)(_bp.iframes * 10.0f) % 2 == 0);
        if (visible) {
            int px = (int)_bp.x, py = (int)_bp.y;
            if (player_sprite) {
                static const int down_cycle[4]  = {1, 0, 2, 0};
                static const int up_cycle[4]    = {4, 3, 5, 3};
                static const int left_cycle[2]  = {7, 6};
                static const int right_cycle[2] = {9, 8};

                int facing = _player_ref->facing;
                int step   = _player_ref->anim_step;
                int frame;
                if      (facing >= 8) frame = _player_ref->is_moving ? right_cycle[step % 2] : facing;
                else if (facing >= 6) frame = _player_ref->is_moving ? left_cycle[step % 2]  : facing;
                else if (facing >= 3) frame = _player_ref->is_moving ? up_cycle[step]         : facing;
                else                  frame = _player_ref->is_moving ? down_cycle[step]       : facing;

                SDL_Rect src = { frame * 16, 0, 16, 24 };
                SDL_Rect dst = { px - 16, py - 24, 32, 48 };
                SDL_RenderCopy(ren, player_sprite, &src, &dst);
            } else {
                _fill_rect(ren, px - 6, py - 6, 12, 12, 220, 220, 255, 255);
            }
            _draw_rect_outline(ren, px - PLAYER_R, py - PLAYER_R,
                               PLAYER_R*2, PLAYER_R*2, 0, 255, 255);
        }
        // Weapon cooldown bar — yellow, above HP bar
        {
            float max_cd = 1.0f / _bp.weapon.fire_rate;
            float ready  = 1.0f - (_bp.fire_timer > 0.0f ? _bp.fire_timer / max_cd : 0.0f);
            _draw_bar(ren, ARENA_W/2 - 80, ARENA_H - 26, 160, 5,
                      ready, 1.0f, 255, 220, 0);
        }
        _draw_bar(ren, ARENA_W/2 - 80, ARENA_H - 18, 160, 10,
                  _bp.hp, _bp.max_hp, 60, 200, 60);
    }

    // Victory / defeat overlay
    if (_phase == BATTLE_PHASE_VICTORY) {
        draw_nes_panel(ren, 160, 180, 320, 70);
        draw_text(ren, "VICTORY",
                  160 + (320 - text_width("VICTORY", 2)) / 2, 206, 2, 255, 255, 255);
    } else if (_phase == BATTLE_PHASE_DEFEAT) {
        draw_nes_panel(ren, 160, 180, 320, 70);
        draw_text(ren, "GAME OVER",
                  160 + (320 - text_width("GAME OVER", 2)) / 2, 206, 2, 255, 255, 255);
    }

    // Tab menu overlay
    if (_tab_open) {
        const int PW = 300, PH = 130;
        const int PX = (ARENA_W - PW) / 2, PY = (ARENA_H - PH) / 2;

        draw_nes_panel(ren, PX, PY, PW, PH);

        draw_text(ren, "EQUIPMENT",
                  PX + (PW - text_width("EQUIPMENT", 2)) / 2, PY + 8, 2, 255, 255, 255);

        SDL_SetRenderDrawColor(ren, 255, 255, 255, 255);
        SDL_Rect div = { PX + 8, PY + 30, PW - 16, 1 };
        SDL_RenderFillRect(ren, &div);

        char buf[48];
        int row_y = PY + 38;

        SDL_snprintf(buf, sizeof(buf), "WEAPON : %s", weapon_name(_weapon_type));
        draw_text(ren, buf, PX + 12, row_y, 1, 255, 230, 80);
        row_y += 18;

        SDL_snprintf(buf, sizeof(buf), "SPELL  : NONE");
        draw_text(ren, buf, PX + 12, row_y, 1, 100, 180, 255);
        row_y += 18;

        SDL_snprintf(buf, sizeof(buf), "HEALING: NONE");
        draw_text(ren, buf, PX + 12, row_y, 1, 80, 220, 120);
        row_y += 18;

        const char* hint = "[TAB] CLOSE";
        draw_text(ren, hint, PX + (PW - text_width(hint, 1)) / 2,
                  PY + PH - 16, 1, 160, 160, 160);
    }
}
