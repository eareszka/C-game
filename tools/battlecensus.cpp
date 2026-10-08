// Battle census: one fight against one enemy, played headless by a dodge bot,
// to test a bullet pattern's fairness (memory: feedback_bullet_fairness).
//
//   battlecensus.exe <enemy id> <seed> [fight seconds=60] [shot dir]
//
// It runs the game's own BattleScene -- its enemy update, fire, breathe and
// on_idle_frame hooks, bullet motion and hit test -- at the game's 60 fps,
// with SDL_GetTicks replaced by the fight's own clock so the idle-frame hooks
// fire as in play and the seed (the enemy RNG's, taken from the clock at the
// start) repeats a fight exactly. The enemy loses HP evenly over the fight
// seconds, so every phase gets played.
//
// The bot: each frame it tries 9 directions x crouch/walk/sprint held for
// LOOKAHEAD s against the bullets moved on in straight lines (mines sit, then
// launch at where it would be), and takes the move whose closest pass is
// widest, drifting home (bottom middle) when nothing is near.
//
// Prints one line per hit (time, the bullet, how far away it spawned) and a
// summary: peak bullets against MAX_ENEMY_BULLETS, frames at the cap, spawns
// within 40 px of the player, tightest clearance the bot found. With a shot
// dir, writes <dir>/hit_<id>_<seed>_<n>.png at each of the first hits.
// One fight a process: the enemy RNG can only be xored, never reset.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cstring>
#include <string>
#include <vector>
#include <algorithm>
#include "entity.h"
#include "input.h"
#include "enemy.h"
#define private public
#include "battle.h"
#undef private

static Uint32 g_ms = 0;
extern "C" Uint32 SDL_GetTicks(void) { return g_ms; }

static const float DT = 1.0f / 60.0f;
static float LOOKAHEAD = 1.0f;   // env BOT_LOOK overrides

struct Ghost { float x, y, vx, vy, r, delay, launch, off, hl, ang;
               float ocx, ocy, orad, oang, ovr, ow;
               float ax, ay;
               float zig, zig_every, zig_t; int zig_s;
               float ease, ease_min; };   // easing: speed falls at ease px/s^2 to ease_min   // zigzag: swings 2*zig every zig_every   // a boomerang's pull (accel without min_speed)   // ow != 0: spirals out from (ocx, ocy)

// Distance along its path by t for a shot at speed v easing at a (< 0) to vmin.
static float eased_dist(float v, float a, float vmin, float t) {
    if (a >= 0.0f || v <= vmin) return v * t;
    float tc = (vmin - v) / a;                   // when it reaches the floor
    if (t <= tc) return v * t + 0.5f * a * t * t;
    return v * tc + 0.5f * a * tc * tc + vmin * (t - tc);
}

