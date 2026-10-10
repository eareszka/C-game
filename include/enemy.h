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
    // A boomerang's speed on its way back is held to this (0 = no limit:
    // it keeps speeding up).
    float max_speed      = 0.0f;
    // A log: a capsule reaching half_len either side of its centre, `radius`
    // thick, lying at `ang` and turning at `spin` rad/s -- hit, grazed and
    // drawn (the enemy's log sprite, EnemySheet::log) along its whole length.
    // With max_tilt set it only rocks: the turn reverses at +-max_tilt.
    float half_len       = 0.0f;
    float ang            = 0.0f;
    float spin           = 0.0f;
    float max_tilt       = 0.0f;
    // Shedding: first after shed_first s, then every shed_every s, it throws
    // shed_n small shots (2.5 px, its damage) fanned shed_spread radians
    // about its own heading, at shed_speed -- a log's bark flying off as it
    // rolls. None leave within 40 px of the player.
    float shed_every     = 0.0f;
    float shed_first     = 0.0f;
    int   shed_n         = 0;
    float shed_spread    = 0.0f;
    float shed_speed     = 0.0f;
    int   shed_times     = 0;       // sheds this many times, then stops (0 = for as long as it lives)
    bool  shed_dies      = false;   // ... and is gone after the last (an egg, hatched)
    float shed_spin      = 0.0f;    // what it sheds turns round the spot it left, rad/s (+ = clockwise on screen)
    // Flies straight out from where it starts while turning round that
    // spot at orbit_w rad/s (+ = clockwise on screen): rings that spin as
    // they spread.
    float orbit_w        = 0.0f;
    // With `delay` (a mine) it orbits until it launches, then flies straight.
    // ...and that spot it turns round moves at (orbit_vx, orbit_vy) px/s:
    // a whole shape drifting as it spreads (a sun coming down). With
    // `homing`, that drift turns toward the player -- the whole shape homes.
    float orbit_vx       = 0.0f, orbit_vy = 0.0f;
    // ...and that drift turns drift_turn rad/s (+ = clockwise on screen) for
    // drift_turn_for s (0 = always): a whole shape flying in an arch.
    float drift_turn     = 0.0f, drift_turn_for = 0.0f;
    // ...or that spot travels an ELLIPSE instead (path_a > 0): semi-axes
    // path_a, path_b, tilted path_tilt, about (path_cx, path_cy), from angle
    // path_phase at path_w rad/s -- shapes on orbits, an atom's.
    float path_a         = 0.0f, path_b = 0.0f, path_tilt = 0.0f, path_w = 0.0f, path_phase = 0.0f;
    float path_cx        = 0.0f, path_cy = 0.0f;
    bool  path_face      = false;   // ...and the shape turned to face along its orbit, not spinning
    float path_for       = 0.0f;    // ...for this long, then on straight the way it was going (0 = always)
    float path_round     = 1.0f;    // ...1 an ellipse; below 1 squarer (0.5: a squircle hugging a box's walls and corners)
    bool  path_aim       = false;   // ...its orbit done, it turns for the player and flies straight on at them --
    int   path_aim_slot  = -1;      // ...at the spot Enemy::aim_slot gives for this slot (>= 0), so a row of them keep in line
    bool  path_even      = false;   // ...path_w then px/s along it, an even pace all round (not rad/s, slow at the tips)
    // ...and the circle it turns on squashed to this share of its height (0 =
    // a circle): a ring seen from a little above, spinning (a tornado's).
    float orbit_squash   = 0.0f;
    // ...or, with orbit_about, it turns round (orbit_cx, orbit_cy) from where
    // it is put down, moving out from there at its speed (0: a fixed radius,
    // a shape laid down in place, spinning about its middle -- the
    // Sazae-oni's great shell; the Corocotta's gears of teeth spread).
    bool  orbit_about    = false;
    float orbit_cx       = 0.0f, orbit_cy = 0.0f;
    // Zigzags: leaves zig radians to one side of its heading and swings to
    // the other side every zig_every seconds -- a twitching, convulsing line
    // that keeps to its course.
    float zig            = 0.0f;
    float zig_every      = 0.0f;
    // Waves: its heading swings wave radians either side of its course and
    // back, smoothly, wave_w rad/s -- a shot rolling along like water.
    float wave           = 0.0f;
    float wave_w         = 0.0f;
    // Gone after this many seconds (0 = until it leaves the arena).
    float life           = 0.0f;
    // Flashes white as it appears (its first FLASH_IN s), to catch the eye --
    // and with a life, again in its last FLASH_OUT s, before it goes.
    bool  flash_in       = false;
    // Leaves from (ox, oy) instead of from the enemy: rain from the top.
    bool  from           = false;
    float ox = 0.0f, oy  = 0.0f;
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
    // Called each time its idle animation reaches its breath frame -- for a
    // creature whose idle breathes fire, whistles, screeches -- so a volley
    // can leave exactly as the sprite shows it. Returns the bullets, like fire().
    virtual int   breathe(float /*px*/, float /*py*/, BulletSpawn /*out*/[], int /*max_out*/) { return 0; }
    // Which idle frame that is (sheet frame, 0-2); most sheets draw it as 2.
    virtual int   breath_frame() const { return 2; }
    // Called each time its idle animation turns to a new frame -- for volleys
    // tied to more than one frame, or to the cycle completing (frame 0).
    // Returns the bullets, like fire().
    virtual int   on_idle_frame(int /*frame*/, float /*px*/, float /*py*/, BulletSpawn /*out*/[], int /*max_out*/) { return 0; }
    // Share of a shot's damage it takes right now (1 = all of it): a shell
    // closed, a guard up.
    virtual float armor() const { return 1.0f; }
    // How solid its sprite is drawn, 0..1, given where the player is -- a
    // ghost that only shows up close. Its shots aren't affected.
    virtual float opacity(float /*px*/, float /*py*/) const { return 1.0f; }
    // How fast its idle animation runs (1 = normal) -- and with it the
    // breath frame and on_idle_frame shots, which go off on its frames.
    virtual float anim_speed() const { return 1.0f; }
    // The sheet frame to draw, or -1 for the idle animation's own.
    virtual int anim_frame() const { return -1; }
    // The share of its HP left when its second phase starts.
    virtual float phase2_at() const { return 0.5f; }
    // How hard it draws the player toward it, px/s (0 = not at all): a
    // hurricane's suck.
    virtual float pull() const { return 0.0f; }
    // Marks it leaves on the ground (footprints) -- drawn under everything,
    // seen however far away, harmless; `kind` picks the frame of the
    // enemy's marks sheet (EnemySheet::marks), `dir` 0-3 turns it in 90-degree
    // steps (0 = toes up), `age` 0..1 fades it out.
    struct Mark { float x, y; int kind, dir; float age; };
    virtual int marks(Mark /*out*/[], int /*max*/) const { return 0; }
    // Lasers it's showing (Touhou style: a bright beam shooting out of it) --
    // drawn always; with hurt_w set, touching the beam (within hurt_w of its
    // line) costs a bar, like a shot. Fills `out`, returns how many.
    // x0,y0 at the enemy, x1,y1 the tip so far; stage 0 shooting out, 1
    // charged (full length), 2 dissipating -- `fade` 0..1 through that;
    // 3 a mark: a thin blinking line, no beam (a spot about to be hit).
    struct TeleLine { float x0, y0, x1, y1; int stage = 0; float fade = 0.0f; float hurt_w = 0.0f;
                      float orb = 0.0f; };   // orb > 0: not a line but a glowing ball of that radius at (x0, y0), drawn like the lasers
    virtual int telegraphs(TeleLine /*out*/[], int /*max*/) const { return 0; }
    // Catching: a player's shot that comes within this of it (0 = never) is
    // caught out of the air -- gone, no damage -- and catch_shot() is told
    // where. (Show it in the sprite -- a catching pose -- not a ring: the user.)
    virtual float catch_radius() const { return 0.0f; }
    virtual void  catch_shot(float /*x*/, float /*y*/) {}
    // Damage for touching its body (whole HP bars, like a bullet's); 0 for
    // an enemy that is harmless to touch.
    virtual float contact_damage() const { return 0.0f; }
    // Where shots sharing an aim slot (BulletSpawn::path_aim_slot) head when
    // their orbits end: by default the player, wherever they are then.
    virtual void  aim_slot(int /*slot*/, float px, float py, float* tx, float* ty) { *tx = px; *ty = py; }
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

