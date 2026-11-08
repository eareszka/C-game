// The intro's night, fog wall and bounds (include/intro.h, docs/story.md).
#include "intro.h"
#include "tilemap.h"
#include "camera.h"
#include "overworld.h"
#include "collision.h"
#include <SDL2/SDL_image.h>
#include <math.h>
#include <string.h>

namespace {

// The area's mask, one byte a tile: 0 open, 1..FOG_STEPS the fog's density
// out from the open ground (FOG_STEPS = solid).
enum { AREA = 200, ORIGIN_FROM_TOWN = -22, FOG_STEPS = 4 };
unsigned char g_fog[AREA][AREA];
bool          g_loaded = false;
// One tile of fog at densities 1..FOG_STEPS-1: a 4x4 Bayer dither in 2 px
// cells (an art pixel), so the edge breaks up the way the NES would draw it.
SDL_Texture*  g_dither[FOG_STEPS] = {};
SDL_Texture*  g_dog = nullptr;

// The night: the frame multiplied by this, then this added. The user's
// approved mock-up (art/story/intro/night_mock_compare.png).
const SDL_Color NIGHT_MUL = { 92, 112, 178, 255 };
const SDL_Color NIGHT_ADD = { 6, 10, 26, 255 };
const SDL_Color FOG       = { 96, 104, 124, 255 };

bool origin(const Tilemap* map, int* ox, int* oy) {
    if (map->towns[0].x < 0) return false;
    *ox = map->towns[0].x + ORIGIN_FROM_TOWN;
    *oy = map->towns[0].y + ORIGIN_FROM_TOWN;
    return true;
}

// Density at world tile (tx, ty); everything off the mask is solid fog.
int density(const Tilemap* map, int tx, int ty) {
    int ox, oy;
    if (!g_loaded || !origin(map, &ox, &oy)) return 0;
    int x = tx - ox, y = ty - oy;
    if (x < 0 || y < 0 || x >= AREA || y >= AREA) return FOG_STEPS;
    return g_fog[y][x];
}

} // namespace

bool intro_init(SDL_Renderer* ren) {
    intro_free();
    SDL_Surface* s = IMG_Load("assets/story/intro_area.png");
    if (!s) return false;
    SDL_Surface* m = SDL_ConvertSurfaceFormat(s, SDL_PIXELFORMAT_RGBA32, 0);
    SDL_FreeSurface(s);
    if (!m) return false;
    static bool open[AREA][AREA];
    for (int y = 0; y < AREA; y++)
        for (int x = 0; x < AREA; x++) {
            bool in = x < m->w && y < m->h;
            const Uint8* p = in ? (const Uint8*)m->pixels + y * m->pitch + x * 4 : nullptr;
            open[y][x] = p && p[0] > 127 && p[3] > 127;   // white = open
        }
    SDL_FreeSurface(m);
    // Fog density: tiles away from the nearest open tile (Chebyshev), capped.
    for (int y = 0; y < AREA; y++)
        for (int x = 0; x < AREA; x++) {
            int d = FOG_STEPS;
            for (int r = 0; r < FOG_STEPS && d == FOG_STEPS; r++)
                for (int dy = -r; dy <= r && d == FOG_STEPS; dy++)
                    for (int dx = -r; dx <= r; dx++) {
                        int nx = x + dx, ny = y + dy;
                        if (nx >= 0 && ny >= 0 && nx < AREA && ny < AREA && open[ny][nx]) { d = r; break; }
                    }
            g_fog[y][x] = (unsigned char)d;
        }
    static const int BAYER[4][4] = { {0, 8, 2, 10}, {12, 4, 14, 6}, {3, 11, 1, 9}, {15, 7, 13, 5} };
    for (int k = 1; k < FOG_STEPS; k++) {
        SDL_Surface* t = SDL_CreateRGBSurfaceWithFormat(0, TILE_SIZE, TILE_SIZE, 32, SDL_PIXELFORMAT_RGBA32);
        if (!t) continue;
        for (int y = 0; y < TILE_SIZE; y++)
            for (int x = 0; x < TILE_SIZE; x++) {
                Uint8* p = (Uint8*)t->pixels + y * t->pitch + x * 4;
                bool on = (BAYER[(y / 2) % 4][(x / 2) % 4] + 0.5f) / 16.0f < (float)k / FOG_STEPS;
                p[0] = FOG.r; p[1] = FOG.g; p[2] = FOG.b; p[3] = on ? 255 : 0;
            }
        g_dither[k] = SDL_CreateTextureFromSurface(ren, t);
        if (g_dither[k]) SDL_SetTextureBlendMode(g_dither[k], SDL_BLENDMODE_BLEND);
        SDL_FreeSurface(t);
    }
    if (SDL_Surface* d = IMG_Load("assets/story/dog.png")) {   // optional: no sheet, no dog
        g_dog = SDL_CreateTextureFromSurface(ren, d);
        SDL_FreeSurface(d);
    }
    g_loaded = true;
    return true;
}

