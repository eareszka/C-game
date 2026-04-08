#include "tilemap.h"
#include <stdint.h>
#include <math.h>

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
    { 50,  50,  50,  160, 160, 160, glyph_cliff  }, // TILE_CLIFF
    { 75,  65,  55,  155, 135, 115, glyph_rock   }, // TILE_ROCK
    {130,  30, 180,  200,  80, 255, glyph_water  }, // TILE_RIVER  (purple)
    {  0, 180, 220,   80, 220, 255, glyph_water  }, // TILE_HUB    (cyan)
};

static const int NUM_TILE_STYLES = (int)(sizeof(tile_styles) / sizeof(tile_styles[0]));

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

// Carve a sinuous river starting at (sx,sy) outward in direction (dir_x, dir_y).
// guard_cx/cy + guard_r define a no-paint zone around the hub center.
static void carve_river(Tilemap* map, float sx, float sy,
                        float dir_x, float dir_y,
                        int length, unsigned int seed,
                        int guard_cx, int guard_cy, int guard_r)
{
    float x = sx;
    float y = sy;
    float angle = atan2f(dir_y, dir_x);

    for (int i = 0; i < length; i++) {
        seed = seed * 1664525u + 1013904223u;
        float drift = ((int)(seed >> 16) % 100 - 50) * 0.018f;
        angle += drift;
        x += cosf(angle);
        y += sinf(angle);
        int ix = (int)x;
        int iy = (int)y;
        if (!in_bounds(ix, iy)) break;
        // skip tiles inside the hub guard zone
        if (abs(ix - guard_cx) <= guard_r && abs(iy - guard_cy) <= guard_r) continue;
        // paint 2 tiles wide for a thick river look
        map->tiles[iy][ix] = TILE_RIVER;
        if (in_bounds(ix + 1, iy)) map->tiles[iy][ix + 1] = TILE_RIVER;
    }
}

void tilemap_build_starting_area(Tilemap* map, unsigned int seed) {
    // --- Base layer: all grass ---
    for (int y = 0; y < MAP_HEIGHT; y++)
        for (int x = 0; x < MAP_WIDTH; x++)
            map->tiles[y][x] = TILE_GRASS;

    // --- Fixed ocean on the left (constant seed 999 — never changes) ---
    // Coastline wiggles slightly using a fixed noise so it always looks the same.
    for (int y = 0; y < MAP_HEIGHT; y++) {
        int coast_x = 8 + (tile_noise(0, y, 999) % 5);  // 8..12 wide
        for (int x = 0; x <= coast_x; x++)
            map->tiles[y][x] = TILE_WATER;
    }

    // --- Tree clusters via noise (seed-independent density, position varies) ---
    for (int y = 1; y < MAP_HEIGHT - 1; y++) {
        for (int x = 1; x < MAP_WIDTH - 1; x++) {
            if (map->tiles[y][x] != TILE_GRASS) continue;
            int n = tile_noise(x, y, (int)seed ^ 7);
            if (n > 26000)
                map->tiles[y][x] = TILE_TREE;
        }
    }

    // --- Scatter rocks (seed-driven) ---
    scatter(map, TILE_ROCK, 80, seed ^ 0xDEAD1);

    // --- Three rivers from center ---
    int cx = MAP_WIDTH  / 2;
    int cy = MAP_HEIGHT / 2;
    int hw = 3;
    int guard_r = hw - 1; // guard only the interior; ring tiles at hw are painted
                           // so rivers visually connect to the hub outline

    // Compute start point on the hub ring in direction (dx,dy).
    // Uses Chebyshev projection: scale direction until max(|dx|,|dy|) == hw.
    #define RING_START_X(dx) (cx + (dx) * (hw / fmaxf(fabsf(dx), fabsf(dy))))
    #define RING_START_Y(dy) (cy + (dy) * (hw / fmaxf(fabsf(dx), fabsf(dy))))

    // Two seed-driven rivers with a forced 100° gap between them.
    // River A locked to upper sector [-110°, -50°]  (NW..NE)
    // River B locked to lower sector [ +50°, +110°] (SE..SW)
    const float PI = 3.14159265f;
    const float DEG = PI / 180.0f;

    unsigned int sa = (seed ^ 0xAAAAu) * 1664525u + 1013904223u;
    float tA = (sa >> 16) / (float)0x10000;
    float angleA = -110.0f*DEG + tA * 60.0f*DEG;

    unsigned int sb = (seed ^ 0xBBBBu) * 1664525u + 1013904223u;
    float tB = (sb >> 16) / (float)0x10000;
    float angleB =   50.0f*DEG + tB * 60.0f*DEG;

    float dAx = cosf(angleA), dAy = sinf(angleA);
    float dBx = cosf(angleB), dBy = sinf(angleB);

    // Scale each direction to land exactly on the hub ring boundary
    float scaleA = (float)hw / fmaxf(fabsf(dAx), fabsf(dAy));
    float scaleB = (float)hw / fmaxf(fabsf(dBx), fabsf(dBy));

    int reach = 55;
    carve_river(map, cx + dAx*scaleA, cy + dAy*scaleA, dAx, dAy, reach, seed,          cx, cy, guard_r);
    carve_river(map, cx + dBx*scaleB, cy + dBy*scaleB, dBx, dBy, reach, seed ^ 0x1111, cx, cy, guard_r);

    #undef RING_START_X
    #undef RING_START_Y

    // Guaranteed west river: starts at left edge of hub ring (cx-hw, cy).
    {
        unsigned int wseed = seed ^ 0x2222;
        int rx = cx - hw;
        int ry = cy;
        while (rx >= 0) {
            wseed = wseed * 1664525u + 1013904223u;
            int jitter = (int)(wseed >> 16) % 3 - 1; // -1, 0, or +1
            ry += jitter;
            if (ry < 1)             ry = 1;
            if (ry >= MAP_HEIGHT-1) ry = MAP_HEIGHT - 2;
            map->tiles[ry][rx] = TILE_RIVER;
            if (in_bounds(rx, ry + 1)) map->tiles[ry + 1][rx] = TILE_RIVER;
            rx--;
        }
    }

    // --- Hub square outline at center ---
    for (int dy = -hw; dy <= hw; dy++) {
        for (int dx = -hw; dx <= hw; dx++) {
            if (abs(dx) == hw || abs(dy) == hw)
                map->tiles[cy + dy][cx + dx] = TILE_HUB;
        }
    }
}