// Closest pass (centre gap minus radii) over the lookahead for one candidate move.
static float clearance(const std::vector<Ghost>& gs, float px, float py, float mx, float my,
                       float speed, float ex, float ey, float evx, float evy, float er) {
    float worst = 1e9f;
    const float STEP = 1.0f / 30.0f;
    for (float t = STEP; t <= LOOKAHEAD + 1e-4f; t += STEP) {
        float x = fminf(fmaxf(px + mx * speed * t, 16.0f), ARENA_W - 16.0f);
        float y = fminf(fmaxf(py + my * speed * t, ARENA_TOP + 16.0f), ARENA_H - 16.0f);
        // Weight the near future more: a close shave 0.5 s out can still be fixed.
        float slack = t * 6.0f;
        for (const Ghost& g : gs) {
            float bx, by;
            if (g.delay > t) { bx = g.x; by = g.y; }
            else if (g.delay > 0.0f) {
                float lx = fminf(fmaxf(px + mx * speed * g.delay, 16.0f), ARENA_W - 16.0f);
                float ly = fminf(fmaxf(py + my * speed * g.delay, ARENA_TOP + 16.0f), ARENA_H - 16.0f);
                float a = atan2f(ly - g.y, lx - g.x) + g.off, s = t - g.delay;
                bx = g.x + cosf(a) * g.launch * s; by = g.y + sinf(a) * g.launch * s;
            } else if (g.ow != 0.0f) {
                float rr = g.orad + g.ovr * t, aa = g.oang + g.ow * t;
                bx = g.ocx + cosf(aa) * rr; by = g.ocy + sinf(aa) * rr;
            } else if (g.zig_every > 0.0f) {
                // Straight legs, turning -2*zig*side at each swing, as _move_bullets does.
                float sp = hypotf(g.vx, g.vy) + 1e-6f;
                float vx = g.vx / sp, vy = g.vy / sp, left = t, leg = g.zig_t, done = 0.0f; int side = g.zig_s;
                bx = g.x; by = g.y;
                while (left > 0.0f) {
                    float d = fminf(leg, left);
                    float ds = eased_dist(sp, g.ease, g.ease_min, done + d) - eased_dist(sp, g.ease, g.ease_min, done);
                    bx += vx * ds; by += vy * ds; left -= d; done += d;
                    if (left <= 0.0f) break;
                    float r = -2.0f * g.zig * side, c = cosf(r), sn = sinf(r), ox = vx;
                    vx = ox * c - vy * sn; vy = ox * sn + vy * c;
                    side = -side; leg = g.zig_every;
                }
            } else if (g.ease < 0.0f) {
                float sp = hypotf(g.vx, g.vy) + 1e-6f, ds = eased_dist(sp, g.ease, g.ease_min, t);
                bx = g.x + g.vx / sp * ds; by = g.y + g.vy / sp * ds;
            } else { bx = g.x + g.vx * t + 0.5f * g.ax * t * t; by = g.y + g.vy * t + 0.5f * g.ay * t * t; }
            float dx = x - bx, dy = y - by;
            if (g.hl > 0.0f) {   // a log: nearest point of its line
                float ux = cosf(g.ang), uy = sinf(g.ang);
                float k = fminf(fmaxf(dx * ux + dy * uy, -g.hl), g.hl);
                dx -= ux * k; dy -= uy * k;
            }
            float c = sqrtf(dx * dx + dy * dy) - g.r - PLAYER_R + slack;
            if (c < worst) worst = c;
        }
        if (er > 0.0f) {
            float dx = x - (ex + evx * t), dy = y - (ey + evy * t);
            float c = sqrtf(dx * dx + dy * dy) - er - PLAYER_R + slack;
            if (c < worst) worst = c;
        }
    }
    return worst;
}

