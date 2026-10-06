#include "enemy.h"
#include <math.h>

static const float PI  = 3.14159265f;
static const float TAU = 6.28318530f;

// ── RNG ───────────────────────────────────────────────────────────────────────

static unsigned int s_erng = 0xDEADBEEFu;

void seed_enemy_rng(unsigned int seed) { s_erng ^= seed; }

static float ernd() {
    s_erng = s_erng * 1664525u + 1013904223u;
    return (float)(s_erng >> 16) / 65536.0f;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

static BulletSpawn mk(float angle, float speed, float radius, float damage) {
    return { cosf(angle)*speed, sinf(angle)*speed, radius, damage, false };
}

// Bouncing bullet — blue, reflects off walls, deleted after 3rd bounce.
static BulletSpawn mkb(float angle, float speed, float radius, float damage) {
    return { cosf(angle)*speed, sinf(angle)*speed, radius, damage, true };
}

// Spawner orb — large bright-orange, slow, emits 8-way ring every spawn_interval seconds.
static BulletSpawn mksp(float angle, float speed, float spawn_interval) {
    return { cosf(angle)*speed, sinf(angle)*speed, 9.0f, 2.0f, false, true, spawn_interval };
}

// Homing bullet — white/purple flash, curves toward player, then goes straight.
static BulletSpawn mkh(float angle, float speed, float radius, float damage,
                       float homing_time = 2.0f) {
    BulletSpawn b = mk(angle, speed, radius, damage);
    b.homing       = true;
    b.homing_timer = homing_time;
    return b;
}

// Homing spawner orb — white/orange flash, curves toward player AND emits rings.
static BulletSpawn mkhsp(float angle, float speed, float spawn_interval) {
    BulletSpawn b = mksp(angle, speed, spawn_interval);
    b.homing = true;
    return b;
}

static float aim_at(float ox, float oy, float tx, float ty) {
    return atan2f(ty - oy, tx - ox);
}

// Returns true when the enemy is in its enraged (low-HP) phase.
#define ENRAGED (hp < max_hp * 0.5f)

// ── Grassland enemies (IDs 0–6) ───────────────────────────────────────────────

// Hops across the top of the arena: stands STAND_T, then arcs over HOP_T to a
// new x at least a body-length away, and flags the landing. Shared by the
// hopping hares, whose phase 2s fire off it.
struct Hopper {
    static constexpr float HOME_Y  = 160.0f;
    static constexpr float HOP_T   = 0.5f;   // seconds in the air
    static constexpr float STAND_T = 1.8f;   // seconds between hops
    float hop_t   = -1.0f;   // seconds into a hop; -1 = standing
    float stand_t = 0.0f;
    float x0 = 0.0f, x1 = 0.0f;
    bool  landed  = false;   // touched down; the owner clears it when it fires

    bool airborne() const { return hop_t >= 0.0f; }
    void update(float dt, float& x, float& y) {
        if (hop_t >= 0.0f) {
            hop_t += dt;
            float k = hop_t / HOP_T;
            if (k >= 1.0f) { k = 1.0f; hop_t = -1.0f; stand_t = 0.0f; landed = true; }
            x = x0 + (x1 - x0) * k;
            y = HOME_Y - 40.0f * sinf(PI * k);
        } else if ((stand_t += dt) >= STAND_T) {
            hop_t = 0.0f;
            x0 = x;
            do x1 = 140.0f + ernd() * 360.0f; while (fabsf(x1 - x) < 90.0f);
        }
    }
};

// Winged, antlered hare.
// Phase 1, Antler Fan: 2 or 3 lines of bullets at the player, the count
//   picked at random each volley -- three put one straight at you, two
//   leave the gap there -- so you keep reading it rather than standing still.
// Phase 2 (half HP), Hop & Gust: it hops across the top of the arena; each
//   landing throws the antler fan again from the new spot, and while it
//   stands a wing-gust stream sweeps back and forth through the player.
class Skvader : public Enemy {
    Hopper hop;
    float  sweep = 0.0f;

    // 2 or 3 lines at angle a, picked at random: three put one straight at
    // the player, two leave the gap there.
    static int antler_fan(float a, BulletSpawn out[]) {
        int n = ernd() < 0.5f ? 2 : 3;
        for (int i = 0; i < n; i++)
            out[i] = mk(a + (i - (n - 1) * 0.5f) * 0.22f, 170.0f, 2.5f, 5.0f);
        return n;
    }
public:
    Skvader() : Enemy(320, Hopper::HOME_Y, 240, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "SKVADER"; }
    float       fire_interval() const override { return ENRAGED ? 0.11f : 0.55f; }
    void update(float dt, float, float) override {
        if (!ENRAGED) return;
        sweep += dt;
        hop.update(dt, x, y);
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (!ENRAGED) return antler_fan(a, out);
        if (hop.airborne()) return 0;   // nothing while airborne
        if (hop.landed) {
            hop.landed = false;
            return antler_fan(a, out);
        }
        out[0] = mk(a + 0.6f * sinf(sweep * 3.0f), 210.0f, 2.5f, 5.0f);
        return 1;
    }
};

// Antlered, winged, fanged hare: the Skvader's harder cousin.
// Phase 1, Antler Fan: a two-speed 5-way fan at the player, nudged half a gap
//   every volley, so standing still is the one thing that doesn't work.
// Phase 2 (half HP), Hop & Gust: it hops across the top of the arena; each
//   landing throws a 16-bullet ring, and while it stands a wing-gust stream
//   sweeps back and forth through the player.
class Wolpertinger : public Enemy {
    Hopper hop;
    float  sweep  = 0.0f;
    int    volley = 0;
public:
    Wolpertinger() : Enemy(320, Hopper::HOME_Y, 280, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "WOLPERTINGER"; }
    float       fire_interval() const override { return ENRAGED ? 0.11f : 0.55f; }
    void update(float dt, float, float) override {
        if (!ENRAGED) return;
        sweep += dt;
        hop.update(dt, x, y);
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (!ENRAGED) {
            float off = (volley++ & 1) ? 0.11f : 0.0f;
            int n = 0;
            for (int layer = 0; layer < 2; layer++)
                for (int i = -2; i <= 2; i++)
                    out[n++] = mk(a + off + i * 0.22f, layer ? 195.0f : 150.0f, 2.5f, 5.0f);
            return n;
        }
        if (hop.airborne()) return 0;   // nothing while airborne
        if (hop.landed) {
            hop.landed = false;
            float base = ernd() * TAU;
            for (int i = 0; i < 16; i++)
                out[i] = mk(base + i * (TAU / 16.0f), 120.0f, 3.0f, 5.0f);
            return 16;
        }
        out[0] = mk(a + 0.6f * sinf(sweep * 3.0f), 210.0f, 2.5f, 5.0f);
        return 1;
    }
};

// Lumberjack-lore tree creature, known for its squeak: its attacks are
// sound rings.
// Phase 1, Squeak: an expanding ring with one gap, somewhere within 60
//   degrees of the player -- read the gap, slip through it.
// Phase 2 (half HP), Echo: rings come quicker, each gap 45 degrees on from
//   the last so you weave, and between rings a tight spread of slow acorns
//   punishes waiting in the gap.
class Treesqueak : public Enemy {
    int   volley = 0;
    float gap    = 0.0f;   // last ring's gap, relative to the aim at the player

    // 24 around, the 4 nearest angle `at` left out.
    static int ring(float at, BulletSpawn out[]) {
        const int N = 24;
        int n = 0;
        for (int i = 0; i < N; i++) {
            float ang = at + (i + 0.5f) * (TAU / N) - PI;   // `at` sits mid-gap at i = N/2
            if (i >= N / 2 - 2 && i < N / 2 + 2) continue;
            out[n++] = mk(ang, 110.0f, 2.5f, 5.0f);
        }
        return n;
    }
public:
    Treesqueak() : Enemy(320, 160, 320, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "TREESQUEAK"; }
    float       fire_interval() const override { return ENRAGED ? 0.45f : 1.1f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (!ENRAGED) {
            gap = (ernd() * 2.0f - 1.0f) * (PI / 3.0f);
            return ring(a + gap, out);
        }
        if (volley++ % 2 == 0) {
            // Next gap 45 degrees on, either way, kept within reach.
            gap += ernd() < 0.5f ? PI / 4.0f : -PI / 4.0f;
            if (gap >  PI / 3.0f) gap -= PI / 2.0f;
            if (gap < -PI / 3.0f) gap += PI / 2.0f;
            return ring(a + gap, out);
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i - 1) * 0.12f, 140.0f, 4.0f, 5.0f);
        return 3;
    }
};

