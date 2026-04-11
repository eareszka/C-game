#include "tilemap.h"
#include "tileset.h"
#include <stdio.h>
#include <stdint.h>

// ---------------------------------------------------------------------------
// Embedded 8x8 bitmap glyphs — one byte per row, MSB = leftmost pixel
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
    { 10,  10,  90,   50, 110, 220, glyph_water  }, // TILE_WATER
    { 50,  50,  50,  160, 160, 160, glyph_cliff  }, // TILE_CLIFF
    { 75,  65,  55,  155, 135, 115, glyph_rock   }, // TILE_ROCK
};

static const int NUM_TILE_STYLES = (int)(sizeof(tile_styles) / sizeof(tile_styles[0]));

// ---------------------------------------------------------------------------

bool tileset_load(Tileset* ts, SDL_Renderer* renderer, const char* path,
                  int tile_width, int tile_height) {
    ts->texture = IMG_LoadTexture(renderer, path);
    if (!ts->texture) {
        printf("Tileset '%s' not found — using ASCII placeholders\n", path);
        ts->tile_width  = tile_width;
        ts->tile_height = tile_height;
        ts->columns     = 0;
        ts->rows        = 0;
        return false;
    }

    ts->tile_width  = tile_width;
    ts->tile_height = tile_height;

    int tex_w = 0, tex_h = 0;
    if (SDL_QueryTexture(ts->texture, NULL, NULL, &tex_w, &tex_h) != 0) {
        printf("Failed to query tileset texture: %s\n", SDL_GetError());
        SDL_DestroyTexture(ts->texture);
        ts->texture = NULL;
        return false;
    }

    ts->columns = tex_w / tile_width;
    ts->rows    = tex_h / tile_height;

    return true;
}

void tileset_unload(Tileset* ts) {
    if (ts->texture) {
        SDL_DestroyTexture(ts->texture);
        ts->texture = NULL;
    }
}

void tileset_draw_tile_ascii(SDL_Renderer* renderer, int tile_id,
                             int screen_x, int screen_y) {
    if (tile_id < 0 || tile_id >= NUM_TILE_STYLES) return;

    const TileStyle* s = &tile_styles[tile_id];

    // Fill background
    SDL_SetRenderDrawColor(renderer, s->bg_r, s->bg_g, s->bg_b, 255);
    SDL_Rect bg = { screen_x, screen_y, TILE_SIZE, TILE_SIZE };
    SDL_RenderFillRect(renderer, &bg);

    // Draw glyph — each bit in the 8x8 bitmap → (TILE_SIZE/8)² block
    const int scale = TILE_SIZE / 8; // 2 when TILE_SIZE==16
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

void tileset_draw_tile(const Tileset* ts, SDL_Renderer* renderer,
                       int tile_id, int screen_x, int screen_y) {
    if (!ts || tile_id < 0) return;

    if (!ts->texture) {
        tileset_draw_tile_ascii(renderer, tile_id, screen_x, screen_y);
        return;
    }

    SDL_Rect src;
    src.w = 16;
    src.h = 16;
    src.x = (tile_id % ts->columns) * 18 + 1;
    src.y = (tile_id / ts->columns) * 18 + 1;

    SDL_Rect dst = { screen_x, screen_y, TILE_SIZE, TILE_SIZE };

    SDL_RenderCopy(renderer, ts->texture, &src, &dst);
}
