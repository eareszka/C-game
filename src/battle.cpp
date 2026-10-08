#include "fc_palette.h"
#include "battle.h"
#include "core.h"
#include "dungeon.h"   // material_color
#include "crafting.h"  // Item, item_slot, part_item
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <math.h>
#include <string.h>

static const float PI  = 3.14159265f;
static const float TAU = 6.28318530f;

static const float ENEMY_FLASH_T   = 0.07f;  // seconds the enemy flashes white after a hit
// At most one flash this often: a full-oil weapon lands a hit every few
// frames, and flashing on each would hold the enemy solid white.
static const float ENEMY_FLASH_GAP = 0.2f;
// A piercing shot still inside the enemy strikes again after this long.
static const float PIERCE_REHIT_T  = 0.07f;
// Every shot flies at one speed: the one that crosses the gap the fight opens
// at (player 400, enemy ~160) in BULLET_TRAVEL_T. Fixed, so a shot's pace
// never depends on where it was fired from.
static const float BULLET_TRAVEL_T = 0.48f;

// See battle.h. A halberd at 0.6 a second goes 0.6, 0.83, 1.1 ... 11, 15;
// a dagger at 2.2 a second, 2.4 ... 15 -- each its own same step.
float faster_fire_rate(float base_rate, int level) {
    return base_rate * powf(TOUHOU_FIRE_RATE / base_rate, (float)level / WEAPON_OIL_MAX);
}

// rate x damage = base rate x base damage x FASTER_DPS_AT_MAX ^ (level/max),
// so the damage takes whatever the rate does not.
float faster_damage(float base_rate, float base_damage, int level) {
    return base_damage * powf(FASTER_DPS_AT_MAX * base_rate / TOUHOU_FIRE_RATE,
                              (float)level / WEAPON_OIL_MAX);
}
static const float BULLET_SPEED    = 240.0f / BULLET_TRAVEL_T;
static const float SHOT_FADE       = 0.4f;   // fade-out stretch, as a share of the sprite's reach   // seconds from firing to reaching the enemy



// ── Weapon profiles ───────────────────────────────────────────────────────────

