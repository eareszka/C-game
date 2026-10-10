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
               float ease, ease_min;
               bool bounce;
               float ocvx, ocvy, oease, omin; };   // orbit centre drift; outward-speed easing   // ricochets off the arena walls (folded, ignoring its bounce count)   // easing: speed falls at ease px/s^2 to ease_min   // zigzag: swings 2*zig every zig_every   // a boomerang's pull (accel without min_speed)   // ow != 0: spirals out from (ocx, ocy)

// Telegraph lines this frame, as the bot sees them: each one's whole line
// (it grows to the arena edge), dangerous now or soon -- a laser that hurts.
struct Hazard { float x, y, ux, uy, w, len = 0.0f, spin = 0.0f, vx = 0.0f, vy = 0.0f; };   // vx, vy: the origin's drift   // len 0: the whole line; else a segment from (x, y); spin: rad/s it turns about (x, y)
static std::vector<Hazard> g_lines;
static float g_spin_horizon = 1e9f;
static float g_pullx = 0.0f, g_pully = 0.0f;   // px/s the enemy's pull moves the player   // seconds a sweep is trusted to keep turning

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
        float x = fminf(fmaxf(px + (mx * speed + g_pullx) * t, 16.0f), ARENA_W - 16.0f);   // g_pull: the enemy drawing the player in
        float y = fminf(fmaxf(py + (my * speed + g_pully) * t, ARENA_TOP + 16.0f), ARENA_H - 16.0f);
        // Weight the near future more: a close shave 0.5 s out can still be fixed.
        float slack = t * 6.0f;
        for (const Ghost& g : gs) {
            float bx, by;
            if (g.delay > t && g.ow != 0.0f) {   // an orbiting mine keeps turning while it waits
                float rr = g.orad + (g.oease < 0.0f ? eased_dist(g.ovr, g.oease, g.omin, t) : g.ovr * t), aa = g.oang + g.ow * t;
                bx = g.ocx + g.ocvx * t + cosf(aa) * rr; by = g.ocy + g.ocvy * t + sinf(aa) * rr;
            } else if (g.delay > t) { bx = g.x; by = g.y; }
            else if (g.delay > 0.0f) {
                float lx = fminf(fmaxf(px + mx * speed * g.delay, 16.0f), ARENA_W - 16.0f);
                float ly = fminf(fmaxf(py + my * speed * g.delay, ARENA_TOP + 16.0f), ARENA_H - 16.0f);
                float a = atan2f(ly - g.y, lx - g.x) + g.off, s = t - g.delay;
                bx = g.x + cosf(a) * g.launch * s; by = g.y + sinf(a) * g.launch * s;
            } else if (g.ow != 0.0f) {
                float rr = g.orad + (g.oease < 0.0f ? eased_dist(g.ovr, g.oease, g.omin, t) : g.ovr * t), aa = g.oang + g.ow * t;
                bx = g.ocx + g.ocvx * t + cosf(aa) * rr; by = g.ocy + g.ocvy * t + sinf(aa) * rr;
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
            if (g.bounce) {   // fold back into the arena, as walls reflect it
                auto fold = [](float v, float lo, float hi) {
                    float span = hi - lo, m = fmodf(v - lo, 2.0f * span);
                    if (m < 0.0f) m += 2.0f * span;
                    return lo + (m <= span ? m : 2.0f * span - m);
                };
                bx = fold(bx, g.r, ARENA_W - g.r);
                by = fold(by, ARENA_TOP + g.r, ARENA_H - g.r);
            }
            float dx = x - bx, dy = y - by;
            if (g.hl > 0.0f) {   // a log: nearest point of its line
                float ux = cosf(g.ang), uy = sinf(g.ang);
                float k = fminf(fmaxf(dx * ux + dy * uy, -g.hl), g.hl);
                dx -= ux * k; dy -= uy * k;
            }
            float c = sqrtf(dx * dx + dy * dy) - g.r - PLAYER_R + slack;
            if (c < worst) worst = c;
        }
        for (const Hazard& h : g_lines) {
            float dx = x - (h.x + h.vx * t), dy = y - (h.y + h.vy * t), c, ux = h.ux, uy = h.uy;
            if (h.spin != 0.0f) {   // a sweeping beam: where it will point by t
                float a = atan2f(uy, ux) + h.spin * fminf(t, g_spin_horizon);   // env SPIN_HORIZON: a sweep that stops
                ux = cosf(a); uy = sinf(a);
            }
            if (h.len > 0.0f) {   // a segment (or a ray: a long one): distance to its nearest point
                float k = fminf(fmaxf(dx * ux + dy * uy, 0.0f), h.len);
                c = hypotf(dx - ux * k, dy - uy * k) - h.w - PLAYER_R + slack;
            } else c = fabsf(dx * uy - dy * ux) - h.w - PLAYER_R + slack;
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

    if (getenv("SPIN_HORIZON")) g_spin_horizon = (float)atof(getenv("SPIN_HORIZON"));
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
    bool boxcheck = getenv("BOXCHECK") != nullptr;
    int min_open = 72, boxed_frames = 0, max_static = 0; float min_open_t = 0.0f;
    static float out_t[MAX_ENEMY_BULLETS]; float out_max = 0.0f;   // seconds a shot has sat outside the arena
    float last_door = -1.0f; std::vector<float> door_moves;   // wall doors, and how far each moved
    bool fire_on = getenv("FIRE") != nullptr, catching = false, hold_on_catch = getenv("HOLD") != nullptr;
    int catches = 0, caught = 0, caught_now = 0;
    float perched_dmg = 0.0f, open_dmg = 0.0f;   // damage while catching / not (drain included)
    if (fire_on) in.keys[SDL_SCANCODE_Z] = KEY_HELD;
    float near_min = 1e9f; int near_passes = 0; bool was_near = false;   // enemy centre within 60 px
    int dashes = 0; float dash_t = 0.0f; bool was_fast = false;   // enemy moving >= 200 px/s   // boomerangs eaten / that left the arena   // a body hit counts once a touch, not once a frame
    int last_dir = 99;
    bool bisector = getenv("BISECTOR") != nullptr, bis_on = false; float bis_x = 0, bis_y = 0;
    bool pose_tell = getenv("POSE_TELL") != nullptr; int last_af = -1; float tell_x = 0, tell_y = 0, tell_ax = 0, tell_ay = 0;
    std::vector<float> prev_ang, prev_ox, prev_oy;   // each telegraph line's angle last frame (99: none), for sweeps   // the bot's held direction last frame, for facing
    float strafe_v = 0.0f, strafe_y = 400.0f, strafe_dir = 1.0f;
    float circ_v = 0.0f, circ_r = 100.0f, circ_x = 320.0f, circ_y = 360.0f, circ_a = 0.0f;
    if (const char* cv = getenv("CIRCLE")) sscanf(cv, "%f,%f,%f,%f", &circ_v, &circ_r, &circ_x, &circ_y);
    float bot_max = getenv("BOT_MAX") ? (float)atof(getenv("BOT_MAX")) : 1e9f;
    float seek = getenv("SEEK") ? (float)atof(getenv("SEEK")) : 0.0f;
    float chase_v = getenv("CHASE") ? (float)atof(getenv("CHASE")) : 0.0f;
    float hug = getenv("HUG") ? (float)atof(getenv("HUG")) : 0.0f;
    // env STILL=x,y: a player who stands there and never moves -- is it a safe spot?
    float still_x = 0.0f, still_y = 0.0f;
    bool  still = getenv("STILL") && sscanf(getenv("STILL"), "%f,%f", &still_x, &still_y) == 2;
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
    // env STOP_HP=0.5: end the run when the enemy falls to that share of its HP (phase 1 alone).
    float stop_hp = getenv("STOP_HP") ? (float)atof(getenv("STOP_HP")) : 0.0f;
    while (en->is_alive() && t < fight * 1.5f && en->hp > en->max_hp * stop_hp) {
        // env SEEK=d: home is d px below the enemy (inside a ghost's sight, to aim).
        if (seek > 0.0f) { home_x = en->x; home_y = fminf(en->y + seek, ARENA_H - 30.0f); }
        // The bot's move.
        std::vector<Ghost> gs;
        for (const Bullet& b : bs._enemy_bullets) if (b.active)
            gs.push_back({ b.x, b.y, b.vx, b.vy, b.radius, b.delay, b.launch_speed, b.launch_off, b.half_len, b.ang,
                           b.ocx, b.ocy, b.orad, b.oang, b.ovr, b.ow,
                           b.min_speed > 0.0f ? 0.0f : b.ux * b.accel, b.min_speed > 0.0f ? 0.0f : b.uy * b.accel,
                           b.zig, b.zig_every, b.zig_t, b.zig_s,
                           b.min_speed > 0.0f && b.ow == 0.0f ? b.accel : 0.0f, b.min_speed, b.bouncing,
                           b.ocvx, b.ocvy, b.ow != 0.0f && b.min_speed > 0.0f ? b.accel : 0.0f, b.min_speed });
        // Keep off the body always (a lunge starts without notice to a bot),
        // moving on at the speed it has now.
        float er = bs._hit_r;
        g_lines.clear();
        {
            Enemy::TeleLine tl[64];
            int nt = en->telegraphs(tl, 64);
            for (int k = 0; k < nt; k++) {
                float dx = tl[k].x1 - tl[k].x0, dy = tl[k].y1 - tl[k].y0, L = hypotf(dx, dy);
                // A big glowing ball is the water heaving where something will
                // rise (88's amixsak): a disc to keep well clear of.
                if (tl[k].orb >= 20.0f && tl[k].stage == 0) { g_lines.push_back({ tl[k].x0, tl[k].y0, 1.0f, 0.0f, tl[k].orb + 60.0f, 0.001f }); continue; }
                if (tl[k].orb > 0.0f) continue;   // a lit ball (78's sun's heart) is harmless: its rays are the hazard
                if (L < 1.0f) continue;   // just starting: no direction yet
                // A line that doesn't hurt is only a hazard while it is still
                // growing (stage 0: a laser about to fire). Harmless markers
                // (Bes Rap's X) and fading tails are ignored.
                // A mark from the enemy's own body is a run it is about to make:
                // its whole body sweeps that segment.
                if (tl[k].hurt_w <= 0.0f && tl[k].stage != 0
                    && hypotf(tl[k].x0 - en->x, tl[k].y0 - en->y) < 12.0f && en->contact_damage() >= 0.0f) {
                    g_lines.push_back({ tl[k].x0, tl[k].y0, dx / L, dy / L, bs._hit_r, L });
                    continue;
                }
                if (tl[k].hurt_w <= 0.0f && tl[k].stage != 0) continue;
                // A beam is a ray from its origin; one that turns between
                // frames (a sweep) is predicted to keep turning.
                float a = atan2f(dy, dx), spin = 0.0f, ovx = 0.0f, ovy = 0.0f;
                if (k < (int)prev_ang.size() && prev_ang[k] < 50.0f) {
                    float da = remainderf(a - prev_ang[k], 6.2831853f);
                    if (fabsf(da) < 0.1f) spin = da / DT;
                    float mx = (tl[k].x0 - prev_ox[k]) / DT, my = (tl[k].y0 - prev_oy[k]) / DT;
                    if (hypotf(mx, my) < 600.0f) { ovx = mx; ovy = my; }   // a moving origin (a falling sun)
                }
                // A harmless line whirling fast is a decoy still settling (78's
                // whirl): only once it slows is it a warning worth dodging.
                if (tl[k].hurt_w <= 0.0f && fabsf(spin) > 1.0f) continue;
                // Growing (stage 0): the whole ray ahead; once grown, the segment itself.
                g_lines.push_back({ tl[k].x0, tl[k].y0, dx / L, dy / L, fmaxf(tl[k].hurt_w, 4.0f),
                                    tl[k].stage == 0 ? 2000.0f : L, spin, ovx, ovy });
            }
        }
        {
            Enemy::TeleLine tl[64];
            int nt = en->telegraphs(tl, 64);
            prev_ang.assign(64, 99.0f); prev_ox.assign(64, 0.0f); prev_oy.assign(64, 0.0f);
            for (int k = 0; k < nt; k++) {
                if (hypotf(tl[k].x1 - tl[k].x0, tl[k].y1 - tl[k].y0) >= 1.0f)
                    prev_ang[k] = atan2f(tl[k].y1 - tl[k].y0, tl[k].x1 - tl[k].x0);
                prev_ox[k] = tl[k].x0; prev_oy[k] = tl[k].y0;
            }
        }
        // A drawn-back pose (anim_frame 1) is a lunge aimed where the player
        // stands as it starts: env POSE_TELL=1 makes the bot read it like a
        // player would, as the body's path to the wall along that line.
        if (pose_tell) {
            int af = en->anim_frame();
            if (af == 1 && last_af != 1) { tell_x = en->x; tell_y = en->y; tell_ax = bs._bp.x; tell_ay = bs._bp.y; }
            if (af == 1 || af == 2) {
                float dx = tell_ax - tell_x, dy = tell_ay - tell_y, L = hypotf(dx, dy);
                if (L > 1.0f) g_lines.push_back({ tell_x, tell_y, dx / L, dy / L, bs._hit_r, 2000.0f });
            }
            last_af = af;
        }
        // env BISECTOR=1: a player who reads closing shears -- two beams from
        // nearby origins turning toward each other -- heads for the line
        // between them (where they will stop), at the distance they stand.
        bis_on = false;
        if (bisector) {
            for (size_t i = 0; i < g_lines.size() && !bis_on; i++)
                for (size_t j = i + 1; j < g_lines.size() && !bis_on; j++) {
                    const Hazard &a = g_lines[i], &b = g_lines[j];
                    if (a.spin * b.spin > 0.0f || hypotf(a.x - b.x, a.y - b.y) > 90.0f) continue;   // still (growing) or closing
                    float mx = 0.5f * (a.x + b.x), my = 0.5f * (a.y + b.y);
                    float bx = a.ux + b.ux, by = a.uy + b.uy, bl = hypotf(bx, by);
                    if (bl < 0.05f) continue;
                    float d = hypotf(bs._bp.x - mx, bs._bp.y - my);
                    bis_x = mx + bx / bl * d; bis_y = my + by / bl * d; bis_on = true;
                }
        }
        {
            float pdx = en->x - bs._bp.x, pdy = en->y - bs._bp.y, pd = hypotf(pdx, pdy), pl = en->pull();
            g_pullx = pd > 1.0f ? pdx / pd * pl : 0.0f; g_pully = pd > 1.0f ? pdy / pd * pl : 0.0f;
        }
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
            float hx = bis_on ? bis_x : home_x, hy = bis_on ? bis_y : home_y, hw = bis_on ? 1.0f : 0.15f;
            float score = c * 10.0f - hypotf(nx - hx, ny - hy) * hw - sp * 0.002f
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
        if (still) { bs._bp.x = still_x; bs._bp.y = still_y; bsp = 0.0f; }
        // Facing as the map keys set it (player_read_input): a new direction
        // is a new key press, which unlocks facing; unlocked, it follows the
        // movement. The battle locks it toward the enemy while it is visible.
        {
            int dir = bsp > 0.0f ? (int)lroundf(atan2f(bmy, bmx) / (3.14159265f / 4)) : 99;
            if (dir != last_dir && dir != 99) player.facing_locked = 0;
            last_dir = dir;
            if (!player.facing_locked && bsp > 0.0f) player.facing = facing_from(bmx, bmy);
        }
        bs._bp.x = fminf(fmaxf(bs._bp.x + bmx * bsp * DT, 16.0f), ARENA_W - 16.0f);
        bs._bp.y = fminf(fmaxf(bs._bp.y + bmy * bsp * DT, ARENA_TOP + 16.0f), ARENA_H - 16.0f);

        // One frame of the fight, in update()'s order, without the player's
        // shots: the enemy bleeds evenly instead.
        g_ms = seed + (Uint32)(t * 1000.0f);
        en->take_damage(drain * DT);
        bs._update_enemy(DT);
        // A wall row (30+ shots born together along the top): where is its door?
        {
            std::vector<float> xs;
            for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
                const Bullet& b = bs._enemy_bullets[i];
                if (b.active && !was_active[i] && b.y < ARENA_TOP + 8.0f) xs.push_back(b.x);
            }
            if (xs.size() >= 30) {
                std::sort(xs.begin(), xs.end());
                float best = 0.0f, door = 0.0f;
                for (size_t k = 1; k < xs.size(); k++)
                    if (xs[k] - xs[k - 1] > best) { best = xs[k] - xs[k - 1]; door = 0.5f * (xs[k] + xs[k - 1]); }
                if (xs.front() > best) { best = xs.front(); door = xs.front() * 0.5f; }
                if (ARENA_W - xs.back() > best) { best = ARENA_W - xs.back(); door = 0.5f * (xs.back() + ARENA_W); }
                if (getenv("DOORS")) printf("  wall t=%.2f door x=%.0f gap %.0f%s\n", t, door, best,
                                            last_door >= 0.0f ? "" : " (first)");
                if (last_door >= 0.0f) door_moves.push_back(fabsf(door - last_door));
                last_door = door;
            }
        }
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
        // Shots outside the arena (beyond 20 px): how long does any one linger there?
        for (int i = 0; i < MAX_ENEMY_BULLETS; i++) {
            const Bullet& b = bs._enemy_bullets[i];
            bool out = b.active && (b.x < -20.0f || b.x > ARENA_W + 20.0f || b.y < ARENA_TOP - 20.0f || b.y > ARENA_H + 20.0f);
            out_t[i] = out ? out_t[i] + DT : 0.0f;
            if (out_t[i] > out_max) out_max = out_t[i];
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
        if (fire_on && !(hold_on_catch && (en->catch_radius() > 0.0f || en->alt_pose()))) bs._update_player_fire(&in, DT);
        float cr = en->catch_radius();
        int pre = 0;
        if (cr > 0.0f) for (const Bullet& b : bs._player_bullets)
            if (b.active && hypotf(b.x - en->x, b.y - en->y) < cr) pre++;
        if (cr > 0.0f && !catching) { catching = true; catches++; }
        if (cr <= 0.0f && catching) { catching = false; printf("  catch %d: %d shots\n", catches, caught_now); caught_now = 0; }
        float ehp0 = en->hp;
        bool laser = false;
        if (!hitter) {
            Enemy::TeleLine tl[64];
            int nt = en->telegraphs(tl, 64);
            for (int k = 0; k < nt && !laser; k++) if (tl[k].hurt_w > 0.0f) {
                float dx = tl[k].x1 - tl[k].x0, dy = tl[k].y1 - tl[k].y0, L2 = dx * dx + dy * dy;
                float u = L2 > 0.0f ? fminf(fmaxf(((bs._bp.x - tl[k].x0) * dx + (bs._bp.y - tl[k].y0) * dy) / L2, 0.0f), 1.0f) : 0.0f;
                laser = hypotf(bs._bp.x - tl[k].x0 - u * dx, bs._bp.y - tl[k].y0 - u * dy) < tl[k].hurt_w + PLAYER_R;
            }
        }
        // env BOXCHECK=1: is the player walled in by stationary shots (speed < 1)?
        // Cast 72 rays to 200 px; a ray is open if it gets there without
        // touching one (or the arena edge stops it after 100 px clear).
        if (boxcheck) {
            std::vector<const Bullet*> st;
            for (const Bullet& b : bs._enemy_bullets)
                if (b.active && b.delay <= 0.0f && hypotf(b.vx, b.vy) < 1.0f
                    && hypotf(b.x - bs._bp.x, b.y - bs._bp.y) < 220.0f) st.push_back(&b);
            int open = 0;
            for (int r = 0; r < 72; r++) {
                float ux = cosf(r * 6.2831853f / 72), uy = sinf(r * 6.2831853f / 72);
                bool ok = true;
                for (float d = 4.0f; d <= 200.0f && ok; d += 4.0f) {
                    float x = bs._bp.x + ux * d, y = bs._bp.y + uy * d;
                    if (x < 16 || x > ARENA_W - 16 || y < ARENA_TOP + 16 || y > ARENA_H - 16) { ok = d > 100.0f; break; }
                    for (const Bullet* b : st)
                        if (hypotf(b->x - x, b->y - y) < b->radius + PLAYER_R + 1.0f) { ok = false; break; }
                }
                open += ok;
            }
            if (open < min_open) { min_open = open; min_open_t = t; }
            if (open == 0) boxed_frames++;
            if ((int)st.size() > max_static) max_static = (int)st.size();
        }
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
            bool body = !hitter;   // a laser counts like a body: once a touch
            if (!(body && body_last)) hits++;
            body_last = body;
            printf("  HIT t=%.2f enemy hp %.0f%% player (%.0f,%.0f) enemy (%.0f,%.0f) bullets %d"
                   " | shot r%.1f speed %.0f age %.2f%s\n",
                   t, 100.0f * en->hp / en->max_hp, bs._bp.x, bs._bp.y, en->x, en->y, act,
                   hitter ? hitter->radius : 0.0f, hitter ? hypotf(hitter->vx, hitter->vy) : 0.0f,
                   hitter ? hitter->age : 0.0f,
                   !hitter ? (laser ? " LASER" : " BODY") : hitter->half_len > 0 ? " log" : hitter->launch_speed > 0 ? " mine" : "");
            if (shots && hits <= 4) shot(hits);
        }
        // env TELE_LOG=1: each frame's telegraph lines (H/V, stage, fade, length).
        if (getenv("TELE_LOG")) {
            Enemy::TeleLine tl[64];
            int nt = en->telegraphs(tl, 64);
            for (int k = 0; k < nt; k++)
            {
                float dx = tl[k].x1 - tl[k].x0, dy = tl[k].y1 - tl[k].y0, L = hypotf(dx, dy);
                // pd: the player's distance across the line's whole extent (-1 before it has a direction)
                float pd = L > 0.5f ? fabsf((bs._bp.x - tl[k].x0) * dy - (bs._bp.y - tl[k].y0) * dx) / L : -1.0f;
                printf("  tele f=%d %c stage %d fade %.2f len %.0f pd %.1f from %.0f,%.0f to %.0f,%.0f\n", frame,
                       tl[k].y0 == tl[k].y1 ? 'H' : 'V', tl[k].stage, tl[k].fade, L, pd,
                       tl[k].x0, tl[k].y0, tl[k].x1, tl[k].y1);
            }
        }
        // env SHOT_FRAMES=frame:name,...: save those frames as <shot dir>/<name>.png.
        if (shots && getenv("SHOT_FRAMES")) {
            char key[32]; snprintf(key, sizeof key, "%d:", frame);
            const char* sf = getenv("SHOT_FRAMES");
            for (const char* q = strstr(sf, key); q; q = strstr(q + 1, key))
                if (q == sf || q[-1] == ',') {
                    char name[128] = {}; sscanf(q + strlen(key), "%127[^,]", name);
                    bs.draw(ren, nullptr);
                    char path[512]; snprintf(path, sizeof path, "%s/%s.png", shots, name);
                    IMG_SavePNG(surf, path);
                    break;
                }
        }
        // env CENSUS_AT=frame: what the live shots are, that frame.
        if (getenv("CENSUS_AT") && frame == atoi(getenv("CENSUS_AT"))) {
            int in = 0, out = 0, mines = 0, orbit = 0, homing = 0, still = 0;
            for (const Bullet& b : bs._enemy_bullets) if (b.active) {
                bool inside = b.x >= 0 && b.x <= ARENA_W && b.y >= ARENA_TOP && b.y <= ARENA_H;
                inside ? in++ : out++;
                if (b.delay > 0.0f) mines++;
                if (b.ow != 0.0f) orbit++;
                if (b.homing) homing++;
                if (hypotf(b.vx, b.vy) < 1.0f && b.delay <= 0.0f) still++;
            }
            printf("  census f=%d: inside %d outside %d mines %d orbiting %d homing %d still(not mines) %d\n",
                   frame, in, out, mines, orbit, homing, still);
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
    if (!door_moves.empty()) {
        std::sort(door_moves.begin(), door_moves.end());
        printf("  walls %zu, door moves px: min %.0f median %.0f p90 %.0f max %.0f\n", door_moves.size() + 1,
               door_moves.front(), door_moves[door_moves.size() / 2], door_moves[door_moves.size() * 9 / 10], door_moves.back());
    }
    if (out_max > 0.0f) printf("  longest stay outside the arena: %.2f s\n", out_max);
    if (boxcheck) printf("  boxcheck: fewest open directions %d/72 at t=%.2f, frames fully boxed %d, most stationary shots near %d\n",
                         min_open, min_open_t, boxed_frames, max_static);
    if (catches) printf("  damage while catching %.0f, otherwise %.0f\n", perched_dmg, open_dmg);
    if (catches) printf("  catch windows %d, shots caught %d\n", catches, caught);
    if (dashes) printf("  enemy fast moves (>=200 px/s): %d, %.1f s in all\n", dashes, dash_t);
    if (swallowed + flew_on) printf("  boomerangs: %d swallowed, %d flew on\n", swallowed, flew_on);
    return 0;
}
