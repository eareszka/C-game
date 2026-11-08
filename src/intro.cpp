// The intro's night, fog wall and bounds (include/intro.h, docs/story.md).
#include "intro.h"
#include "tilemap.h"
#include "camera.h"
#include "overworld.h"
#include "collision.h"
#include "fc_palette.h"
#include "audio.h"
#include "battle.h"      // draw_actor_appearance: the townspeople's door fade
#include "npc_sleep.h"   // the boy asleep in his bed
#include "resident_path.h"   // the townspeople's door spots, inside and out
#include <SDL2/SDL_image.h>
#include <math.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

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
SDL_Texture*  g_boy_sleep = nullptr;   // assets/story/boy_sleep.png (art/story/intro/boy_sleep.py)
SDL_Texture*  g_page = nullptr;        // the hole's falling page, art/structures/hole/page.png
SDL_Texture*  g_hand = nullptr;        // 44 Itqiirpak's battle sheet, drawn black: the hand rising

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
    // Optional, each: without one, that piece just isn't drawn.
    g_dog       = IMG_LoadTexture(ren, "assets/story/dog.png");
    g_boy_sleep = IMG_LoadTexture(ren, "assets/story/boy_sleep.png");
    g_page      = IMG_LoadTexture(ren, "art/structures/hole/page.png");
    g_hand      = IMG_LoadTexture(ren, "assets/enemies/redraws/44_itqiirpak.png");
    if (g_hand) SDL_SetTextureColorMod(g_hand, 8, 6, 12);   // a silhouette: near-black, its shape kept
    g_loaded = true;
    return true;
}

void intro_free() {
    for (SDL_Texture*& t : g_dither) { if (t) SDL_DestroyTexture(t); t = nullptr; }
    for (SDL_Texture** t : { &g_dog, &g_boy_sleep, &g_page, &g_hand }) { if (*t) SDL_DestroyTexture(*t); *t = nullptr; }
    g_loaded = false;
}

// Not saved yet: only `game.exe --intro` starts it until the whole night is built.
static int g_stage = INTRO_NONE;
bool intro_active() { return g_stage != INTRO_NONE; }
bool intro_night()  { return g_stage != INTRO_NONE && g_stage <= INTRO_TAKEN; }
int  intro_stage()  { return g_stage; }
static void intro_reset();   // every clock and the dog back to the night's start (end of file)
void intro_begin()  { intro_reset(); g_stage = INTRO_ASLEEP; }
void intro_end()    { g_stage = INTRO_NONE; }

// DAWN, the morning after (the user): his first step out of the house, he
// stands still while the night lifts to day over DAWN_LIGHT s and the fog
// thins away a step at a time over DAWN_FOG s, from DAWN_HOLD s in (the
// door's black first); he can go at DAWN_END and the intro is over.
static float g_dawn_t = -1;
static const float DAWN_HOLD = 1.0f, DAWN_LIGHT = 3.0f, DAWN_FOG = 3.0f, DAWN_END = 5.5f;
static float dawn_dark() {             // 1 night .. 0 day, eased
    float t = (g_dawn_t - DAWN_HOLD) / DAWN_LIGHT;
    if (t <= 0.0f) return 1.0f;
    if (t >= 1.0f) return 0.0f;
    return 1.0f - t * t * (3.0f - 2.0f * t);
}
static int dawn_fog_cut() {            // fog steps gone: 0 .. FOG_STEPS, in hard steps
    float t = (g_dawn_t - DAWN_HOLD) / DAWN_FOG;
    return t <= 0.0f ? 0 : t >= 1.0f ? FOG_STEPS : (int)(t * (FOG_STEPS + 1));
}

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
            if (g_stage == INTRO_DAWN) d -= dawn_fog_cut();   // the morning: thinning away
            if (d <= 0) continue;
            int x0 = cam_px(cam, (float)tx * TILE_SIZE), y0 = cam_py(cam, (float)ty * TILE_SIZE);
            SDL_Rect r = { x0, y0, cam_px(cam, (float)(tx + 1) * TILE_SIZE) - x0, cam_py(cam, (float)(ty + 1) * TILE_SIZE) - y0 };
            if (d >= FOG_STEPS || !g_dither[d]) SDL_RenderFillRect(ren, &r);
            else SDL_RenderCopy(ren, g_dither[d], nullptr, &r);
        }
}

// How dark the house is, 1 night to 0 lit: once the boy is out of bed the
// lights come up over LIGHT_FADE seconds, eased at both ends.
static float g_light_t = -1;          // seconds since he got up, -1 before
static const float LIGHT_FADE = 1.6f;
static float house_dark() {
    if (g_light_t < 0) return 1.0f;
    float t = g_light_t / LIGHT_FADE;
    if (t >= 1.0f) return 0.0f;
    return 1.0f - t * t * (3.0f - 2.0f * t);
}

void intro_draw_night(SDL_Renderer* ren, int w, int h, bool indoors) {
    if (!intro_active()) return;
    float k = g_stage == INTRO_DAWN ? dawn_dark()
            : indoors && g_stage == INTRO_MORNING ? 0.0f     // the morning: the lights on
            : indoors ? house_dark() : 1.0f;
    if (k <= 0.0f) return;
    auto mix = [&](Uint8 night, float lit) { return (Uint8)(lit + (night - lit) * k + 0.5f); };
    SDL_Rect all = { 0, 0, w, h };
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_MOD);
    SDL_SetRenderDrawColor(ren, mix(NIGHT_MUL.r, 255), mix(NIGHT_MUL.g, 255), mix(NIGHT_MUL.b, 255), 255);
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_ADD);
    SDL_SetRenderDrawColor(ren, mix(NIGHT_ADD.r, 0), mix(NIGHT_ADD.g, 0), mix(NIGHT_ADD.b, 0), 255);
    SDL_RenderFillRect(ren, &all);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
}