ProjectileProfile weapon_profile(WeaponType type) {
    // {damage, fire_rate, count, spread_deg, radius, pierces}
    // One shot a volley for every weapon; more come from upgrades (not built
    // yet), which fan them across the weapon's spread.
    switch (type) {
        case WEAPON_KNIFE:   return {  8.0f, 1.8f, 1,  0.0f, 3.0f };
        case WEAPON_CLUB:    return { 14.0f, 0.8f, 1,  0.0f, 7.0f };
        case WEAPON_DAGGER:  return {  6.0f, 2.2f, 1,  0.0f, 3.0f };
        case WEAPON_AXE:     return { 18.0f, 0.7f, 1, 60.0f, 5.0f };
        case WEAPON_HALBERD: return { 16.0f, 0.6f, 1,  0.0f, 4.0f, true };
        case WEAPON_KATANA:  return { 13.0f, 1.4f, 1, 15.0f, 4.0f };
        case WEAPON_SCYTHE:  return { 24.0f, 0.9f, 1, 30.0f, 4.0f, true };   // the strongest, by a clear step
        default:             return {  6.0f, 2.2f, 1,  0.0f, 3.0f };
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

// A sheet as plain RGBA32 bytes, for the copies below that edit its pixels;
// null if it will not load.
static SDL_Surface* load_rgba(const char* path) {
    SDL_Surface* raw = IMG_Load(path);
    if (!raw) return nullptr;
    SDL_Surface* s = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
    SDL_FreeSurface(raw);
    return s;
}

// Load a sheet, and the same sheet as a solid white silhouette in *white:
// every opaque pixel turned the palette's white, alpha kept. SDL can only
// darken a texture with a colour mod, so the flash needs its own copy.
static SDL_Texture* load_with_white(SDL_Renderer* ren, const char* path, SDL_Texture** white) {
    *white = nullptr;
    SDL_Surface* s = load_rgba(path);
    if (!s) return nullptr;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, s);
    for (int y = 0; y < s->h; y++) {
        Uint8* p = (Uint8*)s->pixels + y * s->pitch;
        for (int x = 0; x < s->w; x++, p += 4)
            p[0] = p[1] = p[2] = 252;
    }
    *white = SDL_CreateTextureFromSurface(ren, s);
    SDL_FreeSurface(s);
    return tex;
}

// Load a sheet, and in fade[i] the same sheet keeping only the pixels whose
// fc_bayer() rank is below 12, 8 and 4: a fade as an ordered dither, the way
// the game does every fade, so no pixel is ever a blend off the palette.
static SDL_Texture* load_with_fades(SDL_Renderer* ren, const char* path, SDL_Texture* fade[3]) {
    SDL_Surface* s = load_rgba(path);
    if (!s) return nullptr;
    SDL_Texture* tex = SDL_CreateTextureFromSurface(ren, s);
    for (int i = 0; i < 3; i++) {
        int keep = 12 - 4 * i;
        for (int y = 0; y < s->h; y++) {
            Uint8* p = (Uint8*)s->pixels + y * s->pitch;
            for (int x = 0; x < s->w; x++, p += 4)
                if (fc_bayer(x, y) >= keep) p[3] = 0;
        }
        fade[i] = SDL_CreateTextureFromSurface(ren, s);   // each step thins the last
    }
    SDL_FreeSurface(s);
    return tex;
}

static bool circles_overlap(float ax, float ay, float ar,
                             float bx, float by, float br) {
    float dx = ax - bx, dy = ay - by, rsum = ar + br;
    return dx*dx + dy*dy < rsum*rsum;
}

// The point of a shot's middle nearest (x, y): its centre, or for a log the
// nearest point of the line it lies along.
static void bullet_nearest(const Bullet& bl, float x, float y, float* nx, float* ny) {
    *nx = bl.x; *ny = bl.y;
    if (bl.half_len <= 0.0f) return;
    float ux = cosf(bl.ang), uy = sinf(bl.ang);
    float t = fminf(fmaxf((x - bl.x) * ux + (y - bl.y) * uy, -bl.half_len), bl.half_len);
    *nx = bl.x + ux * t; *ny = bl.y + uy * t;
}

// An enemy shot touching a circle: round shots as circles, logs as capsules.
static bool bullet_touches(const Bullet& bl, float x, float y, float r) {
    float nx, ny;
    bullet_nearest(bl, x, y, &nx, &ny);
    return circles_overlap(nx, ny, bl.radius, x, y, r);
}

// ── Enemy sprites ─────────────────────────────────────────────────────────────

// Sheets built by tools/build_enemy.py: one row, 8 directions
// (D DR R UR U UL L DL) x `frames` idle frames each. Three frames play in
// `loop` order; more (big creatures, smoother motion) play straight through
// as a cycle, STEP_MS each -- the same timings as the preview GIFs. Enemies past the end of the table have no
// sprite yet and draw as a box.
// flap: an optional sheet played while the enemy moves (Enemy::flap_phase) --
// Qique's wingbeat, the cobra's slither -- laid out like a one-row sheet with
// FLAP_FRAMES frames a direction.
struct EnemySheet { const char* path; Uint8 loop[4]; int frames = 3; bool rows = false;   // rows: one row per direction
                    const char* flap = nullptr;
                    const char* alt  = nullptr;      // alt: the idle in another pose (Enemy::alt_pose), same layout
                    const char* log  = nullptr;      // log: its log bullet, drawn lying flat (BulletSpawn::half_len) --
                    int log_frames   = 1;            // a row of this many frames, rolling, LOG_MS each
                    int log_rows     = 1; };         // 3: rows flat / right end up / right end down, stepped 0 1 0 2 to rock
static const int FLAP_FRAMES = 4;   // wings up, mid, down, mid
static const EnemySheet ENEMY_SHEETS[] = {
    { "assets/enemies/00_skvader.png",                {0, 1, 0, 2} },
    { "assets/enemies/01_wolpertinger.png",           {0, 1, 0, 2} },
    { "assets/enemies/02_treesqueak.png",             {0, 1, 0, 2} },
    { "assets/enemies/03_qique.png",                  {0, 1, 0, 2}, 3, false, "assets/enemies/03_qique_flap.png" },
    { "assets/enemies/04_lili.png",                   {0, 1, 2, 1} },  // legs splay out
    { "assets/enemies/05_crowing_crested_cobra.png",  {0, 1, 0, 2}, 3, false, "assets/enemies/05_crowing_crested_cobra_slither.png" },
    { "assets/enemies/06_wakmangganchi_aragondi.png", {0, 1, 0, 2} },
    { "assets/enemies/07_alber.png",                  {0, 1, 0, 2} },
    { "assets/enemies/08_snawfus.png",                {0, 1, 0, 2} },
    { "assets/enemies/09_questing_beast.png",         {0, 1, 0, 2}, 3, false, "assets/enemies/09_questing_beast_walk.png" },
    { "assets/enemies/10_grand_goule.png",            {0, 1, 0, 2} },
    { "assets/enemies/11_paoxiao.png",                {0, 1, 0, 2}, 3, false,
      "assets/enemies/11_paoxiao_leap.png", "assets/enemies/11_paoxiao_closed.png" },
    { "assets/enemies/12_ebigane.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/12_ebigane_fly.png" },
    { "assets/enemies/13_beast_of_the_charred_forests.png", {0, 1, 0, 2} },
    { "assets/enemies/14_lodsilungur.png",            {0, 1, 0, 2} },
    { "assets/enemies/15_ofuguggi.png",               {0, 1, 0, 2}, 3, false, "assets/enemies/15_ofuguggi_swim.png" },  // swim = backwards, tail first
    { "assets/enemies/16_kamaitachi.png",             {0, 1, 0, 2} },
    { "assets/enemies/17_qiqirn.png",                 {0, 1, 0, 2}, 3, false, "assets/enemies/17_qiqirn_run.png" },  // run = its frightened gallop round the edge
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
    { "assets/enemies/50_teakettler.png",             {0, 1, 0, 2}, 3, false, "assets/enemies/50_teakettler_walk.png" },  // frame 1: the whistle; walk = backwards
    { nullptr },                                                       // 51 Aspidochelone: not drawn yet, a box
    { nullptr },                                                       // 52 Sannaja: not drawn yet, a box
    { "assets/enemies/53_come_at_a_body.png",         {0, 1, 0, 2}, 3, false, "assets/enemies/53_come_at_a_body_dash.png" },  // frame 1: it spits; dash = rush and flight
    { "assets/enemies/54_billdad.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/54_billdad_slap.png" },  // frame 1: the spring; slap (phase 2) = tail hammer, already turned to show its back
    { "assets/enemies/55_wapaloosie.png",             {0, 1, 0, 2}, 3, false, nullptr,
      "assets/enemies/55_wapaloosie_up.png", "assets/enemies/55_wapaloosie_log.png", 8, 3 },                         // frame 1: the inchworm hump; alt: reared up on its back legs
    { "assets/enemies/56_moskitto.png",               {}, 5, false, "assets/enemies/56_moskitto_grab.png" },  // big: always aloft; grab = lunging to snatch
    { "assets/enemies/57_dingbat.png",                {}, 5, false, nullptr, "assets/enemies/57_dingbat_catch.png" },  // big, 6 dirs; alt = catching pose, while perched
    { "assets/enemies/58_agropelter.png",             {}, 5 },         // big: squatting, its long skinny arms flailing
    { nullptr }, { nullptr },                                          // 59-60: not drawn yet, boxes
    { nullptr }, { nullptr }, { nullptr }, { nullptr },                // 61-64: not drawn yet
    { nullptr },                                                       // 65 Mice That Eat Iron: skipped for now
    { "assets/enemies/66_ayotochtli.png",             {0, 1, 0, 2}, 3, false, "assets/enemies/66_ayotochtli_roll.png" },  // frame 1: hunched into its shell; flap = curled in a ball, rolling
    { "assets/enemies/67_lagopus.png",                {0, 1, 0, 2}, 3, false, "assets/enemies/67_lagopus_fly.png" },  // 6 dirs; idle: wings spread, rippling; flap = flying, all 8 dirs
    { "assets/enemies/68_shuyu.png",                  {0, 1, 0, 2}, 3, false, "assets/enemies/68_shuyu_flap.png" },  // frames 1, 2: heads plucking the air; flap (phase 2) = wings beating
    { "assets/enemies/69_bes_chem.png",               {0, 1, 0, 2} },  // frame 1: the fanged mouth gapes wide
};
static const int ENEMY_SHEET_COUNT = sizeof(ENEMY_SHEETS) / sizeof(ENEMY_SHEETS[0]);

// A log whose sheet has tilt rows rocks by stepping them -- flat, right end
// up, flat, right end down -- ROCK_STEP s each, from its own age; its hitbox
// tilts with the row (LOG_TILT: the drawn rows lean ~10 degrees).
static const float ROCK_STEP = 0.25f;
static const float LOG_TILT  = 0.18f;   // radians
static int log_row(const Bullet& bl, const EnemySheet& es) {
    static const int STEPS[4] = { 0, 1, 0, 2 };
    return es.log_rows > 1 ? STEPS[(int)(bl.age / ROCK_STEP) % 4] : 0;
}
static const Uint32 LOOP_MS[4] = { 400, 250, 400, 250 };
static const Uint32 STEP_MS = 260;

// The idle frame an enemy sheet shows right now: three frames in `loop`
// order at LOOP_MS, more straight through at STEP_MS. Drawing and the breath
// hook (Enemy::breathe) both read it, so a volley leaves on the frame shown.
static int idle_frame_now(const EnemySheet& es) {
    if (es.frames != 3) return (SDL_GetTicks() / STEP_MS) % es.frames;
    Uint32 t = SDL_GetTicks() % (LOOP_MS[0] + LOOP_MS[1] + LOOP_MS[2] + LOOP_MS[3]);
    int step = 0;
    while (t >= LOOP_MS[step]) t -= LOOP_MS[step++];
    return es.loop[step];
}

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
    _weapon_type = equipped_weapon(player).type;
    _tab_open    = false;

    _bp = {};
    _bp.x      = ARENA_W * 0.5f;
    _bp.y      = ARENA_H - 80.0f;
    _bp.hp     = (float)player->stats.hp;
    _bp.max_hp = (float)player->stats.max_hp;
    _equip(_weapon_type);

    seed_enemy_rng((unsigned int)SDL_GetTicks());
    _enemy    = enemy_create(enemy_id);
    _enemy_id = enemy_id;
}