// Crested, rooster-like bird.
// Phase 1, Peck: bursts of 4 quick shots down one line, aimed when the burst
//   starts and then locked -- one step aside clears it, if you take it in time.
// Phase 2 (half HP), Peck & Flap: bursts of 5, then a wing beat throws an arc
//   of feathers out to each side, leaving the middle lane -- where the pecks
//   come -- as the only room to move -- and it takes off on that beat, flying
//   to a new perch across the top before the next burst.
class Qique : public Enemy {
    static constexpr float FLY_T = 0.7f;   // seconds in the air; lands before the next burst
    int   shot  = 0;       // shots fired; a cycle is a burst, plus a flap in phase 2
    float lock  = 0.0f;    // this burst's aim
    float fly_t = -1.0f;   // seconds into a flight; -1 = perched
    float fx0 = 0.0f, fy0 = 0.0f, fx1 = 0.0f, fy1 = 0.0f;

    int cycle() const { return ENRAGED ? 6 : 4; }   // phase 2: 5 pecks + 1 flap
public:
    Qique() : Enemy(320, 160, 360, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QIQUE"; }
    // Quick within a burst, a breath between bursts.
    float fire_interval() const override {
        return shot % cycle() == 0 ? (ENRAGED ? 0.8f : 0.9f) : 0.08f;
    }
    float flap_phase() const override { return fly_t < 0.0f ? -1.0f : fly_t / FLY_T; }
    // A flight eases out and in along a raised arc: a flap's lift, a glide down.
    void update(float dt, float, float) override {
        if (fly_t < 0.0f) return;
        fly_t += dt;
        float k = fly_t / FLY_T;
        if (k >= 1.0f) { k = 1.0f; fly_t = -1.0f; }
        float e = k * k * (3.0f - 2.0f * k);
        x = fx0 + (fx1 - fx0) * e;
        y = fy0 + (fy1 - fy0) * e - 30.0f * sinf(PI * k);
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        int k = shot++ % cycle();
        if (k == 0) lock = a;
        if (ENRAGED && k == 5) {
            // Take off: a short hop to a new perch, 50-180 to either side
            // (turning back at the arena's edges) and up to 40 up or down.
            fly_t = 0.0f;
            fx0 = x; fy0 = y;
            float dx = (50.0f + ernd() * 130.0f) * (ernd() < 0.5f ? -1.0f : 1.0f);
            if (x + dx < 140.0f || x + dx > 500.0f) dx = -dx;
            fx1 = x + dx;
            fy1 = y + (ernd() * 2.0f - 1.0f) * 40.0f;
            if (fy1 < 120.0f) fy1 = 120.0f;
            if (fy1 > 200.0f) fy1 = 200.0f;
            // Flap: 7 feathers each side, centred 1 radian off the aim, so
            // the lane within about 0.6 of it stays open.
            int n = 0;
            for (int side = -1; side <= 1; side += 2)
                for (int i = -3; i <= 3; i++)
                    out[n++] = mk(a + side * 1.0f + i * 0.12f, 150.0f, 2.5f, 5.0f);
            return n;
        }
        out[0] = mk(lock, 230.0f, 2.5f, 5.0f);
        return 1;
    }
};

class Lili : public Enemy {
public:
    Lili() : Enemy(320, 160, 30, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "LILI"; }
    float       fire_interval() const override { return ENRAGED ? 0.6f : 0.9f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.25f, 175.0f, 3.5f, 0.8f);
            out[1] = mk(a + 0.25f, 175.0f, 3.5f, 0.8f);
            out[2] = mk(a + PI/2.0f, 130.0f, 3.0f, 0.6f);
            out[3] = mk(a - PI/2.0f, 130.0f, 3.0f, 0.6f);
            return 4;
        }
        out[0] = mk(a - 0.2f, 155.0f, 3.5f, 0.7f);
        out[1] = mk(a + 0.2f, 155.0f, 3.5f, 0.7f);
        return 2;
    }
};

