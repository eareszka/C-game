#ifndef BATTLE_H
#define BATTLE_H

#include <SDL2/SDL.h>
#include "input.h"
#include "entity.h"
#include "enemy.h"

// ── Weapon types ──────────────────────────────────────────────────────────────

// No speed: every weapon's shots fly at BULLET_SPEED (src/battle.cpp).
struct ProjectileProfile {
    float damage;
    float fire_rate;
    int   count;
    float spread;
    float radius;
    bool  pierces;   // passes through the enemy instead of stopping, striking it
                     // again each time its hit flash ends while still inside
};

ProjectileProfile weapon_profile(WeaponType type);

// FASTER, the fire-speed upgrade (Weapon::oil, 0 to WEAPON_OIL_MAX). Level 0 is
// the weapon as weapon_profile() has it. Each level multiplies its fire rate
// by the same amount, so every weapon reaches TOUHOU_FIRE_RATE together at the
// top; and its damage a shot moves the other way (or less far) so that its
// damage per second grows by the same FASTER_DPS_AT_MAX for every weapon --
// fast weapons and slow ones keep their places, the scythe first, all the
// way up.
static const float TOUHOU_FIRE_RATE  = 15.0f;   // shots a second at the top: a shot every 4 frames
static const float FASTER_DPS_AT_MAX = 8.0f;    // damage per second at the top, over level 0's
float faster_fire_rate(float base_rate, int level);
float faster_damage(float base_rate, float base_damage, int level);

// Display name, e.g. "KATANA". Shared by the battle HUD and the debug menu so
// there is one list to update when a weapon is added.
const char* weapon_name(WeaponType type);

// ── Arena constants ────────────────────────────────────────────────────────────

static const int ARENA_W  = 640;
static const int ARENA_H  = 480;
// The top HUD bar covers y < ARENA_TOP: the arena, and everything in it, is below.
static const int ARENA_TOP = 28;

// The player's battle shots (art/battle/shots_design.py): one PLAYER_SHOT_CELL
// square per weapon (column) and ore (row), drawn at 2x, each pointing right.
// Flat NES shots in the ore's colours, each the plain silhouette of its weapon;
// the katana and scythe fire crescent slashes, the scythe's the biggest.
static const char* const PLAYER_SHOT_SHEET = "assets/battle/player_shots.png";
static const int         PLAYER_SHOT_CELL  = 16;

// The weapons themselves (art/items/weapons_design.py): the same rows and
// columns, 16px cells, each drawn grip low left and point high right. The
// menu shows them and the map swings them.
static const char* const WEAPON_ICON_SHEET = "assets/weapon_icons.png";
static const int         WEAPON_ICON_CELL  = 16;
static const int ENEMY_X  = 320;
static const int ENEMY_Y  = 160;
static const int ENEMY_R  = 24;
// The player's hitbox: a small core at the body's centre, Touhou-sized, so a
// pattern's gaps are read against the dot rather than the whole sprite. 3
// reaches the edge of the crouch marker's white dot, so what the player sees
// is exactly what gets hit.
static const float PLAYER_R = 3.0f;

#define MAX_PLAYER_BULLETS 128   // a Touhou-rate stream of three, piercing, stays well under
#define MAX_ENEMY_BULLETS  1024  // Grand'Goule's phase 2 keeps ~270 in the air; Lagopus ~670; Dingbat's ring maze ~650

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
    bool  homing;         // steers toward player each frame
    float homing_timer;   // counts down; when 0 homing turns off
    float age;            // player shots: seconds since fired
    float delay;          // a mine's seconds left sitting before it launches
    float launch_speed;   // its speed then, at the player
    float launch_off;     // radians off the line to the player
    float accel;          // a boomerang's px/s^2 along its first heading
    float ux, uy;         // that heading
    float min_speed;      // slows to this and keeps going, instead of turning back
    float max_speed;      // a boomerang's top speed coming back (0 = none)
    float half_len;       // a log's half length (0 = a round bullet)
    float ang, spin;      // ... the way it lies, and how fast it turns
    float max_tilt;       // ... rocking: the turn reverses past +-this (0 = turns freely)
    float shed_every, shed_t, shed_spread, shed_speed;   // shedding small shots (BulletSpawn)
    int   shed_n;
    int   shed_left;      // sheds still to come (-1 = no limit)
    bool  shed_dies;      // gone after its last shed
    float shed_spin;      // what it sheds orbits, rad/s
    float ocx, ocy, orad, oang, ovr, ow;   // orbiting: centre, radius, angle, speed out, turn rate (ow 0 = straight)
    float ocvx, ocvy;                      // ...and the centre's drift
    float octurn, octurn_t;                // ...turning at this, rad/s (an arch), for this long (<= 0: always)
    float pa, pb, ptilt, pw, pphi, pcx, pcy; // ...or the centre travelling an ellipse (pa > 0)
    bool  pface; float obase;               // ...the shape facing along it (obase: its angle in the shape)
    float pfor;                             // ...for this long, then straight on (<= 0: always)
    float pround;                           // ...1 an ellipse, below 1 squarer
    bool  peven;                            // ...pw is px/s along it, not rad/s
    bool  paim; int paim_slot;              // ...then straight at the player (or the enemy's aim slot)
    float osq;                             // ...and the circle squashed to this share of its height (0 = round)
    float zig, zig_every, zig_t; int zig_s; // zigzagging: swing, period, timer, which side it's on
    float wave, wave_w, wave_t;             // waving: swing, rate, age
    float life;                             // seconds it lasts (0 = until it leaves)
    bool  flash_in;       // flashes white for its first moment
    // Player shots: what fired it, so a shot in flight keeps its own weapon's
    // look and strike after the player swaps.
    int   weapon;         // WeaponType
    int   material;       // Material
    bool  pierces;
    bool  grazed;         // enemy shots: already counted as a graze (once each)
};

