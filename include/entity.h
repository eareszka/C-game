#ifndef ENTITY_H
#define ENTITY_H

#include "input.h"

// What a weapon or tool is made of. Mined in cave dungeons, one material per
// enemy band -- see MATERIALS in src/dungeon.cpp for the floor and minimap
// colours and the difficulty thresholds that gate them, tools/oreprof.cpp for
// the census those thresholds were calibrated from, and tools/gen_cave_tiles.py
// for the rock art, which is baked per material rather than tinted at runtime.
//
// Ordered weakest to strongest. MAT_STONE is 0 so a zero-initialised DungeonMap
// degrades to the weakest material rather than to garbage, and MAT_VEYRITE is
// the rung whose generated art is a byte-for-byte copy of the hand-painted
// master, so it renders exactly as caves did before materials existed.
enum Material {
    MAT_STONE,
    MAT_BRONZE,
    MAT_EMERALD,
    MAT_VEYRITE,
    MAT_DRAVIUM,
    MAT_KHARVITE,
    MAT_REALITY_SHARD,
    MAT_COUNT   // keep last -- number of materials, not a material
};

enum WeaponType {
    WEAPON_KNIFE,
    WEAPON_CLUB,
    WEAPON_DAGGER,
    WEAPON_AXE,
    WEAPON_HALBERD,
    WEAPON_KATANA,
    WEAPON_SCYTHE,
    WEAPON_COUNT   // keep last — number of weapons, not a weapon
};

// ── Harvesting ──────────────────────────────────────────────────────────────
// Axe and scythe fell a tree in a single swing; everything else chips one point
// off at a time. Non-tree nodes are unaffected, so rock and ore still take the
// same work with any weapon.
// What a swing is landing on. Resource nodes and overlay tiles are separate
// type systems, so both map onto this and the damage rules live in one place.
typedef enum HarvestTarget {
    HARVEST_TREE,
    HARVEST_ROCK,
    HARVEST_ORE,
    HARVEST_OTHER,   // gravestones, flowers — no shortcut applies
} HarvestTarget;

inline int weapon_harvest_damage(WeaponType w, HarvestTarget t) {
    if (t == HARVEST_OTHER) return 1;
    // The scythe goes through tree, rock and ore alike in a single pass — that
    // is what makes it the farming tool. The axe only fells trees outright.
    if (w == WEAPON_SCYTHE) return 9999;
    if (w == WEAPON_AXE && t == HARVEST_TREE) return 9999;
    return 1;
}

// Some weapons swing as a travelling blade rather than striking one thing:
// the blade turns through `span` radians over `seconds`, hitting whatever it
// passes over within `radius`. `start_offset` places the arc relative to the
// way the player is facing — centre it (-span/2) for a partial arc, or leave it
// at 0 for a full turn so the blade sets off from the facing direction.
typedef struct SweepProfile {
    float span;              // radians travelled; 0 means this weapon doesn't sweep
    float start_offset;      // where the arc begins, relative to facing
    float seconds;           // time to travel the span
    float radius;            // reach in pixels
    // When set, the cooldown is the swing itself plus cooldown_recovery seconds
    // of pause afterwards, rather than the weapon profile's fire rate. A zero
    // recovery means a held key swings again the instant the blade lands.
    bool  cooldown_is_sweep;
    float cooldown_recovery;
} SweepProfile;

inline SweepProfile weapon_sweep_profile(WeaponType w) {
    switch (w) {
        // Scythe: a full clockwise turn that doubles as its own cooldown, so a
        // held key spins without pause. The farming tool.
        case WEAPON_SCYTHE: return { 6.2831853f,  0.0f,        0.45f, 80.0f, true, 0.0f  };
        // Katana: a third of the scythe's turn — 120 degrees — centred on the
        // facing direction so it takes the three neighbours in front. Those sit
        // 45 degrees either side, well inside the 60 the arc reaches, while the
        // sideways neighbours at 90 stay 30 degrees clear.
        //
        // 0.22s over that third puts the blade at ~545 deg/sec against the
        // scythe's 800, so the slash is a deliberate cut rather than a flick.
        //
        // Like the scythe, the swing is its own cooldown with no recovery, so
        // it resets the moment the blade finishes and a held key keeps cutting.
        //
        // Reach is 56 rather than the 45 a diagonal neighbour sits at, so the
        // three tiles in front are comfortably covered and loose nodes sitting
        // slightly off the grid still fall inside the arc — without getting
        // close to the 64 that would start reaching a second ring.
        case WEAPON_KATANA: {
            const float SCYTHE_SPAN = 6.2831853f;
            const float span = SCYTHE_SPAN / 3.0f;
            return { span, -span * 0.5f, 0.22f, 56.0f, true, 0.0f };
        }
        default:            return { 0.0f,        0.0f,        0.0f,   0.0f, false, 0.0f };
    }
}

inline bool weapon_sweeps(WeaponType w) { return weapon_sweep_profile(w).span > 0.0f; }

