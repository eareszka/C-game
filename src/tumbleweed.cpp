#include "tumbleweed.h"
#include "crafting.h"     // ITEM_WOOD
#include "fc_palette.h"
#include <math.h>
#include <stdlib.h>

// The ball on the sheet: the tumbleweed prop's eight frames (props.py), col
// 13 of row 226, a cell each, one turn rolling right. Its ground line is art
// row 14 of the cell, its middle column 8; the ball is ~5 art pixels round.
static const int SHEET_COL = 13, SHEET_ROW = 226, CELL = 16, FRAMES = 8;
static const float ART = TILE_SIZE / 16.0f;            // world pixels an art pixel
static const float FOOT_ROW = 14.0f, MID_COL = 8.0f;
static const float BALL_R = 5.0f * ART;                // the ball's middle above its ground point
static const float TURN = 3.14159265f * 2.0f * BALL_R / FRAMES;   // ground rolled a frame

static const float GRAVITY  = 900.0f;    // px/s/s
static const float HOP_LO   = 160.0f, HOP_HI = 260.0f;     // a landing's bounce, px/s up: 14-37 px high
static const float BIG_HOP  = 380.0f;                      // over a prop, or now and then: ~80 px
static const float CLEAR_Z  = 20.0f;     // this high, it sails over a prop
static const float SPAWN_T_LO = 4.0f, SPAWN_T_HI = 10.0f;
static const float LIFE     = 40.0f;

static Tumbleweed s_weeds[TUMBLE_MAX];
static float s_spawn_t = 2.0f;
struct Burst { float x, y, t; };
static Burst s_bursts[TUMBLE_MAX];

static float frand(float a, float b) { return a + (b - a) * (rand() % 10000) / 9999.0f; }

void tumble_wind(double t, float* dx, float* dy, float* strength) {
    const double TAU = 6.283185307179586;
    // Round the compass about once a day and a half, squashed toward the
    // sideways (the film shot), with a slower wobble on top.
    double a = t * TAU / 1380.0 + 0.4 * sin(t * TAU / 600.0);
    float x = (float)cos(a), y = 0.55f * (float)sin(a);
    float l = sqrtf(x * x + y * y);
    *dx = x / l; *dy = y / l;
    *strength = 1.0f + 0.3f * (float)(sin(t * TAU / 7.0) * sin(t * TAU / 11.3));
}

void tumble_clear(void) {
    for (Tumbleweed& w : s_weeds) w.live = false;
    for (Burst& b : s_bursts) b.t = -1.0f;
    s_spawn_t = 2.0f;
}

Tumbleweed* tumble_spawn_at(float x, float y) {
    for (Tumbleweed& w : s_weeds) {
        if (w.live) continue;
        w = {};
        w.live = true;
        w.x = wrap_px(x); w.y = wrap_py(y);
        w.z = frand(0.0f, 12.0f);
        w.vz = frand(HOP_LO, HOP_HI);
        w.speed = frand(90.0f, 140.0f);
        w.face = 1;
        return &w;
    }
    return nullptr;
}

const Tumbleweed* tumble_list(void) { return s_weeds; }

int tumble_frame(const Tumbleweed& t) {
    int f = (int)(t.rolled / TURN) % FRAMES;
    return t.face > 0 ? f : (FRAMES - f) % FRAMES;
}

// The ground ahead, at the ground point (x, y) and either side of it across
// the way it goes: 0 open, 1 something low to hop, 2 shut.
static int ground_at(const Tilemap* map, float x, float y, float ux, float uy) {
    int worst = 0;
    for (int s = -1; s <= 1; s++) {
        float qx = x - uy * s * 6.0f, qy = y + ux * s * 6.0f;
        if (!tilemap_pixel_solid(map, qx, qy)) continue;
        int k = tilemap_low_obstacle(map, qx, qy) ? 1 : 2;
        if (k > worst) worst = k;
    }
    return worst;
}

