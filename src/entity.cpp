#include "entity.h"
#include <math.h>

void player_read_input(Player* player, const Input* in, float* out_dx, float* out_dy)
{
    float dx = 0.0f, dy = 0.0f;
    player->is_moving = 0;

    // Update last-pressed direction and unlock facing on new key
    if (input_pressed(in, SDL_SCANCODE_LEFT)  || input_pressed(in, SDL_SCANCODE_A))  { player->last_hdir = -1; player->facing_locked = 0; }
    if (input_pressed(in, SDL_SCANCODE_RIGHT) || input_pressed(in, SDL_SCANCODE_D))  { player->last_hdir =  1; player->facing_locked = 0; }
    if (input_pressed(in, SDL_SCANCODE_UP)    || input_pressed(in, SDL_SCANCODE_W))  { player->last_vdir = -1; player->facing_locked = 0; }
    if (input_pressed(in, SDL_SCANCODE_DOWN)  || input_pressed(in, SDL_SCANCODE_S))  { player->last_vdir =  1; player->facing_locked = 0; }

    bool left  = input_down(in, SDL_SCANCODE_LEFT)  || input_down(in, SDL_SCANCODE_A);
    bool right = input_down(in, SDL_SCANCODE_RIGHT) || input_down(in, SDL_SCANCODE_D);
    bool up    = input_down(in, SDL_SCANCODE_UP)    || input_down(in, SDL_SCANCODE_W);
    bool down  = input_down(in, SDL_SCANCODE_DOWN)  || input_down(in, SDL_SCANCODE_S);

    if (left && right) { dx = (float)player->last_hdir; }
    else if (left)     { dx = -1.0f; player->last_hdir = -1; }
    else if (right)    { dx =  1.0f; player->last_hdir =  1; }

    if (up && down)    { dy = (float)player->last_vdir; }
    else if (up)       { dy = -1.0f; player->last_vdir = -1; }
    else if (down)     { dy =  1.0f; player->last_vdir =  1; }

    if (!player->facing_locked) {
        if (dx < 0.0f) player->facing = 6;
        if (dx > 0.0f) player->facing = 8;
        if (dy < 0.0f) player->facing = 3;
        if (dy > 0.0f) player->facing = 0;
    }

    if (dx != 0.0f || dy != 0.0f) {
        float len = sqrtf(dx * dx + dy * dy);
        dx /= len;
        dy /= len;
        player->is_moving = 1;
    }

    *out_dx = dx;
    *out_dy = dy;
}

void player_animate(Player* player, float dt, float anim_speed)
{
    if (player->is_moving) {
        player->anim_timer += dt;
        if (player->anim_timer >= anim_speed) {
            player->anim_timer = 0.0f;
            player->anim_step  = (player->anim_step + 1) % 4;
        }
    } else {
        player->anim_step  = 0;
        player->anim_timer = 0.0f;
    }
}
