#include "tilemap.h"
#include <stdint.h>
#include <math.h>
#include <string.h>

// ---------------------------------------------------------------------------
// Embedded 8x8 bitmap glyphs — one byte per row, MSB = leftmost pixel
// With TILE_SIZE=32, each bit renders as a 4x4 block.
// ---------------------------------------------------------------------------
static const uint8_t glyph_grass[8]  = {0x00,0x00,0x00,0x00,0x18,0x18,0x00,0x00}; // '.'
static const uint8_t glyph_path[8]   = {0x00,0x00,0x00,0x18,0x18,0x08,0x10,0x00}; // ','
static const uint8_t glyph_tree[8]   = {0xFE,0xFE,0x18,0x18,0x18,0x18,0x18,0x18}; // 'T'
static const uint8_t glyph_water[8]  = {0x62,0x94,0x08,0x62,0x94,0x08,0x62,0x94}; // '~'
static const uint8_t glyph_cliff[8]  = {0x24,0x7E,0x24,0x24,0x7E,0x24,0x00,0x00}; // '#'
static const uint8_t glyph_rock[8]   = {0x3C,0x42,0x81,0x81,0x81,0x42,0x3C,0x00}; // 'o'

struct TileStyle {
    uint8_t bg_r, bg_g, bg_b;
    uint8_t fg_r, fg_g, fg_b;
    const uint8_t* glyph;
};

static const TileStyle tile_styles[] = {
    { 34,  85,  34,  100, 200, 100, glyph_grass  }, // TILE_GRASS
    {120, 100,  60,  180, 155,  90, glyph_path   }, // TILE_PATH
    {  0,  40,   0,    0, 140,   0, glyph_tree   }, // TILE_TREE
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_WATER  (blue ocean)
    { 50,  50,  50,  160, 160, 160, glyph_cliff  }, // TILE_CLIFF   elev 1
    { 75,  65,  55,  155, 135, 115, glyph_rock   }, // TILE_ROCK
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_RIVER  (blue, same as ocean)
    { 30,  90, 200,   80, 160, 255, glyph_water  }, // TILE_HUB    (blue, same as ocean)
    { 75,  72,  68,  180, 178, 174, glyph_cliff  }, // TILE_CLIFF_2 elev 2
    {100,  95,  88,  195, 192, 186, glyph_cliff  }, // TILE_CLIFF_3 elev 3
    {125, 118, 108,  210, 206, 198, glyph_cliff  }, // TILE_CLIFF_4 elev 4
    {155, 145, 132,  225, 220, 212, glyph_cliff  }, // TILE_CLIFF_5 elev 5
};

static const int NUM_TILE_STYLES = (int)(sizeof(tile_styles) / sizeof(tile_styles[0]));

// Shared between phase1 and phase2 — computed once after rivers are placed.
static bool  cliff_blocked[MAP_HEIGHT][MAP_WIDTH];
static float s_cliff_dir_x, s_cliff_dir_y, s_cliff_dir_len;

// ---------------------------------------------------------------------------

static bool in_bounds(int x, int y) {
    return x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT;
}

// Simple deterministic LCG noise — returns 0..32767
static int tile_noise(int x, int y, int seed) {
    unsigned int n = (unsigned int)(x * 1619 + y * 31337 + seed * 3571);
    n = (n ^ (n >> 13)) * 1664525u + 1013904223u;
    return (int)((n >> 16) & 0x7FFF);
}

// Place `count` tiles of `type` on GRASS cells, seeded RNG
static void scatter(Tilemap* map, int type, int count, unsigned int seed) {
    for (int i = 0; i < count; i++) {
        seed = seed * 1664525u + 1013904223u;
        int x = 1 + (int)((seed >> 16) % (MAP_WIDTH  - 2));
        seed = seed * 1664525u + 1013904223u;
        int y = 1 + (int)((seed >> 16) % (MAP_HEIGHT - 2));
        if (map->tiles[y][x] == TILE_GRASS)
            map->tiles[y][x] = type;
    }
}

// Paints a filled circle brush at (ix, iy), skipping the guard zone.
static void paint_river_brush(Tilemap* map, int ix, int iy, int brush_r,
                              int guard_cx, int guard_cy, int guard_r)
{
    for (int by = -brush_r; by <= brush_r; by++) {
        for (int bx = -brush_r; bx <= brush_r; bx++) {
            if (bx*bx + by*by > brush_r*brush_r) continue;
            int px = ix + bx, py = iy + by;
            if (!in_bounds(px, py)) continue;
            if (abs(px - guard_cx) <= guard_r && abs(py - guard_cy) <= guard_r) continue;
            map->tiles[py][px] = TILE_RIVER;
        }
    }
}