void intro_free() {
    for (SDL_Texture*& t : g_dither) { if (t) SDL_DestroyTexture(t); t = nullptr; }
    if (g_dog) SDL_DestroyTexture(g_dog);
    g_dog = nullptr;
    g_loaded = false;
}

// Not saved yet: only `game.exe --intro` starts it until the whole night is built.
static int g_stage = INTRO_NONE;
bool intro_active() { return g_stage != INTRO_NONE; }
void intro_begin()  { g_stage = INTRO_NIGHT; }
void intro_end()    { g_stage = INTRO_NONE; }

bool intro_tile_open(const Tilemap* map, int tx, int ty) {
    return density(map, tx, ty) == 0;
}

void intro_confine(const Tilemap* map, Overworld* ow, float px, float py) {
    if (!intro_active() || !g_loaded) return;
    // The feet box's four corners must all stand on open tiles.
    auto inside = [&](float x, float y) {
        const float xs[2] = { x + HB_X1, x + HB_X2 - 1 }, ys[2] = { y + HB_Y1, y + HB_Y2 - 1 };
        for (float fx : xs)
            for (float fy : ys)
                if (!intro_tile_open(map, (int)floorf(fx / TILE_SIZE), (int)floorf(fy / TILE_SIZE))) return false;
        return true;
    };
    if (inside(ow->x, ow->y)) return;
    if (inside(ow->x, py))      { ow->y = py; return; }
    if (inside(px, ow->y))      { ow->x = px; return; }
    ow->x = px; ow->y = py;
}

void intro_draw_fog(SDL_Renderer* ren, const Camera* cam, const Tilemap* map) {
    if (!intro_active() || !g_loaded) return;
    float zoom = cam->zoom > 0.0f ? cam->zoom : 1.0f;
    int tx0 = (int)floorf(cam->x / TILE_SIZE) - 1, ty0 = (int)floorf(cam->y / TILE_SIZE) - 1;
    int tw = (int)(cam->screen_w / zoom / TILE_SIZE) + 3, th = (int)(cam->screen_h / zoom / TILE_SIZE) + 3;
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    SDL_SetRenderDrawColor(ren, FOG.r, FOG.g, FOG.b, 255);
    for (int ty = ty0; ty < ty0 + th; ty++)
        for (int tx = tx0; tx < tx0 + tw; tx++) {
            int d = density(map, tx, ty);
            if (!d) continue;
            int x0 = cam_px(cam, (float)tx * TILE_SIZE), y0 = cam_py(cam, (float)ty * TILE_SIZE);
            SDL_Rect r = { x0, y0, cam_px(cam, (float)(tx + 1) * TILE_SIZE) - x0, cam_py(cam, (float)(ty + 1) * TILE_SIZE) - y0 };
            if (d >= FOG_STEPS || !g_dither[d]) SDL_RenderFillRect(ren, &r);
            else SDL_RenderCopy(ren, g_dither[d], nullptr, &r);
        }
}

void intro_draw_night(SDL_Renderer* ren, int w, int h) {
    if (!intro_active()) return;
    SDL_Rect all = { 0, 0, w, h };
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_MOD);
    SDL_SetRenderDrawColor(ren, NIGHT_MUL.r, NIGHT_MUL.g, NIGHT_MUL.b, 255);
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_ADD);
    SDL_SetRenderDrawColor(ren, NIGHT_ADD.r, NIGHT_ADD.g, NIGHT_ADD.b, 255);
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
}