class CrowingCrestedCobra : public Enemy {
public:
    CrowingCrestedCobra() : Enemy(320, 160, 38, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "CROWING CRESTED COBRA"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.32f, 185.0f, 3.5f, 1.0f);
            return 5;
        }
        out[0] = mk(a,         160.0f, 3.5f, 0.9f);
        out[1] = mk(a - 0.35f, 140.0f, 3.5f, 0.8f);
        out[2] = mk(a + 0.35f, 140.0f, 3.5f, 0.8f);
        return 3;
    }
};

class WakmangganchiAragondi : public Enemy {
public:
    WakmangganchiAragondi() : Enemy(320, 160, 45, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "WAKMANGGANCHI ARAGONDI"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.25f, 190.0f, 4.0f, 1.1f);
            out[5] = mk(a + PI/2.0f, 150.0f, 3.5f, 0.9f);
            out[6] = mk(a - PI/2.0f, 150.0f, 3.5f, 0.9f);
            return 7;
        }
        out[0] = mk(a,        170.0f, 4.0f, 1.0f);
        out[1] = mk(a - 0.22f,150.0f, 3.5f, 0.9f);
        out[2] = mk(a + 0.22f,150.0f, 3.5f, 0.9f);
        return 3;
    }
};

// ── Forest enemies (IDs 7–13) ─────────────────────────────────────────────────

class Alber : public Enemy {
public:
    Alber() : Enemy(320, 160, 50, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "ALBER"; }
    float       fire_interval() const override { return ENRAGED ? 0.5f : 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.2f, 195.0f, 4.0f, 1.1f);
            out[1] = mk(a,        195.0f, 4.0f, 1.2f);
            out[2] = mk(a + 0.2f, 195.0f, 4.0f, 1.1f);
            return 3;
        }
        out[0] = mk(a, 170.0f, 4.0f, 1.0f);
        return 1;
    }
};

class Snawfus : public Enemy {
public:
    Snawfus() : Enemy(320, 160, 58, {1.0f,1.0f,1.0f,1.25f,1.25f,1.25f,1.25f}) {}
    const char* name()          const override { return "SNAWFUS"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.3f, 200.0f, 3.5f, 1.1f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.3f, 175.0f, 3.5f, 1.0f);
        return 3;
    }
};

class QuestingBeast : public Enemy {
public:
    QuestingBeast() : Enemy(320, 160, 68, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QUESTING BEAST"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 195.0f, 3.5f, 1.1f);
            out[5] = mk(a, 250.0f, 3.0f, 1.3f);
            return 6;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.28f, 165.0f, 3.5f, 0.9f);
        return 5;
    }
};

class GrandGoule : public Enemy {
public:
    GrandGoule() : Enemy(320, 160, 75, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "GRAND'GOULE"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.3f, 190.0f, 4.0f, 1.3f);
            out[5] = mk(a + PI/2.0f, 150.0f, 3.5f, 0.9f);
            out[6] = mk(a - PI/2.0f, 150.0f, 3.5f, 0.9f);
            return 7;
        }
        out[0] = mk(a,           175.0f, 4.0f, 1.2f);
        out[1] = mk(a + PI/2.0f, 130.0f, 3.5f, 0.8f);
        out[2] = mk(a - PI/2.0f, 130.0f, 3.5f, 0.8f);
        return 3;
    }
};

class Paoxiao : public Enemy {
public:
    Paoxiao() : Enemy(320, 160, 82, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "PAOXIAO"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.28f, 180.0f, 4.0f, 1.1f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.32f, 160.0f, 4.0f, 1.0f);
        return 5;
    }
};

class Ebigane : public Enemy {
public:
    Ebigane() : Enemy(320, 160, 90, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "EBIGANE"; }
    float       fire_interval() const override { return ENRAGED ? 1.8f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 4; i++)
                out[i] = mk(i * PI/2.0f, 90.0f, 7.0f, 2.2f);
            out[4] = mk(a,         140.0f, 5.5f, 2.8f);
            out[5] = mk(a + 0.4f,  110.0f, 4.5f, 2.0f);
            out[6] = mk(a - 0.4f,  110.0f, 4.5f, 2.0f);
            return 7;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 80.0f, 7.0f, 2.0f);
        out[4] = mk(a, 120.0f, 5.0f, 2.5f);
        return 5;
    }
};

class BeastOfTheCharredForests : public Enemy {
public:
    BeastOfTheCharredForests() : Enemy(320, 160, 100, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "BEAST OF THE CHARRED FORESTS"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         145.0f, 6.5f, 3.2f);
            out[1] = mk(a + 0.45f, 120.0f, 5.5f, 2.3f);
            out[2] = mk(a - 0.45f, 120.0f, 5.5f, 2.3f);
            for (int i = 0; i < 6; i++)
                out[i+3] = mk(i * TAU/6.0f, 70.0f, 4.5f, 1.4f);
            return 9;
        }
        out[0] = mk(a,         130.0f, 6.0f, 2.8f);
        out[1] = mk(a + 0.45f, 110.0f, 5.0f, 2.0f);
        out[2] = mk(a - 0.45f, 110.0f, 5.0f, 2.0f);
        return 3;
    }
};

// ── Snow enemies (IDs 14–20) ──────────────────────────────────────────────────

class Lodsilungur : public Enemy {
public:
    Lodsilungur() : Enemy(320, 160, 80, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "LODSILUNGUR"; }
    float       fire_interval() const override { return ENRAGED ? 0.15f : 0.3f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.22f, 250.0f, 3.0f, 0.7f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.25f, 220.0f, 3.0f, 0.6f);
        return 3;
    }
};

class Ofuguggi : public Enemy {
public:
    Ofuguggi() : Enemy(320, 160, 90, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OFUGUGGI"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,           190.0f, 4.0f, 1.3f);
            out[1] = mk(a + PI,      150.0f, 4.0f, 1.0f);
            out[2] = mk(a + PI/2.0f, 130.0f, 3.5f, 0.9f);
            out[3] = mk(a - PI/2.0f, 130.0f, 3.5f, 0.9f);
            return 4;
        }
        out[0] = mk(a,      170.0f, 4.0f, 1.1f);
        out[1] = mk(a + PI, 130.0f, 4.0f, 0.9f);
        return 2;
    }
};

