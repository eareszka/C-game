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

    bool reared() const { return hp < max_hp * 0.66f; }   // its own phase line: a third down
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
// Phase 2 (half HP): each caught shot comes back as two, the glides are
//   quicker, and the perches shorter.
class Dingbat : public Enemy {
    static constexpr float CATCH = 72.0f;    // past its body circle (~52): no shot reaches it while it perches
    bool  gliding = false;
    float t = 0.0f, drop_t = 0.0f;
    float x0 = 0, y0 = 0, x1 = 0, y1 = 0;
    float px_ = 320.0f, py_ = 400.0f;
    struct Back { float x, y; } back[32];
    int   nback = 0;

    float glide_t() const { return ENRAGED ? 1.3f : 1.7f; }
    float perch_t() const { return ENRAGED ? 1.1f : 1.6f; }
public:
    Dingbat() : Enemy(320, 120, 420, {1.0f,1.0f,1.0f,1.0f,1.0f,1.0f,1.0f}) {}
    const char* name()          const override { return "DINGBAT"; }
    float       fire_interval() const override { return 0.05f; }   // reflections and glide drops, as they come
    float       catch_radius()  const override { return gliding ? 0.0f : CATCH; }
    bool        alt_pose()      const override { return !gliding; }   // perched: its catching pose (the alt sheet)
    void catch_shot(float bx, float by) override { if (nback < 32) back[nback++] = { bx, by }; }
    int move_facing() const override { return gliding ? facing_toward(x1 - x0, y1 - y0) : -1; }
    void update(float dt, float px, float py) override {
        px_ = px; py_ = py;
        t += dt;
        if (!gliding) {
            if (t >= perch_t()) {
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
        for (int i = 0; i < nback && n < 120; i++) {
            float a = aim_at(back[i].x, back[i].y, px, py);
            for (int k = 0; k < (ENRAGED ? 2 : 1); k++) {
                BulletSpawn b = mk(a + (ENRAGED ? (k ? 0.12f : -0.12f) : 0.0f), 210.0f, 2.5f, 5.0f);
                b.from = true; b.ox = back[i].x; b.oy = back[i].y;
                b.flash_in = true;
                out[n++] = b;
            }
        }
        nback = 0;
        if (gliding && drop_t >= 0.35f) {                        // a 3-fan as it glides
            drop_t = 0.0f;
            float a = aim_at(x,y,px,py);
            for (int i = 0; i < 3; i++) out[n++] = mk(a + (i - 1) * 0.22f, 165.0f, 2.5f, 5.0f);
        }
        return n;
    }
    int on_idle_frame(int frame, float px, float py, BulletSpawn out[], int) override {
        if (frame != 2 || gliding) return 0;                     // a downstroke, perched
        float a = aim_at(x,y,px,py);
        for (int i = 0; i < 9; i++) out[i] = mk(a + (i - 4) * 0.18f, 175.0f, 2.5f, 5.0f);
        return 9;
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
        case 58: return new Unfinished("AGROPELTER", 520, T_MEDIUM);
        case 59: return new Unfinished("TRIPODERO", 540, T_MEDIUM);
        case 60: return new Unfinished("RUMPTIFUSEL", 560, T_MEDIUM);
        case 61: return new Unfinished("ROPERITE", 620, T_UPPER);
        case 62: return new Unfinished("HUGAG", 640, T_UPPER);
        case 63: return new Unfinished("HIDEBEHIND", 660, T_UPPER);
        case 64: return new Unfinished("DUNGAVENHOOTER", 680, T_UPPER);
        case 65: return new Unfinished("MICE THAT EAT IRON", 300, T_LOW);
        case 66: return new Ayotochtli();
        case 67: return new Lagopus();
        case 68: return new Shuyu();
        case 69: return new BesChem();
        case 70: return new Unfinished("TROLLGADDA", 500, T_MEDIUM);
        case 71: return new Unfinished("NAMUNGUMI", 520, T_MEDIUM);
        case 72: return new Unfinished("MAHWOT", 540, T_MEDIUM);
        case 73: return new Unfinished("LIDERC", 550, T_MEDIUM);
        case 74: return new Unfinished("BES RAP", 560, T_MEDIUM);
        case 75: return new Unfinished("MAKALALA", 580, T_MEDIUM);
        case 76: return new Unfinished("LOCH OICH MONSTER", 600, T_UPPER);
        case 77: return new Unfinished("HOGA", 620, T_UPPER);
        case 78: return new Unfinished("ZANKALLALA", 630, T_UPPER);
        case 79: return new Unfinished("UGJUKNARPAK", 650, T_UPPER);
        case 80: return new Unfinished("BES KOTAK", 660, T_UPPER);
        case 81: return new Unfinished("IELTXU", 680, T_UPPER);
        case 82: return new Unfinished("NADUBI", 700, T_UPPER);
        case 83: return new Unfinished("BEAST OF BARRISDALE", 720, T_HARD);
        case 84: return new Unfinished("KIGUTILIK", 730, T_HARD);
        case 85: return new Unfinished("NANABOLELE", 740, T_HARD);
        case 86: return new Unfinished("LEUCROCOTTA", 750, T_HARD);
        case 87: return new Unfinished("COROCOTTA", 760, T_HARD);
        case 88: return new Unfinished("AMIXSAK", 770, T_HARD);
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
    static const int BASE[] = { 50, 50, 100, 250, 350, 450, 600, 800, 1500, 3000 };   // by EnemyTier
    EnemyTier t = enemy_tier(id);
    int before = 0;   // earlier members of the same tier
    for (int i = 0; i < id; i++) before += enemy_tier(i) == t;
    return BASE[t] + (t == T_UNSET ? 25 : 15) * before;
}