// Creates enemy by id (0 to ENEMY_COUNT-1); caller owns the pointer.
Enemy* enemy_create(int enemy_id);

// The roster: an enemy's id is its region block (7 a region, grassland 0-6 ...
// ocean 42-49) and its sprite file -- NOT how hard it is. How hard it is is
// its tier, set here by the user, one per enemy:
//   STARTER  00, the first fight
//   LOW      01-05, one tier that gets harder in id order; 50 53-56 65 66 68 69
//   MEDIUM   above LOW: 08 09 11 14 15 17 57-60 70-75
//   UPPER    between MEDIUM and HARD: 21 22 24 26 28 61-64 67 76-82
//   HARD     above UPPER: 16 18 19 20 27 33 39 42 43 83-89
//   SEVERE   between HARD and ELITE: 25 35 36 37 38 40 45 46 47 90-95
//   ELITE    very hard, a tier below the tier-1 bosses: 07 10 12 13 29 31 32 41 48 51 96-99. They
//            spawn like any enemy, but only in the wastelands and the
//            hard-to-reach dungeons (place_spawners in src/dungeon.cpp).
//   BOSS1/2  the bosses the game needs beaten, met where they're placed and
//            never as random spawns: 06 23 30 about level, then 34 44 49 52.
//   BOSS3    the final boss, 100 the flesh planet (the ending).
//   UNSET    not placed yet (none now); ranked by region order until it is.
// Inline so the dungeon tools need not link the enemies.
enum EnemyTier : unsigned char { T_UNSET, T_STARTER, T_LOW, T_MEDIUM, T_UPPER, T_HARD, T_SEVERE, T_ELITE, T_BOSS1, T_BOSS2, T_BOSS3 };
static const EnemyTier ENEMY_TIERS[] = {
    T_STARTER, T_LOW,    T_LOW,    T_LOW,    T_LOW,    T_LOW,    T_BOSS1,   //  0- 6 grassland
    T_ELITE,   T_MEDIUM, T_MEDIUM, T_ELITE,  T_MEDIUM, T_ELITE,  T_ELITE,   //  7-13 forest
    T_MEDIUM,  T_MEDIUM, T_HARD,   T_MEDIUM, T_HARD,   T_HARD,   T_HARD,    // 14-20 snow
    T_UPPER,   T_UPPER,  T_BOSS1,  T_UPPER,  T_SEVERE, T_UPPER,  T_HARD,    // 21-27 desert
    T_UPPER,   T_ELITE,  T_BOSS1,  T_ELITE,  T_ELITE,  T_HARD,   T_BOSS2,   // 28-34 wasteland
    T_SEVERE,  T_SEVERE, T_SEVERE, T_SEVERE, T_HARD,   T_SEVERE, T_ELITE,   // 35-41 mountains
    T_HARD,    T_HARD,   T_BOSS2,  T_SEVERE,  T_SEVERE, T_SEVERE, T_ELITE, T_BOSS2,   // 42-49 ocean
    // 50 on: cryptids added after the region blocks -- region in enemy_region.
    T_LOW,     T_ELITE,  T_BOSS2,                                            // 50 Teakettler, 51 Aspidochelone, 52 Sannaja
    // 53-64: fearsome critters (abookofcreatures.com), no sprites yet
    T_LOW, T_LOW, T_LOW, T_LOW,   // 53-56 Come-at-a-body, Billdad, Wapaloosie, Moskitto
    T_MEDIUM, T_MEDIUM, T_MEDIUM, T_MEDIUM,   // 57-60 Dingbat, Agropelter, Tripodero, Rumptifusel
    T_UPPER, T_UPPER, T_UPPER, T_UPPER,   // 61-64 Roperite, Hugag, Hidebehind, Dungavenhooter
    // 65-99: folklore creatures (abookofcreatures.com), no sprites yet -- names in ENEMY_NAMES
    T_LOW, T_LOW, T_UPPER, T_LOW, T_LOW, T_MEDIUM, // 65-70 (67 Lagopus moved up to UPPER: its ring fight)
    T_MEDIUM, T_MEDIUM, T_MEDIUM, T_MEDIUM, T_MEDIUM, T_UPPER,   // 71-76
    T_UPPER, T_UPPER, T_UPPER, T_UPPER, T_UPPER, T_UPPER,   // 77-82
    T_HARD, T_HARD, T_HARD, T_HARD, T_HARD, T_HARD,   // 83-88
    T_HARD, T_SEVERE, T_SEVERE, T_SEVERE, T_SEVERE, T_SEVERE,   // 89-94
    T_SEVERE, T_ELITE, T_ELITE, T_ELITE, T_ELITE,   // 95-99
    T_BOSS3,                                        // 100 the flesh planet, the final boss
};
static const int ENEMY_COUNT = (int)(sizeof(ENEMY_TIERS) / sizeof(ENEMY_TIERS[0]));
inline EnemyTier enemy_tier(int id) { return id >= 0 && id < ENEMY_COUNT ? ENEMY_TIERS[id] : T_UNSET; }
inline bool enemy_is_boss(int id)  { return enemy_tier(id) >= T_BOSS1; }
inline bool enemy_is_elite(int id) { return enemy_tier(id) == T_ELITE; }

