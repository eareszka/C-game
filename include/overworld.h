#ifndef OVERWORLD_H
#define OVERWORLD_H

#include <SDL2/SDL.h>
#include "input.h"
#include "camera.h"
#include "resource_node.h"
#include "tilemap.h"

typedef struct Overworld {
    float x, y;
    float speed;
    int width;
    int height;

    int facing;            // idle sprite frame index: 0=down, 3=up, 6=left, 8=right
    int facing_locked;     // true after a hit, until player presses a new direction
    int anim_step;         // 0, 1, 2 within the row
    float anim_timer;
    int is_moving;
} Overworld;

void overworld_init(Overworld* ow, float x, float y, float speed, int width, int height);
void overworld_update(Overworld* ow, const Input* in, float dt, ResourceNodeList* resources, Tilemap* map);
void overworld_draw(const Overworld* ow, const Camera* cam, SDL_Renderer* ren, SDL_Texture* player_sprite);

#endif
