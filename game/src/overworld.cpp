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

    ow->facing = 0; // idle down
    ow->facing_locked = 0;
    ow->anim_step = 0;
    ow->anim_timer = 0.0f;
    ow->is_moving = 0;
}


void overworld_update(Overworld* ow, const Input* in, float dt, ResourceNodeList* resources, Tilemap* map) {
    float dx = 0.0f;
    float dy = 0.0f;
    float anim_speed = 0.15f;

    ow->is_moving = 0;

    if ((input_pressed(in, SDL_SCANCODE_SPACE))
     || (input_pressed(in, SDL_SCANCODE_Z))
     || (input_pressed(in, SDL_SCANCODE_RETURN)))
    {
        float hx = ow->x + ow->width  * 0.5f;
        float hy = ow->y + ow->height - 8.0f;
        float rx, ry;
        int rn_hit  = resource_nodes_try_hit(resources, hx, hy, 40, &rx, &ry);
        int map_hit = !rn_hit && tilemap_try_hit(map, hx, hy, 40, &rx, &ry);
        if (rn_hit || map_hit) {
            float ddx = rx - hx;
            float ddy = ry - hy;
            if (ddx * ddx >= ddy * ddy)
                ow->facing = ddx >= 0.0f ? 8 : 6;  // right : left
            else
                ow->facing = ddy >= 0.0f ? 0 : 3;  // down : up
            ow->facing_locked = 1;
        }
    }

    // A newly pressed movement key unlocks facing
    if (input_pressed(in, SDL_SCANCODE_LEFT)  || input_pressed(in, SDL_SCANCODE_A) ||
        input_pressed(in, SDL_SCANCODE_RIGHT) || input_pressed(in, SDL_SCANCODE_D) ||
        input_pressed(in, SDL_SCANCODE_UP)    || input_pressed(in, SDL_SCANCODE_W) ||
        input_pressed(in, SDL_SCANCODE_DOWN)  || input_pressed(in, SDL_SCANCODE_S))
        ow->facing_locked = 0;

    //handles movement
    if ((input_down(in, SDL_SCANCODE_LEFT))||(input_down(in, SDL_SCANCODE_A)))
    {
        dx -= 1.0f;
        if (!ow->facing_locked) ow->facing = 6;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_RIGHT))||(input_down(in, SDL_SCANCODE_D)))
    {
        dx += 1.0f;
        if (!ow->facing_locked) ow->facing = 8;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_UP))||(input_down(in, SDL_SCANCODE_W)))
    {
        dy -= 1.0f;
        if (!ow->facing_locked) ow->facing = 3;
        ow->is_moving = 1;
    }
    if ((input_down(in, SDL_SCANCODE_DOWN))||(input_down(in, SDL_SCANCODE_S)))
    {
        dy += 1.0f;
        if (!ow->facing_locked) ow->facing = 0;
        ow->is_moving = 1;
    }
    if (input_down(in, SDL_SCANCODE_LSHIFT))
    {
        ow->speed = 300.0f;
        anim_speed = .10;
    }
    else
    {
        ow->speed = 150.0f;
        anim_speed = .20;
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

        if (ow->anim_timer >= anim_speed) {
            ow->anim_timer = 0.0f;

            ow->anim_step = (ow->anim_step + 1) % 4;
        }
    } else {
        ow->anim_step = 0;
        ow->anim_timer = 0.0f;
    }
}

void overworld_draw(const Overworld* ow, const Camera* cam, SDL_Renderer* ren, SDL_Texture* player_sprite) {
    float z = cam->zoom;
    int screen_x = (int)((ow->x - cam->x) * z);
    int screen_y = (int)((ow->y - cam->y) * z);

    int frame_index;
    if (ow->facing >= 8)
        frame_index = ow->is_moving ? right_cycle[ow->anim_step % 2] : ow->facing;
    else if (ow->facing >= 6)
        frame_index = ow->is_moving ? left_cycle[ow->anim_step % 2] : ow->facing;
    else if (ow->facing >= 3)
        frame_index = ow->is_moving ? up_cycle[ow->anim_step] : ow->facing;
    else
        frame_index = ow->is_moving ? down_cycle[ow->anim_step] : ow->facing;

    SDL_Rect src = {
        frame_index * 16,
        0,
        16,
        24
    };

    SDL_Rect dst = {
        screen_x,
        screen_y,
        (int)(ow->width  * z),
        (int)(ow->height * z)
    };

    SDL_RenderCopy(ren, player_sprite, &src, &dst);
}