class Kamaitachi : public Enemy {
    float sweep = 0.0f;
public:
    Kamaitachi() : Enemy(320, 160, 98, {1.25f,0.75f,1.25f,0.75f,1.0f,1.5f,1.5f}) {}
    const char* name()          const override { return "KAMAITACHI"; }
    float       fire_interval() const override { return ENRAGED ? 0.1f : 0.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            out[0] = mk(sweep,        300.0f, 2.5f, 0.6f);
            out[1] = mk(sweep + PI,   220.0f, 2.5f, 0.5f);
            sweep += PI / 4.0f;
            return 2;
        }
        out[0] = mk(sweep, 280.0f, 2.5f, 0.5f);
        sweep += PI / 5.0f;
        return 1;
    }
};

class Qiqirn : public Enemy {
public:
    Qiqirn() : Enemy(320, 160, 115, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QIQIRN"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 205.0f, 4.0f, 1.3f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.28f, 180.0f, 4.0f, 1.1f);
        return 3;
    }
};

class Vatnaormur : public Enemy {
public:
    Vatnaormur() : Enemy(320, 160, 128, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "VATNAORMUR"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.32f, 185.0f, 3.5f, 1.3f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.35f, 160.0f, 3.5f, 1.1f);
        return 5;
    }
};

class Skeljaskrimsli : public Enemy {
    int phase = 0;
public:
    Skeljaskrimsli() : Enemy(320, 160, 140, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SKELJASKRIMSLI"; }
    float       fire_interval() const override { return ENRAGED ? 1.2f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            // shell burst + bouncing shards simultaneously
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 100.0f, 5.0f, 1.3f);
            for (int i = 0; i < 3; i++)
                out[i+8] = mkb(a + (i-1)*0.4f, 160.0f, 4.0f, 1.2f);
            return 11;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 90.0f, 5.0f, 1.2f);
            phase++; return 8;
        } else {
            // bouncing shards
            for (int i = 0; i < 3; i++)
                out[i] = mkb(a + (i-1)*0.45f, 150.0f, 4.0f, 1.1f);
            phase++; return 3;
        }
    }
};

class Sermilik : public Enemy {
public:
    Sermilik() : Enemy(320, 160, 155, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SERMILIK"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 80.0f, 6.5f, 1.9f);
            out[8]  = mk(a,         145.0f, 6.0f, 2.8f);
            out[9]  = mk(a + 0.3f,  120.0f, 5.0f, 2.2f);
            out[10] = mk(a - 0.3f,  120.0f, 5.0f, 2.2f);
            out[11] = mksp(a, 55.0f, 0.45f);
            return 12;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(i * PI/2.0f, 75.0f, 7.0f, 2.0f);
        out[4] = mk(a, 130.0f, 5.5f, 2.5f);
        out[5] = mksp(a, 50.0f, 0.5f);
        return 6;
    }
};

// ── Desert enemies (IDs 21–27) ────────────────────────────────────────────────

class Asp : public Enemy {
public:
    Asp() : Enemy(320, 160, 145, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ASP"; }
    float       fire_interval() const override { return ENRAGED ? 0.5f : 0.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a - 0.18f, 265.0f, 3.5f, 1.4f);
            out[1] = mk(a,         265.0f, 3.5f, 1.5f);
            out[2] = mk(a + 0.18f, 265.0f, 3.5f, 1.4f);
            return 3;
        }
        out[0] = mk(a - 0.12f, 240.0f, 3.5f, 1.2f);
        out[1] = mk(a + 0.12f, 240.0f, 3.5f, 1.2f);
        return 2;
    }
};

class CactusCat : public Enemy {
public:
    CactusCat() : Enemy(320, 160, 155, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "CACTUS CAT"; }
    float       fire_interval() const override { return ENRAGED ? 0.7f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a, 200.0f, 4.5f, 1.5f);
            for (int i = 0; i < 8; i++)
                out[i+1] = mk(i * TAU/8.0f, 120.0f, 3.0f, 0.9f);
            return 9;
        }
        out[0] = mk(a, 180.0f, 4.0f, 1.3f);
        for (int i = 0; i < 4; i++)
            out[i+1] = mk(a + (i+1) * PI/2.0f, 110.0f, 3.0f, 0.8f);
        return 5;
    }
};

class OlgoiKhorkhoi : public Enemy {
public:
    OlgoiKhorkhoi() : Enemy(320, 160, 165, {0.4f,1.0f,0.4f,0.75f,1.0f,1.0f,1.5f}) {}
    const char* name()          const override { return "OLGOI-KHORKHOI"; }
    float       fire_interval() const override { return ENRAGED ? 1.4f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            float off = ernd() * TAU;
            for (int i = 0; i < 16; i++)
                out[i] = mk(off + i * TAU/16.0f, 115.0f, 4.5f, 1.4f);
            return 16;
        }
        float off = ernd() * TAU;
        for (int i = 0; i < 10; i++)
            out[i] = mk(off + i * TAU/10.0f, 95.0f, 4.5f, 1.2f);
        return 10;
    }
};

class Zoureg : public Enemy {
public:
    Zoureg() : Enemy(320, 160, 175, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ZOUREG"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.35f, 195.0f, 3.5f, 1.3f);
            out[7] = mk(a, 280.0f, 3.5f, 1.6f);
            return 8;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.38f, 170.0f, 3.5f, 1.1f);
        return 5;
    }
};

class Myrmecoleon : public Enemy {
    float ring_rot = 0.0f;
public:
    Myrmecoleon() : Enemy(320, 160, 190, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "MYRMECOLEON"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         220.0f, 4.5f, 1.7f);
            out[1] = mk(a - 0.2f,  200.0f, 4.0f, 1.4f);
            out[2] = mk(a + 0.2f,  200.0f, 4.0f, 1.4f);
            for (int i = 0; i < 8; i++)
                out[i+3] = mk(ring_rot + i * TAU/8.0f, 100.0f, 3.5f, 1.0f);
            ring_rot += PI / 8.0f;
            return 11;
        }
        out[0] = mk(a, 200.0f, 4.0f, 1.4f);
        for (int i = 0; i < 6; i++)
            out[i+1] = mk(ring_rot + i * TAU/6.0f, 85.0f, 3.5f, 0.9f);
        ring_rot += PI / 6.0f;
        return 7;
    }
};