// March a river from (sx,sy) in direction (dir_x,dir_y).
// Always advances 1 tile per step along the primary axis — guarantees the
// river reaches the map edge. Perpendicular axis gets ±4 random jitter,
// matching the style of the guaranteed west river.
// depth=0: main river (can spawn branches), depth=1: branch (no further branching)
static void march_river(Tilemap* map, int sx, int sy,
                        float dir_x, float dir_y,
                        unsigned int seed,
                        int guard_cx, int guard_cy, int guard_r,
                        int brush_r,
                        int max_steps,
                        int jitter_range,
                        int depth)
{
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float base_angle = atan2f(dir_y, dir_x);

    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    int steps = 0;
    float smooth_j = 0.0f;

    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(seed >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 0 || rx >= MAP_WIDTH) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 1)             ry = 1;
            if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT - 2;
        } else {
            ry += sign_y;
            if (ry < 0 || ry >= MAP_HEIGHT) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 1)            rx = 1;
            if (rx >= MAP_WIDTH-1) rx = MAP_WIDTH - 2;
        }

        paint_river_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r);

        // Very rarely spawn a thin branch off this river (main rivers only)
        if (depth == 0 && (seed >> 16) % 1000 == 0) {
            seed = seed * 1664525u + 1013904223u;
            // Branch veers off at ±25°–65° from the river's base direction
            float side    = ((seed >> 31) ? 1.0f : -1.0f);
            float offset  = (25.0f + (float)((seed >> 16) % 40)) * 3.14159f / 180.0f;
            float bangle  = base_angle + side * offset;
            float bdx = cosf(bangle), bdy = sinf(bangle);

            seed = seed * 1664525u + 1013904223u;
            int blen = 150 + (int)((seed >> 16) % 250); // 150..399 steps

            march_river(map, rx, ry, bdx, bdy,
                        seed, guard_cx, guard_cy, guard_r,
                        1, blen, jitter_range, 1);
        }
    }
}

// March the west river as a single meandering channel, then fan it into
// 2-4 branches (delta) as it nears the ocean coast.
static void generate_delta_river(Tilemap* map, int sx, int sy,
                                  float dir_x, float dir_y,
                                  unsigned int seed,
                                  int guard_cx, int guard_cy, int guard_r,
                                  int brush_r, int jitter_range)
{
    const float PI = 3.14159265f;
    unsigned int s = seed;

    // Where (in x) to begin fanning — random per seed, well before the coast
    s = s * 1664525u + 1013904223u;
    int delta_x = 600 + (int)((s >> 16) % 400); // 600..999

    // --- Phase 1: single meandering river trunk ---
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    float smooth_j = 0.0f;

    for (int step = 0; step < MAP_WIDTH + MAP_HEIGHT; step++) {
        s = s * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(s >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 0 || rx >= MAP_WIDTH) { rx -= sign_x; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 1)             ry = 1;
            if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT - 2;
        } else {
            ry += sign_y;
            if (ry < 0 || ry >= MAP_HEIGHT) { ry -= sign_y; break; }
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 1)            rx = 1;
            if (rx >= MAP_WIDTH-1) rx = MAP_WIDTH - 2;
        }

        paint_river_brush(map, rx, ry, brush_r, guard_cx, guard_cy, guard_r);

        if (rx <= delta_x) break; // trunk done, start fanning
    }

    // --- Phase 2: fan into delta branches from (rx, ry) ---
    s = s * 1664525u + 1013904223u;
    int num_branches = 2 + (int)((s >> 16) % 3); // 2..4

    s = s * 1664525u + 1013904223u;
    float base_angle = atan2f(dir_y, dir_x);
    // Half-spread: 20°..39° so branches diverge visibly without going vertical
    float spread = (20.0f + (float)((s >> 16) % 20)) * PI / 180.0f;

    for (int b = 0; b < num_branches; b++) {
        // t goes -1..+1 across branches, giving symmetric fan
        float t = (num_branches <= 1) ? 0.0f
                : (float)b / (num_branches - 1) * 2.0f - 1.0f;
        float bangle = base_angle + t * spread;
        float bdx = cosf(bangle);
        float bdy = sinf(bangle);
        s = s * 1664525u + 1013904223u;
        march_river(map, rx, ry, bdx, bdy,
                    s, guard_cx, guard_cy, guard_r,
                    brush_r, MAP_WIDTH + MAP_HEIGHT, jitter_range, 1);
    }
}