// Region: 0 grassland, 1 forest, 2 snow, 3 desert, 4 wasteland, 5 mountains,
// 6 ocean. The original fifty are seven a region by id (ocean 42-49); every
// later one says its own.
static const unsigned char LATER_REGIONS[] = {
    1, 6, 5,                       // 50 Teakettler (Northwoods), 51 Aspidochelone, 52 Sannaja (Tibet)
    5, 1, 1, 0, 1, 1, 3, 1, 5, 2, 1, 4,   // 53-64 fearsome critters
    3, 3, 2, 0, 1, 2, 6, 0, 1, 1, 0, 2,   // 65-76
    3, 3, 2, 1, 5, 4, 5, 2, 5, 3, 4, 6,   // 77-88
    5, 6, 4, 1, 6, 6, 2, 6, 6, 1, 4,   // 89-99
};
inline int enemy_region(int id) {
    if (id >= 50) return id - 50 < (int)sizeof(LATER_REGIONS) ? LATER_REGIONS[id - 50] : 0;
    return id >= 42 ? 6 : id / 7;
}

// EXP for beating it, by tier -- STARTER 50, LOW 100, MEDIUM 250, UPPER 350, HARD 450, SEVERE 600, ELITE 800,
// BOSS1 1500, BOSS2 3000, BOSS3 6000 -- plus 15 for each earlier member of the same tier,
// so a tier still climbs in id order. UNSET: 50 + 25 per earlier unset.
int enemy_defeat_exp(int enemy_id);

// The monster part enemy_id drops when beaten.
MonsterPart enemy_part(int enemy_id);

// The colour enemy_id's bullets are drawn in.
SDL_Color enemy_bullet_color(int enemy_id);

// Reseed enemy RNG so patterns vary between encounters.
void seed_enemy_rng(unsigned int seed);

#endif