// Firing as weapon w: its shape's profile, sped up by its oil, hitting as
// hard as its ore, with a shot a volley more per echo -- and the shot hitbox,
// the opaque bounds of its cell in the shot sheet. At the start of a fight
// and on every swap.
void BattleScene::_equip(WeaponType w) {
    _weapon_type = w;
    _bp.weapon = weapon_profile(_weapon_type);
    // What the weapon is made of and what has been bought for it: ore sets
    // the damage, oil the cooldown, echo the shots a volley.
    const Weapon& held = _player_ref->arsenal[w];
    float base_rate = _bp.weapon.fire_rate;
    _bp.weapon.fire_rate  = faster_fire_rate(base_rate, held.oil);
    _bp.weapon.damage     = faster_damage(base_rate, _bp.weapon.damage, held.oil)
                          * material_power(held.material)
                          * level_damage_mult(_player_ref->level);
    _bp.weapon.count     += held.echo;

    // The hitbox is the sprite: the opaque bounds of this weapon's cell, about
    // its centre, at the 2x it is drawn. Every ore row is the same shape.
    float r = _bp.weapon.radius;
    _shot_x0 = _shot_y0 = -r;
    _shot_x1 = _shot_y1 =  r;
    {
        const int CELL = PLAYER_SHOT_CELL;
        SDL_Surface* s = load_rgba(PLAYER_SHOT_SHEET);
        if (s) {
            int cx = (int)_weapon_type * CELL, x0 = CELL, y0 = CELL, x1 = -1, y1 = -1;
            for (int y = 0; y < CELL && y < s->h; y++)
                for (int x = 0; x < CELL && cx + x < s->w; x++)
                    if (((Uint8*)s->pixels)[y * s->pitch + (cx + x) * 4 + 3]) {
                        if (x < x0) x0 = x;
                        if (x > x1) x1 = x;
                        if (y < y0) y0 = y;
                        if (y > y1) y1 = y;
                    }
            if (x1 >= 0) {
                const int c = CELL / 2;
                _shot_x0 = (x0 - c) * 2.0f;  _shot_x1 = (x1 + 1 - c) * 2.0f;
                _shot_y0 = (y0 - c) * 2.0f;  _shot_y1 = (y1 + 1 - c) * 2.0f;
            }
            SDL_FreeSurface(s);
        }
    }
    float ex = fmaxf(-_shot_x0, _shot_x1), ey = fmaxf(-_shot_y0, _shot_y1);
    _shot_reach = sqrtf(ex * ex + ey * ey);
}

// Swap to the next or previous weapon the player owns, in arsenal order,
// wrapping. The choice is the player's equipped weapon from then on, so it
// carries out of the fight. The new weapon's cooldown starts at a quarter
// second at least: a swap is never a free extra volley.
void BattleScene::_cycle(int dir) {
    WeaponType w = owned_neighbour(_player_ref, dir);
    _swap_t = 0.0f;                                  // the box shows even with only one weapon
    if (w == _player_ref->equipped) return;
    _player_ref->equipped = w;
    _equip(w);
    _bp.fire_timer = fmaxf(_bp.fire_timer, 0.25f);
    _swap_t = 0.0f;
}