// A thrusting weapon drives straight ahead instead of turning: it looks for the
// first thing in front, then carries on `overshoot` past it, striking everything
// in a corridor `half_width` either side of the line on the way through.
typedef struct ThrustProfile {
    float half_width;        // corridor half-width in pixels; 0 = doesn't thrust
    float base_reach;        // how far ahead it looks for that first target
    float overshoot;         // how far past the first target it drives
    float seconds;           // time for the head to travel out
    bool  cooldown_is_swing; // cooldown is the thrust plus the recovery below
    float cooldown_recovery;
    // Otherwise the weapon's fire-rate cooldown scaled by this — 1.0 leaves the
    // profile alone, 0.5 makes it swing twice as often.
    float cooldown_scale;
} ThrustProfile;

inline ThrustProfile weapon_thrust_profile(WeaponType w) {
    switch (w) {
        // Halberd: a long weapon. Corridor one tile wide, looks ahead for
        // something to bite on, then drives two tiles beyond it.
        //
        // The distances are half a tile past the round numbers on purpose. On a
        // 32px grid, a reach of exactly two tiles lands precisely on the centre
        // of the second tile, where floating point decides whether it is struck
        // — and the strike test is half-open, so it was being missed. 80 stops
        // midway between the second and third tile instead: the intended two are
        // comfortably inside and the third is comfortably out. Likewise 72 for
        // the look-ahead, so a target exactly two tiles away always registers.
        //
        // Cooldown is half its fire rate: still the slow, heavy option, but not
        // as punishing as the raw 0.6/sec profile.
        case WEAPON_HALBERD: return { 16.0f, 72.0f, 80.0f, 0.14f, false, 0.0f, 0.5f };
        default:             return { 0.0f,   0.0f,  0.0f, 0.0f,  false, 0.0f, 1.0f };
    }
}

inline bool weapon_thrusts(WeaponType w) { return weapon_thrust_profile(w).half_width > 0.0f; }

// A throwing weapon launches one object in the facing direction instead of
// striking anything itself. The object flies until it meets something it can
// harvest, or leaves the screen, and is gone either way.
typedef struct ThrowProfile {
    float speed;           // pixels/sec; 0 = this weapon doesn't throw
    float radius;          // how close it must come to catch something
    float cooldown_scale;  // multiplier on the weapon's fire-rate cooldown
} ThrowProfile;

inline ThrowProfile weapon_throw_profile(WeaponType w) {
    switch (w) {
        // 600/sec is 10px a frame — well inside the ~28px it needs to come
        // within, so nothing is skipped over at speed. Cooldown is half the
        // fire rate, which still clears the flight time to the screen edge.
        case WEAPON_AXE: return { 450.0f, 12.0f, 0.5f };
        default:         return { 0.0f,    0.0f, 1.0f };
    }
}

inline bool weapon_throws(WeaponType w) { return weapon_throw_profile(w).speed > 0.0f; }

// The heavy weapons root the player for the swing, the way the original Zelda
// plants you mid-slash — no walking and no turning until it lands. Seconds, or
// 0 for the light weapons, which stay free to move. Each is well inside that
// weapon's cooldown, so the freeze never outlasts the wait you already had.
inline float weapon_freeze_seconds(WeaponType w) {
    switch (w) {
        case WEAPON_CLUB:    return 0.20f;
        case WEAPON_AXE:     return 0.24f;
        case WEAPON_HALBERD: return 0.28f;  // covers the thrust plus a beat after
        default:             return 0.0f;
    }
}

typedef struct {
    int max_hp;
    int hp;

    int max_spd;
    int spd;

    int max_mag;
    int mag;

    int max_attack;
    int attack;

    int max_luck;
    int luck;

    int max_iq;
    int iq;

    int exp; //total or gained after ene killed
} Stats;

typedef struct {
    Stats stats;
    int level;

    // Visual/animation state — shared across all game states
    int   width, height;    // sprite size in pixels (32x48)
    int   facing;           // idle frame: 0=down 3=up 6=left 8=right
    int   facing_locked;    // true after a hit/action until next direction key
    int   anim_step;
    float anim_timer;
    int   is_moving;

    // Last-pressed direction for resolving opposing key conflicts
    int   last_hdir;        // -1=left, +1=right
    int   last_vdir;        // -1=up,   +1=down

    // Inventory: counts indexed by ResourceType enum (TREE=0, ROCK=1, FLOWER=2, GOLD=3, GRAVESTONE=4)
    int   inventory[5];

    WeaponType equipped_weapon;
} Player;

// Reads WASD/arrow keys, resolves opposing keys via last-pressed,
// updates player facing/is_moving/last_hdir/last_vdir.
// Outputs normalized dx/dy (not yet scaled by speed).
void player_read_input(Player* player, const Input* in, float* out_dx, float* out_dy);

// Advances the walk animation. Call after movement with the desired frame duration.
void player_animate(Player* player, float dt, float anim_speed);

typedef struct {
    Stats stats;
    int enemy_id;
} EnemyData;

#endif