// Tiles within this radius of center are generated in phase1.
// Outside is handled by phase2 on a background thread.
#define PHASE_RADIUS 500

static void place_cliffs(Tilemap* map, unsigned int seed,
                         int cx, int cy, int hw,
                         int min_r2, int max_r2)
{
    const int CLIFF_GRID      = 64;
    const int CLIFF_THRESHOLD = 30000;
    // Derive bounding box from max radius so we don't walk all 9M tiles.
    int max_r = (int)sqrtf((float)max_r2) + 1;
    int y_lo = (cy - max_r > 1)           ? cy - max_r : 1;
    int y_hi = (cy + max_r < MAP_HEIGHT-1) ? cy + max_r : MAP_HEIGHT - 1;
    int x_lo = (cx - max_r > 1)           ? cx - max_r : 1;
    int x_hi = (cx + max_r < MAP_WIDTH-1)  ? cx + max_r : MAP_WIDTH  - 1;
    for (int py = y_lo; py < y_hi; py++) {
        for (int px = x_lo; px < x_hi; px++) {
            int ddx = px - cx, ddy = py - cy;
            int r2  = ddx*ddx + ddy*ddy;
            if (r2 < min_r2 || r2 >= max_r2) continue;
            if (map->tiles[py][px] != TILE_GRASS) continue;
            if (cliff_blocked[py][px]) continue;
            if (r2 <= hw*hw) continue;

            int gx = px / CLIFF_GRID,  gy = py / CLIFF_GRID;
            float fx = (float)(px % CLIFF_GRID) / CLIFF_GRID;
            float fy = (float)(py % CLIFF_GRID) / CLIFF_GRID;

            int n00 = tile_noise(gx,   gy,   (int)seed ^ 0xC11F);
            int n10 = tile_noise(gx+1, gy,   (int)seed ^ 0xC11F);
            int n01 = tile_noise(gx,   gy+1, (int)seed ^ 0xC11F);
            int n11 = tile_noise(gx+1, gy+1, (int)seed ^ 0xC11F);

            float top  = n00 + fx * (n10 - n00);
            float bot  = n01 + fx * (n11 - n01);
            int smooth = (int)(top + fy * (bot - top));

            float proj = ((float)px * s_cliff_dir_x + ((float)py - MAP_HEIGHT) * s_cliff_dir_y) / s_cliff_dir_len;
            if (proj < 0.0f) proj = 0.0f;
            if (proj > 1.0f) proj = 1.0f;
            smooth += (int)(proj * 20000);

            if      (smooth >= CLIFF_THRESHOLD + 16000) map->tiles[py][px] = TILE_CLIFF_5;
            else if (smooth >= CLIFF_THRESHOLD + 12000) map->tiles[py][px] = TILE_CLIFF_4;
            else if (smooth >= CLIFF_THRESHOLD +  8000) map->tiles[py][px] = TILE_CLIFF_3;
            else if (smooth >= CLIFF_THRESHOLD +  4000) map->tiles[py][px] = TILE_CLIFF_2;
            else if (smooth >= CLIFF_THRESHOLD)         map->tiles[py][px] = TILE_CLIFF;
        }
    }
}

void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed) {
    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // Grass fill (TILE_GRASS==0)
    memset(map->tiles, 0, sizeof(map->tiles));

    // Hub ring only — everything else is generated in phase2
    int ring_inner = hw - 12, ring_outer = hw + 12;
    for (int dy = -(hw+15); dy <= (hw+15); dy++)
        for (int dx = -(hw+15); dx <= (hw+15); dx++) {
            int d2 = dx*dx + dy*dy;
            if (d2 >= ring_inner*ring_inner && d2 <= ring_outer*ring_outer)
                map->tiles[cy + dy][cx + dx] = TILE_HUB;
        }
}