static void step(Tumbleweed& w, const Tilemap* map, float wx, float wy, float strength, float dt) {
    w.age += dt;
    // The wind takes it: its pace eases toward the wind's, so a glance off a
    // cliff is shrugged off in a second or so.
    float tx = wx * w.speed * strength, ty = wy * w.speed * strength;
    float ease = fminf(1.0f, 2.0f * dt);
    w.vx += (tx - w.vx) * ease;
    w.vy += (ty - w.vy) * ease;

    // Up and down: a hop, the fall, a bounce -- now and then a moment's roll
    // along the sand between.
    if (w.z > 0.0f || w.vz > 0.0f) {
        w.vz -= GRAVITY * dt;
        w.z += w.vz * dt;
        if (w.z <= 0.0f) {
            w.z = 0.0f;
            w.hops++;
            if (rand() % 10 < 3) { w.vz = 0.0f; w.rest = frand(0.2f, 0.6f); }
            else if (rand() % 6 == 0) { w.vz = BIG_HOP * frand(0.9f, 1.05f); w.big_hops++; }
            else w.vz = frand(HOP_LO, HOP_HI);
        }
    } else if ((w.rest -= dt) <= 0.0f) {
        w.vz = frand(HOP_LO, HOP_HI);
    }

    float sp = sqrtf(w.vx * w.vx + w.vy * w.vy);
    if (sp < 1.0f) return;
    float ux = w.vx / sp, uy = w.vy / sp;
    float nx = w.x + w.vx * dt, ny = w.y + w.vy * dt;
    int g = ground_at(map, nx + ux * 8.0f, ny + uy * 8.0f, ux, uy);
    if (g == 1 && w.z < CLEAR_Z && w.vz < BIG_HOP * 0.5f) {   // a prop in the way: over it
        w.vz = BIG_HOP;
        w.rest = 0.0f;
        w.big_hops++;
    } else if (g == 2) {
        // Shut: glance off. Whichever way along it is open, slide that way,
        // the other way thrown back and damped.
        bool open_x = ground_at(map, nx + ux * 8.0f, w.y, ux, 0.0f) != 2;
        bool open_y = ground_at(map, w.x, ny + uy * 8.0f, 0.0f, uy) != 2;
        w.deflects++;
        if (open_x && !open_y)      { w.vy *= -0.4f; ny = w.y; }
        else if (open_y && !open_x) { w.vx *= -0.4f; nx = w.x; }
        else                        { w.vx *= -0.5f; w.vy *= -0.5f; nx = w.x; ny = w.y; }
    }
    // Never onto shut ground itself, whatever the look ahead missed (a corner
    // of a smoothed shore between its three points): it holds there instead.
    if (tilemap_pixel_solid(map, nx, ny) && !tilemap_low_obstacle(map, nx, ny)) { nx = w.x; ny = w.y; }
    float moved = sqrtf((nx - w.x) * (nx - w.x) + (ny - w.y) * (ny - w.y));
    w.rolled += moved;
    if (fabsf(w.vx) > 4.0f) w.face = w.vx > 0 ? 1 : -1;
    w.x = wrap_px(nx);
    w.y = wrap_py(ny);
}

void tumble_step(Tumbleweed* t, const Tilemap* map, double world_seconds, float dt) {
    float wx, wy, strength;
    tumble_wind(world_seconds, &wx, &wy, &strength);
    step(*t, map, wx, wy, strength, dt);
}

