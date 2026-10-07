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
    Alber() : Enemy(320, 140, 480, {1.0f,1.0f,1.0f,1.25f,1.0f,1.25f,1.25f}) {}
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
    bool blooming() const { return hp < max_hp * 0.66f; }

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
    bool gluttony() const { return hp < max_hp * 0.66f; }

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
    GrandGoule() : Enemy(320, 160, 600, {1.0f,0.75f,1.0f,1.25f,1.25f,1.5f,1.25f}) {}
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
    Ebigane() : Enemy(320, 140, 680, {0.75f,1.5f,0.75f,1.5f,1.25f,1.0f,1.0f}) {}
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
    // A pentagram: every bullet leaves its middle at once with a velocity
    // that is the shape -- the star's five lines (each point to the one two
    // on), 9 along each, inside a ring of 30 -- so the star holds its shape
    // and grows from the enemy outward, a point 120 px/s out, until it is
    // bigger than the arena. Turned at random. `slowing`: every bullet eases
    // off by the same share of its own speed -- to a quarter of it over 3.4 s,
    // when the ring is some 255 px out, near the arena's edges -- so the star
    // keeps its shape while it slows into a huge, slow star round them.
    static int pentagram(BulletSpawn out[], bool slowing) {
        const float R = 120.0f;
        float turn = ernd() * TAU;
        int n = 0;
        auto put = [&](float vx, float vy) {
            BulletSpawn b = mk(0.0f, 0.0f, 2.5f, 5.0f);
            b.vx = vx; b.vy = vy;
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
    // Phase 1: a pentagram. Phase 2: a slowing pentagram at the middle of
    // the loop.
    int fire(float, float, BulletSpawn out[], int) override {
        if (!ENRAGED) return pentagram(out, false);
        if (crossed) { crossed = false; return pentagram(out, true); }
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
    { 252, 116, 180 },   //  4 Lili: hot pink, its pink hide
    { 208, 192, 120 },   //  5 Crowing Crested Cobra: pale gold, its scales
    { 252, 116, 180 },   //  6 Wakmangganchi Aragondi: not yet picked (the default)
    { 250, 228, 136 },   //  7 Alber: pale flame yellow, its electric-fire glow
    { 252, 116, 180 },   //  8 Snawfus: blossom pink, the flowers on its antlers
    { 240, 188,  60 },   //  9 Questing Beast: gold, its leopard's coat
    {  78, 220,  74 },   // 10 Grand'Goule: green, its fire breath
    { 240, 184, 144 },   // 11 Paoxiao: pale skin, its human face
    { 236, 132, 118 },   // 12 Ebigane: wing red, its bat wings
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