void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed) {
    const int cx = MAP_WIDTH  / 2;
    const int cy = MAP_HEIGHT / 2;
    const int hw = 90;

    // --- Ocean ---
    {
        static int coast_x[MAP_HEIGHT];
        for (int y = 0; y < MAP_HEIGHT; y++)
            coast_x[y] = 300 + (tile_noise(0, y, 999) % 120);
        float sc = (float)coast_x[0];
        for (int y = 1; y < MAP_HEIGHT; y++) {
            sc = sc * 0.97f + (float)coast_x[y] * 0.03f;
            coast_x[y] = (int)sc;
        }
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x <= coast_x[y]; x++)
                map->tiles[y][x] = TILE_WATER;
    }

    // --- Rivers ---
    const float PI = 3.14159265f;
    int guard_r = hw - 1, brush_r = 6;
    unsigned int cnt_seed = seed * 1664525u + 1013904223u;
    int num_rivers = 5 + (int)((cnt_seed >> 16) % 6);
    cnt_seed = cnt_seed * 1664525u + 1013904223u;
    float global_offset = (cnt_seed >> 16) / (float)0x10000 * 2.0f * PI;
    float spoke_step = 2.0f * PI / num_rivers;

    int west_idx = 0; float best_west = 999.0f;
    for (int i = 0; i < num_rivers; i++) {
        float base = global_offset + i * spoke_step;
        float d = fabsf(fmodf(fabsf(base - PI), 2.0f * PI));
        if (d > PI) d = 2.0f * PI - d;
        if (d < best_west) { best_west = d; west_idx = i; }
    }
    for (int i = 0; i < num_rivers; i++) {
        float base = global_offset + i * spoke_step;
        unsigned int ps = (seed ^ (unsigned int)(0x3333*(i+1))) * 1664525u + 1013904223u;
        float perturb = ((int)(ps >> 16) % 1000 - 500) / 500.0f * spoke_step * 0.35f;
        float angle = base + perturb;
        while (angle >  PI) angle -= 2.0f * PI;
        while (angle < -PI) angle += 2.0f * PI;
        float dx = cosf(angle), dy = sinf(angle);
        int sx = cx + (int)(dx * hw), sy = cy + (int)(dy * hw);
        unsigned int js = (seed ^ (unsigned int)(0x7777*(i+1))) * 1664525u + 1013904223u;
        int jitter_range = (3 + (int)((js >> 16) % 3)) * 6;
        if (i == west_idx) {
            generate_delta_river(map, sx, sy, dx, dy,
                                 seed ^ (unsigned int)(i * 0x1111),
                                 cx, cy, guard_r, brush_r, jitter_range);
        } else {
            int max_steps;
            if (fabsf(dx) >= fabsf(dy) && dx > 0.0f) {
                int half    = (MAP_WIDTH - sx) / 2;
                int three_q = (MAP_WIDTH - sx) * 3 / 4;
                unsigned int ls = (seed ^ (unsigned int)(0x9999*(i+1))) * 1664525u + 1013904223u;
                max_steps = half + (int)((ls >> 16) % (three_q - half + 1));
            } else {
                max_steps = MAP_WIDTH + MAP_HEIGHT;
            }
            march_river(map, sx, sy, dx, dy,
                        seed ^ (unsigned int)(i * 0x1111), cx, cy, guard_r, brush_r,
                        max_steps, jitter_range, 0);
        }
    }

    // --- Trees ---
    for (int y = 1; y < MAP_HEIGHT - 1; y++) {
        for (int x = 1; x < MAP_WIDTH - 1; x++) {
            if (map->tiles[y][x] != TILE_GRASS) continue;
            int ddx = x - cx, ddy = y - cy;
            if (ddx*ddx + ddy*ddy <= hw*hw) continue;
            int n = tile_noise(x, y, (int)seed ^ 7);
            if (n > 30000) map->tiles[y][x] = TILE_TREE;
        }
    }

    // --- Rocks ---
    {
        unsigned int s = seed ^ 0xDEAD1;
        for (int i = 0; i < 72000; i++) {
            s = s * 1664525u + 1013904223u;
            int x = 1 + (int)((s >> 16) % (MAP_WIDTH  - 2));
            s = s * 1664525u + 1013904223u;
            int y = 1 + (int)((s >> 16) % (MAP_HEIGHT - 2));
            int ddx = x - cx, ddy = y - cy;
            if (ddx*ddx + ddy*ddy <= hw*hw) continue;
            if (map->tiles[y][x] == TILE_GRASS) map->tiles[y][x] = TILE_ROCK;
        }
    }

    // --- Cliff gradient direction ---
    {
        unsigned int gs = seed ^ 0xB00B5EED;
        gs = gs * 1664525u + 1013904223u;
        int perim = MAP_WIDTH / 2 + MAP_HEIGHT;
        int pick  = (int)((gs >> 16) % perim);
        float peak_x = (pick < MAP_WIDTH / 2) ? (float)(MAP_WIDTH / 2 + pick) : (float)MAP_WIDTH;
        float peak_y = (pick < MAP_WIDTH / 2) ? 0.0f : (float)(pick - MAP_WIDTH / 2);
        map->cliff_peak_x = peak_x;
        map->cliff_peak_y = peak_y;
        float dir_x = peak_x, dir_y = peak_y - MAP_HEIGHT;
        s_cliff_dir_len = sqrtf(dir_x*dir_x + dir_y*dir_y);
        s_cliff_dir_x = dir_x / s_cliff_dir_len;
        s_cliff_dir_y = dir_y / s_cliff_dir_len;
    }

    // --- Cliff blocked prepass ---
    const int CLIFF_CLEAR = 20;
    memset(cliff_blocked, 0, sizeof(cliff_blocked));
    for (int y = 0; y < MAP_HEIGHT; y++) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int t = map->tiles[y][x];
            if (t != TILE_RIVER && t != TILE_WATER) continue;
            int y0 = y - CLIFF_CLEAR > 0         ? y - CLIFF_CLEAR : 0;
            int y1 = y + CLIFF_CLEAR < MAP_HEIGHT ? y + CLIFF_CLEAR : MAP_HEIGHT - 1;
            int x0 = x - CLIFF_CLEAR > 0         ? x - CLIFF_CLEAR : 0;
            int x1 = x + CLIFF_CLEAR < MAP_WIDTH  ? x + CLIFF_CLEAR : MAP_WIDTH  - 1;
            for (int by = y0; by <= y1; by++)
                for (int bx = x0; bx <= x1; bx++)
                    cliff_blocked[by][bx] = true;
        }
    }

    // --- Cliffs ---
    place_cliffs(map, seed, cx, cy, hw, hw*hw, MAP_WIDTH * MAP_WIDTH);
}