class Akhekh : public Enemy {
public:
    Akhekh() : Enemy(320, 160, 205, {0.5f,0.5f,0.75f,0.5f,1.5f,1.0f,1.5f}) {}
    const char* name()          const override { return "AKHEKH"; }
    float       fire_interval() const override { return ENRAGED ? 0.45f : 0.7f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,           275.0f, 3.5f, 1.5f);
            out[1] = mk(a - 0.3f,    250.0f, 3.0f, 1.2f);
            out[2] = mk(a + 0.3f,    250.0f, 3.0f, 1.2f);
            out[3] = mk(a + PI/2.0f, 200.0f, 3.0f, 1.0f);
            out[4] = mk(a - PI/2.0f, 200.0f, 3.0f, 1.0f);
            return 5;
        }
        out[0] = mk(a,         250.0f, 3.5f, 1.3f);
        out[1] = mk(a - 0.3f, 230.0f, 3.0f, 1.1f);
        out[2] = mk(a + 0.3f, 230.0f, 3.0f, 1.1f);
        return 3;
    }
};

class Grootslang : public Enemy {
public:
    Grootslang() : Enemy(320, 160, 220, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "GROOTSLANG"; }
    float       fire_interval() const override { return ENRAGED ? 1.6f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         125.0f, 8.5f, 4.0f);
            out[1] = mk(a + 0.5f,  100.0f, 6.5f, 2.8f);
            out[2] = mk(a - 0.5f,  100.0f, 6.5f, 2.8f);
            for (int i = 0; i < 4; i++)
                out[i+3] = mk(i * PI/2.0f, 75.0f, 5.5f, 1.8f);
            return 7;
        }
        out[0] = mk(a,         110.0f, 8.0f, 3.5f);
        out[1] = mk(a + 0.5f,  90.0f, 6.0f, 2.5f);
        out[2] = mk(a - 0.5f,  90.0f, 6.0f, 2.5f);
        return 3;
    }
};

// ── Wasteland enemies (IDs 28–34) ─────────────────────────────────────────────

class Opimachus : public Enemy {
public:
    Opimachus() : Enemy(320, 160, 210, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OPIMACHUS"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.3f, 200.0f, 4.0f, 1.5f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.32f, 175.0f, 4.0f, 1.3f);
        return 5;
    }
};

class Karnabo : public Enemy {
    int phase = 0;
public:
    Karnabo() : Enemy(320, 160, 225, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "KARNABO"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            // curse ring + bouncing aimed bolts simultaneously
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 110.0f, 3.5f, 1.0f);
            for (int i = 0; i < 3; i++)
                out[i+12] = mkb(a + (i-1)*0.25f, 200.0f, 3.5f, 1.5f);
            return 15;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 100.0f, 3.5f, 0.9f);
            phase++; return 12;
        } else {
            // bouncing curse bolts
            for (int i = 0; i < 3; i++)
                out[i] = mkb(a + (i-1)*0.25f, 190.0f, 3.5f, 1.3f);
            phase++; return 3;
        }
    }
};

class Dajna : public Enemy {
    float rot = 0.0f;
public:
    Dajna() : Enemy(320, 171, 238, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "DAJNA"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i]   = mk(rot       + i * TAU/8.0f, 105.0f, 3.5f, 1.0f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mk(rot + PI/8.0f + i * TAU/8.0f, 80.0f, 3.0f, 0.8f);
            out[16] = mk(a,         230.0f, 4.5f, 1.8f);
            out[17] = mk(a + 0.2f,  200.0f, 4.0f, 1.5f);
            rot += PI / 8.0f;
            return 18;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(rot + i * TAU/8.0f, 95.0f, 3.5f, 0.9f);
        out[8] = mk(a, 210.0f, 4.5f, 1.6f);
        rot += PI / 8.0f;
        return 9;
    }
};

class ManEatingBoulder : public Enemy {
public:
    ManEatingBoulder() : Enemy(320, 160, 258, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "MAN-EATING BOULDER"; }
    float       fire_interval() const override { return ENRAGED ? 1.6f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // rock fragments — inner ring bounces
            for (int i = 0; i < 8; i++)
                out[i]   = mk(i * TAU/8.0f,            80.0f, 7.0f, 2.5f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mkb(PI/8.0f + i * TAU/8.0f, 70.0f, 5.0f, 1.8f);
            return 16;
        }
        for (int i = 0; i < 4; i++)
            out[i]   = mk(i * PI/2.0f,            70.0f, 7.0f, 2.2f);
        for (int i = 0; i < 4; i++)
            out[i+4] = mkb(PI/4.0f + i * PI/2.0f, 60.0f, 5.0f, 1.6f);
        return 8;
    }
};

class Angont : public Enemy {
public:
    Angont() : Enemy(320, 160, 272, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ANGONT"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 9; i++)
                out[i] = mk(a + (i-4)*0.28f, 195.0f, 4.0f, 1.5f);
            out[9]  = mk(a,         270.0f, 4.5f, 2.0f);
            return 10;
        }
        for (int i = 0; i < 7; i++)
            out[i] = mk(a + (i-3)*0.3f, 170.0f, 4.0f, 1.3f);
        return 7;
    }
};

class TsenaGahi : public Enemy {
    float spin = 0.0f;
public:
    TsenaGahi() : Enemy(320, 160, 285, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "TSE'NAGAHI"; }
    float       fire_interval() const override { return ENRAGED ? 1.2f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // rolling stone — half the shots bounce
            for (int i = 0; i < 8; i++)
                out[i]   = mk(spin + i * TAU/8.0f,              105.0f, 6.0f, 2.2f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mkb(spin + PI/8.0f + i * TAU/8.0f,   90.0f, 5.0f, 1.8f);
            spin += PI / 16.0f;
            return 16;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(spin + i * TAU/8.0f, 90.0f, 6.0f, 2.0f);
        spin += PI / 8.0f;
        return 8;
    }
};

class Anaye : public Enemy {
public:
    Anaye() : Enemy(320, 160, 300, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "ANAYE"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 12; i++)
                out[i] = mk(i * TAU/12.0f, 95.0f, 6.0f, 2.0f);
            out[12] = mk(a,         165.0f, 7.5f, 3.5f);
            out[13] = mk(a + 0.35f, 135.0f, 6.0f, 2.5f);
            out[14] = mk(a - 0.35f, 135.0f, 6.0f, 2.5f);
            out[15] = mk(a + 0.7f,  110.0f, 5.0f, 2.0f);
            out[16] = mk(a - 0.7f,  110.0f, 5.0f, 2.0f);
            return 17;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(i * TAU/8.0f, 85.0f, 6.0f, 1.8f);
        out[8]  = mk(a,         150.0f, 7.0f, 3.0f);
        out[9]  = mk(a + 0.4f,  120.0f, 5.0f, 2.2f);
        out[10] = mk(a - 0.4f,  120.0f, 5.0f, 2.2f);
        out[11] = mksp(a + PI/4.0f, 45.0f, 0.5f);
        out[12] = mksp(a - PI/4.0f, 45.0f, 0.5f);
        return 13;
    }
};

