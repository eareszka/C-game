#include "enemy.h"
#include "battle.h"   // ARENA_W/H/TOP: Grand'Goule's breath reaches the edge
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

// A SCRATCH out of (cx, cy) along `a`: four parallel claw streaks 7 px
// apart, three shots long, flying together at `speed`, curving at `curve`
// rad/s (0 = straight). 12 shots.
static int scratch_shots(float cx, float cy, float a, float speed, float curve, BulletSpawn out[]) {
    float ux = cosf(a), uy = sinf(a), vx = -uy, vy = ux;
    int n = 0;
    for (int c = 0; c < 4; c++)
        for (int k = 0; k < 3; k++) {
            float side = (c - 1.5f) * 7.0f, back = k * 7.0f;
            BulletSpawn b = mk(a, speed, 2.5f, 5.0f);
            b.from = true; b.ox = cx + vx * side - ux * back; b.oy = cy + vy * side - uy * back;
            b.orbit_w = curve;
            out[n++] = b;
        }
    return n;
}

// A SHAPE: shots at (sx[i], sy[i]) round its middle, all leaving one point
// (ox, oy) and easing out to their places in form_t s, the whole shape
// turning at `spin` and flying along `a` at `speed`. m shots.
static int shape_shots(float ox, float oy, float a, float speed, float spin, float form_t,
                       const float* sx, const float* sy, int m, BulletSpawn out[]) {
    for (int i = 0; i < m; i++) {
        float r = hypotf(sx[i], sy[i]), v0 = 2.0f * r / form_t;
        BulletSpawn b = mk(atan2f(sy[i], sx[i]) + a, v0, 3.0f, 5.0f);
        b.from = true; b.ox = ox; b.oy = oy;
        b.accel = -v0 / form_t; b.min_speed = 0.5f;
        b.orbit_w = spin; b.orbit_vx = cosf(a) * speed; b.orbit_vy = sinf(a) * speed;
        out[i] = b;
    }
    return m;
}

// A facing as its index in the sheets' order: D DR R UR U UL L DL -- for a
// table of a part's spot in each view.
static int face8(int f) {
    return f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
         : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
}

// A diamond outline for shape_shots: 16 spots, 4 corners and 3 along each
// side, r tall and 0.7 r wide (the Grootslang's gems, the Nanabolele's scales).
static const int GEM_SPOTS = 16;
static void gem_points(float r, float sx[GEM_SPOTS], float sy[GEM_SPOTS]) {
    const float CX[4] = { 0, r * 0.7f, 0, -r * 0.7f }, CY[4] = { -r, 0, r, 0 };   // taller than wide
    for (int c = 0; c < 4; c++)
        for (int k = 0; k < 4; k++) {
            float f = k / 4.0f;
            sx[c * 4 + k] = CX[c] + (CX[(c + 1) & 3] - CX[c]) * f;
            sy[c * 4 + k] = CY[c] + (CY[(c + 1) & 3] - CY[c]) * f;
        }
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
#define ENRAGED (hp < max_hp * phase2_at())

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

// Round, pink, many-legged scuttler. Everything it fires is aimed at the
// player; what changes is where from.
// Phase 1, Scuttle: it scuttles side to side across the top, firing a
//   3-bullet fan at the player every half second, so the angle keeps shifting.
// Phase 2 (half HP), Pinch: it scuttles up and down instead, and every few
//   volleys it stops to pinch: pairs of bullets either side of the player
//   that close in, shot by shot, like a pair of claws -- get out before
//   they meet.
class Lili : public Enemy {
    int   dir   = 1;       // scuttling right/down (1) or left/up (-1)
    int   shot  = 0;       // rain volleys so far
    int   pinch = -1;      // pair of the pinch being fired; -1 = scuttling
    float lock  = 0.0f;    // the pinch's aim, set when it starts
public:
    Lili() : Enemy(320, 160, 400, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "LILI"; }
    float fire_interval() const override {
        if (pinch >= 0) return 0.1f;
        return ENRAGED ? 0.4f : 0.5f;
    }
    void update(float dt, float, float) override {
        if (pinch >= 0) return;   // still while pinching
        if (!ENRAGED) {           // side to side across the top
            x += dir * 100.0f * dt;
            if (x < 140.0f) { x = 140.0f; dir =  1; }
            if (x > 500.0f) { x = 500.0f; dir = -1; }
        } else {                  // up and down, wherever phase 1 left it
            y += dir * 110.0f * dt;
            if (y <  90.0f) { y =  90.0f; dir =  1; }
            if (y > 250.0f) { y = 250.0f; dir = -1; }
        }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (pinch < 0 && ENRAGED && ++shot % 6 == 0) { pinch = 0; lock = a; }
        if (pinch >= 0) {
            // 8 pairs, from 0.75 either side of the aim down to 0.05.
            float off = 0.05f + 0.70f * (1.0f - pinch / 7.0f);
            out[0] = mk(lock - off, 200.0f, 2.5f, 5.0f);
            out[1] = mk(lock + off, 200.0f, 2.5f, 5.0f);
            if (++pinch == 8) pinch = -1;
            return 2;
        }
        for (int i = -1; i <= 1; i++)
            out[i + 1] = mk(a + i * 0.25f, 150.0f, 2.5f, 5.0f);
        return 3;
    }
};

// Coiled, crested snake that crows. Venom sprays, its crow is a sound ring.
// Phase 1, Spray & Crow: coiled where it is, it sprays venom at the player
//   -- 5 drops scattered round the aim at mixed speeds, so no two volleys
//   look alike -- and every fourth volley it crows: two rings at once, the
//   outer fast, the inner slow and half a step round, so the gaps of one are
//   covered by the other until they part.
// Phase 2 (half HP), Slither: it uncoils and hunts the player across the
//   arena, turning after them like a snake rather than on the spot; its body
//   hurts to touch (contact_damage), so the player has to keep running, and
//   it still spits a short spray as it comes.
class CrowingCrestedCobra : public Enemy {
    static constexpr float SLITHER_SPEED = 120.0f;   // under the player's walk (160): it can be outrun
    static constexpr float TURN          = 2.2f;     // radians a second it can turn
    float heading = PI / 2.0f;   // the way it slithers
    float t       = 0.0f;        // slither clock, for the sprite's wave
    int   shot    = 0;

    static int spray(float a, int n, float spread, float lo, float hi, BulletSpawn out[]) {
        for (int i = 0; i < n; i++)
            out[i] = mk(a + (ernd() - 0.5f) * spread, lo + ernd() * (hi - lo), 2.5f, 5.0f);
        return n;
    }
    static int crow_rings(BulletSpawn out[]) {
        float base = ernd() * TAU;
        for (int i = 0; i < 16; i++) out[i]      = mk(base + i * (TAU / 16.0f), 130.0f, 2.5f, 5.0f);
        for (int i = 0; i < 16; i++) out[16 + i] = mk(base + (i + 0.5f) * (TAU / 16.0f), 85.0f, 2.5f, 5.0f);
        return 32;
    }
public:
    CrowingCrestedCobra() : Enemy(320, 150, 440, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()           const override { return "CROWING CRESTED COBRA"; }
    float       fire_interval()  const override { return ENRAGED ? 0.9f : 0.6f; }
    float       contact_damage() const override { return ENRAGED ? 5.0f : 0.0f; }
    // The slither sheet (EnemySheet::flap), a wave every 0.6 s, while it hunts.
    float flap_phase() const override { return ENRAGED ? fmodf(t / 0.6f, 1.0f) : -1.0f; }
    void update(float dt, float px, float py) override {
        if (!ENRAGED) return;     // phase 1: coiled, still
        t += dt;
        // Turn toward the player, no faster than TURN.
        float want = aim_at(x, y, px, py);
        float d = fmodf(want - heading + 3.0f * PI, TAU) - PI;
        float step = TURN * dt;
        heading += d > step ? step : d < -step ? -step : d;
        x += cosf(heading) * SLITHER_SPEED * dt;
        y += sinf(heading) * SLITHER_SPEED * dt;
        // Inside the arena (640x480, the HUD above y 28).
        if (x <  30.0f) x =  30.0f;
        if (x > 610.0f) x = 610.0f;
        if (y <  60.0f) y =  60.0f;
        if (y > 450.0f) y = 450.0f;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (ENRAGED) return spray(a, 3, 0.5f, 150.0f, 210.0f, out);
        if (++shot % 4 == 0) return crow_rings(out);
        return spray(a, 5, 0.7f, 120.0f, 200.0f, out);
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

// Great fiery dragon "glowing like an electric fire", always in flight.
// Phase 1, Fire Breath: it hovers and breathes a stream of flame that sweeps
//   across where the player was when it drew breath -- one way, then back
//   the other the next time -- the flames flickering at mixed speeds, so the
//   stream has gaps to slip through; then a breath's rest.
// Phase 2 (half HP), Electric Fire: it glides about the top of the arena,
//   breathing quicker, and at the end of every breath spits an ember that
//   drifts across and bursts into rings as it goes.
class Alber : public Enemy {
    float cyc   = 0.0f;    // seconds into the breath-and-rest cycle
    float t     = 0.0f;    // glide clock (phase 2)
    int   n     = -1;      // which cycle this is, to notice a new one
    int   dir   = 1;       // this breath sweeps clockwise (1) or back (-1)
    float lock  = 0.0f;    // aim at the player when the breath was drawn
    bool  embers = false;  // this cycle's ember spat

    float breath_t() const { return ENRAGED ? 1.1f : 1.4f; }
    float rest_t()   const { return ENRAGED ? 0.7f : 1.0f; }
    bool  breathing() const { return fmodf(cyc, breath_t() + rest_t()) < breath_t(); }
public:
    Alber() : Enemy(320, 140, 780, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "ALBER"; }
    float       fire_interval() const override { return breathing() ? 0.07f : 0.1f; }
    void update(float dt, float, float) override {
        cyc += dt;
        if (!ENRAGED) return;
        t += dt;
        x = 320.0f + 170.0f * sinf(t * 0.55f);
        y = 140.0f +  35.0f * sinf(t * 1.1f);
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        int now = (int)(cyc / (breath_t() + rest_t()));
        if (now != n) { n = now; lock = a; dir = -dir; embers = false; }
        float k = fmodf(cyc, breath_t() + rest_t());
        if (k < breath_t()) {
            // From 0.8 one side of the locked aim to 0.8 the other.
            float sweep = lock + dir * 0.8f * (2.0f * k / breath_t() - 1.0f);
            out[0] = mk(sweep + (ernd() - 0.5f) * 0.12f, 170.0f + ernd() * 70.0f, 3.0f, 5.0f);
            return 1;
        }
        if (ENRAGED && !embers) {
            embers = true;
            // One ember, a little off the aim: it crosses the arena in
            // about three seconds, two or three rings on the way.
            out[0] = mksp(a + (ernd() < 0.5f ? -0.4f : 0.4f), 120.0f, 1.2f);
            return 1;
        }
        return 0;
    }
};

// White deer with flowering boughs on its antlers.
// Phase 1, Blossom Shower: the antlers shed petals upward that arc over and
//   home down onto the player, then fly straight -- read the curves, and move
//   so they miss; every third shower adds an aimed fan, so standing still
//   doesn't work either.
// Phase 2 (two-thirds HP), Bloom: it stands its ground and throws whole blossoms
//   of bullets -- a five-petal flower outline round a ring of a centre --
//   that open as they drift toward the player, each turned a new way. The
//   player picks a gap between petals and threads it precisely.
class Snawfus : public Enemy {
    int shower = 0;   // showers shed

    // Its bloom comes early: phase 2 from two-thirds health, not half.
    float phase2_at() const override { return 0.66f; }
    bool blooming() const { return hp < max_hp * phase2_at(); }

    // 6 petals fanned upward, homing down onto the player for 1.2 s.
    static int petals(BulletSpawn out[]) {
        for (int i = 0; i < 6; i++)
            out[i] = mkh(-PI / 2.0f + (i - 2.5f) * 0.36f, 90.0f, 2.5f, 5.0f, 1.2f);
        return 6;
    }

    // A blossom: every bullet leaves at once with a speed set by a five-
    // lobed rose, r = |sin(2.5 t)|, so together they hold a flower's shape
    // and it grows as it flies; all share a drift toward the player, so the
    // whole flower travels at them while it opens.
    static int bloom(float aim, BulletSpawn out[]) {
        const int   OUTLINE = 40, CENTRE = 8;
        const float DRIFT   = 55.0f;
        float turn = ernd() * TAU;
        float dx = cosf(aim) * DRIFT, dy = sinf(aim) * DRIFT;
        int n = 0;
        for (int i = 0; i < OUTLINE; i++) {
            float t = i * (TAU / OUTLINE);
            float spd = 25.0f + 75.0f * fabsf(sinf(2.5f * t));
            BulletSpawn b = mk(t + turn, spd, 2.5f, 5.0f);
            b.vx += dx; b.vy += dy;
            out[n++] = b;
        }
        for (int i = 0; i < CENTRE; i++) {
            BulletSpawn b = mk(turn + i * (TAU / CENTRE), 14.0f, 2.5f, 5.0f);
            b.vx += dx; b.vy += dy;
            out[n++] = b;
        }
        return n;
    }
public:
    Snawfus() : Enemy(320, 160, 520, {1.0f,1.0f,1.0f,1.25f,1.25f,1.25f,1.25f}) {}
    const char* name()          const override { return "SNAWFUS"; }
    float       fire_interval() const override { return blooming() ? 1.6f : 1.2f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        if (blooming()) return bloom(a, out);
        int n = petals(out);
        if (++shower % 3 == 0)
            for (int i = -1; i <= 1; i++)
                out[n++] = mk(a + i * 0.2f, 170.0f, 2.5f, 5.0f);
        return n;
    }
};

// Snake's head, leopard's body, hart's legs: the beast hunted forever and
// never caught.
// Phase 1, The Chase: it gallops side to side across the top, a hoofprint
//   every few steps; each waits a second, then flies at the player -- a
//   barrage from all along its track, every shot from a different spot.
// Phase 2 (half HP), Leopard Coat: it trots back to the middle and stands,
//   and throws its own spots -- clumps of bullets, solid spots and hollow
//   rosettes like the ones on its coat, scattered across a wide arc and each
//   holding its shape as it flies, so the screen fills with a leopard print
//   to pick a way through.
class QuestingBeast : public Enemy {
    static constexpr float HOME_X = 320.0f, HOME_Y = 140.0f;
    int   dir = 1;       // phase 1: galloping right (1) or left (-1)
    float run = 0.0f;    // phase 1: gallop clock, for the walk sheet's cycle

    bool home() const { return fabsf(x - HOME_X) < 1.0f && fabsf(y - HOME_Y) < 1.0f; }

    static BulletSpawn hoofprint(float wait, float speed, float off) {
        BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
        b.delay = wait; b.launch_speed = speed; b.launch_off = off;
        return b;
    }

    // One spot: 5 bullets sharing a velocity, each nudged a little off it, so
    // the clump flies together and opens slowly. A rosette is a ring of 5
    // round an empty middle; a solid spot is a centre and 4 round it.
    static int spot(float ang, float speed, bool rosette, BulletSpawn out[]) {
        const float SPREAD = 9.0f;   // px/s each bullet drifts from the clump's centre
        float vx = cosf(ang) * speed, vy = sinf(ang) * speed, turn = ernd() * TAU;
        for (int i = 0; i < 5; i++) {
            BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
            float r = (rosette || i > 0) ? SPREAD : 0.0f;
            float k = turn + i * (TAU / (rosette ? 5 : 4));
            b.vx = vx + cosf(k) * r;
            b.vy = vy + sinf(k) * r;
            out[i] = b;
        }
        return 5;
    }
public:
    QuestingBeast() : Enemy(HOME_X, HOME_Y, 560, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QUESTING BEAST"; }
    float       fire_interval() const override { return ENRAGED ? 1.3f : 0.15f; }
    // Galloping in phase 1: the walk sheet (09_questing_beast_walk), one
    // stride every 0.36 s, facing the way it runs. Phase 2 is its idle.
    float flap_phase()  const override { return ENRAGED ? -1.0f : fmodf(run / 0.36f, 1.0f); }
    int   move_facing() const override { return ENRAGED ? -1 : (dir > 0 ? FACE_RIGHT : FACE_LEFT); }
    void update(float dt, float, float) override {
        if (!ENRAGED) {
            run += dt;
            x += dir * 220.0f * dt;
            if (x < 120.0f) { x = 120.0f; dir =  1; }
            if (x > 520.0f) { x = 520.0f; dir = -1; }
            return;
        }
        // Back to the middle, then stand.
        float dx = HOME_X - x, dy = HOME_Y - y, d = sqrtf(dx * dx + dy * dy), step = 200.0f * dt;
        if (d <= step) { x = HOME_X; y = HOME_Y; }
        else           { x += dx / d * step; y += dy / d * step; }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (!ENRAGED) { out[0] = hoofprint(1.0f, 160.0f, 0.0f); return 1; }
        if (!home()) return 0;   // nothing until it stands in the middle
        // 9 spots across +-1.3 of the aim, each a little off its slot and at
        // its own speed, every other one a rosette.
        float a = aim_at(x,y,px,py);
        int n = 0;
        for (int i = 0; i < 9; i++) {
            float ang = a + (i - 4) * 0.29f + (ernd() - 0.5f) * 0.16f;
            n += spot(ang, 85.0f + ernd() * 60.0f, i % 2 == 0, out + n);
        }
        return n;
    }
};

// The dragon of Poitiers -- its name is "the great gullet". It breathes
// fire out and gulps it back.
// Phase 1, Gulp: on the frame its idle shows the breath (Enemy::breathe), a
//   ring of fireballs bursts from its mouth, each slowing to a stop just
//   short of the screen's edge along its own line (or halfway, for every
//   other one) and sucked back into the gullet -- dodge it going out, and
//   again coming home. Between breaths it spits fire at the player, a shot
//   every quarter second, each easing off as it comes (spit()).
// Phase 2 (two-thirds HP), Gluttony: the breath never stops. Two arms of
//   fire wheel round from its mouth without pause, every fireball out to the
//   screen's edge and back -- about 164 in the air at once -- while it sprays
//   a stream of fire straight at the player.
class GrandGoule : public Enemy {
    float wheel = 0.0f;   // phase 2: the breath's turning angle
    int   tick  = 0;      // phase 2: volleys, to spray every other one

    // Its gluttony starts early: phase 2 from two-thirds health, not half.
    float phase2_at() const override { return 0.66f; }
    bool gluttony() const { return hp < max_hp * phase2_at(); }

    // A shot at the player that leaves fast and eases off as it comes, so it
    // arrives slow: 260 down to 90.
    static BulletSpawn spit(float ang) {
        BulletSpawn b = mk(ang, 260.0f, 3.0f, 5.0f);
        b.accel = -220.0f; b.min_speed = 90.0f;
        return b;
    }

    // One boomerang fireball at `ang`: leaves at a speed set by `share`, and
    // slows to a stop that share of the way to the arena's edge along its
    // line -- no lower than `floor` (default the arena's bottom edge) --
    // then comes back to be swallowed.
    BulletSpawn fireball(float ang, float share, float floor = ARENA_H - 14.0f) const {
        const float MARGIN = 14.0f;
        float cx = cosf(ang), cy = sinf(ang), reach = 1e9f;
        if (cx > 0.0f) reach = fminf(reach, (ARENA_W - MARGIN - x) / cx);
        if (cx < 0.0f) reach = fminf(reach, (MARGIN - x) / cx);
        if (cy > 0.0f) reach = fminf(reach, (floor - y) / cy);
        if (cy < 0.0f) reach = fminf(reach, (ARENA_TOP + MARGIN - y) / cy);
        reach *= share;
        float speed = 140.0f + 160.0f * share;   // the far ones leave fastest
        BulletSpawn b = mk(ang, speed, 3.0f, 5.0f);
        b.accel = -speed * speed / (2.0f * fmaxf(reach, 20.0f));   // stops after `reach`
        return b;
    }
public:
    GrandGoule() : Enemy(320, 160, 820, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "GRAND'GOULE"; }
    // Phase 2 fires without pause; phase 1 spits a shot at the player every
    // quarter second, its rings coming through breathe().
    float       fire_interval() const override { return gluttony() ? 0.044f : 0.25f; }
    // Phase 1's ring: 24 round, turned at random, the even ones to the edge
    // and the odd halfway.
    int breathe(float, float, BulletSpawn out[], int) override {
        if (gluttony()) return 0;   // phase 2's breath is the constant wheel
        float turn = ernd() * TAU;
        for (int i = 0; i < 24; i++)
            out[i] = fireball(turn + i * (TAU / 24), i % 2 == 0 ? 1.0f : 0.5f);
        return 24;
    }
    // Phase 2: every 0.044 s two fireballs from opposite arms of the wheel,
    // out to the edge -- 3.6 s there and back on average, so about 164 in
    // the air -- and
    // every other volley a spray shot at the player, scattered a little and
    // at mixed speeds, so it reads as a hose of fire.
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (!gluttony()) {   // phase 1: one spit at the player, scattered a little
            out[0] = spit(aim_at(x,y,px,py) + (ernd() - 0.5f) * 0.3f);
            return 1;
        }
        wheel += 0.18f;   // a full turn every 1.5 s
        // Fair play: the wheel's fireballs stop and turn back above y 330,
        // not in the bottom strip where the player moves -- there they would
        // all pause and reverse on top of the player, under the spray
        // (feedback_bullet_fairness). Below it, only the spray reaches.
        const float WHEEL_FLOOR = 330.0f;
        int n = 0;
        out[n++] = fireball(wheel, 1.0f, WHEEL_FLOOR);
        out[n++] = fireball(wheel + PI, 1.0f, WHEEL_FLOOR);
        if (tick++ % 2 == 0)
            out[n++] = spit(aim_at(x,y,px,py) + (ernd() - 0.5f) * 0.4f);
        return n;
    }
};

// Goat-bodied man-eater with a human face, eyes under its arms, and a cry
// like a baby's -- its idle opens its mouth wide on frame 2, and that is
// when it wails (Enemy::breathe).
// Phase 1, Evil Eye: every cry throws an eye made of bullets -- an almond of
//   lids round an iris ring and a pupil -- that drifts at the player and
//   opens as it comes. Slip in where the lids part and out past the iris.
//   Between cries the eye under its arm watches: every 0.9 s a shot at the
//   player.
// Phase 2 (half HP), Devour: the eyes keep coming, and now it hunts. The eye
//   on its flank stays shut (the closed-eye idle, alt_pose) until it opens
//   -- the warning -- and it fixes on where the player stands; then it leaps
//   there in a straight line, legs flung back (the leap sheet), its body
//   hurting to touch, bursts a ring where it lands, and stays there until
//   the next charge. Move when the eye opens.
class Paoxiao : public Enemy {
    static constexpr float HOME_X = 320.0f, HOME_Y = 150.0f;
    enum State { WAIT, AIM, LUNGE } state = WAIT;
    float st = 0.0f;               // seconds in this state
    float tx = 0.0f, ty = 0.0f;    // where the lunge is going
    bool  landed = false;          // a ring owed: it just touched down

    void enter(State s) { state = s; st = 0.0f; }
public:
    Paoxiao() : Enemy(HOME_X, HOME_Y, 640, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "PAOXIAO"; }
    // The eye's shot, and phase 2's landing ring, both through fire().
    float       fire_interval() const override { return landed ? 0.0f : 0.9f; }
    float       contact_damage() const override { return ENRAGED ? 5.0f : 0.0f; }
    // Phase 2: the flank eye shut except in the wind-up; the leap sheet
    // through the charge, facing where it's going.
    bool  alt_pose()    const override { return ENRAGED && state == WAIT; }
    float flap_phase()  const override { return ENRAGED && state == LUNGE ? 0.0f : -1.0f; }
    int   move_facing() const override { return ENRAGED && state == LUNGE ? facing_toward(tx - x, ty - y) : -1; }
    void update(float dt, float px, float py) override {
        if (!ENRAGED) return;
        st += dt;
        switch (state) {
            case WAIT: if (st >= 1.6f) enter(AIM); break;
            case AIM:   // the wind-up: the eye opens, fixing on the player
                tx = px; ty = fminf(py, 400.0f);
                if (st >= 0.6f) enter(LUNGE);
                break;
            case LUNGE: {
                float dx = tx - x, dy = ty - y, d = sqrtf(dx * dx + dy * dy), step = 520.0f * dt;
                // Lands and stays: the next charge goes from here.
                if (d <= step) { x = tx; y = ty; landed = true; fire_timer = 0.0f; enter(WAIT); }
                else           { x += dx / d * step; y += dy / d * step; }
                break;
            }
        }
    }
    // The cry: an eye of bullets. Every bullet leaves at once with a velocity
    // that is the eye's shape -- upper and lower lids as parabolas meeting at
    // the corners, a ring of an iris, a small pupil -- plus a shared drift at
    // the player, so the eye holds its shape, grows as it flies (90 px/s
    // wide, 45 tall per lid) and travels at them.
    int breathe(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        float dx = cosf(a) * 70.0f, dy = sinf(a) * 70.0f;
        int n = 0;
        auto put = [&](float vx, float vy) {
            BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
            b.vx = vx + dx; b.vy = vy + dy;
            out[n++] = b;
        };
        for (int i = 0; i < 12; i++) {                 // lids: 12 along the top,
            float t = -1.0f + 2.0f * i / 11.0f;        // the bottom's 10 between the corners
            float lid = (1.0f - t * t) * 45.0f;
            put(t * 90.0f, -lid);
            if (i > 0 && i < 11) put(t * 90.0f, lid);
        }
        for (int i = 0; i < 10; i++)                   // iris
            put(cosf(i * TAU / 10) * 26.0f, sinf(i * TAU / 10) * 26.0f);
        for (int i = 0; i < 4; i++)                    // pupil
            put(cosf(i * TAU / 4) * 6.0f, sinf(i * TAU / 4) * 6.0f);
        return n;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (landed) {   // touched down from a lunge: a ring round where it stands
            landed = false;
            // Fair play: it lands where the player stood, so if they are
            // still within 60 px the ring would burst point-blank with gaps
            // too small to pass (feedback_bullet_fairness) -- skip it.
            float ddx = px - x, ddy = py - y;
            if (ddx * ddx + ddy * ddy < 60.0f * 60.0f) return 0;
            float turn = ernd() * TAU;
            for (int i = 0; i < 16; i++)
                out[i] = mk(turn + i * (TAU / 16), 150.0f, 2.5f, 5.0f);
            return 16;
        }
        // The flank eye shoots only while it is open: always in phase 1,
        // only in the wind-up in phase 2.
        if (ENRAGED && state != AIM) return 0;
        out[0] = mk(aim_at(x,y,px,py), 200.0f, 2.5f, 5.0f);   // the eye's shot
        return 1;
    }
};

// A PENTAGRAM (Ebigane's; Nadubi's too): every bullet leaves its middle at
// once with a velocity that is the shape -- the star's five lines (each
// point to the one two on), 9 along each, inside a ring of 30 -- so the star
// holds its shape and grows outward from the enemy (or from (ox, oy)), a point 120 px/s out, until it is
// bigger than the arena. Turned at random. `slowing`: every bullet eases
// off by the same share of its own speed -- to a quarter of it over 3.4 s,
// when the ring is some 255 px out, near the arena's edges -- so the star
// keeps its shape while it slows into a huge, slow star round them.
static int pentagram_shots(BulletSpawn out[], bool slowing, bool from = false, float ox = 0.0f, float oy = 0.0f) {
    const float R = 120.0f;
    float turn = ernd() * TAU;
    int n = 0;
    auto put = [&](float vx, float vy) {
        BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
        b.vx = vx; b.vy = vy;
        b.from = from; b.ox = ox; b.oy = oy;   // from (ox, oy), or the enemy's middle
        if (slowing) {
            float sp = sqrtf(vx * vx + vy * vy);
            b.accel = -0.22f * sp; b.min_speed = 0.25f * sp;
        }
        out[n++] = b;
    };
    for (int k = 0; k < 5; k++) {
        float a0 = turn + k * (TAU / 5), a1 = turn + (k + 2) * (TAU / 5);
        for (int i = 0; i < 9; i++) {   // each line from one point toward the next but one
            float u = i / 9.0f;
            put(R * (cosf(a0) + (cosf(a1) - cosf(a0)) * u), R * (sinf(a0) + (sinf(a1) - sinf(a0)) * u));
        }
    }
    for (int i = 0; i < 30; i++)        // the ring through the points
        put(R * cosf(turn + i * (TAU / 30)), R * sinf(turn + i * (TAU / 30)));
    return n;
}

// Tusked, boar-bodied beast on red bat wings. Its screech is a bat's: it
// echoes off the walls. It screeches on the frame its idle opens its mouth
// (Enemy::breathe).
// Phase 1, Echo & Pentagram: every screech, a fan of big bouncing shots
//   round the player that ricochet off the walls -- hollow until their last
//   bounce (the battle's bouncing kind), so read where each will come back
//   from. Between screeches it casts massive pentagrams of bullets -- a
//   five-point star in its ring -- that open out from its middle until they
//   fill the arena: slip through a gap in the ring, then between the
//   star's points, as it sweeps past.
// Phase 2 (half HP), Night Flight: it takes wing -- legs drawn up, wings
//   beating (the fly sheet) -- and flies figure-eights through the upper
//   arena. Each time it crosses the middle of the loop it casts a pentagram
//   -- one that slows as it spreads, settling into a huge, slow star round
//   the arena's edges -- and its screech, a wider fan of ricochets, keeps
//   going between. Nothing aimed: only ricochets and stars.
class Ebigane : public Enemy {
    static constexpr float LOOP_W = 1.05f;   // rad/s: a figure-eight every 6 s, the middle every 3
    float t        = 0.0f;   // phase 2: flight clock
    bool  crossed  = false;  // just crossed the middle: a pentagram owed
public:
    Ebigane() : Enemy(320, 140, 860, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "EBIGANE"; }
    // Phase 2 checks often, so the crossing's volley leaves on the crossing.
    float       fire_interval() const override { return ENRAGED ? 0.05f : 2.2f; }
    // Flying: the fly sheet, a wingbeat every 0.6 s.
    float flap_phase() const override { return ENRAGED ? fmodf(t / 0.6f, 1.0f) : -1.0f; }
    void update(float dt, float, float) override {
        if (!ENRAGED) return;
        float before = sinf(t * LOOP_W);
        t += dt;
        float now = sinf(t * LOOP_W);
        // A figure-eight: across the arena and back, two loops up and down.
        x = 320.0f + 200.0f * now;
        y = 170.0f +  70.0f * sinf(2.0f * t * LOOP_W);
        if ((before < 0.0f) != (now < 0.0f)) crossed = true;   // through the middle
    }
    // The screech: big bouncing shots fanned round the aim -- 7, or 9 in flight.
    int breathe(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x, y, px, py);
        int n = ENRAGED ? 9 : 7;
        for (int i = 0; i < n; i++)
            out[i] = mkb(a + (i - (n - 1) * 0.5f) * 0.32f, 170.0f, 5.0f, 5.0f);
        return n;
    }
    // Phase 1: a pentagram. Phase 2: a slowing pentagram at the middle of
    // the loop.
    int fire(float, float, BulletSpawn out[], int) override {
        if (!ENRAGED) return pentagram_shots(out, false);
        if (crossed) { crossed = false; return pentagram_shots(out, true); }
        return 0;
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

// The lodsilungur, Iceland's "shaggy trout" (A Book of Creatures): a trout
// "covered with fine, downy, cottony-white hair" that "resembles mold", with
// a reddish beard, pitch-black teeth and small deep-set eyes; to eat one is
// death -- a whole household at Kaldrani died of a single meal. MEDIUM tier,
// 500 HP, mold-white bullets.
// Phase 1 -- swimming a slow S across the top of the arena, facing its way:
//   Mold  -- on its inhale frame (idle frame 1) it breathes out a spray of
//            mold spores at the player; they slow to a drift and each FRUITS
//            -- bursts into three -- a moment later, then drifts on out.
//   Beard -- every 1.1 s a flick of the beard: a fan of 5 at the player.
//   Roe   -- every 2.5 s it drops an egg where it is (the user's design);
//            the egg sits a moment, then hatches into a ring of 10.
// Everything it fires turns clockwise round where it left at one shared rate
//   (SWIRL; the user's call), so its whole pattern is one slow swirl.
// Phase 2 (half HP, the user's design) -- it swims VERY FAST in straight
//   dashes, slams into a wall, and every wall it hits bursts out a big ring
//   of 30 (plus an egg); a breath, then it dashes off the wall at a new angle
//   across the arena. Its spores fruit three times.
class Lodsilungur : public Enemy {
    static constexpr float DASH_SPEED = 380.0f;   // phase 2: very fast
    static constexpr float STUN_T     = 0.35f;    // ... a breath against the wall before the next dash
    // Every shot it makes turns clockwise round where it left at this one
    // rate (the user: all of it spinning the same way, the same speed), so
    // the whole fight reads as one slow swirl.
    static constexpr float SWIRL = 0.6f;
    static BulletSpawn swirl(BulletSpawn b) { b.orbit_w = SWIRL; return b; }
    float swim = 0.0f;                       // phase 1: time along its S
    float vx = 0.0f, vy = 0.0f;              // phase 2: the dash (0 = against a wall, getting its breath)
    float stun = 0.0f;
    bool  slammed = false;                   // hit a wall: the burst is due
    float last_x = 320.0f, last_y = 160.0f;  // for which way it swims
    float egg_t = 0.0f;                      // phase 1: time to the next egg
    bool  lay = false;

    // An egg: sits where it's laid, hatches after HATCH_T into a ring that
    // turns clockwise as it spreads, and is gone.
    static BulletSpawn egg() {
        BulletSpawn b = mk(0.0f, 0.0f, 5.0f, 5.0f);
        b.shed_first = 1.4f; b.shed_every = 1.0f; b.shed_times = 1; b.shed_dies = true;
        b.shed_n = 10; b.shed_spread = TAU * 9.0f / 10.0f; b.shed_speed = 85.0f;
        b.shed_spin = SWIRL;                                 // clockwise, with the rest
        b.flash_in = true;
        return b;
    }

    static BulletSpawn spore(float a) {
        BulletSpawn b = mk(a, 120.0f + ernd() * 50.0f, 3.5f, 5.0f);
        // Slows to a drift, but keeps going -- off the screen in ~8 s, so old
        // spores don't pile up (the tester measured 90 at 14 px/s).
        b.accel = -140.0f; b.min_speed = 38.0f;
        b.shed_first = 1.1f + ernd() * 0.3f;                 // then fruits
        b.shed_every = 0.9f; b.shed_times = 1;
        b.shed_n = 3; b.shed_spread = TAU * 2.0f / 3.0f; b.shed_speed = 110.0f;
        b.shed_spin = SWIRL;
        return swirl(b);
    }
public:
    Lodsilungur() : Enemy(320, 140, 500, {1.25f,0.75f,1.25f,0.75f,1.0f,1.25f,1.5f}) {}
    const char* name()          const override { return "LODSILUNGUR"; }
    int         breath_frame()  const override { return 1; }       // the inhale
    float       fire_interval() const override { return 0.05f; }   // eggs, flicks and splashes on their own clocks
    bool dashing() const { return vx != 0.0f || vy != 0.0f; }
    int move_facing() const override {                             // swimming its way
        if (!ENRAGED) return facing_toward(x - last_x, y - last_y);
        return dashing() ? facing_toward(vx, vy) : -1;
    }
    void update(float dt, float px, float py) override {
        last_x = x; last_y = y;
        if (!ENRAGED) {
            if ((egg_t += dt) >= 2.5f) { egg_t = 0.0f; lay = true; }
            swim += dt;
            x = 320.0f + 200.0f * sinf(swim * 0.45f);
            y = 140.0f + 40.0f * sinf(swim * 0.9f);
            return;
        }
        if ((egg_t += dt) >= 2.5f) { egg_t = 0.0f; lay = true; }
        if (!dashing()) {
            if ((stun += dt) < STUN_T) return;
            // Off the wall, out across the arena: roughly through the
            // player's side of it, so the dashes keep crossing the room --
            // but never at a wall spot near the player: its burst there
            // would leave them no room (the tester's finding). A dash whose
            // wall hit lands within SLAM_CLEAR of them is picked again.
            stun = 0.0f;
            const float L = 40.0f, R = ARENA_W - 40.0f, T = ARENA_TOP + 40.0f, B = ARENA_H - 40.0f;
            const float SLAM_CLEAR = 110.0f;
            float a = 0.0f;
            for (int tries = 0; tries < 24; tries++) {
                a = aim_at(x, y, px, py) + (ernd() * 2.0f - 1.0f) * (tries < 12 ? 0.7f : PI);
                float c = cosf(a), sn = sinf(a), t = 1e9f;   // where along it the wall is hit
                if (c >  0.001f) t = fminf(t, (R - x) / c);
                if (c < -0.001f) t = fminf(t, (L - x) / c);
                if (sn >  0.001f) t = fminf(t, (B - y) / sn);
                if (sn < -0.001f) t = fminf(t, (T - y) / sn);
                if (t < 60.0f) continue;                     // straight back into the wall it's on
                if (hypotf(x + c * t - px, y + sn * t - py) >= SLAM_CLEAR) break;
            }
            vx = cosf(a) * DASH_SPEED; vy = sinf(a) * DASH_SPEED;
            return;
        }
        x += vx * dt; y += vy * dt;
        const float L = 40.0f, R = ARENA_W - 40.0f, T = ARENA_TOP + 40.0f, B = ARENA_H - 40.0f;
        if (x < L || x > R || y < T || y > B) {                       // slam
            x = fminf(fmaxf(x, L), R); y = fminf(fmaxf(y, T), B);
            vx = vy = 0.0f;
            slammed = true;
        }
    }
    float fire_due = 0.0f;                                          // phase 1: the beard flick's own clock
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        int n = 0;
        if (lay) { lay = false; out[n++] = egg(); }
        if (!ENRAGED) {                                             // the beard flick, every 1.1 s
            if ((fire_due += 0.05f) < 1.1f) return n;
            fire_due = 0.0f;
            // Led against the swirl: it turns SWIRL rad/s on the way, so it
            // leaves that much anticlockwise of the player and curves in
            // onto them, arriving from their right.
            float lead = SWIRL * hypotf(px - x, py - y) / 200.0f;
            for (int i = 0; i < 5; i++) out[n++] = swirl(mk(a - lead + (i - 2) * 0.2f, 200.0f, 2.5f, 5.0f));
            return n;
        }
        if (!slammed) return n;
        slammed = false;                                            // the wall burst: 30 round, and an egg
        float turn = ernd() * TAU;
        for (int i = 0; i < 30; i++) out[n++] = swirl(mk(turn + i * (TAU / 30), 135.0f, 3.0f, 5.0f));
        out[n++] = egg();
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED && dashing()) return 0;                         // not mid-dash
        float a = aim_at(x,y,px,py);
        int n = 6;
        for (int i = 0; i < n; i++) {
            BulletSpawn b = spore(a + (ernd() * 2.0f - 1.0f) * 0.55f);
            if (ENRAGED) b.shed_times = 3;                          // phase 2: fruits three times
            out[i] = b;
        }
        return n;
    }
};

// The ofuguggi, Iceland's "reverse-fin trout" (A Book of Creatures): jet-
// black, its red flesh fed on the drowned, it "swims backwards with its tail
// first and the head following"; its poison makes a victim "swell up until
// their stomach bursts, producing a cross-shaped wound". MEDIUM tier, 520 HP,
// red-flesh bullets.
// It swims TAIL FIRST, its head trailing (its sheet is drawn tail-forward),
// wandering unpredictably -- random spots, curving, changing pace.
// Phase 1:
//   Reverse fins -- on its breath frame (idle frame 1) two fans thrown the
//                   WRONG way, away from the player -- 9, and 8 slower in their
//                   gaps; they slow, stop and come back (no faster than 220)
//                   -- by then it has swum on, so they fly past where it was
//                   and on at the player.
//   Swell        -- every 2.2 s a slow fat orb at the player that, after a
//                   moment, BURSTS into a double cross: eight out, + and x.
// Phase 2 (half HP): it swims faster, the fans are 13 and 12, and two swells
//   come at a time, each double cross bursting three times -- streams.
class Ofuguggi : public Enemy {
    // Swimming: it heads for a random spot anywhere in the top two thirds,
    // steering round to it (so it curves, never a straight line), at a speed
    // it keeps changing, and picks a new spot before it gets there -- no
    // loop to learn (the user wanted it unpredictable and not stuck at one
    // height).
    float vx = 60.0f, vy = 0.0f, tx = 320.0f, ty = 160.0f, retarget = 0.0f, pace = 90.0f;
    float last_x = 320.0f, last_y = 130.0f;
    float swell_t = 0.0f;

    static BulletSpawn swell(float a, int bursts) {
        BulletSpawn b = mk(a, 75.0f, 6.0f, 5.0f);
        b.shed_first = 1.3f; b.shed_every = 0.12f; b.shed_times = bursts; b.shed_dies = true;
        b.shed_n = 8; b.shed_spread = TAU * 7.0f / 8.0f; b.shed_speed = 150.0f;   // a double cross, + and x
        return b;
    }
public:
    Ofuguggi() : Enemy(320, 130, 520, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OFUGUGGI"; }
    int         breath_frame()  const override { return 1; }
    float       fire_interval() const override { return 0.05f; }   // swells on their own clock
    // Tail first. Its sheet is drawn reversed -- each direction's frame has
    // the TAIL toward that direction -- so facing the way it moves puts its
    // head behind (flipping it here as well cancelled out: face first).
    int move_facing() const override { return facing_toward(x - last_x, y - last_y); }
    // Always swimming: its backwards swim (15_ofuguggi_swim), 4 frames at 130 ms.
    float swim_t = 0.0f;
    float flap_phase() const override { return fmodf(swim_t / 0.52f, 1.0f); }
    void update(float dt, float, float) override {
        last_x = x; last_y = y;
        swell_t += dt; swim_t += dt;
        if ((retarget -= dt) <= 0.0f || hypotf(tx - x, ty - y) < 40.0f) {
            tx = 70.0f + ernd() * (ARENA_W - 140.0f);
            ty = ARENA_TOP + 50.0f + ernd() * 240.0f;
            retarget = 0.8f + ernd() * 1.6f;
            pace = 60.0f + ernd() * 80.0f;
        }
        float speed = pace * (ENRAGED ? 1.6f : 1.0f);
        float want = atan2f(ty - y, tx - x), have = atan2f(vy, vx);
        float turn = remainderf(want - have, TAU);
        float max_turn = 2.4f * dt;                          // it curves round, it doesn't snap
        have += fminf(fmaxf(turn, -max_turn), max_turn);
        vx = cosf(have) * speed; vy = sinf(have) * speed;
        x = fminf(fmaxf(x + vx * dt, 50.0f), ARENA_W - 50.0f);
        y = fminf(fmaxf(y + vy * dt, ARENA_TOP + 40.0f), ARENA_TOP + 320.0f);
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (swell_t < 2.2f) return 0;
        swell_t = 0.0f;
        float a = aim_at(x,y,px,py);
        if (!ENRAGED) { out[0] = swell(a, 1); return 1; }
        out[0] = swell(a - 0.4f, 3);
        out[1] = swell(a + 0.4f, 3);
        return 2;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        float away = aim_at(px, py, x, y);                       // the wrong way
        int f = ENRAGED ? 13 : 9, n = 0;
        for (int layer = 0; layer < 2; layer++) {                // a fan, and a slower one in its gaps
            int m = f - layer;
            for (int i = 0; i < m; i++) {
                BulletSpawn b = mk(away + (i - (m - 1) * 0.5f) * 0.16f, layer ? 120.0f : 150.0f, 3.0f, 5.0f);
                b.accel = -190.0f;                               // slows, stops, comes back the way it went
                b.max_speed = 220.0f;                            // ... but no faster than this
                out[n++] = b;
            }
        }
        return n;
    }
};

// The kamaitachi of Japan (A Book of Creatures): "something like a weasel
// with razor-sharp sickle claws" that travels hidden in whirlwinds and cuts
// whoever it passes -- told as three, one knocking you down, one cutting, one
// salving the wound so it doesn't bleed. HARD tier, 720 HP, wind-white
// bullets. SMALL sheet (30x31): a white ermine with sickle forelimbs riding a
// tornado. Every shot leaves from the part of it that makes it (the user):
// its whirlwind, its sickles. Every shot at about one pace, SPEED.
// Its patterns are TORNADOES (the user): funnels drawn in shots.
// Phase 1 -- riding the wind about the upper arena, darting spot to spot:
//   Twisters -- every TWISTER_EVERY s its whirlwind casts off a TORNADO: a
//               funnel of shots -- stacked rings, narrow at the foot, wide at
//               the top -- every ring SPINNING so the whole funnel spins, and
//               it FOLLOWS the player a couple of seconds, then goes straight.
//   Sickles  -- as its head comes up (idle frame 2) it flings three SICKLES:
//               crescent blades of shots spinning fast as they fly, one
//               straight at the player and one either side.
// Phase 2 (half HP) -- the HURRICANE (the user, from a reference): it rides
//   to the middle of the screen and SPINS there, and out of the eye -- a clear
//   gap round it, EYE_R wide -- pour two arrays of three shots, half a turn
//   apart, the whole spray turning SPRAY_TURN every shot: the shots fly
//   straight out, so the turning paints a hurricane of curling arms over the
//   whole screen. And it DRAWS THE PLAYER IN: hold against the pull and weave
//   between the arms. Not too hard (the user): a gentle pull.
class Kamaitachi : public Enemy {
    static constexpr float SPEED = 110.0f, DART = 240.0f, PAUSE = 0.6f, TWISTER_EVERY = 1.1f;
    static constexpr float TWISTER_FORM = 0.6f, TWISTER_SPIN = 2.5f, TWISTER_HOME = 2.0f;
    static constexpr float HURRICANE_PULL = 55.0f, EYE_R = 50.0f;   // PULL: felt, but focus (70) still walks out of it
    static constexpr float SPRAY_EVERY = 1.0f / 15.0f, SPRAY_TURN = 0.7f;   // the reference's fire rate 4 frames, spin 10 deg a frame
    static constexpr float MID_X = 320.0f, MID_Y = (ARENA_TOP + ARENA_H) * 0.5f;
    bool  hurricane = false, eye = false;   // spraying; it has reached the middle
    float spray_t = 0.0f, spray_a = 0.0f;
    static constexpr int   FUNNEL_N = 66;
    float t = 0.0f, twister_t = 0.6f, rest = 0.0f, tx = 320.0f, ty = 140.0f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (30x31, drawn 2x about its middle) -> screen
        *ox = x + (fx - 15.0f) * 2.0f; *oy = y + (fy - 15.5f) * 2.0f;
    }
    // A twister: six rings stacked foot to top, each a ring of shots turning
    // on its own squashed circle round a centre on the funnel's axis -- every
    // ring spinning, so the whole tornado spins -- opening out from its axis
    // in TWISTER_FORM s, drifting along `a` and HOMING on the player a couple
    // of seconds (the user).
    int twister(float ox, float oy, float a, float spin, BulletSpawn out[], int max) const {
        int n = 0;
        for (int k = 0; k < 6; k++) {
            float half = 5.0f + k * 6.0f, cy = 32.0f - k * 12.8f;   // a tall funnel: 64 px foot to top
            int pts = 6 + 2 * k;
            for (int q = 0; q < pts && n < max; q++) {
                float v0 = 2.0f * half / TWISTER_FORM;
                BulletSpawn b = mk(q * (TAU / pts) + k * 0.3f, v0, 3.0f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy + cy;          // each ring round its own point on the axis
                b.accel = -v0 / TWISTER_FORM; b.min_speed = 0.01f;
                b.orbit_w = spin; b.orbit_squash = 0.28f;
                b.orbit_vx = cosf(a) * SPEED * 0.8f; b.orbit_vy = sinf(a) * SPEED * 0.8f;
                b.homing = true; b.homing_timer = TWISTER_HOME;
                out[n++] = b;
            }
        }
        return n;
    }
public:
    Kamaitachi() : Enemy(320, 140, 720, {1.25f,0.75f,1.25f,0.75f,1.0f,1.5f,1.5f}) {}
    const char* name()          const override { return "KAMAITACHI"; }
    int         breath_frame()  const override { return 2; }       // the sickles flung
    float       fire_interval() const override { return 0.02f; }   // the twisters on their own clock
    float pull() const override { return hurricane ? HURRICANE_PULL : 0.0f; }
    // In the eye it SPINS (the user): round its eight facings.
    int move_facing() const override {
        static const int ROUND[8] = { FACE_DOWN, FACE_DOWN_RIGHT, FACE_RIGHT, FACE_UP_RIGHT, FACE_UP, FACE_UP_LEFT, FACE_LEFT, FACE_DOWN_LEFT };
        return eye ? ROUND[(int)(t * 10.0f) & 7] : -1;
    }
    void update(float dt, float px, float py) override {
        t += dt; twister_t += dt;
        if (eye) spray_t += dt;
        if (ENRAGED) {                                           // to the middle, and stay
            float dx = MID_X - x, dy = MID_Y - y, d = hypotf(dx, dy);
            if (d > 2.0f) { float st = fminf(DART * dt, d); x += dx / d * st; y += dy / d * st; }
            else { x = MID_X; y = MID_Y; eye = true; }
            return;
        }
        // Darting on the wind: spot to spot in the upper arena, a beat between.
        float dx = tx - x, dy = ty - y, d = hypotf(dx, dy);
        if (d > 3.0f) { float st = fminf(DART * dt, d); x += dx / d * st; y += dy / d * st; return; }
        if ((rest += dt) >= PAUSE) {
            rest = 0.0f;
            for (int k = 0; k < 10; k++) {
                tx = 80.0f + ernd() * (ARENA_W - 160.0f); ty = ARENA_TOP + 60.0f + ernd() * 150.0f;
                if (hypotf(tx - px, ty - py) > 170.0f && hypotf(tx - x, ty - y) > 90.0f) break;
            }
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        if (ENRAGED) {
            if (!eye) return 0;
            hurricane = true;
            // The spray: two arrays of three (a quarter turn across each), half a
            // turn apart, out of the eye's rim, the whole spray turning a step a
            // shot -- straight-flying shots that curl into the hurricane's arms.
            int n = 0;
            while (spray_t >= SPRAY_EVERY && n + 6 <= max) {
                spray_t -= SPRAY_EVERY;
                spray_a += SPRAY_TURN;
                for (int arr = 0; arr < 2; arr++)
                    for (int k = -1; k <= 1; k++) {
                        float a = spray_a + arr * PI + k * (PI / 4);
                        BulletSpawn b = mk(a, SPEED, 3.0f, 5.0f);
                        b.from = true; b.ox = x + cosf(a) * EYE_R; b.oy = y + sinf(a) * EYE_R;
                        out[n++] = b;
                    }
            }
            return n;
        }
        float every = ENRAGED ? TWISTER_EVERY * 0.8f : TWISTER_EVERY;
        if (twister_t < every) return 0;
        twister_t = 0.0f;
        // A twister off its whirlwind: the funnel, upright, marching at the
        // player, leaning slowly as it goes.
        float wx, wy;
        at(15.0f, 27.0f, &wx, &wy);
        float a = aim_at(wx, wy, px, py);
        int m = ENRAGED ? 3 : 1, n = 0;
        for (int k = 0; k < m && n + FUNNEL_N <= max; k++) {
            float ak = a + (k - (m - 1) * 0.5f) * 0.6f;
            n += twister(wx, wy, ak, (k & 1) ? -TWISTER_SPIN : TWISTER_SPIN, out + n, max - n);
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        if (ENRAGED) return 0;                                   // the hurricane is the whole of phase 2
        // The sickles: crescent blades of nine, spinning fast, flung from its
        // forelimbs -- one at the player, the rest either side.
        static float sx[9], sy[9];
        static bool built = false;
        if (!built) {
            built = true;
            for (int k = 0; k < 9; k++) { float a = -1.2f + k * 0.3f; sx[k] = cosf(a) * 14.0f; sy[k] = sinf(a) * 14.0f; }
        }
        float cx, cy;
        at(15.0f, 12.0f, &cx, &cy);                              // its sickle forelimbs
        float a = aim_at(cx, cy, px, py);
        int m = ENRAGED ? 5 : 3, n = 0;
        for (int k = 0; k < m && n + 9 <= max; k++) {
            float ak = a + (k - (m - 1) * 0.5f) * 0.3f;
            n += shape_shots(cx, cy, ak, SPEED * 1.2f, (k & 1) ? -4.0f : 4.0f, 0.3f, sx, sy, 9, out + n);
        }
        return n;
    }
};

// The qiqirn, "a huge dog of Inuit folklore", "hairless except for its
// mouth, feet, and ear and tail tips" (A Book of Creatures): its presence
// throws men and dogs into "fits" that "end only when the qiqirn leaves" --
// yet it is "extremely scared of humans, and will run away if an angakoq sees
// it". MEDIUM tier, 540 HP, pale-skin bullets.
// Fear (the user's design): it keeps to the EDGE of the screen, always on
//   the side opposite the player -- straight through the middle from them --
//   running round the border to get there (17_qiqirn_run, its frightened
//   gallop), so to close on it you have to cross the arena through its fire.
// Fits (the user's design: the whole arena shaking with them, threaded
//   precisely -- crouch-dodging): it keeps up a stream of SHAKING bullets at
//   the player -- tight zigzag fans, twitching side to side down their
//   course, gaps just wide enough to slip through slowly -- and on its breath
//   frame (idle frame 1) a zigzag RING of 28 from its edge, sweeping the
//   whole arena.
// Phase 2 (half HP): the stream comes quicker, and each breath is two rings,
//   the second slower and turned half a step.
class Qiqirn : public Enemy {
    static constexpr float RUN = 220.0f;    // round the border (the user put it back from 500)
    static constexpr float STRIDE_T = 0.36f; // a gallop: the run sheet's 4 frames
    float shot_t = 0.0f;
    float vx = 0.0f, vy = 0.0f;
    float u = -1.0f, ut = 0.0f;             // place along the border (-1 = not on it yet), and where it's headed

    // The border it runs round: a rectangle inset from the walls, measured
    // as distance u from its top-left corner, clockwise.
    static constexpr float L = 50.0f, R = ARENA_W - 50.0f, T = ARENA_TOP + 45.0f, B = ARENA_H - 50.0f;
    static float perim() { return 2.0f * ((R - L) + (B - T)); }
    static void at(float u, float& px, float& py) {
        float w = R - L, h = B - T;
        if (u < w)             { px = L + u;               py = T; }
        else if (u < w + h)    { px = R;                   py = T + (u - w); }
        else if (u < 2*w + h)  { px = R - (u - w - h);     py = B; }
        else                   { px = L;                   py = B - (u - 2*w - h); }
    }
    static float place(float px, float py) {   // the border spot nearest (px, py), as u
        float w = R - L, h = B - T;
        px = fminf(fmaxf(px, L), R); py = fminf(fmaxf(py, T), B);
        float dT = py - T, dB = B - py, dL = px - L, dR = R - px;
        float m = fminf(fminf(dT, dB), fminf(dL, dR));
        if (m == dT) return px - L;
        if (m == dR) return w + (py - T);
        if (m == dB) return w + h + (R - px);
        return 2*w + h + (B - py);
    }

    static BulletSpawn fit(float a, float speed) {
        BulletSpawn b = mk(a, speed, 3.0f, 5.0f);
        b.zig = 0.45f; b.zig_every = 0.18f;                  // a twitch every 0.18 s
        b.accel = -45.0f; b.min_speed = 70.0f;               // slowing as it nears the player (the user's call)
        return b;
    }
public:
    Qiqirn() : Enemy(320, 130, 540, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "QIQIRN"; }
    int         breath_frame()  const override { return 1; }
    float       fire_interval() const override { return 0.05f; }   // the stream on its own clock
    bool running() const { return vx * vx + vy * vy > 30.0f * 30.0f; }
    int move_facing() const override { return running() ? facing_toward(vx, vy) : -1; }
    float run_t = 0.0f;
    float flap_phase() const override { return running() ? fmodf(run_t / STRIDE_T, 1.0f) : -1.0f; }
    void update(float dt, float px, float py) override {
        shot_t += dt;
        if (u < 0.0f) {
            // Onto the border first -- running there at its normal pace,
            // not snapping to it.
            float bx, by;
            at(place(x, y), bx, by);
            float dx = bx - x, dy = by - y, d = hypotf(dx, dy), st = RUN * dt;
            if (d <= st) { x = bx; y = by; u = place(x, y); }
            else {
                x += dx / d * st; y += dy / d * st;
                if (dt > 0.0f) { vx = dx / d * RUN; vy = dy / d * RUN; }
                run_t += dt;
                return;
            }
        }
        // Where it wants to be: on the border, straight through the middle
        // of the arena from the player (with the player dead centre, it
        // stays where it's headed).
        float cx = (L + R) * 0.5f, cy = (T + B) * 0.5f, dx = cx - px, dy = cy - py;
        if (dx * dx + dy * dy > 1.0f) {
            float t = 1e9f;
            if (dx >  0.001f) t = fminf(t, (R - cx) / dx);
            if (dx < -0.001f) t = fminf(t, (L - cx) / dx);
            if (dy >  0.001f) t = fminf(t, (B - cy) / dy);
            if (dy < -0.001f) t = fminf(t, (T - cy) / dy);
            ut = place(cx + dx * t, cy + dy * t);
        }
        // Round the border the short way.
        float P = perim(), d = remainderf(ut - u, P);
        float st = fminf(RUN * (ENRAGED ? 1.2f : 1.0f) * dt, fabsf(d));
        run_t += dt;
        float ox = x, oy = y;
        u = fmodf(u + (d > 0.0f ? st : -st) + P, P);
        at(u, x, y);
        if (dt > 0.0f) { vx = (x - ox) / dt; vy = (y - oy) / dt; }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float every = ENRAGED ? 0.2f : 0.28f;
        if (shot_t < every) return 0;
        shot_t = 0.0f;
        // The stream: a tight zigzag fan of 9 at the player, 0.09 apart --
        // ~27 px between shots where the player is (~300 px off), a precise
        // crouch-walk through -- or, with them right on top of it (within
        // 60 px, the gaps would close), a single shot.
        float a = aim_at(x,y,px,py);
        if (hypotf(px - x, py - y) < 60.0f) { out[0] = fit(a, 150.0f); return 1; }
        // The middle one comes STRAIGHT at the player, no twitch: the
        // zigzags wobble ~6 px off their line and could slide past someone
        // standing still (the user: staying put shouldn't be safe).
        for (int i = 0; i < 9; i++) {
            out[i] = fit(a + (i - 4) * 0.09f, 150.0f);
            if (i == 4) { out[i].zig = 0.0f; out[i].zig_every = 0.0f; }
        }
        return 9;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        // A twitching ring from its edge across the whole arena (the half
        // aimed at the wall behind it is gone at once); phase 2 a second,
        // slower and half a step round. Not with the player on top of it
        // (within 60 px its gaps would close -- the stream's guard too).
        if (hypotf(px - x, py - y) < 60.0f) return 0;
        const int N = 28;
        float turn = ernd() * TAU;
        int n = 0;
        for (int r = 0; r < (ENRAGED ? 2 : 1); r++)
            for (int i = 0; i < N; i++) out[n++] = fit(turn + (i + r * 0.5f) * (TAU / N), r ? 95.0f : 125.0f);
        return n;
    }
};

// The vatnaormur, Iceland's lake serpent (A Book of Creatures): the
// Lagarfljot worm began as a little heath-worm a girl laid on a gold ring in
// a box, hoping the gold would grow; the worm grew instead, so she threw it,
// ring and all, into the lake, where it grew into a monster, its spiked humps
// rising from the water. Two Finnish sorcerers bound it head and tail to the
// lake bottom. HARD tier, 740 HP, lake-blue bullets. BIG sheet (114x59, five
// idle frames: the neck sways the head out at frame 1). It never leaves its
// lake, always facing front. Every shot leaves from the part of it that makes it (the user): its
// mouth, its humps. Every shot at one pace, SPEED.
// Phase 1:
//   Ripples -- every RIPPLE_EVERY s a ring spreads from where each hump meets
//              the water, the two rings crossing into a moire.
//   Ring    -- as the head sways out (idle frame 1) it spits the GOLD RING
//              it grew on: a ring of shots opening out of its mouth, spinning,
//              HOMING on the player for RING_HOME s.
// Phase 2 (half HP) -- bound head and tail, it thrashes: a third hump ripples
//   between the coils (not the tail's, the user), the rings curl as they spread; no
//   more gold rings (the user).
class Vatnaormur : public Enemy {
    static constexpr float SPEED = 85.0f, RIPPLE_EVERY = 0.9f, RING_R = 34.0f,   // SPEED: the user, a little slower (was 100)
                           RING_HOME = 1.5f;   // the user: shorter (was 2.5)
    static constexpr int   RIPPLE_N = 32, RING_N = 16;
    float ripple_t = 0.0f;
    int   ripples = 0;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (114x59, drawn 2x about its middle) -> screen
        *ox = x + (fx - 57.0f) * 2.0f; *oy = y + (fy - 29.5f) * 2.0f;
    }
    void mouth(float* ox, float* oy) const { at(56.5f, 22.0f, ox, oy); }   // it always faces front (the user)
public:
    Vatnaormur() : Enemy(320, 140, 740, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "VATNAORMUR"; }
    int         breath_frame()  const override { return 1; }       // the head swayed out
    int         move_facing()   const override { return FACE_DOWN; }
    float       fire_interval() const override { return 0.02f; }   // the ripples on their own clock
    void update(float dt, float, float) override { ripple_t += dt; }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        static const float HX[3] = { 30.0f, 84.0f, 57.0f };   // where the humps meet the water: the coils, then the middle
        int humps = ENRAGED ? 3 : 2;
        if (ripple_t >= RIPPLE_EVERY && n + humps * RIPPLE_N <= max) {
            // Ripples: a ring from each hump, every other volley half a step
            // round so the gaps don't line up twice.
            ripple_t = 0.0f;
            float off = (ripples++ & 1) * 0.5f;
            for (int h = 0; h < humps; h++) {
                float hx, hy;
                at(HX[h], 46.0f, &hx, &hy);
                for (int k = 0; k < RIPPLE_N; k++) {
                    BulletSpawn b = mk((k + off) * (TAU / RIPPLE_N), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = hx; b.oy = hy;
                    if (ENRAGED) b.orbit_w = (h & 1) ? 0.25f : -0.25f;   // thrashing: the rings curl, the two ways
                    out[n++] = b;
                }
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The gold ring (phase 1 only): opening out of its mouth, spinning,
        // homing on the player for RING_HOME s.
        if (ENRAGED || max < RING_N) return 0;
        static float sx[RING_N], sy[RING_N];
        static bool built = false;
        if (!built) {
            built = true;
            for (int k = 0; k < RING_N; k++) { sx[k] = cosf(k * (TAU / RING_N)) * RING_R; sy[k] = sinf(k * (TAU / RING_N)) * RING_R; }
        }
        float mx, my;
        mouth(&mx, &my);
        int n = shape_shots(mx, my, aim_at(mx, my, px, py), SPEED, 1.5f, 0.5f, sx, sy, RING_N, out);
        for (int k = 0; k < n; k++) { out[k].homing = true; out[k].homing_timer = RING_HOME; }
        return n;
    }
};

// The skeljaskrimsli, Iceland's shell monster (A Book of Creatures): a
// humped beast the size of a bull calf or a huge horse that comes up out of
// the sea, broad-necked, impressive jaws, a glow from its mouth, short strong
// legs, a tail with a lump at the end, and a coat of shells that rattle and
// shine as it moves. HARD tier, 760 HP, shell-pearl bullets. BIG sheet
// (86x43, five idle frames: the hump rises, the mouth glow pulses at frame 2,
// a glint sweeps the shells). It stands its ground, always facing front (the user).
// TODO art (the user): its tail should swing behind its head, slamming the
// ground on the opposite side each swing.
// Every shot leaves from the part of it that makes it (the user): its
// shells, its mouth. Every shot at one pace, SPEED.
// Phase 1 (to 66% HP, the user) -- a BUILDUP to phase 2:
//   Shells -- off its hump all the while, two spirals of shells turning
//             opposite ways -- mirror images, as a shell is -- weaving a
//             lattice over the arena: one arm each at first, quickening as
//             it is hurt, a second arm each from halfway through.
//   Glow   -- as the mouth glow pulses (idle frame 2), two rows of light
//             fanned at the player, widening as it is hurt.
// Phase 2 (66% HP) -- rattling: the spirals at full pace, and every
//   RATTLE_EVERY s its whole coat shakes loose a ring of shells, half of them
//   curling each way. Kept open (the user: less clustered).
class Skeljaskrimsli : public Enemy {
    static constexpr float SPEED = 90.0f, SHELL_EVERY = 0.08f, SHELL_SLOW = 0.13f, SHELL_TURN = 0.17f, RATTLE_EVERY = 1.9f;
    static constexpr int   RATTLE_N = 20;
    float shell_t = 0.0f, shell_a = 0.0f, rattle_t = 0.0f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (86x43, drawn 2x about its middle) -> screen
        *ox = x + (fx - 43.0f) * 2.0f; *oy = y + (fy - 21.5f) * 2.0f;
    }
    void mouth(float* ox, float* oy) const { at(42.5f, 27.0f, ox, oy); }   // its glowing mouth; it always faces front (the user)
    // How far phase 1 has built toward phase 2: 0 at full HP, 1 at 66%.
    float build() const { return fminf((1.0f - (float)hp / max_hp) / (1.0f - phase2_at()), 1.0f); }
public:
    Skeljaskrimsli() : Enemy(320, 150, 760, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SKELJASKRIMSLI"; }
    int         breath_frame()  const override { return 2; }       // the mouth glow at its brightest
    float       phase2_at()     const override { return 0.66f; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       fire_interval() const override { return 0.02f; }   // the shells on their own clocks
    void update(float dt, float, float) override { shell_t += dt; rattle_t += dt; }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        float hx, hy;
        at(43.0f, 16.0f, &hx, &hy);                              // its hump
        int arms = build() >= 0.5f ? 2 : 1;
        float every = SHELL_SLOW + (SHELL_EVERY - SHELL_SLOW) * build();
        while (shell_t >= every && n + 2 * arms <= max) {
            // The shells: two spirals off the hump, mirror images.
            shell_t -= every;
            shell_a += SHELL_TURN;
            for (int k = 0; k < arms; k++)
                for (int m = 0; m < 2; m++) {
                    float a = shell_a + k * (TAU / arms) + PI / 2;
                    BulletSpawn b = mk(m ? PI - a : a, SPEED, 2.5f, 5.0f);   // the mirror image about straight down
                    b.from = true; b.ox = hx; b.oy = hy;
                    out[n++] = b;
                }
        }
        if (ENRAGED && rattle_t >= RATTLE_EVERY && n + RATTLE_N <= max) {
            // The rattle: a ring of shells off its coat, half curling each way.
            rattle_t = 0.0f;
            float turn = ernd() * TAU;
            for (int k = 0; k < RATTLE_N; k++) {
                float a = turn + k * (TAU / RATTLE_N);
                BulletSpawn b = mk(a, SPEED * 0.85f, 2.5f, 5.0f);
                b.from = true; b.ox = hx + cosf(a) * 30.0f; b.oy = hy + sinf(a) * 18.0f;
                b.orbit_w = (k & 1) ? 0.35f : -0.35f;
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The glow: two rows of light from its mouth, fanned at the player,
        // the second row in the first's gaps.
        float mx, my;
        mouth(&mx, &my);
        float a = aim_at(mx, my, px, py);
        int fan = 7 + (int)(4.0f * build() + 0.5f), n = 0;   // 7, widening to 11
        for (int r = 0; r < 2; r++)
            for (int k = 0; k < fan - r && n < max; k++) {
                BulletSpawn b = mk(a + (k - (fan - 1 - r) * 0.5f) * 0.14f, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = mx - cosf(a) * r * 14.0f; b.oy = my - sinf(a) * r * 14.0f;
                out[n++] = b;
            }
        return n;
    }
};

// The sermilik ("ice-clad") of Aasiaat, Greenland (A Book of Creatures): an
// enormous and highly dangerous polar bear whose very long fur is completely
// covered with ice, its four paws like lumps of ice. HARD tier, 780 HP,
// ice-blue bullets. BIG sheet (108x59, five idle frames: the back rises, the
// head dips, frosty breath puffs from its mouth at frame 2). It stands its
// ground, always facing front (like the last two, the user's wish). Every
// shot leaves from the part of it that makes it (the user): its frosty
// breath, its frozen fur. Every shot at one pace, SPEED.
// Phase 1:
//   Icicles -- its frozen fur sheds all the while: from each flank of the
//              hem a fan of three streams of icicles (dashes of three shots,
//              gaps between to slip through) swinging slowly side to side, the
//              two flanks mirror images, sweeping the arena like sprinklers.
//   Breath  -- as the breath puffs (idle frame 2), SNOWFLAKES: six-armed
//              flakes of shots opening out of its mouth, spinning, drifting
//              out every way round (the user), one at the player.
//   Drifts  -- snow in the top corners (the user: they were too easy), blown
//              out sideways along the top -- left on the left, right on the
//              right -- and off the walls before it reaches the rest.
// Phase 2 (66% HP, the user) -- the BLIZZARD, so nowhere in the arena is
//   safe (the user): the icicles stop, and snow drives in over the whole
//   arena from the sky -- rows of flakes across its full width every
//   BLIZ_EVERY s, each row shifted along, on a wind that swings slowly from
//   one side to the other -- a moving lattice to weave through; ten flakes
//   on each breath. (The one pattern not from its body: a storm.)
class Sermilik : public Enemy {
    static constexpr float SPEED = 90.0f, ICE_EVERY = 0.09f, FLAKE_R = 16.0f;
    static constexpr float DRIFT_EVERY = 0.3f, DRIFT_W = 280.0f, DRIFT_SLANT = 0.75f;   // SLANT: the user, lower (was 0.6)   // DRIFT_W: how far in from each wall it snows
    static constexpr float BLIZ_EVERY = 0.35f, BLIZ_STEP = 44.0f, WIND_SWING = 0.55f, WIND_PACE = 0.35f;
    static constexpr int   FLAKE_N = 13;                       // six arms of two, and the heart
    float t = 0.0f, ice_t = 0.0f, bliz_t = 0.0f, drift_t = 0.0f;
    int   ice_k = 0, bliz_k = 0, drift_k = 0;

    // A row of snow along the top of the arena from x0 to x1, BLIZ_STEP apart,
    // shifted a golden step along from the last row, flying at `wind`.
    static int snow_row(float x0, float x1, float wind, int& k, BulletSpawn out[], int max) {
        int n = 0;
        float off = fmodf(k++ * BLIZ_STEP * 0.382f, BLIZ_STEP);  // no column repeats soon
        for (float sx = x0 + off; sx < x1 && n < max; sx += BLIZ_STEP) {
            BulletSpawn b = mk(wind, SPEED, 2.5f, 5.0f);
            b.from = true; b.ox = sx; b.oy = ARENA_TOP - 6.0f;
            out[n++] = b;
        }
        return n;
    }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (108x59, drawn 2x about its middle) -> screen
        *ox = x + (fx - 54.0f) * 2.0f; *oy = y + (fy - 29.5f) * 2.0f;
    }
public:
    Sermilik() : Enemy(320, 140, 780, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "SERMILIK"; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       phase2_at()     const override { return 0.66f; }
    float       fire_interval() const override { return 0.02f; }   // the icicles on their own clock
    void update(float dt, float, float) override { t += dt; ice_t += dt; drift_t += dt; if (ENRAGED) bliz_t += dt; }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        if (ENRAGED) {
            // The blizzard: a row of snow across the whole sky (wide enough
            // that the slant still covers the arena), shifted along each row,
            // driven on the swinging wind.
            float wind = PI / 2 + WIND_SWING * sinf(t * WIND_PACE), reach = (ARENA_H - ARENA_TOP) * fabsf(cosf(wind) / sinf(wind));
            while (bliz_t >= BLIZ_EVERY && n + 48 <= max) {
                bliz_t -= BLIZ_EVERY;
                n += snow_row(-reach - BLIZ_STEP, ARENA_W + reach + BLIZ_STEP, wind, bliz_k, out + n, max - n);
            }
            return n;
        }
        while (drift_t >= DRIFT_EVERY && n + 16 <= max) {
            // The drifts: snow along the top by each wall, blown out off it.
            drift_t -= DRIFT_EVERY;
            int r = snow_row(ARENA_W - DRIFT_W, (float)ARENA_W, DRIFT_SLANT, drift_k, out + n, max - n);
            for (int q = 0; q < r && n + r + q < max; q++) {        // the left: the right's exact mirror image
                BulletSpawn b = out[n + q];
                b.ox = ARENA_W - b.ox; b.vx = -b.vx;
                out[n + r + q] = b;
            }
            n += 2 * r;
        }
        float swing = 0.6f, pace = 0.9f;
        while (ice_t >= ICE_EVERY && n + 6 <= max) {
            // The icicles: a fan of three off each flank, swinging, mirrored.
            ice_t -= ICE_EVERY;
            if (ice_k++ % 6 >= 3) continue;                       // in icicles of three: a stream's gaps to slip through
            float w = swing * sinf((t - ice_t) * pace);
            for (int side = 0; side < 2; side++) {
                float hx, hy;
                at(side ? 72.0f : 36.0f, 54.0f, &hx, &hy);
                float mid = PI / 2 + (side ? -0.45f - w : 0.45f + w);   // each fan leans out its own side
                for (int k = -1; k <= 1; k++) {
                    BulletSpawn b = mk(mid + k * 0.35f, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = hx; b.oy = hy;
                    out[n++] = b;
                }
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The breath: snowflakes opening out of its mouth, spinning, drifting
        // out every way (the user), one at the player.
        static float sx[FLAKE_N], sy[FLAKE_N];
        static bool built = false;
        if (!built) {
            built = true;
            sx[0] = sy[0] = 0.0f;
            for (int k = 0; k < 6; k++)
                for (int r = 0; r < 2; r++) {
                    float a = k * (TAU / 6);
                    sx[1 + k * 2 + r] = cosf(a) * FLAKE_R * (r + 1) * 0.5f;
                    sy[1 + k * 2 + r] = sinf(a) * FLAKE_R * (r + 1) * 0.5f;
                }
        }
        float mx, my;
        at(48.5f, 41.0f, &mx, &my);                              // its mouth, where the breath puffs
        float a = aim_at(mx, my, px, py);
        int m = ENRAGED ? 10 : 7, n = 0;
        for (int k = 0; k < m && n + FLAKE_N <= max; k++)                 // every way round, one at the player
            n += shape_shots(mx, my, a + k * (TAU / m), SPEED, (k & 1) ? -2.0f : 2.0f, 0.4f, sx, sy, FLAKE_N, out + n);
        return n;
    }
};

// ── Desert enemies (IDs 21–27) ────────────────────────────────────────────────

// The asp of the medieval bestiaries (A Book of Creatures): a serpent that
// "carries instantaneous death in its fangs" and, to resist the snake
// charmer, presses one ear to the ground and "stops its ears with its tail".
// UPPER tier, 600 HP, venom-red bullets. MEDIUM sheet (frame 1 the tail
// plugging its ear, frame 2 its head up, forked tongue out). Coiled in
// place, it never moves. Every shot leaves from the part of it that makes
// it (the user): its forked tongue, its coils.
// Phase 1:
//   Hiss  -- when its tongue flicks out (idle frame 2) a FORKED stream
//            pours from the tongue's tip at the player for HISS_T s: two
//            snaking lines, swaying opposite ways -- a double helix -- each
//            curve a serpent winding toward you.
//   Fangs -- every FANG_EVERY s its coils loose a ring of 12 fang PAIRS, the
//            ring turned a little each time.
// Phase 2 (half HP): three forked streams, at the player and either side;
//   the fang rings come quicker.
class Asp : public Enemy {
    static constexpr float HISS_T = 0.8f, HISS_EVERY = 0.03f, WIND = 12.0f, SWAY = 0.35f;
    float hiss_t = -1.0f, emit_t = 0.0f, aim = 0.0f, tx = 0.0f, ty = 0.0f;
    float fang_t = 0.0f, fang_turn = 0.0f;
    int   hiss_face = -1;                    // the way it faced at the flick: held till the hiss is done (the user)

    float fang_every() const { return ENRAGED ? 0.9f : 1.3f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (42x35, drawn 2x about its middle) -> screen
        *ox = x + (fx - 21.0f) * 2.0f; *oy = y + (fy - 17.5f) * 2.0f;
    }
    // Its tongue's tip on the hiss frame, by facing (from behind: the top
    // of its head).
    void tongue(float px, float py, float* ox, float* oy) const {
        int f = facing_toward(px - x, py - y);
        float fx = f == FACE_DOWN ? 20.5f : f == FACE_DOWN_RIGHT ? 32.0f : f == FACE_RIGHT ? 37.0f
                 : f == FACE_UP_RIGHT ? 28.0f : f == FACE_UP ? 21.0f : f == FACE_UP_LEFT ? 14.0f
                 : f == FACE_LEFT ? 4.0f : 9.0f;
        float fy = f == FACE_RIGHT || f == FACE_LEFT ? 10.0f
                 : f == FACE_UP || f == FACE_UP_RIGHT || f == FACE_UP_LEFT ? 7.0f : 15.5f;
        at(fx, fy, ox, oy);
    }
public:
    Asp() : Enemy(320, 140, 600, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ASP"; }
    int         breath_frame()  const override { return 2; }       // tongue out
    float       fire_interval() const override { return 0.02f; }   // the hiss and fangs on their own clocks
    int         move_facing()   const override { return hiss_t >= 0.0f ? hiss_face : -1; }
    void update(float dt, float, float) override {
        fang_t += dt;
        if (hiss_t >= 0.0f) { hiss_t += dt; emit_t += dt; if (hiss_t >= HISS_T) hiss_t = -1.0f; }
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        int streams = ENRAGED ? 3 : 1;
        while (hiss_t >= 0.0f && emit_t >= HISS_EVERY && n + 2 * streams <= max) {
            // The hiss: each stream two winding lines, swaying opposite ways.
            emit_t -= HISS_EVERY;
            float w = SWAY * sinf((hiss_t - emit_t) * WIND);
            for (int k = 0; k < streams; k++) {
                float a = aim + (k - (streams - 1) * 0.5f) * 0.7f;
                for (int side = -1; side <= 1; side += 2) {
                    BulletSpawn b = mk(a + side * w, 140.0f, 2.5f, 5.0f);
                    b.from = true; b.ox = tx; b.oy = ty;
                    out[n++] = b;
                }
            }
        }
        if (fang_t >= fang_every() && n + 24 <= max) {
            // Fangs: a ring of 12 pairs from its coils, turning on each time.
            fang_t = 0.0f;
            fang_turn += 0.13f;
            float cx, cy;
            at(21.0f, 28.0f, &cx, &cy);
            for (int i = 0; i < 12; i++)
                for (int side = -1; side <= 1; side += 2) {
                    BulletSpawn b = mk(fang_turn + i * (TAU / 12) + side * 0.05f, 100.0f, 3.0f, 5.0f);
                    b.from = true; b.ox = cx; b.oy = cy;
                    out[n++] = b;
                }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn[], int) override {
        // The tongue flicks out: the hiss pours from its tip, aimed now.
        tongue(px, py, &tx, &ty);
        hiss_face = facing_toward(px - x, py - y);
        aim = aim_at(tx, ty, px, py);
        hiss_t = 0.0f; emit_t = HISS_EVERY;
        return 0;
    }
};

// The cactus cat of the American Southwest (Fearsome Creatures): bobcat-like,
// covered in hair-like thorns, with an armoured, branching tail and bone
// blades on its forelegs; it slashes the cacti, then comes back to drink the
// fermented sap and wanders drunk. UPPER tier, 620 HP, thorn-pale bullets.
// MEDIUM sheet. It stays put (the user).
// The pattern (the user, from a Touhou reference): it gathers RINGS of
// PRICKLY-PEAR PADS round itself -- one ring after another sweeping out of
// it to its place, each pad lying along its ring, the rings turning, every
// other one the other way, a great rosette -- dangerous as it forms -- holds
// them a beat, then FIRES THEM ALL at the player at once.
// And all the while SPINES fly from its coat in a symmetrical lattice: two
// four-armed spirals turning opposite ways, every spine HOMING for a moment
// as it leaves (the user) -- the arms bend toward the player.
// Phase 2 (half HP): a fourth ring, quicker cycles, five-armed spirals.
class CactusCat : public Enemy {
    static constexpr int   RINGS = 3;
    static constexpr int   RING_PADS[4] = { 6, 9, 12, 15 };   // much easier (the user): fewer pads
    static constexpr float RING_R[4] = { 55.0f, 90.0f, 125.0f, 160.0f };
    static constexpr float RING_GAP = 0.3f, FORM_T = 0.5f, HOLD = 0.8f, SPEED = 90.0f, RING_SPIN = 0.6f;
    static constexpr float SPINE_EVERY = 0.22f, SPINE_TURN = 0.2f, SPINE_SPEED = 75.0f, SPINE_HOME_T = 0.4f;   // much easier: sparse, slow, a brief bend
    float t = 0.0f, spine_t = 0.0f, spine_a = 0.0f;
    int   next_ring = 0;

    int   rings() const { return ENRAGED ? 4 : RINGS; }
    float cycle() const { return ENRAGED ? 3.4f : 4.4f; }
    float launch_at() const { return (rings() - 1) * RING_GAP + FORM_T + HOLD; }   // every pad leaves together
public:
    CactusCat() : Enemy(320, 140, 620, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "CACTUS CAT"; }
    float       fire_interval() const override { return 0.02f; }   // rings and spines on their own clocks
    void update(float dt, float, float) override {
        spine_t += dt;
        if ((t += dt) >= cycle()) { t = 0.0f; next_ring = 0; }
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        while (next_ring < rings() && t >= next_ring * RING_GAP) {
            // The next ring of pads sweeps out of it: every thorn of every pad
            // (six to an oval lying along the ring) eases out from its middle
            // to its place in FORM_T s, the ring turning, waiting -- then all
            // of them, every ring, dart at the player together.
            int r = next_ring++, pads = RING_PADS[r];
            float turn = r * 0.35f, spin = (r & 1) ? -RING_SPIN : RING_SPIN;
            for (int k = 0; k < pads && n + 6 <= max; k++) {
                float a = turn + k * (TAU / pads), ux = cosf(a), uy = sinf(a), vx = -uy, vy = ux;
                for (int q = 0; q < 6; q++) {
                    float c = q * (TAU / 6), along = cosf(c) * 10.0f, out_ = sinf(c) * 5.0f;
                    float sx = ux * (RING_R[r] + out_) + vx * along, sy = uy * (RING_R[r] + out_) + vy * along;
                    float rr = hypotf(sx, sy), v0 = 2.0f * rr / FORM_T;
                    BulletSpawn b = mk(atan2f(sy, sx), v0, 2.5f, 5.0f);
                    b.from = true; b.ox = x; b.oy = y;
                    b.accel = -v0 / FORM_T; b.min_speed = 0.01f;
                    b.orbit_w = spin;
                    b.delay = launch_at() - t; b.launch_speed = SPEED; b.launch_off = 0.0f;
                    out[n++] = b;
                }
            }
        }
        // The spines: two spirals off its coat, turning opposite ways.
        int arms = ENRAGED ? 5 : 4;
        while (spine_t >= SPINE_EVERY && n + 2 * arms <= max) {
            spine_t -= SPINE_EVERY;
            spine_a += SPINE_TURN;
            for (int k = 0; k < arms; k++) {
                out[n++] = mk( spine_a + k * (TAU / arms), SPINE_SPEED, 2.5f, 5.0f);
                out[n++] = mk(-spine_a + k * (TAU / arms) + PI / arms, SPINE_SPEED, 2.5f, 5.0f);
            }
            for (int q = n - 2 * arms; q < n; q++) { out[q].homing = true; out[q].homing_timer = SPINE_HOME_T; }   // every spine homes (the user), a moment
        }
        return n;
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

// The zoureg (de Plancy's Dictionnaire Infernal): a snake a foot long of the
// Arabian desert that goes through rocks, trees, walls and bodies "like a
// hot knife through butter". UPPER tier, 640 HP, molten-orange bullets.
// MEDIUM sheet: a red-hot knife of a snake (frame 1 its head drawn back,
// glowing hotter; frame 2 the thrust). Its shots leave from the part of it
// that makes them (the user): the white-hot line it cuts.
// The pattern: it coils and DRAWS BACK, glowing hotter (frame 1) -- the only
// warning (the user: no line, its sprite signals it), AIM_T s -- fixed on
// where the player is, then THRUSTS (frame 2) straight there, right across
// to the far wall: it shoots down
// the line to the wall, touching it hurts, the cut FORMING behind it as it
// goes -- a white-hot laser (the user) -- and the moment it stops the cut
// dissipates, spitting EMBERS to both sides, a step apart all along it. It
// rests a beat where it stopped, and again.
// Phase 2 (half HP) -- it glides back to the middle, rears its head up, and
//   three LASERS form out of its three heads (the user), each time shooting
//   out a different way, then sweeping round to ENCLOSE where
//   the player is: two close in from either side like a pair of shears,
//   stopping just short of each other -- the gap opens a little off where the
//   player stood when they formed (read where they meet) -- while the third
//   circles round behind, and molten spit flies from its head at the player
//   as they close: sidestep inside the gap.
class Zoureg : public Enemy {
    enum State { REST, AIM, THRUST, HOME, SHEARS };
    static constexpr float AIM_T = 0.6f, THRUST_SPEED = 1100.0f, FADE_T = 0.35f, REST_T = 1.0f;
    static constexpr float EMBER_SPEED = 70.0f;
    static constexpr float BELLY = (26.0f - 14.5f) * 2.0f;   // its coil's underside, art y 26 in the 29-tall frame: what it slides on
    State state = REST;
    float t = 0.0f;
    float sx = 0, sy = 0, ex = 0, ey = 0;   // the line: where it set off, where it stops
    float cut = -1.0f;                       // seconds the cut has been dissipating (-1 = none)
    float cx0 = 0, cy0 = 0, cx1 = 0, cy1 = 0;   // the cut line, latched as it was cut
    int   thrusts_left = 0;
    bool  embers = false;
    // Phase 2's shears: the cycle clock and the aim they close on.
    static constexpr float HOME_X = 320.0f, HOME_Y = 170.0f, HOME_SPEED = 300.0f;
    static constexpr float S_GROW = 0.5f, S_CLOSE = 1.6f, S_FADE = 0.3f, S_REST = 0.4f;
    static constexpr float S_OPEN = 1.3f, S_GAP_PX = 40.0f;   // S_OPEN: how far the third beam circles   // the shears open this wide, and close to a gap this wide (centre to centre) at the player's distance -- thin (the user), the same wherever they stand
    static constexpr float S_SHIFT = 0.2f, SPIT_EVERY = 0.25f;  // the gap's shift off the player; spit from its head while the shears close
    float spit_t = 0.0f, bob_t = 0.0f;
    float shear_t = 0.0f, shear_aim = 0.0f;
    float shx[3] = {}, shy[3] = {}, shear_end[2] = {};   // this volley's heads, and the angles the two shear beams close to
    float shear_start[3] = {};                            // ...and the random ways they shoot out first (the user)
    void shear_origin(float* ox, float* oy) const { *ox = x; *oy = y - 12.0f; }   // its head, reared up (aiming)
    // Its three heads' needle tips on the three-headed sheet (60x35, drawn 2x
    // with its bottom on the idle frame's: art (c, r) -> (x + 2c - 60,
    // y - 41 + 2r)) -- the front drawing in every facing (the user), so the
    // same everywhere: [0] the screen-right head, [1] the screen-left, [2] the
    // middle one.
    // The tips bob with the sheet's frames, which it plays itself while the
    // shears are out (three_frame), so each laser stays on its tip; art
    // pixel centres (+0.5).
    int three_frame() const { static const int LOOP[4] = { 0, 1, 0, 2 }; return LOOP[(int)(bob_t / 0.25f) & 3]; }
    void heads(float, float, float hx[3], float hy[3]) const {
        static const float RY[3] = { 7, 6, 8 }, LY[3] = { 7, 8, 6 }, MY[3] = { 3, 2, 4 };   // [frame]: its L (screen right), its R, the middle
        int f = three_frame();
        hx[0] = x + 2.0f * 43.5f - 60.0f; hy[0] = y - 41.0f + 2.0f * (RY[f] + 0.5f);
        hx[1] = x + 2.0f * 17.5f - 60.0f; hy[1] = y - 41.0f + 2.0f * (LY[f] + 0.5f);
        hx[2] = x + 2.0f * 30.5f - 60.0f; hy[2] = y - 41.0f + 2.0f * (MY[f] + 0.5f);
    }

    void aim(float px, float py) {
        // Straight at the player, to 40 px short of the far wall.
        state = AIM; t = 0.0f; sx = x; sy = y;
        float a = aim_at(x, y, px, py), dx = cosf(a), dy = sinf(a), reach = 1e9f;
        if (dx > 1e-3f)  reach = fminf(reach, (ARENA_W - 40.0f - x) / dx);
        if (dx < -1e-3f) reach = fminf(reach, (40.0f - x) / dx);
        if (dy > 1e-3f)  reach = fminf(reach, (ARENA_H - 40.0f - y) / dy);
        if (dy < -1e-3f) reach = fminf(reach, (ARENA_TOP + 40.0f - y) / dy);
        reach = fmaxf(reach, 0.0f);
        ex = x + dx * reach; ey = y + dy * reach;
    }
public:
    Zoureg() : Enemy(320, 140, 640, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "ZOUREG"; }
    float       fire_interval() const override { return 0.02f; }   // the embers as the cut dissipates
    float       contact_damage() const override { return state == THRUST ? 5.0f : 0.0f; }
    int   anim_frame()  const override { return state == AIM ? 1 : state == THRUST ? 2 : state == SHEARS ? three_frame() : -1; }
    bool  alt_pose()    const override { return state == SHEARS; }   // three-headed (24_zoureg_three, from art), a laser from each head
    int   move_facing() const override { return state == AIM || state == THRUST ? facing_toward(ex - sx, ey - sy) : -1; }
    int telegraphs(TeleLine out[], int max) const override {
        int n = 0;
        if (state == SHEARS && max >= 3) {
            // The shears: growing out harmless, then hot as two close on the
            // aim from either side (to a gap S_GAP_PX wide) and the third
            // circles round behind; then fading.
            const float* hx = shx; const float* hy = shy;      // a laser out of each head (the user), latched for the volley
            float k = fminf(shear_t / S_GROW, 1.0f); k = 1.0f - (1.0f - k) * (1.0f - k);
            float c = fminf(fmaxf((shear_t - S_GROW) / S_CLOSE, 0.0f), 1.0f);   // how far they've closed
            float ang[3] = { shear_start[0] + (shear_end[0] - shear_start[0]) * c,
                             shear_start[1] + (shear_end[1] - shear_start[1]) * c,
                             shear_start[2] + c * S_OPEN };
            bool fading = shear_t >= S_GROW + S_CLOSE;
            float fade = fading ? fminf((shear_t - S_GROW - S_CLOSE) / S_FADE, 1.0f) : 0.0f;
            for (int b = 0; b < 3; b++) {
                TeleLine L{ hx[b], hy[b], hx[b] + cosf(ang[b]) * 800.0f * k, hy[b] + sinf(ang[b]) * 800.0f * k };
                L.stage = shear_t < S_GROW ? 0 : fading ? 2 : 1;
                L.fade = fade;
                L.hurt_w = (L.stage == 1 || (L.stage == 2 && fade < 0.33f)) ? 5.0f : 0.0f;
                out[n++] = L;
            }
        }
        if (state == THRUST && max > n) {                        // the cut FORMING behind it as it shoots along (the user): white-hot
            TeleLine L{ sx, sy + BELLY, x, y + BELLY };            // under it: it runs on its sluggish belly (the user)
            L.stage = 1; L.hurt_w = 5.0f;
            out[n++] = L;
        }
        if (cut >= 0.0f && max > n) {                            // ...and dissipating once it has stopped
            TeleLine L{ cx0, cy0, cx1, cy1 };
            L.stage = 2;
            L.fade = fminf(cut / FADE_T, 1.0f);
            L.hurt_w = L.fade < 0.33f ? 5.0f : 0.0f;
            out[n++] = L;
        }
        return n;
    }
    void update(float dt, float px, float py) override {
        t += dt;
        if (ENRAGED && (state == REST || state == AIM)) state = HOME;   // phase 2: back to the middle
        if (state == HOME) {
            float dx = HOME_X - x, dy = HOME_Y - y, d = hypotf(dx, dy), st = HOME_SPEED * dt;
            if (d > st) { x += dx / d * st; y += dy / d * st; }
            else { x = HOME_X; y = HOME_Y; state = SHEARS; shear_t = S_GROW + S_CLOSE + S_FADE + S_REST; }
        }
        if (state == SHEARS) {
            spit_t += dt; bob_t += dt;
            heads(px, py, shx, shy);                             // the lasers ride the tips as they bob
            if ((shear_t += dt) >= S_GROW + S_CLOSE + S_FADE + S_REST) {   // the next pair of shears, on where the player is now
                float ox, oy;
                shear_origin(&ox, &oy);
                shear_t = 0.0f; shear_aim = aim_at(ox, oy, px, py) + (ernd() * 2.0f - 1.0f) * S_SHIFT;   // the gap opens a little off where they stand: read where
                // Each shear beam closes to pass S_GAP_PX/2 either side of the
                // gap's middle at the player's distance -- worked out from its
                // own head, so the gap is the same width at any facing and
                // range (the tester: a fixed angle shut it toward the corners).
                heads(px, py, shx, shy);
                // They shoot out each time a different way (the user): the two
                // shears opened a random width, 0.7-2.0 rad, but the SAME either
                // side of the gap, so where they'll meet reads from the first
                // frame (the tester: uneven widths hid the gap); the third
                // anywhere its circle (S_OPEN round) keeps 0.6 rad clear of the
                // gap -- it must never sweep over the player.
                float w = 0.7f + ernd() * 1.3f;
                shear_start[0] = shear_aim - w;
                shear_start[1] = shear_aim + w;
                shear_start[2] = shear_aim + 0.6f + ernd() * (TAU - 1.2f - S_OPEN);
                float d = hypotf(px - ox, py - oy), gx = ox + cosf(shear_aim) * d, gy = oy + sinf(shear_aim) * d;
                for (int b = 0; b < 2; b++) {
                    float side = b ? 1.0f : -1.0f;                // beam 0 closes from aim - open, beam 1 from aim + open
                    float tx = gx + cosf(shear_aim + side * PI / 2) * S_GAP_PX * 0.5f, ty = gy + sinf(shear_aim + side * PI / 2) * S_GAP_PX * 0.5f;
                    float e = atan2f(ty - shy[b], tx - shx[b]);
                    shear_end[b] = shear_aim + remainderf(e - shear_aim, TAU);   // the same turn as the aim, so it closes the short way
                }
            }
        }
        if (cut >= 0.0f) {
            cut += dt;
            if (cut >= FADE_T) cut = -1.0f;
        }
        switch (state) {
        case REST:
            if (t >= REST_T) { if (thrusts_left <= 0) thrusts_left = ENRAGED ? 2 : 1; aim(px, py); }
            break;
        case AIM:
            if (t >= AIM_T) { state = THRUST; t = 0.0f; }
            break;
        case THRUST: {
            float dx = ex - x, dy = ey - y, d = hypotf(dx, dy), st = THRUST_SPEED * dt;
            if (d > st) { x += dx / d * st; y += dy / d * st; break; }
            x = ex; y = ey;
            cx0 = sx; cy0 = sy + BELLY; cx1 = ex; cy1 = ey + BELLY; cut = 0.0f;   // there: the cut dissipates, spitting embers
            embers = true;
            // Phase 2: again -- once the cut has cooled past hurting, so the
            // new line never makes you cross a hot one (the tester).
            state = REST;
            t = --thrusts_left > 0 ? REST_T - FADE_T * 0.34f : 0.0f;
            break;
        }
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        if (state == SHEARS) {
            // While the shears close, molten spit from its head at the player:
            // three, fanned -- sidestep inside the gap.
            bool closing = shear_t >= S_GROW && shear_t < S_GROW + S_CLOSE;
            if (!closing || spit_t < SPIT_EVERY || max < 3) return 0;
            spit_t = 0.0f;
            float ox, oy;
            shear_origin(&ox, &oy);
            float a = aim_at(ox, oy, px, py);
            for (int k = -1; k <= 1; k++) {
                BulletSpawn b = mk(a + k * 0.12f, 95.0f, 2.5f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                out[k + 1] = b;
            }
            return 3;
        }
        if (!embers) return 0;
        embers = false;
        // Embers off the cooling cut: a pair every step along it, out to
        // both sides.
        float dx = cx1 - cx0, dy = cy1 - cy0, len = hypotf(dx, dy);
        if (len < 1.0f) return 0;
        float ux = dx / len, uy = dy / len, a = atan2f(uy, ux);
        float step = ENRAGED ? 24.0f : 32.0f;
        int n = 0;
        for (float d = step * 0.5f; d < len && n + 2 <= max; d += step) {
            float ox = cx0 + ux * d, oy = cy0 + uy * d;
            if (hypotf(px - ox, py - oy) < 60.0f) continue;      // none beside a player who only just stepped clear (the tester)
            for (int side = -1; side <= 1; side += 2) {
                BulletSpawn b = mk(a + side * PI / 2, EMBER_SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy; b.flash_in = true;
                out[n++] = b;
            }
        }
        return n;
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

// The akhekh of Egyptian art (A Book of Creatures): an antelope with bird's
// wings and a falcon's head crowned with three uraei -- the royal cobras,
// each with its sun disc -- and sometimes a serpent's tail; a creature of the
// desert's edge, an ally of Set. UPPER tier, 650 HP, sun-gold bullets. MEDIUM
// sheet (frame 1 the wings raised, frame 2 the downstroke). It hangs still in
// the air at the top. Every shot at one pace, SPEED.
// Round it always turns a SHIELD (the user): a ring of SHIELD_N shots
// spinning at SHIELD_R, and every pattern flies out of that ring --
// Phase 1:
//   Uraei -- three arms of fire wheeling out of the ring, turning with it --
//            a sun's rays.
//   Wings -- every downstroke (idle frame 2) a fan of feathers off each side
//            of the ring, curling in toward each other as they fly, mirror
//            images: a pair of wings drawn in shots.
// Phase 2 (half HP) -- Set's sandstorm: three more arms wheeling the other
//   way (the rays cross), wider wing fans, and every SAND_EVERY s a ring of
//   sand spiralling off the whole shield.
class Akhekh : public Enemy {
    static constexpr float SPEED = 100.0f, ARM_EVERY = 0.05f, SAND_EVERY = 1.5f;
    static constexpr float SHIELD_R = 60.0f, SHIELD_W = 0.92f, SHIELD_FORM = 0.8f;   // the arms leave from it, so they wheel at its pace
    static constexpr int   SHIELD_N = 24;
    float arm_t = 0.0f, sand_t = 0.0f, t = 0.0f;
    bool  shield_out = false;

    float spin() const { return t * SHIELD_W; }              // the shield's turn now
    void  on_ring(float a, float* ox, float* oy, float r = SHIELD_R) const { *ox = x + cosf(a) * r; *oy = y + sinf(a) * r; }
    static constexpr float ARM_R = 20.0f;   // the arms start inside the shield and pass out through it: no safe spot just outside it (the tester)
public:
    Akhekh() : Enemy(320, 130, 650, {0.5f,0.5f,0.75f,0.5f,1.5f,1.0f,1.5f}) {}
    const char* name()          const override { return "AKHEKH"; }
    int         breath_frame()  const override { return 2; }       // the downstroke
    float       fire_interval() const override { return 0.02f; }   // the shield, arms and sand on their own clocks
    void update(float dt, float, float) override { t += dt; arm_t += dt; sand_t += dt; }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (!shield_out && max >= SHIELD_N) {
            // The shield: a ring opening out of it to SHIELD_R and spinning
            // there for the whole fight.
            shield_out = true;
            for (int k = 0; k < SHIELD_N; k++) {
                float v0 = 2.0f * SHIELD_R / SHIELD_FORM;
                BulletSpawn b = mk(k * (TAU / SHIELD_N), v0, 3.0f, 5.0f);
                b.accel = -v0 / SHIELD_FORM; b.min_speed = 0.01f;
                b.orbit_w = SHIELD_W;
                out[n++] = b;
            }
        }
        while (arm_t >= ARM_EVERY && n + 6 <= max) {
            // The uraei: three arms leaving the shield, wheeling with it (in
            // phase 2 three more the other way).
            arm_t -= ARM_EVERY;
            for (int k = 0; k < 3; k++) {
                float a = spin() + k * (TAU / 3), ox, oy;
                on_ring(a, &ox, &oy, ARM_R);
                BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                out[n++] = b;
                if (ENRAGED) {
                    float c = -spin() + k * (TAU / 3) + PI / 3;
                    on_ring(c, &ox, &oy, ARM_R);
                    BulletSpawn e = mk(c, SPEED, 2.5f, 5.0f);
                    e.from = true; e.ox = ox; e.oy = oy;
                    out[n++] = e;
                }
            }
        }
        if (ENRAGED && sand_t >= SAND_EVERY && n + SHIELD_N <= max) {
            // Set's sand: off every shot of the shield, spiralling out.
            sand_t = 0.0f;
            for (int k = 0; k < SHIELD_N; k++) {
                float a = spin() + k * (TAU / SHIELD_N), ox, oy;
                on_ring(a, &ox, &oy);
                BulletSpawn b = mk(a, SPEED * 0.8f, 2.5f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                b.orbit_w = 0.7f;
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The downstroke: a fan of feathers off each side of the shield,
        // curling in toward each other -- mirror images.
        int fan = ENRAGED ? 13 : 9, n = 0;
        float down = aim_at(x, y, px, py), lx, ly, rx, ry;
        on_ring(down + PI / 2, &lx, &ly);                        // the shield's left and right of the player's line
        on_ring(down - PI / 2, &rx, &ry);
        for (int k = 0; k < fan && n + 2 <= max; k++) {
            float off = (k - (fan - 1) * 0.5f) * 0.12f;
            BulletSpawn l = mk(down + 0.25f + off, SPEED * 1.1f, 2.5f, 5.0f);  // the left wing's fan, leaning just left of the player
            l.from = true; l.ox = lx; l.oy = ly; l.orbit_w = 0.45f;           // ...curling in (clockwise: back toward the middle)
            BulletSpawn r = mk(down - 0.25f - off, SPEED * 1.1f, 2.5f, 5.0f);
            r.from = true; r.ox = rx; r.oy = ry; r.orbit_w = -0.45f;
            out[n++] = l; out[n++] = r;
        }
        return n;
    }
};

// The grootslang ("great snake") of South Africa (A Book of Creatures): an
// enormous serpent with an elephant's head, made in the first days when the
// gods were still learning; it lurks in a bottomless cave said to be full of
// diamonds, and lures elephants -- and people -- to their deaths. HARD tier,
// 800 HP, diamond-white bullets. BIG sheet (98x65, five idle frames: the trunk
// sways, the ears fan, the rattle shakes). Coiled in its mound, always facing
// front. Every shot leaves from the part of it that makes it (the user): its
// tusks, its trunk, its rattle. Every shot at one pace, SPEED.
// Phase 1:
//   Tusks    -- off each tusk tip all the while, a stream sweeping slowly to
//               and fro, curling in toward the middle as it flies -- the two
//               mirror images, tusk-curved arcs crossing; in dashes of three.
//   Diamonds -- as the trunk swings (idle frame 2) it SWEEPS out DIAMONDS
//               from its cave (the user): diamond outlines of shots opening
//               out of the trunk's tip one after another, the throw sweeping
//               across the arena below -- left to right, then back the next
//               time -- each turning slowly as it flies.
// Phase 2 (half HP) -- the rattle: its rattlesnake tail buzzes a three-armed
//   spiral off its tip all the while, and the sweeps throw more diamonds.
class Grootslang : public Enemy {
    static constexpr float SPEED = 95.0f, TUSK_EVERY = 0.08f, SWEEP = 0.6f, SWEEP_PACE = 1.1f, CURL = 0.5f;
    static constexpr float RATTLE_EVERY = 0.07f, RATTLE_TURN = 0.29f, GEM_R = 18.0f, GEM_EVERY = 0.13f, GEM_ARC = 1.3f;   // GEM_ARC: the sweep swings this far either side of straight down
    static constexpr int   GEM_N = 16;                         // a diamond: 4 corners, 3 shots along each side
    float t = 0.0f, tusk_t = 0.0f, rattle_t = 0.0f, rattle_a = 0.0f;
    int   tusk_k = 0, gem_left = 0, gem_of = 0, sweeps = 0;
    float gem_t = 0.0f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
public:
    Grootslang() : Enemy(320, 150, 800, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
    const char* name()          const override { return "GROOTSLANG"; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       fire_interval() const override { return 0.02f; }   // the tusks and the rattle on their own clocks
    void update(float dt, float, float) override { t += dt; tusk_t += dt; gem_t += dt; if (ENRAGED) rattle_t += dt; }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        while (tusk_t >= TUSK_EVERY && n + 2 <= max) {
            // The tusks: a sweeping stream off each tip, curling in, mirrored.
            tusk_t -= TUSK_EVERY;
            if (tusk_k++ % 6 >= 3) continue;                       // in dashes of three: gaps to slip through
            float w = SWEEP * sinf((t - tusk_t) * SWEEP_PACE);
            for (int side = 0; side < 2; side++) {
                float tx, ty;
                at(side ? 60.0f : 37.0f, 34.0f, &tx, &ty);
                float a = PI / 2 + (side ? -0.6f - w : 0.6f + w);  // leaning out its own side...
                BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = tx; b.oy = ty;
                b.orbit_w = side ? CURL : -CURL;                   // ...curling back in, like a tusk
                out[n++] = b;
            }
        }
        if (gem_left > 0 && gem_t >= GEM_EVERY && n + GEM_N <= max) {
            // The diamonds: one more out of the trunk's tip, the throw
            // sweeping across below (back the other way each sweep).
            static float sx[GEM_N], sy[GEM_N];
            static bool built = false;
            if (!built) { built = true; gem_points(GEM_R, sx, sy); }
            gem_t = 0.0f;
            float f = (gem_of - gem_left--) / (float)(gem_of - 1);   // 0 .. 1 along the sweep
            if (sweeps & 1) f = 1.0f - f;
            float mx, my;
            at(48.5f, 47.0f, &mx, &my);                          // the trunk's tip
            n += shape_shots(mx, my, PI / 2 + GEM_ARC * (1.0f - 2.0f * f), SPEED, (gem_left & 1) ? -1.0f : 1.0f, 0.45f, sx, sy, GEM_N, out + n);
        }
        if (ENRAGED) {
            float rx, ry;
            at(80.0f, 8.0f, &rx, &ry);                           // the rattle's tip
            while (rattle_t >= RATTLE_EVERY && n + 3 <= max) {
                // The rattle: a three-armed spiral buzzing off its tail.
                rattle_t -= RATTLE_EVERY;
                rattle_a += RATTLE_TURN;
                for (int k = 0; k < 3; k++) {
                    BulletSpawn b = mk(rattle_a + k * (TAU / 3), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = rx; b.oy = ry;
                    out[n++] = b;
                }
            }
        }
        return n;
    }
    int breathe(float, float, BulletSpawn[], int) override {
        // The trunk swings: a sweep of diamonds begins (fire() throws them).
        gem_of = gem_left = ENRAGED ? 9 : 7;
        gem_t = GEM_EVERY;
        sweeps++;
        return 0;
    }
};

// ── Wasteland enemies (IDs 28–34) ─────────────────────────────────────────────

// The opimachus ("snake-fighter") of the medieval encyclopedias (A Book of
// Creatures): small and weak beside a serpent but bold and skilled, it wins
// by latching on just below the snake's head; by the Ortus Sanitatis a small
// four-legged griffin with a long pointed beak and big rabbit's ears. UPPER
// tier, 640 HP, gold bullets. MEDIUM sheet (frame 1 the ears flick and the
// wings lift, frame 2 the beak jabs). It stands its ground. Every shot at one
// pace, SPEED.
// Phase 1 -- the easier half (the user):
//   Peck -- as it pecks (idle frame 2) rings of small shots burst from the
//           centre of its body: three rings, packed tight, each turned on
//           from the last and turning as they spread -- curling chains.
//   Ears -- the ears flick (idle frame 1): a ring of 8 off each ear tip, the
//           two rings half a step apart.
// Phase 2 (half HP) -- the full pattern: five rings a peck, every other peck
//   curling the other way; ear rings of 12.
class Opimachus : public Enemy {
    static constexpr float SPEED = 100.0f;
    float t = 0.0f;
    static constexpr int   PECK_N = 36;
    static constexpr float PECK_SPIN = 0.25f;  // the rings' turn as they spread: slow enough to adjust to (the user; was 0.5)
    static constexpr float PECK_GAP = 0.16f;   // between rings: ~16 px apart as they spread (the user: wider)
    int   rings_left = 0, pecks = 0;
    float ring_t = 0.0f, ring_turn = 0.0f, ring_spin = PECK_SPIN, rx_ = 0.0f, ry_ = 0.0f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (50x39, drawn 2x about its middle) -> screen
        *ox = x + (fx - 25.0f) * 2.0f; *oy = y + (fy - 19.5f) * 2.0f;
    }
public:
    Opimachus() : Enemy(320, 140, 640, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "OPIMACHUS"; }
    float       fire_interval() const override { return 0.02f; }   // the peck's rings on their own clock
    void update(float dt, float, float) override { t += dt; ring_t += dt; }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        while (rings_left > 0 && ring_t >= PECK_GAP && n + PECK_N <= max) {
            // The peck's rings: small balls packed tight, each ring turned on a
            // step, all turning as they spread -- curling chains.
            ring_t -= PECK_GAP; rings_left--;
            ring_turn += 0.06f;
            for (int k = 0; k < PECK_N; k++) {
                BulletSpawn b = mk(ring_turn + k * (TAU / PECK_N), SPEED, 3.0f, 5.0f);   // small (the user)
                b.from = true; b.ox = rx_; b.oy = ry_;
                b.orbit_w = ring_spin;
                out[n++] = b;
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (frame == 2) {
            // The peck: rings start bursting from the centre of its body (the user).
            rx_ = x; ry_ = y;
            rings_left = ENRAGED ? 5 : 3; ring_t = PECK_GAP;
            ring_turn = ernd() * TAU;
            ring_spin = (ENRAGED && (pecks & 1)) ? -PECK_SPIN : PECK_SPIN;
            pecks++;
        } else if (frame == 1) {
            // The ears flick: a ring off each ear tip, half a step apart
            // (phase 1 a lighter ring).
            float ex[2], ey[2], turn = ernd() * TAU;
            at(20.0f, 5.0f, &ex[0], &ey[0]); at(29.0f, 5.0f, &ex[1], &ey[1]);
            for (int e = 0; e < 2; e++)
                for (int k = 0, m = ENRAGED ? 12 : 8; k < m && n < max; k++) {
                    BulletSpawn b = mk(turn + (k + e * 0.5f) * (TAU / m), SPEED * 0.85f, 2.5f, 5.0f);
                    b.from = true; b.ox = ex[e]; b.oy = ey[e];
                    out[n++] = b;
                }
        }
        return n;
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

// The Tse'nagahi ("Traveling Rock") of Navajo lore (A Book of Creatures):
// one of the monsters the Hero Twins slew -- a rock that rolled after
// travelers to crush them. HARD tier, 800 HP, sandstone bullets. MEDIUM sheet
// (46x43: frame 1 rolled forward, frame 2 back), a faceted mass of banded red
// sandstone carved with petroglyphs -- spiral eyes, a zigzag mouth, a sun on
// its back. No legs: it ROLLS. Every shot leaves from the part of it that
// makes it (the user): its grinding body, its carved eyes, its sun. Every
// shot at one pace, SPEED. Nothing is thrown within CLEAR of the player.
// Phase 1 -- it sits still where it is (the user: no shaking), spewing
//   everywhere:
//   Grit    -- a five-armed spiral of grit off its edge all the while, in
//              dashes, turning.
//   Glyphs  -- every GLYPH_EVERY s its spiral eyes fling their petroglyphs:
//              SPIRALS of shots opening out of it every way round (one at the
//              player), spinning as they fly.
//   Crash   -- halfway between, it judders down: a ring of chips off its base.
// Phase 2 (half HP) -- it breaks loose and ROLLS after you: a run THROUGH
//   where you stood and on past (it crushes on touch), then it settles a
//   beat, and rolls again (kept gentle, the user); grit pairs off both flanks as it grinds along, and
//   each landing throws the chips, a spiral from each eye at you, and a ring
//   of rays off the sun on its back.
class TsenaGahi : public Enemy {
    static constexpr float SPEED = 90.0f, ROLL = 190.0f, SETTLE = 1.2f, GRIT_EVERY = 0.1f,   // phase 2 eased (the user: too hard; was 240, 0.8, 0.07)
                           CLEAR = 60.0f, GLYPH_CLEAR = 150.0f, OVERSHOOT = 160.0f;
    static constexpr float SPIN_EVERY = 0.06f, SPIN_TURN = 0.21f, GLYPH_EVERY = 1.8f;
    static constexpr int   GLYPH_N = 20, SUN_N = 16, CHIP_N = 22, LAND_CHIP_N = 16;
    enum State { SITTING, SETTLED, ROLLING };
    State state = SITTING;
    float rest = 0.0f, tx = 320.0f, ty = 160.0f, rx = 0.0f, ry = 1.0f, grit_t = 0.0f, spin_a = 0.0f, glyph_t = 0.0f;
    int   spin_k = 0;
    bool  landed = false, crashed = false;                     // just settled / juddered: fire() throws

    // A petroglyph spiral opening out of (ox, oy) along a, spinning `spin`.
    static int glyph(float ox, float oy, float a, float spin, BulletSpawn out[]) {
        static float sx[GLYPH_N], sy[GLYPH_N];
        static bool built = false;
        if (!built) {
            built = true;
            for (int k = 0; k < GLYPH_N; k++) {
                float f = k / (float)(GLYPH_N - 1), g = f * 3.5f * PI, r = 4.0f + 32.0f * f;
                sx[k] = cosf(g) * r; sy[k] = sinf(g) * r;
            }
        }
        return shape_shots(ox, oy, a, SPEED, spin, 0.5f, sx, sy, GLYPH_N, out);
    }
    // A ring of m shots off an ellipse (rw x rh) about (cx, cy).
    static int ring(float cx, float cy, float rw, float rh, int m, BulletSpawn out[]) {
        float turn = ernd() * TAU;
        for (int k = 0; k < m; k++) {
            float r = turn + k * (TAU / m);
            BulletSpawn b = mk(r, SPEED, 2.5f, 5.0f);
            b.from = true; b.ox = cx + cosf(r) * rw; b.oy = cy + sinf(r) * rh;
            out[k] = b;
        }
        return m;
    }
public:
    TsenaGahi() : Enemy(320, 160, 800, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()           const override { return "TSE'NAGAHI"; }
    float       fire_interval()  const override { return 0.02f; }   // everything on its own clock
    float       contact_damage() const override { return state == ROLLING ? 5.0f : 0.0f; }   // it crushes
    float       anim_speed()     const override { return state == ROLLING ? 4.0f : 1.0f; }    // tumbling over and over
    int         move_facing()    const override { return state == ROLLING ? facing_toward(rx, ry) : state == SITTING ? FACE_DOWN : -1; }
    void update(float dt, float px, float py) override {
        if (state == SITTING) {
            grit_t += dt;
            float was = glyph_t;
            glyph_t += dt;
            if (was < GLYPH_EVERY * 0.5f && glyph_t >= GLYPH_EVERY * 0.5f) crashed = true;
            if (ENRAGED) { state = SETTLED; rest = SETTLE; }       // it breaks loose
            return;
        }
        if (state == SETTLED) {
            if ((rest += dt) >= SETTLE) {
                // Off again, through where the player stands and on past.
                rest = 0.0f; state = ROLLING; grit_t = 0.0f;
                float d = hypotf(px - x, py - y);
                if (d < 1.0f) { rx = 0.0f; ry = 1.0f; } else { rx = (px - x) / d; ry = (py - y) / d; }
                tx = fminf(fmaxf(px + rx * OVERSHOOT, 60.0f), ARENA_W - 60.0f);       // inside the walls
                ty = fminf(fmaxf(py + ry * OVERSHOOT, ARENA_TOP + 60.0f), ARENA_H - 60.0f);
                float e = hypotf(tx - x, ty - y);
                if (e > 1.0f) { rx = (tx - x) / e; ry = (ty - y) / e; }
            }
            return;
        }
        grit_t += dt;
        float d = hypotf(tx - x, ty - y), st = ROLL * dt;
        if (d <= st) { x = tx; y = ty; state = SETTLED; landed = true; return; }
        x += rx * st; y += ry * st;
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        bool near = hypotf(x - px, y - py) < GLYPH_CLEAR;
        if (state == SITTING) {
            while (grit_t >= SPIN_EVERY && n + 5 <= max) {
                // The grit: a five-armed spiral off its edge, in dashes.
                grit_t -= SPIN_EVERY;
                spin_a += SPIN_TURN;
                if (spin_k++ % 5 >= 3) continue;
                for (int k = 0; k < 5; k++) {
                    float a = spin_a + k * (TAU / 5);
                    BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = x + cosf(a) * 32.0f; b.oy = y + sinf(a) * 28.0f;
                    out[n++] = b;
                }
            }
            if (crashed) { crashed = false; if (n + CHIP_N <= max) n += ring(x, y + 30.0f, 30.0f, 10.0f, CHIP_N, out + n); }
            if (glyph_t >= GLYPH_EVERY) {
                // The glyphs: spirals out of its eyes every way round, one at the player.
                glyph_t = 0.0f;
                if (!near) {
                    float a = aim_at(x, y, px, py);
                    for (int k = 0; k < 5 && n + GLYPH_N <= max; k++)
                        n += glyph(x, y - 6.0f, a + k * (TAU / 5), (k & 1) ? -1.6f : 1.6f, out + n);
                }
            }
            return n;
        }
        while (state == ROLLING && grit_t >= GRIT_EVERY && n + 4 <= max) {
            // The rubble: a pair of grit off both flanks, square to its run.
            grit_t -= GRIT_EVERY;
            for (int side = -1; side <= 1; side += 2) {
                float a = atan2f(ry, rx) + side * (PI / 2 + 0.35f);  // a little back: ruts trailing behind
                float ox = x + cosf(a) * 36.0f, oy = y + sinf(a) * 36.0f;   // off its flank
                if (hypotf(ox - px, oy - py) < CLEAR) continue;       // never point-blank
                for (int k = -1; k <= 1; k += 2) {
                    BulletSpawn b = mk(a + k * 0.18f, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = ox; b.oy = oy;
                    out[n++] = b;
                }
            }
        }
        if (landed) {
            landed = false;
            if (hypotf(x - px, y - py) < CLEAR + 40.0f) return n;  // landed by the player (a wall stopped it short): it holds
            if (n + LAND_CHIP_N <= max) n += ring(x, y + 30.0f, 30.0f, 10.0f, LAND_CHIP_N, out + n);   // the crash: chips off its base
            if (near) return n;                                   // too near: the spirals would open on top of them
            float a = aim_at(x, y, px, py), ux = cosf(a), uy = sinf(a);
            for (int e = -1; e <= 1 && n + GLYPH_N <= max; e += 2) {
                float ex = x + ux * 10.0f - uy * e * 14.0f, ey = y + uy * 10.0f + ux * e * 14.0f;   // its eyes: on the face toward you
                n += glyph(ex, ey, aim_at(ex, ey, px, py) + e * 0.35f, e * 1.6f, out + n);
            }
            if (n + SUN_N <= max) n += ring(x, y - 8.0f, 20.0f, 20.0f, SUN_N, out + n);   // the sun on its back: rays
        }
        return n;
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

// The ajaju, terror of the Garo Hills (A Book of Creatures): like a
// chameleon on long kneeless legs "like bamboo stalks without nodes", with
// twelve long, sharp, forked, sickle-like tongues that lick its prey's flesh
// away; it lures people with a shrill "wa-o, wa-o". HARD tier, 820 HP,
// tongue-red bullets. MEDIUM sheet (62x47: frame 1 the tongues fan out into
// writhing sickles, frame 2 it calls "wa-o", mouth open). Always facing
// front. Every shot leaves from the part of it that makes it (the user): its
// mouth, its tongues. Every shot at one pace, SPEED.
// Phase 1 -- high on its stilts at the top, staying put:
//   Tongues -- as they fan out (idle frame 1), TWELVE forked SICKLES of shots
//              lash out of its mouth every way round (one at the player),
//              each curved and forked at the tip, writhing (turning) as they
//              fly, every other one the other way.
//   Wa-o    -- as it calls (idle frame 2), two shrill rings out of its mouth,
//              "wa" and then "o", half a step apart, quavering as they spread.
// Phase 2 (half HP) -- it stalks to the middle of the arena and its tongues
//   become LASERS (the user): six beams out of its mouth, forming harmless
//   with the player in a gap, then hot, SWEEPING round together -- one way,
//   slowing, and back -- to be walked through, staying in a gap; the beams
//   go in three pairs that scissor open and shut, so every other gap GROWS
//   AND SHRINKS (the user); their middle is one glowing ball, seamless (the
//   user); and it keeps calling its rings.
class Ajaju : public Enemy {
    static constexpr float SPEED = 90.0f, WRITHE = 0.7f;
    static constexpr float MID_X = 320.0f, MID_Y = (ARENA_TOP + ARENA_H) * 0.5f, STALK = 200.0f;
    static constexpr float FORM = 1.2f, SWING = 1.8f, SWING_PACE = 0.22f;   // the beams sweep SWING rad either way of where they formed
    static constexpr float SCISSOR = 0.28f, SCISSOR_PACE = 0.5f, BALL = 14.0f;   // at 0.33 / 0.9 a closing gap outran the bot   // each pair opens and shuts SCISSOR rad either way
    static constexpr int   TONGUES = 12, TONGUE_N = 8, CALL_N = 30, BEAMS = 6;
    int   call_k = 0;
    bool  centred = false;
    float beam_t = 0.0f, beam_a0 = 0.0f;

    void mouth(float* ox, float* oy) const { *ox = x + (31.5f - 31.0f) * 2.0f; *oy = y + (16.0f - 23.5f) * 2.0f; }   // art px (62x47, drawn 2x about its middle)
    float beam_a(int k) const {
        float t = fmaxf(beam_t - FORM, 0.0f), open = SCISSOR * sinf(t * SCISSOR_PACE);   // the pairs scissoring
        return beam_a0 + SWING * sinf(t * SWING_PACE) + k * (TAU / BEAMS) + ((k & 1) ? open : -open);
    }
public:
    Ajaju() : Enemy(320, 150, 820, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
    const char* name()          const override { return "AJAJU"; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       fire_interval() const override { return 99.0f; }   // all on its idle frames
    int fire(float, float, BulletSpawn[], int) override { return 0; }
    void update(float dt, float px, float py) override {
        if (!ENRAGED) return;
        if (!centred) {
            // Stalking to the middle.
            float dx = MID_X - x, dy = MID_Y - y, d = hypotf(dx, dy), st = STALK * dt;
            if (d > st) { x += dx / d * st; y += dy / d * st; return; }
            x = MID_X; y = MID_Y; centred = true; beam_t = 0.0f;
            float mx, my;
            mouth(&mx, &my);
            beam_a0 = aim_at(mx, my, px, py) + PI / BEAMS;        // the player in the middle of a gap
            return;
        }
        beam_t += dt;
    }
    int telegraphs(TeleLine out[], int max) const override {
        if (!centred || max < BEAMS + 1) return 0;
        // The tongue lasers: growing out harmless, then hot and sweeping.
        float mx, my;
        mouth(&mx, &my);
        float k = fminf(beam_t / FORM, 1.0f);
        k = 1.0f - (1.0f - k) * (1.0f - k);
        for (int b = 0; b < BEAMS; b++) {
            float a = beam_a(b);
            TeleLine L{ mx, my, mx + cosf(a) * 900.0f * k, my + sinf(a) * 900.0f * k };
            L.stage = beam_t < FORM ? 0 : 1;
            L.hurt_w = L.stage == 1 ? 5.0f : 0.0f;
            out[b] = L;
        }
        TeleLine ball{ mx, my, mx, my };                          // their middle: one ball, drawn over the roots (harmless)
        ball.stage = 1; ball.orb = BALL * k;
        out[BEAMS] = ball;
        return BEAMS + 1;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (ENRAGED && !centred) return 0;                        // on the move
        int n = 0;
        float mx, my;
        mouth(&mx, &my);
        if (frame == 1 && !ENRAGED) {
            // The tongues: twelve forked sickles -- a curved run of six, then
            // the fork's two prongs -- lashing out every way, writhing.
            static float sx[TONGUE_N], sy[TONGUE_N];
            static bool built = false;
            if (!built) {
                built = true;
                for (int k = 0; k < 6; k++) {                    // the blade: along x, bending up as it goes
                    float f = k / 5.0f;
                    sx[k] = 8.0f + 30.0f * f; sy[k] = -10.0f * f * f;
                }
                sx[6] = 44.0f; sy[6] = -16.0f;                    // the fork
                sx[7] = 44.0f; sy[7] = -6.0f;
            }
            float a = aim_at(mx, my, px, py);
            for (int k = 0; k < TONGUES && n + TONGUE_N <= max; k++)
                n += shape_shots(mx, my, a + k * (TAU / TONGUES), SPEED, (k & 1) ? -WRITHE : WRITHE, 0.4f, sx, sy, TONGUE_N, out + n);
        } else if (frame == 2) {
            // Wa-o: two quavering rings, half a step apart (among the
            // lasers, one).
            int rings = ENRAGED ? 1 : 2;
            float turn = (call_k++ & 1) * 0.5f;
            for (int r = 0; r < rings; r++)
                for (int k = 0; k < CALL_N && n < max; k++) {
                    BulletSpawn b = mk((k + turn + r * 0.5f) * (TAU / CALL_N), SPEED * (r ? 0.8f : 1.0f), 2.5f, 5.0f);
                    b.from = true; b.ox = mx; b.oy = my;
                    b.zig = 0.3f; b.zig_every = 0.18f;
                    out[n++] = b;
                }
        }
        return n;
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

// The nykur of Iceland (A Book of Creatures): the water horse, a fine
// dapple-grey horse waiting by lakes and the sea, tempting people to ride it,
// then galloping into the water and drowning them; it gives itself away by
// its hooves, which face backwards. HARD tier, 840 HP, lake-grey bullets.
// MEDIUM sheet (58x51: frame 1 it tosses its head, the wet mane swinging out,
// frame 2 it lowers its head, beckoning). Every shot leaves from the part of
// it that makes it (the user): its backward hooves, its mane, its muzzle.
// Every shot at one pace, SPEED, and every one rolls along in WAVES like
// water (the user): its heading swinging WAVE either side, smoothly.
// Phase 1 -- it GALLOPS from wall to wall across the top, a beat at each end:
//   Hooves  -- its backward hooves kick water out behind it as it runs: a
//              pair back and down off each hoof -- sheets of spray
//              trailing across the arena.
//   Mane    -- as it tosses its head (idle frame 1) its wet mane flings a
//              fan of drops at the player.
//   Beckon  -- only when it stands at a wall (the user): as it pulls up, a
//              ripple out of its muzzle -- a ring.
// Phase 2 (half HP) -- the drowning: it DRAGS you toward it (a pull, the
//   rider it carries off) and gallops faster, three off each hoof, and each
//   beckon is two rings, half a step apart. (Kept gentle: the user.)
class Nykur : public Enemy {
    static constexpr float SPEED = 85.0f, RUN = 200.0f, RUN2 = 250.0f, TURN = 1.0f, RUN_Y = 140.0f, KICK_EVERY = 0.14f, DRAG = 28.0f;   // eased (the user)
    static constexpr float WAVE = 0.45f, WAVE_W = 3.0f;
    static BulletSpawn water(float a) { BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f); b.wave = WAVE; b.wave_w = WAVE_W; return b; }
    static constexpr int   RIPPLE_N = 20;
    int   dir = 1, beckons = 0;
    float rest = 0.0f, kick_t = 0.0f;
    bool  pulled_up = false;                                   // just reached a wall: fire() beckons

    // Art px (58x51, drawn 2x about its middle) of its right-facing view ->
    // screen, mirrored when it runs left.
    void at(float fx, float fy, float* ox, float* oy) const {
        if (dir < 0) fx = 57.0f - fx;
        *ox = x + (fx - 29.0f) * 2.0f; *oy = y + (fy - 25.5f) * 2.0f;
    }
public:
    Nykur() : Enemy(90, RUN_Y, 840, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
    const char* name()          const override { return "NYKUR"; }
    float       fire_interval() const override { return 0.02f; }   // the kicks on their own clock
    float       pull()          const override { return ENRAGED ? DRAG : 0.0f; }
    int         move_facing()   const override { return dir > 0 ? FACE_RIGHT : FACE_LEFT; }   // side on, running
    void update(float dt, float, float) override {
        if (rest > 0.0f) { rest -= dt; return; }                 // a beat at the wall
        kick_t += dt;
        float edge = dir > 0 ? ARENA_W - 90.0f : 90.0f, st = (ENRAGED ? RUN2 : RUN) * dt;
        if (fabsf(edge - x) <= st) { x = edge; dir = -dir; rest = TURN; kick_t = 0.0f; pulled_up = true; return; }   // turned back to the arena
        x += dir * st;
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        int fan = ENRAGED ? 3 : 2;
        while (rest <= 0.0f && kick_t >= KICK_EVERY && n + 2 * fan <= max) {
            // The hooves: a fan kicked back and down off each.
            kick_t -= KICK_EVERY;
            static const float HX[2] = { 17.0f, 34.0f };
            for (int h = 0; h < 2; h++) {
                float hx, hy;
                at(HX[h], 45.0f, &hx, &hy);
                for (int k = 0; k < fan; k++) {
                    float down = 0.35f + k * (0.8f / (fan - 1));  // from nearly flat behind to steeply down
                    float a = dir > 0 ? PI - down : down;           // behind it: the way it came
                    BulletSpawn b = water(a);
                    b.from = true; b.ox = hx; b.oy = hy;
                    out[n++] = b;
                }
            }
        }
        if (pulled_up) {
            // The beckon: a ripple out of its muzzle (phase 2, two).
            pulled_up = false;
            float mx, my;
            at(46.0f, 21.0f, &mx, &my);
            float turn = (beckons++ & 1) * 0.5f;
            for (int r = 0; r < (ENRAGED ? 2 : 1); r++)
                for (int k = 0; k < RIPPLE_N && n < max; k++) {
                    BulletSpawn b = water((k + turn + r * 0.5f) * (TAU / RIPPLE_N));
                    if (r) { b.vx *= 0.8f; b.vy *= 0.8f; b.wave = -WAVE; }   // the second ring slower, rolling the other way
                    b.from = true; b.ox = mx; b.oy = my;
                    out[n++] = b;
                }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (frame == 1) {
            // The mane: a fan of drops flung at the player.
            float mx, my;
            at(37.0f, 13.0f, &mx, &my);
            float a = aim_at(mx, my, px, py);
            for (int k = 0; k < 9 && n < max; k++) {
                BulletSpawn b = water(a + (k - 4) * 0.16f);
                b.from = true; b.ox = mx; b.oy = my;
                out[n++] = b;
            }
        }
        return n;
    }
};

// The sazae-oni of Japan (A Book of Creatures): a turban snail that, having
// lived a very long time, becomes an oni -- in Toriyama Sekien's picture a
// monstrous face leering out of a great spiral shell; in one tale it rode
// the sea as a drowning woman, was hauled aboard by pirates, and ate them.
// HARD tier, 860 HP, mother-of-pearl bullets. MEDIUM sheet (54x51: frame 1
// it leans out grinning wide, frame 2 it shrinks back into the shell).
// Sitting in its shell, always facing front. Every shot leaves from the part
// of it that makes it (the user): its shell's spines, its fanged mouth. Every
// shot at one pace, SPEED.
// Phase 1:
//   Spines -- every SPINE_EVERY s the spines round its whorls fire: eight
//             SPIKES, dashes of three, the shell turned a step each time --
//             a turning star of spikes.
//   Bite   -- as it leans out grinning (idle frame 1): JAWS -- two arcs of
//             shots out of its mouth, above and below the player's line,
//             curling in to close on it like teeth.
//   Shell  -- as it shrinks back (idle frame 2), a ring off its shell.
// Phase 2 (half HP) -- the GREAT SHELL (the user): its whorls are drawn in
//   shots over the whole arena, a massive spiral silhouette round it that
//   SPINS, the arms sliding slowly outward as it turns -- keep between them.
//   It GROWS from the middle out, the whorl laid down along itself at
//   WHORL_RATE shots a second, so its edge comes on slowly enough to see and
//   step clear of (the user: time to react); none is put down within
//   SHELL_HOLE of the player; it stays to the end. And it SUCKS the player
//   in (the user) while the first phase's patterns go on, lighter: fewer
//   spikes, slower, one bite, a thinner ring.
class SazaeOni : public Enemy {
    static constexpr float SPEED = 90.0f, SPINE_EVERY = 0.5f, SPINE_STEP = 0.2f, JAW_CURL = 0.25f;   // the jaws meet ~160-270 px out
    static constexpr int   SHELL_N = 22;
    // The great shell: an Archimedean spiral r = WHORL_R0 + WHORL_C * th out
    // to WHORL_MAX (the arena's far corners), a shot every WHORL_STEP px
    // along it, turning WHORL_W rad/s (its arms slide out WHORL_C*WHORL_W px/s).
    static constexpr float WHORL_R0 = 34.0f, WHORL_C = 15.0f, WHORL_MAX = 480.0f, WHORL_STEP = 15.0f, WHORL_W = 0.3f;
    static constexpr float SHELL_HOLE = 50.0f, WHORL_RATE = 40.0f, SUCK = 30.0f;
    static constexpr int   WHORL_CAP = 640;
    float spine_t = 0.0f, spine_a = 0.0f;
    int   spines = 0;
    float wx[WHORL_CAP], wy[WHORL_CAP];                         // the great shell's spots, relative to its middle
    int   whorl_n = -1, whorl_done = 0;                          // -1: not built
    float whorl_t = 0.0f;                                        // since it began to be laid down

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (54x51, drawn 2x about its middle) -> screen
        *ox = x + (fx - 27.0f) * 2.0f; *oy = y + (fy - 25.5f) * 2.0f;
    }
public:
    SazaeOni() : Enemy(320, 150, 860, {0.4f,1.75f,0.4f,1.5f,1.25f,0.6f,0.6f}) {}
    const char* name()          const override { return "SAZAE-ONI"; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       fire_interval() const override { return 0.02f; }   // the spines on their own clock
    float       pull()          const override { return whorl_n >= 0 ? SUCK : 0.0f; }
    void update(float dt, float, float) override { spine_t += dt; if (whorl_n >= 0) whorl_t += dt; }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (ENRAGED) {
            float cx, cy;
            at(27.5f, 30.0f, &cx, &cy);                          // the shell's middle
            if (whorl_n < 0) {
                // Build the spiral: step along it WHORL_STEP px at a time.
                whorl_n = 0;
                for (float th = 0.0f; whorl_n < WHORL_CAP; ) {
                    float r = WHORL_R0 + WHORL_C * th;
                    if (r > WHORL_MAX) break;
                    wx[whorl_n] = cosf(th) * r; wy[whorl_n] = sinf(th) * r; whorl_n++;
                    th += WHORL_STEP / hypotf(r, WHORL_C);              // ds = sqrt(r^2 + c^2) dth
                }
            }
            // Grow the shell along itself, the spots turned on by as far as
            // it has spun, so it's one shape.
            float turn = WHORL_W * whorl_t, ct = cosf(turn), st = sinf(turn);
            int end = (int)(whorl_t * WHORL_RATE) + 1;
            if (end > whorl_n) end = whorl_n;
            for (; whorl_done < end && n < max; whorl_done++) {
                float sx = cx + wx[whorl_done] * ct - wy[whorl_done] * st, sy = cy + wx[whorl_done] * st + wy[whorl_done] * ct;
                if (hypotf(sx - px, sy - py) < SHELL_HOLE) continue;   // never on the player
                BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
                b.from = true; b.ox = sx; b.oy = sy;
                b.orbit_about = true; b.orbit_cx = cx; b.orbit_cy = cy; b.orbit_w = WHORL_W;
                out[n++] = b;
            }
        }
        int m = ENRAGED ? 5 : 8;                                    // lighter among the whorls
        if (spine_t >= (ENRAGED ? SPINE_EVERY * 1.6f : SPINE_EVERY) && n + 3 * m <= max) {
            // The spines: spikes -- dashes of three -- off the whorls, the
            // shell a step round each time (phase 2, back and forth).
            spine_t = 0.0f;
            spine_a += SPINE_STEP;
            spines++;
            float cx, cy;
            at(27.5f, 34.0f, &cx, &cy);                          // the broad lower whorls
            for (int k = 0; k < m; k++) {
                float a = spine_a + k * (TAU / m);
                for (int d = 0; d < 3; d++) {
                    BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = cx + cosf(a) * (24.0f - d * 7.0f); b.oy = cy + sinf(a) * (16.0f - d * 5.0f);
                    out[n++] = b;
                }
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (frame == 1) {
            // The bite: jaws -- two arcs from its mouth, above and below the
            // player's line, curling in to close on it.
            float mx, my;
            at(26.0f, 35.0f, &mx, &my);
            float a = aim_at(mx, my, px, py);
            int bites = 1;
            for (int b = 0; b < bites; b++) {
                float ab = a + (b - (bites - 1) * 0.5f) * 1.1f;
                for (int jaw = -1; jaw <= 1; jaw += 2)
                    for (int k = 0; k < 7 && n < max; k++) {
                        BulletSpawn s = mk(ab + jaw * (0.45f + k * 0.05f), SPEED, 2.5f, 5.0f);   // the jaw's teeth, a row
                        s.from = true; s.ox = mx; s.oy = my;
                        s.orbit_w = -jaw * JAW_CURL;                    // curling in toward the line
                        out[n++] = s;
                    }
            }
        } else if (frame == 2 && max >= SHELL_N) {
            // Shrinking back: a ring off its shell.
            float cx, cy, turn = ernd() * TAU;
            at(27.5f, 30.0f, &cx, &cy);
            int ring = ENRAGED ? SHELL_N / 2 : SHELL_N;
            for (int k = 0; k < ring; k++) {
                float a = turn + k * (TAU / ring);
                BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = cx + cosf(a) * 24.0f; b.oy = cy + sinf(a) * 28.0f;
                out[n++] = b;
            }
        }
        return n;
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

// ── Later cryptids (ids 50 on; region in enemy_region) ──────────────────────

// ponytail: placeholders until each one's pattern round -- tier-sized HP and a
// plain shot, so they can be fought (F3) and spawned before their art exists.

// Small Northwoods fearsome critter (A Book of Creatures): it whistles like a
// boiling teakettle, clouds of steam come out of its nostrils, and it walks
// backwards by choice. LOW tier, 300 HP, steam-white bullets.
// Whistle -- on its sprite's whistle frame (idle frame 1, head up, mouth
//   open): lines of pellets aimed at the player, each line rising in speed
//   from back to front like a whistle rising in pitch -- 3 lines (0.30 apart),
//   5 in phase 2 (0.22 apart).
// Steam: every 2.4 s a puff of 4 big bubbles from its nose, blown at the
//   player, easing off to a steady 80 and RICOCHETING off the walls (3
//   bounces, the user's call), so steam keeps crossing the room. Every 1.6 s
//   in phase 2.
// Phase 2 (half HP): it walks backwards -- always away from the player,
//   still facing them -- around the top of the arena, playing its backwards
//   walk (50_teakettler_walk, a trot with the legs stepping toward its tail).
class Teakettler : public Enemy {
    static constexpr float BACK_SPEED = 45.0f;
    static constexpr float STEP_T     = 0.5f;    // seconds per trot cycle (the walk sheet's 4 frames)
    float walk_t = -1.0f;                        // seconds walked; -1 = standing
    // A whistle line: pellets one behind another along `a`, slow at the back,
    // fast at the front, so the line stretches as it flies.
    static int whistle_line(float a, BulletSpawn out[]) {
        for (int i = 0; i < 4; i++) out[i] = mk(a, 120.0f + i * 30.0f, 2.5f, 5.0f);
        return 4;
    }
public:
    Teakettler() : Enemy(320, 160, 300, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "TEAKETTLER"; }
    int         breath_frame()  const override { return 1; }   // its whistle frame
    float       flap_phase()    const override { return walk_t < 0.0f ? -1.0f : fmodf(walk_t / STEP_T, 1.0f); }
    float       fire_interval() const override { return ENRAGED ? 1.6f : 2.4f; }
    void update(float dt, float px, float py) override {
        if (!ENRAGED) return;
        float dx = x - px, dy = y - py, d = sqrtf(dx * dx + dy * dy);
        if (d < 1.0f) return;
        x += dx / d * BACK_SPEED * dt;
        y += dy / d * BACK_SPEED * dt;
        // Backing into a wall, it slides along it instead.
        float ox = x - dx / d * BACK_SPEED * dt, oy = y - dy / d * BACK_SPEED * dt;
        x = fminf(fmaxf(x, 90.0f), ARENA_W - 90.0f);
        y = fminf(fmaxf(y, ARENA_TOP + 50.0f), 230.0f);
        // It trots while it's getting anywhere; wedged in a corner, it stands.
        bool moved = fabsf(x - ox) + fabsf(y - oy) > BACK_SPEED * dt * 0.2f;
        walk_t = moved ? (walk_t < 0.0f ? 0.0f : walk_t + dt) : -1.0f;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        int lines = ENRAGED ? 5 : 3, n = 0;
        float step = ENRAGED ? 0.22f : 0.30f;
        for (int i = 0; i < lines; i++) n += whistle_line(a + (i - (lines - 1) * 0.5f) * step, out + n);
        return n;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py) + (ernd() * 2.0f - 1.0f) * 0.5f;
        for (int i = 0; i < 4; i++) {
            BulletSpawn b = mkb(a + (ernd() * 2.0f - 1.0f) * 0.35f, 120.0f + ernd() * 30.0f, 5.0f, 5.0f);
            b.accel = -60.0f; b.min_speed = 80.0f;   // eases off, then ricochets on at 80
            out[i] = b;
        }
        return 4;
    }
};

// Island-sized turtle: sailors land on its back, light a fire, and it dives
// and drowns them. ELITE, giant, ocean.
class Aspidochelone : public Enemy {
public:
    Aspidochelone() : Enemy(320, 150, 900, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "ASPIDOCHELONE"; }
    float       fire_interval() const override { return 1.4f; }
    int fire(float, float, BulletSpawn out[], int) override {
        float turn = ernd() * TAU;
        for (int i = 0; i < 20; i++) out[i] = mk(turn + i * (TAU / 20), 120.0f, 3.0f, 5.0f);
        return 20;
    }
};

// Vast creature of Tibet whose gaze kills whatever it sees -- unless that
// sees it first. BOSS tier 2, mountains.
class Sannaja : public Enemy {
public:
    Sannaja() : Enemy(320, 150, 1800, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "SANNAJA"; }
    float       fire_interval() const override { return 1.2f; }
    int fire(float, float, BulletSpawn out[], int) override {
        float turn = ernd() * TAU;
        for (int i = 0; i < 24; i++) out[i] = mk(turn + i * (TAU / 24), 130.0f, 3.0f, 5.0f);
        return 24;
    }
};

// The Beast of Barrisdale (A Book of Creatures): a roaring, flying beast with
// great wings and three legs, seen by stalkers in Knoydart in the Scottish
// Highlands in the 1800s. HARD tier, 880 HP, ember-orange bullets (its small
// burning eyes). BIG sheet (98x65, five idle frames, the wings beating slowly;
// frame 2 it rears, wings thrown high, roaring); flap = 83_..._fly. Every
// shot leaves from the part of it that makes it (the user): its wings, its
// roaring mouth, its feet. Every shot at one pace, SPEED.
// Phase 1 -- planted on its three legs at the top, facing front:
//   Wingbeats -- each beat (idle frames 1 and 3) a gust off each wingtip: a
//                fan leaning out and down, curling back in -- mirrored.
//   Stomp     -- as it settles its weight (idle frames 0 and 4) a small ring
//                off each of its three feet.
//   Roar      -- rearing (idle frame 2) it ROARS: three rings close behind
//                one another, lined up -- thick spokes, lanes between.
// Phase 2 (half HP) -- a harder Dingbat (the user): it takes to the air and
//   goes by turns --
//   Flying  -- FLY_T s along a great figure of eight, OPEN to the player's
//              shots: its legs trail talon-drops (a three-pronged fan
//              straight down) and it roars its spokes on taking off.
//   Hanging -- HANG_T s still in the air (the idle sheet: wings beating, the
//              tell), BLOCKING: after CATCH_DELAY any shot within CATCH is
//              caught and flung straight back at the player as two, and it
//              keeps its wingbeats and roar.
//   Nothing thrown within CLEAR of the player.
class BeastOfBarrisdale : public Enemy {
    static constexpr float SPEED = 90.0f, CLEAR = 60.0f, ROAR_CLEAR = 120.0f, TALON_EVERY = 0.15f;
    static constexpr float LOOP_W = 0.55f, LOOP_X = 230.0f, LOOP_Y = 80.0f, HOME_Y = 150.0f, FLY_Y = 200.0f;
    static constexpr float FLY_T = 2.4f, HANG_T = 2.0f, CATCH = 76.0f, CATCH_DELAY = 0.35f, RISE = 140.0f;
    static constexpr int   ROAR_N = 24, STOMP_N = 8;
    float loop_t = 0.0f, talon_t = 0.0f, state_t = 0.0f;
    bool  aloft = false, flying = false, take_off = false;      // aloft: phase 2 started (risen to the loop)
    struct Back { float x, y; } back[32];
    int   nback = 0;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // The roar: three rings close behind one another, lined up -- spokes.
    int roar(float mx, float my, BulletSpawn out[], int max) const {
        int n = 0;
        float turn = ernd() * TAU;
        for (int r = 0; r < 3; r++)
            for (int k = 0; k < ROAR_N && n < max; k++) {
                float a = turn + k * (TAU / ROAR_N);
                BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = mx + cosf(a) * (14.0f + r * 11.0f); b.oy = my + sinf(a) * (14.0f + r * 11.0f);
                out[n++] = b;
            }
        return n;
    }
    bool hanging() const { return aloft && !flying; }
public:
    BeastOfBarrisdale() : Enemy(320, HOME_Y, 880, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "BEAST OF BARRISDALE"; }
    float       fire_interval() const override { return 0.02f; }   // the flight's drops and the catches as they come
    float       flap_phase()    const override { return ENRAGED && (!aloft || flying) ? fmodf(state_t / 0.7f, 1.0f) : -1.0f; }   // a slow, heavy wingbeat
    float       catch_radius()  const override { return hanging() && state_t >= CATCH_DELAY ? CATCH : 0.0f; }
    void        catch_shot(float bx, float by) override { if (nback < 32) back[nback++] = { bx, by }; }
    int         move_facing()   const override {
        if (!ENRAGED || hanging()) return FACE_DOWN;
        if (!aloft) return FACE_UP;                               // rising
        return facing_toward(LOOP_X * cosf(loop_t * LOOP_W), LOOP_Y * 2.0f * cosf(loop_t * 2.0f * LOOP_W));
    }
    void update(float dt, float, float) override {
        if (!ENRAGED) return;
        state_t += dt;
        if (!aloft) {
            // Taking off: to where the figure of eight starts.
            float dy = FLY_Y - y, st = RISE * dt;
            if (fabsf(dy) > st) { y += dy > 0.0f ? st : -st; return; }
            aloft = flying = take_off = true; state_t = 0.0f;
            return;
        }
        if (flying) {
            loop_t += dt; talon_t += dt;
            x = 320.0f + LOOP_X * sinf(loop_t * LOOP_W);
            y = FLY_Y + LOOP_Y * sinf(loop_t * 2.0f * LOOP_W);
            if (state_t >= FLY_T) { flying = false; state_t = 0.0f; }
        } else if (state_t >= HANG_T) {
            flying = take_off = true; state_t = 0.0f; talon_t = 0.0f; nback = 0;
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        // Its catches flung straight back at the player, two a little apart.
        for (int i = 0; i < nback && n + 2 <= max; i++) {
            if (hypotf(back[i].x - px, back[i].y - py) < CLEAR) continue;   // caught at point-blank: just eaten
            float a = aim_at(back[i].x, back[i].y, px, py);
            for (int k = -1; k <= 1; k += 2) {
                BulletSpawn b = mk(a + k * 0.12f, SPEED * 1.6f, 2.5f, 5.0f);
                b.from = true; b.ox = back[i].x; b.oy = back[i].y;
                b.flash_in = true;
                out[n++] = b;
            }
        }
        nback = 0;
        if (!aloft || !flying) return n;
        if (take_off) {
            take_off = false;
            if (hypotf(x - px, y - py) >= ROAR_CLEAR) n += roar(x, y - 10.0f, out + n, max - n);
        }
        while (talon_t >= TALON_EVERY && n + 3 <= max) {
            // The talons: a three-pronged fan straight down off its legs.
            talon_t -= TALON_EVERY;
            float lx = x, ly = y + 40.0f;
            if (hypotf(lx - px, ly - py) < CLEAR) continue;
            for (int k = -1; k <= 1; k++) {
                BulletSpawn b = mk(PI / 2 + k * 0.4f, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = lx; b.oy = ly;
                out[n++] = b;
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (ENRAGED && !hanging()) return 0;                      // flying: fire() has it
        int n = 0;
        if (frame == 1 || frame == 3) {
            // The wingbeat: a gust off each wingtip, leaning out and down,
            // curling back in.
            float wy = frame == 1 ? 29.0f : 37.0f;
            for (int side = -1; side <= 1; side += 2) {
                float wx, wyy;
                at(side < 0 ? 21.0f : 68.0f, wy, &wx, &wyy);
                if (hypotf(wx - px, wyy - py) < CLEAR) continue;      // hanging low over the player: not point-blank
                for (int k = 0; k < 7 && n < max; k++) {
                    float a = PI / 2 - side * (0.5f + k * 0.12f);  // out its own side, and down
                    BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = wx; b.oy = wyy;
                    b.orbit_w = side * 0.3f;                          // curling back in
                    out[n++] = b;
                }
            }
        } else if ((frame == 0 || frame == 4) && !ENRAGED) {
            // The stomp: a small ring off each of its three feet (on the ground).
            static const float FX[3] = { 40.0f, 58.0f, 49.0f }, FY[3] = { 63.0f, 63.0f, 59.0f };
            float turn = ernd() * TAU;
            for (int f = 0; f < 3; f++) {
                float fx, fy;
                at(FX[f], FY[f], &fx, &fy);
                for (int k = 0; k < STOMP_N && n < max; k++) {
                    BulletSpawn b = mk(turn + (k + f / 3.0f) * (TAU / STOMP_N), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = fx; b.oy = fy;
                    out[n++] = b;
                }
            }
        } else if (frame == 2 && hypotf(x - px, y - py) >= ROAR_CLEAR) {
            float mx, my;
            at(54.0f, 35.0f, &mx, &my);                          // its mouth, reared up roaring
            n += roar(mx, my, out, max);
        }
        return n;
    }
};

// The kigutilik of the central Arctic's Inuit (A Book of Creatures): a huge
// hairless beast on long stilt legs with a walrus's head, fanged and tusked
// -- here, from the user's reference, with a cup-shaped bowl growing on a
// stalk from the top of its head and two curling tentacle tails. HARD tier,
// 900 HP, ice-violet bullets. BIG sheet (98x65, five idle frames, the tails
// curling; frame 2 the head raised, the jaws open). Standing high on its
// stilts, always facing front. Every shot leaves from the part of it that
// makes it (the user): its cup, its tusks, its jaws, its tails. Every shot at
// one pace, SPEED.
// Phase 1:
//   Fountain -- its cup brims over all the while: two streams arcing up and
//               out of it in gouts (gaps between to slip through), one each
//               way, curling over and down like water in great wide arches
//               reaching across the arena (the user) -- a high pair and a
//               low pair, gushing (the user: more active),
//               the spout swaying -- mirror images.
//   Tusks    -- the middle of the arena below it (the user: it was bare):
//               off each tusk tip all the while a stream stabbing down,
//               swinging to and fro across the middle, the two crossing --
//               in dashes, gaps between.
//   Jaws     -- raising its head (idle frame 2), a wide fan from its open
//               jaws at the player.
// Phase 2 (66% HP, the user) -- it overflows: a third, middle pair of fountain
//   streams, and its two tentacle tails lash, each curling out a wavering
//   stream.
class Kigutilik : public Enemy {
    static constexpr float SPEED = 90.0f, SPOUT_EVERY = 0.06f, SPOUT_SWAY = 0.45f, CURL = 0.45f,   // CURL: wide arches over the arena (was 1.0, tight curls)
                           TAIL_EVERY = 0.12f;
    float t = 0.0f, spout_t = 0.0f, tail_t = 0.0f;
    int   spout_k = 0, tail_k = 0, tusk_k = 0;
    float tusk_t = 0.0f;
    static constexpr float TUSK_EVERY = 0.08f, TUSK_SWING = 0.4f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
public:
    Kigutilik() : Enemy(320, 140, 900, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "KIGUTILIK"; }
    int         move_facing()   const override { return FACE_DOWN; }
    float       phase2_at()     const override { return 0.66f; }   // the user
    float       fire_interval() const override { return 0.02f; }   // the fountain and tails on their own clocks
    void update(float dt, float, float) override { t += dt; spout_t += dt; tail_t += dt; tusk_t += dt; }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        while (tusk_t >= TUSK_EVERY && n + 2 <= max) {
            // The tusks: a stream stabbing down off each, swinging across the
            // middle below, crossing -- in dashes.
            tusk_t -= TUSK_EVERY;
            if (tusk_k++ % 6 >= 3) continue;
            float w = TUSK_SWING * sinf((t - tusk_t) * 1.4f);
            for (int k = 0; k < 2; k++) {
                float tx, ty;
                at(k ? 64.0f : 59.0f, 41.0f, &tx, &ty);
                BulletSpawn b = mk(PI / 2 + (k ? w : -w), SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = tx; b.oy = ty;
                out[n++] = b;
            }
        }
        float cx, cy;
        at(57.0f, 12.0f, &cx, &cy);                              // the cup's brim
        int pairs = ENRAGED ? 3 : 2;
        while (spout_t >= SPOUT_EVERY && n + 2 * pairs <= max) {
            // The fountain: up and out each way, curling over and down.
            spout_t -= SPOUT_EVERY;
            if (spout_k++ % 6 >= 4) continue;                     // in gouts of four: gaps to slip through
            float sway = SPOUT_SWAY * sinf((t - spout_t) * 2.0f);
            for (int p = 0; p < pairs; p++) {
                static const float LEAN[3] = { 0.45f, 1.05f, 0.75f };  // off straight up: high, low, then (phase 2) between
                float lean = LEAN[p] + (p == 1 ? -sway : sway);     // the low pair sways against the high
                for (int side = -1; side <= 1; side += 2) {
                    BulletSpawn b = mk(-PI / 2 + side * lean, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = cx; b.oy = cy;
                    b.orbit_w = side * CURL;                          // over and down, its own side
                    out[n++] = b;
                }
            }
        }
        if (ENRAGED) {
            // The tails: each curling out a wavering stream.
            static const float TX[2] = { 28.0f, 31.0f }, TY[2] = { 24.0f, 31.0f };
            while (tail_t >= TAIL_EVERY && n + 2 <= max) {
                tail_t -= TAIL_EVERY;
                if (tail_k++ % 6 >= 3) continue;                   // in lashes: gaps between
                for (int k = 0; k < 2; k++) {
                    float tx, ty;
                    at(TX[k], TY[k], &tx, &ty);
                    BulletSpawn b = mk(PI * (k ? 0.75f : 1.1f) + 0.4f * sinf((t - tail_t) * 1.3f + k * PI), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = tx; b.oy = ty;
                    b.wave = 0.4f; b.wave_w = 4.0f;
                    out[n++] = b;
                }
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (frame != 2) return 0;
        // Raising its head: a fan from its open jaws.
        int n = 0;
        float mx, my;
        at(62.0f, 35.0f, &mx, &my);
        float j = aim_at(mx, my, px, py);
        for (int k = 0; k < 13 && n < max; k++) {
            BulletSpawn b = mk(j + (k - 6) * 0.15f, SPEED, 2.5f, 5.0f);
            b.from = true; b.ox = mx; b.oy = my;
            out[n++] = b;
        }
        return n;
    }

};

// The nanabolele of the Sotho (A Book of Creatures): river dragons living in
// flooded caves, their scaly skins glowing in the dark -- the hero
// Hlabakoane crossed their river to cut a shining hide for a shield. HARD
// tier, 920 HP, glow-green bullets (its scale lights). BIG sheet (98x65, five
// idle frames, the lights pulsing; frame 2 the jaws gape, every light
// blazing). It lies side on along the top, facing whichever side the player
// is on. (ART NOTE, the user, for the redesign: its head should face the
// player with its body turned to the right.) Every shot leaves from the part
// of it that makes it (the user): its glowing scale lights, its jaws. Every
// shot at one pace, SPEED.
// Phase 1:
//   Glow  -- a pulse of light runs down its flank from tail to head, over and
//            over, and each scale light as it flares sheds a fan of three
//            downward -- a rippling curtain sweeping along beneath it.
//   Blaze -- jaws gaping (idle frame 2), every light blazes: a small ring off
//            each one at once, and a fan from its jaws at the player.
// Phase 2 (66% HP, the user) -- the flooded dark: staying where it lies (the user), it
//   DRAGS the player in, harder than most (DRAG); as the pulse runs along
//   its flank every scale light launches a spinning DIAMOND of shots (the
//   main thing to dodge, the user; no homing), pointing the way it flies,
//   onto an ORBIT round it -- a
//   long ellipse, each pulse's tilted a golden turn on from the last, the six
//   diamonds following one another round it -- so the orbits cross into an
//   atom's flower (the user's picture), each diamond pointing the way it
//   goes all the while, and starting small, GROWING to full size by the time
//   it reaches the player (the user). After one lap the pulse's diamonds turn, all for the
//   one spot -- where the player was when the first came round -- and fly on
//   straight in their row, off the arena (the user). The lights still blaze,
//   but no breath from its jaws (the user).
class Nanabolele : public Enemy {
    static constexpr float SPEED = 90.0f, PULSE_T = 0.9f, PULSE_T2 = 2.6f, DRAG = 65.0f, GEM_R = 12.0f, GEM_GROW = 13.0f;   // GEM_GROW: from a point to full size over its lap and run at the player   // PULSE_T2: at 2.0 a long fight filled the 1024 bullets
    static constexpr float ORBIT_A = 230.0f, ORBIT_B = 50.0f;
    static constexpr float ORBIT_LAP = 973.0f;                   // the orbit's length (Ramanujan: pi(3(a+b) - sqrt((3a+b)(a+3b))))
    static constexpr int   LIGHTS = 6;
    static constexpr float LX[LIGHTS] = { 25.0f, 33.5f, 43.5f, 49.0f, 56.0f, 62.0f }, LY[LIGHTS] = { 45.0f, 44.0f, 42.5f, 42.5f, 42.5f, 42.5f };
    float pulse_t = 0.0f;
    int   lit_fwd = -1;                                          // the last light the pulse lit
    float orbit_tilt = 0.3f;                                     // this pulse's orbit
    int   pulses = 0;
    struct Aim { bool set; float x, y; } aims[16] = {};          // each pulse's row: where its diamonds head when their laps end

    bool facing_left(float px) const { return px < x; }
    // Art px of its right-facing view (98x65, drawn 2x about its middle) ->
    // screen, mirrored when it faces left.
    void at(float fx, float fy, bool left, float* ox, float* oy) const {
        if (left) fx = 97.0f - fx;
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    int shed(int k, bool left, BulletSpawn out[], int max) const {
        // A flaring light: a fan of three downward.
        float lx, ly;
        at(LX[k], LY[k], left, &lx, &ly);
        int n = 0;
        for (int f = -1; f <= 1 && n < max; f++) {
            BulletSpawn b = mk(PI / 2 + f * 0.35f, SPEED, 2.5f, 5.0f);
            b.from = true; b.ox = lx; b.oy = ly;
            out[n++] = b;
        }
        return n;
    }
    // Put b down where this pulse's orbit passes nearest and set it riding
    // the orbit: one lap, then straight on and away.
    void onto_orbit(BulletSpawn& b) const {
        float c = cosf(orbit_tilt), sn = sinf(orbit_tilt);
        b.from = true; b.ox = x - ORBIT_B * sn; b.oy = y + ORBIT_B * c;   // the minor axis's end
        if (b.orbit_w == 0.0f) b.orbit_w = 1e-4f;                  // (a formation, even of one: it rides the path)
        b.path_a = ORBIT_A; b.path_b = ORBIT_B; b.path_tilt = orbit_tilt; b.path_w = SPEED; b.path_even = true; b.path_phase = PI / 2;
        b.path_cx = x; b.path_cy = y;
        b.path_for = ORBIT_LAP / SPEED;                         // an even pace all round (the tips don't bunch), one lap
    }
    int gem(BulletSpawn out[], int max) const {
        // A flaring light, phase 2: a spinning diamond onto this pulse's
        // orbit round it, put down where the orbit passes nearest.
        static float sx[GEM_SPOTS], sy[GEM_SPOTS];
        static bool built = false;
        if (!built) { built = true; gem_points(GEM_R, sx, sy); }
        if (max < GEM_SPOTS) return 0;
        float c = cosf(orbit_tilt), sn = sinf(orbit_tilt);
        int m = shape_shots(x - ORBIT_B * sn, y + ORBIT_B * c, PI / 2, 0.0f, 1e-4f, GEM_GROW, sx, sy, GEM_SPOTS, out);   // long axis along +x: the way it flies; small, growing
        for (int q = 0; q < m; q++) { onto_orbit(out[q]); out[q].path_face = true; out[q].path_aim = true; out[q].path_aim_slot = pulses & 15; }   // pointing the way it flies; lap done, the row at the player (the user)
        return m;
    }
public:
    void aim_slot(int slot, float px, float py, float* tx, float* ty) override {
        // The first of a row to come round fixes where the row heads: the
        // player, then.
        Aim& a = aims[slot & 15];
        if (!a.set) a = { true, px, py };
        *tx = a.x; *ty = a.y;
    }
    Nanabolele() : Enemy(320, 130, 920, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "NANABOLELE"; }
    float       fire_interval() const override { return 0.02f; }   // the pulses on their own clock
    float       pull()          const override { return ENRAGED ? DRAG : 0.0f; }
    float       phase2_at()     const override { return 0.66f; }   // the user
    int         move_facing()   const override { return face_left ? FACE_LEFT : FACE_RIGHT; }
    void update(float dt, float px, float) override {
        face_left = facing_left(px);
        float period = ENRAGED ? PULSE_T2 : PULSE_T;
        pulse_t += dt;
        if (pulse_t >= period) { pulse_t -= period; lit_fwd = -1; if (ENRAGED) { orbit_tilt += 2.39996f; aims[++pulses & 15].set = false; } }   // the next orbit a golden turn on, its row's aim fresh
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        // Which light the pulse has reached, tail to head: each sheds its
        // fan (phase 2, a diamond onto the orbit).
        int fwd = (int)(pulse_t / (ENRAGED ? PULSE_T2 : PULSE_T) * LIGHTS);
        while (lit_fwd < fwd && n + GEM_SPOTS <= max)
            if (!ENRAGED) n += shed(++lit_fwd, face_left, out + n, max - n);
            else { ++lit_fwd; n += gem(out + n, max - n); }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (frame != 2) return 0;
        int n = 0;
        // The blaze: a small ring off every light at once...
        int m = ENRAGED ? 10 : 7;
        float turn = ernd() * TAU;
        for (int k = 0; k < LIGHTS; k++) {
            float lx, ly;
            at(LX[k], LY[k], face_left, &lx, &ly);
            for (int r = 0; r < m && n < max; r++) {
                BulletSpawn b = mk(turn + (r + k * 0.5f) * (TAU / m), SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = lx; b.oy = ly;
                out[n++] = b;
            }
        }
        // ...and a fan from its gaping jaws at the player (not in phase 2).
        if (ENRAGED) return n;
        float jx, jy;
        at(84.0f, 48.0f, face_left, &jx, &jy);
        float a = aim_at(jx, jy, px, py);
        for (int k = 0; k < 9 && n < max; k++) {
            BulletSpawn b = mk(a + (k - 4) * 0.16f, SPEED, 2.5f, 5.0f);
            b.from = true; b.ox = jx; b.oy = jy;
            out[n++] = b;
        }
        return n;
    }
private:
    bool face_left = false;
};

// The leucrocotta of Pliny (A Book of Creatures): a swift beast of India and
// Ethiopia the size of a wild ass, with a stag's legs, a lion's neck, chest
// and tail, a badger's head, and a mouth slit back to its ears holding one
// solid ridge of bone; it mimics human voices to lure travellers. HARD tier,
// 940 HP, bone-white bullets. BIG sheet (98x65, five idle frames; frame 2 the
// head thrown up, the ear-to-ear mouth gaping -- calling). Every shot leaves
// from the part of it that makes it (the user): its mouth. Every shot at one
// pace, SPEED.
// Phase 1 -- the lure: it stands at the top calling (kept easy, the user: no
//   pull, no ricochets): every CALL_EVERY s a SOUND WAVE out of its mouth --
//   two rings braided together, quavering opposite ways -- each call turned
//   a fixed step on from the last (one way, then back).
// Phase 2 (half HP) -- swift (the user): it RUNS off the arena, gone, while
//   out of the side it will come back from a spray of its calls pours in --
//   the tell -- then it bursts back in from that side, stands a beat calling
//   (the ONLY time it can be hit), and is off again.
class Leucrocotta : public Enemy {
    static constexpr float SPEED = 90.0f, CALL_EVERY = 0.85f, CALL_STEP = 0.13f;   // the user: a little harder (was 1.3)
    static constexpr float DASH = 620.0f, GONE_T = 1.8f, STAND_T = 1.6f, SPRAY_EVERY = 0.14f, CLEAR = 110.0f;
    static constexpr int   CALL_N = 22;
    enum State { CALLING, LEAVING, GONE, ENTERING, STANDING };
    State state = CALLING;
    float t = 0.0f, call_t = 0.0f, call_a = 0.0f, state_t = 0.0f, tx = 0.0f, ty = 0.0f, spray_t = 0.0f;
    int   calls = 0, side = 1;                                   // side: the wall it comes back from (-1 left, 1 right)
    float back_y = 200.0f;                                       // the height it comes back at

    // Its gaping mouth, by facing (from behind: its crown).
    void mouth(int f, float* ox, float* oy) const {
        static const float MX[8] = { 59.2f, 67.5f, 75.9f, 69.5f, 50.0f, 27.5f, 21.1f, 29.5f },
                           MY[8] = { 21.8f, 21.3f, 20.6f, 20.8f, 10.0f, 20.8f, 20.6f, 21.3f };
        int d = face8(f);
        *ox = x + (MX[d] - 49.0f) * 2.0f; *oy = y + (MY[d] - 32.5f) * 2.0f;   // art px (98x65, drawn 2x about its middle)
    }
    bool run_to(float dt) {                                      // dashing for (tx, ty); true on arrival
        float dx = tx - x, dy = ty - y, d = hypotf(dx, dy), st = DASH * dt;
        if (d <= st) { x = tx; y = ty; return true; }
        x += dx / d * st; y += dy / d * st;
        return false;
    }
public:
    Leucrocotta() : Enemy(320, 140, 940, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "LEUCROCOTTA"; }
    float       fire_interval() const override { return 0.02f; }   // the calls and sprays on their own clocks
    int         move_facing()   const override {
        if (state == LEAVING || state == ENTERING) return facing_toward(tx - x, ty - y);
        return -1;
    }
    void update(float dt, float px, float py) override {
        t += dt; call_t += dt; state_t += dt;
        if (!ENRAGED) return;
        if (state == CALLING || (state == STANDING && state_t >= STAND_T)) {
            // Off: out the nearer side wall, fast.
            state = LEAVING; state_t = 0.0f;
            tx = x < ARENA_W * 0.5f ? -120.0f : ARENA_W + 120.0f; ty = y;
        }
        if (state == LEAVING && run_to(dt)) {
            // Gone; it picks the side and height it comes back at.
            state = GONE; state_t = 0.0f; spray_t = 0.0f;
            side = ernd() < 0.5f ? -1 : 1;
            back_y = ARENA_TOP + 80.0f + ernd() * 240.0f;
            if (fabsf(back_y - py) < 90.0f) back_y = back_y < py ? fmaxf(ARENA_TOP + 60.0f, py - 120.0f) : fminf(ARENA_H - 80.0f, py + 120.0f);
            x = side < 0 ? -120.0f : ARENA_W + 120.0f; y = back_y;
        }
        if (state == GONE && state_t >= GONE_T) {
            state = ENTERING; state_t = 0.0f;
            tx = side < 0 ? 130.0f : ARENA_W - 130.0f; ty = back_y;
        }
        if (state == ENTERING && run_to(dt)) { state = STANDING; state_t = 0.0f; call_t = CALL_EVERY; }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (state == GONE) {
            // The tell: its calls pouring in from the wall it will come back
            // from -- a fan sweeping to and fro at its height.
            spray_t += 0.02f;
            while (spray_t >= SPRAY_EVERY && n + 5 <= max) {
                spray_t -= SPRAY_EVERY;
                float wx = side < 0 ? 4.0f : ARENA_W - 4.0f, in = side < 0 ? 0.0f : PI;
                float sweep = 0.5f * sinf(state_t * 3.0f);
                if (hypotf(wx - px, back_y - py) < CLEAR) continue;
                for (int k = -2; k <= 2; k++) {
                    BulletSpawn b = mk(in + sweep + k * 0.18f, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = wx; b.oy = back_y;
                    out[n++] = b;
                }
            }
            return n;
        }
        if ((state == CALLING || state == STANDING) && call_t >= CALL_EVERY && n + 2 * CALL_N <= max) {
            // A call: two rings of sound out of its mouth, braided -- quavering
            // opposite ways -- turned a fixed step on from the last.
            call_t = 0.0f;
            float mx, my;
            mouth(facing_toward(px - x, py - y), &mx, &my);
            if (hypotf(mx - px, my - py) < CLEAR) return n;       // the player right by it: it holds the call
            call_a += ((calls++ / 4) & 1) ? -CALL_STEP : CALL_STEP;
            for (int r = 0; r < 2; r++)
                for (int k = 0; k < CALL_N; k++) {
                    BulletSpawn b = mk(call_a + (k + r * 0.5f) * (TAU / CALL_N), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = mx; b.oy = my;
                    b.wave = r ? -0.35f : 0.35f; b.wave_w = 4.0f;
                    out[n++] = b;
                }
        }
        return n;
    }
};

// The corocotta of Pliny (A Book of Creatures): a cross of hyena and wolf
// out of Ethiopia that mimics human speech to call men out at night, with a
// single unbroken tooth in each jaw that never wears, and eyes that change
// colour. HARD tier, 960 HP, grey-steel bullets. BIG sheet (98x65, five idle
// frames, the mane bristling; frame 2 the jaws thrown wide on its two great
// teeth). It stands still the whole fight (the user). Every shot leaves from the
// part of it that makes it (the user): its mouth, its two teeth. Every shot
// at one pace, SPEED.
// Phase 1:
//   Speech -- every WORD_EVERY s it speaks a WORD: syllables, quick rings out
//             of its mouth one after another, each half a step round from the
//             last -- braided.
//   Chomp  -- jaws wide (idle frame 2): a pair of JAWS of shots (the user):
//             two rows of teeth -- zigzags, the points facing each other --
//             flying at the player either side of its line and closing as
//             they come, CHOMPING shut, the teeth meshing, just where the
//             player stood; then on past, parting.
// Phase 2 (half HP) -- all teeth, MIRRORED (the user: saws and streams in a
//   symmetrical pattern, every shot moving alike): everything flies straight
//   out of its mouth at SPEED, in pairs mirrored about straight down --
//   Saws    -- every SAW_EVERY s a pair of SAWS, wheels of SAW_TEETH teeth,
//              spinning as mirror images, the pair's spread swinging slowly
//              out and in.
//   Streams -- four pairs of streams of shots, in dashes, fanned STREAM_GAP
//              apart (the last pair up past its shoulders), swinging against the saws -- a lattice of lines that
//              opens and shuts.
//   Rings   -- and every RING_EVERY s a full ring of shots, turned a golden
//              step on each time, so no spot anywhere stays safe for long
//              (the user: standing still was safe in places).
//   No chomps, no words: the teeth say it. It draws BREATH s of breath first
//   (phase 1's shots clear: the two phases' loads met at the bullet cap).
class Corocotta : public Enemy {
    static constexpr float SPEED = 90.0f, WORD_EVERY = 1.5f, SYLLABLE = 0.16f;
    static constexpr float SAW_EVERY = 1.0f, SAW_R = 26.0f, SAW_W = 2.0f, SAW_TOOTH = 16.0f;
    static constexpr float SWING_W = 0.9f, STREAM_EVERY = 0.07f, STREAM_GAP = 0.6f, BREATH = 1.2f, RING_EVERY = 0.8f;   // SWING_W: the pairs swing out and in at this, rad/s
    static constexpr int   SAW_TEETH = 8, SAW_N = SAW_TEETH * 4, RING_N = 44;
    static constexpr float JAW_LEN = 100.0f, JAW_OPEN = 70.0f, TOOTH = 14.0f;   // a row of teeth; the jaws start this far either side of the line; a tooth this long
    static constexpr int   SYLLABLE_N = 14, TEETH = 5, JAW_N = 11 + 3 * TEETH;   // a row: its gum line, and each tooth's tip and its two sides
    float t = 0.0f, word_t = 0.0f, syl_t = 0.0f, saw_t = 0.0f, stream_t = 0.0f, ring_t = 0.0f;
    int   syllables = 0, words = 0, stream_k = 0, rings = 0;
    bool  breathed = false;                                      // phase 2 begun (after its breath)

    void mouth(int f, float* ox, float* oy) const {
        static const float MX[8] = { 59.8f, 65.8f, 75.5f, 67.5f, 50.0f, 29.5f, 21.5f, 31.2f },
                           MY[8] = { 28.0f, 27.2f, 26.6f, 26.5f, 9.0f, 26.5f, 26.6f, 27.2f };
        int d = face8(f);
        *ox = x + (MX[d] - 49.0f) * 2.0f; *oy = y + (MY[d] - 32.5f) * 2.0f;   // art px (98x65, drawn 2x about its middle)
    }
public:
    Corocotta() : Enemy(320, 140, 960, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "COROCOTTA"; }
    float       fire_interval() const override { return 0.02f; }   // the words on their own clock
    void update(float dt, float, float) override {
        t += dt; word_t += dt; saw_t += dt; stream_t += dt; ring_t += dt;
        if (syllables > 0) syl_t += dt;
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (ENRAGED) {
            // Everything in mirrored pairs about straight down from its mouth,
            // the pairs' spread swinging: the saws out as the streams come in.
            if (!breathed) { breathed = true; saw_t = SAW_EVERY - BREATH; stream_t = -BREATH; ring_t = RING_EVERY - BREATH; }
            float mx, my;
            mouth(facing_toward(px - x, py - y), &mx, &my);
            float swing = 0.5f + 0.5f * sinf(t * SWING_W);
            if (saw_t >= SAW_EVERY && n + 2 * SAW_N <= max) {
                // A pair of saws: wheels of teeth, spinning as mirror images.
                saw_t = 0.0f;
                static float sx[SAW_N], sy[SAW_N];
                static bool built = false;
                if (!built) {
                    built = true;
                    int m = 0;
                    float tooth = TAU / SAW_TEETH;
                    for (int k = 0; k < SAW_TEETH; k++) {
                        float a = k * tooth;
                        sx[m] = cosf(a) * (SAW_R + SAW_TOOTH); sy[m++] = sinf(a) * (SAW_R + SAW_TOOTH);   // the point
                        for (int e = -1; e <= 1; e += 2) { sx[m] = cosf(a + e * 0.17f) * SAW_R; sy[m++] = sinf(a + e * 0.17f) * SAW_R; }   // its base
                        sx[m] = cosf(a + tooth * 0.5f) * SAW_R; sy[m++] = sinf(a + tooth * 0.5f) * SAW_R;   // the gum between
                    }
                }
                float off = 0.2f + 1.0f * swing;
                for (int side = -1; side <= 1; side += 2)
                    n += shape_shots(mx, my, PI / 2 + side * off, SPEED, side * SAW_W, 0.35f, sx, sy, SAW_N, out + n);
            }
            while (stream_t >= STREAM_EVERY && n + 8 <= max) {
                // The streams: four mirrored pairs (the last reaching up past
                // its shoulders: no empty top corners), in dashes, swinging in
                // as the saws swing out.
                stream_t -= STREAM_EVERY;
                if (stream_k++ % 8 >= 3) continue;
                float off = 0.6f * (1.0f - swing);                // down to straight below: no lane there
                for (int k = 0; k < 4; k++)
                    for (int side = -1; side <= 1; side += 2) {
                        BulletSpawn b = mk(PI / 2 + side * (off + k * STREAM_GAP), SPEED, 2.5f, 5.0f);
                        b.from = true; b.ox = mx; b.oy = my;
                        out[n++] = b;
                    }
            }
            if (ring_t >= RING_EVERY && n + RING_N <= max) {
                // A ring, turned a golden step on from the last.
                ring_t = 0.0f;
                float turn = rings++ * 2.39996f;
                for (int k = 0; k < RING_N; k++) {
                    BulletSpawn b = mk(turn + k * (TAU / RING_N), SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = mx; b.oy = my;
                    out[n++] = b;
                }
            }
            return n;
        }
        if (word_t >= WORD_EVERY && syllables == 0) { word_t = 0.0f; syllables = 3; syl_t = SYLLABLE; words++; }
        if (syllables > 0 && syl_t >= SYLLABLE && n + SYLLABLE_N <= max) {
            // A syllable: a quick ring out of its mouth, half a step round
            // from the last.
            syl_t = 0.0f;
            int k = 3 - syllables--;
            float mx, my;
            mouth(facing_toward(px - x, py - y), &mx, &my);
            float turn = words * 0.37f + k * (PI / SYLLABLE_N);
            for (int i = 0; i < SYLLABLE_N; i++) {
                BulletSpawn b = mk(turn + i * (TAU / SYLLABLE_N), SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = mx; b.oy = my;
                out[n++] = b;
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (frame != 2 || ENRAGED) return 0;
        // The chomp: two rows of teeth, the points facing each other, flying
        // at the player either side of its line and closing to mesh just
        // where the player stood.
        float mx, my;
        mouth(facing_toward(px - x, py - y), &mx, &my);
        float a = aim_at(mx, my, px, py), d = fmaxf(hypotf(px - mx, py - my), 120.0f);
        int jaws = 1, n = 0;
        for (int j = 0; j < jaws; j++) {
            float aj = a + (j - (jaws - 1) * 0.5f) * 0.7f;
            for (int side = -1; side <= 1 && n + JAW_N <= max; side += 2) {
                // One jaw, in its flight's frame (x along it, y across): the
                // gum line at side * JAW_OPEN, teeth pointing in; the other
                // jaw's teeth half a tooth along, so they mesh.
                float rx[JAW_N], ry[JAW_N];
                int m = 0;
                float gum = side * JAW_OPEN, in = -side * TOOTH, step = JAW_LEN / (TEETH * 2), shift = side > 0 ? step : 0.0f;
                for (int k = 0; k <= 10; k++) { rx[m] = -JAW_LEN * 0.5f + k * (JAW_LEN / 10); ry[m++] = gum; }
                for (int t = 0; t < TEETH; t++) {
                    float cx = -JAW_LEN * 0.5f + step * (2 * t + 1) + shift - step * 0.5f;
                    rx[m] = cx;               ry[m++] = gum + in;           // the point
                    rx[m] = cx - step * 0.5f; ry[m++] = gum + in * 0.5f;    // its sides
                    rx[m] = cx + step * 0.5f; ry[m++] = gum + in * 0.5f;
                }
                // Flying in, closing: aimed in so the gum line crosses the
                // player's line where the player is, less a tooth -- shut.
                float close = atan2f(side * (JAW_OPEN - TOOTH * 0.5f), d);
                float fly = aj - close;
                for (int k = 0; k < m; k++) {                    // turn the jaw with its flight so it stays along the line
                    float r = close, qx = rx[k] * cosf(r) - ry[k] * sinf(r), qy = rx[k] * sinf(r) + ry[k] * cosf(r);
                    rx[k] = qx; ry[k] = qy;
                }
                n += shape_shots(mx, my, fly, SPEED, 1e-4f, 0.35f, rx, ry, m, out + n);
            }
        }
        return n;
    }

};

// The amixsak of the Yupik of the Bering Sea (A Book of Creatures): a walrus
// skin left behind on the ice sinks and becomes a vengeful monster that rises
// under a skin boat, reaches its flippers over the gunwales and pulls it
// down. HARD tier, 980 HP, seawater-green bullets. BIG sheet (98x65, five
// idle frames, bobbing, the flippers groping; frame 2 both flippers flung
// high to seize, the empty mouth gaping). Every shot leaves from the part of
// it that makes it (the user): its flippers, its rising bulk. Every shot at
// one pace, SPEED.
// Phase 1 -- risen, floating at the top, facing the player: a CLUSTER of
//   SEIZES (the user), nothing else -- every SEIZE_EVERY s a new seize
//   begins while the last are still sweeping (up to ARMS at once):
//   Seize -- two ARMS of shots sweep out of the flipper tips, each three
//            streams side by side whose aim swings from flung HIGH (up and
//            out: the top of the arena is swept too, the user) down and
//            across -- the arms closing over the gunwales -- crossing below
//            it; in dashes. Several at once, staggered: a fan of arms
//            closing one after another.
// Phase 2 (half HP) -- it goes UNDER: it sinks out of sight, glides unseen
//   beneath the arena to where the player is (a trail of bubbles -- harmless
//   -- gives it away), the water HEAVES there for HEAVE_T s (a swelling,
//   harmless), and it RISES under them -- crushing on touch,
//   and once it's up an EXPLOSION of bubbles (the user): rings close behind
//   one another bursting out all round it -- and PULLING the player in --
//   then stays risen RISEN_T s and (ARM_DELAY s on, the player having had
//   time to get clear) makes one seize -- the only time it can be hurt -- and
//   sinks again. It never comes up in a corner (the player boxed in there
//   with it had nowhere to go).
class Amixsak : public Enemy {
    static constexpr float SPEED = 90.0f, ARM_T = 3.4f, ARM_EVERY = 0.06f, SEIZE_EVERY = 1.0f, CLEAR = 50.0f;   // ARM_T: 2.5 rad at ~0.7 rad/s, slow enough to walk ahead of; CLEAR: nothing put down this near the player
    static constexpr int   ARM_W = 3, ARMS = 4;                  // streams to an arm; seizes sweeping at once
    static constexpr float SINK_T = 0.6f, GLIDE = 220.0f, HEAVE_T = 0.8f, HEAVE_R = 48.0f, RISE_T = 0.4f, RISEN_T = 3.0f, DRAG = 45.0f, DRAG_T = 0.8f, ARM_DELAY = 0.9f;
    static constexpr int   BUBBLES = 12, BURST_N = 30, BURST_RINGS = 3;   // the burst: rings close behind one another, each half a step round
    enum State { RISEN, SINKING, UNDER, HEAVING, RISING };
    State state = RISEN;
    float t = 0.0f, state_t = 0.0f, seize_t = 0.0f, bob0 = 140.0f;
    float arm_t[ARMS] = { -1.0f, -1.0f, -1.0f, -1.0f };          // each seize's clock (-1: free)
    int   arm_k[ARMS] = { 0, 0, 0, 0 };
    bool  burst_due = false, seize_due = false;
    float bx[BUBBLES], by[BUBBLES];                              // the bubble trail: where it has been, under
    int   nb = 0, bhead = 0;
    float bubble_t = 0.0f;

    // Art px (98x65, drawn 2x about its middle) -> screen.
    void at(float fx, float fy, float* ox, float* oy) const { *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f; }
    // Its flipper tips, flung high, by facing.
    void flipper(int side, int f, float* ox, float* oy) const {
        static const float LX[8] = { 37, 39, 58, 40, 37, 24, 30, 22 }, LY[8] = { 17, 22, 15, 20, 15, 18, 15, 15 };
        static const float RX[8] = { 72, 73, 66, 62, 72, 58, 40, 58 }, RY[8] = { 16, 15, 20, 18, 18, 22, 22, 22 };
        int d = face8(f);
        at(side < 0 ? LX[d] : RX[d], side < 0 ? LY[d] : RY[d], ox, oy);
    }
    void  seize() { for (int i = 0; i < ARMS; i++) if (arm_t[i] < 0.0f) { arm_t[i] = 0.0f; arm_k[i] = 0; return; } }
    void  drop_arms() { for (int i = 0; i < ARMS; i++) arm_t[i] = -1.0f; }
public:
    Amixsak() : Enemy(320, 140, 980, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()           const override { return "AMIXSAK"; }
    float       fire_interval()  const override { return 0.02f; }   // the arms on their own clocks
    float       opacity(float, float) const override {
        return state == RISEN ? 1.0f : state == SINKING ? 1.0f - state_t / SINK_T : state == RISING ? state_t / RISE_T : 0.0f;
    }
    float       armor()          const override { return state == RISEN ? 1.0f : 0.0f; }   // only hurt risen
    float       contact_damage() const override { return state == RISING ? 5.0f : 0.0f; }  // it comes up under the boat
    float       pull()           const override { return state == RISING || (state == RISEN && ENRAGED && state_t < DRAG_T) ? DRAG : 0.0f; }
    int telegraphs(TeleLine out[], int max) const override {
        int n = 0;
        if (state == UNDER || state == HEAVING) {
            // The bubble trail, the newest biggest.
            for (int k = 0; k < nb && n < max; k++) {
                int i = (bhead - 1 - k + BUBBLES) % BUBBLES;
                TeleLine b{ bx[i], by[i], bx[i], by[i] };
                b.stage = 0; b.orb = 5.0f - 3.0f * k / (float)BUBBLES;
                out[n++] = b;
            }
        }
        if (state == HEAVING && n < max) {
            // The water heaving where it will rise.
            TeleLine h{ x, y, x, y };
            h.stage = 0; h.orb = HEAVE_R * fminf(state_t / HEAVE_T, 1.0f);
            out[n++] = h;
        }
        return n;
    }
    void update(float dt, float px, float py) override {
        t += dt; state_t += dt;
        if (state == RISEN && !ENRAGED) seize_t += dt;
        for (int i = 0; i < ARMS; i++) if (arm_t[i] >= 0.0f) arm_t[i] += dt;
        switch (state) {
        case RISEN:
            if (ENRAGED && state_t >= RISEN_T) { state = SINKING; state_t = 0.0f; drop_arms(); break; }   // (an arm half swept is dropped, not banked)
            y = bob0 + 4.0f * sinf(t * 1.6f);                    // bobbing on the water
            break;
        case SINKING:
            y += 25.0f * dt;
            if (state_t >= SINK_T) { state = UNDER; state_t = 0.0f; nb = 0; bubble_t = 0.0f; }
            break;
        case UNDER: {
            // Gliding beneath the water to the player -- or as near as its
            // bulk can get to one against a wall (it heaves there: a player
            // hugging a wall used to leave it circling under for ever).
            float tx = fminf(fmaxf(px, 130.0f), ARENA_W - 130.0f), ty = fminf(fmaxf(py, ARENA_TOP + 80.0f), ARENA_H - 110.0f);   // never in a corner
            float dx = tx - x, dy = ty - y, d = hypotf(dx, dy), st = GLIDE * dt;
            if (d > st) { x += dx / d * st; y += dy / d * st; } else { x = tx; y = ty; }
            if ((bubble_t += dt) >= 0.12f) { bubble_t = 0.0f; bx[bhead] = x + 10.0f * sinf(t * 7.0f); by[bhead] = y; bhead = (bhead + 1) % BUBBLES; if (nb < BUBBLES) nb++; }
            if (d <= st) { state = HEAVING; state_t = 0.0f; }
            break;
        }
        case HEAVING:
            if (state_t >= HEAVE_T) { state = RISING; state_t = 0.0f; }
            break;
        case RISING:
            if (state_t >= RISE_T) { state = RISEN; state_t = 0.0f; bob0 = y; seize_due = burst_due = true; }
            break;
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (burst_due && n + BURST_N * BURST_RINGS <= max) {
            // Risen: a ring of bubbles bursting out round it (from 30 px out,
            // so one standing right on it isn't shot point-blank: the hide
            // itself is what hits them there).
            burst_due = false;
            float turn = ernd() * TAU;
            for (int r = 0; r < BURST_RINGS; r++)
                for (int k = 0; k < BURST_N; k++) {
                    float a = turn + (k + r * 0.5f) * (TAU / BURST_N), rad = 30.0f + r * 16.0f;
                    float ox = x + cosf(a) * rad, oy = y + sinf(a) * rad;
                    if (hypotf(ox - px, oy - py) < CLEAR) continue;
                    BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                    b.from = true; b.ox = ox; b.oy = oy;
                    out[n++] = b;
                }
        }
        if (state != RISEN) return n;
        if (seize_due && state_t >= ARM_DELAY) { seize_due = false; seize(); }   // phase 2, risen a moment: one seize
        while (!ENRAGED && seize_t >= SEIZE_EVERY) { seize_t -= SEIZE_EVERY; seize(); }   // phase 1: seize on seize
        int f = facing_toward(px - x, py - y);
        for (int i = 0; i < ARMS; i++) {
            if (arm_t[i] < 0.0f) continue;
            // An arm pair: from each flipper tip three streams side by side
            // whose aim swings from straight out to down and across --
            // closing -- in dashes.
            while (arm_t[i] >= ARM_EVERY && n + 2 * ARM_W <= max) {
                arm_t[i] -= ARM_EVERY; arm_k[i]++;
                if (arm_k[i] % 8 >= 3) continue;                  // dashes 3 on, 5 off: ~32 px holes through the arm
                float k = fminf((float)arm_k[i] * ARM_EVERY / ARM_T, 1.0f);
                for (int side = -1; side <= 1; side += 2) {
                    float fx, fy;
                    flipper(side, f, &fx, &fy);
                    float a = PI / 2 + side * (2.2f - 2.5f * k), ux = -sinf(a), uy = cosf(a);   // from flung high, down and across; (ux, uy): across the stream
                    for (int w = 0; w < ARM_W; w++) {
                        float off = (w - (ARM_W - 1) * 0.5f) * 9.0f, ox = fx + ux * off, oy = fy + uy * off;
                        if (hypotf(ox - px, oy - py) < CLEAR) continue;
                        BulletSpawn b = mk(a, SPEED, 2.5f, 5.0f);
                        b.from = true; b.ox = ox; b.oy = oy;
                        out[n++] = b;
                    }
                }
            }
            if ((float)arm_k[i] * ARM_EVERY >= ARM_T) arm_t[i] = -1.0f;
        }
        return n;
    }
};

// A cryptid on the roster before its pattern round: its name, tier-sized HP,
// and a plain aimed volley that widens with the tier (LOW 2, MEDIUM 3, UPPER
// 5 shots), so it can be fought and spawned now. Each gets its own class --
// its real patterns -- in its round.
class Unfinished : public Enemy {
    const char* nm;
    int         shots;
public:
    Unfinished(const char* name, float hp, EnemyTier tier)
        : Enemy(320, 160, hp, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}), nm(name),
          shots(tier == T_LOW ? 2 : tier == T_MEDIUM ? 3 : 5) {}
    const char* name()          const override { return nm; }
    float       fire_interval() const override { return 0.9f; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < shots; i++)
            out[i] = mk(a + (i - (shots - 1) * 0.5f) * 0.25f, 150.0f, 2.5f, 5.0f);
        return shots;
    }
};

// Small woodchuck-like fearsome critter of the White Mountains with velvety
// kitten fur (A Book of Creatures): it "runs directly at unsuspecting
// passers-by from out of the brush and comes to a sudden halt a few inches
// away", then "spits like a cat, emits a mink-like stench, and runs away
// again". LOW tier, 320 HP, musky pale-yellow bullets.
// The cycle, over and over:
//   Lurk  -- waits in the brush along the top of the arena.
//   Rush  -- runs straight at the player, fast, and stops short -- HALT px
//            from them (the book's "few inches", kept fair: never point-blank).
//   Spit  -- stands, and on its sprite's spit frame (idle frame 1: fur up,
//            fangs bared, spit flying) spits a fan of flecks at the player
//            and leaves a ring of stench that spreads slowly and lingers.
//   Flee  -- runs back up to a new spot in the brush.
//   Rushing and fleeing it plays its dash (53_come_at_a_body_dash, a low
//   flat-out gallop), facing the way it runs.
// Phase 2 (half HP): no lurking between rushes -- it rushes twice in a row,
//   from the halt straight into a second rush from a new angle -- a wider
//   spit, a thicker ring.
class ComeAtABody : public Enemy {
    enum State { LURK, RUSH, STAND, FLEE };
    static constexpr float HALT       = 120.0f;  // px short of the player it stops
    static constexpr float RUSH_SPEED = 330.0f;  // faster than a sprint (250): you dodge the spit, not the rush
    static constexpr float FLEE_SPEED = 220.0f;
    static constexpr float MIN_STAND  = 0.3f;    // it stands this long before it can spit: time to see it stop
    static constexpr float STRIDE_T   = 0.36f;   // seconds per gallop cycle (the dash sheet's 4 frames, 90 ms each)
    State state   = LURK;
    float t       = 0.0f;                        // seconds in this state
    float tx = 0, ty = 0;                        // where it's running to
    int   rushes  = 0;                           // rushes in this run of them
    bool  spat    = false;

    bool run_to(float dt, float speed) {         // true on arrival
        float dx = tx - x, dy = ty - y, d = sqrtf(dx * dx + dy * dy);
        float st = speed * dt;
        if (d <= st) { x = tx; y = ty; return true; }
        x += dx / d * st; y += dy / d * st;
        return false;
    }
    // Run at the player and stop HALT short -- on the line from here, or
    // swung `swing` radians around them (a second rush, from a new angle).
    void start_rush(float px, float py, float swing = 0.0f) {
        float a = aim_at(px, py, x, y) + swing;            // from the player, out to where it stops
        tx = fminf(fmaxf(px + cosf(a) * HALT, 40.0f), ARENA_W - 40.0f);
        ty = fminf(fmaxf(py + sinf(a) * HALT, ARENA_TOP + 40.0f), ARENA_H - 40.0f);
        state = RUSH; t = 0.0f;
    }
public:
    ComeAtABody() : Enemy(320, 110, 320, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "COME-AT-A-BODY"; }
    int         breath_frame()  const override { return 1; }    // its spit frame
    float       fire_interval() const override { return 99.0f; } // everything leaves on the spit
    int fire(float, float, BulletSpawn[], int) override { return 0; }
    bool running() const { return state == RUSH || state == FLEE; }
    int move_facing() const override {                           // running, it faces the way it runs
        return running() ? facing_toward(tx - x, ty - y) : -1;
    }
    float flap_phase() const override { return running() ? fmodf(t / STRIDE_T, 1.0f) : -1.0f; }
    void update(float dt, float px, float py) override {
        t += dt;
        switch (state) {
        case LURK:
            if (t >= (ENRAGED ? 0.6f : 1.4f)) { rushes = 0; start_rush(px, py); }
            break;
        case RUSH:
            if (run_to(dt, RUSH_SPEED)) { state = STAND; t = 0.0f; spat = false; }
            break;
        case STAND:
            if (spat && t >= 0.25f) {
                if (ENRAGED && ++rushes < 2) {
                    // Straight into a second rush, swinging round to a new side.
                    start_rush(px, py, (ernd() < 0.5f ? -1.2f : 1.2f));
                } else {
                    tx = 120.0f + ernd() * (ARENA_W - 240.0f);
                    ty = 80.0f + ernd() * 50.0f;
                    state = FLEE; t = 0.0f;
                }
            }
            break;
        case FLEE:
            if (run_to(dt, FLEE_SPEED)) { state = LURK; t = 0.0f; }
            break;
        }
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (state != STAND || spat || t < MIN_STAND) return 0;
        spat = true; t = 0.0f;
        float a = aim_at(x,y,px,py);
        int flecks = ENRAGED ? 7 : 5, n = 0;
        for (int i = 0; i < flecks; i++)                      // the spit: a fan, 0.2 apart
            out[n++] = mk(a + (i - (flecks - 1) * 0.5f) * 0.2f, 180.0f, 2.5f, 5.0f);
        int puffs = ENRAGED ? 10 : 8;
        float turn = ernd() * TAU;
        for (int i = 0; i < puffs; i++) {                     // the stench: a ring that spreads, slows, lingers
            BulletSpawn b = mk(turn + i * (TAU / puffs), 70.0f, 4.0f, 5.0f);
            b.accel = -50.0f; b.min_speed = 28.0f;
            out[n++] = b;
        }
        return n;
    }
};

// Beaver-sized fearsome critter of Boundary Pond, Maine (A Book of
// Creatures): long kangaroo hind legs, webbed feet, a strong hawk-like bill
// and a flat beaver tail. It hunts by "jumping above a surfacing fish and
// smacking it hard with its flat tail", and a grown one clears "over sixty
// yards in a single leap"; it's "usually heard and not seen". LOW tier,
// 340 HP, pond-water blue bullets.
// Phase 1 -- the leaps:
//   Stand -- on its spring frame (idle frame 1: legs straight, tail flung up)
//            the tail flicks a fan of 4 droplets at the player.
//   Leap  -- a long, high bound to above where the player was when it
//            jumped (LAND_ABOVE px over them -- the fish under it -- never on
//            them), landing with a splash: two rings of 14, the second slower
//            and turned half a step.
// Phase 2 (half HP) -- the tail (the user's design): it leaps clean off the
//   top of the screen ("heard and not seen"), is gone a moment, and drops in
//   above where the player is NOW; then turns its back and hammers its tail
//   down (54_billdad_slap, this phase's sheet), and on the impact frame a
//   MASSIVE SHOCKWAVE bursts out -- four staggered rings, 108 bullets (1.5x
//   the first cut, the user's call), that slow right down, leaving a field of
//   crawling bullets to thread. Flicks 5 between.
class Billdad : public Enemy {
    enum State { STAND, LEAP, GONE, DROP, SLAP };
    static constexpr float LAND_ABOVE = 100.0f;  // px above the player it lands
    static constexpr float LEAP_T  = 0.7f;       // seconds in a bound
    static constexpr float DROP_T  = 0.35f;      // phase 2: seconds falling back in
    static constexpr float GONE_T  = 0.6f;       // phase 2: seconds off screen
    static constexpr float SLAP_T  = 0.6f;       // seconds of the tail slap (the slap sheet's 4 frames)
    State state = STAND;
    float t = 0.0f;
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0;        // this bound's start and landing
    enum Pending { NONE, SPLASH, SHOCKWAVE } pending = NONE;

    void land_above(float px, float py) {
        x1 = fminf(fmaxf(px, 70.0f), ARENA_W - 70.0f);
        y1 = fminf(fmaxf(py - LAND_ABOVE, ARENA_TOP + 45.0f), 280.0f);
    }
public:
    Billdad() : Enemy(320, 140, 340, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "BILLDAD"; }
    int         breath_frame()  const override { return 1; }     // its spring frame
    float       fire_interval() const override { return 0.05f; } // only sends a splash or shockwave when one's due
    float flap_phase() const override { return state == SLAP ? fminf(t / SLAP_T, 0.999f) : -1.0f; }
    void update(float dt, float px, float py) override {
        float prev = t;
        t += dt;
        switch (state) {
        case STAND:
            if (t >= (ENRAGED ? 1.1f : 1.2f)) {
                x0 = x; y0 = y; t = 0.0f; state = LEAP;
                if (ENRAGED) { x1 = x; y1 = ARENA_TOP - 60.0f; }              // off the top
                else         land_above(px, py);
            }
            break;
        case LEAP: {
            float k = fminf(t / LEAP_T, 1.0f), e = k * k * (3.0f - 2.0f * k);
            x = x0 + (x1 - x0) * e;
            y = y0 + (y1 - y0) * e - 70.0f * sinf(PI * k);                    // a long, high bound
            if (k >= 1.0f) {
                t = 0.0f;
                if (y1 < ARENA_TOP) state = GONE;
                else { state = STAND; pending = SPLASH; }
            }
            break;
        }
        case GONE:
            if (t >= GONE_T) { land_above(px, py); x = x1; y = y0 = ARENA_TOP - 60.0f; t = 0.0f; state = DROP; }
            break;
        case DROP: {
            float k = fminf(t / DROP_T, 1.0f);
            y = y0 + (y1 - y0) * k * k;                                       // falling: speeds up
            if (k >= 1.0f) { t = 0.0f; state = SLAP; }
            break;
        }
        case SLAP:
            // The impact: the slap sheet's frame 2 begins halfway through.
            if (prev < SLAP_T * 0.5f && t >= SLAP_T * 0.5f) pending = SHOCKWAVE;
            if (t >= SLAP_T) { t = 0.0f; state = STAND; }
            break;
        }
    }
    int fire(float, float, BulletSpawn out[], int) override {
        Pending p = pending;
        pending = NONE;
        if (p == SPLASH) {                                   // phase 1 landing: a double splash
            float turn = ernd() * TAU;
            int n = 0;
            for (int r = 0; r < 2; r++)
                for (int i = 0; i < 14; i++) out[n++] = mk(turn + (i + r * 0.5f) * (TAU / 14), 125.0f - r * 35.0f, 3.0f, 5.0f);
            return n;
        }
        if (p != SHOCKWAVE) return 0;
        // The shockwave: four rings of 27, each turned a different share of a
        // step (0, 1/2, 1/4, 3/4), fast to slow, all braking hard to a crawl --
        // a spreading field of slow bullets, staggered so there's always a way
        // through (gaps ~23 px at the player's 100 px, 14 clear).
        const int N = 27;
        static const float STAGGER[4] = { 0.0f, 0.5f, 0.25f, 0.75f };
        float turn = ernd() * TAU;
        int n = 0;
        for (int r = 0; r < 4; r++)
            for (int i = 0; i < N; i++) {
                BulletSpawn b = mk(turn + (i + STAGGER[r]) * (TAU / N), 210.0f - r * 38.0f, 3.0f, 5.0f);
                b.accel = -220.0f; b.min_speed = 28.0f + r * 4.0f;
                out[n++] = b;
            }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (state != STAND) return 0;
        float a = aim_at(x,y,px,py);
        int n = ENRAGED ? 5 : 4;                                              // the tail's flick of droplets
        for (int i = 0; i < n; i++) out[i] = mk(a + (i - (n - 1) * 0.5f) * 0.22f, 170.0f, 2.5f, 5.0f);
        return n;
    }
};

// Dachshund-sized fearsome critter of the Pacific Coast forests (A Book of
// Creatures): velvety fur, woodpecker feet and a spike-tipped tail; it humps
// like an inchworm "effortlessly up the tallest of trees" to feed on bracket
// fungus, and mittens made of its fur kept climbing -- "last seen clambering
// over lumber slash". LOW tier, 360 HP, velvet violet bullets.
// Phase 1 (the first third of its HP, the user's design) -- on all fours in
//   the middle of the arena:
//   Hump   -- on its inchworm-hump frame (idle frame 1: arched, tail cocked)
//             the spiked tail throws a double fan of spikes at the player: 7
//             fast, and 6 slower ones in their gaps.
//   Spores -- every 2 s a ring of 20 bracket-fungus spores drifts out slowly.
// Phase 2 (from 66% HP, the user's design): it humps off to the left or
//   right side -- same height -- and STAYS there reared up on its back legs
//   (55_wapaloosie_up, the alt idle), and lumber slash comes RAINING DOWN:
//   big logs (55_wapaloosie_log, outlined in its bullet violet) falling
//   straight down from out of sight above the top, rolling (the sheet's
//   frames) and rocking by its sheet's hand-tilted rows. No engine rotation:
//   turned pixels broke the game's 2px grid. Each roll, as the log's branch
//   stub comes round underneath (roll frames 4-5), bark flies off it: two
//   chips sprayed down either side of its fall, so every log trails a fan
//   you dodge along with it. On the reared-up breath frame (chest up) it
//   sends a spore ring.
class Wapaloosie : public Enemy {
    static constexpr float HOME_Y   = 150.0f;
    static constexpr float SIDE_X   = 120.0f;   // px in from the wall it settles at, phase 2
    static constexpr float HUMP_SPD = 110.0f;   // px/s getting there
    static constexpr float SPORE_EVERY = 2.0f, LOG_EVERY = 0.85f;
    float tx      = -1.0f;                      // phase 2: the side it goes to (-1 = not chosen)
    float spore_t = 0.0f, log_t = 0.0f;
    bool  spores  = false;

    float phase2_at() const override { return 0.66f; }   // its own phase line: a third down
    bool reared() const { return hp < max_hp * phase2_at(); }
    static int spore_ring(BulletSpawn out[]) {
        const int N = 20;
        float turn = ernd() * TAU;
        for (int i = 0; i < N; i++) {
            BulletSpawn b = mk(turn + i * (TAU / N), 95.0f, 3.5f, 5.0f);
            b.accel = -60.0f; b.min_speed = 35.0f;
            out[i] = b;
        }
        return N;
    }
public:
    Wapaloosie() : Enemy(320, HOME_Y, 360, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "WAPALOOSIE"; }
    int         breath_frame()  const override { return 1; }       // the hump / chest up
    bool        alt_pose()      const override { return reared() && tx >= 0.0f && fabsf(tx - x) <= 1.0f; }   // up once it's there
    float       fire_interval() const override { return 0.05f; }   // sends spores / logs when due
    void update(float dt, float, float) override {
        if (!reared()) {
            if ((spore_t += dt) >= SPORE_EVERY) { spore_t = 0.0f; spores = true; }
            return;
        }
        if (tx < 0.0f) tx = ernd() < 0.5f ? SIDE_X : ARENA_W - SIDE_X;
        float d = tx - x;
        if (fabsf(d) > 1.0f) x += (d > 0 ? 1.0f : -1.0f) * fminf(HUMP_SPD * dt, fabsf(d));
        log_t += dt;
    }
    int fire(float, float, BulletSpawn out[], int) override {
        if (spores) { spores = false; return spore_ring(out); }
        if (!reared() || log_t < LOG_EVERY) return 0;
        log_t = 0.0f;
        // A big log falling straight down at a random spot, from just out of
        // sight above the top, rolling as it falls; one at a time, 0.85 s
        // apart -- ~150 px of fall between them. Its capsule matches the
        // sprite's body: 82 x 16 on screen (its branch stub doesn't count).
        BulletSpawn b = mk(PI / 2, 140.0f + ernd() * 50.0f, 8.0f, 5.0f);
        b.half_len = 33.0f;
        // Bark off the stub: the sheet rolls 8 frames x 90 ms, the stub is
        // underneath on frames 4-5, so mid-way through them -- 0.45 s in --
        // and every full roll (0.72 s) after.
        b.shed_first = 0.45f; b.shed_every = 0.72f;
        b.shed_n = 2; b.shed_spread = 1.1f; b.shed_speed = 210.0f;
        b.from = true;
        b.ox = 50.0f + ernd() * (ARENA_W - 100.0f);
        b.oy = ARENA_TOP - (b.half_len + b.radius);                          // just out of sight
        out[0] = b;
        return 1;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (alt_pose()) return spore_ring(out);                 // reared up: the tail lies behind; spores
        if (reared()) return 0;                                 // humping over to its side
        float a = aim_at(x,y,px,py);
        int n = 0;
        for (int i = 0; i < 7; i++) out[n++] = mk(a + (i - 3) * 0.2f, 190.0f, 2.5f, 5.0f);          // fast fan
        for (int i = 0; i < 6; i++) out[n++] = mk(a + (i - 2.5f) * 0.2f, 135.0f, 2.5f, 5.0f);       // slower, in its gaps
        return n;
    }
};

// Paul Bunyan's moskitto (A Book of Creatures): the Chippewa River
// mosquitos, "large enough to straddle a stream, pick lumberjacks off logs as
// they floated by, and drain them dry", crossed with the "deadly fighting
// bumblebees from Texas" Bunyan brought in to fight them -- the young had
// "stingers at both ends". LOW tier (the top of it), 380 HP, bee-yellow
// bullets. BIG sprite, always in the air (the user: it never lands).
// Phase 1 -- hovering back and forth across the top:
//   Needle  -- each time the proboscis reaches furthest forward (its sheet's
//              frame 4) it stabs a quick line of 4 needles at the player.
//   Wings   -- each time its wingbeat cycle completes (the sheet wraps to
//              frame 0, the user's timing) it flings 3 stings out of its
//              wings, AWAY from the player; they ricochet off the walls and
//              come back.
// Phase 2 (half HP) -- "pick lumberjacks off logs" (the user's design):
//   every 4 s it stops and buzzes in place (the warning, 0.6 s), swoops in
//   fast to GRAB_NEAR px off the player, then CHASES them, flying straight at
//   them for GRAB_T s at GRAB_SPEED -- faster than walking (160) or crouching
//   (70), slower than a sprint (250): only sprinting gets away. Touching it
//   costs a bar. Then it gives up and climbs back to its beat. Needles 6,
//   stings 5.
class Moskitto : public Enemy {
    enum State { HOVER, WIND, SWOOP, CHASE, RISE };
    static constexpr float WIND_T = 0.6f, RISE_T = 0.8f, DIVE_EVERY = 4.0f;
    static constexpr float SWOOP_SPEED = 380.0f;  // closing in
    static constexpr float GRAB_NEAR   = 120.0f;  // px off the player the chase starts
    static constexpr float GRAB_SPEED  = 230.0f;  // the chase: walking can't outrun it, sprinting can
    static constexpr float GRAB_T      = 2.0f;
    State state = HOVER;
    float t = 0.0f, beat = 0.0f, since_dive = 0.0f;
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0;

    void hover_point(float& hx, float& hy) const {
        hx = 320.0f + 190.0f * sinf(beat * 0.5f);
        hy = 125.0f + 18.0f * sinf(beat * 1.1f);
    }
public:
    Moskitto() : Enemy(320, 125, 380, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()           const override { return "MOSKITTO"; }
    float       fire_interval()  const override { return 99.0f; }   // everything leaves on its frames
    bool        grabbing()       const { return state == SWOOP || state == CHASE; }
    // Lunging, its grab sheet (56_moskitto_grab): legs snapping open and shut, 70 ms a frame.
    float flap_phase() const override { return grabbing() ? fmodf(t / 0.28f, 1.0f) : -1.0f; }
    float       contact_damage() const override { return grabbing() ? 5.0f : 0.0f; }
    int move_facing() const override {                          // lunging, it faces where it flies
        return grabbing() ? facing_toward(x1 - x, y1 - y) : -1;
    }
    void update(float dt, float px, float py) override {
        t += dt;
        switch (state) {
        case HOVER:
            beat += dt;
            hover_point(x, y);
            if (ENRAGED && (since_dive += dt) >= DIVE_EVERY) {
                since_dive = 0.0f; state = WIND; t = 0.0f;
                x0 = x; y0 = y;
            }
            break;
        case WIND:                                               // buzzing in place: a 2px shiver
            x = x0 + ((int)(t * 40.0f) % 2 ? 2.0f : -2.0f);
            if (t >= WIND_T) { x = x0; t = 0.0f; state = SWOOP; }
            break;
        case SWOOP:                                              // in fast, to just off the player
        case CHASE: {                                            // then straight at them
            x1 = px; y1 = py;
            float dx = px - x, dy = py - y, d = sqrtf(dx * dx + dy * dy);
            if (state == SWOOP && d <= GRAB_NEAR) { state = CHASE; t = 0.0f; }
            float st = (state == SWOOP ? SWOOP_SPEED : GRAB_SPEED) * dt;
            if (d > 1.0f) { x += dx / d * fminf(st, d); y += dy / d * fminf(st, d); }
            if (state == CHASE && t >= GRAB_T) { t = 0.0f; state = RISE; x0 = x; y0 = y; }
            break;
        }
        case RISE: {
            float hx, hy; hover_point(hx, hy);
            float k = fminf(t / RISE_T, 1.0f), e = k * k * (3.0f - 2.0f * k);
            x = x0 + (hx - x0) * e; y = y0 + (hy - y0) * e;
            if (k >= 1.0f) state = HOVER;
            break;
        }
        }
    }
    int fire(float, float, BulletSpawn[], int) override { return 0; }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (state != HOVER) return 0;
        if (frame == 0) {                                       // the wingbeat cycle done: stings off the wings
            float away = aim_at(px, py, x, y);                  // from the player, out past it
            int n = ENRAGED ? 5 : 3;
            for (int i = 0; i < n; i++)
                out[i] = mkb(away + (i - (n - 1) * 0.5f) * 0.45f, 200.0f, 3.0f, 5.0f);
            return n;
        }
        if (frame == 4) {                                       // proboscis at full reach: the needle
            float a = aim_at(x,y,px,py);
            int n = ENRAGED ? 6 : 4;                            // one line, fast at the front
            for (int i = 0; i < n; i++) out[i] = mk(a, 170.0f + i * 25.0f, 2.5f, 5.0f);
            return n;
        }
        return 0;
    }
};

// The Aztec "tortoise-rabbit", the armadillo (A Book of Creatures, from
// Topsell): "no bigger than a cat", with a "segmented, lobster-like shell
// resembling the trappings of a horse", and it "protects itself with that
// shell such that neither its head nor neck are clearly visible, with only
// the ears sticking out". LOW tier, 320 HP, shell-tan bullets.
// It only ever moves curled in its ball (66_ayotochtli_roll, the user's
// design: "in its ball and just rolling around fast"):
//   Stand -- uncurled; on its hunch frame (idle frame 1: bands bunched, head
//            drawn in) it sheds a ring of shell plates.
//   Roll  -- curls up and rolls off fast toward the player, glancing off the
//            walls like a ball, leaving a STRAIGHT LINE of plates along its
//            path that then breaks up -- each plate sits a moment, then
//            drifts off in a random direction, so the line dissolves behind
//            it into scatter (the user's design). Rolling into the player
//            costs a bar.
//            Curled up its shell takes the hits: shots do HALF damage while
//            it rolls, so hit it when it stands.
// Phase 2 (half HP): it stands less and rolls longer and faster, and every
//   wall it glances off bursts a ring of plates.
class Ayotochtli : public Enemy {
    static constexpr float ROLL_T_FRAME = 0.28f;  // the roll sheet's 4 frames at 70 ms
    bool  rolling = false;
    float t = 0.0f, wake_t = 0.0f;
    float vx = 0.0f, vy = 0.0f;
    int   bursts = 0;                              // wall bounces waiting to burst (phase 2)
    bool  wake   = false;

    float roll_speed() const { return ENRAGED ? 360.0f : 300.0f; }
    static int plate_ring(int n, float speed, BulletSpawn out[]) {
        float turn = ernd() * TAU;
        for (int i = 0; i < n; i++) out[i] = mk(turn + i * (TAU / n), speed, 3.0f, 5.0f);
        return n;
    }
public:
    Ayotochtli() : Enemy(320, 140, 320, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()           const override { return "AYOTOCHTLI"; }
    int         breath_frame()   const override { return 1; }      // hunched into its shell
    float       fire_interval()  const override { return 0.05f; }  // the wake and the bursts
    float       armor()          const override { return rolling ? 0.5f : 1.0f; }
    float       contact_damage() const override { return rolling ? 5.0f : 0.0f; }
    float       flap_phase()     const override { return rolling ? fmodf(t / ROLL_T_FRAME, 1.0f) : -1.0f; }
    int         move_facing()    const override { return rolling ? facing_toward(vx, vy) : -1; }
    void update(float dt, float px, float py) override {
        t += dt;
        if (!rolling) {
            if (t >= (ENRAGED ? 0.8f : 1.5f)) {
                // Off toward the player, a little to one side.
                float a = aim_at(x, y, px, py) + (ernd() * 2.0f - 1.0f) * 0.4f;
                vx = cosf(a) * roll_speed(); vy = sinf(a) * roll_speed();
                rolling = true; t = 0.0f; wake_t = 0.0f;
            }
            return;
        }
        x += vx * dt; y += vy * dt;
        const float L = 40.0f, R = ARENA_W - 40.0f, T = ARENA_TOP + 40.0f, B = ARENA_H - 40.0f;
        if (x < L) { x = L; vx =  fabsf(vx); bursts++; }
        if (x > R) { x = R; vx = -fabsf(vx); bursts++; }
        if (y < T) { y = T; vy =  fabsf(vy); bursts++; }
        if (y > B) { y = B; vy = -fabsf(vy); bursts++; }
        if ((wake_t += dt) >= 0.06f) { wake_t = 0.0f; wake = true; }   // a plate every ~18 px of path
        if (t >= (ENRAGED ? 3.2f : 2.4f)) { rolling = false; t = 0.0f; bursts = 0; }
    }
    int fire(float, float, BulletSpawn out[], int) override {
        if (!rolling) return 0;
        int n = 0;
        if (bursts && ENRAGED) { bursts = 0; n += plate_ring(10, 110.0f, out); }   // the wall it hit
        bursts = 0;
        if (wake) {
            // A plate left where it rolled: it sits (the line), then after
            // its own moment drifts off any which way (the line dissolving).
            wake = false;
            BulletSpawn b = mk(0.0f, 0.0f, 3.0f, 5.0f);
            b.delay        = 0.8f + ernd() * 0.4f;
            b.launch_speed = 55.0f + ernd() * 45.0f;
            b.launch_off   = (ernd() * 2.0f - 1.0f) * PI;          // any direction at all
            out[n++] = b;
        }
        return n;
    }
    int breathe(float, float, BulletSpawn out[], int) override {
        if (rolling) return 0;
        return plate_ring(ENRAGED ? 16 : 12, 120.0f, out);
    }
};

// Pliny's lagopus, the "hare-foot" -- the ptarmigan (A Book of Creatures):
// "the size of a pigeon and white all over", its "feet are covered with hair
// like those of a hare's foot", and by Albertus Magnus' reckoning "the
// lagopus cannot fly well". LOW tier, 340 HP, snow-white-blue bullets.
// Flight: every few seconds it takes off for a new perch (67_lagopus_fly,
//   true 8 directions) -- clumsily, the book says it can't fly well: the
//   flight wobbles from side to side. Landing it scatters a ring of snow.
// Phase 1 (the user's design): perched, it quickly builds a RING of snow
//   around itself -- flake after flake sweeping round the first row, then
//   the next out, row upon row, each flashing as it appears, until half a
//   second before take-off (~11 rows) -- and every row it finishes sends a
//   separate ring of 12 flying out; the moment it takes off, the
//   whole ring is let fly at the player, flake after flake, as it flies away.
// Phase 2 (half HP) -- a blizzard, topping phase 1 (the user's call): it
//   still builds the ring every perch, faster (3 flakes a frame), and each
//   finished row's ring is 16 and turns the OTHER way from the last, so the
//   lanes cross into a lattice; at take-off the ring bursts at the player
//   loosely (each flake a little off-line). On top of that its wings, always
//   spread and rippling (the user's idle), throw on each ripple -- tips up
//   (idle frame 1): feathers off both wingtips, out to the sides and down;
//   tips down (idle frame 2): a puff of snow at the player. It flies more
//   often, the wobble grows, and every wingbeat in the air beats a gust of 5
//   feathers at the player.
class Lagopus : public Enemy {
    static constexpr float BEAT_T = 0.44f;   // a wingbeat: the fly sheet's 4 frames at 110 ms
    bool  flying = false;
    float t = 0.0f;
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    int   beats = 0;                          // wingbeats done this flight
    bool  landed = false, gust = false;
    int   flakes = 0;                         // ... flakes in it so far this perch
    float build = 0.0f;                       // ... flakes owed: built by time, not by frame
    static constexpr int   RING_N      = 24;  // flakes to a circle
    static constexpr float ROW_GAP     = 12.0f;   // px between circles
    static constexpr float STOP_BUILD  = 0.5f;    // s before take-off it stops adding

    float fly_t()   const { return ENRAGED ? 0.9f : 1.1f; }
    float perch_t() const { return ENRAGED ? 1.6f : 2.8f; }
public:
    Lagopus() : Enemy(320, 150, 340, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "LAGOPUS"; }
    float       fire_interval() const override { return 0.016f; }  // every frame: the ring builds fast
    float       flap_phase()    const override { return flying ? fmodf(t / BEAT_T, 1.0f) : -1.0f; }
    int         move_facing()   const override { return flying ? facing_toward(x1 - x0, y1 - y0) : -1; }
    void update(float dt, float, float) override {
        t += dt;
        if (!flying) build += dt * (ENRAGED ? 180.0f : 120.0f);   // flakes a second (3 / 2 a frame at 60 fps)
        if (!flying) {
            if (t >= perch_t()) {
                x0 = x; y0 = y;
                do { x1 = 100.0f + ernd() * (ARENA_W - 200.0f); } while (fabsf(x1 - x) < 120.0f);
                y1 = 100.0f + ernd() * 100.0f;
                flying = true; t = 0.0f; beats = 0; flakes = 0; build = 0.0f;
            }
            return;
        }
        float k = fminf(t / fly_t(), 1.0f), e = k * k * (3.0f - 2.0f * k);
        // Clumsy: it wobbles side to side across its line, and lifts in an arc.
        float dx = x1 - x0, dy = y1 - y0, len = sqrtf(dx * dx + dy * dy) + 0.001f;
        float wob = (ENRAGED ? 22.0f : 14.0f) * sinf(k * PI * 4.0f) * sinf(k * PI);
        x = x0 + dx * e - dy / len * wob;
        y = y0 + dy * e + dx / len * wob - 30.0f * sinf(PI * k);
        if ((int)(t / BEAT_T) > beats) { beats++; if (ENRAGED) gust = true; }
        if (k >= 1.0f) { flying = false; t = 0.0f; landed = true; }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (!flying && t < perch_t() - STOP_BUILD) {
            // The next flakes round the ring, one row after another, two a
            // frame (a row in ~0.2 s), row upon row outward until half a
            // second before take-off -- ~11 rows on a full perch. Each
            // flashes in, hangs there until the take-off -- its delay runs out
            // exactly then, one after another, so the ring leaves as a stream
            // -- then flies at wherever the player is.
            int n = 0;
            for (; build >= 1.0f && n < 100; build -= 1.0f, flakes++) {   // room left in the 128 volley for a row ring
                int row = flakes / RING_N, k = flakes % RING_N;
                if (k == 0 && row > 0) {
                    // A row just finished: a separate ring flies out from it
                    // (the user's design) -- 12 round, each turned a little on
                    // from the last, so the lanes between them curve slowly.
                    // Phase 2: 16, alternating which way they turn -- crossing lanes.
                    int   rn   = ENRAGED ? 16 : 12;
                    float turn = ENRAGED ? (row % 2 ? 1.0f : -1.0f) * row * 0.06f : row * 0.06f;
                    for (int i = 0; i < rn; i++)
                        out[n++] = mk(turn + i * (TAU / rn), 120.0f, 3.0f, 5.0f);
                }
                float a = (k + row * 0.33f) * (TAU / RING_N), r = 40.0f + row * ROW_GAP;
                BulletSpawn b = mk(0.0f, 0.0f, 3.0f, 5.0f);
                b.from = true; b.ox = x + cosf(a) * r; b.oy = y + sinf(a) * r;
                // Never on the player: a flake whose spot is within 40 px of
                // them is left out (the tester caught unwarned hits from
                // mines made on top of the player).
                float ddx = b.ox - px, ddy = b.oy - py;
                if (ddx * ddx + ddy * ddy < 40.0f * 40.0f) continue;
                b.delay        = (perch_t() - t) + flakes * 0.005f;   // the stream: ~1.4 s for a full ring
                b.launch_speed = 190.0f;
                b.launch_off   = ENRAGED ? (ernd() * 2.0f - 1.0f) * 0.12f : 0.0f;   // phase 2: a looser burst
                b.flash_in     = true;
                out[n++] = b;
            }
            return n;
        }
        if (landed) {                                         // landing: snow thrown up all round
            landed = false;
            float turn = ernd() * TAU;
            for (int i = 0; i < 12; i++) out[i] = mk(turn + i * (TAU / 12), 105.0f, 3.0f, 5.0f);
            return 12;
        }
        if (gust) {                                           // a downbeat in the air: 3 feathers at the player
            gust = false;
            float a = aim_at(x,y,px,py);
            for (int i = 0; i < 5; i++) out[i] = mk(a + (i - 2) * 0.22f, 190.0f, 2.5f, 5.0f);
            return 5;
        }
        return 0;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (flying || !ENRAGED) return 0;                     // the ripples throw in phase 2
        int n = 0;
        if (frame == 1) {                                     // tips up: feathers off both wingtips
            for (int side = -1; side <= 1; side += 2)
                for (int i = 0; i < 3; i++) {
                    float a = PI / 2 - side * (1.15f - i * 0.22f);   // out to the side, angled down
                    out[n++] = mk(a, 175.0f, 2.5f, 5.0f);
                }
            return n;
        }
        if (frame == 2) {                                     // tips down: a puff of snow at the player
            float a = aim_at(x,y,px,py);
            for (int i = 0; i < 6; i++) {
                BulletSpawn b = mk(a + (ernd() * 2.0f - 1.0f) * 0.35f, 150.0f + ernd() * 50.0f, 3.0f, 5.0f);
                b.accel = -90.0f; b.min_speed = 70.0f;
                out[n++] = b;
            }
            return n;
        }
        return 0;
    }
};

// The shuyu of the Peng River (A Book of Creatures, from the Shanhaijing):
// a chicken with "red feathers", "four heads (or four eyes), six feet, and
// three tails"; it "caws like a magpie". LOW tier, 360 HP, red-feather
// bullets.
// Phase 1 -- its heads pluck at the air two at a time (the user's idle), and
//   every jab throws:
//   Idle frame 1 -- the front-left head jabs forward: a fan of 3 pecks from
//                   that head at the player; the back-right head jabs up: 2
//                   shots up and right that ricochet off the top wall and
//                   come down.
//   Idle frame 2 -- the same from the other pair: front-right pecks, back-left
//                   up and left.
// Phase 2 (half HP, the user's design: "it flaps its wings") -- heads up and
//   still, wings beating (68_shuyu_flap): every downstroke beats a fan of 5
//   feathers at the player, and every fourth beat it CAWS -- a ring of 20
//   with four gaps, one for each head.
class Shuyu : public Enemy {
    static constexpr float BEAT_T = 0.44f;   // a wingbeat: the flap sheet's 4 frames at 110 ms
    float t = 0.0f;
    int   beats = 0;
    bool  down = false;

    // A head's mouth: off the body toward the player, `side` -1 left / +1
    // right of the line to them; `up` for the back pair, raised.
    void head(float px, float py, int side, bool up, float& hx, float& hy) const {
        float a = aim_at(x, y, px, py);
        float fx = cosf(a), fy = sinf(a);
        hx = x + fx * (up ? 2.0f : 10.0f) - fy * side * 10.0f;
        hy = y + fy * (up ? 2.0f : 10.0f) + fx * side * 10.0f - (up ? 12.0f : 0.0f);
    }
    int jab(float px, float py, int side, BulletSpawn out[]) const {
        int n = 0;
        float hx, hy;
        head(px, py, side, false, hx, hy);                  // front head: pecks at the player
        float a = aim_at(hx, hy, px, py);
        for (int i = 0; i < 3; i++) {
            BulletSpawn b = mk(a + (i - 1) * 0.2f, 175.0f, 2.5f, 5.0f);
            b.from = true; b.ox = hx; b.oy = hy;
            out[n++] = b;
        }
        head(px, py, -side, true, hx, hy);                  // back head, the other side: up, to ricochet
        for (int i = 0; i < 2; i++) {
            BulletSpawn b = mkb(-PI / 2 - side * (0.3f + i * 0.25f), 170.0f, 3.0f, 5.0f);
            b.from = true; b.ox = hx; b.oy = hy;
            out[n++] = b;
        }
        return n;
    }
public:
    Shuyu() : Enemy(320, 150, 360, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "SHUYU"; }
    float       fire_interval() const override { return 0.05f; }   // the downstrokes, when due
    float       flap_phase()    const override { return ENRAGED ? fmodf(t / BEAT_T, 1.0f) : -1.0f; }
    void update(float dt, float, float) override {
        if (!ENRAGED) return;
        float prev = fmodf(t / BEAT_T, 1.0f);
        t += dt;
        float now = fmodf(t / BEAT_T, 1.0f);
        if (prev < 0.5f && now >= 0.5f) { down = true; beats++; }   // frame 2 of the beat: wings down
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (!down) return 0;
        down = false;
        int n = 0;
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < 5; i++) out[n++] = mk(a + (i - 2) * 0.22f, 185.0f, 2.5f, 5.0f);
        if (beats % 4 == 0) {                                // the caw: four gaps, one a head
            float turn = a + PI / 4;
            for (int i = 0; i < 20; i++) {
                if (i % 5 == 0) continue;
                out[n++] = mk(turn + i * (TAU / 20), 120.0f, 3.0f, 5.0f);
            }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) return 0;                               // heads up and still while it flaps
        if (frame == 1) return jab(px, py, -1, out);         // front-left pecks, back-right up
        if (frame == 2) return jab(px, py, +1, out);         // front-right pecks, back-left up
        return 0;
    }
};

// Bes Chem, the Malaysian bird spirit (A Book of Creatures, from Werner): in
// the jungle it sits in the great branches calling "e... e... e...", and
// when someone passes underneath it "scatters tiny, poisonous feathers onto
// the interloper" -- they "cause anyone they touch to become thin forever";
// another comes to the village at night calling "pok... pok...". LOW tier,
// 380 HP, glowing eye-yellow bullets.
// Phase 1 -- perched up high:
//   e... e... e... -- on its open-mouth frame (idle frame 1, the fanged
//                     mouth in its chest gaping) three rings, one inside the
//                     next, each turned a third of a step: three calls.
//   Feathers       -- tiny poison feathers keep drifting down from the canopy
//                     (the top of the arena) above the player; stand right
//                     under it and they come thick.
// Phase 2 (half HP) -- "pok... pok...": every 2 s two big slow orbs at the
//   player, each shedding a cross of tiny feathers as it drifts; the calls
//   become four rings and the feathers fall faster.
class BesChem : public Enemy {
    float feather_t = 0.0f, pok_t = 0.0f;
    float px_ = 320.0f, py_ = 400.0f;          // where the player is, for the canopy

    bool under() const { return fabsf(px_ - x) < 60.0f && py_ > y; }
public:
    // Perched off to one side: the player starts at the middle, and right
    // under it the heavy rain would fall from the first moment.
    BesChem() : Enemy(200, 120, 380, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "BES CHEM"; }
    int         breath_frame()  const override { return 1; }       // the chest mouth gaping
    float       fire_interval() const override { return 0.05f; }   // feathers and poks, when due
    void update(float dt, float px, float py) override {
        px_ = px; py_ = py;
        feather_t += dt;
        if (ENRAGED) pok_t += dt;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        float every = under() ? 0.08f : (ENRAGED ? 0.16f : 0.25f);
        if (feather_t >= every) {
            // A tiny feather from the canopy, somewhere above the player,
            // drifting down a little aslant.
            feather_t = 0.0f;
            BulletSpawn b = mk(PI / 2 + (ernd() * 2.0f - 1.0f) * 0.25f, 75.0f + ernd() * 35.0f, 2.0f, 5.0f);
            b.from = true;
            b.ox = fminf(fmaxf(px + (ernd() * 2.0f - 1.0f) * 110.0f, 10.0f), ARENA_W - 10.0f);
            b.oy = ARENA_TOP + 2.0f;
            out[n++] = b;
        }
        if (pok_t >= 2.0f) {
            // Pok... pok...: two big slow orbs, each shedding a cross of
            // tiny feathers every half second as it comes.
            pok_t = 0.0f;
            float a = aim_at(x,y,px,py);
            for (int i = 0; i < 2; i++) {
                BulletSpawn b = mk(a + (i ? 0.35f : -0.35f), 85.0f, 6.0f, 5.0f);
                b.shed_first = 0.5f; b.shed_every = 0.5f;
                b.shed_n = 4; b.shed_spread = TAU * 0.75f; b.shed_speed = 90.0f;   // 4 ways round
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float, float, BulletSpawn out[], int) override {
        // e... e... e...: a ring per call, each slower and turned a share
        // of a step, so they leave as rings one inside the next.
        int calls = ENRAGED ? 4 : 3, n = 0;
        const int N = 14;
        float turn = ernd() * TAU;
        for (int c = 0; c < calls; c++)
            for (int i = 0; i < N; i++)
                out[n++] = mk(turn + (i + c / (float)calls) * (TAU / N), 150.0f - c * 25.0f, 3.0f, 5.0f);
        return n;
    }
};

// The dingbat of Rice Lake, Wisconsin (A Book of Creatures): "a terrifying
// hybrid of bird and mammal", "a short, feathered body, short antlers, and
// large wings", that specializes "in tormenting hunters" -- catching bullets
// in mid-air among its pranks; "any seemingly sure-fire shot that misses its
// mark is the work of a dingbat". MEDIUM tier, 420 HP (only hurt half the time), owl-buff bullets.
// BIG sheet, always in the air.
// The user's design: it can only be hurt WHILE IT MOVES.
//   Glide -- it moves slowly from perch to perch across the top, open to
//            the player's shots, dropping a 3-fan at the player as it goes.
//   Perch -- hanging still, it CATCHES: any shot that comes within CATCH px
//            (its catching pose, 57_dingbat_catch) is snatched out of the air and
//            REFLECTED straight back at the player from where it was caught.
//            Each downstroke of its long wings (idle frame 2) throws a fan
//            of 9 at the player.
//   Stare -- the user asked for a slow, intricate pattern that matches the
//            owl: perched, every STARE_EVERY s, it beats its cupped wings and
//            its eyes flare (57_dingbat_stare, played once) -- and on the
//            flare, from its two great round eyes, two
//            rings spread slowly -- the left one turning clockwise, the right
//            one anticlockwise -- each with three gaps, so as they cross the
//            openings slide past each other and safe spots open and close.
//            Each fades after STARE_LIFE s.
//   Feathers -- each downstroke of its long wings (idle frame 2), perched,
//            sheds 7 feathers at the player that drift and sway as they slow,
//            curving left and right in turn.
// Every shot it fires -- stare, feathers, glide fans, reflections -- slows to
//   the same FLOW speed by SETTLE px out, each with the deceleration that gets
//   it there, so past that line everything moves together and flows evenly
//   (the user's call).
// Phase 2 (half HP): every shot it catches also sets off a RING of 14 from it
//   (no more than one every RING_CD s, so a hail of shots is a hail of rings,
//   not a wall) -- shooting into its block is punished hard; each caught shot
//   comes back as two, the glides are
//   quicker, the perches shorter, and it stares more often.
class Dingbat : public Enemy {
    static constexpr float CATCH = 72.0f;    // past its body circle (~52): no shot reaches it while it perches
    bool  gliding = false;
    float t = 0.0f, drop_t = 0.0f, stare_t = 1.0f;
    static constexpr float STARE_ANIM = 0.32f;   // the stare sheet's 4 frames, 80 ms each
    float stare_anim = -1.0f;                    // seconds into the stare's wingbeat (-1 = not staring)
    bool  stare_due = false;                     // the flare frame reached: the rings go
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    float px_ = 320.0f, py_ = 400.0f;
    struct Back { float x, y; } back[32];
    int   nback = 0;
    static constexpr float RING_CD = 0.2f;
    int   rings_due = 0;                    // phase 2: catches waiting to set off a ring
    float ring_cd = 0.0f;

    // FLOW px/s by SETTLE px out, whatever it started at: a = (v0^2 - FLOW^2) / 2*SETTLE.
    static constexpr float FLOW = 55.0f, SETTLE = 110.0f;
    static BulletSpawn settle(BulletSpawn b) {
        float v0 = sqrtf(b.vx * b.vx + b.vy * b.vy);
        b.min_speed = FLOW;
        b.accel = v0 > FLOW ? -(v0 * v0 - FLOW * FLOW) / (2.0f * SETTLE) : 0.0f;
        return b;
    }
    float glide_t() const { return ENRAGED ? 1.3f : 1.7f; }
    float perch_t() const { return ENRAGED ? 1.1f : 1.6f; }
public:
    Dingbat() : Enemy(320, 120, 420, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "DINGBAT"; }
    float       fire_interval() const override { return 0.05f; }   // reflections and glide drops, as they come
    // The pose shows the moment it perches (the tell); the catch opens
    // CATCH_DELAY later, so a player can stop firing in time and shots
    // already in flight still land (the tester found they were caught,
    // making holding fire cost most of the damage).
    static constexpr float CATCH_DELAY = 0.35f;
    float       catch_radius()  const override { return (gliding || t < CATCH_DELAY) ? 0.0f : CATCH; }
    bool        alt_pose()      const override { return !gliding; }   // perched: its catching pose (the alt sheet)
    float       flap_phase()    const override { return stare_anim >= 0.0f ? fminf(stare_anim / STARE_ANIM, 0.999f) : -1.0f; }
    void catch_shot(float bx, float by) override {
        if (nback < 32) back[nback++] = { bx, by };
        if (ENRAGED) rings_due++;
    }
    int move_facing() const override { return gliding ? facing_toward(x1 - x0, y1 - y0) : -1; }
    void update(float dt, float px, float py) override {
        px_ = px; py_ = py;
        t += dt; stare_t += dt;
        if (ring_cd > 0.0f) ring_cd -= dt;
        // The stare: perched only, its wingbeat played once; the rings
        // leave on its flare frame (frame 1, a quarter of the way in).
        if (!gliding && stare_anim < 0.0f && stare_t >= (ENRAGED ? 1.5f : 2.0f)) { stare_anim = 0.0f; stare_t = 0.0f; }
        if (stare_anim >= 0.0f) {
            float prev = stare_anim;
            stare_anim += dt;
            if (prev < STARE_ANIM * 0.25f && stare_anim >= STARE_ANIM * 0.25f) stare_due = true;
            if (stare_anim >= STARE_ANIM) stare_anim = -1.0f;
        }
        if (!gliding) {
            if (t >= perch_t() && stare_anim < 0.0f) {            // it finishes a stare before it glides
                x0 = x; y0 = y;
                do { x1 = 90.0f + ernd() * (ARENA_W - 180.0f); } while (fabsf(x1 - x) < 140.0f);
                y1 = 90.0f + ernd() * 90.0f;
                gliding = true; t = 0.0f; drop_t = 0.0f;
            }
            return;
        }
        drop_t += dt;
        float k = fminf(t / glide_t(), 1.0f), e = k * k * (3.0f - 2.0f * k);
        x = x0 + (x1 - x0) * e; y = y0 + (y1 - y0) * e;
        if (k >= 1.0f) { gliding = false; t = 0.0f; }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        // Reflections: each caught shot sent straight back at the player
        // from where it was caught (two, a little apart, in phase 2).
        for (int i = 0; i < nback && n < 80; i++) {
            float a = aim_at(back[i].x, back[i].y, px, py);
            for (int k = 0; k < (ENRAGED ? 2 : 1); k++) {
                BulletSpawn b = settle(mk(a + (ENRAGED ? (k ? 0.12f : -0.12f) : 0.0f), 210.0f, 2.5f, 5.0f));
                b.from = true; b.ox = back[i].x; b.oy = back[i].y;
                b.flash_in = true;
                out[n++] = b;
            }
        }
        nback = 0;
        if (rings_due > 0 && ring_cd <= 0.0f) {                  // phase 2: a ring for a shot it caught
            rings_due--; ring_cd = RING_CD;
            if (rings_due > 5) rings_due = 5;                    // a burst of catches doesn't bank forever
            float turn = ernd() * TAU;
            for (int i = 0; i < 14; i++) out[n++] = settle(mk(turn + i * (TAU / 14), 140.0f, 3.0f, 5.0f));
        }
        if (stare_due) {
            // The stare: a ring from each eye, 30 round with three gaps of
            // two, spreading slowly (75 easing to 30) while it turns -- the
            // left eye's clockwise, the right eye's anticlockwise -- so where
            // they overlap, gaps drift past each other. Gone after STARE_LIFE.
            const int   N = 30;
            const float STARE_LIFE = 10.0f;
            stare_due = false;
            for (int eye = -1; eye <= 1; eye += 2) {
                float turn = ernd() * TAU;
                for (int i = 0; i < N; i++) {
                    if (i % 10 >= 8) continue;                   // three gaps, two shots wide
                    BulletSpawn b = settle(mk(turn + i * (TAU / N), 75.0f, 3.0f, 5.0f));
                    b.orbit_w = eye < 0 ? 0.35f : -0.35f;
                    b.life = STARE_LIFE;
                    b.from = true; b.ox = x + eye * 12.0f; b.oy = y - 8.0f;
                    out[n++] = b;
                }
            }
        }
        if (gliding && drop_t >= 0.35f) {                        // a 3-fan as it glides
            drop_t = 0.0f;
            float a = aim_at(x,y,px,py);
            for (int i = 0; i < 3; i++) out[n++] = settle(mk(a + (i - 1) * 0.22f, 165.0f, 2.5f, 5.0f));
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (frame != 2 || gliding) return 0;                     // a downstroke, perched
        // Feathers: 7 at the player, slowing from 160 to a 55 drift, each
        // curving -- left, right, left -- as it falls.
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < 7; i++) {
            BulletSpawn b = settle(mk(a + (i - 3) * 0.2f, 160.0f, 2.5f, 5.0f));
            b.orbit_w = (i % 2 ? 0.25f : -0.25f);
            out[i] = b;
        }
        return 7;
    }
};

// The agropelter, the lumberjack's "widow-maker" (A Book of Creatures): "the
// villainous face of an ape on a sinewy little body, with incredibly
// powerful arms like organic whips"; it breaks off branches and flings them
// with "pinpoint accuracy", smashing or impaling -- Big Ole Kittleson lived
// only because the branch that hit him was rotten and crumbled. MEDIUM tier,
// 520 HP, bark bullets. BIG sheet. It never moves (the user's design).
// Whips (the user: whip-like patterns covering the screen, Touhou style):
//   each time an arm reaches furthest out (idle frames 1 and 3, left then
//   right) it LASHES -- a long line of shots let out one after another while
//   the arm sweeps across the arena, each a little faster toward the tip and
//   curling as it flies, so the whole line cracks out as a curving whip arm
//   over the screen. Close to it the line is solid; out where the player is
//   its shots are ~25 px apart, to slip between.
// Branches: every BRANCH_EVERY s one flung end over end straight at the
//   player (pinpoint: aimed true, fast). Every third is ROTTEN and crumbles
//   in mid-air into a burst of splinters.
// Phase 2 (half HP): longer, wider lashes; its scream (idle frame 2, mouth
//   widest) sends a ring of 24; branches come two at a time.
class Agropelter : public Enemy {
    static constexpr float LASH_T = 0.5f;    // seconds to let a lash out -- inside the 0.52 s from frame 1 to frame 3, so one lash finishes before the next
    float throw_t = 0.0f;
    int   thrown = 0;
    // The lash being let out: which arm, how far along, and its sweep.
    int   lash_side = 0;                     // -1 left, +1 right, 0 none
    float lash_t = 0.0f, lash_a0 = 0.0f, lash_due = 0.0f;
    int   lash_n = 0, lash_done = 0;

    static BulletSpawn branch(float a, bool rotten) {
        BulletSpawn b = mk(a, rotten ? 170.0f : 230.0f, 3.0f, 5.0f);
        b.half_len = 14.0f;                                  // a stick, spinning end over end
        b.ang = ernd() * PI; b.spin = 7.0f;
        if (rotten) {
            b.shed_first = 0.75f; b.shed_times = 1; b.shed_dies = true;
            b.shed_n = 8; b.shed_spread = TAU * 7.0f / 8.0f; b.shed_speed = 120.0f;
        }
        return b;
    }
    float sweep() const { return ENRAGED ? 2.8f : 2.4f; }
public:
    Agropelter() : Enemy(320, 120, 520, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "AGROPELTER"; }
    float       fire_interval() const override { return 0.016f; }  // the lash, shot by shot
    void update(float dt, float, float) override {
        throw_t += dt;
        if (lash_side) lash_t += dt;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        if (lash_side) {
            // Let out the shots the lash owes by now: shot i leaves at
            // i/lash_n through LASH_T, aimed along the sweep, faster toward
            // the tip, curling the way the arm swings.
            int owed = (int)(fminf(lash_t / LASH_T, 1.0f) * lash_n);
            for (; lash_done < owed && n < 60; lash_done++) {
                float k = lash_done / (float)(lash_n - 1);
                float ang = lash_a0 + lash_side * k * sweep();
                BulletSpawn b = mk(ang, 140.0f + 100.0f * k, 3.0f, 5.0f);
                b.orbit_w = lash_side * 0.3f;
                out[n++] = b;
            }
            if (lash_done >= lash_n) lash_side = 0;
        }
        if (throw_t >= 1.8f) {
            throw_t = 0.0f;
            float a = aim_at(x,y,px,py);
            bool rotten = (++thrown % 3) == 0;
            if (!ENRAGED) out[n++] = branch(a, rotten);
            else { out[n++] = branch(a - 0.12f, rotten); out[n++] = branch(a + 0.12f, false); }
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (frame == 1 || frame == 3) {
            // An arm at full reach: start a lash, sweeping from out wide on
            // its side across past the player.
            lash_side = frame == 1 ? 1 : -1;
            lash_a0 = aim_at(x, y, px, py) - lash_side * sweep() * 0.6f;
            lash_t = 0.0f; lash_done = 0;
            lash_n = ENRAGED ? 36 : 28;
            return 0;
        }
        if (frame == 2 && ENRAGED) {                             // the scream
            float turn = ernd() * TAU;
            for (int i = 0; i < 24; i++) out[i] = mk(turn + i * (TAU / 24), 115.0f, 3.0f, 5.0f);
            return 24;
        }
        return 0;
    }
};

// The tripodero of the California chaparral (A Book of Creatures): a small
// strong body on "two telescopic legs" that "can be collapsed or extended at
// will", a face that is "all nose" and a cheek pouch of clay slugs; from up
// high it "sights down its snout and fires a clay slug" with "perfect aim".
// MEDIUM tier, 540 HP, clay-red bullets.
// Phase 1 -- standing tall, sighting:
//   Slug  -- on its fire frame (idle frame 1: legs at full height, a slug
//            off the snout) a heavy fast slug LED at the player: aimed where
//            they're going, from how they're moving -- keep straight and it
//            meets you; change course and it misses.
//            Three of them: the led one and one either side of it, so the
//            step that dodges it has to be a real one.
//   Pouch -- with each slug, two fans of clay pellets aimed where the player
//            is now -- 7, and 6 slower in their gaps -- so the two together
//            close off staying put and running straight.
//   Spit  -- and between slugs (idle frame 2) a spray of 9 pellets, spread
//            loose, slowing as they come. (Phase 1 made harder by the user.)
// Phase 2 (below 40% HP -- phase 1 holds until then, the user's call) -- it dances round on its legs
//   (59_tripodero_walk: big steps left then right, legs telescoping), its
//   steps carrying it about the top of the arena; each time a foot plants it
//   fires a led slug and a ring of 12.
class Tripodero : public Enemy {
#define DANCING (hp < max_hp * phase2_at())   // its own phase line (phase2_at): phase 1 runs down to 40%
    static constexpr float SLUG_SPEED = 300.0f;
    static constexpr float STEP_T = 0.22f;   // one frame of the dance: step out, plant, step, plant
    float lastpx = 320.0f, lastpy = 400.0f, pvx = 0.0f, pvy = 0.0f;
    float dance = 0.0f, home = 320.0f;
    int   dance_frame = -1;
    bool  planted = false;

    // Where to aim for a shot at `speed` to meet the player if they keep
    // going as they are: solve |p + v t - e| = speed t, take the first t.
    float lead(float px, float py, float speed) const {
        float dx = px - x, dy = py - y;
        float a = pvx * pvx + pvy * pvy - speed * speed;
        float b = 2.0f * (dx * pvx + dy * pvy), c = dx * dx + dy * dy;
        float t = -1.0f;
        if (fabsf(a) > 1e-3f) {
            float disc = b * b - 4.0f * a * c;
            if (disc >= 0.0f) {
                float s = sqrtf(disc), t1 = (-b - s) / (2.0f * a), t2 = (-b + s) / (2.0f * a);
                t = (t1 > 0.0f && (t1 < t2 || t2 <= 0.0f)) ? t1 : t2;
            }
        }
        if (t <= 0.0f || t > 3.0f) return aim_at(x, y, px, py);
        return aim_at(x, y, px + pvx * t, py + pvy * t);
    }
    BulletSpawn slug(float px, float py) const { return mk(lead(px, py, SLUG_SPEED), SLUG_SPEED, 4.5f, 5.0f); }
public:
    float phase2_at() const override { return 0.4f; }
    Tripodero() : Enemy(320, 125, 540, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "TRIPODERO"; }
    int         breath_frame()  const override { return 1; }       // legs at full height, slug off the snout
    float       fire_interval() const override { return 0.05f; }   // the planted-foot shots
    float flap_phase() const override { return DANCING ? fmodf(dance / (STEP_T * 4.0f), 1.0f) : -1.0f; }
    void update(float dt, float px, float py) override {
        if (dt > 0.0f) {                                        // the player's motion, smoothed, for the lead
            pvx += ((px - lastpx) / dt - pvx) * fminf(1.0f, dt * 8.0f);
            pvy += ((py - lastpy) / dt - pvy) * fminf(1.0f, dt * 8.0f);
        }
        lastpx = px; lastpy = py;
        if (!DANCING) return;
        // The dance: frame 0 a big step out left, 1 planted, 2 a big step
        // right, 3 planted -- and the whole dance drifting round the top.
        dance += dt;
        int f = (int)(dance / STEP_T) % 4;
        float k = fmodf(dance, STEP_T) / STEP_T;
        home = 320.0f + 180.0f * sinf(dance * 0.35f);
        float off = f == 0 ? 60.0f - 120.0f * k : f == 1 ? -60.0f : f == 2 ? -60.0f + 120.0f * k : 60.0f;
        x = home + off;
        y = 125.0f - ((f == 0 || f == 2) ? 18.0f * sinf(PI * k) : 0.0f);   // up on its legs mid-step
        if ((f == 1 || f == 3) && f != dance_frame) planted = true;
        dance_frame = f;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        if (!planted) return 0;
        planted = false;
        int n = 0;
        out[n++] = slug(px, py);
        float turn = ernd() * TAU;
        for (int i = 0; i < 12; i++) out[n++] = mk(turn + i * (TAU / 12), 120.0f, 3.0f, 5.0f);
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (DANCING) return 0;                                  // dancing: it fires as its feet plant
        int n = 0;
        float l = lead(px, py, SLUG_SPEED);
        for (int i = -1; i <= 1; i++) out[n++] = mk(l + i * 0.16f, SLUG_SPEED, 4.5f, 5.0f);   // the led slug, flanked
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < 7; i++) out[n++] = mk(a + (i - 3) * 0.2f, 165.0f, 3.0f, 5.0f);
        for (int i = 0; i < 6; i++) out[n++] = mk(a + (i - 2.5f) * 0.2f, 125.0f, 3.0f, 5.0f);   // slower, in the gaps
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (DANCING || frame != 2) return 0;                     // between slugs: a loose spray of clay
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < 9; i++) {
            BulletSpawn b = mk(a + (ernd() * 2.0f - 1.0f) * 0.6f, 150.0f + ernd() * 50.0f, 3.0f, 5.0f);
            b.accel = -60.0f; b.min_speed = 90.0f;
            out[i] = b;
        }
        return 9;
    }
};
#undef DANCING

// The rumptifusel (A Book of Creatures): big and vicious, flat and "very
// flexible", in "a fine pelt not unlike mink"; it drapes itself over a stump
// "looking for all the world like an abandoned expensive fur coat", and when
// a "greedy tenderfoot" comes close it moves "with deceptive speed" and
// engulfs them -- "tiny sucking pores" on its underside drain them off their
// bones. MEDIUM tier, 560 HP, fur-brown bullets. BIG sheet.
// It's meant to be a DENSE fight (the user), both phases.
// Phase 1 -- lying there like a coat:
//   Pore sheet -- each time it rears its hood and bares its pocked belly
//                 (idle frame 2) it throws a SHEET at the player: a hex
//                 lattice of 24 small shots -- its pores -- flying as one like
//                 a coat flung over you, the holes between them just wide
//                 enough to slip through (the user: traversable). Phase 1
//                 throws three at a time, fanned, with a spray of 10 from its
//                 pores. (A fourth on the settle frame made it too hard -- the user.)
//   The lure   -- come within LURE px of it and it bunches up (a beat), then
//                 lunges at where you are "with deceptive speed" -- touching
//                 it costs a bar -- and slides slowly back to where it lay.
// Phase 2 (half HP): it throws FIVE sheets at a time, fanned across most of
//   the screen; and its pores SUCK: every 2 s a ring of 20 flies out to a
//   different reach each time -- anywhere from just past its body to the
//   whole screen -- stops, and collapses back into it.
class Rumptifusel : public Enemy {
    enum State { LIE, BUNCH, LUNGE, CREEP };
    static constexpr float LURE = 150.0f, BUNCH_T = 0.35f, LUNGE_SPEED = 420.0f, CREEP_SPEED = 70.0f;
    static constexpr float HOME_X = 320.0f, HOME_Y = 130.0f;
    State state = LIE;
    float t = 0.0f, suck_t = 0.0f;
    float tx = 0, ty = 0;

    // A coat of shots: a hex lattice (rows 4-5-6-5-4, 24 shots), 26 px
    // apart, drifting at 75 -- slow and open enough to thread at a crouch
    // (the tester: at 24 px and 110 the holes' channels needed walk speed to
    // ride) -- centred 50 px out toward `a`, all flying along `a`.
    int sheet(float a, BulletSpawn out[]) const {
        static const int ROW[5] = { 4, 5, 6, 5, 4 };
        float cx = x + cosf(a) * 50.0f, cy = y + sinf(a) * 50.0f;
        float ux = cosf(a), uy = sinf(a), vx = -uy, vy = ux;      // along and across the throw
        int n = 0;
        for (int r = 0; r < 5; r++)
            for (int i = 0; i < ROW[r]; i++) {
                float across = (i - (ROW[r] - 1) * 0.5f) * 26.0f, along = (r - 2) * 22.5f;
                BulletSpawn b = mk(a, 75.0f, 2.5f, 5.0f);
                b.from = true; b.ox = cx + ux * along + vx * across; b.oy = cy + uy * along + vy * across;
                out[n++] = b;
            }
        return n;
    }
public:
    Rumptifusel() : Enemy(HOME_X, HOME_Y, 560, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()           const override { return "RUMPTIFUSEL"; }
    int         breath_frame()   const override { return 2; }     // hood reared, belly bared
    float       fire_interval()  const override { return 0.05f; } // the suck ring on its own clock
    float       contact_damage() const override { return state == LUNGE ? 5.0f : 0.0f; }
    int move_facing() const override { return state == LUNGE ? facing_toward(tx - x, ty - y) : -1; }
    void update(float dt, float px, float py) override {
        t += dt;
        if (ENRAGED) suck_t += dt;
        switch (state) {
        case LIE:
            if (hypotf(px - x, py - y) < LURE) { state = BUNCH; t = 0.0f; tx = px; ty = py; }
            break;
        case BUNCH:                                              // a beat, gathering itself
            if (t >= BUNCH_T) { state = LUNGE; t = 0.0f; }
            break;
        case LUNGE: {
            float dx = tx - x, dy = ty - y, d = hypotf(dx, dy), st = LUNGE_SPEED * dt;
            if (d <= st) { x = tx; y = ty; state = CREEP; t = 0.0f; }
            else { x += dx / d * st; y += dy / d * st; }
            break;
        }
        case CREEP: {                                            // back to where it lay, slowly
            float dx = HOME_X - x, dy = HOME_Y - y, d = hypotf(dx, dy), st = CREEP_SPEED * dt;
            if (d <= st) { x = HOME_X; y = HOME_Y; state = LIE; t = 0.0f; }
            else { x += dx / d * st; y += dy / d * st; }
            break;
        }
        }
    }
    int fire(float, float, BulletSpawn out[], int) override {
        if (suck_t < 2.0f) return 0;
        suck_t = 0.0f;
        // The pores suck: a ring out to a reach picked fresh each time --
        // from just past its body (70 px) to the whole screen (460 px) --
        // where it stops and collapses back in: decelerating so it stops
        // exactly there, v^2 / 2R.
        float reach = 70.0f + ernd() * 390.0f;
        float turn = ernd() * TAU;
        for (int i = 0; i < 20; i++) {
            BulletSpawn b = mk(turn + i * (TAU / 20), 170.0f, 3.0f, 5.0f);
            b.accel = -(170.0f * 170.0f) / (2.0f * reach); b.max_speed = 170.0f;
            out[i] = b;
        }
        return 20;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (state == LUNGE || state == BUNCH) return 0;
        float a = aim_at(x,y,px,py);
        int n = 0;
        int fan = ENRAGED ? 2 : 1;                                   // five in phase 2, three in phase 1, fanned
        for (int k = -fan; k <= fan; k++) n += sheet(a + k * 0.5f, out + n);
        for (int i = 0; i < 10; i++)                            // a spray from its pores
            out[n++] = mk(a + (ernd() * 2.0f - 1.0f) * 0.8f, 140.0f + ernd() * 60.0f, 2.0f, 5.0f);
        return n;
    }
};

// The trollgadda, Sweden's troll pike (A Book of Creatures): in Lake Bolmen
// one "is as long as the lake is wide, and can barely move", "a willow shrub
// grows on its head and neck"; in Dalsland its "scales as big as roof
// tiles"; and the Sjora, the Mistress of the Lake, dresses her pet pikes in
// bells like cows. MEDIUM tier (a DENSE one, the user's call), 500 HP, moss
// green bullets. BIG sheet. It swims in place -- it never moves (the user).
// Phase 1:
//   Leaves -- all fight long, leaves drift down out of the tree in its jaws,
//             fanning out as they fall and swaying side to side.
//   Bells  -- when its jaws strain widest (idle frame 2) its bells chime:
//             two rings, one inside the other, turned half a step.
//   Scales -- every SCALE_EVERY s a fan of 5 roof-tile scales -- big, slow --
//             at the player.
// Phase 2 (half HP): the tree sheds twice as fast and wider, the bells ring
//   three rings, and the scales come 7 at a time.
class Trollgadda : public Enemy {
    float leaf_t = 0.0f, scale_t = 0.0f;
public:
    Trollgadda() : Enemy(320, 120, 500, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "TROLLGADDA"; }
    int         breath_frame()  const override { return 2; }       // jaws strained widest
    float       fire_interval() const override { return 0.05f; }   // leaves and scales on their own clocks
    void update(float dt, float, float) override { leaf_t += dt; scale_t += dt; }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        // Leaves: from across the canopy above it, down and fanning out,
        // swaying as they fall.
        float every = ENRAGED ? 0.045f : 0.09f, spread = ENRAGED ? 0.75f : 0.55f;
        while (leaf_t >= every && n < 8) {
            leaf_t -= every;
            BulletSpawn b = mk(PI / 2 + (ernd() * 2.0f - 1.0f) * spread, 65.0f + ernd() * 30.0f, 2.5f, 5.0f);
            b.zig = 0.35f; b.zig_every = 0.45f;                  // swaying
            b.from = true; b.ox = x + (ernd() * 2.0f - 1.0f) * 80.0f; b.oy = y - 20.0f + ernd() * 20.0f;
            out[n++] = b;
        }
        float se = 1.6f;
        if (scale_t >= se) {                                     // roof-tile scales
            scale_t = 0.0f;
            float a = aim_at(x,y,px,py);
            int m = ENRAGED ? 7 : 5;
            for (int i = 0; i < m; i++) out[n++] = mk(a + (i - (m - 1) * 0.5f) * 0.22f, 140.0f, 5.5f, 5.0f);
        }
        return n;
    }
    int breathe(float, float, BulletSpawn out[], int) override {
        // The bells: rings one inside the next, each turned half a step.
        const int N = 24;
        int rings = ENRAGED ? 3 : 2, n = 0;
        float turn = ernd() * TAU;
        for (int r = 0; r < rings; r++)
            for (int i = 0; i < N; i++) out[n++] = mk(turn + (i + r * 0.5f) * (TAU / N), 135.0f - r * 30.0f, 3.0f, 5.0f);
        return n;
    }
};

// The namungumi of Lake Malawi (A Book of Creatures): for all its "whale"
// name it "has four limbs", webbing between them, prominent tusks, and its
// "whole body is covered in a complex grid pattern"; villagers cut meat from
// it painlessly and "the wounds healed immediately". MEDIUM tier, 520 HP,
// pale vein-blue bullets. BIG sheet. It lies where it is.
// Phase 1:
//   The net  -- Touhou-laser style (the user): a bright beam shoots out of its
//               glowing EYE both ways at once -- harmless while it shoots
//               out (the warning), then it HURTS to touch while it holds,
//               charged, and as it starts to fade -- and dissipates as a
//               dashed line of shots appears all along it, splitting off to
//               both sides of the line. The beams SWEEP round clockwise, each
//               turned one SWEEP step on from the last, so the next one can be
//               read coming (the user: predictable). Crossing beams leave a
//               moving net of cells; the dash gaps are the way through.
//   The eye  -- when its eye glows brightest (idle frame 2) a ring of 12
//               light-nodes, and 3 aimed at the player.
// Phase 2 (half HP): the beams come quicker, the eye's ring is 18, and it
//   HEALS -- left alone for a moment, its wounds close (REGEN HP/s).
class Namungumi : public Enemy {
    static constexpr float REGEN = 6.0f, REGEN_AFTER = 1.2f;
    static constexpr float GROW_T = 0.4f;        // a beam shoots out of the eye this long...
    static constexpr float HOLD_T = 0.35f;       // ...holds, charged and hurting, this long -- then the shots appear along it
    static constexpr float SWEEP = 0.6f;         // rad each beam turns on from the last: a steady clockwise sweep
    static constexpr float FADE_T = 0.32f;       // ...and the beam dissipates over this long as they do
    static constexpr float STEP = 16.0f;         // px between a line's shots
    static constexpr float REACH = 760.0f;       // a beam's length each way: past the far corner
    float beam_t = 0.0f, last_ang = 0.0f, quiet = 0.0f, last_hp = 520.0f;
    float px_ = 320.0f, py_ = 400.0f;
    struct Beam { bool on = false, fired = false; float t = 0.0f, ox = 0.0f, oy = 0.0f, ang = 0.0f; int phase = 0; };
    Beam beams[2];

    float every() const { return ENRAGED ? 0.8f : 1.3f; }
    static bool dash(int k, int phase) { return (k + phase) % 8 < 4; }   // 4 on, 4 off: 64 px gaps
    // Its eye, on the sprite as it faces the player (art: the glowing node
    // sits ~48 px forward of its middle, ~74 side-on, 11 px down).
    void eye(float& ex, float& ey) const {
        int f = facing_toward(px_ - x, py_ - y);
        float off = f == FACE_RIGHT ? 74.0f : f == FACE_LEFT ? -76.0f
                  : (f == FACE_UP_LEFT || f == FACE_DOWN_LEFT) ? -50.0f : 48.0f;   // D and U use the 3/4-right art
        ex = x + off; ey = y + 11.0f;
    }
    // How far the beam has shot out: fast, then slowing (ease-out).
    static float grown(const Beam& b) { float k = fminf(b.t / GROW_T, 1.0f); return 1.0f - (1.0f - k) * (1.0f - k); }
    static TeleLine line(const Beam& b, int dir) {
        float k = grown(b) * REACH * dir;
        TeleLine L{ b.ox, b.oy, b.ox + cosf(b.ang) * k, b.oy + sinf(b.ang) * k };
        L.stage = b.t < GROW_T ? 0 : b.t < GROW_T + HOLD_T ? 1 : 2;
        L.fade = L.stage == 2 ? fminf((b.t - GROW_T - HOLD_T) / FADE_T, 1.0f) : 0.0f;
        // Harmless shooting out; it hurts charged, and for the first
        // third of its fade.
        L.hurt_w = (L.stage == 1 || (L.stage == 2 && L.fade < 0.33f)) ? 4.0f : 0.0f;
        return L;
    }
public:
    Namungumi() : Enemy(320, 120, 520, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "NAMUNGUMI"; }
    int         breath_frame()  const override { return 2; }       // its eye at its brightest
    float       fire_interval() const override { return 0.05f; }   // the beams, when they're ready
    int telegraphs(TeleLine out[], int) const override {
        int n = 0;
        for (const Beam& b : beams)
            if (b.on) { out[n++] = line(b, 1); out[n++] = line(b, -1); }   // both ways from the eye
        return n;
    }
    void update(float dt, float px, float py) override {
        px_ = px; py_ = py;
        beam_t += dt;
        for (Beam& b : beams) if (b.on) b.t += dt;
        // Its wounds heal: once it's gone REGEN_AFTER s without being hurt.
        if (hp < last_hp) quiet = 0.0f; else quiet += dt;
        if (ENRAGED && quiet >= REGEN_AFTER && hp > 0.0f) hp = fminf(hp + REGEN * dt, max_hp * 0.5f - 1.0f);   // never back into phase 1
        last_hp = hp;
    }
    int fire(float, float, BulletSpawn out[], int) override {
        int n = 0;
        if (beam_t >= every()) {
            for (Beam& b : beams) if (!b.on) {
                beam_t = 0.0f;
                b = Beam(); b.on = true;
                eye(b.ox, b.oy);
                b.ang = last_ang = fmodf(last_ang + SWEEP, PI);   // one step on, clockwise: predictable
                b.phase = (int)(ernd() * 8);
                break;
            }
        }
        for (Beam& b : beams) {
            if (b.on && b.t >= GROW_T + HOLD_T + FADE_T) b.on = false;   // the beam's gone
            if (!b.on || b.fired || b.t < GROW_T + HOLD_T) continue;
            b.fired = true;
            // Shots all along it, both ways from the eye -- dashed -- each
            // splitting into a pair sliding off either side of the line.
            float ux = cosf(b.ang), uy = sinf(b.ang), nx = -uy, ny = ux;
            int K = (int)(REACH / STEP);
            for (int k = -K; k <= K && n < 220; k++) {
                if (!dash(k + 64, b.phase)) continue;
                float sx = b.ox + ux * k * STEP, sy = b.oy + uy * k * STEP;
                if (sx < 0.0f || sx > ARENA_W || sy < ARENA_TOP || sy > ARENA_H) continue;
                for (int side = -1; side <= 1; side += 2) {
                    BulletSpawn s2 = mk(atan2f(ny * side, nx * side), 60.0f, 3.0f, 5.0f);
                    s2.from = true; s2.ox = sx; s2.oy = sy;
                    out[n++] = s2;
                }
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        int N = ENRAGED ? 18 : 12, n = 0;
        float turn = ernd() * TAU;
        for (int i = 0; i < N; i++) out[n++] = mk(turn + i * (TAU / N), 120.0f, 3.0f, 5.0f);
        float a = aim_at(x,y,px,py);
        for (int i = -1; i <= 1; i++) out[n++] = mk(a + i * 0.18f, 190.0f, 2.5f, 5.0f);
        return n;
    }
};

// The mahwot of the Meuse (A Book of Creatures): a lizard-like amphibious
// monster the size of a calf that "runs back and forth along the riverbed"
// between Revin and Liege, rarely leaving the water, and "pulls in and
// devours children who play too close" -- a bogey to keep them from the
// river. Drawn as a swimming mini-Godzilla. MEDIUM tier, 540 HP, river-green
// bullets. BIG sheet.
// Always swimming fast (the user): it RUNS the arena back and forth along a
// lane near the top, weaving in an S, leaving a WAKE of shots behind it that
// spread slowly as it passes. At each end it turns, rears, and ROARS --
// ATOMIC BREATH: a laser from its mouth at where the player is (harmless as
// it shoots out, the warning; it hurts while it holds), with a burst of 12
// as it lets go.
// Phase 2 (half HP): it runs faster, its wake is thicker, and its breath is
//   two beams (the user: sprint away from one, but not too far or the other
//   gets you): one locks on where the player IS, the other on where they'll
//   be LEAD_T s later if they keep going as they are -- a short step off the
//   first slips between them; a long run meets the second.
class Mahwot : public Enemy {
    static constexpr float GROW_T = 0.35f, HOLD_T = 0.4f, FADE_T = 0.3f;
    static constexpr float LANE_L = 70.0f, LANE_R = ARENA_W - 70.0f;
    float dir = 1.0f;                        // which way it's running
    float swim = 0.0f, wake_t = 0.0f;
    float roar = -1.0f;                      // seconds into the roar at a turn (-1 = running)
    float aim = 0.0f, aim2 = 0.0f, mx = 0.0f, my = 0.0f;   // the breath's aims (phase 2: the second) and its mouth
    static constexpr float LEAD_T = 0.6f;    // phase 2: the second beam aims this far ahead of the player
    float lpx = 320.0f, lpy = 400.0f, pvx = 0.0f, pvy = 0.0f;   // the player's motion, smoothed
    bool  burst = false;
    bool  pair = false;                      // this roar's breath is two beams -- fixed when it locks, so a
                                             // phase change mid-roar can't put a beam up with no warning

    float speed() const { return ENRAGED ? 420.0f : 340.0f; }
    TeleLine beam(float a) const {
        float k = fminf(roar / GROW_T, 1.0f); k = 1.0f - (1.0f - k) * (1.0f - k);
        float reach = 800.0f * k;
        TeleLine L{ mx, my, mx + cosf(a) * reach, my + sinf(a) * reach };
        L.stage = roar < GROW_T ? 0 : roar < GROW_T + HOLD_T ? 1 : 2;
        L.fade = L.stage == 2 ? fminf((roar - GROW_T - HOLD_T) / FADE_T, 1.0f) : 0.0f;
        L.hurt_w = (L.stage == 1 || (L.stage == 2 && L.fade < 0.33f)) ? 5.0f : 0.0f;
        return L;
    }
public:
    Mahwot() : Enemy(LANE_L, 130, 540, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "MAHWOT"; }
    float       fire_interval() const override { return 0.05f; }   // wake and burst on their own clocks
    int roar_facing = FACE_DOWN;             // the way it faces through a roar -- locked with the beam,
                                             // so the open mouth stays on it however the player moves
    int move_facing() const override { return roar < 0.0f ? (dir > 0.0f ? FACE_RIGHT : FACE_LEFT) : roar_facing; }
    bool alt_pose() const override { return roar >= 0.0f; }   // roaring: its open-mouthed breath pose (72_mahwot_roar)
    int telegraphs(TeleLine out[], int) const override {
        if (roar < 0.0f) return 0;
        out[0] = beam(aim);
        if (!pair) return 1;
        out[1] = beam(aim2);
        return 2;
    }
    void update(float dt, float px, float py) override {
        if (dt > 0.0f) {                                     // the player's motion, smoothed, for the lead
            pvx += ((px - lpx) / dt - pvx) * fminf(1.0f, dt * 8.0f);
            pvy += ((py - lpy) / dt - pvy) * fminf(1.0f, dt * 8.0f);
        }
        lpx = px; lpy = py;
        if (roar >= 0.0f) {                                  // rearing at the end of a run, breathing
            float prev = roar;
            roar += dt;
            if (prev < GROW_T + HOLD_T && roar >= GROW_T + HOLD_T) burst = true;
            if (roar >= GROW_T + HOLD_T + FADE_T) { roar = -1.0f; dir = -dir; }
            return;
        }
        swim += dt; wake_t += dt;
        x += dir * speed() * dt;
        y = 130.0f + 22.0f * sinf(swim * 5.0f);              // the S of its swimming
        if ((dir > 0.0f && x >= LANE_R) || (dir < 0.0f && x <= LANE_L)) {
            x = dir > 0.0f ? LANE_R : LANE_L;
            roar = 0.0f;                                     // turn and roar
            // It turns to face the player to breathe, in its roar pose; the
            // beam leaves its open mouth -- where the roar sheet draws it in
            // the facing it turns to (art px in the 98x65 frame, drawn 2x
            // about the frame's middle).
            {
                int f = roar_facing = facing_toward(px - x, py - y);
                float fx = f == FACE_RIGHT ? 83 : f == FACE_LEFT ? 14
                         : (f == FACE_DOWN_RIGHT || f == FACE_UP_RIGHT) ? 72
                         : (f == FACE_DOWN_LEFT  || f == FACE_UP_LEFT)  ? 25 : 64;   // D and U: 64
                mx = x + (fx - 49.0f) * 2.0f; my = y + (27.0f - 32.5f) * 2.0f;
            }
            aim = aim_at(mx, my, px, py);
            pair = ENRAGED;
            // The second beam: where they'll be if they keep going -- but at
            // least MIN_SPLIT to the side of the first where they stand, so
            // the space between the beams is always real (moving slowly, or
            // toward or away from it, the two nearly overlapped into a double
            // wall -- the tester). Kept in the arena.
            {
                const float MIN_SPLIT = 40.0f;
                float nx = -sinf(aim), ny = cosf(aim);               // across the first beam
                float qx = px + pvx * LEAD_T, qy = py + pvy * LEAD_T;
                float side = (qx - px) * nx + (qy - py) * ny;
                if (fabsf(side) < MIN_SPLIT) {
                    float sgn = side != 0.0f ? (side > 0.0f ? 1.0f : -1.0f) : (ernd() < 0.5f ? -1.0f : 1.0f);
                    qx += nx * (sgn * MIN_SPLIT - side); qy += ny * (sgn * MIN_SPLIT - side);
                }
                qx = fminf(fmaxf(qx, 0.0f), (float)ARENA_W);
                qy = fminf(fmaxf(qy, (float)ARENA_TOP), (float)ARENA_H);
                // Against a wall the clamp can pull it back in close: then it
                // goes MIN_SPLIT the other side instead.
                float now = (qx - px) * nx + (qy - py) * ny;
                if (fabsf(now) < MIN_SPLIT - 1.0f) {
                    float sgn = now > 0.0f ? -1.0f : 1.0f;
                    qx = fminf(fmaxf(px + nx * sgn * MIN_SPLIT, 0.0f), (float)ARENA_W);
                    qy = fminf(fmaxf(py + ny * sgn * MIN_SPLIT, (float)ARENA_TOP), (float)ARENA_H);
                }
                aim2 = aim_at(mx, my, qx, qy);
            }
        }
    }
    int fire(float, float, BulletSpawn out[], int) override {
        int n = 0;
        if (burst) {                                         // the breath let go: a burst of 12
            burst = false;
            float turn = ernd() * TAU;
            for (int i = 0; i < 12; i++) out[n++] = mk(turn + i * (TAU / 12), 120.0f, 3.0f, 5.0f);
        }
        float every = ENRAGED ? 0.07f : 0.1f;
        while (roar < 0.0f && wake_t >= every && n < 20) {   // the wake: shots left behind, spreading slowly
            wake_t -= every;
            for (int side = -1; side <= 1; side += 2) {
                BulletSpawn b = mk(PI / 2 + side * (0.5f + ernd() * 0.6f), 40.0f + ernd() * 30.0f, 3.0f, 5.0f);
                b.from = true; b.ox = x - dir * 30.0f; b.oy = y;
                out[n++] = b;
            }
        }
        return n;
    }
};

// The liderc, Hungary's will-o'-the-wisp (A Book of Creatures): a
// shape-shifter -- a marsh flame, a "shooting star or fiery rod", a
// featherless talking chicken hatched from an egg kept under a man's armpit
// -- that "spits fire and throws sparks when angry". MEDIUM tier, 550 HP,
// wisp-flame bullets. BIG sheet.
// The user's design: you can only SEE it the closer you get -- far off it's
// gone, a ghost; up close, a burning hen. Its fire always shows (fair play).
// Its tell (the lore: one foot is always a goose's): when it DASHES in phase
// 2 it leaves glowing FOOTPRINTS, a human foot and a goose foot by turns,
// seen however far, fading after PRINT_LIFE s -- track the dash by them.
// Phase 1 -- drifting about the upper arena:
//   Sparks -- when its flames flare (idle frame 2) it spits a spray of 9
//             sparks at the player, loose and slowing.
//   Wisps  -- every WISP_EVERY s four little lights appear round it, hang
//             there flickering, then dart at the player one by one.
// Phase 2 (half HP) -- the shooting star: every few seconds it streaks
//   across the arena in a straight line, dropping embers all along its path
//   (still unseen unless you're near -- its prints show the way); sparks and
//   wisps both come thicker.
class Liderc : public Enemy {
    static constexpr float NEAR = 70.0f, FAR = 180.0f;    // fully seen within NEAR, gone past FAR (the user pulled it in from 110/300)
    float wander_t = 0.0f, wisp_t = 0.0f, star_t = 0.0f, ember_t = 0.0f;
    float tx = 320.0f, ty = 140.0f;
    bool  streaking = false;
    float sx0 = 0, sy0 = 0, sx1 = 0, sy1 = 0, st = 0.0f;
    // Footprints: a ring of the last PRINTS, stepped every PRINT_STEP px it goes.
    static constexpr int   PRINTS = 24;
    static constexpr float PRINT_STEP = 22.0f, PRINT_LIFE = 3.0f;
    struct Print { float x, y, born; int kind, dir; } prints[PRINTS] = {};
    int   nprint = 0;
    float clock = 0.0f, walked = 0.0f, lx = 320.0f, ly = 140.0f;
    void step_prints() {
        if (!streaking) { lx = x; ly = y; walked = 0.0f; return; }   // only its phase-2 dashes leave prints (the user)
        walked += hypotf(x - lx, y - ly);
        float mx = x - lx, my = y - ly;
        lx = x; ly = y;
        if (walked < PRINT_STEP) return;
        walked = 0.0f;
        int kind = nprint % 2;                                   // human, goose, human, goose...
        float side = kind ? 6.0f : -6.0f, d = hypotf(mx, my) + 1e-3f;
        int dir = fabsf(mx) > fabsf(my) ? (mx > 0 ? 1 : 3) : (my > 0 ? 2 : 0);   // toes the way it goes
        prints[nprint % PRINTS] = { x - my / d * side, y + mx / d * side + 24.0f, clock, kind, dir };
        nprint++;
    }

    float wisp_every() const { return ENRAGED ? 1.6f : 2.2f; }
public:
    Liderc() : Enemy(320, 140, 550, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "LIDERC"; }
    int         breath_frame()  const override { return 2; }       // flames flaring
    float       fire_interval() const override { return 0.05f; }   // wisps and embers on their own clocks
    float opacity(float px, float py) const override {
        return (FAR - hypotf(px - x, py - y)) / (FAR - NEAR);   // even streaking: only near (the user)
    }
    int marks(Mark out[], int max) const override {
        int n = 0;
        for (int i = 0; i < PRINTS && i < nprint && n < max; i++) {
            const Print& p = prints[i];
            float age = (clock - p.born) / PRINT_LIFE;
            if (age < 1.0f) out[n++] = { p.x, p.y, p.kind, p.dir, age };
        }
        return n;
    }
    int move_facing() const override { return streaking ? facing_toward(sx1 - sx0, sy1 - sy0) : -1; }
    void update(float dt, float px, float py) override {
        wisp_t += dt; clock += dt;
        step_prints();
        if (streaking) {
            st += dt;
            float k = fminf(st / 0.6f, 1.0f);
            x = sx0 + (sx1 - sx0) * k; y = sy0 + (sy1 - sy0) * k;
            ember_t += dt;
            if (k >= 1.0f) { streaking = false; star_t = 0.0f; }
            return;
        }
        // Drifting from spot to spot, slow and wavering.
        wander_t += dt;
        float dx = tx - x, dy = ty - y, d = hypotf(dx, dy);
        if (d < 6.0f || wander_t > 3.0f) {
            wander_t = 0.0f;
            tx = 80.0f + ernd() * (ARENA_W - 160.0f);
            ty = ARENA_TOP + 50.0f + ernd() * 160.0f;
        } else {
            x += dx / d * 55.0f * dt + 12.0f * sinf(wisp_t * 3.0f) * dt;
            y += dy / d * 55.0f * dt;
        }
        if (ENRAGED && (star_t += dt) >= 3.5f) {
            // A shooting star: from where it is, straight across past the
            // player's side of the arena to the far side.
            streaking = true; st = 0.0f; ember_t = 0.0f;
            sx0 = x; sy0 = y;
            float a = aim_at(x, y, px, py) + (ernd() * 2.0f - 1.0f) * 0.6f;
            sx1 = fminf(fmaxf(x + cosf(a) * 420.0f, 60.0f), ARENA_W - 60.0f);
            sy1 = fminf(fmaxf(y + sinf(a) * 420.0f, ARENA_TOP + 50.0f), 300.0f);
        }
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        if (streaking) {                                         // embers dropped along the streak
            while (ember_t >= 0.04f && n < 30) {
                ember_t -= 0.04f;
                for (int side = -1; side <= 1; side += 2) {
                    float a = atan2f(sy1 - sy0, sx1 - sx0) + side * PI / 2;
                    BulletSpawn b = mk(a + (ernd() - 0.5f) * 0.5f, 35.0f + ernd() * 25.0f, 2.5f, 5.0f);
                    out[n++] = b;
                }
            }
            return n;
        }
        if (wisp_t >= wisp_every()) {
            // Wisps: little lights round it, hanging there flickering, then
            // darting at the player one after another.
            wisp_t = 0.0f;
            int w = ENRAGED ? 6 : 4;
            float turn = ernd() * TAU;
            for (int i = 0; i < w; i++) {
                float a = turn + i * (TAU / w);
                BulletSpawn b = mk(0.0f, 0.0f, 3.5f, 5.0f);
                b.from = true; b.ox = x + cosf(a) * 46.0f; b.oy = y + sinf(a) * 46.0f;
                b.delay = 0.9f + i * 0.18f; b.launch_speed = 170.0f; b.launch_off = 0.0f;
                b.flash_in = true;
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (streaking) return 0;
        float a = aim_at(x,y,px,py);
        int m = ENRAGED ? 13 : 9;
        for (int i = 0; i < m; i++) {
            BulletSpawn b = mk(a + (ernd() * 2.0f - 1.0f) * 0.55f, 150.0f + ernd() * 70.0f, 2.5f, 5.0f);
            b.accel = -80.0f; b.min_speed = 80.0f;
            out[i] = b;
        }
        return m;
    }
};

// Bes Rap, the Jah Hut pig spirit (A Book of Creatures): it lives at the
// roots of the pokok ara tree in the deep jungle, "especially present during
// the tree's fruiting period", and "blows its saliva" at anyone gathering
// the fruit -- they sicken, "foaming at the mouth"; even its droppings are
// hot, and stepping on them brings on "bubbling, frothing saliva". MEDIUM
// tier, 560 HP, foam-white bullets. BIG sheet.
// Phase 1 -- crouched at the roots, never moving (the user):
//   Spit      -- when its head lunges and its jaw drops (idle frame 2) it
//                blows a frothing cone of 15 foam bubbles at the player,
//                loose, fast and slow mixed, slowing as they come.
//   Droppings -- every DROP_EVERY s it leaves hot toxic droppings on the
//                ground around where the player is: each spot is marked by a
//                cross for HINT_T s first (the user: a hint before they
//                appear), then a big blob lands there and just SITS a few
//                seconds -- don't step in them.
// Phase 2 (half HP) -- the tree fruits: figs drop out of the canopy above
//   and burst where they land into seeds; the spit cone is 21; more
//   droppings.
class BesRap : public Enemy {
    static constexpr float DROP_LIFE = 2.5f, HINT_T = 0.8f, HINT_R = 7.0f;
    float drop_t = 1.0f, fig_t = 0.0f;
    static constexpr int MAX_SPOTS = 12;
    struct Spot { float x, y, t; } spots[MAX_SPOTS];     // droppings about to land, t = seconds marked
    int   nspot = 0;
public:
    BesRap() : Enemy(320, 130, 560, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "BES RAP"; }
    int         breath_frame()  const override { return 2; }       // head lunges, jaw drops
    float       fire_interval() const override { return 0.05f; }   // droppings and figs on their own clocks
    int telegraphs(TeleLine out[], int max) const override {
        // Each spot about to be dropped on: a small blinking X, harmless.
        int n = 0;
        for (int i = 0; i < nspot && n + 2 <= max; i++) {
            const Spot& s = spots[i];
            TeleLine a{ s.x - HINT_R, s.y - HINT_R, s.x + HINT_R, s.y + HINT_R };
            TeleLine b{ s.x + HINT_R, s.y - HINT_R, s.x - HINT_R, s.y + HINT_R };
            a.stage = b.stage = 3;                               // thin and blinking: subtle
            out[n++] = a; out[n++] = b;
        }
        return n;
    }
    void update(float dt, float, float) override {
        drop_t += dt; fig_t += dt;
        for (int i = 0; i < nspot; i++) spots[i].t += dt;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        if (drop_t >= (ENRAGED ? 1.8f : 2.6f)) {
            // Droppings: around the player -- never on them (60-150 px off) --
            // sitting still, flashing in so they're seen landing, gone after
            // DROP_LIFE s.
            drop_t = 0.0f;
            int m = ENRAGED ? 12 : 8;                            // the user: WAY more
            for (int i = 0; i < m && nspot < MAX_SPOTS; i++) {
                // A spot that's in the arena as it is -- never clamped back
                // in toward a player at a wall (the tester caught that
                // dropping them 25-40 px off); re-picked until it fits.
                float ox = -1.0f, oy = -1.0f;
                for (int tries = 0; tries < 16; tries++) {
                    float a = ernd() * TAU, r = 60.0f + ernd() * 90.0f;
                    float cx = px + cosf(a) * r, cy = py + sinf(a) * r;
                    if (cx < 20.0f || cx > ARENA_W - 20.0f || cy < ARENA_TOP + 20.0f || cy > ARENA_H - 20.0f) continue;
                    ox = cx; oy = cy; break;
                }
                if (ox < 0.0f) continue;                         // nowhere fits this time: skip it
                spots[nspot++] = { ox, oy, 0.0f };               // marked now, dropped HINT_T s on
            }
        }
        for (int i = 0; i < nspot; ) {                           // marked long enough: it lands
            if (spots[i].t < HINT_T) { i++; continue; }
            BulletSpawn b = mk(0.0f, 0.0f, 6.0f, 5.0f);
            b.from = true; b.ox = spots[i].x; b.oy = spots[i].y;
            b.life = DROP_LIFE; b.flash_in = true;
            out[n++] = b;
            spots[i] = spots[--nspot];
        }
        if (ENRAGED && fig_t >= 0.45f) {
            // A fig dropping out of the canopy somewhere above, bursting
            // into 5 seeds after it's fallen a way.
            fig_t = 0.0f;
            BulletSpawn b = mk(PI / 2, 120.0f, 4.0f, 5.0f);
            b.from = true; b.ox = 40.0f + ernd() * (ARENA_W - 80.0f); b.oy = ARENA_TOP + 4.0f;
            b.shed_first = 1.0f + ernd() * 0.8f; b.shed_times = 1; b.shed_dies = true;
            b.shed_n = 5; b.shed_spread = TAU * 4.0f / 5.0f; b.shed_speed = 100.0f;
            out[n++] = b;
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        // The spit: a frothing cone of foam at the player, out of its open
        // mouth -- where the spit frame draws it in the facing it shows (art
        // px in the 98x65 frame, drawn 2x about the frame's middle; the left
        // facings are the right ones mirrored).
        int f = facing_toward(px - x, py - y);
        float fx = f == FACE_RIGHT ? 82 : f == FACE_LEFT ? 16
                 : f == FACE_DOWN_RIGHT ? 70 : f == FACE_DOWN_LEFT ? 28
                 : f == FACE_UP_RIGHT ? 72 : f == FACE_UP_LEFT ? 26
                 : f == FACE_UP ? 66 : 58;                         // D: 58
        float fy = f == FACE_UP_RIGHT || f == FACE_UP_LEFT ? 19 : 20;
        float mx = x + (fx - 49.0f) * 2.0f, my = y + (fy - 32.5f) * 2.0f;
        float a = aim_at(mx,my,px,py);
        int m = ENRAGED ? 21 : 15;
        for (int i = 0; i < m; i++) {
            BulletSpawn b = mk(a + (ernd() * 2.0f - 1.0f) * 0.5f, 120.0f + ernd() * 130.0f, 2.5f, 5.0f);
            b.accel = -90.0f; b.min_speed = 90.0f;
            b.from = true; b.ox = mx; b.oy = my;               // misses leave soon (at 70 they collected in the corners)
            out[i] = b;
        }
        return m;
    }
};

// The makalala of East Africa, "the noisy one" (A Book of Creatures): a
// giant ground bird that screams, and clubs its prey to death with the great
// bony knob on its head. MEDIUM tier, 580 HP, beak-yellow bullets. BIG sheet;
// flap = 75_makalala_fly (wings beating, the club on its head glowing).
// Phase 1 -- planted on the ground, never moving, all noise: massive
// patterns, every shot the same speed (the user):
//   Calls  -- a three-armed spiral turning out of it all the while.
//   Scream -- when it screams (idle frame 2: neck up, beak gaping, wings
//             flared) six rings of 24 burst out one after another, lined
//             up -- 24 thick spokes with lanes between to stand in.
// Phase 2 (half HP) -- it takes off and hangs in the air at the top, wings
//   beating, and its glowing club fires LASERS that SPIN (the user): three
//   beams, a third of a turn apart, shoot out (harmless, the warning) away
//   from the player, then sweep round together (SPIN_W rad/s) for SPIN_T s -- hurting --
//   slow enough to walk ahead of, always turning to drive the player away
//   from their nearer side wall, never into a corner; and a
//   slow ring of 16 from the club every RING_EVERY s.
class Makalala : public Enemy {
    static constexpr float SPEED = 100.0f;                       // phase 1: every shot
    static constexpr float ARM_EVERY = 0.12f, ARM_TURN = 0.21f;
    static constexpr int   SCREAM_RINGS = 6;
    static constexpr float SCREAM_GAP = 0.1f;
    static constexpr float GROW_T = 0.5f, SPIN_T = 3.0f, FADE_T = 0.3f, REST_T = 0.8f, SPIN_W = 0.35f;   // 0.35: a focusing player along the floor outruns it (the tester)
    static constexpr float RING_EVERY = 2.2f;
    static constexpr float HOVER_X = 320.0f, HOVER_Y = 130.0f;
    float arm_t = 0.0f, arm_a = 0.0f, scream_t = 0.0f, scream_a = 0.0f, ring_t = 0.0f, bob = 0.0f;
    float smx = 0.0f, smy = 0.0f;            // the scream's gaping beak, latched: all its rings from there
    int   scream_left = 0;
    bool  hovering = false;
    // The laser volley: latched at lock (cx, cy the club then).
    float beam_age = -1.0f, rest = 0.0f, aim = 0.0f, spin_dir = 1.0f, cx = 0.0f, cy = 0.0f;   // spin_dir +1 clockwise

    // The glowing club: pinned at (49, 15) in every frame of the fly sheet
    // (the user), drawn 2x about the frame's middle (49, 32.5).
    void club(float* ox, float* oy) const { *ox = x; *oy = y + (15.0f - 32.5f) * 2.0f; }
    // Its beak, where the idle sheet draws it in the facing it shows -- the
    // tip, closed (frames 0-1, 3-4) or gaping in the scream (frame 2); seen
    // from behind (U), the back of its head. Art px in the 98x65 frame,
    // drawn 2x about the frame's middle; the left facings mirror the right.
    void beak(float px, float py, bool scream, float* ox, float* oy) const {
        int f = facing_toward(px - x, py - y);
        float fx = f == FACE_DOWN_RIGHT || f == FACE_DOWN_LEFT ? (scream ? 63.0f : 61.0f)
                 : f == FACE_RIGHT || f == FACE_LEFT           ? (scream ? 71.0f : 68.0f)
                 : f == FACE_UP_RIGHT || f == FACE_UP_LEFT     ? (scream ? 64.0f : 62.0f) : 49.0f;
        float fy = f == FACE_UP ? 12.0f : scream ? 17.0f : 18.0f;
        if (f == FACE_LEFT || f == FACE_DOWN_LEFT || f == FACE_UP_LEFT) fx = 97.0f - fx;
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // A phase-1 shot: out of the beak at (ox, oy).
    BulletSpawn from_beak(float a, float r, float ox, float oy) const {
        BulletSpawn b = mk(a, SPEED, r, 5.0f);
        b.from = true; b.ox = ox; b.oy = oy;
        return b;
    }
    TeleLine beam(int k) const {
        float g = fminf(beam_age / GROW_T, 1.0f); g = 1.0f - (1.0f - g) * (1.0f - g);
        float spun = fminf(fmaxf(beam_age - GROW_T, 0.0f), SPIN_T) * SPIN_W * spin_dir;
        float a = aim + k * (TAU / 3) + spun, reach = 800.0f * g;
        TeleLine L{ cx, cy, cx + cosf(a) * reach, cy + sinf(a) * reach };
        L.stage = beam_age < GROW_T ? 0 : beam_age < GROW_T + SPIN_T ? 1 : 2;
        L.fade = L.stage == 2 ? fminf((beam_age - GROW_T - SPIN_T) / FADE_T, 1.0f) : 0.0f;
        L.hurt_w = (L.stage == 1 || (L.stage == 2 && L.fade < 0.33f)) ? 5.0f : 0.0f;
        return L;
    }
public:
    Makalala() : Enemy(320, 140, 580, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()           const override { return "MAKALALA"; }
    int         breath_frame()   const override { return 2; }       // the scream
    float       fire_interval()  const override { return 0.05f; }   // the spiral, burst and rings on their own clocks
    // Phase 2 is FLOWN, a wingbeat per 0.28 s.
    float flap_phase() const override { return ENRAGED ? fmodf(bob / 0.28f, 1.0f) : -1.0f; }
    int telegraphs(TeleLine out[], int max) const override {
        if (!hovering || beam_age < 0.0f || max < 3) return 0;
        for (int k = 0; k < 3; k++) out[k] = beam(k);
        return 3;
    }
    void update(float dt, float px, float py) override {
        bob += dt;
        if (!ENRAGED) { arm_t += dt; scream_t += dt; return; }   // planted
        if (!hovering) {
            // Taking off: up to its spot at the top, then hanging there.
            float hx = HOVER_X - x, hy = HOVER_Y - y, hd = hypotf(hx, hy);
            if (hd > 6.0f) { float st = fminf(150.0f * dt, hd); x += hx / hd * st; y += hy / hd * st; return; }
            hovering = true; rest = REST_T;
        }
        x = HOVER_X; y = HOVER_Y + 4.0f * sinf(bob * 3.0f);
        ring_t += dt;
        if (beam_age >= 0.0f) {
            beam_age += dt;
            if (beam_age >= GROW_T + SPIN_T + FADE_T) { beam_age = -1.0f; rest = 0.0f; }
        } else if ((rest += dt) >= REST_T) {
            // A volley locks: from the club, the three beams set a sixth of
            // a turn off the player (never on them), spinning so the beam
            // coming at them drives them toward the open middle, away from
            // their nearer side wall (clockwise sweeps a player below it
            // left) -- the tester: the other way pins a slow one in a corner.
            beam_age = 0.0f;
            spin_dir = px > HOVER_X ? 1.0f : -1.0f;
            club(&cx, &cy);
            aim = aim_at(cx, cy, px, py) + TAU / 6;
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (!ENRAGED) {
            while (arm_t >= ARM_EVERY && n + 3 <= max) {         // the spiral: three arms, turning
                arm_t -= ARM_EVERY;
                arm_a += ARM_TURN;
                float ox, oy;
                beak(px, py, false, &ox, &oy);
                for (int k = 0; k < 3; k++) out[n++] = from_beak(arm_a + k * (TAU / 3), 3.0f, ox, oy);
            }
            while (scream_left > 0 && scream_t >= SCREAM_GAP && n + 24 <= max) {   // the scream's rings, lined up
                scream_t -= SCREAM_GAP; scream_left--;
                for (int i = 0; i < 24; i++) out[n++] = from_beak(scream_a + i * (TAU / 24), 2.5f, smx, smy);
            }
            return n;
        }
        if (hovering && ring_t >= RING_EVERY) {                  // a slow ring of 16 from the club
            ring_t = 0.0f;
            float ox, oy, turn = ernd() * TAU;
            club(&ox, &oy);
            for (int i = 0; i < 16; i++) {
                BulletSpawn b = mk(turn + i * (TAU / 16), 85.0f, 3.0f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) return 0;
        // The scream: the first of its rings now, the rest SCREAM_GAP apart.
        scream_a = ernd() * TAU;
        scream_left = SCREAM_RINGS - 1; scream_t = 0.0f;
        beak(px, py, true, &smx, &smy);
        for (int i = 0; i < 24; i++) out[i] = from_beak(scream_a + i * (TAU / 24), 2.5f, smx, smy);
        return 24;
    }
};

// The roperite (Fearsome Creatures, California): a fast runner whose snout
// is drawn out into a long rope that it lassos its prey with, running it
// down; the rattle on its tail warns it's coming. UPPER tier, 620 HP,
// rattle-orange bullets. BIG sheet, the idle a sprint cycle -- it is
// DASHING AT ALL TIMES (the user): it runs laps of the upper arena, round an
// ellipse, facing the way it runs.
// Every shot leaves from the part of it that throws it (the user): the
// lasso from the forward tip of its rope loop, the rattle shots from its tail.
// Phase 1:
//   Rattle -- as it runs its tail drops a rattle shot every RATTLE_EVERY s;
//             each sits RATTLE_WAIT s where it fell, then darts at the player.
//   Lasso  -- when it flicks its rope out (idle frame 2) it throws a LOOP: a
//             ring of 12 flying together at the player, slowing to a stop
//             out where the player was, then reeled back the way it came
//             (never thrown at a player within LASSO_MIN px: no dodging it).
// Phase 2 (half HP): it runs faster and turns back on itself every TURN_EVERY
//   s; it throws two loops either side of the player, and the rattle comes
//   quicker and darts faster.
class Roperite : public Enemy {
    static constexpr float CX = 320.0f, CY = 190.0f, RX = 230.0f, RY = 100.0f;
    static constexpr float RATTLE_WAIT = 1.0f, TURN_EVERY = 4.0f, LASSO_MIN = 180.0f;
    float th = -PI / 2;                      // where on its lap it is
    float dir = 1.0f;                        // +1 clockwise on screen
    float rattle_t = 0.0f, turn_t = 0.0f;
    float vx_ = 1.0f, vy_ = 0.0f;            // the way it's running

    float speed()        const { return ENRAGED ? 320.0f : 260.0f; }
    float rattle_every() const { return ENRAGED ? 0.25f : 0.35f; }
    int   facing()       const { return facing_toward(vx_, vy_); }
    // Art px in the 98x65 frame -> the screen, drawn 2x about its middle.
    void at(float fx, float fy, float* ox, float* oy) const {
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // The forward tip of its rope loop, flicked out (frame 2), by facing.
    void rope_tip(float* ox, float* oy) const {
        int f = facing();
        float fx = f == FACE_RIGHT ? 79.0f : f == FACE_LEFT ? 18.0f
                 : (f == FACE_DOWN_RIGHT || f == FACE_UP_RIGHT) ? 70.0f
                 : (f == FACE_DOWN_LEFT  || f == FACE_UP_LEFT)  ? 27.0f : 63.0f;
        at(fx, f == FACE_DOWN || f == FACE_UP ? 23.0f : 21.0f, ox, oy);
    }
    // The rattle on its tail, by facing.
    void rattle(float* ox, float* oy) const {
        int f = facing();
        float fx = f == FACE_RIGHT ? 19.8f : f == FACE_LEFT ? 77.2f
                 : f == FACE_DOWN_RIGHT ? 28.5f : f == FACE_DOWN_LEFT ? 68.5f
                 : f == FACE_UP_RIGHT ? 30.0f : f == FACE_UP_LEFT ? 67.0f : 38.0f;
        at(fx, 28.0f, ox, oy);
    }
public:
    Roperite() : Enemy(CX, CY - RY, 620, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "ROPERITE"; }
    int         breath_frame()  const override { return 2; }       // the lasso flicked out
    float       fire_interval() const override { return 0.05f; }   // the rattle on its own clock
    int move_facing() const override { return facing(); }
    void update(float dt, float, float) override {
        rattle_t += dt;
        if (ENRAGED && (turn_t += dt) >= TURN_EVERY) { turn_t = 0.0f; dir = -dir; }   // doubling back
        // Round its lap at a steady speed: the angle steps by speed over the
        // ellipse's radius of the moment.
        float r = hypotf(RX * sinf(th), RY * cosf(th));
        th += dir * speed() / fmaxf(r, 1.0f) * dt;
        float nx = CX + RX * cosf(th), ny = CY + RY * sinf(th);
        vx_ = nx - x; vy_ = ny - y;
        x = nx; y = ny;
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        while (rattle_t >= rattle_every() && n < max) {
            // A rattle shot dropped from its tail: it sits, then darts at the player.
            rattle_t -= rattle_every();
            float ox, oy;
            rattle(&ox, &oy);
            BulletSpawn b = mk(0.0f, 0.0f, 3.0f, 5.0f);
            b.from = true; b.ox = ox; b.oy = oy;
            b.delay = RATTLE_WAIT; b.launch_speed = ENRAGED ? 150.0f : 130.0f; b.launch_off = 0.0f;
            out[n++] = b;
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        // The lasso: a loop of 12 thrown from its rope's tip at the player --
        // flying together, slowing to a stop ~260 px out, reeled back.
        float tx, ty;
        rope_tip(&tx, &ty);
        if (hypotf(px - tx, py - ty) < LASSO_MIN) return 0;     // too close to dodge a loop at 330 (the tester)
        float a0 = aim_at(tx, ty, px, py);
        int n = 0, loops = ENRAGED ? 2 : 1;
        for (int l = 0; l < loops; l++) {
            float a = loops == 1 ? a0 : a0 + (l ? 0.3f : -0.3f);
            for (int i = 0; i < 12; i++) {
                float c = i * (TAU / 12);
                BulletSpawn b = mk(a, 330.0f, 3.0f, 5.0f);
                b.accel = -210.0f; b.max_speed = 330.0f;
                b.from = true; b.ox = tx + cosf(c) * 30.0f; b.oy = ty + sinf(c) * 30.0f;
                out[n++] = b;
            }
        }
        return n;
    }
};

// The hugag (Fearsome Creatures, the Lake States): a beast the size of a
// moose on jointless legs -- it can never lie down, so it sleeps leaning on
// a tree -- with a great overhanging upper lip, wandering the woods day and
// night. UPPER tier, 640 HP, coat-gold bullets. BIG sheet; flap =
// 62_hugag_stomp (a foot swung high, SLAM, the other foot, SLAM).
// It never moves from its spot (the user), and every shot leaves from the
// part of it that makes it (the user): its lip, its coat, its feet.
// Phase 1 -- standing:
//   Bellow -- when it lifts its head and flaps its lip open (idle frame 2):
//             two rows of 17 fanned wide at the player out of its lip, the
//             second slower and half a step over, each shot wobbling.
//   Coat   -- every COAT_EVERY s the flaps of its shaggy coat shed: shots
//             dropping off the hem of its body, swaying slowly down.
// Phase 2 (half HP) -- it STOMPS in place, and each slammed foot (stomp
//   frames 1 and 3) blows out a DENSE CLUSTER (the user) of 14 shots
//   from under it, a clump flung at the player that loosens as it flies.
//   The coat keeps shedding, faster; no bellow (it's stomping).
class Hugag : public Enemy {
    static constexpr float STEP_T = 0.9f;    // one stomp cycle: two slams
    float coat_t = 0.0f, step_t = 0.0f;
    int   last_frame = 0, slam_foot = -1;    // the stomp frame shown last; a slam due (1 or 3)

    float coat_every() const { return ENRAGED ? 0.8f : 0.9f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    int facing(float px, float py) const { return facing_toward(px - x, py - y); }
    // Its lip flapped open on the bellow frame, by facing (seen from behind:
    // the top of its head). Left facings mirror the right.
    void lip(float px, float py, float* ox, float* oy) const {
        int f = facing(px, py);
        bool left = f == FACE_LEFT || f == FACE_DOWN_LEFT || f == FACE_UP_LEFT;
        float fx = f == FACE_RIGHT || f == FACE_LEFT ? 75.0f
                 : f == FACE_DOWN_RIGHT || f == FACE_DOWN_LEFT ? 63.0f
                 : f == FACE_UP_RIGHT || f == FACE_UP_LEFT ? 64.0f : f == FACE_UP ? 60.0f : 57.0f;
        float fy = f == FACE_UP ? 15.0f : f == FACE_UP_RIGHT || f == FACE_UP_LEFT ? 20.0f : 24.0f;
        at(left ? 97.0f - fx : fx, fy, ox, oy);
    }
    // The foot it just slammed (where the stomp sheet's dust bursts), by
    // facing and slam (1 front-left, 3 front-right).
    void foot(float px, float py, int slam, float* ox, float* oy) const {
        static const float FX[8][2] = {   // [D DR R UR U UL L DL][frame 1, frame 3]
            { 60.3f, 50.3f }, { 59.3f, 50.7f }, { 62.0f, 60.8f }, { 49.2f, 59.0f },
            { 50.0f, 60.9f }, { 47.8f, 38.0f }, { 35.0f, 36.2f }, { 37.7f, 46.3f } };
        int f = facing(px, py);
        int d = f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
              : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
        at(FX[d][slam == 1 ? 0 : 1], 59.0f, ox, oy);
    }
public:
    Hugag() : Enemy(320, 120, 640, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "HUGAG"; }
    int         breath_frame()  const override { return 2; }       // head lifted, lip flapped open
    float       fire_interval() const override { return 0.05f; }   // coat and stomps on their own clocks
    float flap_phase() const override { return ENRAGED ? step_t / STEP_T : -1.0f; }
    void update(float dt, float, float) override {
        coat_t += dt;
        if (!ENRAGED) return;
        step_t = fmodf(step_t + dt, STEP_T);
        int f = (int)(step_t / STEP_T * 4.0f) % 4;               // the stomp frame now
        if (f != last_frame && (f == 1 || f == 3)) slam_foot = f; // a foot comes down
        last_frame = f;
    }
    int fire(float px, float py, BulletSpawn out[], int) override {
        int n = 0;
        if (coat_t >= coat_every()) {
            // The coat sheds: off the hem of its body (art y 34, x 18-74),
            // swaying down.
            coat_t = 0.0f;
            int m = ENRAGED ? 5 : 6;
            for (int i = 0; i < m; i++) {
                float ox, oy;
                at(18.0f + ernd() * 56.0f, 34.0f, &ox, &oy);
                BulletSpawn b = mk(ernd() * TAU, 65.0f + ernd() * 20.0f, 3.0f, 5.0f);   // every way (the user)
                b.from = true; b.ox = ox; b.oy = oy;
                b.zig = 0.35f; b.zig_every = 0.5f;
                out[n++] = b;
            }
        }
        if (slam_foot > 0) {
            // A slam: a dense clump blown out from under the foot at the
            // player, loosening as it flies (speeds and angles mixed).
            float ox, oy;
            foot(px, py, slam_foot, &ox, &oy);
            slam_foot = -1;
            float a = aim_at(ox, oy, px, py);
            for (int i = 0; i < 14; i++)
                out[n++] = mk(a + (ernd() * 2.0f - 1.0f) * 0.35f, 110.0f + ernd() * 60.0f, 2.5f, 5.0f);
            for (int i = n - 14; i < n; i++) { out[i].from = true; out[i].ox = ox; out[i].oy = oy; }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (ENRAGED) return 0;                                   // stomping, not bellowing
        // The bellow: all round out of its lip (the user: every way, not just
        // at the player), in CLUMPS -- two rings of 16 clumps of 4, the
        // second slower and half a step over (the user: denser), each clump
        // a tight knot of mixed speeds, wobbling.
        float ox, oy;
        lip(px, py, &ox, &oy);
        float turn = ernd() * TAU;
        int n = 0;
        for (int r = 0; r < 2; r++)
        for (int c = 0; c < 16; c++)
            for (int i = 0; i < 4; i++) {
                BulletSpawn b = mk(turn + (c + r * 0.5f) * (TAU / 16) + (ernd() * 2.0f - 1.0f) * 0.07f,
                                   (r ? 70.0f : 100.0f) + ernd() * 25.0f, 3.0f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                b.zig = 0.2f; b.zig_every = 0.3f;
                out[n++] = b;
            }
        return n;
    }
};

// The hidebehind (Fearsome Creatures, the north woods): it always hides
// behind something -- a tree, your own back -- so no one has ever seen it;
// turn to look and it's already behind you. UPPER tier, 660 HP, claw-ivory
// bullets. BIG sheet. It never moves (the user). Every shot leaves from the
// part of it that makes it (the user): its claws, its fur.
// Phase 1:
//   Swipe -- when it rears and raises its claws (idle frame 2) it slashes:
//            a BAR of 9 claw marks flung from its claws at the player, flying
//            past, slowing, and coming BACK the way it went -- at the player
//            from behind, the way it hunts.
//   Fur   -- every FUR_EVERY s loose shots drift off its shaggy coat, every
//            way, slowly.
// Phase 2 (half HP) -- it HIDES: faded nearly out of sight (so the player's
//   shots go where they face, not at it), showing only for a blink
//   (REVEAL_T) as it rears to swipe; the swipe is five bars fanned, and the
//   fur sheds faster.
class Hidebehind : public Enemy {
    static constexpr float REVEAL_T = 0.25f;   // phase 2: seen only this long a swipe (the user: hidden longer)
    float fur_t = 0.0f, reveal = 0.0f;

    float fur_every() const { return ENRAGED ? 0.4f : 0.45f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (76x61, drawn 2x about its middle) -> screen
        *ox = x + (fx - 38.0f) * 2.0f; *oy = y + (fy - 30.5f) * 2.0f;
    }
    // Its raised claws: it only ever shows its front, a fan of claws at each
    // upper corner (art x 3-17 and 58-72, y 2-26) -- the one on the player's side.
    void claws(float px, float, float* ox, float* oy) const {
        at(px < x ? 10.0f : 65.0f, 13.0f, ox, oy);
    }
    // A slash: 7 claw marks in a row across the throw, flung out at `a`,
    // stopping `reach` px out and coming back along the same line.
    int bar(float ox, float oy, float a, float reach, BulletSpawn out[]) const {
        // Never stopping past a wall: out there it would be culled leaving
        // and never come back (the tester).
        float c = cosf(a), sn = sinf(a), edge = 1e9f;
        if (c > 1e-3f)  edge = fminf(edge, (ARENA_W - ox) / c);
        if (c < -1e-3f) edge = fminf(edge, -ox / c);
        if (sn > 1e-3f)  edge = fminf(edge, (ARENA_H - oy) / sn);
        if (sn < -1e-3f) edge = fminf(edge, (ARENA_TOP - oy) / sn);
        reach = fmaxf(fminf(reach, edge - 10.0f), 60.0f);
        float vx = -sn, vy = c;
        for (int i = 0; i < 7; i++) {
            BulletSpawn b = mk(a, 300.0f, 3.0f, 5.0f);
            b.accel = -(300.0f * 300.0f) / (2.0f * reach); b.max_speed = 300.0f;   // stops exactly there
            // 24 px apart: an 18 px gap between shots to slip through (the user)
            b.from = true; b.ox = ox + vx * (i - 3) * 24.0f; b.oy = oy + vy * (i - 3) * 24.0f;
            out[i] = b;
        }
        return 7;
    }
public:
    Hidebehind() : Enemy(320, 130, 660, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "HIDEBEHIND"; }
    int         breath_frame()  const override { return 2; }       // the dip of its idle; the claws are always raised
    float       fire_interval() const override { return 0.05f; }   // the fur on its own clock
    float opacity(float, float) const override { return !ENRAGED || reveal > 0.0f ? 1.0f : 0.15f; }
    void update(float dt, float, float) override {
        fur_t += dt;
        if (reveal > 0.0f) reveal -= dt;
    }
    int fire(float, float, BulletSpawn out[], int) override {
        if (fur_t < fur_every()) return 0;
        fur_t = 0.0f;
        // Loose fur off its coat (art x 26-50, y 10-58), drifting every way.
        int m = 6;
        for (int i = 0; i < m; i++) {
            float ox, oy;
            at(26.0f + ernd() * 24.0f, 10.0f + ernd() * 48.0f, &ox, &oy);
            BulletSpawn b = mk(ernd() * TAU, 55.0f + ernd() * 25.0f, 3.0f, 5.0f);
            b.from = true; b.ox = ox; b.oy = oy;
            out[i] = b;
        }
        return m;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        reveal = REVEAL_T;                                       // seen, for a moment
        float ox, oy;
        claws(px, py, &ox, &oy);
        // A player in a corner: aimed 80 px out of it, toward the middle --
        // a bar thrown straight into a corner lies across the only ways out
        // (the tester).
        float tx = px, ty = py;
        bool wx = px < 70.0f || px > ARENA_W - 70.0f, wy = py < ARENA_TOP + 70.0f || py > ARENA_H - 70.0f;
        if (wx && wy) {
            float cx = ARENA_W * 0.5f - px, cy = (ARENA_TOP + ARENA_H) * 0.5f - py, cd = hypotf(cx, cy);
            tx += cx / cd * 80.0f; ty += cy / cd * 80.0f;
        }
        float a = aim_at(ox, oy, tx, ty);
        // Past the player, stopping BEHIND them, then back at them from
        // behind (the tester: stopping 250 px out never reached them).
        float reach = hypotf(tx - ox, ty - oy) + 70.0f;
        int n = 0;
        // Fanned 0.55 rad apart -- ~40 px gaps between bars at the player:
        // three, five in phase 2 (the user: phase 1 was far too easy).
        int side = ENRAGED ? 2 : 1;
        for (int k = -side; k <= side; k++) n += bar(ox, oy, a + k * 0.55f, reach, out + n);
        return n;
    }
};

// The dungavenhooter (Fearsome Creatures, Maine): a squat crocodilian with
// NO MOUTH that lies in wait beside a trail, pounds whoever passes into
// vapour with the club on its tail, and inhales the vapour through its
// nostrils. UPPER tier, 680 HP, club-grey bullets. BIG sheet. It lies in
// wait -- it never moves.
// ONE pattern (the user): it slaps its tail down, and the slap comes faster
// and faster as its HP drains -- its whole idle animation speeds up, from
// normal to SLAP_FAST times.
//   Slap -- as the club hits the ground (idle frame 4): five shockwave rings
//           of 20 at once from where it lands, fast to slower, each easing
//           off as it nears the player, each turned a quarter step on.
class Dungavenhooter : public Enemy {
    static constexpr float SLAP_FAST = 1.8f;
    static constexpr int   IMPACT = 6;          // the frame the club hits the ground, dust crowning out
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // The splash where its club lands (the impact frame's dust crown, its
    // middle), by facing D DR R UR U UL L DL.
    void club(float px, float py, float* ox, float* oy) const {
        static const float FX[8] = { 35, 30, 21, 30, 35, 67, 76, 67 };
        int f = facing_toward(px - x, py - y);
        int d = f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
              : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
        at(FX[d], 58.0f, ox, oy);
    }
public:
    Dungavenhooter() : Enemy(320, 130, 680, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "DUNGAVENHOOTER"; }
    int         breath_frame()  const override { return -1; }      // none: all on the slap frame
    float       fire_interval() const override { return 99.0f; }
    // 8 frames a slap: played 1.6x so a slap still takes 1.3 s at full HP.
    float       anim_speed()    const override { return 1.6f * (1.0f + (SLAP_FAST - 1.0f) * (1.0f - hp / max_hp)); }
    int fire(float, float, BulletSpawn[], int) override { return 0; }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (frame != IMPACT) return 0;
        float cx, cy;
        club(px, py, &cx, &cy);
        int n = 0;
        float turn = ernd() * TAU;
        for (int r = 0; r < 5; r++)
            for (int i = 0; i < 20; i++) {
                BulletSpawn b = mk(turn + (i + r * 0.25f) * (TAU / 20), 230.0f - r * 28.0f, 3.0f, 5.0f);
                b.accel = -140.0f; b.min_speed = 65.0f - r * 3.0f;
                b.from = true; b.ox = cx; b.oy = cy;
                out[n++] = b;
            }
        return n;
    }
};

// The Loch Oich monster (A Book of Creatures): Loch Ness's smaller
// neighbour in the Great Glen, seen as a string of humps -- and with the
// head of a DOG on a long neck. UPPER tier, 600 HP, loch-brown bullets. BIG
// sheet: a dog's head on an eel's body, floating. Every shot leaves from the
// part of it that makes it (the user): its barking mouth, its humps.
// SONIC WAVES are the fight (the user): a bullet hell, but a pretty and
// predictable one, made to be learned.
// Phase 1 -- holding still at the top of the loch, barking without end:
//   Waves  -- every BARK (idle frame 2, its jaw open -- the animation runs
//             BARK_RATE times quick, a bark every ~0.7 s) a ring of 144 -- a
//             WALL where the player is -- rolls out of its barking mouth, cut
//             by four gaps; ring after ring the gaps turn on a step, so they
//             trace four SPIRAL corridors turning slowly round it -- follow
//             one. Every SPIN_FLIP s the turn reverses (count it), and only
//             then does it turn its head to the player, so its mouth -- and
//             the corridors -- hold still in between.
//   Splash -- every SPLASH_EVERY s a hump breaks the water: two drops ricocheting
//             off the shores.
// Phase 2 (half HP): a second, sparse set of waves joins, between the first
//   -- slower, 48 a ring, turning the other way -- weaving a lattice of
//   diamonds over the corridors.
class LochOich : public Enemy {
    static constexpr float BARK_RATE = 1.3f / 0.7f;   // the 1.3 s idle loop played in 0.7 s
    static constexpr float WAVE2_EVERY = 0.5f, SPIN = 0.05f, SPIN_FLIP = 6.0f, SPLASH_EVERY = 2.0f;
    float splash_t = 0.0f, wave2_t = WAVE2_EVERY * 0.5f;
    int   face = -1;                         // the way it faces, turned to the player each spin flip
    float turn = 0.0f, turn2 = 0.0f, spin = 1.0f, flip_t = 0.0f;

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // Its open mouth on the bark frame, in the way it faces (from behind:
    // the top of its head).
    void mouth(float* ox, float* oy) const {
        int f = face;
        float fx = f == FACE_DOWN ? 62.0f : f == FACE_DOWN_RIGHT ? 70.0f : f == FACE_RIGHT ? 80.0f
                 : f == FACE_UP_RIGHT ? 66.0f : f == FACE_UP ? 54.0f : f == FACE_UP_LEFT ? 31.0f
                 : f == FACE_LEFT ? 17.0f : 27.0f;
        at(fx, f == FACE_UP ? 14.0f : f == FACE_UP_RIGHT || f == FACE_UP_LEFT ? 16.0f : 19.0f, ox, oy);
    }
    // A wave: a ring of `m` from (ox, oy) at `speed`, `gaps` evenly round it
    // (`gap_w` shots each) starting at `a0`.
    int wave(float ox, float oy, int m, int gaps, int gap_w, float a0, float speed, BulletSpawn out[]) const {
        int n = 0, per = m / gaps;
        for (int i = 0; i < m; i++) {
            if (i % per < gap_w) continue;                         // a gap
            BulletSpawn b = mk(a0 + i * (TAU / m), speed, 2.5f, 5.0f);
            b.from = true; b.ox = ox; b.oy = oy;
            out[n++] = b;
        }
        return n;
    }
public:
    LochOich() : Enemy(320, 125, 600, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "LOCH OICH MONSTER"; }
    int         breath_frame()  const override { return 2; }       // head up, barking
    float       fire_interval() const override { return 0.05f; }   // the second set and splashes on their own clocks
    float       anim_speed()    const override { return BARK_RATE; }
    int         move_facing()   const override { return face; }
    void update(float dt, float px, float py) override {
        splash_t += dt; flip_t += dt;
        if (ENRAGED) wave2_t += dt;
        if (face < 0 || flip_t >= SPIN_FLIP) {                   // the spin turns; it turns its head
            if (face >= 0) { flip_t = 0.0f; spin = -spin; }
            face = facing_toward(px - x, py - y);
        }
    }
    int breathe(float, float, BulletSpawn out[], int) override {
        // A bark: the main wave -- a wall, spiralling -- out of its open mouth.
        float ox, oy;
        mouth(&ox, &oy);
        turn += SPIN * spin;
        return wave(ox, oy, 144, 4, 5, turn, 105.0f, out);
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        float ox, oy;
        mouth(&ox, &oy);
        if (ENRAGED && wave2_t >= WAVE2_EVERY && n + 48 <= max) { // the sparse second set, turning the other way
            wave2_t -= WAVE2_EVERY;
            turn2 -= SPIN * 1.4f * spin;
            n += wave(ox, oy, 48, 3, 3, turn2, 80.0f, out + n);
        }
        if (splash_t >= SPLASH_EVERY && n + 2 <= max) {           // a hump breaks the water
            splash_t = 0.0f;
            float hx, hy, a = ernd() * TAU;
            at(20.0f + ernd() * 56.0f, 52.0f, &hx, &hy);
            for (int i = 0; i < 2; i++) {
                BulletSpawn b = mk(a + i * PI, 90.0f, 3.0f, 5.0f);
                b.from = true; b.ox = hx; b.oy = hy;
                b.bouncing = true;                                 // skipping off the shores
                out[n++] = b;
            }
        }
        return n;
    }
};

// The hoga of Lake Metztitlan (A Book of Creatures): a lake monster of
// Mexico, half ox and half fish, that churns the lake into waves and floods
// as it goes. UPPER tier, 620 HP, lake-blue bullets. BIG sheet: a fish body
// with a bull's head and horns, floating. Every shot leaves from the part of
// it that makes it (the user): its horns, its bellow.
// It holds its place facing the way it first faced the player, so its horns
// and mouth -- and every spiral -- never jump.
// Phase 1:
//   Horns  -- a SPINNING spawner on each horn (the user): three spiral arms
//             from each, the left horn's turning one way, the right's the
//             other, the arms crossing into a turning lattice.
//   Bellow -- when it lifts its head and bellows (idle frame 2): a ring of 40
//             from its mouth.
// Phase 2 (half HP): four arms a horn, and both spawners turn back every
//   TURN_EVERY s; the bellow is two rings, the second slower and half a
//   step over.
class Hoga : public Enemy {
    static constexpr float ARM_EVERY = 0.08f, SPIN = 0.55f, TURN_EVERY = 6.0f;   // spin x interval <= ~0.045 rad: the arms are walls at range, the lattice real cells (the tester)
    float arm_t = 0.0f, spin = 0.0f, spin_dir = 1.0f, turn_t = 0.0f;
    int   face = -1;                         // the way it faces: toward the player at the start, then held

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // Its two horn tips, in the way it faces (seen side on the far horn is
    // behind the near one: a step apart).
    void horns(float* lx, float* ly, float* rx, float* ry) const {
        float l, r;
        switch (face) {
        case FACE_RIGHT:      l = 68; r = 72; break;
        case FACE_LEFT:       l = 25; r = 29; break;
        case FACE_DOWN_RIGHT: case FACE_UP_RIGHT: l = 55; r = 72; break;
        case FACE_DOWN_LEFT:  case FACE_UP_LEFT:  l = 25; r = 41; break;
        default:              l = 49; r = 70; break;           // D, U
        }
        at(l, 22.0f, lx, ly); at(r, 22.0f, rx, ry);
    }
    // Its mouth, open on the bellow frame, in the way it faces.
    void mouth(float* ox, float* oy) const {
        float fx = face == FACE_RIGHT ? 80.0f : face == FACE_LEFT ? 17.0f
                 : face == FACE_DOWN_RIGHT ? 68.0f : face == FACE_DOWN_LEFT ? 29.0f
                 : face == FACE_UP_RIGHT ? 70.0f : face == FACE_UP_LEFT ? 27.0f : face == FACE_UP ? 66.0f : 62.0f;
        at(fx, 38.0f, ox, oy);
    }
public:
    Hoga() : Enemy(320, 125, 620, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "HOGA"; }
    int         breath_frame()  const override { return 2; }       // head lifted, bellowing
    float       fire_interval() const override { return 0.02f; }   // the streams on their own clock
    int         move_facing()   const override { return face; }
    void update(float dt, float px, float py) override {
        arm_t += dt; turn_t += dt;
        spin += SPIN * spin_dir * dt;
        if (face < 0) face = facing_toward(px - x, py - y);
        if (turn_t >= TURN_EVERY) { turn_t = 0.0f; if (ENRAGED) spin_dir = -spin_dir; }   // phase 2: the spawners turn back
    }
    int fire(float, float, BulletSpawn out[], int max) override {
        int n = 0;
        float hx[2], hy[2];
        horns(&hx[0], &hy[0], &hx[1], &hy[1]);
        int arms = ENRAGED ? 4 : 3;
        while (arm_t >= ARM_EVERY && n + 2 * arms <= max) {
            arm_t -= ARM_EVERY;
            for (int h = 0; h < 2; h++)                          // left horn one way, right horn the other
                for (int k = 0; k < arms; k++) {
                    BulletSpawn b = mk((h ? -spin : spin) + k * (TAU / arms), 105.0f, 2.5f, 5.0f);
                    b.from = true; b.ox = hx[h]; b.oy = hy[h];
                    out[n++] = b;
                }
        }
        return n;
    }
    int breathe(float, float, BulletSpawn out[], int) override {
        float ox, oy, turn = ernd() * TAU;
        mouth(&ox, &oy);
        int n = 0, rings = ENRAGED ? 2 : 1;
        for (int r = 0; r < rings; r++)
            for (int i = 0; i < 40; i++) {
                BulletSpawn b = mk(turn + (i + r * 0.5f) * (TAU / 40), r ? 100.0f : 130.0f, 3.0f, 5.0f);
                b.from = true; b.ox = ox; b.oy = oy;
                out[n++] = b;
            }
        return n;
    }
};

// Zankallala (Hausa folklore, A Book of Creatures): a TINY, boastful
// trickster who rides a jerboa, leans on a snake for a walking stick, wears
// scorpions for spurs and a swarm of bees for a hat, with birds following
// to sing its praises -- swallowed three times by the man-eating Dodo, it
// burst out through its head. UPPER tier, 630 HP, bee-gold bullets. MEDIUM
// sheet (frame 1 the boast: snake staff raised); flap = 78_zankallala_run,
// the jerboa bounding. Every shot leaves from the part of it that makes it
// (the user): its bee hat, its snake staff, its scorpion spurs.
// Phase 1:
//   Run    -- VERY FAST (the user): it stands a beat, turns to a new spot,
//             and its staff shoots a LASER out ahead along the way it's
//             about to go (the user) -- harmless as it shoots out (AIM_T s,
//             the warning), hot while it bounds down it at RUN_SPEED -- then
//             it fades as it lands.
//   Bees   -- its hat sheds bees all the while it runs: pairs flying out to
//             both sides of its run, buzzing gently -- a ladder in its wake.
// Every shot goes at about the same pace, SPEED (the user): pretty to watch.
//   Boast  -- standing, as it raises its staff (idle frame 1): the birds'
//             praise-song, a SUN coming down (the user) -- a ring of notes
//             with eight rays round it, sinking from the staff's tip and
//             slowly swelling as it falls.
//   Spurs  -- landing from a run, its scorpion spurs sting: a fan of 5 at
//             the player from its feet.
// Phase 2 (half HP) -- it bounds back to the middle and stays (the user):
//   Laser sun -- one at a time, a sun forms from a ball at its staff's tip,
//             ALL laser (the user): a giant glowing ball in the lasers' own
//             bands (harmless) with SUN_RAYS rays reaching right across the
//             screen, harmless as they shoot out, then hot -- spinning
//             constantly as the sun sinks down the screen: walk a gap round
//             with it. Near the bottom it dies away -- rays breaking up, the
//             ball shrinking -- then the next.
//   Swarm  -- all the while its bee hat swarms: bees streaming off it in a
//             turning spiral, buzzing.
class Zankallala : public Enemy {
    static constexpr float BEE_EVERY = 0.07f, AIM_T = 0.45f, FADE_T = 0.25f, SUN_FORM = 0.7f;
    static constexpr float SPEED = 100.0f;   // every shot about the same pace (the user): calm, pretty to watch
    enum State { STAND, AIM, RUN, HOME, CENTRE };
    static constexpr float HOME_X = 320.0f, HOME_Y = 150.0f;
    static constexpr int   SUN_RAYS = 6;
    static constexpr float SUN_R = 26.0f, RAY_LEN = 800.0f, SUN_GAP = 0.4f;   // rays cross the whole screen
    static constexpr float SUN_BALL = 34.0f;  // its middle: a glowing ball in the lasers' own bands (harmless)
    // The rays spin CONSTANTLY (the user), hot once formed -- fast (the
    // user): a walking player rides a gap round within ~230 px of the ball.
    static constexpr float SUN_SPIN = 0.7f;
    static constexpr float SUN_END_Y = ARENA_H - 70.0f, SUN_FADE = 0.45f;   // it dies away here, before reaching the edge (the user)
    State state = STAND;
    bool  landed = false;
    float t = 0.0f, bee_t = 0.0f, tx = 320.0f, ty = 140.0f;
    float bx = 0.0f, by = 0.0f, fade = -1.0f;   // the laser's far end (latched), its fade after landing
    int   run_face = FACE_DOWN;
    // Phase 2's laser sun: where it started, how long it's been sinking
    // (-1 = none yet / between suns), the turn it started at.
    float sun_x = 0.0f, sun_y = 0.0f, sun_age = -1.0f, sun_wait = 0.0f, swarm_a = 0.0f;
    bool  sun_new = false;
    float ray_rot = 0.0f;                    // the rays' turn
    float sun_fade = -1.0f;                  // dying away at the bottom (-1 = not yet)

    float run_speed() const { return ENRAGED ? 460.0f : 380.0f; }
    float stand_t()   const { return ENRAGED ? 0.9f : 1.3f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (58x53, drawn 2x about its middle) -> screen
        *ox = x + (fx - 29.0f) * 2.0f; *oy = y + (fy - 26.5f) * 2.0f;
    }
    // The tip of its snake staff, facing `f`.
    void staff(int f, float* ox, float* oy) const {
        static const float FX[8] = { 33, 35, 33, 30, 27, 26, 23, 22 };   // D DR R UR U UL L DL
        int d = f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
              : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
        at(FX[d], 13.0f, ox, oy);
    }
public:
    Zankallala() : Enemy(320, 140, 630, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "ZANKALLALA"; }
    int         breath_frame()  const override { return 1; }       // the boast, staff raised
    float       fire_interval() const override { return 0.02f; }   // bees and spurs on their own clocks
    int   move_facing() const override { return state == STAND || state == CENTRE ? -1 : run_face; }
    float flap_phase()  const override { return state == RUN || state == HOME ? fmodf(t / 0.24f, 1.0f) : -1.0f; }
    // Its idle loop (1.3 s, one boast) kept to its stop, so every stop boasts.
    float anim_speed()  const override { return 1.3f / (stand_t() + AIM_T); }
    int telegraphs(TeleLine out[], int max) const override {
        if (state == CENTRE) {
            // The laser sun's rays, out from its ring, turning as it sinks.
            if (sun_age < 0.0f || max < SUN_RAYS + 1) return 0;
            float k = fminf(sun_age / SUN_FORM, 1.0f); k = 1.0f - (1.0f - k) * (1.0f - k);
            float cy = fminf(sun_y + SPEED * sun_age, SUN_END_Y);
            float fade = sun_fade < 0.0f ? 0.0f : fminf(sun_fade / SUN_FADE, 1.0f);   // dying away: rays break up, the ball shrinks
            for (int r = 0; r < SUN_RAYS; r++) {                 // the rays, out from the ball's edge
                float a = ray_rot + (r + 0.5f) * (TAU / SUN_RAYS);
                float r0 = SUN_BALL * k * 0.8f;
                TeleLine L{ sun_x + cosf(a) * r0, cy + sinf(a) * r0,
                            sun_x + cosf(a) * (r0 + RAY_LEN * k), cy + sinf(a) * (r0 + RAY_LEN * k) };
                L.stage = sun_age < SUN_FORM ? 0 : fade > 0.0f ? 2 : 1;
                L.fade = fade;
                L.hurt_w = sun_age < SUN_FORM || fade >= 0.33f ? 0.0f : 5.0f;
                out[r] = L;
            }
            TeleLine ball{ sun_x, cy, sun_x, cy };                // the ball, drawn over the rays' roots
            ball.stage = 1; ball.orb = SUN_BALL * k * (1.0f - fade);
            out[SUN_RAYS] = ball;
            return SUN_RAYS + 1;
        }
        // The laser ahead of its run, from its staff's tip.
        if (max < 1 || state == HOME || (state == STAND && fade < 0.0f)) return 0;
        float sx, sy;
        staff(run_face, &sx, &sy);
        TeleLine L{ sx, sy, bx, by };
        if (state == AIM) {                                      // shooting out: harmless
            float k = fminf(t / AIM_T, 1.0f); k = 1.0f - (1.0f - k) * (1.0f - k);
            L.x1 = sx + (bx - sx) * k; L.y1 = sy + (by - sy) * k;
            L.stage = 0;
        } else if (state == RUN) {
            L.stage = 1; L.hurt_w = 5.0f;
        } else {                                                 // landed: fading
            L.stage = 2; L.fade = fminf(fade / FADE_T, 1.0f);
            L.hurt_w = L.fade < 0.33f ? 5.0f : 0.0f;
        }
        out[0] = L;
        return 1;
    }
    void update(float dt, float px, float py) override {
        t += dt;
        if (fade >= 0.0f && (fade += dt) >= FADE_T) fade = -1.0f;
        if (ENRAGED && (state == STAND || state == AIM)) {      // phase 2: back to the middle
            state = HOME; t = 0.0f; tx = HOME_X; ty = HOME_Y; fade = -1.0f;
            run_face = facing_toward(tx - x, ty - y);
        }
        if (state == HOME) {
            float dx = tx - x, dy = ty - y, d = hypotf(dx, dy), st = run_speed() * dt;
            if (d <= st) { x = tx; y = ty; state = CENTRE; t = 0.0f; sun_wait = 0.0f; }
            else { x += dx / d * st; y += dy / d * st; }
            return;
        }
        if (state == CENTRE) {
            bee_t += dt;
            if (sun_age >= 0.0f) {
                sun_age += dt;
                ray_rot += SUN_SPIN * dt;                            // spinning, always
                if (sun_fade < 0.0f && sun_y + SPEED * sun_age >= SUN_END_Y) sun_fade = 0.0f;   // low enough: it dies away
                if (sun_fade >= 0.0f && (sun_fade += dt) >= SUN_FADE) { sun_age = -1.0f; sun_fade = -1.0f; sun_wait = 0.0f; }
            } else if ((sun_wait += dt) >= SUN_GAP) {             // the next sun forms at its staff's tip
                staff(facing_toward(px - x, py - y), &sun_x, &sun_y);
                sun_age = 0.0f; ray_rot = ernd() * TAU; sun_new = true;
            }
            return;
        }
        if (state == STAND) {
            if (t >= stand_t()) {
                // A new spot in the upper two thirds, well clear of the player;
                // the laser reaches 60 px on past it.
                for (int k = 0; k < 12; k++) {
                    tx = 70.0f + ernd() * (ARENA_W - 140.0f);
                    ty = ARENA_TOP + 50.0f + ernd() * 200.0f;
                    if (hypotf(tx - px, ty - py) > 160.0f && hypotf(tx - x, ty - y) > 120.0f) break;
                }
                run_face = facing_toward(tx - x, ty - y);
                float dx = tx - x, dy = ty - y, d = hypotf(dx, dy) + 1e-3f;
                bx = tx + dx / d * 60.0f; by = ty + dy / d * 60.0f;
                state = AIM; t = 0.0f;
            }
            return;
        }
        if (state == AIM) {
            if (t >= AIM_T) { state = RUN; t = 0.0f; }
            return;
        }
        bee_t += dt;
        float dx = tx - x, dy = ty - y, d = hypotf(dx, dy), st = run_speed() * dt;
        if (d <= st) { x = tx; y = ty; state = STAND; landed = true; t = 0.0f; fade = 0.0f; }
        else { x += dx / d * st; y += dy / d * st; }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        if (state == CENTRE) {
            sun_new = false;
            while (bee_t >= BEE_EVERY * 0.6f && n < max) {        // the swarm: a turning spiral off its hat
                bee_t -= BEE_EVERY * 0.6f;
                swarm_a += 0.55f;
                float hx, hy;
                at(27.0f, 21.0f, &hx, &hy);
                BulletSpawn b = mk(swarm_a, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = hx; b.oy = hy;
                b.zig = 0.25f; b.zig_every = 0.2f;
                out[n++] = b;
            }
            return n;
        }
        float bee = ENRAGED ? BEE_EVERY * 0.7f : BEE_EVERY;
        while (state == RUN && bee_t >= bee && n + 2 <= max) {   // bees off its hat
            // A pair, out to both sides of its run -- a tidy ladder of bees
            // left in its wake, buzzing gently.
            bee_t -= bee;
            float hx, hy, run = atan2f(ty - y, tx - x);
            at(27.0f, 21.0f, &hx, &hy);
            for (int side = -1; side <= 1; side += 2) {
                BulletSpawn b = mk(run + side * PI / 2, SPEED, 2.5f, 5.0f);
                b.from = true; b.ox = hx; b.oy = hy;
                b.zig = 0.25f; b.zig_every = 0.2f;                 // buzzing
                out[n++] = b;
            }
        }
        if (landed && n + 5 <= max) {                            // its spurs sting, landing
            landed = false;
            float fx, fy;
            at(29.0f, 50.0f, &fx, &fy);
            float a = aim_at(fx, fy, px, py);
            for (int k = -2; k <= 2; k++) {
                BulletSpawn b = mk(a + k * 0.16f, SPEED, 3.0f, 5.0f);
                b.from = true; b.ox = fx; b.oy = fy;
                out[n++] = b;
            }
        }
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int) override {
        if (state != STAND || ENRAGED) return 0;
        // The praise-song: a SUN coming down -- formed from a condensed ball
        // at the staff's tip, every note bursting out to its place in the
        // ring or a ray within SUN_FORM s and easing to a slow swell there,
        // the whole sun sinking and turning slowly as it falls (the user).
        float sx, sy;
        staff(facing_toward(px - x, py - y), &sx, &sy);
        int n = 0, ring = ENRAGED ? 22 : 18, rays = ENRAGED ? 12 : 8;
        // ...flying at where the player is now (the user), not just down.
        float aim = aim_at(sx, sy, px, py), turn = ernd() * TAU;
        float fvx = cosf(aim) * SPEED, fvy = sinf(aim) * SPEED;
        auto shot = [&](float a, float r) {
            float v0 = 2.0f * r / SUN_FORM;                       // there in SUN_FORM s, then easing
            BulletSpawn b = mk(a, v0, 3.0f, 5.0f);
            b.from = true; b.ox = sx; b.oy = sy;
            b.accel = -v0 / SUN_FORM; b.min_speed = 8.0f * r / 26.0f;
            b.orbit_w = 0.25f; b.orbit_vx = fvx; b.orbit_vy = fvy;
            out[n++] = b;
        };
        for (int i = 0; i < ring; i++) shot(turn + i * (TAU / ring), 26.0f);
        for (int k = 0; k < rays; k++)
            for (int j = 0; j < 3; j++) shot(turn + (k + 0.5f) * (TAU / rays), 38.0f + j * 9.0f);
        return n;
    }
};

// The ugjuknarpak of Kodiak Island (A Book of Creatures): ugjuk, the
// bearded seal, -narpak, huge -- a giant seal in the island's lakes that
// overturns kayaks and drags the hunters down. UPPER tier, 650 HP, ice-grey
// bullets. BIG sheet: REARED UP on its hind legs the whole time (the user),
// clawing at the air in turn and roaring. It never moves. Every shot
// leaves from the part of it that makes it (the user): its claws, its roar.
// It SCRATCHES BULLETS EVERYWHERE (the user): every shot is part of a
// SCRATCH -- four parallel claw streaks, three shots long, flying together.
// Phase 1:
//   Swipe -- each time a paw comes up (idle frames 1 and 3) it rakes the air:
//            SWIPE_DIRS scratches out of the paw all round, one of them
//            always straight at the player.
//   Roar  -- with its mouth widest (idle frame 2) it tears at everything:
//            ROAR_DIRS scratches burst from its mouth all round, set between
//            the swipe's.
// Phase 2 (half HP): every scratch CURVES as it flies, the left paw's one
//   way and the right paw's the other (the roar's alternating), so the
//   claw streaks sweep in spirals across each other.
class Ugjuknarpak : public Enemy {
    static constexpr float SPEED = 100.0f;
    static constexpr int   SWIPE_DIRS = 6, ROAR_DIRS = 12;
    int swipes = 0;                          // which paw: they swipe in turn

    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    int dir8(float px, float py) const {                       // D DR R UR U UL L DL
        int f = facing_toward(px - x, py - y);
        return f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
             : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
    }
public:
    Ugjuknarpak() : Enemy(320, 130, 650, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "UGJUKNARPAK"; }
    int         breath_frame()  const override { return 2; }       // the roar, mouth widest
    float       fire_interval() const override { return 99.0f; }   // all on its idle frames
    int fire(float, float, BulletSpawn[], int) override { return 0; }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int max) override {
        if (frame != 1 && frame != 3) return 0;
        // A paw up: scratches out of it all round, one straight at the player.
        static const float PX[8] = { 70, 71, 67, 73, 72, 24, 29, 25 }, PY[8] = { 22, 22, 42, 42, 42, 42, 42, 22 };
        int d = dir8(px, py);
        float cx, cy;
        at(PX[d], PY[d], &cx, &cy);
        float a = aim_at(cx, cy, px, py), curve = ENRAGED ? ((swipes++ & 1) ? -0.45f : 0.45f) : 0.0f;
        int n = 0;
        for (int k = 0; k < SWIPE_DIRS && n + 12 <= max; k++) n += scratch_shots(cx, cy, a + k * (TAU / SWIPE_DIRS), SPEED, curve, out + n);
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The roar: scratches burst from its mouth all round, set between the swipe's.
        static const float MX[8] = { 54, 58, 66, 64, 60, 33, 31, 39 }, MY[8] = { 23, 22, 22, 20, 18, 20, 22, 22 };
        int d = dir8(px, py);
        float ox, oy;
        at(MX[d], MY[d], &ox, &oy);
        float a = aim_at(ox, oy, px, py) + PI / ROAR_DIRS;
        int n = 0;
        for (int k = 0; k < ROAR_DIRS && n + 12 <= max; k++)
            n += scratch_shots(ox, oy, a + k * (TAU / ROAR_DIRS), SPEED, ENRAGED ? ((k & 1) ? -0.45f : 0.45f) : 0.0f, out + n);
        return n;
    }
};

// Bes kotak, the Jah Hut "box spirit" (A Book of Creatures): a river spirit
// of the muddy hollows that weighs divers down into the mud until they
// drown. UPPER tier, 660 HP, lid-gold bullets. BIG sheet: a BLOCKY floating
// wooden box with a lid, glowing square eyes and block arms (frame 2 the
// lid lifts off, the mouth slot gapes). It never moves. Every shot leaves
// from the part of it that makes it (the user): out of the open box, or
// dropped from its bottom. BOXES all the way: its shots fly in square
// formations. Every shot goes at about one pace, SPEED.
// Phase 1:
//   Lid    -- as the lid lifts (idle frame 2): BOX_N spinning BOXES burst out
//             of the open box all round -- each a hollow square of 12 shots,
//             opening out of a single point as it flies, turning as it goes
//             -- one of them straight at the player.
//   Sink   -- every SINK_EVERY s it drops a heavy BLOCK from its bottom: a
//             solid 3x3 square, turning slowly, that HOMES on the player for
//             HOME_T s (the user) -- the weight that drags divers down.
// Phase 2 (half HP): twelve boxes, every other one turning the other way;
//   two blocks at a time, either side of the player.
class BesKotak : public Enemy {
    static constexpr float SPEED = 100.0f, FORM_T = 0.6f, BOX_H = 18.0f, HOME_T = 4.0f;   // HOME_T: the user wanted the homing longer (was 2)
    float sink_t = 0.0f;

    float sink_every() const { return ENRAGED ? 1.1f : 1.4f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
public:
    BesKotak() : Enemy(320, 130, 660, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "BES KOTAK"; }
    int         breath_frame()  const override { return 2; }       // the lid lifting off
    float       fire_interval() const override { return 0.05f; }   // the blocks on their own clock
    void update(float dt, float, float) override { sink_t += dt; }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        if (sink_t < sink_every() || max < 18) return 0;
        sink_t = 0.0f;
        // A heavy block from its bottom: a solid 3x3, turning slowly, at the player.
        static float bx[9], by[9];
        for (int k = 0; k < 9; k++) { bx[k] = (k % 3 - 1) * 11.0f; by[k] = (k / 3 - 1) * 11.0f; }
        bx[4] = 0.01f;                                              // the middle one: just off centre, so it has a heading
        float ox, oy;
        at(49.0f, 46.0f, &ox, &oy);
        float a = aim_at(ox, oy, px, py);
        int n = 0;
        if (!ENRAGED) n += shape_shots(ox, oy, a, SPEED, 0.6f, FORM_T, bx, by, 9, out);
        else for (int s = -1; s <= 1; s += 2) n += shape_shots(ox, oy, a + s * 0.3f, SPEED, s * 0.6f, FORM_T, bx, by, 9, out + n);
        for (int k = 0; k < n; k++) { out[k].homing = true; out[k].homing_timer = HOME_T; }   // it HOMES (the user), for a while
        return n;
    }
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The lid: hollow spinning boxes burst out of the open box all round.
        static float qx[12], qy[12];
        static const float T[4] = { -1.0f, -1.0f / 3.0f, 1.0f / 3.0f, 1.0f };
        for (int k = 0; k < 3; k++) {                               // round the square: top, right, bottom, left
            qx[k]     = T[k] * BOX_H;      qy[k]     = -BOX_H;
            qx[3 + k] = BOX_H;             qy[3 + k] = T[k] * BOX_H;
            qx[6 + k] = -T[k] * BOX_H;     qy[6 + k] = BOX_H;
            qx[9 + k] = -BOX_H;            qy[9 + k] = -T[k] * BOX_H;
        }
        float ox, oy;
        at(49.0f, 19.0f, &ox, &oy);
        float a = aim_at(ox, oy, px, py);
        int n = 0, boxes = ENRAGED ? 12 : 8;
        for (int k = 0; k < boxes && n + 12 <= max; k++)
            n += shape_shots(ox, oy, a + k * (TAU / boxes), SPEED, (ENRAGED && (k & 1)) ? -1.0f : 1.0f, FORM_T, qx, qy, 12, out + n);
        return n;
    }
};

// The ieltxu of Gernika's caves and wells (A Book of Creatures): a Basque
// trickster spirit that leads travellers astray at night, seen as a bird
// shooting flames from its mouth -- in the dark, only its fire. UPPER tier,
// 680 HP, flame-orange bullets. MEDIUM sheet: a near-black night bird; ALT
// sheet 81_ieltxu_fire, the same bird LIT, breathing fire (0 drawing breath,
// 1 the jet from its beak, 2 trailing off).
// The user's design: it's DARK -- unseen (the player's shots go where they
// face) -- and only LIGHTS UP when it breathes fire, or when the player comes
// close... and close is exactly where not to be (the user: it's meant NOT
// to be approached): within NEAR px its heat bursts out round it, ring
// after ring, fast. It flits about at random round a spot that drifts on
// its own -- but it breathes fire from that spot.
// Every shot leaves from the part of it that makes it (the user): its beak,
// its burning body.
// Phase 1:
//   Fire  -- every BREATH_EVERY s it lights up, draws breath (DRAW_T s, the
//            warning) and SPEWS fireballs from its beak at where the player
//            was for JET_T s -- tons, spraying wide: the part to dodge
//            (the user).
//   Heat  -- while the player is within NEAR px it's lit and bursts rings of
//            20 embers round itself every HEAT_EVERY s -- keep away.
// Phase 2 (half HP): it spews thicker and wider, and breathes more often.
class Ieltxu : public Enemy {
    static constexpr float NEAR = 150.0f, HEAT_EVERY = 0.22f, SPEED = 110.0f;   // don't come close: dense heat, fast
    static constexpr float DRAW_T = 0.35f, JET_T = 0.6f, TRAIL_T = 0.3f, SPEW_EVERY = 0.03f;
    static constexpr float RING_R = 95.0f;   // it flits about within this of its drifting spot
    static constexpr float DART_T = 0.45f, DART_SPEED = 170.0f;   // flitting about round its spot
    float rcx = 320.0f, rcy = 150.0f, rtx = 320.0f, rty = 150.0f;   // its spot, drifting to (rtx, rty)
    float tx = 320.0f, ty = 150.0f;          // where the bird is darting to, round its spot
    float breath_t = 0.0f, breath = -1.0f, spew_t = 0.0f, aim = 0.0f, bx = 0.0f, by = 0.0f;
    float heat_t = 0.0f, dart_t = 0.0f;
    bool  near = false;
    int   breath_face = FACE_DOWN;

    float breath_every() const { return ENRAGED ? 2.2f : 3.0f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (64x49, drawn 2x about its middle) -> screen
        *ox = x + (fx - 32.0f) * 2.0f; *oy = y + (fy - 24.5f) * 2.0f;
    }
    // Its beak, where the fire sheet's jet leaves it, facing `f`.
    void beak(int f, float* ox, float* oy) const {
        static const float FX[8] = { 40, 38, 36, 36, 34, 27, 27, 25 }, FY[8] = { 18, 17, 17, 15, 12, 15, 17, 17 };
        int d = f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
              : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
        at(FX[d], FY[d], ox, oy);
    }
    bool lit() const { return breath >= 0.0f || near; }
public:
    Ieltxu() : Enemy(320, 150, 680, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "IELTXU"; }
    float       fire_interval() const override { return 0.02f; }   // all on its own clocks
    float opacity(float, float) const override { return lit() ? 1.0f : 0.15f; }
    bool  alt_pose()    const override { return lit(); }
    int   anim_frame()  const override {                         // the breath plays the fire sheet 0-1-2
        if (breath < 0.0f) return near ? 0 : -1;
        return breath < DRAW_T ? 0 : breath < DRAW_T + JET_T ? 1 : 2;
    }
    int   move_facing() const override { return breath >= 0.0f ? breath_face : -1; }
    void update(float dt, float px, float py) override {
        near = hypotf(px - x, py - y) < NEAR;
        heat_t += dt;
        // Its spot drifts about the upper arena on its own (holding still
        // while it breathes)...
        float dx = rtx - rcx, dy = rty - rcy, d = hypotf(dx, dy);
        if (d < 4.0f) { rtx = 130.0f + ernd() * (ARENA_W - 260.0f); rty = ARENA_TOP + 110.0f + ernd() * 120.0f; }
        else if (breath < 0.0f) { rcx += dx / d * 40.0f * dt; rcy += dy / d * 40.0f * dt; }
        // ...and the bird flits about round it at random (the user): quick
        // darts to new spots, a new one every DART_T s or so.
        if (breath < 0.0f) {
            float ex = tx - x, ey = ty - y, ed = hypotf(ex, ey);
            dart_t -= dt;
            if (ed < 4.0f || dart_t <= 0.0f || hypotf(tx - rcx, ty - rcy) > RING_R - 25.0f) {
                float a = ernd() * TAU, r = ernd() * (RING_R - 30.0f);
                tx = rcx + cosf(a) * r; ty = rcy + sinf(a) * r;
                dart_t = DART_T * (0.5f + ernd());
            } else { float st = fminf(DART_SPEED * dt, ed); x += ex / ed * st; y += ey / ed * st; }
            if ((breath_t += dt) >= breath_every()) {           // it lights up and draws breath -- on its spot (the user)
                x = rcx; y = rcy;
                breath_t = 0.0f; breath = 0.0f; spew_t = 0.0f;
                breath_face = facing_toward(px - x, py - y);
                beak(breath_face, &bx, &by);
                aim = aim_at(bx, by, px, py);
            }
        } else {
            breath += dt;
            if (breath >= DRAW_T) spew_t += dt;
            if (breath >= DRAW_T + JET_T + TRAIL_T) breath = -1.0f;
        }
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int n = 0;
        // The fire: TONS of fireballs spewed from its beak at where the
        // player was, spraying wide -- the part to dodge (the user).
        int per = ENRAGED ? 3 : 2;
        float spread = ENRAGED ? 0.9f : 0.55f;
        while (breath >= DRAW_T && breath < DRAW_T + JET_T && spew_t >= SPEW_EVERY && n + per <= max) {
            spew_t -= SPEW_EVERY;
            for (int k = 0; k < per; k++) {
                BulletSpawn b = mk(aim + (ernd() * 2.0f - 1.0f) * spread, SPEED, 3.0f, 5.0f);
                b.from = true; b.ox = bx; b.oy = by;
                out[n++] = b;
            }
        }
        if (near && heat_t >= HEAT_EVERY && n + 20 <= max) {      // too close: its heat bursts out, ring after ring
            heat_t = 0.0f;
            float turn = ernd() * TAU;
            for (int i = 0; i < 20; i++) out[n++] = mk(turn + i * (TAU / 20), SPEED * 1.3f, 3.0f, 5.0f);
        }
        return n;
    }
};

// The nadubi of western Arnhem Land (A Book of Creatures; Kunwinjku rock
// art): malevolent spirits with barbs growing from their elbows and knees,
// which they SHOOT into people to kill them. UPPER tier, 700 HP, bone-pale
// bullets. BIG sheet: a gaunt dark-ochre spirit crawling like a spider,
// long bone barbs off its elbows, knees and spine (frame 2 reared, crest
// flared -- the launch); flap = 82_nadubi_crawl when the art lands, played
// as it scuttles. Every shot leaves from the part of it that makes it (the
// user): the tips of its barbs. DEMONIC IMAGERY AND SCRATCHES (the user):
// its shots are claw scratches and sigils. Every shot goes at one pace.
// SCRATCHES ONLY, like MAGIC (the user): wave after wave of claw scratches
// all moving in the same curving motion, each wave from the next barb tip
// round its body and turned a step on -- they wheel out in spiral arms,
// mesmerising, to be learned.
//   Scuttle -- it skitters along the top in sudden bursts, side to side,
//              SCUTTLES times between formations, holding its fire.
//   Form    -- then it REARS UP on its hind legs and SCRATCHES the air (the
//              user; ALT sheet 82_nadubi_scratch, its frames played through
//              on its own clock) for FORM_T s, and where its claws rake the
//              pattern forms: at each slash (frames 1 and 3, left claw then
//              right), WAVE_N scratches all round from the slashing claw's
//              tip, the ring turned TURN on from the last, every scratch
//              curving at CURVE as it flies.
//   Idle    -- standing between skitters, its idle raises one claw and
//              rakes once, and a PENTAGRAM grows out from where it
//              scratched -- Ebigane's, a star in its ring, 75 shots,
//              until it's bigger than the arena.
// Phase 2 (a third of its HP left, the user): it rears up and SCRATCHES
//   UNTIL IT DIES (the user),
//   every other wave curving the other way -- the arms weave.
class Nadubi : public Enemy {
    static constexpr float SPEED = 120.0f, SCUTTLE_SPEED = 260.0f;   // quick enough to clear the screen: a denser fight under the shot cap
    static constexpr float TURN = 0.3f, CURVE = 0.4f;
    static constexpr int   WAVE_N = 9;     // denser (the user): 40 deg between clumps
    static constexpr int   SCUTTLES = 1;   // more often (the user)
    static constexpr float CLAW_FRAME = 0.2f;    // the scratch sheet's frames, this long each: a slash every 0.4 s
    float scuttle_t = 0.0f, turn = 0.0f, tx = 320.0f, t = 0.0f;
    int   last_frame = -1;                  // the scratch frame shown last: a slash fires as it turns to 1 or 3
    float form = -1.0f;                      // seconds into a formation (-1 = scuttling)
    int   waves = 0, scuttles = 0;

    float form_t() const { return 4.0f; }   // longer (the user); phase 2 never stops

    float scuttle_every() const { return ENRAGED ? 0.9f : 1.4f; }
    void at(float fx, float fy, float* ox, float* oy) const {   // art px (98x65, drawn 2x about its middle) -> screen
        *ox = x + (fx - 49.0f) * 2.0f; *oy = y + (fy - 32.5f) * 2.0f;
    }
    // Its five barb tips (the launch frame's), in the way it's drawn.
    void tips(float px, float py, float ox[5], float oy[5]) const {
        static const float T[8][5][2] = {
            {{26,21},{33,15},{48,25},{61,21},{69,15}},   // D
            {{21,21},{40,26},{41,15},{47,21},{67,15}},   // DR
            {{28,21},{36,26},{40,21},{45,25},{55,15}},   // R
            {{21,21},{40,26},{41,15},{44,21},{67,15}},   // UR
            {{26,21},{33,15},{47,21},{61,21},{69,15}},   // U
            {{30,15},{50,21},{57,15},{57,26},{76,21}},   // UL
            {{42,15},{52,25},{57,21},{61,26},{70,21}},   // L
            {{30,15},{50,21},{57,15},{57,26},{76,21}} }; // DL
        int f = move_facing() >= 0 ? move_facing() : facing_toward(px - x, py - y);   // the way it's drawn
        int d = f == FACE_DOWN ? 0 : f == FACE_DOWN_RIGHT ? 1 : f == FACE_RIGHT ? 2 : f == FACE_UP_RIGHT ? 3
              : f == FACE_UP ? 4 : f == FACE_UP_LEFT ? 5 : f == FACE_LEFT ? 6 : 7;
        for (int k = 0; k < 5; k++) at(T[d][k][0], T[d][k][1], &ox[k], &oy[k]);
    }
    bool scuttling() const { return fabsf(tx - x) > 0.5f; }
    // A wave: WAVE_N scratches spaced down a claw's rake, (x0, y0) to (x1,
    // y1) in art px, flying out all round, turned on a step, all curving alike.
    int wave(float x0, float y0, float x1, float y1, BulletSpawn out[]) {
        float curve = (ENRAGED && (waves & 1)) ? -CURVE : CURVE;
        waves++;
        turn += TURN;
        int n = 0;
        for (int k = 0; k < WAVE_N; k++) {
            float u = (k + 0.5f) / WAVE_N, cx, cy;               // down the rake
            at(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, &cx, &cy);
            n += scratch_shots(cx, cy, turn + k * (TAU / WAVE_N), SPEED, curve, out + n);
        }
        return n;
    }
public:
    Nadubi() : Enemy(320, 130, 700, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "NADUBI"; }
    float       phase2_at()     const override { return 0.33f; }   // stage 1 for the first two thirds of its HP (the user)
    float       fire_interval() const override { return 0.05f; }   // the waves on their own clock
    int   move_facing() const override { return scuttling() ? (tx > x ? FACE_RIGHT : FACE_LEFT) : -1; }
    bool  alt_pose()    const override { return form >= 0.0f; }   // reared up, scratching
    int   breath_frame() const override { return 2; }              // its idle claw raised and raking once
    int breathe(float px, float py, BulletSpawn out[], int max) override {
        // The idle scratch (the user): its one raised claw rakes once and a
        // PENTAGRAM forms where it scratched -- a star in its ring, the same
        // as Ebigane's (the user), growing out of the claw's tip (the idle
        // sheet's frame 2, measured; left facings mirror the right) until
        // it's bigger than the arena.
        if (form >= 0.0f || scuttling() || max < 75) return 0;
        static const float CX[5] = { 71, 79, 81, 60, 45 };          // D DR R UR U, y 32
        int fc = facing_toward(px - x, py - y);
        bool mirror = fc == FACE_DOWN_LEFT || fc == FACE_LEFT || fc == FACE_UP_LEFT;
        int d = fc == FACE_DOWN ? 0 : fc == FACE_DOWN_RIGHT || fc == FACE_DOWN_LEFT ? 1 : fc == FACE_RIGHT || fc == FACE_LEFT ? 2
              : fc == FACE_UP_RIGHT || fc == FACE_UP_LEFT ? 3 : 4;
        float hx = mirror ? 97.0f - CX[d] : CX[d], cx, cy;
        at(hx, 32.0f, &cx, &cy);
        return pentagram_shots(out, false, true, cx, cy);   // the same pentagram as Ebigane's (the user): huge, growing
    }
    int   anim_frame()  const override { return form >= 0.0f ? (int)(form / CLAW_FRAME) % 5 : -1; }
    float flap_phase()  const override { return scuttling() ? fmodf(t / 0.3f, 1.0f) : -1.0f; }   // the crawl, once drawn
    void update(float dt, float, float) override {
        t += dt;
        if (form >= 0.0f) {                                      // reared up, scratching the pattern out
            form += dt;
            if (form >= form_t() && !ENRAGED) { form = -1.0f; scuttles = 0; scuttle_t = 0.0f; }   // phase 2: scratching till it dies (the user)
            return;
        }
        if (ENRAGED && !scuttling()) { form = 0.0f; last_frame = -1; return; }   // phase 2: up it rears, for good
        if ((scuttle_t += dt) >= scuttle_every()) {              // a sudden skitter to a new spot -- or, after a few, a formation
            scuttle_t = 0.0f;
            if (scuttles++ >= SCUTTLES && !scuttling()) { form = 0.0f; last_frame = -1; return; }
            float step = (ernd() < 0.5f ? -1.0f : 1.0f) * (90.0f + ernd() * 90.0f);
            if (x + step < 110.0f || x + step > ARENA_W - 110.0f) step = -step;
            tx = fminf(fmaxf(x + step, 110.0f), ARENA_W - 110.0f);
        }
        float dx = tx - x, st = SCUTTLE_SPEED * dt;
        x = fabsf(dx) <= st ? tx : x + (dx > 0.0f ? st : -st);
    }
    int fire(float px, float py, BulletSpawn out[], int max) override {
        int f = anim_frame();
        if (f == last_frame) return 0;
        last_frame = f;
        if ((f != 1 && f != 3) || max < WAVE_N * 12) return 0;
        // A slash: scratches spawned ALONG THE RAKE (the user: where it
        // scratches) -- spaced down the line its claw sweeps, from its high
        // tip (frame 0 / 2) to its slash tip (frame 1 / 3), all measured on
        // the scratch sheet (left facings mirror the right) -- flying out all
        // round, turned on a step, all curving alike.
        static const float HIGH_X[2][5]  = { { 63, 68, 66, 54, 44 }, { 44, 54, 66, 68, 63 } };   // [left, right claw][D DR R UR U], y 4
        static const float SLASH_X[2][5] = { { 63, 71, 72, 59, 47 }, { 47, 59, 72, 71, 63 } };   // y 47
        int fc = facing_toward(px - x, py - y);
        bool mirror = fc == FACE_DOWN_LEFT || fc == FACE_LEFT || fc == FACE_UP_LEFT;
        int d = fc == FACE_DOWN ? 0 : fc == FACE_DOWN_RIGHT || fc == FACE_DOWN_LEFT ? 1 : fc == FACE_RIGHT || fc == FACE_LEFT ? 2
              : fc == FACE_UP_RIGHT || fc == FACE_UP_LEFT ? 3 : 4;
        int claw = f == 3;
        float hx = HIGH_X[claw][d], sx = SLASH_X[claw][d];
        if (mirror) { hx = 97.0f - hx; sx = 97.0f - sx; }
        return wave(hx, 4.0f, sx, 47.0f, out);
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
        case 50: return new Teakettler();
        case 51: return new Aspidochelone();
        case 52: return new Sannaja();
        case 53: return new ComeAtABody();
        case 54: return new Billdad();
        case 55: return new Wapaloosie();
        case 56: return new Moskitto();
        case 57: return new Dingbat();
        case 58: return new Agropelter();
        case 59: return new Tripodero();
        case 60: return new Rumptifusel();
        case 61: return new Roperite();
        case 62: return new Hugag();
        case 63: return new Hidebehind();
        case 64: return new Dungavenhooter();
        case 65: return new Unfinished("MICE THAT EAT IRON", 300, T_LOW);
        case 66: return new Ayotochtli();
        case 67: return new Lagopus();
        case 68: return new Shuyu();
        case 69: return new BesChem();
        case 70: return new Trollgadda();
        case 71: return new Namungumi();
        case 72: return new Mahwot();
        case 73: return new Liderc();
        case 74: return new BesRap();
        case 75: return new Makalala();
        case 76: return new LochOich();
        case 77: return new Hoga();
        case 78: return new Zankallala();
        case 79: return new Ugjuknarpak();
        case 80: return new BesKotak();
        case 81: return new Ieltxu();
        case 82: return new Nadubi();
        case 83: return new BeastOfBarrisdale();
        case 84: return new Kigutilik();
        case 85: return new Nanabolele();
        case 86: return new Leucrocotta();
        case 87: return new Corocotta();
        case 88: return new Amixsak();
        case 89: return new Unfinished("CUERO", 780, T_HARD);
        case 90: return new Unfinished("CHIPEKWE", 800, T_SEVERE);
        case 91: return new Unfinished("KURREA", 820, T_SEVERE);
        case 92: return new Unfinished("SIEHNAM", 830, T_SEVERE);
        case 93: return new Unfinished("CHIPIQUE", 840, T_SEVERE);
        case 94: return new Unfinished("TROCHUS", 860, T_SEVERE);
        case 95: return new Unfinished("WITKES", 880, T_SEVERE);
        case 96: return new Unfinished("BREGDI", 920, T_ELITE);
        case 97: return new Unfinished("RO", 950, T_ELITE);
        case 98: return new Unfinished("BOIUNA", 980, T_ELITE);
        case 99: return new Unfinished("FAD FELEN", 1000, T_ELITE);
        case 100: return new Unfinished("FLESH PLANET", 6000, T_BOSS3);   // final boss: the ball only for now
        default: return new Skvader();
    }
}

// What each enemy drops, by id: fur and feather give hide, shell, scale and
// stone give bone, spirits and omens give essence. The Treesqueak, a tree
// creature met on the starting island, gives vine -- the lashing for the raft
// that is the way off it.
// Fur only from the bears, and only the hard ones (UPPER and up): the
// sleeping bag's lining is meant to be hard won.
static const MonsterPart ENEMY_PARTS[] = {
    PART_HIDE,    PART_HIDE,    PART_VINE,    PART_FEATHER, PART_HIDE,      //  0-4  (03 Qique: feathers)
    PART_BONE,    PART_HIDE,    PART_ESSENCE, PART_HIDE,    PART_BONE,      //  5-9
    PART_BONE,    PART_HIDE,    PART_BONE,    PART_HIDE,    PART_BONE,      // 10-14
    PART_BONE,    PART_ESSENCE, PART_ESSENCE, PART_BONE,    PART_BONE,      // 15-19
    PART_FUR,     PART_BONE,    PART_HIDE,    PART_BONE,    PART_BONE,      // 20-24  (20 Sermilik: white fur)
    PART_BONE,    PART_ESSENCE, PART_BONE,    PART_HIDE,    PART_HIDE,      // 25-29
    PART_ESSENCE, PART_BONE,    PART_BONE,    PART_HIDE,    PART_ESSENCE,   // 30-34
    PART_ESSENCE, PART_HIDE,    PART_ESSENCE, PART_ESSENCE, PART_HIDE,      // 35-39
    PART_BONE,    PART_FUR,     PART_ESSENCE, PART_BONE,    PART_HIDE,      // 40-44  (41 Sasnalkahi: white fur)
    PART_ESSENCE, PART_BONE,    PART_BONE,    PART_FUR,     PART_BONE,      // 45-49  (48 Bjarndyrakongur: white fur)
    PART_HIDE,    PART_BONE,    PART_ESSENCE,                               // 50 Teakettler, 51 Aspidochelone, 52 Sannaja
    PART_HIDE, PART_HIDE, PART_HIDE, PART_ESSENCE, PART_HIDE, PART_HIDE, PART_BONE, PART_HIDE, PART_HIDE, PART_HIDE, PART_HIDE, PART_BONE,   // 53-64
    PART_HIDE, PART_BONE, PART_HIDE, PART_HIDE, PART_ESSENCE, PART_BONE,   // 65-70
    PART_BONE, PART_BONE, PART_ESSENCE, PART_ESSENCE, PART_HIDE, PART_HIDE,   // 71-76
    PART_BONE, PART_ESSENCE, PART_HIDE, PART_ESSENCE, PART_ESSENCE, PART_ESSENCE,   // 77-82
    PART_HIDE, PART_ESSENCE, PART_BONE, PART_HIDE, PART_BONE, PART_ESSENCE,   // 83-88
    PART_HIDE, PART_BONE, PART_BONE, PART_HIDE, PART_BONE, PART_BONE,   // 89-94
    PART_ESSENCE, PART_BONE, PART_BONE, PART_ESSENCE, PART_ESSENCE,   // 95-99
};

// Each enemy's bullet colour, picked from its art and brightened to an exact
// palette entry that stands off the black. Ids past the table get pink until
// their round.
struct BulletRGB { int id; Uint8 r, g, b; };
static const BulletRGB ENEMY_BULLET_RGB[] = {
    {  0, 252, 152,  56 },   // Skvader: orange, its gold-brown fur brightened
    {  1, 236, 132, 118 },   // Wolpertinger: salmon, its red wings
    {  2,  78, 220,  74 },   // Treesqueak: green, its leaf marks
    {  3, 182, 156, 238 },   // Qique: lavender, its dark purple plumage
    {  4, 252, 116, 180 },   // Lili: hot pink, its pink hide
    {  5, 208, 192, 120 },   // Crowing Crested Cobra: pale gold, its scales
    {  6, 252, 116, 180 },   // Wakmangganchi Aragondi: not yet picked (the default)
    {  7, 250, 228, 136 },   // Alber: pale flame yellow, its electric-fire glow
    {  8, 252, 116, 180 },   // Snawfus: blossom pink, the flowers on its antlers
    {  9, 240, 188,  60 },   // Questing Beast: gold, its leopard's coat
    { 10,  78, 220,  74 },   // Grand'Goule: green, its fire breath
    { 11, 240, 184, 144 },   // Paoxiao: pale skin, its human face
    { 12, 236, 132, 118 },   // Ebigane: wing red, its bat wings
    { 50, 198, 204, 218 },   // Teakettler: steam, white-blue (repick with its sprite)
    { 51,  79, 166, 103 },   // Aspidochelone: sea green (repick with its sprite)
    { 52, 183,   0,   0 },   // Sannaja: deep red, its killing gaze (repick with its sprite)
    { 53, 206, 190, 130 },   // Come-at-a-body: musky pale yellow, its spit and stench (sprite's pale fur)
    { 54, 132, 167, 233 },   // Billdad: pond-water blue, the splash of Boundary Pond
    { 55, 182, 156, 238 },   // Wapaloosie: its velvet violet (sprite's light fur)
    { 56, 240, 188,  60 },   // Moskitto: bee yellow (its bands)
    { 66, 206, 190, 130 },   // Ayotochtli: shell tan (its light bands)
    { 67, 220, 240, 255 },   // Lagopus: near-white snow (the user wanted it whiter)
    { 68, 236, 132, 118 },   // Shuyu: red feather, the light red of its plumage
    { 69, 240, 232, 128 },   // Bes Chem: its glowing yellow eyes
    { 14, 198, 204, 218 },   // Lodsilungur: mold white (its cottony hair)
    { 15, 236, 132, 118 },   // Ofuguggi: its red flesh
    { 17, 240, 184, 144 },   // Qiqirn: its bare pale skin
    { 57, 206, 190, 130 },   // Dingbat: owl buff (its pale face)
    { 58, 178, 150, 106 },   // Agropelter: bark (its branches)
    { 59, 236, 132, 118 },   // Tripodero: clay red (its slugs)
    { 60, 148, 112,  61 },   // Rumptifusel: its fur brown
    { 70,  79, 166, 103 },   // Trollgadda: moss green (its leaves)
    { 71, 198, 204, 218 },   // Namungumi: its pale veins
    { 72,  79, 166, 103 },   // Mahwot: river green (its scales)
    { 73, 252, 152,  56 },   // Liderc: wisp-flame orange
    { 74, 232, 224, 192 },   // Bes Rap: frothing foam
    { 75, 201, 164,  51 },   // Makalala: its beak yellow
    { 61, 216, 152,  48 },   // Roperite: its rattle orange
    { 62, 193, 138,  57 },   // Hugag: its coat's gold tips
    { 63, 232, 224, 192 },   // Hidebehind: its ivory claws
    { 64, 164, 170, 186 },   // Dungavenhooter: its club grey
    { 76, 193, 138,  57 },   // Loch Oich monster: its brown coat, lit
    { 77,  62, 145, 204 },   // Hoga: lake blue (its fins' shine)
    { 21, 183,   0,   0 },   // Asp: venom red (its tongue)
    { 78, 240, 188,  60 },   // Zankallala: bee gold
    { 79, 188, 190, 202 },   // Ugjuknarpak: its grey hide, lit
    { 80, 240, 188,  60 },   // Bes kotak: its glowing eyes
    { 81, 252, 152,  56 },   // Ieltxu: its flame
    { 82, 232, 224, 192 },   // Nadubi: its bone barbs
    { 22, 232, 224, 160 },   // Cactus cat: its pale thorns
    { 24, 248,  88,   0 },   // Zoureg: red-hot orange
    { 26, 248, 216, 120 },   // Akhekh: sun gold
    { 28, 232, 184,  48 },   // Opimachus: its gold beak
    { 16, 220, 240, 255 },   // Kamaitachi: wind white
    { 18, 132, 167, 233 },   // Vatnaormur: its lake's blue
    { 19, 214, 220, 236 },   // Skeljaskrimsli: shell pearl
    { 20, 160, 216, 255 },   // Sermilik: ice blue
    { 27, 200, 240, 248 },   // Grootslang: its cave's diamonds
    { 33, 224, 144,  96 },   // Tse'nagahi: red sandstone
    { 39, 232,  72,  88 },   // Ajaju: its tongues' red
    { 42, 176, 208, 216 },   // Nykur: lake grey
    { 43, 240, 216, 232 },   // Sazae-oni: mother-of-pearl
    { 83, 248, 152,  56 },   // Beast of Barrisdale: its burning eyes
    { 84, 200, 176, 248 },   // Kigutilik: ice violet
    { 85, 168, 240, 188 },   // Nanabolele: its scale lights
    { 86, 236, 228, 200 },   // Leucrocotta: its bone ridge
    { 87, 196, 200, 220 },   // Corocotta: grey steel, its teeth
    { 88, 120, 200, 184 },   // Amixsak: cold seawater
    {100, 182,  67,  61 },   // Flesh planet: raw flesh
};

SDL_Color enemy_bullet_color(int id) {
    for (const BulletRGB& c : ENEMY_BULLET_RGB)
        if (c.id == id) return { c.r, c.g, c.b, 255 };
    return { 252, 116, 180, 255 };   // not picked yet: pink
}

MonsterPart enemy_part(int id) {
    if (id < 0 || id >= (int)(sizeof(ENEMY_PARTS) / sizeof(ENEMY_PARTS[0]))) return PART_HIDE;
    return ENEMY_PARTS[id];
}

int enemy_defeat_exp(int id) {
    static const int BASE[] = { 50, 50, 100, 250, 350, 450, 600, 800, 1500, 3000, 6000 };   // by EnemyTier
    EnemyTier t = enemy_tier(id);
    int before = 0;   // earlier members of the same tier
    for (int i = 0; i < id; i++) before += enemy_tier(i) == t;
    return BASE[t] + (t == T_UNSET ? 25 : 15) * before;
}