BattleScene::~BattleScene() {
    delete _enemy;
    if (_sheet) SDL_DestroyTexture(_sheet);
    if (_flap)  SDL_DestroyTexture(_flap);
    if (_alt)   SDL_DestroyTexture(_alt);
    if (_log)   SDL_DestroyTexture(_log);
    if (_alt_white) SDL_DestroyTexture(_alt_white);
    if (_sheet_white) SDL_DestroyTexture(_sheet_white);
    if (_flap_white)  SDL_DestroyTexture(_flap_white);
    if (_bullets) SDL_DestroyTexture(_bullets);
    if (_item_icons) SDL_DestroyTexture(_item_icons);
    for (SDL_Texture* t : _bullets_fade) if (t) SDL_DestroyTexture(t);
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

// Being hit: the whole fight freezes for HITSTOP, the screen flashes white
// then red, and shakes for SHAKE_T -- a hit costs whole bars now, so it has to
// land like one.
static const float HITSTOP = 0.12f;
static const float SHAKE_T = 0.30f;
static const float FLASH_T = 0.40f;

void hurt_shake_begin(SDL_Renderer* ren, float t, SDL_Rect* saved) {
    SDL_RenderGetViewport(ren, saved);
    if (t < SHAKE_T) {
        int amp = 2 * (int)(3.0f * (1.0f - t / SHAKE_T) + 0.5f);   // 6, 4, 2 px
        SDL_Rect shaken = *saved;
        shaken.x += ((int)(t * 30.0f) % 2) ? amp : -amp;
        SDL_RenderSetViewport(ren, &shaken);
    }
}

void hurt_shake_end(SDL_Renderer* ren, const SDL_Rect* saved) {
    SDL_RenderSetViewport(ren, saved);
}

// White over the first HITSTOP, then red fading out in hard steps, NES
// palette-flash style.
void hurt_flash(SDL_Renderer* ren, float t, int w, int h) {
    if (t >= FLASH_T) return;
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
    SDL_Rect all = { 0, 0, w, h };
    if (t < HITSTOP) fc_draw_color(ren, 252, 252, 252, 150);
    else {
        float k = 1.0f - (t - HITSTOP) / (FLASH_T - HITSTOP);
        fc_draw_color(ren, 183, 0, 0, (Uint8)(110 * ((int)(k * 3.0f + 0.999f) / 3.0f)));
    }
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}

void BattleScene::update(const Input* in, float dt) {
    if (_hit_t < HITSTOP) { _hit_t += dt; return; }
    _hit_t += dt;
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
                _fire_iv = _enemy->fire_interval();
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

    // Swap weapons on the fly: Q back, E or X on.
    if (input_pressed(in, SDL_SCANCODE_Q)) _cycle(-1);
    if (input_pressed(in, SDL_SCANCODE_E) || input_pressed(in, SDL_SCANCODE_X)) _cycle(1);
    _swap_t += dt;

    // Debug: instantly win the current battle.
    if (input_pressed(in, SDL_SCANCODE_T))
        _enemy->take_damage(_enemy->hp);

    _update_movement(in, dt);
    _update_player_fire(in, dt);
    _update_enemy(dt);
    _move_bullets(dt);
    _check_collisions();

    if (_bp.iframes > 0.0f) _bp.iframes -= dt;
    if (_enemy_flash > 0.0f) _enemy_flash -= dt;
    if (_flash_gap   > 0.0f) _flash_gap   -= dt;
    if (_pierce_wait > 0.0f) _pierce_wait -= dt;

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
// What a cancelled bullet turns into: mostly the common stuff of the world,
// and one in PART_SHARE the part this enemy drops -- the vine off a
// Treesqueak, the hide off a hare. The enemy itself always gives one part,
// so even a clean win with nothing in the air pays it.
static const Item COMMON_DROPS[] = { ITEM_WOOD, ITEM_STONE };
static const int  PART_SHARE     = 4;
static_assert(ITEM_COUNT <= 32, "BattleScene::_won holds a count per Item");

// Anything not from the common pool is rare: the part an enemy is hunted for.
static bool is_common_drop(int it) {
    for (Item c : COMMON_DROPS) if (c == it) return true;
    return false;
}

void BattleScene::_win() {
    _player_ref->stats.hp = (int)_bp.hp;
    _phase = BATTLE_PHASE_VICTORY;
    _t = 0.0f;
    for (int& n : _won) n = 0;

    Item part = part_item(enemy_part(_enemy_id));
    unsigned rng = SDL_GetTicks() * 2654435761u + (unsigned)_enemy_id;
    int n = 0;
    // The enemy's own part, from where it stood.
    _pickups[n++] = { _enemy->x, _enemy->y, 0.0f, -120.0f, true, part };
    for (int i = 0; i < MAX_ENEMY_BULLETS && n < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.active = false;
        rng = rng * 1664525u + 1013904223u;
        int roll = (int)((rng >> 16) % (PART_SHARE * 64));
        Item it = roll < 64 ? part : COMMON_DROPS[roll % (int)(sizeof(COMMON_DROPS) / sizeof(COMMON_DROPS[0]))];
        // Pop back the way it came, then get pulled in.
        _pickups[n++] = { bl.x, bl.y, -bl.vx * 0.4f, -bl.vy * 0.4f, true, it };
    }
    // ponytail: credited now, not as pickups land -- the scene can be dismissed
    // before they arrive, so the flight is only for show.
    _won_new = 0;
    for (int i = 0; i < n; i++)
        if (!item_found(_player_ref, (Item)_pickups[i].item)) _won_new |= 1u << _pickups[i].item;
    for (int i = 0; i < n; i++) item_mark_found(_player_ref, (Item)_pickups[i].item);
    for (int i = 0; i < n; i++) {
        item_slot(_player_ref, (Item)_pickups[i].item) += 1;
        _won[_pickups[i].item]++;
    }
    // The score: hits + grazes + the defeat bonus (enemy_defeat_exp: a
    // common's grows with its rank, a boss pays far more). A level-up heals:
    // the battle's own HP follows.
    _exp_gain = _hits + _grazes + enemy_defeat_exp(_enemy_id);
    _levels   = player_gain_exp(_player_ref, _exp_gain);
    if (_levels > 0) {
        _bp.max_hp = (float)_player_ref->stats.max_hp;
        _bp.hp     = (float)_player_ref->stats.hp;
    }
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
    // The map's keys: crouch (ctrl) is focus -- slow and precise -- and
    // shift sprints.
    bool focus  = player_crouching(in);
    bool sprint = player_sprinting(in);
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
    BulletSpawn spawns[128];   // the most one volley may fire (Ebigane's pentagram is 75)
    // When its rate speeds up mid-fight -- a phase change, say -- the wait shrinks to
    // the new rate at once instead of running out the old, slower one. Only
    // on a speed-up, so the opening grace stays whole.
    float iv = _enemy->fire_interval();
    if (iv < _fire_iv) _enemy->fire_timer = fminf(_enemy->fire_timer, iv);
    _fire_iv = iv;
    _enemy->fire_timer -= dt;
    if (_enemy->fire_timer <= 0.0f) {
        int count = _enemy->fire(_bp.x, _bp.y, spawns, 128);
        for (int i = 0; i < count; i++)
            _spawn_enemy_bullet(spawns[i]);
        _enemy->fire_timer = _enemy->fire_interval();
    }
    // The breath frame: the moment the idle animation turns to it.
    if (_enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT) {
        int f = idle_frame_now(ENEMY_SHEETS[_enemy_id]), bf = _enemy->breath_frame();
        if (f == bf && _idle_frame != bf) {
            int count = _enemy->breathe(_bp.x, _bp.y, spawns, 128);
            for (int i = 0; i < count; i++)
                _spawn_enemy_bullet(spawns[i]);
        }
        if (f != _idle_frame) {
            int count = _enemy->on_idle_frame(f, _bp.x, _bp.y, spawns, 128);
            for (int i = 0; i < count; i++)
                _spawn_enemy_bullet(spawns[i]);
        }
        _idle_frame = f;
    }
}

void BattleScene::_move_bullets(float dt) {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        bl.age += dt;
        bl.x += bl.vx * dt;
        bl.y += bl.vy * dt;
        // Gone when its centre reaches the edge: by then it has dithered
        // away (see _shot_edge_gap), so nothing is cut off.
        if (_shot_edge_gap(bl) <= 0.0f) bl.active = false;
    }

    // Collect orb spawn positions so we don't modify the array while iterating.
    struct OrbSpawn { float x, y; };
    OrbSpawn orb_pending[32];
    int n_orb = 0;
    struct Shed { float x, y, heading, spread, speed, damage; int n; float spin; };
    Shed shed_pending[32];
    int n_shed = 0;

    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        bl.age += dt;   // from its spawn, waiting or not

        // A boomerang slows along its heading, stops, and flies back; once
        // it is returning and reaches the enemy, the enemy swallows it.
        if (bl.accel != 0.0f && bl.min_speed > 0.0f && bl.ow != 0.0f) {
            bl.ovr = fmaxf(bl.ovr + bl.accel * dt, bl.min_speed);   // orbiting: it's the speed outward that eases
        } else if (bl.accel != 0.0f && bl.min_speed > 0.0f) {
            // Easing off: slows along the way it is going now (a ricochet
            // turns it), never below min_speed.
            float cur = sqrtf(bl.vx * bl.vx + bl.vy * bl.vy);
            float sp  = fmaxf(cur + bl.accel * dt, bl.min_speed);
            if (cur > 0.0f) { bl.vx = bl.vx / cur * sp; bl.vy = bl.vy / cur * sp; }
        } else if (bl.accel != 0.0f) {
            bl.vx += bl.ux * bl.accel * dt;
            bl.vy += bl.uy * bl.accel * dt;
            if (bl.max_speed > 0.0f) {                  // coming back no faster than this
                float sp = sqrtf(bl.vx * bl.vx + bl.vy * bl.vy);
                if (sp > bl.max_speed) { bl.vx *= bl.max_speed / sp; bl.vy *= bl.max_speed / sp; }
            }
            float ddx = bl.x - _enemy->x, ddy = bl.y - _enemy->y;
            if (bl.vx * bl.ux + bl.vy * bl.uy < 0.0f && ddx * ddx + ddy * ddy < 24.0f * 24.0f) {
                bl.active = false;
                continue;
            }
        }

        // A mine waits where it was dropped, then launches at the player.
        if (bl.delay > 0.0f) {
            bl.delay -= dt;
            if (bl.delay > 0.0f) continue;
            float la = atan2f(_bp.y - bl.y, _bp.x - bl.x) + bl.launch_off;
            bl.vx = cosf(la) * bl.launch_speed;
            bl.vy = sinf(la) * bl.launch_speed;
        }

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

        if (bl.ow != 0.0f) {
            // Orbiting: straight out from its centre while turning round it.
            bl.orad += bl.ovr * dt;
            bl.oang += bl.ow * dt;
            float nx = bl.ocx + cosf(bl.oang) * bl.orad, ny = bl.ocy + sinf(bl.oang) * bl.orad;
            if (dt > 0.0f) { bl.vx = (nx - bl.x) / dt; bl.vy = (ny - bl.y) / dt; }
            bl.x = nx; bl.y = ny;
        } else {
            if (bl.zig_every > 0.0f && (bl.zig_t -= dt) <= 0.0f) {
                // Swing across its course to the other side.
                bl.zig_t += bl.zig_every;
                float r = -2.0f * bl.zig * bl.zig_s, c = cosf(r), sn = sinf(r), vx = bl.vx, vy = bl.vy;
                bl.vx = vx * c - vy * sn; bl.vy = vx * sn + vy * c;
                bl.zig_s = -bl.zig_s;
            }
            bl.x += bl.vx * dt;
            bl.y += bl.vy * dt;
        }
        if (bl.shed_every > 0.0f && bl.shed_left != 0 && (bl.shed_t -= dt) <= 0.0f) {
            bl.shed_t += bl.shed_every;
            if (bl.shed_left > 0) bl.shed_left--;
            bool still = bl.vx == 0.0f && bl.vy == 0.0f;     // a sitting egg sheds from its middle
            if (n_shed < 32)
                shed_pending[n_shed++] = { bl.x, still ? bl.y : bl.y + bl.radius, atan2f(bl.vy, bl.vx),
                                           bl.shed_spread, bl.shed_speed, bl.damage, bl.shed_n, bl.shed_spin };
            if (bl.shed_left == 0 && bl.shed_dies) { bl.active = false; continue; }
        }
        bl.ang += bl.spin * dt;   // a log turns -- or rocks, turning back at its tilt
        if (bl.half_len > 0.0f && _enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT
            && ENEMY_SHEETS[_enemy_id].log_rows > 1) {
            int row = log_row(bl, ENEMY_SHEETS[_enemy_id]);   // the hitbox leans with the drawn row
            bl.ang = row == 1 ? -LOG_TILT : row == 2 ? LOG_TILT : 0.0f;
        }
        if (bl.max_tilt > 0.0f && fabsf(bl.ang) > bl.max_tilt) {
            bl.ang  = copysignf(bl.max_tilt, bl.ang);
            bl.spin = -bl.spin;
        }

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
            // Gone once its centre leaves the arena -- for a log, once all of
            // it has (m: its reach), so one can enter from out of sight
            // above (spawned up to m over the top) and leave the same way.
            float m = bl.half_len > 0.0f ? bl.half_len + bl.radius : 0.0f;
            if (bl.x < -m || bl.x > ARENA_W + m || bl.y < ARENA_TOP - 2.0f * m || bl.y > ARENA_H + m)
                bl.active = false;
        }
    }

    // Emit 8-way ring from each orb that ticked.
    // Minimum distance: at d < 50px the ring gaps (39px) are too small for the
    // player circle (r=12) to fit through, making the hit unavoidable.
    for (int p = 0; p < n_shed; p++) {
        const Shed& s = shed_pending[p];
        float dx = s.x - _bp.x, dy = s.y - _bp.y;
        if (dx*dx + dy*dy < 40.0f*40.0f) continue;   // never point-blank
        for (int k = 0; k < s.n; k++) {
            float a = s.heading + (s.n > 1 ? (k / (float)(s.n - 1) - 0.5f) * s.spread : 0.0f);
            BulletSpawn chip = { cosf(a) * s.speed, sinf(a) * s.speed, 2.5f, s.damage };
            chip.orbit_w = s.spin;
            _spawn_bullet_at(s.x, s.y, chip);
        }
    }
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