// ── Mountains enemies (IDs 35–41) ─────────────────────────────────────────────

class Lomie : public Enemy {
public:
    Lomie() : Enemy(320, 160, 290, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "LOMIE"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.28f, 210.0f, 4.0f, 1.8f);
            return 5;
        }
        for (int i = 0; i < 3; i++)
            out[i] = mk(a + (i-1)*0.28f, 185.0f, 4.0f, 1.5f);
        return 3;
    }
};

class CuSith : public Enemy {
public:
    CuSith() : Enemy(320, 160, 310, {1.0f,1.0f,1.0f,1.25f,1.0f,1.5f,1.25f}) {}
    const char* name()          const override { return "CU SITH"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 6; i++)
                out[i] = mk(a + (i-2.5f)*0.28f, 215.0f, 4.0f, 1.8f);
            return 6;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(a + (i-1.5f)*0.25f, 190.0f, 4.0f, 1.5f);
        return 4;
    }
};

class CelestialStag : public Enemy {
public:
    CelestialStag() : Enemy(320, 160, 325, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "CELESTIAL STAG"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 4; i++)
                out[i] = mk(a + (i-1.5f)*0.3f, 205.0f, 4.0f, 1.7f);
            out[4] = mk(a + PI/2.0f, 160.0f, 3.5f, 1.2f);
            out[5] = mk(a - PI/2.0f, 160.0f, 3.5f, 1.2f);
            for (int i = 0; i < 6; i++)
                out[i+6] = mk(i * TAU/6.0f, 80.0f, 4.0f, 1.2f);
            return 12;
        }
        for (int i = 0; i < 4; i++)
            out[i] = mk(a + (i-1.5f)*0.3f, 185.0f, 4.0f, 1.5f);
        out[4] = mk(a + PI/2.0f, 140.0f, 3.5f, 1.0f);
        out[5] = mk(a - PI/2.0f, 140.0f, 3.5f, 1.0f);
        return 6;
    }
};

class Igtuk : public Enemy {
    int phase = 0;
public:
    Igtuk() : Enemy(320, 160, 340, {0.5f,0.5f,0.5f,0.5f,0.75f,1.0f,0.75f}) {}
    const char* name()          const override { return "IGTUK"; }
    float       fire_interval() const override { return ENRAGED ? 0.65f : 1.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // phase shot + bouncing ghost projectiles simultaneously
            out[0] = mk(aim_at(x,y,px,py), 220.0f, 4.5f, 2.0f);
            for (int i = 0; i < 6; i++)
                out[i+1] = mkb(ernd() * TAU, 140.0f, 3.5f, 1.1f);
            return 7;
        }
        if (phase % 2 == 0) {
            out[0] = mk(aim_at(x,y,px,py), 200.0f, 4.0f, 1.6f);
            phase++; return 1;
        } else {
            // ghost shots bounce around the arena
            for (int i = 0; i < 6; i++)
                out[i] = mkb(ernd() * TAU, 120.0f, 3.5f, 0.9f);
            phase++; return 6;
        }
    }
};

class Ajaju : public Enemy {
    float coil = 0.0f;
public:
    Ajaju() : Enemy(320, 160, 360, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "AJAJU"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         220.0f, 5.0f, 2.2f);
            out[1] = mk(a + 0.25f, 200.0f, 4.5f, 1.9f);
            out[2] = mk(a - 0.25f, 200.0f, 4.5f, 1.9f);
            for (int i = 0; i < 8; i++)
                out[i+3] = mk(coil + i * TAU/8.0f, 115.0f, 3.5f, 1.1f);
            coil += PI / 8.0f;
            return 11;
        }
        out[0] = mk(a, 200.0f, 4.5f, 1.8f);
        for (int i = 0; i < 5; i++)
            out[i+1] = mk(coil + i * TAU/5.0f, 100.0f, 3.5f, 1.0f);
        coil += PI / 5.0f;
        return 6;
    }
};

class SlideRockBolter : public Enemy {
public:
    SlideRockBolter() : Enemy(320, 160, 380, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SLIDE-ROCK BOLTER"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 2.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 5; i++)
                out[i] = mk(a + (i-2)*0.35f, 165.0f, 6.5f, 3.0f);
            out[5] = mk(a + PI/2.0f, 130.0f, 5.0f, 2.0f);
            out[6] = mk(a - PI/2.0f, 130.0f, 5.0f, 2.0f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.35f, 140.0f, 6.0f, 2.5f);
        return 5;
    }
};

class Sasnalkahi : public Enemy {
public:
    Sasnalkahi() : Enemy(320, 160, 400, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SASNALKAHI"; }
    float       fire_interval() const override { return ENRAGED ? 1.1f : 1.8f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.28f, 200.0f, 5.5f, 2.6f);
            out[7] = mksp(a, 60.0f, 0.4f);
            return 8;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.3f, 175.0f, 5.5f, 2.2f);
        out[5] = mksp(a, 55.0f, 0.5f);
        return 6;
    }
};

// ── Ocean enemies (IDs 42–49) ─────────────────────────────────────────────────

class Nykur : public Enemy {
public:
    Nykur() : Enemy(320, 160, 380, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "NYKUR"; }
    float       fire_interval() const override { return ENRAGED ? 0.8f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 7; i++)
                out[i] = mk(a + (i-3)*0.3f, 215.0f, 4.5f, 2.1f);
            return 7;
        }
        for (int i = 0; i < 5; i++)
            out[i] = mk(a + (i-2)*0.3f, 190.0f, 4.5f, 1.8f);
        return 5;
    }
};

