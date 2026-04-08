#ifndef TILESET_H
#define TILESET_H

#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>

typedef struct Tileset {
    SDL_Texture* texture;
    int tile_width;
    int tile_height;
    int columns;
    int rows;
} Tileset;

bool tileset_load(Tileset* ts, SDL_Renderer* renderer, const char* path,
                  int tile_width, int tile_height);

void tileset_unload(Tileset* ts);

void tileset_draw_tile(const Tileset* ts, SDL_Renderer* renderer,
                       int tile_id, int screen_x, int screen_y);

void tileset_draw_tile_ascii(SDL_Renderer* renderer, int tile_id,
                             int screen_x, int screen_y);

#endif