// The axe and club tumble; everything else points the way it flies.
double BattleScene::_shot_angle(const Bullet& bl) const {
    if (bl.weapon == WEAPON_AXE || bl.weapon == WEAPON_CLUB)
        return SDL_GetTicks() * 1.03;   // ~1000 deg/sec, as the overworld throw
    return atan2f(bl.vy, bl.vx) * (180.0 / PI);
}

// How far the shot's centre is from the edge it is flying toward -- the
// nearer of the two it heads for -- so a shot leaving past the HUD fades out
// below it, where it can be seen, and a shot just fired near the bottom edge
// it is flying away from does not fade at all.
float BattleScene::_shot_edge_gap(const Bullet& bl) const {
    float gx = bl.vx > 0.0f ? ARENA_W - bl.x : bl.vx < 0.0f ? bl.x : 1e9f;
    float gy = bl.vy > 0.0f ? ARENA_H - bl.y : bl.vy < 0.0f ? bl.y - ARENA_TOP : 1e9f;
    return fminf(gx, gy);
}

// The scythe's slash leaves at the katana's size -- half its own -- and opens
// to full width over BULLET_TRAVEL_T -- at the enemy, from the opening gap. Everything else is drawn
// at the sprite's size throughout.
float BattleScene::_shot_scale(const Bullet& bl) const {
    if (bl.weapon != WEAPON_SCYTHE) return 1.0f;
    float k = bl.age / BULLET_TRAVEL_T;
    return 0.5f + 0.5f * (k < 1.0f ? k : 1.0f);
}