// ── Phase ─────────────────────────────────────────────────────────────────────

enum BattlePhase {
    BATTLE_PHASE_INTRO,      // fading up from black, everyone already in place
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
    bool  focus;   // ctrl held: slow and precise, the sprite drawn see-through
    float dim;     // 0 lit .. 2 darkest: steps down while focused, back up on release
};

// One cancelled bullet flying to the player after the kill, as the item it
// pays (an Item, include/crafting.h).
struct Pickup {
    float x, y, vx, vy;
    bool  active;
    int   item;
};

// ── Battle scene ──────────────────────────────────────────────────────────────

// Being hurt, as a fight shows it: the screen shakes side to side on the 2px
// art grid, dying away, and flashes white then red in hard steps. t is the
// seconds since the hurt. Shared by the fights and the oasis's drowning.
// hurt_shake_begin moves the viewport (keeping the old in *saved) and
// hurt_shake_end puts it back; hurt_flash covers w x h from the top left.
void hurt_shake_begin(SDL_Renderer* ren, float t, SDL_Rect* saved);
void hurt_shake_end(SDL_Renderer* ren, const SDL_Rect* saved);
void hurt_flash(SDL_Renderer* ren, float t, int w, int h);

class BattleScene {
public:
    // chained: the next fight of a pack. No fade in -- the player glides from
    // (from_x, from_y), where the last fight left them, back to the start,
    // while the new enemy drops in from the top.
    BattleScene(Player* player, int enemy_id,
                bool chained = false, float from_x = 0.0f, float from_y = 0.0f);

    // More of the pack waits after this fight: a win ends without fading out.
    void  set_more_after(bool more) { _more_after = more; }
    float player_x() const { return _bp.x; }

    // What the top HUD shows during a fight. hud_enemy is null once it's beaten.
    float hud_hp()      const { return _bp.hp; }
    float hud_max_hp()  const { return _bp.max_hp; }
    float hud_stamina() const;   // 0..1, the weapon's cooldown refilling
    float hud_swap_t()   const { return _swap_t; }    // seconds since the weapon was swapped
    void  sync_weapon();                               // after the TAB menu: fire as the equipped weapon
    // EXP earned this fight so far, not yet paid: the top bar adds it to the
    // player's so the score climbs live. Paid (and any level-up applied) only
    // on the win, so afterwards this is 0.
    int   hud_exp()      const { return _phase == BATTLE_PHASE_VICTORY ? 0 : _hits + _grazes; }
    float hud_hit_t()    const { return _hit_t; }     // seconds since the player was last hit
    int   hud_hit_bars() const { return _hit_bars; }  // how many bars that hit took
    const Enemy* hud_enemy() const { return _phase == BATTLE_PHASE_VICTORY ? nullptr : _enemy; }
    float player_y() const { return _bp.y; }
    // A textbox goes near the top, where it covers least of the dodging --
    // unless the player is up there, when it mirrors to the bottom.
    bool  textbox_low() const { return _bp.y < ARENA_H * 0.5f; }
    ~BattleScene();

    void update(const Input* in, float dt);
    void draw(SDL_Renderer* ren, SDL_Texture* player_sprite) const;