// --- The dog ----------------------------------------------------------------
namespace {

// The sheet: a 12 x 12 cell per pose, drawn at 2 px an art pixel. Rows face
// south, north, east, west; columns stand, walk 1-4, idle B.
enum { DOG_CELL = 12, DOG_PX = 2, DOG_WALK = 1, DOG_IDLE_B = 5 };
enum { DOG_S, DOG_N, DOG_E, DOG_W };
const float DOG_GAP     = 26.0f;     // how far behind the boy it keeps, along his path
const float DOG_STEP    = 0.20f;     // walk frame: the boy's own step time
const float DOG_IDLE    = 0.42f;     // idle: stand and pant (or wag) in turn
const float DOG_SPEED   = 120.0f;    // PLAYER_WALK_SPEED; faster when the boy is
const int   TRAIL       = 256;

struct Crumb { float x, y; };
struct Dog {
    int   space = -2;                // -2: not placed yet
    float x = 0, y = 0;              // feet
    Crumb trail[TRAIL];              // the boy's footsteps, oldest first
    int   head = 0, n = 0;
    float bx = 0, by = 0;            // the boy last frame
    int   face = DOG_S;
    bool  moving = false;
    float t = 0;                     // animation clock
} g_dog_s;

Crumb& crumb(int i) { return g_dog_s.trail[(g_dog_s.head + i) % TRAIL]; }

void push(float x, float y) {
    Dog& d = g_dog_s;
    if (d.n == TRAIL) { d.head = (d.head + 1) % TRAIL; d.n--; }
    crumb(d.n++) = { x, y };
}

} // namespace

void intro_dog_update(int space, float bx, float by, float dt) {
    Dog& d = g_dog_s;
    if (!intro_active() || !g_dog) { d.space = -2; return; }
    if (space != d.space) {          // a new place: it comes in beside him
        d.space = space;
        d.x = bx + DOG_GAP * 0.8f; d.y = by;
        d.n = d.head = 0; d.bx = bx; d.by = by;
        d.face = DOG_W; d.moving = false; d.t = 0;
        return;
    }
    float boy_v = dt > 0 ? sqrtf((bx - d.bx) * (bx - d.bx) + (by - d.by) * (by - d.by)) / dt : 0;
    d.bx = bx; d.by = by;
    if (!d.n || fabsf(crumb(d.n - 1).x - bx) + fabsf(crumb(d.n - 1).y - by) >= 2.0f) push(bx, by);
    // How far it is from the boy along his footsteps.
    float path = 0, px = d.x, py = d.y;
    for (int i = 0; i < d.n; i++) {
        path += sqrtf((crumb(i).x - px) * (crumb(i).x - px) + (crumb(i).y - py) * (crumb(i).y - py));
        px = crumb(i).x; py = crumb(i).y;
    }
    float ox = d.x, oy = d.y;
    if (path > DOG_GAP) {
        float speed = boy_v > DOG_SPEED ? boy_v : DOG_SPEED;
        if (path > DOG_GAP * 3) speed *= 1.5f;      // fallen behind: it runs
        float go = speed * dt;
        if (go > path - DOG_GAP) go = path - DOG_GAP;
        while (go > 0 && d.n) {
            Crumb c = crumb(0);
            float dx = c.x - d.x, dy = c.y - d.y, len = sqrtf(dx * dx + dy * dy);
            if (len <= go) { d.x = c.x; d.y = c.y; go -= len; d.head = (d.head + 1) % TRAIL; d.n--; }
            else { d.x += dx / len * go; d.y += dy / len * go; go = 0; }
        }
    }
    float mx = d.x - ox, my = d.y - oy;
    bool moving = fabsf(mx) + fabsf(my) > 0.01f;
    if (moving) d.face = fabsf(mx) > fabsf(my) ? (mx > 0 ? DOG_E : DOG_W) : (my > 0 ? DOG_S : DOG_N);
    if (moving != d.moving) d.t = 0;
    d.moving = moving;
    d.t += dt;
}

bool intro_dog_feet(float* x, float* y) {
    if (!intro_active() || !g_dog || g_dog_s.space == -2) return false;
    *x = g_dog_s.x; *y = g_dog_s.y;
    return true;
}

void intro_dog_draw(SDL_Renderer* ren, const Camera* cam) {
    float fx, fy;
    if (!intro_dog_feet(&fx, &fy)) return;
    const Dog& d = g_dog_s;
    int col = d.moving ? DOG_WALK + (int)(d.t / DOG_STEP) % 4
                       : ((int)(d.t / DOG_IDLE) % 2 ? DOG_IDLE_B : 0);
    float z = cam->zoom > 0 ? cam->zoom : 1.0f, w = DOG_CELL * DOG_PX;
    SDL_Rect src = { col * DOG_CELL, d.face * DOG_CELL, DOG_CELL, DOG_CELL };
    SDL_Rect dst = { cam_screen_x(cam, fx - w * 0.5f), cam_screen_y(cam, fy - w), (int)(w * z), (int)(w * z) };
    SDL_RenderCopy(ren, g_dog, &src, &dst);
}