// --- The opening: asleep, the dog's panic, the page falling ----------------
//
// The user's staging (docs/story.md): the boy and the dog asleep; the dog
// wakes, panics and runs out (fading at the door, as the townspeople do);
// the boy wakes a second later and the house's lights are on. Outside, the
// dog fades in by the door and sprints north out of sight. At the shore it
// barks north at nothing until the boy comes near; then a page floats down
// out of the air and lands beside it. Only then can it be read.
namespace {

const char* NOTE_TEXT = "Tonight the last pet is taken. Tomorrow something new takes its place.";

// Where the dog stops and barks, the user's spot (2026-11-08, moved the same
// day): sprite origin (48125, 45564) by the debug readout, in a world whose town 0 is at
// its fixed tile (1422, 1422) -- the island is the same stamp in every world,
// so the spot is kept relative to town 0. The page lands just north of it,
// right in front of its nose.
const float DOG_SPOT_DX = 48125 + (HB_X1 + HB_X2) * 0.5f - 1422 * TILE_SIZE;
const float DOG_SPOT_DY = 45564 + HB_Y2 - 1422 * TILE_SIZE;

bool dog_spot(const Tilemap* map, float* x, float* y) {
    if (!map || map->towns[0].x < 0) return false;
    *x = map->towns[0].x * (float)TILE_SIZE + DOG_SPOT_DX;
    *y = map->towns[0].y * (float)TILE_SIZE + DOG_SPOT_DY;
    return true;
}

// Where it is when the boy steps out, the user's spot: sprite origin
// (47831, 46348), already running for the water -- straight from here to
// its spot by the shore (dog_spot), one line.
const float DOG_OUT_DX = 47831 + (HB_X1 + HB_X2) * 0.5f - 1422 * TILE_SIZE;
const float DOG_OUT_DY = 46348 + HB_Y2 - 1422 * TILE_SIZE;

bool dog_out_spot(const Tilemap* map, float* x, float* y) {
    if (!map || map->towns[0].x < 0) return false;
    *x = map->towns[0].x * (float)TILE_SIZE + DOG_OUT_DX;
    *y = map->towns[0].y * (float)TILE_SIZE + DOG_OUT_DY;
    return true;
}

bool page_spot(const Tilemap* map, float* x, float* y) {
    if (!dog_spot(map, x, y)) return false;
    *y -= 42.0f;    // its middle: clear of the dog's ears (it stands 22 px tall)
    return true;
}

// The page's fall: from PAGE_DROP above where it lands, over PAGE_FALL
// seconds, swaying and turning over as the hole's pages do (story.cpp).
const float PAGE_FALL = 2.6f, PAGE_DROP = 170.0f, PAGE_NEAR = 7.0f * TILE_SIZE;
enum { PAGE_W = 6, PAGE_H = 8 };
float g_page_t = 0;          // seconds into the fall

// The boy, asleep then up: his bed in room 0 is the fisher's (room 2's)
// bed, the same numbers (house0_design.py: bed(r, 168, BACK + 8, flip)).
const float BOY_BED_X = 413, BOY_BED_Y = 222;
// His feet once up: the user's spot, sprite origin (403, 217) as the debug
// readout gives it, in front of the bed's front edge (240) so none of him is
// drawn behind it.
const float WAKE_X = 403 + (HB_X1 + HB_X2) * 0.5f, WAKE_Y = 217 + HB_Y2;
float g_sleep_t = 0;         // seconds since the night began, for his breathing and Z's
bool  g_wake_pending = false;
// Waking, in steps: asleep; stirring (the Z's stop, he shifts in the
// covers); out of bed (a hop down onto his spot, facing down); up.
enum BoyPhase { B_SLEEP, B_STIR, B_OUT, B_UP };
BoyPhase g_boy = B_SLEEP;
float    g_boy_t = 0;
const float STIR_SECS = 0.9f, OUT_SECS = 0.35f, OUT_HOP = 8.0f;

void boy_tick(float dt) {
    if (g_boy == B_SLEEP || g_boy == B_UP) return;
    g_boy_t += dt;
    const float len = g_boy == B_STIR ? STIR_SECS : OUT_SECS;
    if (g_boy_t < len) return;
    g_boy_t = 0;
    g_boy = (BoyPhase)(g_boy + 1);
    if (g_boy != B_UP) return;
    g_wake_pending = true;
    if (g_stage == INTRO_ASLEEP) { g_stage = INTRO_AWAKE; g_light_t = 0; }   // the morning keeps its stage
}

} // namespace

bool intro_holds_player() {   // not in the fight: the battle reads the same input
    return g_stage == INTRO_ASLEEP || g_stage == INTRO_READ || g_stage == INTRO_EMERGE || g_stage == INTRO_TAKEN ||
           (g_stage == INTRO_MORNING && g_boy != B_UP) || g_stage == INTRO_DAWN;
}   // not in the fight: the battle reads the same input

bool intro_take_wake(float* feet_x, float* feet_y) {
    if (!g_wake_pending) return false;
    g_wake_pending = false;
    *feet_x = WAKE_X; *feet_y = WAKE_Y;
    return true;
}