    BattlePhase get_phase() const { return _phase; }
    // True once the end panel is confirmed and the fade to black has played.
    bool is_done() const { return _done; }

private:
    BattlePhase  _phase;
    BattlePlayer _bp;
    Enemy*       _enemy;
    Player*      _player_ref;
    WeaponType   _weapon_type;
    Bullet       _player_bullets[MAX_PLAYER_BULLETS];
    Bullet       _enemy_bullets[MAX_ENEMY_BULLETS];
    Pickup       _pickups[MAX_ENEMY_BULLETS];
    int          _enemy_id;
    float        _t        = 0.0f;   // seconds into the current phase
    bool         _confirmed = false; // end panel dismissed
    float        _outro_t  = 0.0f;   // seconds into the fade to black
    bool         _chained  = false;
    float        _from_x   = 0.0f, _from_y = 0.0f;
    bool         _more_after = false;
    bool         _done     = false;
    float        _hit_t    = 99.0f;  // seconds since the player was last hit
    float        _swap_t   = 99.0f;  // seconds since the weapon was swapped
    float        _anim_ms    = 0.0f;   // the enemy's idle-animation clock, run at Enemy::anim_speed
    int          _idle_frame = -1;   // the enemy's idle frame last update, to catch frame 2 starting
    float        _fire_iv    = 0.0f; // the enemy's fire interval last update, to catch a speed-up
    int          _hit_bars = 0;      // bars that hit took
    // What the win paid, by Item, for the victory panel.
    int          _won[32]    = {};
    // The score -- EXP is hits + grazes + the defeat bonus, paid on the win.
    int          _hits       = 0;   // the player's shots that landed
    int          _grazes     = 0;   // enemy shots that passed close without hitting
    int          _exp_gain   = 0;   // what the win paid
    int          _levels     = 0;   // levels that gained
    unsigned     _won_new    = 0;   // which of them the player had never held before
    // The item icons, for the pickups (assets/items.png); loaded on first draw.
    mutable SDL_Texture* _item_icons       = nullptr;
    mutable bool         _item_icons_tried = false;
    // The enemy's sprite sheet, loaded on the first draw (the scene has no
    // renderer before then); null when the enemy has no sprite yet.
    mutable SDL_Texture* _sheet       = nullptr;
    mutable bool         _sheet_tried = false;
    mutable SDL_Texture* _flap        = nullptr;   // wing-flap sheet, if the enemy has one
    mutable SDL_Texture* _alt         = nullptr;   // alternate idle sheet, if the enemy has one
    mutable SDL_Texture* _log         = nullptr;   // its log bullet sprite, if it throws logs
    mutable SDL_Texture* _marks       = nullptr;   // its ground-mark sprites (footprints), if it leaves any
    // The same sheets as solid white silhouettes, for the hit flash.
    mutable SDL_Texture* _sheet_white = nullptr;
    mutable SDL_Texture* _flap_white  = nullptr;
    mutable SDL_Texture* _alt_white   = nullptr;
    // The player's bullets, one cell per weapon and ore (art/battle/
    // gen_shots.py); loaded on the first draw like the enemy's.
    mutable SDL_Texture* _bullets       = nullptr;
    mutable bool         _bullets_tried = false;
    // The same sheet ordered-dithered to 12/16, 8/16 and 4/16 of its pixels:
    // the steps a shot fades through as it leaves the arena.
    mutable SDL_Texture* _bullets_fade[3] = {};
    // A shot's hitbox: its sprite's opaque bounds, in screen pixels about the
    // bullet's centre, before it is turned to _shot_angle(). Measured from the
    // sheet in the constructor; +-radius when the sheet is missing.
    float        _shot_x0, _shot_y0, _shot_x1, _shot_y1;
    float        _shot_reach;   // furthest the box reaches from the centre, any turn
    // Hitbox radius: ENEMY_R until the sheet loads, then sized to the sprite.
    mutable float        _hit_r       = (float)ENEMY_R;
    // Seconds left of the enemy's white hit flash. Only a look: unlike the
    // player's iframes it never stops the next shot landing.
    float        _enemy_flash = 0.0f;
    float        _flash_gap   = 0.0f;   // seconds until another hit may flash it
    float        _pierce_wait = 0.0f;   // seconds until a piercing shot may strike again

    void _draw_enemy(SDL_Renderer* ren) const;

    void _update_movement(const Input* in, float dt);
    void _update_player_fire(const Input* in, float dt);
    void _update_enemy(float dt);
    void _move_bullets(float dt);
    void _check_collisions();
    void _equip(WeaponType w);   // set up firing for w: profile, upgrades, shot hitbox
    void _cycle(int dir);        // next (+1) or previous (-1) owned weapon
    double _shot_angle(const Bullet& bl) const;   // degrees, as drawn
    float  _shot_scale(const Bullet& bl) const;   // size against the sprite, as drawn
    float  _shot_edge_gap(const Bullet& bl) const; // centre to the edge it is heading for
    void _win();
    void _update_pickups(float dt);
    float _darkness() const;  // 1 = black: the fade in and the fade out
    float _chain_in() const;  // 0..1 progress of a chained intro; 1 otherwise
    void _spawn_player_bullet(float angle);
    void _spawn_enemy_bullet(const BulletSpawn& bs);
    void _spawn_bullet_at(float ox, float oy, const BulletSpawn& bs);

    static void _fill_rect(SDL_Renderer* ren, int x, int y, int w, int h,
                            Uint8 r, Uint8 g, Uint8 b, Uint8 a);
    static void _draw_rect_outline(SDL_Renderer* ren, int x, int y, int w, int h,
                                    Uint8 r, Uint8 g, Uint8 b);
};

#endif