void BattleScene::_check_collisions() {
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        // A piercing shot inside the enemy strikes again only every
        // PIERCE_REHIT_T, however long it takes to pass through.
        if (bl.pierces && _pierce_wait > 0.0f) continue;
        if (float cr = _enemy->catch_radius()) {      // caught out of the air: no hit
            float cdx = bl.x - _enemy->x, cdy = bl.y - _enemy->y;
            if (cdx * cdx + cdy * cdy < cr * cr) { bl.active = false; _enemy->catch_shot(bl.x, bl.y); continue; }
        }
        // The enemy's centre in the shot's own frame, then its distance to
        // the nearest point of the shot's box -- grown with it -- against the
        // enemy's radius.
        // ponytail: one box for all shots, the weapon in hand's -- a shot
        // still in flight from before a swap borrows the new one's until it
        // leaves; per-shot boxes if that is ever noticed.
        float a = (float)(_shot_angle(bl) * (PI / 180.0));
        float k = _shot_scale(bl);
        float dx = _enemy->x - bl.x, dy = _enemy->y - bl.y;
        float lx =  dx * cosf(a) + dy * sinf(a);
        float ly = -dx * sinf(a) + dy * cosf(a);
        float x0 = _shot_x0 * k, x1 = _shot_x1 * k, y0 = _shot_y0 * k, y1 = _shot_y1 * k;
        float qx = lx < x0 ? x0 : lx > x1 ? x1 : lx;
        float qy = ly < y0 ? y0 : ly > y1 ? y1 : ly;
        if ((lx - qx) * (lx - qx) + (ly - qy) * (ly - qy) < _hit_r * _hit_r) {
            _enemy->take_damage(bl.damage * _enemy->damage_mult((WeaponType)bl.weapon) * _enemy->armor());
            _hits++;
            _pierce_wait = PIERCE_REHIT_T;
            if (_flash_gap <= 0.0f) { _enemy_flash = ENEMY_FLASH_T; _flash_gap = ENEMY_FLASH_GAP; }
            if (!bl.pierces) bl.active = false;
        }
    }
    float px = _bp.x, py = _bp.y;
    // Graze: an enemy shot passing within GRAZE_MARGIN of the hitbox without
    // touching it -- the reward for dodging close. Once per bullet, so a
    // slow one sitting beside the player can't be farmed.
    const float GRAZE_MARGIN = 10.0f;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active || bl.grazed) continue;
        if (bullet_touches(bl, px, py, PLAYER_R + GRAZE_MARGIN) &&
            !bullet_touches(bl, px, py, PLAYER_R)) {
            bl.grazed = true;
            _grazes++;
        }
    }
    if (_bp.iframes > 0.0f) return;
    // Whole bars, at least one: every hit is a visible chunk.
    auto hurt = [&](float damage) {
        _hit_bars = (int)ceilf(damage / HP_PER_BAR);
        _hit_t    = 0.0f;
        _bp.hp -= _hit_bars * HP_PER_BAR;
        if (_bp.hp < 0.0f) _bp.hp = 0.0f;
        _bp.iframes = 1.5f;
    };
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (bullet_touches(bl, px, py, PLAYER_R)) {
            hurt(bl.damage);
            bl.active = false;
        }
    }
    // Its body, for an enemy that hurts to touch: the same circle shots hit.
    float touch = _enemy->contact_damage();
    if (touch > 0.0f && _bp.iframes <= 0.0f && circles_overlap(_enemy->x, _enemy->y, _hit_r, px, py, PLAYER_R))
        hurt(touch);
}

void BattleScene::_spawn_player_bullet(float angle) {
    const ProjectileProfile& wp = _bp.weapon;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        Bullet& bl = _player_bullets[i];
        if (bl.active) continue;
        bl.x = _bp.x; bl.y = _bp.y;
        bl.vx = cosf(angle) * BULLET_SPEED;
        bl.vy = sinf(angle) * BULLET_SPEED;
        bl.radius = wp.radius;
        bl.damage = wp.damage;
        bl.age = 0.0f;
        bl.weapon   = (int)_weapon_type;
        bl.material = (int)_player_ref->arsenal[_weapon_type].material;
        bl.pierces  = wp.pierces;
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
        bl.delay          = bs.delay;
        bl.launch_speed   = bs.launch_speed;
        bl.launch_off     = bs.launch_off;
        bl.accel          = bs.accel;
        bl.min_speed      = bs.min_speed;
        bl.max_speed      = bs.max_speed;
        bl.age            = 0.0f;
        bl.half_len       = bs.half_len;
        bl.ang            = bs.ang;
        bl.spin           = bs.spin;
        bl.max_tilt       = bs.max_tilt;
        bl.shed_every     = bs.shed_every;
        bl.shed_t         = bs.shed_first;
        bl.shed_n         = bs.shed_n;
        bl.shed_spread    = bs.shed_spread;
        bl.shed_speed     = bs.shed_speed;
        bl.shed_left      = bs.shed_times > 0 ? bs.shed_times : -1;
        bl.shed_dies      = bs.shed_dies;
        bl.shed_spin      = bs.shed_spin;
        bl.ow             = bs.orbit_w;
        bl.zig = bs.zig; bl.zig_every = bs.zig_every; bl.zig_t = bs.zig_every * 0.5f; bl.zig_s = 1;
        if (bs.zig != 0.0f) {                         // it starts on one side of its course
            float c = cosf(bs.zig), sn = sinf(bs.zig), vx = bl.vx, vy = bl.vy;
            bl.vx = vx * c - vy * sn; bl.vy = vx * sn + vy * c;
        }
        bl.ocx = ox; bl.ocy = oy; bl.orad = 0.0f;
        bl.oang = atan2f(bs.vy, bs.vx);
        bl.ovr  = sqrtf(bs.vx * bs.vx + bs.vy * bs.vy);
        bl.flash_in       = bs.flash_in;
        bl.grazed         = false;
        {
            float sp = sqrtf(bs.vx * bs.vx + bs.vy * bs.vy);
            bl.ux = sp > 0.0f ? bs.vx / sp : 0.0f;
            bl.uy = sp > 0.0f ? bs.vy / sp : 0.0f;
        }
        if (bs.delay > 0.0f) bl.vx = bl.vy = 0.0f;   // a mine sits until it launches
        bl.active         = true;
        return;
    }
}

// No enemy shot is ever made on top of the player: one whose start is within
// SAFE_SPAWN (plus its own size) of the hitbox is left out. One rule for every
// enemy -- hugging a body, standing under a rain, a muzzle off to one side --
// instead of a guard in each pattern (the pattern tester's finding).
static const float SAFE_SPAWN = 24.0f;

