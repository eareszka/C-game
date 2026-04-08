#ifndef OVERWORLD_H
#define OVERWORLD_H

#include <SDL2/SDL.h>
#include "input.h"
#include "camera.h"
#include "resource_node.h"

typedef enum Direction {
    DIR_DOWN = 0,
    DIR_UP = 1,
    DIR_LEFT = 2,
    DIR_RIGHT = 3
} Direction;

typedef struct Overworld {
    float x, y;
    float speed;
    int width;
    int height;

    Direction facing;
    int anim_step;         // 0, 1, 2 within the row
    float anim_timer;
    int is_moving;
} Overworld;

void overworld_init(Overworld* ow, float x, float y, float speed, int width, int height);
void overworld_update(Overworld* ow, const Input* in, float dt, ResourceNodeList* resources);
void overworld_draw(const Overworld* ow, const Camera* cam, SDL_Renderer* ren, SDL_Texture* player_sprite);

#endif
