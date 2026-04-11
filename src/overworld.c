#include "overworld.h"
#include "resource_node.h"
#include <math.h>

static const int down_cycle[4]  = {1, 0, 2, 0};
static const int up_cycle[4]    = {4, 3, 5, 3};
static const int left_cycle[2]  = {7, 6};
static const int right_cycle[2] = {9, 8};

void overworld_init(Overworld* ow, float x, float y, float speed, int width, int height) 
{
    ow->x = x;
    ow->y = y;
    ow->speed = speed;
    ow->width = width;
    ow->height = height;

    ow->facing = DIR_DOWN;
    ow->anim_step = 0;
    ow->anim_timer = 0.0f;
    ow->is_moving = 0;
}


void overworld_update(Overworld* ow, const Input* in, float dt, ResourceNodeList* resources) {
    float dx = 0.0f;
    float dy = 0.0f;

    ow->is_moving = 0;
    
    //handles movement
    if ((input_down(in, SDL_SCANCODE_LEFT))||(input_down(in, SDL_SCANCODE_A))) 
    {
        dx -= 1.0f;
        ow->facing = DIR_LEFT;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_RIGHT))||(input_down(in, SDL_SCANCODE_D))) 
    {
        dx += 1.0f;
        ow->facing = DIR_RIGHT;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_UP))||(input_down(in, SDL_SCANCODE_W))) 
    {
        dy -= 1.0f;
        ow->facing = DIR_UP;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_DOWN))||(input_down(in, SDL_SCANCODE_S))) 
    {
        dy += 1.0f;
        ow->facing = DIR_DOWN;
        ow->is_moving = 1;
    }

    if (dx != 0.0f || dy != 0.0f) {
        float len = sqrtf(dx * dx + dy * dy);
        dx /= len;
        dy /= len;

        ow->x += dx * ow->speed * dt;
        ow->y += dy * ow->speed * dt;
    }

    //walking animation
    if (ow->is_moving) {
        ow->anim_timer += dt;

        if (ow->anim_timer >= 0.15f) {
            ow->anim_timer = 0.0f;

            ow->anim_step = (ow->anim_step + 1) % 4;
        }
    } else {
        ow->anim_step = 0;
        ow->anim_timer = 0.0f;
    }

    if ((input_down(in, SDL_SCANCODE_SPACE))||(input_down(in, SDL_SCANCODE_Z))||(input_down(in, SDL_SCANCODE_RETURN))) 
    {
        resource_nodes_try_hit(resources, ow->x, ow->y, 40);
    }
}

void overworld_draw(const Overworld* ow, const Camera* cam, SDL_Renderer* ren, SDL_Texture* player_sprite) {
    int screen_x = (int)(ow->x - cam->x);
    int screen_y = (int)(ow->y - cam->y);

    int frame_index = 0;

    switch (ow->facing) {
        case DIR_DOWN:
            frame_index = ow->is_moving ? down_cycle[ow->anim_step] : 0;
            break;
        case DIR_UP:
            frame_index = ow->is_moving ? up_cycle[ow->anim_step] : 3;
            break;
        case DIR_LEFT:
            frame_index = ow->is_moving ? left_cycle[ow->anim_step % 2] : 6;
            break;
        case DIR_RIGHT:
            frame_index = ow->is_moving ? right_cycle[ow->anim_step % 2] : 8;
            break;
    }

    SDL_Rect src = {
        frame_index * 16,
        0,
        16,
        24
    };

    SDL_Rect dst = {
        screen_x,
        screen_y,
        ow->width,
        ow->height
    };

    SDL_RenderCopy(ren, player_sprite, &src, &dst);
}