bool intro_draw_sleeper(SDL_Renderer* ren, const Camera* cam) {
    if ((g_stage != INTRO_ASLEEP && g_stage != INTRO_MORNING) || !g_boy_sleep) return false;
    if (g_boy == B_SLEEP) { npc_sleep_draw(ren, g_boy_sleep, cam, BOY_BED_X, BOY_BED_Y, true, g_sleep_t); return true; }
    if (g_boy != B_STIR) return false;
    // Stirring: his sleeping cel without the Z's, shifting a pixel in the
    // covers and breathing quick (npc_sleep_draw's own placement).
    int breath = (int)(g_boy_t / 0.22f) & 1;
    float nudge = breath ? 2.0f : 0.0f;
    SDL_Rect src = { breath * 14 + 2, 4, 11, 16 };
    int w = (int)(src.w * 2 * cam->zoom), h = (int)(src.h * 2 * cam->zoom);
    SDL_Rect dst = { cam_screen_x(cam, BOY_BED_X) - w / 2, cam_screen_y(cam, BOY_BED_Y - nudge) - h / 2, w, h };
    SDL_RenderCopyEx(ren, g_boy_sleep, &src, &dst, 90, nullptr, SDL_FLIP_NONE);
    return true;
}

// After the fight: out cold on the ground where he stood -- his sleeping
// cel lying on its side, still, and no Z's (the user), his middle over his feet.
bool intro_draw_fallen(SDL_Renderer* ren, const Camera* cam, float fx, float fy) {
    if (g_stage != INTRO_TAKEN || !g_boy_sleep) return false;
    SDL_Rect src = { 2, 4, 11, 16 };
    int w = (int)(src.w * 2 * cam->zoom), h = (int)(src.h * 2 * cam->zoom);
    SDL_Rect dst = { cam_screen_x(cam, fx) - w / 2, cam_screen_y(cam, fy - 8.0f) - h / 2, w, h };
    SDL_RenderCopyEx(ren, g_boy_sleep, &src, &dst, 90, nullptr, SDL_FLIP_NONE);
    return true;
}

bool intro_boy_scripted(float* feet_x, float* feet_y, float* lift, int* frame) {
    if ((g_stage != INTRO_ASLEEP && g_stage != INTRO_MORNING) || g_boy != B_OUT) return false;
    // Out of bed: on his spot facing down (entity.h FACE_DOWN, frame 0), a
    // little hop as he lands, high at first and down by the end.
    float t = g_boy_t / OUT_SECS;
    *feet_x = WAKE_X; *feet_y = WAKE_Y;
    *lift = OUT_HOP * 4.0f * t * (1.0f - t) + OUT_HOP * (1.0f - t) * (1.0f - t);
    *frame = 0;
    return true;
}

// --- The hand ---------------------------------------------------------------
// Read, a breath; then 44 Itqiirpak, black, rises out of the sea north of the
// dog: its battle sheet's front view (frames 0-1 breathing, 2 every mouth
// wide), at the fight's own size, cut off at the waterline as it comes up.
// It holds a moment, mouths wide, and the fight begins.
namespace {
const float READ_PAUSE = 0.0f, RISE_SECS = 3.2f, ROAR_SECS = 1.2f;
const float DOG_CELL_H = 24.0f;               // the dog drawn: 12 art px at 2
const int   HAND_W = 130, HAND_H = 88;        // a frame of assets/enemies/redraws/44_itqiirpak.png
const float HAND_SUNK = -14.0f;               // risen, this much of it still under the water: none -- the whole hand out and a little clear of the waterline (the user: "slightly more")
float g_hand_t = 0;                           // seconds since the page was read
bool  g_fight_pending = false;

// The sea's edge north of the dog: the shore's first water row, a tile north
// of the page (the user's spot is a tile and a half off the water).
bool waterline(const Tilemap* map, float* x, float* y) {
    if (!dog_spot(map, x, y)) return false;
    *y = floorf((*y - 42.0f) / TILE_SIZE) * TILE_SIZE;   // the top of the page's tile
    return true;
}
} // namespace

namespace {
// TAKEN, in seconds from the fight's end: the hand holds (the map comes back
// out of black), reaches down over the shore, closes on the dog, carries it
// off north faster and faster; then black, and the card on the black.
const float TK_HOLD = 1.4f, TK_REACH = 1.1f, TK_GRAB = 0.5f, TK_CARRY = 3.2f, TK_FADE = 1.0f,
            TK_CARD_IN = 0.4f, TK_CARD = 2.6f;
const float TK_GRAB_AT  = TK_HOLD + TK_REACH;
const float TK_CARRY_AT = TK_GRAB_AT + TK_GRAB;
const float TK_FADE_AT  = TK_CARRY_AT + TK_CARRY;
const float TK_END      = TK_FADE_AT + TK_FADE + TK_CARD_IN + TK_CARD;
const float CARRY_DIST  = 560.0f;      // north, off the top of the screen
const float GRIP_FEET   = 40.0f;       // carried: the dog's feet this far over the hand's bottom edge -- the dog in the middle of the palm (the user)
const float MORNING_IN  = 1.0f;        // the bedroom out of black
const float MORNING_STIR = 2.2f;       // then he stirs and gets up
float g_taken_t = 0, g_morning_t = 0;
bool  g_morning_pending = false;

float ease(float t) { t = t < 0 ? 0 : t > 1 ? 1 : t; return t * t * (3.0f - 2.0f * t); }

// The hand's bottom edge (world y) in TAKEN, and its frame. `wy` the
// waterline, `dog_y` the dog's feet at its spot.
float taken_hand_bottom(float wy, float dog_y, int* frame) {
    float t = g_taken_t, risen = wy + HAND_SUNK, grip = dog_y + GRIP_FEET;   // the palm over the dog
    if (t < TK_HOLD)     { *frame = (int)(t / 0.5f) & 1; return risen; }
    if (t < TK_GRAB_AT)  { *frame = 2; return risen + (grip - risen) * ease((t - TK_HOLD) / TK_REACH); }
    if (t < TK_CARRY_AT) { *frame = 0; return grip; }
    float c = (t - TK_CARRY_AT) / TK_CARRY; if (c > 1) c = 1;
    *frame = (int)(t / 0.35f) & 1;
    return grip - CARRY_DIST * c * c;
}
} // namespace

