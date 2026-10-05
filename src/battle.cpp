#include "fc_palette.h"
#include "battle.h"
#include "core.h"
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
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

const char* weapon_name(WeaponType type) {
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

// ── Enemy sprites ─────────────────────────────────────────────────────────────

// Sheets built by tools/build_enemy.py: one row, 8 directions
// (D DR R UR U UL L DL) x `frames` idle frames each. Three frames play in
// `loop` order; more (big creatures, smoother motion) play straight through
// as a cycle, STEP_MS each -- the same timings as the preview GIFs. Enemies past the end of the table have no
// sprite yet and draw as a box.
struct EnemySheet { const char* path; Uint8 loop[4]; int frames = 3; bool rows = false; };   // rows: one row per direction
static const EnemySheet ENEMY_SHEETS[] = {
    { "assets/enemies/00_skvader.png",                {0, 1, 0, 2} },
    { "assets/enemies/01_wolpertinger.png",           {0, 1, 0, 2} },
    { "assets/enemies/02_treesqueak.png",             {0, 1, 0, 2} },
    { "assets/enemies/03_qique.png",                  {0, 1, 0, 2} },
    { "assets/enemies/04_lili.png",                   {0, 1, 2, 1} },  // legs splay out
    { "assets/enemies/05_crowing_crested_cobra.png",  {0, 1, 0, 2} },
    { "assets/enemies/06_wakmangganchi_aragondi.png", {0, 1, 0, 2} },
    { "assets/enemies/07_alber.png",                  {0, 1, 0, 2} },
    { "assets/enemies/08_snawfus.png",                {0, 1, 0, 2} },
    { "assets/enemies/09_questing_beast.png",         {0, 1, 0, 2} },
    { "assets/enemies/10_grand_goule.png",            {0, 1, 0, 2} },
    { "assets/enemies/11_paoxiao.png",                {0, 1, 0, 2} },
    { "assets/enemies/12_ebigane.png",                {0, 1, 0, 2} },
    { "assets/enemies/13_beast_of_the_charred_forests.png", {0, 1, 0, 2} },
    { "assets/enemies/14_lodsilungur.png",            {0, 1, 0, 2} },
    { "assets/enemies/15_ofuguggi.png",               {0, 1, 0, 2} },
    { "assets/enemies/16_kamaitachi.png",             {0, 1, 0, 2} },
    { "assets/enemies/17_qiqirn.png",                 {0, 1, 0, 2} },
    { "assets/enemies/18_vatnaormur.png",             {}, 5 },
    { "assets/enemies/19_skeljaskrimsli.png",         {}, 5 },
    { "assets/enemies/20_sermilik.png",               {}, 5 },
    { "assets/enemies/21_asp.png",                    {0, 1, 0, 2} },
    { "assets/enemies/22_cactus_cat.png",             {0, 1, 0, 2} },
    { "assets/enemies/23_olgoi_khorkhoi.png",         {}, 8 },
    { "assets/enemies/24_zoureg.png",                 {0, 1, 0, 2} },
    { "assets/enemies/25_myrmecoleon.png",            {}, 5 },
    { "assets/enemies/26_akhekh.png",                 {0, 1, 0, 2} },
    { "assets/enemies/27_grootslang.png",             {}, 5 },
    { "assets/enemies/28_opimachus.png",              {0, 1, 0, 2} },
    { "assets/enemies/29_karnabo.png",                {0, 1, 0, 2} },
    { "assets/enemies/30_dajna.png",                  {}, 8, true },   // fills the top of the arena: one row per direction
    { "assets/enemies/31_man_eating_boulder.png",     {0, 1, 0, 2} },
    { "assets/enemies/32_angont.png",                 {}, 5 },
    { "assets/enemies/33_tsenagahi.png",              {0, 1, 0, 2} },
    { "assets/enemies/34_anaye.png",                  {}, 8, true },   // giant: one row per direction
    { "assets/enemies/35_lomie.png",                  {0, 1, 0, 2} },
    { "assets/enemies/36_cu_sith.png",                {0, 1, 0, 2} },
    { "assets/enemies/37_celestial_stag.png",         {0, 1, 0, 2} },
    { "assets/enemies/38_igtuk.png",                  {0, 1, 0, 2} },
    { "assets/enemies/39_ajaju.png",                  {0, 1, 0, 2} },
    { "assets/enemies/40_slide_rock_bolter.png",      {}, 5 },
    { "assets/enemies/41_sasnalkahi.png",             {}, 5 },
    { "assets/enemies/42_nykur.png",                  {0, 1, 0, 2} },
    { "assets/enemies/43_sazae_oni.png",              {0, 1, 0, 2} },
    { "assets/enemies/44_itqiirpak.png",              {}, 8, true },   // giant: one row per direction
    { "assets/enemies/45_kusa_kap.png",               {0, 1, 0, 2} },
    { "assets/enemies/46_lusca.png",                  {0, 1, 0, 2} },
    { "assets/enemies/47_moha_moha.png",              {}, 5 },
    { "assets/enemies/48_bjarndyrakongur.png",        {0, 1, 0, 2} },
    { "assets/enemies/49_physeter.png",               {}, 8, true },   // fills the top of the arena: one row per direction
};
static const int ENEMY_SHEET_COUNT = sizeof(ENEMY_SHEETS) / sizeof(ENEMY_SHEETS[0]);
static const Uint32 LOOP_MS[4] = { 400, 250, 400, 250 };
static const Uint32 STEP_MS = 260;

// Sheet row for a FACE_* direction.
static int sheet_dir(int facing) {
    switch (facing) {
        case FACE_DOWN:       return 0;
        case FACE_DOWN_RIGHT: return 1;
        case FACE_RIGHT:      return 2;
        case FACE_UP_RIGHT:   return 3;
        case FACE_UP:         return 4;
        case FACE_UP_LEFT:    return 5;
        case FACE_LEFT:       return 6;
        default:              return 7;   // FACE_DOWN_LEFT
    }
}

// ── BattleScene ───────────────────────────────────────────────────────────────

// The fade up from black at the start and down to black at the end, in seconds.
static const float FADE_T  = 0.4f;
// A pack's next fight: the player's glide back and the enemy's drop, in seconds.
static const float CHAIN_T = 0.6f;

BattleScene::BattleScene(Player* player, int enemy_id, bool chained, float from_x, float from_y) {
    _chained = chained;
    _from_x  = from_x;
    _from_y  = from_y;
    memset(_player_bullets, 0, sizeof(_player_bullets));
    memset(_enemy_bullets,  0, sizeof(_enemy_bullets));
    memset(_pickups,        0, sizeof(_pickups));

    _phase       = BATTLE_PHASE_INTRO;
    _player_ref  = player;
    _weapon_type = player->equipped_weapon;
    _tab_open    = false;

    _bp = {};
    _bp.x      = ARENA_W * 0.5f;
    _bp.y      = ARENA_H - 80.0f;
    _bp.hp     = (float)player->stats.hp;
    _bp.max_hp = (float)player->stats.max_hp;
    _bp.weapon = weapon_profile(_weapon_type);

    seed_enemy_rng((unsigned int)SDL_GetTicks());
    _enemy    = enemy_create(enemy_id);
    _enemy_id = enemy_id;
}

BattleScene::~BattleScene() {
    delete _enemy;
    if (_sheet) SDL_DestroyTexture(_sheet);
}

// ── update ────────────────────────────────────────────────────────────────────

// Eased progress of a chained intro: quick off the mark, soft landing.
float BattleScene::_chain_in() const {
    if (!_chained || _phase != BATTLE_PHASE_INTRO) return 1.0f;
    float k = _t / CHAIN_T;
    if (k >= 1.0f) return 1.0f;
    float u = 1.0f - k;
    return 1.0f - u * u * u;
}

// How dark the screen is, 0..1: up from black in the intro, down to black
// once the end panel is dismissed.
float BattleScene::_darkness() const {
    if (_phase == BATTLE_PHASE_INTRO) return _chained ? 0.0f : 1.0f - _t / FADE_T;
    if (_outro_t > 0.0f)              return _outro_t / FADE_T;
    return 0.0f;
}

void BattleScene::update(const Input* in, float dt) {
    _t += dt;
    bool confirm = input_pressed(in, SDL_SCANCODE_RETURN) || input_pressed(in, SDL_SCANCODE_Z);

    switch (_phase) {
        case BATTLE_PHASE_INTRO:
            if (_t >= (_chained ? CHAIN_T : FADE_T)) {
                _phase = BATTLE_PHASE_FIGHTING;
                _t = 0.0f;
                // A beat to move before the first volley: control returns
                // before danger does.
                _enemy->fire_timer = 0.5f;
            }
            return;
        case BATTLE_PHASE_VICTORY:
            _update_pickups(dt);
            // The wait keeps a held fire key (Z) from skipping the panel.
            if (confirm && _t > 0.6f) _confirmed = true;
            if (_confirmed && (_more_after || (_outro_t += dt) >= FADE_T)) _done = true;
            return;
        case BATTLE_PHASE_DEFEAT:
            if (confirm && _t > 0.6f) _confirmed = true;
            if (_confirmed && (_outro_t += dt) >= FADE_T) _done = true;
            return;
        default:
            break;
    }

    if (input_pressed(in, SDL_SCANCODE_TAB))
        _tab_open = !_tab_open;
    if (_tab_open) return;

    // Debug: instantly win the current battle.
    if (input_pressed(in, SDL_SCANCODE_T))
        _enemy->take_damage(_enemy->hp);

    _update_movement(in, dt);
    _update_player_fire(in, dt);
    _update_enemy(dt);
    _move_bullets(dt);
    _check_collisions();

    if (_bp.iframes > 0.0f) _bp.iframes -= dt;

    if (!_enemy->is_alive()) {
        _win();
    } else if (_bp.hp <= 0.0f) {
        _player_ref->stats.hp = 0;
        _phase = BATTLE_PHASE_DEFEAT;
        _t = 0.0f;
    }
}

// Bullet cancel: every enemy bullet still in the air becomes a pickup that
// flies to the player, and a denser screen pays more of the enemy's part.
void BattleScene::_win() {
    _player_ref->stats.hp = (int)_bp.hp;
    _phase = BATTLE_PHASE_VICTORY;
    _t = 0.0f;

    int cancelled = 0;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.active = false;
        // Pop back the way it came, then get pulled in.
        _pickups[cancelled++] = { bl.x, bl.y, -bl.vx * 0.4f, -bl.vy * 0.4f, true };
    }
    _drop_part  = enemy_part(_enemy_id);
    _drop_count = 1 + cancelled / 10;
    // ponytail: credited now, not as pickups land -- the scene can be dismissed
    // before they arrive, so the flight is only for show.
    _player_ref->parts[_drop_part] += _drop_count;
}