static void draw_tile_ascii(SDL_Renderer* renderer, int tile_id, int screen_x, int screen_y) {
    if (tile_id < 0 || tile_id >= NUM_TILE_STYLES) return;

    const TileStyle* s = &tile_styles[tile_id];

    // Fill background
    SDL_SetRenderDrawColor(renderer, s->bg_r, s->bg_g, s->bg_b, 255);
    SDL_Rect bg = { screen_x, screen_y, TILE_SIZE, TILE_SIZE };
    SDL_RenderFillRect(renderer, &bg);

    // Draw glyph — each bit in the 8x8 bitmap → (TILE_SIZE/8)² block
    const int scale = TILE_SIZE / 8; // 4 when TILE_SIZE==32
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
    int start_x = (int)(cam->x / TILE_SIZE);
    int start_y = (int)(cam->y / TILE_SIZE);
    int end_x   = start_x + cam->screen_w / TILE_SIZE + 2;
    int end_y   = start_y + cam->screen_h / TILE_SIZE + 2;

    if (start_x < 0)         start_x = 0;
    if (start_y < 0)         start_y = 0;
    if (end_x > MAP_WIDTH)   end_x = MAP_WIDTH;
    if (end_y > MAP_HEIGHT)  end_y = MAP_HEIGHT;

    for (int y = start_y; y < end_y; y++) {
        for (int x = start_x; x < end_x; x++) {
            int screen_x = x * TILE_SIZE - (int)cam->x;
            int screen_y = y * TILE_SIZE - (int)cam->y;
            draw_tile_ascii(renderer, map->tiles[y][x], screen_x, screen_y);
        }
    }
}

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y)
{
    const int SCALE = 2;
    const int mw = MAP_WIDTH  * SCALE;
    const int mh = MAP_HEIGHT * SCALE;
    int ox = (screen_w - mw) / 2;
    int oy = (screen_h - mh) / 2;

    // semi-transparent dark background
    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 180);
    SDL_Rect bg = { ox - 4, oy - 4, mw + 8, mh + 8 };
    SDL_RenderFillRect(renderer, &bg);

    // one colored block per tile type
    static const SDL_Color tile_colors[] = {
        { 60, 160,  60, 255}, // GRASS
        {160, 130,  70, 255}, // PATH
        {  0,  80,   0, 255}, // TREE
        { 30,  90, 200, 255}, // WATER
        { 90,  90,  90, 255}, // CLIFF
        {120, 100,  80, 255}, // ROCK
        {160,  40, 210, 255}, // RIVER
        {  0, 200, 230, 255}, // HUB
    };
    static const int NUM_MM_COLORS = (int)(sizeof(tile_colors) / sizeof(tile_colors[0]));

    for (int y = 0; y < MAP_HEIGHT; y++) {
        for (int x = 0; x < MAP_WIDTH; x++) {
            int id = map->tiles[y][x];
            if (id < 0 || id >= NUM_MM_COLORS) continue;
            SDL_Color c = tile_colors[id];
            SDL_SetRenderDrawColor(renderer, c.r, c.g, c.b, 255);
            SDL_Rect r = { ox + x * SCALE, oy + y * SCALE, SCALE, SCALE };
            SDL_RenderFillRect(renderer, &r);
        }
    }

    // white 3×3 dot for player position
    int px = ox + (int)(player_x / TILE_SIZE) * SCALE;
    int py = oy + (int)(player_y / TILE_SIZE) * SCALE;
    SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255);
    SDL_Rect dot = { px - 1, py - 1, 3, 3 };
    SDL_RenderFillRect(renderer, &dot);

    SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
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