void tumble_tick(const Tilemap* map, const Camera* cam, float px, float py, double world_seconds, float dt) {
    float wx, wy, strength;
    tumble_wind(world_seconds, &wx, &wy, &strength);
    float vw = cam->screen_w / cam->zoom, vh = cam->screen_h / cam->zoom;
    float reach = fabsf(wx) * vw * 0.5f + fabsf(wy) * vh * 0.5f;   // the view's half, along the wind

    for (Tumbleweed& w : s_weeds) {
        if (!w.live) continue;
        step(w, map, wx, wy, strength, dt);
        float dx = wrap_dpx(w.x - px), dy = wrap_dpy(w.y - py);
        float along = dx * wx + dy * wy;
        if (w.age > LIFE || along > reach + 80.0f || fabsf(dx) > vw * 1.5f || fabsf(dy) > vh * 1.5f) w.live = false;
    }
    for (Burst& b : s_bursts) if (b.t >= 0.0f && (b.t += dt) > 0.6f) b.t = -1.0f;

    // Another, while the player is in the desert: in from just past the
    // windward edge of the view, somewhere along it, on sand.
    int tx = (int)floorf(wrap_px(px) / TILE_SIZE), ty = (int)floorf(wrap_py(py) / TILE_SIZE);
    if (tx < 0 || ty < 0 || tx >= MAP_WIDTH || ty >= MAP_HEIGHT || map->tiles[ty][tx] != TILE_SAND) return;
    if ((s_spawn_t -= dt) > 0.0f) return;
    s_spawn_t = frand(SPAWN_T_LO, SPAWN_T_HI);
    float side = frand(-0.8f, 0.8f) * (fabsf(wy) * vw * 0.5f + fabsf(wx) * vh * 0.5f);
    float sx = px - wx * (reach + 40.0f) - wy * side, sy = py - wy * (reach + 40.0f) + wx * side;
    int stx = (int)floorf(wrap_px(sx) / TILE_SIZE), sty = (int)floorf(wrap_py(sy) / TILE_SIZE);
    if (stx < 0 || sty < 0 || stx >= MAP_WIDTH || sty >= MAP_HEIGHT || map->tiles[sty][stx] != TILE_SAND) return;
    if (tilemap_pixel_solid(map, sx, sy)) return;
    if (Tumbleweed* w = tumble_spawn_at(sx, sy)) {
        w->vx = wx * w->speed * strength;
        w->vy = wy * w->speed * strength;
    }
}

// Its shadow on the sand: an ellipse of black, half its pixels by the dither
// on the ground, thinner and smaller the higher it is (no alpha: every pixel
// stays on the palette).
static void draw_shadow(SDL_Renderer* ren, const Camera* cam, float x, float y, float z) {
    float s = ART * cam->zoom;
    float up = fminf(z, 80.0f) / 80.0f;
    int rx = (int)roundf(6.0f - 2.5f * up), ry = 2;
    int level = 8 - (int)(4.0f * up);   // of 16: how much of it is black
    int gx = cam_screen_x(cam, x), gy = cam_screen_y(cam, y);
    fc_draw_color(ren, 0, 0, 0, 255);
    for (int j = -ry; j <= ry; j++)
        for (int i = -rx; i <= rx; i++)
            if (i * i * ry * ry + j * j * rx * rx <= rx * rx * ry * ry && fc_bayer(i + rx, j + ry) < level) {
                SDL_Rect p = { gx + (int)(i * s), gy + (int)((j - 1) * s), (int)ceilf(s), (int)ceilf(s) };
                SDL_RenderFillRect(ren, &p);
            }
}

bool tumble_sprite(int i, float px, float py, float* feet, float* x, float* y, float* w, float* h) {
    if (i < 0 || i >= TUMBLE_MAX || !s_weeds[i].live) return false;
    const Tumbleweed& t = s_weeds[i];
    float gx = px + wrap_dpx(t.x - px), gy = py + wrap_dpy(t.y - py);
    *feet = gy;
    *x = gx - MID_COL * ART; *w = CELL * ART;
    *y = gy - t.z - FOOT_ROW * ART; *h = CELL * ART + t.z;   // down to the shadow
    return true;
}

void tumble_draw_one(SDL_Renderer* ren, const Camera* cam, SDL_Texture* sheet, int i) {
    if (i < 0 || i >= TUMBLE_MAX || !s_weeds[i].live) return;
    const Tumbleweed& w = s_weeds[i];
    float s = ART * cam->zoom;
    draw_shadow(ren, cam, w.x, w.y, w.z);
    if (!sheet) return;
    SDL_Rect src = { (SHEET_COL + tumble_frame(w)) * CELL, SHEET_ROW * CELL, CELL, CELL };
    SDL_Rect dst = { cam_screen_x(cam, w.x) - (int)(MID_COL * s), cam_screen_y(cam, w.y - w.z) - (int)(FOOT_ROW * s),
                     (int)(CELL * s), (int)(CELL * s) };
    SDL_RenderCopy(ren, sheet, &src, &dst);
}