void BattleScene::_update_pickups(float dt) {
    const float PULL = 2200.0f, DRAG = 4.0f;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Pickup& p = _pickups[i];
        if (!p.active) continue;
        float dx = _bp.x - p.x, dy = _bp.y - p.y;
        float d = sqrtf(dx*dx + dy*dy);
        if (d < 10.0f) { p.active = false; continue; }
        // Drag bleeds off the pop and any sideways drift, so nothing orbits.
        float keep = 1.0f - DRAG * dt;
        if (keep < 0.0f) keep = 0.0f;
        p.vx = p.vx * keep + dx / d * PULL * dt;
        p.vy = p.vy * keep + dy / d * PULL * dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
    }
}

void BattleScene::_update_movement(const Input* in, float dt) {
    // The map's keys: crouch (ctrl) is focus -- slow, precise, the hitbox
    // shown -- and shift sprints.
    bool focus  = player_crouching(in);
    bool sprint = player_sprinting(in);
    _focus = focus;
    const float PSPEED     = focus ? 70.0f : sprint ? 250.0f : 160.0f;
    const float MARGIN     = 16.0f;
    const float ANIM_SPEED = focus ? 0.30f : sprint ? 0.10f : 0.20f;

    float mx, my;
    player_read_input(_player_ref, in, &mx, &my);
    _bp.x += mx * PSPEED * dt;
    _bp.y += my * PSPEED * dt;

    if (_bp.x < MARGIN)           _bp.x = MARGIN;
    if (_bp.x > ARENA_W - MARGIN) _bp.x = ARENA_W - MARGIN;
    if (_bp.y < ARENA_TOP + MARGIN) _bp.y = ARENA_TOP + MARGIN;
    if (_bp.y > ARENA_H - MARGIN) _bp.y = ARENA_H - MARGIN;

    player_animate(_player_ref, dt, ANIM_SPEED);
}