static void draw_tile_ascii(SDL_Renderer* renderer, int tile_id,
    int screen_x, int screen_y, int draw_size) {
    if (tile_id < 0 || tile_id >= NUM_TILE_STYLES) return;

    const TileStyle* s = &tile_styles[tile_id];

    // Fill background
    SDL_SetRenderDrawColor(renderer, s->bg_r, s->bg_g, s->bg_b, 255);
    SDL_Rect bg = { screen_x, screen_y, draw_size, draw_size };
    SDL_RenderFillRect(renderer, &bg);

    // Draw glyph only when tiles are big enough to be readable
    const int scale = draw_size / 8;
    if (scale < 1) return;
    SDL_SetRenderDrawColor(renderer, s->fg_r, s->fg_g, s->fg_b, 255);
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (s->glyph[row] & (0x80u >> col)) {
                SDL_Rect px = {
                    screen_x + col * scale,
                    screen_y + row * scale,
                    scale, scale
                };
                SDL_RenderFillRect(renderer, &px);
            }
        }
    }
}

void tilemap_draw(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer) {
    float z = cam->zoom;
    int draw_size = (int)(TILE_SIZE * z);
    if (draw_size < 1) draw_size = 1;

    int start_x = (int)(cam->x / TILE_SIZE);
    int start_y = (int)(cam->y / TILE_SIZE);
    // How many tiles fit on screen at this zoom level
    int tiles_wide = (int)(cam->screen_w / z / TILE_SIZE) + 2;
    int tiles_tall = (int)(cam->screen_h / z / TILE_SIZE) + 2;
    int end_x = start_x + tiles_wide;
    int end_y = start_y + tiles_tall;

    if (start_x < 0)         start_x = 0;
    if (start_y < 0)         start_y = 0;
    if (end_x > MAP_WIDTH)   end_x = MAP_WIDTH;
    if (end_y > MAP_HEIGHT)  end_y = MAP_HEIGHT;

    for (int y = start_y; y < end_y; y++) {
        for (int x = start_x; x < end_x; x++) {
            int screen_x = (int)((x * TILE_SIZE - cam->x) * z);
            int screen_y = (int)((y * TILE_SIZE - cam->y) * z);
            draw_tile_ascii(renderer, map->tiles[y][x], screen_x, screen_y, draw_size);
        }
    }
}

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y)
{
    // Pick a step size so the minimap fits within 80% of the screen
    int max_dim = (screen_w < screen_h ? screen_w : screen_h) * 4 / 5;
    int step = 1;
    while (MAP_WIDTH / step > max_dim || MAP_HEIGHT / step > max_dim)
        step++;
    const int mw = (MAP_WIDTH  / step);
    const int mh = (MAP_HEIGHT / step);
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    // semi-transparent dark background
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 180);
    SDL_Rect bg = { ox - 4, oy - 4, mw + 8, mh + 8 };
    SDL_RenderFillRect(renderer, &bg);

    // Priority order for block sampling: higher = wins over lower tiles in block.
    // TREE and ROCK have priority 0 so they render as grass (not drawn separately).
    static const int tile_priority[] = { 0, 0, 0, 2, 1, 0, 2, 2, 1, 1, 1, 1 };
    //                                 GRASS PATH TREE WATER CLIFF ROCK RIVER HUB C2 C3 C4 C5
    static const SDL_Color tile_colors[] = {
        { 60, 160,  60, 255}, // GRASS
        { 60, 160,  60, 255}, // PATH   → grass
        { 60, 160,  60, 255}, // TREE   → grass
        { 30,  90, 200, 255}, // WATER
        {100,  95,  88, 255}, // CLIFF   elev 1
        { 60, 160,  60, 255}, // ROCK   → grass
        { 30,  90, 200, 255}, // RIVER
        { 30,  90, 200, 255}, // HUB
        {120, 113, 104, 255}, // CLIFF_2 elev 2
        {140, 132, 120, 255}, // CLIFF_3 elev 3
        {160, 150, 136, 255}, // CLIFF_4 elev 4
        {180, 168, 152, 255}, // CLIFF_5 elev 5
    };
    static const int NUM_MM_COLORS = (int)(sizeof(tile_colors) / sizeof(tile_colors[0]));

    for (int y = 0; y < MAP_HEIGHT; y += step) {
        for (int x = 0; x < MAP_WIDTH; x += step) {
            // Scan the full step×step block, keep highest-priority tile
            int best_id = TILE_GRASS;
            int best_pri = -1;
            int x1 = x + step < MAP_WIDTH  ? x + step : MAP_WIDTH;
            int y1 = y + step < MAP_HEIGHT ? y + step : MAP_HEIGHT;
            for (int by = y; by < y1; by++) {
                for (int bx = x; bx < x1; bx++) {
                    int id = map->tiles[by][bx];
                    if (id >= 0 && id < NUM_MM_COLORS && tile_priority[id] > best_pri) {
                        best_pri = tile_priority[id];
                        best_id  = id;
                    }
                }
            }
            SDL_Color c = tile_colors[best_id];
            SDL_SetRenderDrawColor(renderer, c.r, c.g, c.b, 255);
            SDL_Rect r = { ox + x / step, oy + y / step, 1, 1 };
            SDL_RenderFillRect(renderer, &r);
        }
    }

    // white 3×3 dot for player position
    int px = ox + (int)(player_x / TILE_SIZE) / step;
    int py = oy + (int)(player_y / TILE_SIZE) / step;
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect dot = { px - 1, py - 1, 3, 3 };
    SDL_RenderFillRect(renderer, &dot);

    // red 5×5 dot for cliff gradient peak (debug)
    int peakdot_x = ox + (int)(map->cliff_peak_x) / step;
    int peakdot_y = oy + (int)(map->cliff_peak_y) / step;
    SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
    SDL_Rect peak_dot = { peakdot_x - 2, peakdot_y - 2, 5, 5 };
    SDL_RenderFillRect(renderer, &peak_dot);

    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
}

bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y)
{
    // Mirror the step/offset calculation from minimap_draw exactly
    int max_dim = (screen_w < screen_h ? screen_w : screen_h) * 4 / 5;
    int step = 1;
    while (MAP_WIDTH / step > max_dim || MAP_HEIGHT / step > max_dim)
        step++;
    const int mw = MAP_WIDTH  / step;
    const int mh = MAP_HEIGHT / step;
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    // Check the click is inside the minimap rectangle
    if (mx < ox || mx >= ox + mw || my < oy || my >= oy + mh)
        return false;

    int tile_x = (mx - ox) * step;
    int tile_y = (my - oy) * step;
    *out_world_x = (float)(tile_x * TILE_SIZE);
    *out_world_y = (float)(tile_y * TILE_SIZE);
    return true;
}

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y) {
    if (!in_bounds(tile_x, tile_y)) return false;

    switch (map->tiles[tile_y][tile_x]) {
        case TILE_GRASS:
        case TILE_PATH:
            return true;
        default:
            return false;
    }
}