int main(int argc, char** argv) {
    if (argc < 3) { printf("usage: battlecensus <enemy id> <seed> [seconds] [shot dir]\n"); return 1; }
    int   id    = atoi(argv[1]);
    unsigned seed = (unsigned)strtoul(argv[2], nullptr, 10);
    float fight = argc > 3 ? (float)atof(argv[3]) : 60.0f;
    const char* shots = argc > 4 ? argv[4] : nullptr;

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, ARENA_W, ARENA_H, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);

    Player player = {0};
    player.level = 1;
    player.stats.max_hp = player.stats.hp = 100000;
    // env WEAPON=type OIL=0-10 ECHO=0-2: the weapon in hand (only matters with FIRE).
    if (getenv("WEAPON")) player.equipped = (WeaponType)atoi(getenv("WEAPON"));
    player.arsenal[player.equipped].type = (WeaponType)player.equipped;
    if (getenv("OIL"))  player.arsenal[player.equipped].oil  = atoi(getenv("OIL"));
    if (getenv("ECHO")) player.arsenal[player.equipped].echo = atoi(getenv("ECHO"));   // never dies: count every hit
    Input in; input_init(&in);

    if (const char* lk = getenv("BOT_LOOK")) LOOKAHEAD = (float)atof(lk);
    g_ms = seed;   // the constructor seeds the enemy RNG from the clock
    BattleScene bs(&player, id);
    bs.draw(ren, nullptr);   // loads the sheet: sizes the enemy's hitbox as in play
    Enemy* en = bs._enemy;
    // Skip the fade in.
    while (bs._phase == BATTLE_PHASE_INTRO) { g_ms += 16; bs.update(&in, DT); }

    const float drain = en->max_hp / fight;
    float home_x = ARENA_W * 0.5f, home_y = ARENA_H - 80.0f;
    if (const char* hm = getenv("HOME_AT")) sscanf(hm, "%f,%f", &home_x, &home_y);   // where the bot drifts back to
    int hits = 0, peak = 0, cap_frames = 0, close_spawns = 0;
    float tight = 1e9f, tight_t = 0.0f, min_spawn = 1e9f;
    bool was_active[MAX_ENEMY_BULLETS] = {};
    float t = 0.0f;
    int frame = 0;
    float last_ex = en->x, last_ey = en->y;
    bool body_last = false;
    int swallowed = 0, flew_on = 0;
    bool fire_on = getenv("FIRE") != nullptr, catching = false, hold_on_catch = getenv("HOLD") != nullptr;
    int catches = 0, caught = 0, caught_now = 0;
    float perched_dmg = 0.0f, open_dmg = 0.0f;   // damage while catching / not (drain included)
    if (fire_on) in.keys[SDL_SCANCODE_Z] = KEY_HELD;
    float near_min = 1e9f; int near_passes = 0; bool was_near = false;   // enemy centre within 60 px
    int dashes = 0; float dash_t = 0.0f; bool was_fast = false;   // enemy moving >= 200 px/s   // boomerangs eaten / that left the arena   // a body hit counts once a touch, not once a frame
    float strafe_v = 0.0f, strafe_y = 400.0f, strafe_dir = 1.0f;
    float circ_v = 0.0f, circ_r = 100.0f, circ_x = 320.0f, circ_y = 360.0f, circ_a = 0.0f;
    if (const char* cv = getenv("CIRCLE")) sscanf(cv, "%f,%f,%f,%f", &circ_v, &circ_r, &circ_x, &circ_y);
    float bot_max = getenv("BOT_MAX") ? (float)atof(getenv("BOT_MAX")) : 1e9f;
    float chase_v = getenv("CHASE") ? (float)atof(getenv("CHASE")) : 0.0f;
    float hug = getenv("HUG") ? (float)atof(getenv("HUG")) : 0.0f;
    if (const char* sv = getenv("STRAFE")) sscanf(sv, "%f,%f", &strafe_v, &strafe_y);
    // A picture of the arena, the player a red cross: n > 0 the nth hit, n <= 0 a trace frame.
    // env TRACE=t0,t1 writes every 0.1 s between into the shot dir.
    float trace_from = 0, trace_to = -1;
    bool trace = shots && getenv("TRACE") && sscanf(getenv("TRACE"), "%f,%f", &trace_from, &trace_to) == 2;
    auto shot = [&](int n) {
        bs.draw(ren, nullptr);
        SDL_SetRenderDrawColor(ren, 255, 0, 0, 255);
        int px = (int)bs._bp.x, py = (int)bs._bp.y;
        SDL_RenderDrawLine(ren, px - 6, py, px + 6, py);
        SDL_RenderDrawLine(ren, px, py - 6, px, py + 6);
        // The enemy's hitbox, green, to hold against its art.
        SDL_SetRenderDrawColor(ren, 0, 255, 0, 255);
        for (int k = 0; k < 64; k++) {
            float a0 = k * 6.2831853f / 64, a1 = (k + 1) * 6.2831853f / 64;
            SDL_RenderDrawLine(ren, (int)(en->x + cosf(a0) * bs._hit_r), (int)(en->y + sinf(a0) * bs._hit_r),
                                    (int)(en->x + cosf(a1) * bs._hit_r), (int)(en->y + sinf(a1) * bs._hit_r));
        }
        char path[512];
        if (n > 0) snprintf(path, sizeof path, "%s/hit_%02d_%u_%d.png", shots, id, seed, n);
        else       snprintf(path, sizeof path, "%s/tr_%02d_%u_%05d.png", shots, id, seed, -n);
        IMG_SavePNG(surf, path);
    };
    while (en->is_alive() && t < fight * 1.5f) {
        // The bot's move.
        std::vector<Ghost> gs;
        for (const Bullet& b : bs._enemy_bullets) if (b.active)
            gs.push_back({ b.x, b.y, b.vx, b.vy, b.radius, b.delay, b.launch_speed, b.launch_off, b.half_len, b.ang,
                           b.ocx, b.ocy, b.orad, b.oang, b.ovr, b.ow,
                           b.min_speed > 0.0f ? 0.0f : b.ux * b.accel, b.min_speed > 0.0f ? 0.0f : b.uy * b.accel,
                           b.zig, b.zig_every, b.zig_t, b.zig_s,
                           b.min_speed > 0.0f && b.ow == 0.0f ? b.accel : 0.0f, b.min_speed });
        // Keep off the body always (a lunge starts without notice to a bot),
        // moving on at the speed it has now.
        float er = bs._hit_r;
        float evx = (en->x - last_ex) / DT, evy = (en->y - last_ey) / DT;
        last_ex = en->x; last_ey = en->y;
        // Fast moves (a dash, a flight, a fear bolt): how many, how long.
        bool fast = hypotf(evx, evy) >= 200.0f;
        if (fast && !was_fast) dashes++;
        if (fast) dash_t += DT;
        was_fast = fast;
        // How near the enemy itself comes: a run along the player's edge.
        float ed = hypotf(en->x - bs._bp.x, en->y - bs._bp.y);
        if (ed < near_min) near_min = ed;
        bool nr = ed < 60.0f;
        if (nr && !was_near) near_passes++;
        was_near = nr;
        float best = -1e9f, bmx = 0, bmy = 0, bsp = 0;
        static const float SPEEDS[3] = { 70.0f, 160.0f, 250.0f };
        for (int d = 0; d < 9; d++) for (int s = 0; s < 3; s++) {
            if (d == 8 && s > 0) continue;
            if (SPEEDS[s] > bot_max) continue;   // env BOT_MAX=70: a focus-only bot
            float mx = 0, my = 0;
            if (d < 8) { mx = cosf(d * 3.14159265f / 4); my = sinf(d * 3.14159265f / 4); }
            float sp = d == 8 ? 0.0f : SPEEDS[s];
            float c = fminf(clearance(gs, bs._bp.x, bs._bp.y, mx, my, sp, en->x, en->y, evx, evy, er), 24.0f);
            float nx = bs._bp.x + mx * sp * 0.1f, ny = bs._bp.y + my * sp * 0.1f;
            // Walls trap a dodger (an aimed stream follows it in): keep off them.
            float wall = fminf(fminf(nx - 16.0f, ARENA_W - 16.0f - nx), ARENA_H - 16.0f - ny);
            float score = c * 10.0f - hypotf(nx - home_x, ny - home_y) * 0.15f - sp * 0.002f
                        - (wall < 80.0f ? (80.0f - wall) * 1.0f : 0.0f);
            if (score > best) { best = score; bmx = mx; bmy = my; bsp = sp; }
        }
        // env STRAFE=speed,y: no dodging -- walk side to side along y between
        // x 40 and 600, the textbook answer to an aimed stream.
        if (strafe_v > 0.0f) {
            bmx = strafe_dir; bmy = 0.0f; bsp = strafe_v;
            if (bs._bp.y != strafe_y) bs._bp.y = strafe_y;
            if ((bs._bp.x > 600.0f && strafe_dir > 0) || (bs._bp.x < 40.0f && strafe_dir < 0)) strafe_dir = -strafe_dir;
        }
        // env CIRCLE=speed,radius,cx,cy: no dodging -- walk round a circle,
        // never back over a spot within a lap: the other answer to a stream.
        if (circ_v > 0.0f) {
            circ_a += circ_v / circ_r * DT;
            bs._bp.x = circ_x + cosf(circ_a) * circ_r; bs._bp.y = circ_y + sinf(circ_a) * circ_r;
            bsp = 0.0f;
        }
        // env HUG=dist: sit dist px below the enemy, wherever it goes -- is
        // hugging a free safe spot? (Teleports: a probe, not a player.)
        // env CHASE=speed: walk straight at the enemy (no dodging), stopping 40 px short.
        if (chase_v > 0.0f) {
            float dx = en->x - bs._bp.x, dy = en->y - bs._bp.y, d = hypotf(dx, dy);
            bmx = d > 40.0f ? dx / d : 0.0f; bmy = d > 40.0f ? dy / d : 0.0f; bsp = chase_v;
        }
        if (hug > 0.0f) { bs._bp.x = en->x; bs._bp.y = en->y + hug; bsp = 0.0f; }
        bs._bp.x = fminf(fmaxf(bs._bp.x + bmx * bsp * DT, 16.0f), ARENA_W - 16.0f);
        bs._bp.y = fminf(fmaxf(bs._bp.y + bmy * bsp * DT, ARENA_TOP + 16.0f), ARENA_H - 16.0f);

        // One frame of the fight, in update()'s order, without the player's
        // shots: the enemy bleeds evenly instead.
        g_ms = seed + (Uint32)(t * 1000.0f);
        en->take_damage(drain * DT);
        bs._update_enemy(DT);
        // New bullets this frame: how close to the player did they appear?
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
            const Bullet& b = bs._enemy_bullets[i];
            if (b.active && !was_active[i]) {
                float d = hypotf(b.x - bs._bp.x, b.y - bs._bp.y) - b.radius - b.half_len;
                if (d < min_spawn) min_spawn = d;
                if (d < 40.0f) {
                    close_spawns++;
                    if (close_spawns <= 5)
                        printf("  close spawn t=%.2f d=%.1f at (%.0f,%.0f) player (%.0f,%.0f) delay=%.2f\n",
                               t, d, b.x, b.y, bs._bp.x, bs._bp.y, b.delay);
                }
            }
        }
        bool boom[MAX_ENEMY_BULLETS];
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
            const Bullet& b = bs._enemy_bullets[i];
            boom[i] = b.active && b.accel != 0.0f && b.min_speed <= 0.0f && b.ow == 0.0f;
        }
        bs._move_bullets(DT);
        // Boomerangs: swallowed by the enemy, or flown on past it?
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) if (boom[i] && !bs._enemy_bullets[i].active) {
            const Bullet& b = bs._enemy_bullets[i];
            if (hypotf(b.x - en->x, b.y - en->y) < 30.0f) swallowed++; else flew_on++;
        }
        int act = 0;
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) { was_active[i] = bs._enemy_bullets[i].active; act += was_active[i]; }
        if (act > peak) peak = act;
        if (act >= MAX_ENEMY_BULLETS) cap_frames++;

        for (const Bullet& b : bs._enemy_bullets) if (b.active) {
            float nx = b.x, ny = b.y;
            if (b.half_len > 0.0f) {
                float ux = cosf(b.ang), uy = sinf(b.ang);
                float k = fminf(fmaxf((bs._bp.x - b.x) * ux + (bs._bp.y - b.y) * uy, -b.half_len), b.half_len);
                nx += ux * k; ny += uy * k;
            }
            float c = hypotf(nx - bs._bp.x, ny - bs._bp.y) - b.radius - PLAYER_R;
            if (c < tight) { tight = c; tight_t = t; }
        }
        // The shot about to land, if any: what kind it is.
        const Bullet* hitter = nullptr;
        for (const Bullet& b : bs._enemy_bullets) if (b.active) {
            float dx = bs._bp.x - b.x, dy = bs._bp.y - b.y, r = b.radius + PLAYER_R;
            if (b.half_len > 0.0f) {
                float ux = cosf(b.ang), uy = sinf(b.ang);
                float k = fminf(fmaxf(dx * ux + dy * uy, -b.half_len), b.half_len);
                dx -= ux * k; dy -= uy * k;
            }
            if (dx * dx + dy * dy < r * r) { hitter = &b; break; }
        }
        // env FIRE=1: the player holds fire (auto-aimed, as in play). Shots
        // the enemy catches (catch_radius) are counted, per catch window.
        // env HOLD=1: a player who stops firing while the enemy catches.
        if (fire_on && !(hold_on_catch && en->catch_radius() > 0.0f)) bs._update_player_fire(&in, DT);
        float cr = en->catch_radius();
        int pre = 0;
        if (cr > 0.0f) for (const Bullet& b : bs._player_bullets)
            if (b.active && hypotf(b.x - en->x, b.y - en->y) < cr) pre++;
        if (cr > 0.0f && !catching) { catching = true; catches++; }
        if (cr <= 0.0f && catching) { catching = false; printf("  catch %d: %d shots\n", catches, caught_now); caught_now = 0; }
        float ehp0 = en->hp;
        float hp0 = bs._bp.hp;
        bs._check_collisions();
        if (cr > 0.0f) perched_dmg += ehp0 - en->hp; else open_dmg += ehp0 - en->hp;
        if (cr > 0.0f) {
            int post = 0;
            for (const Bullet& b : bs._player_bullets)
                if (b.active && hypotf(b.x - en->x, b.y - en->y) < cr) post++;
            caught_now += pre - post; caught += pre - post;
        }
        if (bs._bp.hp < hp0) {
            bool body = !hitter;
            if (!(body && body_last)) hits++;
            body_last = body;
            printf("  HIT t=%.2f enemy hp %.0f%% player (%.0f,%.0f) enemy (%.0f,%.0f) bullets %d"
                   " | shot r%.1f speed %.0f age %.2f%s\n",
                   t, 100.0f * en->hp / en->max_hp, bs._bp.x, bs._bp.y, en->x, en->y, act,
                   hitter ? hitter->radius : 0.0f, hitter ? hypotf(hitter->vx, hitter->vy) : 0.0f,
                   hitter ? hitter->age : 0.0f,
                   !hitter ? " BODY" : hitter->half_len > 0 ? " log" : hitter->launch_speed > 0 ? " mine" : "");
            if (shots && hits <= 4) shot(hits);
        }
        if (trace && t >= trace_from && t <= trace_to && frame % 6 == 0) shot(-frame);
        bs._bp.iframes = 0.0f;   // count every hit, not one per 1.5 s
        // update()'s own timers, which this loop stands in for.
        if (bs._enemy_flash > 0.0f) bs._enemy_flash -= DT;
        if (bs._flash_gap   > 0.0f) bs._flash_gap   -= DT;
        if (bs._pierce_wait > 0.0f) bs._pierce_wait -= DT;
        t += DT; frame++;
    }
    printf("enemy %d %s seed %u: %.1fs, hits %d, peak bullets %d/%d, frames at cap %d, "
           "spawns <40px %d (closest %.1f), tightest pass %.1fpx at t=%.2f\n",
           id, en->name(), seed, t, hits, peak, MAX_ENEMY_BULLETS, cap_frames,
           close_spawns, min_spawn, tight, tight_t);
    printf("  enemy nearest %.0f px, passes within 60 px: %d\n", near_min, near_passes);
    if (catches) printf("  damage while catching %.0f, otherwise %.0f\n", perched_dmg, open_dmg);
    if (catches) printf("  catch windows %d, shots caught %d\n", catches, caught);
    if (dashes) printf("  enemy fast moves (>=200 px/s): %d, %.1f s in all\n", dashes, dash_t);
    if (swallowed + flew_on) printf("  boomerangs: %d swallowed, %d flew on\n", swallowed, flew_on);
    return 0;
}