void tumble_draw_bursts(SDL_Renderer* ren, const Camera* cam) {
    // Broken: a spray of twigs, out and down.
    float s = ART * cam->zoom;
    for (const Burst& b : s_bursts) {
        if (b.t < 0.0f) continue;
        for (int k = 0; k < 8; k++) {
            float a = k * 0.785398f + 0.3f;
            float d = 40.0f * b.t, fall = 200.0f * b.t * b.t;
            float x = b.x + cosf(a) * d, y = b.y - BALL_R + sinf(a) * d * 0.6f + fall;
            fc_draw_color(ren, k % 2 ? 120 : 80, k % 2 ? 80 : 50, k % 2 ? 40 : 24, 255);
            SDL_Rect p = { cam_screen_x(cam, x), cam_screen_y(cam, y), (int)ceilf(s), (int)ceilf(s) };
            SDL_RenderFillRect(ren, &p);
        }
    }
}

// ── Struck ───────────────────────────────────────────────────────────────

static void burst(Tumbleweed& w, HarvestResult* out) {
    w.live = false;
    float bx = w.x, by = w.y - w.z;
    harvest_add_item(out, bx, by - BALL_R, ITEM_WOOD, 1);
    for (Burst& b : s_bursts) if (b.t < 0.0f) { b = { bx, by, 0.0f }; break; }
}

// The ball's middle, from (px, py), the nearest way round the world.
static void offset(const Tumbleweed& w, float px, float py, float* dx, float* dy) {
    *dx = wrap_dpx(w.x - px);
    *dy = wrap_dpy(w.y - w.z - BALL_R - py);
}

int tumble_try_hit(float px, float py, int range, HarvestResult* out) {
    Tumbleweed* best = nullptr;
    float bd = (float)range * range;
    for (Tumbleweed& w : s_weeds) {
        if (!w.live) continue;
        float dx, dy;
        offset(w, px, py, &dx, &dy);
        float d2 = dx * dx + dy * dy;
        if (d2 <= bd) { bd = d2; best = &w; }
    }
    if (!best) return 0;
    burst(*best, out);
    return 1;
}

int tumble_sweep(float px, float py, float radius, float start_ang, float rel0, float rel1, HarvestResult* out) {
    int n = 0;
    for (Tumbleweed& w : s_weeds) {
        if (!w.live) continue;
        float dx, dy;
        offset(w, px, py, &dx, &dy);
        float r = radius + BALL_R;
        if (dx * dx + dy * dy > r * r) continue;
        float rel = sweep_relative_angle(start_ang, dx, dy);
        if (rel < rel0 || rel >= rel1) continue;
        burst(w, out);
        n++;
    }
    return n;
}

int tumble_thrust(float px, float py, float angle, float half_width, float from, float to, HarvestResult* out) {
    int n = 0;
    for (Tumbleweed& w : s_weeds) {
        if (!w.live) continue;
        float dx, dy, along, side;
        offset(w, px, py, &dx, &dy);
        thrust_project(angle, dx, dy, &along, &side);
        if (along < from || along >= to || fabsf(side) > half_width + BALL_R) continue;
        burst(w, out);
        n++;
    }
    return n;
}

int tumble_strike_point(float x, float y, float radius, HarvestResult* out) {
    for (Tumbleweed& w : s_weeds) {
        if (!w.live) continue;
        float dx, dy;
        offset(w, x, y, &dx, &dy);
        float r = radius + BALL_R;
        if (dx * dx + dy * dy <= r * r) { burst(w, out); return 1; }
    }
    return 0;
}