void intro_taken_begin() { g_stage = INTRO_TAKEN; g_taken_t = 0; g_morning_pending = false; }

void intro_test_taken() { intro_test_read(); intro_taken_begin(); }

bool intro_take_morning() {
    if (!g_morning_pending) return false;
    g_morning_pending = false;
    g_stage = INTRO_MORNING; g_morning_t = 0; g_sleep_t = 0;
    g_boy = B_SLEEP; g_boy_t = 0; g_wake_pending = false;
    return true;
}

float intro_blackout(const char** card) {
    *card = nullptr;
    if (g_stage == INTRO_TAKEN) {
        float t = g_taken_t - TK_FADE_AT;
        if (t <= 0) return 0;
        if (t >= TK_FADE + TK_CARD_IN) *card = "THE NEXT MORNING";
        return t >= TK_FADE ? 1.0f : t / TK_FADE;
    }
    if (g_stage == INTRO_MORNING && g_morning_t < MORNING_IN) return 1.0f - g_morning_t / MORNING_IN;
    return 0;
}

bool intro_take_fight(const Tilemap* map, float* x, float* y) {
    if (!g_fight_pending || !waterline(map, x, y)) return false;
    g_fight_pending = false;
    g_stage = INTRO_FIGHT;
    *y -= HAND_H;      // its middle, risen
    return true;
}

static void draw_hand(SDL_Renderer* ren, const Camera* cam, const Tilemap* map) {
    float wx, wy;
    if (!g_hand || (g_stage != INTRO_EMERGE && g_stage != INTRO_FIGHT && g_stage != INTRO_TAKEN) || !waterline(map, &wx, &wy)) return;
    if (g_stage == INTRO_TAKEN) {
        // Reaching over the shore and carrying the dog off: clear of the water, no clip.
        float dx, dy;
        int frame;
        if (!dog_spot(map, &dx, &dy)) return;
        float bottom = taken_hand_bottom(wy, dy, &frame), h = HAND_H * 2.0f, z = cam->zoom;
        SDL_Rect src = { frame * HAND_W, 0, HAND_W, HAND_H };
        SDL_Rect dst = { cam_px(cam, wx - HAND_W), cam_py(cam, bottom - h), (int)(HAND_W * 2 * z), (int)(h * z) };
        SDL_RenderCopy(ren, g_hand, &src, &dst);
        return;
    }
    float t = g_hand_t - READ_PAUSE;
    if (t <= 0) return;
    float rise = t >= RISE_SECS ? 1.0f : t / RISE_SECS;
    rise = 1.0f - (1.0f - rise) * (1.0f - rise);                // slowing as it comes clear
    float h = HAND_H * 2.0f, bottom = wy + h + HAND_SUNK - (h) * rise;   // its frame's bottom edge
    int frame = t >= RISE_SECS ? 2 : ((int)(t / 0.5f) & 1);
    float z = cam->zoom;
    SDL_Rect src = { frame * HAND_W, 0, HAND_W, HAND_H };
    SDL_Rect dst = { cam_px(cam, wx - HAND_W), cam_py(cam, bottom - h), (int)(HAND_W * 2 * z), (int)(h * z) };
    // Under the water nothing shows: clipped at the waterline.
    SDL_Rect clip = { 0, 0, 100000, cam_py(cam, wy) };
    SDL_RenderSetClipRect(ren, &clip);
    SDL_RenderCopy(ren, g_hand, &src, &dst);
    SDL_RenderSetClipRect(ren, nullptr);
}

bool intro_page_land(const Tilemap* map, float* x, float* y) {
    return page_spot(map, x, y);
}

bool intro_note_spot(const Tilemap* map, float* x, float* y) {
    return g_stage == INTRO_PAGE_DOWN && page_spot(map, x, y);
}

const char* intro_note_take() {
    g_stage = INTRO_READ;
    return NOTE_TEXT;
}

void intro_draw_note(SDL_Renderer* ren, const Camera* cam, const Tilemap* map) {
    draw_hand(ren, cam, map);
    float x, y, z = cam->zoom;
    if (!page_spot(map, &x, &y)) return;
    if (g_stage == INTRO_PAGE_FALLING && g_page) {
        // Drifting down, swaying, turning over and back.
        float ph = g_page_t / PAGE_FALL;
        float px = x + 12.0f * sinf(ph * 7.0f), py = y - PAGE_DROP * (1.0f - ph);
        int frame = (int)(g_page_t * 5.0f) & 1;
        SDL_Rect src = { frame * PAGE_W, 0, PAGE_W, PAGE_H };
        SDL_Rect dst = { cam_px(cam, px - PAGE_W), cam_py(cam, py - PAGE_H), (int)(PAGE_W * 2 * z), (int)(PAGE_H * 2 * z) };
        SDL_RenderCopy(ren, g_page, &src, &dst);
        return;
    }
    if (g_stage != INTRO_PAGE_DOWN) return;
    // Landed: the writers' page as every note is drawn (main.cpp notes_tick).
    SDL_Rect page = { cam_px(cam, x) - (int)(6 * z), cam_py(cam, y) - (int)(5 * z), (int)(12 * z), (int)(10 * z) };
    fc_draw_color(ren, 40, 40, 40, 255);
    SDL_Rect shade = { page.x + 1, page.y + 1, page.w, page.h };
    SDL_RenderFillRect(ren, &shade);
    fc_draw_color(ren, 252, 252, 252, 255);
    SDL_RenderFillRect(ren, &page);
    fc_draw_color(ren, 160, 160, 160, 255);
    SDL_Rect fold = { page.x + (int)(2 * z), page.y + (int)(4 * z), page.w - (int)(4 * z), (int)(1 * z) > 0 ? (int)(1 * z) : 1 };
    SDL_RenderFillRect(ren, &fold);
}