class SazaeOni : public Enemy {
    float spiral = 0.0f;
public:
    SazaeOni() : Enemy(320, 160, 415, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SAZAE-ONI"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) {
            // shell shards — all bouncing
            for (int i = 0; i < 12; i++)
                out[i] = mkb(spiral + i * TAU/12.0f, 130.0f, 5.0f, 2.0f);
            spiral += PI / 12.0f;
            return 12;
        }
        // alternating: normal then bouncing spiral
        for (int i = 0; i < 3; i++)
            out[i]   = mk(spiral + i * TAU/3.0f,            100.0f, 6.0f, 2.0f);
        for (int i = 0; i < 3; i++)
            out[i+3] = mkb(spiral + PI/3.0f + i * TAU/3.0f, 90.0f, 5.0f, 1.6f);
        spiral += PI / 6.0f;
        return 6;
    }
};

class Itqiirpak : public Enemy {
    int phase = 0;
public:
    Itqiirpak() : Enemy(320, 160, 445, {1.25f,1.5f,2.0f,0.75f,0.75f,1.5f,1.0f}) {}
    const char* name()          const override { return "ITQIIRPAK"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 10; i++)
                out[i] = mk(i * TAU/10.0f, 120.0f, 4.0f, 1.5f);
            for (int i = 0; i < 5; i++)
                out[i+10] = mk(a + (i-2)*0.22f, 240.0f, 4.5f, 2.3f);
            return 15;
        }
        if (phase % 2 == 0) {
            for (int i = 0; i < 10; i++)
                out[i] = mk(i * TAU/10.0f, 110.0f, 4.0f, 1.3f);
            phase++; return 10;
        } else {
            for (int i = 0; i < 4; i++)
                out[i] = mk(a + (i-1.5f)*0.22f, 220.0f, 4.5f, 2.0f);
            phase++; return 4;
        }
    }
};

class KusaKap : public Enemy {
public:
    KusaKap() : Enemy(320, 160, 475, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "KUSA KAP"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(a + (i-3.5f)*0.3f, 190.0f, 4.5f, 2.2f);
            for (int i = 0; i < 8; i++)
                out[i+8] = mk(i * TAU/8.0f, 85.0f, 4.0f, 1.4f);
            return 16;
        }
        for (int i = 0; i < 8; i++)
            out[i] = mk(a + (i-3.5f)*0.3f, 165.0f, 4.5f, 1.9f);
        return 8;
    }
};

class Lusca : public Enemy {
    float tentrot = 0.0f;
public:
    Lusca() : Enemy(320, 160, 515, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "LUSCA"; }
    float       fire_interval() const override { return ENRAGED ? 1.0f : 1.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            out[0] = mk(a,         235.0f, 5.5f, 2.8f);
            out[1] = mk(a + 0.3f,  205.0f, 5.0f, 2.3f);
            out[2] = mk(a - 0.3f,  205.0f, 5.0f, 2.3f);
            out[3] = mk(a + 0.6f,  175.0f, 4.5f, 1.9f);
            out[4] = mk(a - 0.6f,  175.0f, 4.5f, 1.9f);
            for (int i = 0; i < 8; i++)
                out[i+5] = mk(tentrot + i * TAU/8.0f, 105.0f, 4.0f, 1.4f);
            tentrot += PI / 8.0f;
            return 13;
        }
        out[0] = mk(a,         210.0f, 5.0f, 2.2f);
        out[1] = mk(a + 0.35f, 180.0f, 4.5f, 1.8f);
        out[2] = mk(a - 0.35f, 180.0f, 4.5f, 1.8f);
        for (int i = 0; i < 5; i++)
            out[i+3] = mk(tentrot + i * TAU/5.0f, 90.0f, 4.0f, 1.2f);
        tentrot += PI / 5.0f;
        return 8;
    }
};

class MohaMoha : public Enemy {
public:
    MohaMoha() : Enemy(320, 160, 555, {0.5f,1.5f,0.5f,1.5f,1.5f,0.75f,1.0f}) {}
    const char* name()          const override { return "MOHA-MOHA"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++)
                out[i] = mk(i * TAU/8.0f, 90.0f, 7.5f, 2.8f);
            out[8]  = mk(a,         180.0f, 7.0f, 4.0f);
            out[9]  = mk(a + 0.4f,  150.0f, 6.0f, 3.2f);
            out[10] = mk(a - 0.4f,  150.0f, 6.0f, 3.2f);
            out[11] = mk(a + 0.8f,  120.0f, 5.0f, 2.5f);
            out[12] = mk(a - 0.8f,  120.0f, 5.0f, 2.5f);
            return 13;
        }
        for (int i = 0; i < 6; i++)
            out[i] = mk(i * TAU/6.0f, 80.0f, 7.5f, 2.5f);
        out[6] = mk(a,         160.0f, 6.5f, 3.5f);
        out[7] = mk(a + 0.5f,  130.0f, 5.5f, 2.8f);
        out[8] = mk(a - 0.5f,  130.0f, 5.5f, 2.8f);
        return 9;
    }
};

class Bjarndyrakongur : public Enemy {
public:
    Bjarndyrakongur() : Enemy(320, 160, 595, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "BJARNDYRAKONGUR"; }
    float       fire_interval() const override { return ENRAGED ? 2.0f : 3.0f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 8; i++) {
                float ang = i * TAU/8.0f;
                out[i]   = mk(ang,             110.0f, 5.5f, 2.3f);
                out[i+8] = mk(ang + PI/8.0f,    75.0f, 6.5f, 2.8f);
            }
            out[16] = mk(a,         200.0f, 7.5f, 4.5f);
            out[17] = mk(a + 0.25f, 170.0f, 6.5f, 3.5f);
            out[18] = mk(a - 0.25f, 170.0f, 6.5f, 3.5f);
            out[19] = mksp(a, 50.0f, 0.4f);
            return 20;
        }
        for (int i = 0; i < 8; i++) {
            float ang = i * TAU/8.0f;
            out[i]   = mk(ang,           95.0f, 5.5f, 2.0f);
            out[i+8] = mk(ang + PI/8.0f, 60.0f, 6.5f, 2.5f);
        }
        out[16] = mk(a, 180.0f, 7.0f, 4.0f);
        out[17] = mksp(a, 45.0f, 0.5f);
        return 18;
    }
};