void BattleScene::_update_player_fire(const Input* in, float dt) {
    _bp.fire_timer -= dt;
    bool pressed = input_down(in, SDL_SCANCODE_SPACE) ||
                   input_down(in, SDL_SCANCODE_Z);

    if (pressed && _bp.fire_timer <= 0.0f) {
        _player_ref->facing = facing_toward(_enemy->x - _bp.x, _enemy->y - _bp.y);
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
        if (bl.x < 0 || bl.x > ARENA_W || bl.y < ARENA_TOP || bl.y > ARENA_H)
            bl.active = false;
    }

    // Collect orb spawn positions so we don't modify the array while iterating.
    struct OrbSpawn { float x, y; };
    OrbSpawn orb_pending[32];
    int n_orb = 0;

    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;

        if (bl.homing && bl.homing_timer > 0.0f) {
            bl.homing_timer -= dt;
            if (bl.homing_timer <= 0.0f) bl.homing = false;
        }

        if (bl.homing) {
            // Turn rate: fast for bullets, slow for orbs so the ring still matters
            const float TURN = bl.spawner ? 0.9f : 2.2f;
            float dx = _bp.x - bl.x, dy = _bp.y - bl.y;
            float dist = sqrtf(dx*dx + dy*dy);
            if (dist > 1.0f) {
                float spd = sqrtf(bl.vx*bl.vx + bl.vy*bl.vy);
                if (spd > 0.0f) {
                    float nx = bl.vx/spd + dx/dist * TURN * dt;
                    float ny = bl.vy/spd + dy/dist * TURN * dt;
                    float len = sqrtf(nx*nx + ny*ny);
                    bl.vx = nx/len * spd;
                    bl.vy = ny/len * spd;
                }
            }
        }

        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;

        if (bl.spawner) {
            bl.spawn_timer -= dt;
            if (bl.spawn_timer <= 0.0f && n_orb < 32) {
                orb_pending[n_orb++] = { bl.x, bl.y };
                bl.spawn_timer = bl.spawn_interval;
            }
            if (bl.x < -20 || bl.x > ARENA_W + 20 ||
                bl.y < ARENA_TOP - 20 || bl.y > ARENA_H + 20)
                bl.active = false;
        } else if (bl.bouncing) {
            float r = bl.radius;
            if (bl.x - r < 0)       { bl.x = r;           bl.vx =  fabsf(bl.vx); bl.bounces++; }
            if (bl.x + r > ARENA_W) { bl.x = ARENA_W - r; bl.vx = -fabsf(bl.vx); bl.bounces++; }
            if (bl.y - r < ARENA_TOP) { bl.y = ARENA_TOP + r; bl.vy = fabsf(bl.vy); bl.bounces++; }
            if (bl.y + r > ARENA_H) { bl.y = ARENA_H - r; bl.vy = -fabsf(bl.vy); bl.bounces++; }
            if (bl.bounces >= 3) bl.active = false;
        } else {
            if (bl.x < 0 || bl.x > ARENA_W || bl.y < ARENA_TOP || bl.y > ARENA_H)
                bl.active = false;
        }
    }

    // Emit 8-way ring from each orb that ticked.
    // Minimum distance: at d < 50px the ring gaps (39px) are too small for the
    // player circle (r=12) to fit through, making the hit unavoidable.
    for (int p = 0; p < n_orb; p++) {
        float dx = orb_pending[p].x - _bp.x;
        float dy = orb_pending[p].y - _bp.y;
        if (dx*dx + dy*dy < 50.0f*50.0f) continue;
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
                            _enemy->x, _enemy->y, _hit_r)) {
            _enemy->take_damage(bl.damage * _enemy->damage_mult(_weapon_type));
            bl.active = false;
        }
    }
    if (_bp.iframes > 0.0f) return;
    float px = _bp.x, py = _bp.y;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (circles_overlap(bl.x, bl.y, bl.radius, px, py, PLAYER_R)) {
            // Whole bars, at least one: every hit is a visible chunk.
            _bp.hp -= ceilf(bl.damage / HP_PER_BAR) * HP_PER_BAR;
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
        bl.homing         = bs.homing;
        bl.homing_timer   = bs.homing_timer;
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
    fc_draw_color(ren, r, g, b, a);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderFillRect(ren, &rect);
}

