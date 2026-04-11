#include "tilemap.h"
#include "tileset.h"
#include <stdio.h>

bool tileset_load(Tileset* ts, SDL_Renderer* renderer, const char* path,
                  int tile_width, int tile_height) {
    ts->texture = IMG_LoadTexture(renderer, path);
    if (!ts->texture) {
        printf("Failed to load tileset '%s': %s\n", path, IMG_GetError());
        return false;
    }

    ts->tile_width = tile_width;
    ts->tile_height = tile_height;

    int tex_w = 0;
    int tex_h = 0;
    if (SDL_QueryTexture(ts->texture, NULL, NULL, &tex_w, &tex_h) != 0) {
        printf("Failed to query tileset texture: %s\n", SDL_GetError());
        SDL_DestroyTexture(ts->texture);
        ts->texture = NULL;
        return false;
    }

    ts->columns = tex_w / tile_width;
    ts->rows = tex_h / tile_height;

    return true;
}

void tileset_unload(Tileset* ts) {
    if (ts->texture) {
        SDL_DestroyTexture(ts->texture);
        ts->texture = NULL;
    }
}

void tileset_draw_tile(const Tileset* ts, SDL_Renderer* renderer,
                       int tile_id, int screen_x, int screen_y) {
    if (!ts || !ts->texture || tile_id < 0) {
        return;
    }

    SDL_Rect src;
    src.w = 16;
    src.h = 16;
    src.x = (tile_id % ts->columns) * 18 + 1;
    src.y = (tile_id / ts->columns) * 18 + 1;

    SDL_Rect dst = { screen_x, screen_y, TILE_SIZE, TILE_SIZE};

    SDL_RenderCopy(renderer, ts->texture, &src, &dst);
}