class Physeter : public Enemy {
public:
    // TESTING: a million HP, a punching bag for weapon tests. Was 650.
    Physeter() : Enemy(320, 171, 1000000, {0.75f,0.75f,1.0f,1.0f,1.5f,1.25f,1.25f}) {}
    const char* name()          const override { return "PHYSETER"; }
    float       fire_interval() const override { return ENRAGED ? 1.7f : 2.5f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) {
            for (int i = 0; i < 16; i++)
                out[i] = mk(i * TAU/16.0f, 120.0f, 5.5f, 2.5f);
            for (int i = 0; i < 7; i++)
                out[i+16] = mk(a + (i-3)*0.28f, 220.0f, 5.0f, 3.0f);
            out[23] = mksp(a,           40.0f, 0.35f);
            out[24] = mksp(a + PI/2.0f, 35.0f, 0.4f);
            out[25] = mksp(a - PI/2.0f, 35.0f, 0.4f);
            return 26;
        }
        for (int i = 0; i < 16; i++)
            out[i] = mk(i * TAU/16.0f, 105.0f, 5.0f, 2.0f);
        for (int i = 0; i < 5; i++)
            out[i+16] = mk(a + (i-2)*0.3f, 200.0f, 5.0f, 2.5f);
        out[21] = mksp(a, 40.0f, 0.4f);
        return 22;
    }
};

// ── Factory ───────────────────────────────────────────────────────────────────

Enemy* enemy_create(int id) {
    switch (id) {
        case  0: return new Skvader();
        case  1: return new Wolpertinger();
        case  2: return new Treesqueak();
        case  3: return new Qique();
        case  4: return new Lili();
        case  5: return new CrowingCrestedCobra();
        case  6: return new WakmangganchiAragondi();
        case  7: return new Alber();
        case  8: return new Snawfus();
        case  9: return new QuestingBeast();
        case 10: return new GrandGoule();
        case 11: return new Paoxiao();
        case 12: return new Ebigane();
        case 13: return new BeastOfTheCharredForests();
        case 14: return new Lodsilungur();
        case 15: return new Ofuguggi();
        case 16: return new Kamaitachi();
        case 17: return new Qiqirn();
        case 18: return new Vatnaormur();
        case 19: return new Skeljaskrimsli();
        case 20: return new Sermilik();
        case 21: return new Asp();
        case 22: return new CactusCat();
        case 23: return new OlgoiKhorkhoi();
        case 24: return new Zoureg();
        case 25: return new Myrmecoleon();
        case 26: return new Akhekh();
        case 27: return new Grootslang();
        case 28: return new Opimachus();
        case 29: return new Karnabo();
        case 30: return new Dajna();
        case 31: return new ManEatingBoulder();
        case 32: return new Angont();
        case 33: return new TsenaGahi();
        case 34: return new Anaye();
        case 35: return new Lomie();
        case 36: return new CuSith();
        case 37: return new CelestialStag();
        case 38: return new Igtuk();
        case 39: return new Ajaju();
        case 40: return new SlideRockBolter();
        case 41: return new Sasnalkahi();
        case 42: return new Nykur();
        case 43: return new SazaeOni();
        case 44: return new Itqiirpak();
        case 45: return new KusaKap();
        case 46: return new Lusca();
        case 47: return new MohaMoha();
        case 48: return new Bjarndyrakongur();
        case 49: return new Physeter();
        default: return new Skvader();
    }
}

// What each enemy drops, by id: fur and feather give hide, shell, scale and
// stone give bone, spirits and omens give essence. The Treesqueak, a tree
// creature met on the starting island, gives vine -- the lashing for the raft
// that is the way off it.
static const MonsterPart ENEMY_PARTS[] = {
    PART_HIDE,    PART_HIDE,    PART_VINE,    PART_HIDE,    PART_HIDE,      //  0-4
    PART_BONE,    PART_HIDE,    PART_ESSENCE, PART_HIDE,    PART_BONE,      //  5-9
    PART_BONE,    PART_HIDE,    PART_BONE,    PART_HIDE,    PART_BONE,      // 10-14
    PART_BONE,    PART_ESSENCE, PART_ESSENCE, PART_BONE,    PART_BONE,      // 15-19
    PART_HIDE,    PART_BONE,    PART_HIDE,    PART_BONE,    PART_BONE,      // 20-24
    PART_BONE,    PART_ESSENCE, PART_BONE,    PART_HIDE,    PART_HIDE,      // 25-29
    PART_ESSENCE, PART_BONE,    PART_BONE,    PART_HIDE,    PART_ESSENCE,   // 30-34
    PART_ESSENCE, PART_HIDE,    PART_ESSENCE, PART_ESSENCE, PART_HIDE,      // 35-39
    PART_BONE,    PART_BONE,    PART_ESSENCE, PART_BONE,    PART_HIDE,      // 40-44
    PART_ESSENCE, PART_BONE,    PART_BONE,    PART_HIDE,    PART_BONE,      // 45-49
};

// Each enemy's bullet colour, picked from its art and brightened to an exact
// palette entry that stands off the black. Ids past the table get pink until
// their round.
static const Uint8 ENEMY_BULLET_RGB[][3] = {
    { 252, 152,  56 },   //  0 Skvader: orange, its gold-brown fur brightened
    { 236, 132, 118 },   //  1 Wolpertinger: salmon, its red wings
    {  78, 220,  74 },   //  2 Treesqueak: green, its leaf marks
    { 182, 156, 238 },   //  3 Qique: lavender, its dark purple plumage
};

SDL_Color enemy_bullet_color(int id) {
    if (id < 0 || id >= (int)(sizeof(ENEMY_BULLET_RGB) / sizeof(ENEMY_BULLET_RGB[0])))
        return { 252, 116, 180, 255 };
    return { ENEMY_BULLET_RGB[id][0], ENEMY_BULLET_RGB[id][1], ENEMY_BULLET_RGB[id][2], 255 };
}

MonsterPart enemy_part(int id) {
    if (id < 0 || id >= (int)(sizeof(ENEMY_PARTS) / sizeof(ENEMY_PARTS[0]))) return PART_HIDE;
    return ENEMY_PARTS[id];
}