void BattleScene::_draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                                      Uint8 r, Uint8 g, Uint8 b) {
    fc_draw_color(ren, r, g, b, 255);
    SDL_Rect rect = {x, y, w, h};
    SDL_RenderDrawRect(ren, &rect);
}

float BattleScene::hud_stamina() const {
    float max_cd = 1.0f / _bp.weapon.fire_rate;
    return 1.0f - (_bp.fire_timer > 0.0f ? _bp.fire_timer / max_cd : 0.0f);
}

// ── draw ──────────────────────────────────────────────────────────────────────

// The enemy faces the player and plays its idle loop, drawn at the player's 2x
// and centred on its hitbox; enemies without a sheet yet draw as a box. On a
// win it blinks out.
void BattleScene::_draw_enemy(SDL_Renderer* ren) const {
    if (_phase == BATTLE_PHASE_VICTORY && (_t > 0.4f || (int)(_t * 20.0f) % 2)) return;
    float k = _chain_in();
    int ex = (int)_enemy->x;
    int ey = (int)(-60.0f + (_enemy->y + 60.0f) * k);
    if (!_sheet_tried) {
        _sheet_tried = true;
        if (_enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT) {
            _sheet = IMG_LoadTexture(ren, ENEMY_SHEETS[_enemy_id].path);
            if (!_sheet) SDL_Log("enemy sheet %s: %s", ENEMY_SHEETS[_enemy_id].path, IMG_GetError());
        }
        if (_sheet) {
            // Hitbox scales with the creature: 40% of the drawn frame's
            // smaller side, so a hare is a small target and a boar a big one.
            int sw, sh;
            SDL_QueryTexture(_sheet, NULL, NULL, &sw, &sh);
            const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
            int fw = es.rows ? sw / es.frames : sw / (8 * es.frames), fh = es.rows ? sh / 8 : sh;
            _hit_r = 0.4f * 2.0f * (fw < fh ? fw : fh);
        }
    }

    if (_sheet) {
        int sw, sh;
        SDL_QueryTexture(_sheet, NULL, NULL, &sw, &sh);
        const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
        int fw = es.rows ? sw / es.frames : sw / (8 * es.frames), fh = es.rows ? sh / 8 : sh;
        int frame;
        if (es.frames == 3) {
            Uint32 t = SDL_GetTicks() % (LOOP_MS[0] + LOOP_MS[1] + LOOP_MS[2] + LOOP_MS[3]);
            int step = 0;
            while (t >= LOOP_MS[step]) t -= LOOP_MS[step++];
            frame = es.loop[step];
        } else {
            frame = (SDL_GetTicks() / STEP_MS) % es.frames;
        }
        int dir = sheet_dir(facing_toward(_bp.x - _enemy->x, _bp.y - _enemy->y));
        SDL_Rect src = es.rows ? SDL_Rect{ frame * fw, dir * fh, fw, fh }
                               : SDL_Rect{ (dir * es.frames + frame) * fw, 0, fw, fh };
        SDL_Rect dst = { ex - fw, ey - fh, fw * 2, fh * 2 };
        if (k >= 1.0f) {
            SDL_RenderCopy(ren, _sheet, &src, &dst);
        } else {
            // Phasing in, the map's stripe wipe in reverse: bands two art
            // pixels tall fill in from alternate sides, in hard eighths.
            float fill = (float)(int)((_t / CHAIN_T) * 8.0f) / 8.0f + 0.125f;
            int sw = (int)(fw * (fill > 1.0f ? 1.0f : fill));
            for (int row = 0, band = 0; row < fh; row += 2, band++) {
                int rh = fh - row < 2 ? fh - row : 2;
                int sx = band % 2 ? fw - sw : 0;
                SDL_Rect bs = { src.x + sx, src.y + row, sw, rh };
                SDL_Rect bd = { dst.x + sx * 2, dst.y + row * 2, sw * 2, rh * 2 };
                SDL_RenderCopy(ren, _sheet, &bs, &bd);
            }
        }
    } else {
        int hw = ENEMY_R + 4;
        Uint8 pulse = (_phase == BATTLE_PHASE_FIGHTING) ? 200 : 80;
        _fill_rect(ren, ex - hw, ey - hw, hw*2, hw*2, 40, pulse, 40, 255);
        _draw_rect_outline(ren, ex - hw, ey - hw, hw*2, hw*2, 80, 255, 80);
    }
}