void BattleScene::_spawn_enemy_bullet(const BulletSpawn& bs) {
    float ox = bs.from ? bs.ox : _enemy->x, oy = bs.from ? bs.oy : _enemy->y;
    float reach = SAFE_SPAWN + bs.radius + bs.half_len;
    float dx = ox - _bp.x, dy = oy - _bp.y;
    if (dx * dx + dy * dy < reach * reach) return;
    _spawn_bullet_at(ox, oy, bs);
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
        if (_enemy_id >= 0 && _enemy_id < ENEMY_SHEET_COUNT && ENEMY_SHEETS[_enemy_id].path) {
            _sheet = load_with_white(ren, ENEMY_SHEETS[_enemy_id].path, &_sheet_white);
            if (!_sheet) SDL_Log("enemy sheet %s: %s", ENEMY_SHEETS[_enemy_id].path, IMG_GetError());
            if (const char* fp = ENEMY_SHEETS[_enemy_id].flap) {
                _flap = load_with_white(ren, fp, &_flap_white);
                if (!_flap) SDL_Log("enemy flap sheet %s: %s", fp, IMG_GetError());
            }
            if (const char* ap = ENEMY_SHEETS[_enemy_id].alt) {
                _alt = load_with_white(ren, ap, &_alt_white);
                if (!_alt) SDL_Log("enemy alt sheet %s: %s", ap, IMG_GetError());
            }
            if (const char* lp = ENEMY_SHEETS[_enemy_id].log) {
                _log = IMG_LoadTexture(ren, lp);
                if (!_log) SDL_Log("enemy log sprite %s: %s", lp, IMG_GetError());
            }
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
        int frame = idle_frame_now(es);
        int mf  = _enemy->move_facing();   // running somewhere: face that way, not the player
        int dir = sheet_dir(mf >= 0 ? mf : facing_toward(_bp.x - _enemy->x, _bp.y - _enemy->y));
        SDL_Rect src = es.rows ? SDL_Rect{ frame * fw, dir * fh, fw, fh }
                               : SDL_Rect{ (dir * es.frames + frame) * fw, 0, fw, fh };
        // Moving, the flap sheet: a wingbeat across a flight, a slither wave.
        SDL_Texture* tex = _sheet;
        float flap = _enemy->flap_phase();
        if (flap >= 0.0f && _flap) {
            int f = (int)(flap * FLAP_FRAMES) % FLAP_FRAMES;
            src = SDL_Rect{ (dir * FLAP_FRAMES + f) * fw, 0, fw, fh };
            tex = _flap;
        } else if (_alt && _enemy->alt_pose()) {
            tex = _alt;   // same frame, the other pose
        }
        // Hit: the frame in solid white for a few frames.
        if (_enemy_flash > 0.0f) {
            SDL_Texture* w = tex == _flap ? _flap_white : tex == _alt ? _alt_white : _sheet_white;
            if (w) tex = w;
        }
        SDL_Rect dst = { ex - fw, ey - fh, fw * 2, fh * 2 };
        if (k >= 1.0f) {
            SDL_RenderCopy(ren, tex, &src, &dst);
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
                SDL_RenderCopy(ren, tex, &bs, &bd);
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

    // Hit shake: the arena jumps side to side on the 2px art grid, dying
    // away over SHAKE_T. The HUD, drawn after, stays still.
    SDL_Rect vp;
    hurt_shake_begin(ren, _hit_t, &vp);


    _draw_enemy(ren);

    // Player bullets: the weapon's own shape in its ore's metal -- row is the
    // material, column the weapon, each cell drawn pointing right and turned
    // to the way it flies (the axe and club spin instead). Same 2x art pixels as the
    // enemy, and the hitbox is the same box (see the constructor). Without the
    // sheet, a square in the ore's lit tone with a white core.
    if (!_bullets_tried) {
        _bullets_tried = true;
        _bullets = load_with_fades(ren, PLAYER_SHOT_SHEET, _bullets_fade);
        if (!_bullets) SDL_Log("player bullets: %s", IMG_GetError());
    }
    const int BCELL = PLAYER_SHOT_CELL;
    for (int i = 0; i < MAX_PLAYER_BULLETS; i++) {
        const Bullet& bl = _player_bullets[i];
        if (!bl.active) continue;
        // Each shot in its own weapon and ore: one fired before a swap keeps them.
        SDL_Rect bsrc = { bl.weapon * BCELL, bl.material * BCELL, BCELL, BCELL };
        SDL_Color ore = material_color((Material)bl.material, ORE_LIT);
        if (_bullets) {
            double deg = _shot_angle(bl);
            int half = (int)(BCELL * _shot_scale(bl));
            SDL_Rect dst = { (int)bl.x - half, (int)bl.y - half, half * 2, half * 2 };
            // Leaving: over the last stretch before the edge -- a share of
            // the sprite's reach -- it dithers out in three steps, so it is
            // gone by the time its centre arrives and _move_bullets retires it.
            float m = SHOT_FADE * _shot_reach * _shot_scale(bl);
            float gap = _shot_edge_gap(bl);
            SDL_Texture* tex = _bullets;
            if (gap < m) {
                int step = (int)((1.0f - gap / m) * 3.0f);
                tex = _bullets_fade[step < 2 ? step : 2];
            }
            if (tex) SDL_RenderCopyEx(ren, tex, &bsrc, &dst, deg, NULL, SDL_FLIP_NONE);
            continue;
        }
        int r = (int)bl.radius;
        _fill_rect(ren, (int)bl.x - r, (int)bl.y - r, r*2, r*2, ore.r, ore.g, ore.b, 255);
        _fill_rect(ren, (int)bl.x - 1, (int)bl.y - 1, 2, 2, 252, 252, 252, 255);
    }

    // Enemy bullets, in the colour of the enemy firing them (exact palette
    // colours, bright enough to pop off the black). The kind shows by shape,
    // NES style: plain is solid with a white core, homing flickers white,
    // bouncing is a hollow ring until its last bounce, a spawner orb has a
    // yellow core.
    //
    // Drawn chunkier than they hit, like NES shots: a ball on the 2px art
    // grid, half-size 2*ceil((radius+1)/2) -- a 2.5 bullet draws 8x8, a 4
    // acorn 12x12 -- corners cut so it reads round. The hit stays bl.radius,
    // so the art is a size up and the dodging is unchanged.
    SDL_Color c = enemy_bullet_color(_enemy_id);
    bool flash = (SDL_GetTicks() / 100) % 2 == 0;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Bullet& bl = _enemy_bullets[i];
        if (!bl.active) continue;
        if (bl.half_len > 0.0f && _log) {
            // A log: the enemy's log sprite at 2x, centred, turned to lie
            // at its angle, its frames rolling -- each log a few frames out
            // of step with the last, so they don't roll in unison.
            // A sheet with tilt rows rocks by its rows (drawn on the grid,
            // log_row) and is never turned by the engine.
            const Uint32 LOG_MS = 90;
            const EnemySheet& es = ENEMY_SHEETS[_enemy_id];
            int nf = es.log_frames, sw, sh;
            SDL_QueryTexture(_log, NULL, NULL, &sw, &sh);
            // The roll runs off the log's own age, so what it sheds (BulletSpawn
            // shed_*) can leave on a frame of the roll -- the stub at the bottom.
            int lw = sw / nf, lh = sh / es.log_rows, f = (int)(bl.age * 1000.0f / LOG_MS) % nf;
            SDL_Rect src = { f * lw, log_row(bl, es) * lh, lw, lh };
            SDL_Rect dst = { (int)bl.x - lw, (int)bl.y - lh, lw * 2, lh * 2 };
            if (es.log_rows > 1) SDL_RenderCopy(ren, _log, &src, &dst);
            else SDL_RenderCopyEx(ren, _log, &src, &dst, bl.ang * (180.0 / PI), NULL, SDL_FLIP_NONE);
            continue;
        }
        if (bl.half_len > 0.0f) {
            // A log without a sprite, on the 2px grid: in the enemy's bullet colour
            // like any of its shots, with the white core along its middle.
            // A capsule is convex, so each 2px row is one run.
            float reach = bl.half_len + bl.radius + 2.0f;
            int y0 = ((int)(bl.y - reach)) & ~1, y1 = (int)(bl.y + reach);
            int x0 = ((int)(bl.x - reach)) & ~1, x1 = (int)(bl.x + reach);
            for (int yy = y0; yy <= y1; yy += 2) {
                for (int pass = 0; pass < 2; pass++) {
                    float lim = pass ? 1.5f : bl.radius + 1.0f;   // body, then core
                    int xa = x1 + 2, xb = x0 - 2;
                    for (int xx = x0; xx <= x1; xx += 2) {
                        float nx, ny;
                        bullet_nearest(bl, xx + 1.0f, yy + 1.0f, &nx, &ny);
                        float dx = xx + 1.0f - nx, dy = yy + 1.0f - ny;
                        if (dx * dx + dy * dy <= lim * lim) { if (xx < xa) xa = xx; xb = xx; }
                    }
                    if (xa > xb) continue;
                    if (pass) _fill_rect(ren, xa, yy, xb - xa + 2, 2, 252, 252, 252, 255);
                    else      _fill_rect(ren, xa, yy, xb - xa + 2, 2, c.r, c.g, c.b, 255);
                }
            }
            continue;
        }
        int h  = 2 * (int)ceilf((bl.radius + 1.0f) / 2.0f);
        int cx = (int)bl.x & ~1, cy = (int)bl.y & ~1;
        // Homing shots flicker white; a flash_in shot flickers as it appears.
        const float FLASH_IN = 0.25f;
        bool white = (bl.homing && flash) || (bl.flash_in && bl.age < FLASH_IN && (int)(bl.age * 20.0f) % 2 == 0);
        Uint8 r = white ? 252 : c.r, g = white ? 252 : c.g, b = white ? 252 : c.b;
        _fill_rect(ren, cx - h + 2, cy - h, 2*h - 4, 2*h, r, g, b, 255);
        _fill_rect(ren, cx - h, cy - h + 2, 2*h, 2*h - 4, r, g, b, 255);
        int k = h >= 6 ? 4 : 2;   // core: two art pixels across on the big ones
        if (bl.bouncing && bl.bounces < 2)
            _fill_rect(ren, cx - h + 2, cy - h + 2, 2*h - 4, 2*h - 4, 0, 0, 0, 255);   // hollow
        else if (bl.spawner)
            _fill_rect(ren, cx - k, cy - k, 2*k, 2*k, 240, 188, 60, 255);
        else if (bl.delay <= 0.0f)   // a waiting mine has no white core: it lights when it launches
            _fill_rect(ren, cx - k/2 - 1, cy - k/2 - 1, k + 2, k + 2, 252, 252, 252, 255);
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

    // Cancelled bullets flying in, each as the item it pays -- the menu's own
    // picture of it, at 1x.
    if (!_item_icons_tried) {
        _item_icons_tried = true;
        _item_icons = IMG_LoadTexture(ren, "assets/items.png");
    }
    bool flying = false;
    for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
        const Pickup& p = _pickups[i];
        if (!p.active) continue;
        flying = true;
        if (_item_icons) {
            SDL_Rect src = { p.item * 16, 0, 16, 16 }, dst = { (int)p.x - 8, (int)p.y - 8, 16, 16 };
            SDL_RenderCopy(ren, _item_icons, &src, &dst);
        } else {
            _fill_rect(ren, (int)p.x - 2, (int)p.y - 2, 4, 4, 252, 252, 252, 255);
        }
    }

    // Hitbox marker: the hitbox itself, a white dot -- the roundest shape the
    // art grid allows at this size, a 3x3 art-pixel circle -- with a black
    // outline so it stands off the sprite and any bullet. Always shown in a
    // fight, drawn over everything, and blinking for its first second so the
    // player sees that this dot is what gets hit.
    bool intro_blink = _t < 1.0f && (int)(_t * 8.0f) % 2;
    if (_phase == BATTLE_PHASE_FIGHTING && !intro_blink) {
        int cx = (int)_bp.x, cy = (int)_bp.y;
        const int BX[5] = { -3, 1, -1, -1, -1 }, BY[5] = { -1, -1, -3, 1, -1 };
        for (int i = 0; i < 5; i++)
            _fill_rect(ren, cx + BX[i] - 2, cy + BY[i] - 2, 6, 6, 0, 0, 0, 255);
        for (int i = 0; i < 5; i++)
            _fill_rect(ren, cx + BX[i], cy + BY[i], 2, 2, 252, 252, 252, 255);
    }

    // Victory / defeat overlay
    // The win panel waits for the pickups to land and goes as the fade out starts.
    if (_phase == BATTLE_PHASE_VICTORY && !_confirmed && (!flying || _t > 1.2f)) {
        draw_nes_panel(ren, 160, 172, 320, 148);
        draw_text(ren, "VICTORY",
                  160 + (320 - text_width("VICTORY", 2)) / 2, 186, 2, 255, 255, 255);
        // Everything it paid, as the item's picture and how many, side by
        // side: the rare ones first, their count in gold, then the common
        // stuff in white. Under anything never held before, NEW, flashing
        // gently.
        int order[ITEM_COUNT], no = 0;
        for (int pass = 0; pass < 2; pass++)
            for (int it = 0; it < ITEM_COUNT; it++)
                if (_won[it] && is_common_drop(it) == (pass == 1)) order[no++] = it;
        const int GAP = 20;
        int total = 0;
        char cnt[ITEM_COUNT][8];
        for (int i = 0; i < no; i++) {
            SDL_snprintf(cnt[i], sizeof(cnt[i]), "%d", _won[order[i]]);
            total += 32 + 6 + text_width(cnt[i], 2) + (i ? GAP : 0);
        }
        int x = 320 - total / 2;
        for (int i = 0; i < no; i++) {
            bool rare = !is_common_drop(order[i]);
            if (_item_icons) {
                SDL_Rect src = { order[i] * 16, 0, 16, 16 }, dst = { x, 214, 32, 32 };
                SDL_RenderCopy(ren, _item_icons, &src, &dst);
            }
            int w = text_width(cnt[i], 2);
            draw_text(ren, cnt[i], x + 38, 222, 2, 255, rare ? 220 : 255, rare ? 40 : 255);
            if (((_won_new >> order[i]) & 1u) && (SDL_GetTicks() / 400) % 2 == 0)
                draw_text(ren, "NEW", x + (38 + w - text_width("NEW", 1)) / 2, 252, 1, 255, 220, 40);
            x += 32 + 6 + w + GAP;
        }
        // The score under the haul: what earned it, the total, and a level-up.
        {
            char line[48];
            SDL_snprintf(line, sizeof(line), "HITS %d  GRAZE %d  DEFEAT %d", _hits, _grazes, enemy_defeat_exp(_enemy_id));
            draw_text(ren, line, 320 - text_width(line, 1) / 2, 266, 1, 200, 200, 200);
            SDL_snprintf(line, sizeof(line), "+%d EXP", _exp_gain);
            draw_text(ren, line, 320 - text_width(line, 2) / 2, 280, 2, 252, 252, 252);
            if (_levels > 0 && (SDL_GetTicks() / 400) % 2 == 0) {
                SDL_snprintf(line, sizeof(line), "LEVEL UP!  LV %d", _player_ref->level);
                draw_text(ren, line, 320 - text_width(line, 1) / 2, 302, 1, 255, 255, 80);
            }
        }
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

    // Hit flash: white over the freeze, then red fading out in hard steps.
    hurt_flash(ren, _hit_t, ARENA_W, ARENA_H);

    // Fading in or out: black over everything in the NES's four hard steps.
    float dark = _darkness();
    if (dark > 0.0f) {
        dark = dark >= 1.0f ? 1.0f : (float)(int)(dark * 4.0f + 0.999f) / 4.0f;
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
        _fill_rect(ren, 0, 0, ARENA_W, ARENA_H, 0, 0, 0, (Uint8)(255 * dark));
        SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    }

    hurt_shake_end(ren, &vp);
}