// --- The dog ----------------------------------------------------------------
namespace {

// The sheet: a 12 x 12 cell per pose, drawn at 2 px an art pixel. Rows face
// south, north, east, west; columns stand, walk 1-4, idle B, asleep A and B.
enum { DOG_CELL = 12, DOG_PX = 2, DOG_WALK = 1, DOG_IDLE_B = 5, DOG_SLEEP = 6 };
enum { DOG_S, DOG_N, DOG_E, DOG_W };
const float DOG_GAP     = 26.0f;     // how far behind the boy it keeps, along his path
const float DOG_STEP    = 0.20f;     // walk frame: the boy's own step time
const float DOG_IDLE    = 0.42f;     // idle: stand and pant (or wag) in turn
const float DOG_SPEED   = 120.0f;    // PLAYER_WALK_SPEED; faster when the boy is
const float DOG_RUN     = 170.0f;    // out of the house
const float DOG_SPRINT  = 230.0f;    // north to the water
const int   TRAIL       = 256;
// Room 0 (house0_intro_design.py, room_0_intro.txt; screen pixels are
// 2 * (art + the frame's 32, 49)): the dog's bed's middle, art x 83 on floor
// row 69; the way out, tiles 4-5 of row 9.
// Its feet sit on the bed's front row (+4) so the rim doesn't draw over it;
// asleep it's drawn SLEEP_SINK up from there, lying in the cushion.
const float BED_X = 2 * (83 + 32), BED_Y = 2 * (69 + 49) + 4, SLEEP_SINK = 8.0f;
// The way out is the townspeople's: they walk to the room's entry spot
// (resident_entry: where the boy comes in) and fade there on the frame they
// arrived with, then appear on that frame outside the town's door
// (resident_outside). Feet are a sprite origin's (28x40 box) bottom middle.
ResidentPoint door_feet(ResidentPoint origin) { return { origin.x + (HB_X1 + HB_X2) * 0.5f, origin.y + HB_Y2 }; }
// The opening's beats, in seconds.
const float ASLEEP_SECS = 2.0f;      // both asleep
const float JOLT_SECS   = 0.6f;      // up with a start, the "!" over it
const float LOOK_SECS   = 0.25f;     // each glance: west, east, west, east
const float WAKE_AFTER  = 1.0f;      // the boy wakes this long after it's gone
// Barking: two yips, then a breath, heard out to BARK_HEARD pixels, fading.
const float BARK_EVERY = 1.3f, BARK_GAP = 0.2f, BARK_OPEN = 0.12f, BARK_HEARD = 700.0f;

enum Mode { M_FOLLOW, M_SLEEP, M_JOLT, M_LOOK, M_TO_DOOR, M_FADE_OUT, M_OUT,
            M_WAIT_DOOR, M_FADE_IN, M_SPRINT, M_AT_SHORE, M_CARRIED };

struct Crumb { float x, y; };
struct Dog {
    int   space = -2;                // -2: not placed yet
    Mode  mode = M_FOLLOW;
    bool  left_house = false;        // it ran out: the room is empty of it
    bool  at_shore = false;          // it has reached the water
    float x = 0, y = 0;              // feet
    float wx[3] = {}, wy[3] = {};    // the sprint's waypoints
    int   wn = 0, wi = 0;
    Crumb trail[TRAIL];              // the boy's footsteps, oldest first
    int   head = 0, n = 0;
    float bx = 0, by = 0;            // the boy last frame
    int   face = DOG_S;
    bool  moving = false, open = false;   // open: mid-bark, mouth open
    float t = 0, mt = 0;             // animation clock; time in this mode
    float gone_t = -1;               // time since it left the house (the boy's wake)
    int   fade_col = 0;              // the frame it went through the door on, kept for both fades
    int   ring = -1;                 // round the landed page: which spot (RING), -1 not started
    bool  ring_go = false;           // on its way to it
    float ring_t = 0;                // time barking there
} g_dog_s;

Crumb& crumb(int i) { return g_dog_s.trail[(g_dog_s.head + i) % TRAIL]; }

void push(float x, float y) {
    Dog& d = g_dog_s;
    if (d.n == TRAIL) { d.head = (d.head + 1) % TRAIL; d.n--; }
    crumb(d.n++) = { x, y };
}

void set_mode(Dog& d, Mode m) { d.mode = m; d.mt = 0; }

// Straight toward (tx, ty) at speed; true on arrival.
bool walk_to(Dog& d, float tx, float ty, float speed, float dt) {
    float dx = tx - d.x, dy = ty - d.y, len = sqrtf(dx * dx + dy * dy), go = speed * dt;
    if (len <= go) { d.x = tx; d.y = ty; return true; }
    d.x += dx / len * go; d.y += dy / len * go;
    return false;
}

void follow(Dog& d, float bx, float by, float dt) {
    float boy_v = dt > 0 ? sqrtf((bx - d.bx) * (bx - d.bx) + (by - d.by) * (by - d.by)) / dt : 0;
    if (!d.n || fabsf(crumb(d.n - 1).x - bx) + fabsf(crumb(d.n - 1).y - by) >= 2.0f) push(bx, by);
    float path = 0, px = d.x, py = d.y;
    for (int i = 0; i < d.n; i++) {
        path += sqrtf((crumb(i).x - px) * (crumb(i).x - px) + (crumb(i).y - py) * (crumb(i).y - py));
        px = crumb(i).x; py = crumb(i).y;
    }
    if (path <= DOG_GAP) return;
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

// Its place by the water, facing north (dog_spot).
bool shore(const Tilemap* map, float* x, float* y) { return dog_spot(map, x, y); }

// A new place: where the night puts the dog, or beside the boy.
void arrive(Dog& d, const Tilemap* map, int space, float bx, float by) {
    d.space = space; d.n = d.head = 0; d.bx = bx; d.by = by;
    d.moving = d.open = false; d.t = 0;
    float sx, sy;
    if (g_stage == INTRO_ASLEEP && space == 0 && !d.left_house) {
        set_mode(d, M_SLEEP); d.x = BED_X; d.y = BED_Y; d.face = DOG_S;
    } else if (g_stage < INTRO_READ && space == 0) {
        set_mode(d, M_OUT);                       // it's outside
    } else if (space == -1 && shore(map, &sx, &sy) && g_stage < INTRO_FIGHT) {
        d.left_house = true;
        float far = sqrtf((bx - sx) * (bx - sx) + (by - sy) * (by - sy));
        if (d.at_shore || far < 10.0f * TILE_SIZE) {
            set_mode(d, M_AT_SHORE); d.at_shore = true; d.x = sx; d.y = sy; d.face = DOG_N;
        } else {
            // He steps out and it's already well on its way (dog_out_spot).
            // It holds there while the screen is still black from the door,
            // then runs straight to its spot by the water (the user: "running
            // exactly to" it).
            float ax, ay;
            if (!dog_out_spot(map, &ax, &ay)) { ax = bx; ay = by; }
            set_mode(d, M_WAIT_DOOR); d.x = ax; d.y = ay; d.face = DOG_N;
            d.wn = 1; d.wi = 0;
            d.wx[0] = sx; d.wy[0] = sy;
        }
    } else {
        set_mode(d, M_FOLLOW); d.x = bx + DOG_GAP * 0.8f; d.y = by; d.face = DOG_W;
    }
}

const int LOOK[4] = { DOG_W, DOG_E, DOG_W, DOG_E };

// Once the page is down it goes round it barking: left of it, in front, right
// of it, in front again, and on; facing it from each. Feet offsets from the
// page's middle, and the facing.
struct RingSpot { float dx, dy; int face; };
const RingSpot RING[4] = { { -30, 8, DOG_E }, { 0, 30, DOG_N }, { 30, 8, DOG_W }, { 0, 30, DOG_N } };
const float RING_BARKS = 2.0f;       // bark rounds at each spot before moving on

} // namespace

void intro_test_read() {
    intro_skip_opening();
    g_stage = INTRO_READ; g_hand_t = 0;
}

void intro_skip_opening() {
    if (g_stage == INTRO_ASLEEP) g_stage = INTRO_AWAKE;
    g_boy = B_UP; g_light_t = LIGHT_FADE;
    g_dog_s.left_house = true;
}

// TAKEN: the dog at its spot barking up at the hand; gripped, it's carried
// off north kicking and barking, fainter as it goes.
static void taken_tick(const Tilemap* map, int space, float bx, float by, float dt) {
    Dog& d = g_dog_s;
    g_taken_t += dt;
    if (g_taken_t >= TK_END) g_morning_pending = true;
    float sx, sy, wx, wy;
    if (!dog_spot(map, &sx, &sy) || !waterline(map, &wx, &wy)) return;
    d.space = space;
    d.mt += dt; d.t += dt;
    bool was_open = d.open;
    float dist = sqrtf((bx - d.x) * (bx - d.x) + (by - d.y) * (by - d.y));
    if (g_taken_t < TK_GRAB_AT) {
        d.mode = M_AT_SHORE; d.x = sx; d.y = sy; d.face = DOG_N; d.moving = false;
        float ph = fmodf(d.mt, BARK_EVERY);
        d.open = ph < BARK_OPEN || (ph >= BARK_GAP && ph < BARK_GAP + BARK_OPEN);
        if (d.open && !was_open && dist < BARK_HEARD)
            audio_play(SFX_BARK, 1.0f - dist / BARK_HEARD, ph < BARK_GAP ? 1.0f : 0.92f);
        return;
    }
    int frame;
    d.mode = M_CARRIED; d.face = DOG_S;
    d.x = sx + (((int)(d.t / 0.12f) & 1) ? 1.0f : -1.0f);   // squirming
    d.y = taken_hand_bottom(wy, sy, &frame) - GRIP_FEET;
    // Quick yelps while it's carried off, dying away with the distance.
    float ph = fmodf(g_taken_t - TK_GRAB_AT, 0.45f);
    d.open = ph < BARK_OPEN;
    float gone = (g_taken_t - TK_CARRY_AT) / TK_CARRY;
    float gain = (1.0f - (gone > 0 ? gone : 0)) * (1.0f - dist / (BARK_HEARD * 1.5f));
    if (d.open && !was_open && gain > 0.03f && g_taken_t < TK_FADE_AT)
        audio_play(SFX_BARK, gain, ((int)((g_taken_t - TK_GRAB_AT) / 0.45f) & 1) ? 1.1f : 1.02f);
}

void intro_dog_update(const Tilemap* map, int space, float bx, float by, float dt) {
    Dog& d = g_dog_s;
    if (g_stage == INTRO_TAKEN) { taken_tick(map, space, bx, by, dt); return; }
    if (g_stage == INTRO_MORNING) {             // the dog's gone, and its things; he wakes in bed
        d = Dog{};
        g_morning_t += dt; g_sleep_t += dt;
        if (g_boy == B_SLEEP && g_morning_t >= MORNING_STIR) { g_boy = B_STIR; g_boy_t = 0; }
        boy_tick(dt);
        if (space == -1) { g_stage = INTRO_DAWN; g_dawn_t = 0; }   // his first step outside
        return;
    }
    if (g_stage == INTRO_DAWN) {                // standing still while the day comes; then he's free
        d = Dog{};
        g_dawn_t += dt;
        if (g_dawn_t >= DAWN_END) intro_end();
        return;
    }
    if (!intro_active() || !g_dog) { d = Dog{}; return; }
    if (g_stage == INTRO_ASLEEP) g_sleep_t += dt;
    boy_tick(dt);
    if (g_light_t >= 0) g_light_t += dt;
    if (d.gone_t >= 0) {
        d.gone_t += dt;
        if (g_boy == B_SLEEP && d.gone_t >= WAKE_AFTER) { g_boy = B_STIR; g_boy_t = 0; }
    }
    if (g_stage == INTRO_PAGE_FALLING) {
        g_page_t += dt;
        if (g_page_t >= PAGE_FALL) g_stage = INTRO_PAGE_DOWN;
    }
    if (g_stage == INTRO_READ || g_stage == INTRO_EMERGE) {
        g_hand_t += dt;
        if (g_stage == INTRO_READ && g_hand_t >= READ_PAUSE) g_stage = INTRO_EMERGE;
        if (g_stage == INTRO_EMERGE && g_hand_t >= READ_PAUSE + RISE_SECS + ROAR_SECS) g_fight_pending = true;
    }
    if (space != d.space) { arrive(d, map, space, bx, by); return; }
    float ox = d.x, oy = d.y;
    bool was_open = d.open;
    d.open = false;
    d.mt += dt;
    float sx, sy;
    switch (d.mode) {
    case M_SLEEP:
        if (g_sleep_t >= ASLEEP_SECS) { set_mode(d, M_JOLT); d.face = DOG_S; }
        break;
    case M_JOLT:
        if (d.mt >= JOLT_SECS) set_mode(d, M_LOOK);
        break;
    case M_LOOK:
        if (d.mt >= LOOK_SECS * 4) set_mode(d, M_TO_DOOR);
        else d.face = LOOK[(int)(d.mt / LOOK_SECS)];
        break;
    case M_TO_DOOR: {
        static const ResidentPoint way_out = door_feet(resident_entry(0));
        if (walk_to(d, way_out.x, way_out.y, DOG_RUN, dt)) {
            // Through it on the step it's on, facing the way it was going.
            float mx = d.x - ox, my = d.y - oy;
            if (fabsf(mx) + fabsf(my) > 0.01f) d.face = fabsf(mx) > fabsf(my) ? (mx > 0 ? DOG_E : DOG_W) : (my > 0 ? DOG_S : DOG_N);
            d.fade_col = DOG_WALK + (int)(d.t / DOG_STEP) % 4;
            set_mode(d, M_FADE_OUT);
        }
        break;
    }
    case M_FADE_OUT:
        if (d.mt >= ACTOR_APPEAR_T) { set_mode(d, M_OUT); d.left_house = true; d.gone_t = 0; }
        break;
    case M_OUT:
        break;
    case M_WAIT_DOOR:
        if (d.mt >= BATTLE_FADE_T) set_mode(d, M_SPRINT);   // the screen comes back with it running
        break;
    case M_FADE_IN:
        if (d.mt >= ACTOR_APPEAR_T) set_mode(d, M_SPRINT);
        break;
    case M_SPRINT:
        if (walk_to(d, d.wx[d.wi], d.wy[d.wi], DOG_SPRINT, dt) && ++d.wi >= d.wn) {
            set_mode(d, M_AT_SHORE); d.at_shore = true;
        }
        break;
    case M_AT_SHORE: {
        float dist = sqrtf((bx - d.x) * (bx - d.x) + (by - d.y) * (by - d.y));
        // Two yips a breath, the mouth open on each, fainter the farther the boy is.
        auto bark = [&]() {
            float ph = fmodf(d.mt, BARK_EVERY);
            d.open = ph < BARK_OPEN || (ph >= BARK_GAP && ph < BARK_GAP + BARK_OPEN);
            if (d.open && !was_open && dist < BARK_HEARD)
                audio_play(SFX_BARK, 1.0f - dist / BARK_HEARD, ph < BARK_GAP ? 1.0f : 0.92f);
        };
        float px, py;
        if (g_stage == INTRO_PAGE_DOWN && page_spot(map, &px, &py)) {
            // Round the page, barking at it from each side.
            if (d.ring < 0) { d.ring = 0; d.ring_go = true; }
            const RingSpot& r = RING[d.ring];
            if (d.ring_go) {
                if (walk_to(d, px + r.dx, py + r.dy, DOG_SPEED * 1.2f, dt)) { d.ring_go = false; d.ring_t = 0; d.mt = 0; }
            } else {
                d.face = r.face;
                bark();
                d.ring_t += dt;
                if (d.ring_t >= BARK_EVERY * RING_BARKS) { d.ring = (d.ring + 1) % 4; d.ring_go = true; }
            }
        } else if (g_stage == INTRO_EMERGE || g_stage == INTRO_FIGHT) {
            d.face = DOG_N;            // at the sea: the hand coming up
            if (g_hand_t > READ_PAUSE) bark();
        } else if (g_stage < INTRO_PAGE_DOWN) {
            // At its spot, barking north at nothing; the boy in sight of it
            // brings the page down.
            bark();
            if (g_stage == INTRO_AWAKE && dist < PAGE_NEAR) { g_stage = INTRO_PAGE_FALLING; g_page_t = 0; }
            if (shore(map, &sx, &sy)) { d.x = sx; d.y = sy; }
            d.face = DOG_N;
        }
        break;
    }
    case M_FOLLOW:
        follow(d, bx, by, dt);
        break;
    }
    d.bx = bx; d.by = by;
    float mx = d.x - ox, my = d.y - oy;
    bool moving = fabsf(mx) + fabsf(my) > 0.01f;
    if (moving) d.face = fabsf(mx) > fabsf(my) ? (mx > 0 ? DOG_E : DOG_W) : (my > 0 ? DOG_S : DOG_N);
    if (moving != d.moving) d.t = 0;
    d.moving = moving;
    d.t += dt;
}

bool intro_dog_feet(float* x, float* y) {
    if (!intro_active() || !g_dog || g_dog_s.space == -2 || g_dog_s.mode == M_OUT) return false;
    *x = g_dog_s.x; *y = g_dog_s.y;
    return true;
}

namespace {

// A small cream Z with a black outline, art pixels of `px` screen pixels:
// the residents' sleeping Z (npc_sleep.h), drawn here for the dog.
void draw_glyph(SDL_Renderer* ren, const Camera* cam, float x, float y, const unsigned* rows, int w, int h, Uint8 alpha, float px = 2.0f) {
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
    for (int pass = 0; pass < 2; pass++) {
        SDL_SetRenderDrawColor(ren, pass ? 232 : 0, pass ? 224 : 0, pass ? 192 : 0, alpha);
        int r = pass ? 0 : 1;
        for (int row = 0; row < h; row++)
            for (int col = 0; col < w; col++) {
                if (!(rows[row] & (1u << (w - 1 - col)))) continue;
                float l = x + (col - r) * px, t = y + (row - r) * px;
                int x0 = cam_screen_x(cam, l), y0 = cam_screen_y(cam, t);
                SDL_Rect dot = { x0, y0, cam_screen_x(cam, l + (1 + 2 * r) * px) - x0, cam_screen_y(cam, t + (1 + 2 * r) * px) - y0 };
                SDL_RenderFillRect(ren, &dot);
            }
    }
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
}

} // namespace

void intro_dog_draw(SDL_Renderer* ren, const Camera* cam) {
    float fx, fy;
    if (!intro_dog_feet(&fx, &fy)) return;
    const Dog& d = g_dog_s;
    int col;
    float lift = 0;
    if (d.mode == M_SLEEP) { col = DOG_SLEEP + ((int)(g_sleep_t / 0.9f) & 1); lift = SLEEP_SINK; }
    else if (d.mode == M_JOLT) { col = 0; lift = d.mt < 0.12f ? 4.0f : 0.0f; }   // up with a start
    else if (d.mode == M_CARRIED) col = DOG_WALK + (int)(d.t / 0.08f) % 4;   // legs kicking
    else if (d.moving) col = DOG_WALK + (int)(d.t / DOG_STEP) % 4;
    else if (d.mode == M_AT_SHORE && (g_stage < INTRO_READ || g_stage >= INTRO_EMERGE)) col = d.open ? DOG_IDLE_B : 0;
    else if (d.mode == M_WAIT_DOOR) col = DOG_WALK;      // mid-stride: it's running
    else if (d.mode == M_FADE_IN || d.mode == M_FADE_OUT) col = d.fade_col;
    else if (d.mode == M_LOOK) col = 0;
    else col = (int)(d.t / DOG_IDLE) % 2 ? DOG_IDLE_B : 0;
    float z = cam->zoom > 0 ? cam->zoom : 1.0f, w = DOG_CELL * DOG_PX;
    SDL_Rect src = { col * DOG_CELL, d.face * DOG_CELL, DOG_CELL, DOG_CELL };
    SDL_Rect dst = { cam_screen_x(cam, fx - w * 0.5f), cam_screen_y(cam, fy - w - lift), (int)(w * z), (int)(w * z) };
    if (d.mode == M_FADE_OUT)     draw_actor_appearance(ren, g_dog, src, dst, 1.0f - d.mt / ACTOR_APPEAR_T);
    else if (d.mode == M_FADE_IN) draw_actor_appearance(ren, g_dog, src, dst, d.mt / ACTOR_APPEAR_T);
    else SDL_RenderCopy(ren, g_dog, &src, &dst);
    if (d.mode == M_SLEEP) {
        // Z's rising off it, as off a sleeping townsperson -- and the boy:
        // the same size as his (npc_sleep_draw's, a room pixel an art pixel).
        static const unsigned Z[5] = { 31, 2, 4, 8, 31 };
        for (int i = 0; i < 2; i++) {
            float age = fmodf(g_sleep_t + i * 1.0f, 2.0f) / 2.0f;
            draw_glyph(ren, cam, fx + 6 + 3 * sinf(age * 5 + i), fy - 20 - age * 30, Z, 5, 5, age < 0.8f ? 255 : 120, 1.0f);
        }
    } else if (d.mode == M_JOLT) {
        // "!" over its head.
        static const unsigned BANG[6] = { 1, 1, 1, 1, 0, 1 };
        draw_glyph(ren, cam, fx - 1, fy - w - 16 - lift, BANG, 1, 6, 255);
    }
}

// A new game can start the night again in the same run: everything back.
static void intro_reset() {
    g_dawn_t = -1; g_light_t = -1; g_page_t = 0; g_sleep_t = 0; g_wake_pending = false;
    g_boy = B_SLEEP; g_boy_t = 0; g_hand_t = 0; g_fight_pending = false;
    g_taken_t = 0; g_morning_t = 0; g_morning_pending = false;
    g_dog_s = Dog{};
}