void BattleScene::draw(SDL_Renderer* ren, SDL_Texture* player_sprite) const {
    _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, 255);


    _draw_enemy(ren);

    // Player bullets: two-tone like the enemy's, bright yellow (#f0e880) with
    // a white core -- a colour no enemy bullet uses, so they read as "mine".
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        const Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        int r = (int)bl.radius;
        _fill_rect(ren, (int)bl.x - r, (int)bl.y - r, r*2, r*2, 240, 232, 128, 255);
        _fill_rect(ren, (int)bl.x - 1, (int)bl.y - 1, 2, 2, 252, 252, 252, 255);
    }

    // Enemy bullets, in the colour of the enemy firing them (exact palette
    // colours, bright enough to pop off the black). The kind shows by shape,
    // NES style: plain is solid with a white core, homing flickers white,
    // bouncing is a hollow ring until its last bounce, a spawner orb has a
    // yellow core.
    SDL_Color c = enemy_bullet_color(_enemy_id);
    bool flash = (SDL_GetTicks() / 100) % 2 == 0;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        int r = (int)bl.radius, bx = (int)bl.x - r, by = (int)bl.y - r;
        bool white = bl.homing && flash;
        _fill_rect(ren, bx, by, r*2, r*2, white ? 252 : c.r, white ? 252 : c.g, white ? 252 : c.b, 255);
        if (bl.bouncing && bl.bounces < 2 && r > 2)
            _fill_rect(ren, bx + 2, by + 2, r*2 - 4, r*2 - 4, 0, 0, 0, 255);   // hollow
        else if (bl.spawner)
            _fill_rect(ren, (int)bl.x - 2, (int)bl.y - 2, 4, 4, 240, 188, 60, 255);
        else
            _fill_rect(ren, (int)bl.x - 1, (int)bl.y - 1, 2, 2, 252, 252, 252, 255);
    }

    // Player sprite (flickers during iframes)
    {
        bool visible = _bp.iframes <= 0.0f ||
                       ((int)(_bp.iframes * 10.0f) % 2 == 0);
        if (visible) {
            float k = _chain_in();
            float px = _from_x + (_bp.x - _from_x) * k;
            float py = _from_y + (_bp.y - _from_y) * k;
            if (player_sprite) {
                // The map's sheet at the map's 2x. The art is 11x15 at the
                // bottom middle of a 14x20 frame, so the body's centre -- where
                // the hitbox is -- sits 15 across and 25 down the 28x40 frame.
                int frame = player_frame(_player_ref);

                SDL_Rect src = { frame * 14, 0, 14, 20 };
                // 29 down rather than the body's centre at 25: the hitbox sits
                // two art pixels lower on the body, at the chest.
                SDL_Rect dst = { (int)px - 15, (int)py - 29, 28, 40 };
                SDL_RenderCopy(ren, player_sprite, &src, &dst);
            } else {
                _fill_rect(ren, (int)px - 6, (int)py - 6, 12, 12, 220, 220, 255, 255);
            }
        }
    }

    // Cancelled bullets flying in, in the colour of the part they pay.
    static const Uint8 PART_RGB[PART_COUNT][3] = {
        { 200, 150,  90 },   // hide
        { 235, 230, 210 },   // bone
        {  90, 220, 255 },   // essence
    };
    const Uint8* pc = PART_RGB[_drop_part];
    fc_draw_color(ren, pc[0], pc[1], pc[2], 255);
    bool flying = false;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Pickup& p = _pickups[i];
        if (!p.active) continue;
        flying = true;
        SDL_Rect rect = { (int)p.x - 2, (int)p.y - 2, 4, 4 };
        SDL_RenderFillRect(ren, &rect);
    }

    // Crouch marker: a 3x3 art-pixel diamond on the hitbox, its core the
    // exact hit area. Drawn over everything, and core and arms swap colour
    // every few frames -- NES flicker -- so no bullet colour can hide it.
    if (_focus && _phase == BATTLE_PHASE_FIGHTING) {
        // Outlined in black and coloured white and the palette's bright blue
        // (#5c94fc) -- colours the player sprite doesn't use -- so it stands
        // off the skin and red shirt.
        int cx = (int)_bp.x, cy = (int)_bp.y;
        const int BX[5] = { -3, 1, -1, -1, -1 }, BY[5] = { -1, -1, -3, 1, -1 };  // arms, then core
        for (int i = 0; i < 5; i++)
            _fill_rect(ren, cx + BX[i] - 2, cy + BY[i] - 2, 6, 6, 0, 0, 0, 255);
        bool swap = (SDL_GetTicks() / 67) % 2;
        for (int i = 0; i < 5; i++) {
            bool white = (i == 4) != swap;   // core white, arms blue; swapped every few frames
            _fill_rect(ren, cx + BX[i], cy + BY[i], 2, 2,
                       white ? 252 : 92, white ? 252 : 148, 252, 255);
        }
    }

    // Victory / defeat overlay
    // The win panel waits for the pickups to land and goes as the fade out starts.
    if (_phase == BATTLE_PHASE_VICTORY && !_confirmed && (!flying || _t > 1.2f)) {
        draw_nes_panel(ren, 160, 180, 320, 70);
        draw_text(ren, "VICTORY",
                  160 + (320 - text_width("VICTORY", 2)) / 2, 196, 2, 255, 255, 255);
        char buf[32];
        SDL_snprintf(buf, sizeof(buf), "+%d %s", _drop_count, part_name(_drop_part));
        draw_text(ren, buf, 160 + (320 - text_width(buf, 1)) / 2, 222, 1, pc[0], pc[1], pc[2]);
    } else if (_phase == BATTLE_PHASE_DEFEAT && !_confirmed) {
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

        fc_draw_color(ren, 255, 255, 255, 255);
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

    // Fading in or out: black over everything in the NES's four hard steps.
    float dark = _darkness();
    if (dark > 0.0f) {
        dark = dark >= 1.0f ? 1.0f : (float)(int)(dark * 4.0f + 0.999f) / 4.0f;
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, (Uint8)(255 * dark));
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    }
}
