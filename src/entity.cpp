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

    if (!player->facing_locked && (dx != 0.0f || dy != 0.0f))
        player->facing = facing_from(dx, dy);

    if (dx != 0.0f || dy != 0.0f) {
        float len = sqrtf(dx * dx + dy * dy);
        dx /= len;
        dy /= len;
        player->is_moving = 1;
    }

    *out_dx = dx;
    *out_dy = dy;
}

int facing_from(float dx, float dy)
{
    if (dy > 0.0f) return dx < 0.0f ? FACE_DOWN_LEFT : dx > 0.0f ? FACE_DOWN_RIGHT : FACE_DOWN;
    if (dy < 0.0f) return dx < 0.0f ? FACE_UP_LEFT   : dx > 0.0f ? FACE_UP_RIGHT   : FACE_UP;
    return dx < 0.0f ? FACE_LEFT : FACE_RIGHT;
}

int facing_toward(float dx, float dy)
{
    // An axis counts only when it is more than tan(22.5 deg) of the other,
    // which splits the circle into eight equal 45-degree sectors.
    const float T = 0.41421356f;
    float ax = fabsf(dx), ay = fabsf(dy);
    return facing_from(ax > T * ay ? dx : 0.0f, ay > T * ax ? dy : 0.0f);
}

int player_frame(const Player* player)
{
    int f = player->facing;
    if (!player->is_moving) return f;
    if (f == FACE_LEFT || f == FACE_RIGHT) {
        int stride2 = f == FACE_LEFT ? STRIDE2_LEFT : STRIDE2_RIGHT;
        const int side4[4] = {f + 1, f, stride2, f}; // stride, pass, other stride, pass
        return side4[player->anim_step % 4];
    }
    static const int step3[4] = {1, 0, 2, 0};       // step A, idle, step B, idle
    return f + step3[player->anim_step % 4];
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

bool player_crouching(const Input* in)
{
    return input_down(in, SDL_SCANCODE_LCTRL);
}

bool player_sprinting(const Input* in)
{
    return input_down(in, SDL_SCANCODE_LSHIFT) && !player_crouching(in);
}

void player_gait(const Input* in, float* speed, float* anim_speed)
{
    if (player_crouching(in))      { *speed = PLAYER_CROUCH_SPEED; *anim_speed = 0.30f; }
    else if (player_sprinting(in)) { *speed = PLAYER_RUN_SPEED;    *anim_speed = 0.10f; }
    else                           { *speed = PLAYER_WALK_SPEED;   *anim_speed = 0.20f; }
}

const char* part_name(int part)
{
    switch (part) {
        case PART_HIDE:    return "HIDE";
        case PART_BONE:    return "BONE";
        case PART_ESSENCE: return "ESSENCE";
        case PART_VINE:    return "VINE";
        default:           return "?";
    }
}

int exp_for_level(int level)
{
    if (level <= 1) return 0;
    return (int)(100.0f * powf((float)(level - 1), 1.6f) + 0.5f);
}

float level_damage_mult(int level)
{
    return 1.0f + 0.05f * (level - 1);
}

int player_gain_exp(Player* p, int amount)
{
    p->stats.exp += amount;
    int gained = 0;
    while (p->stats.exp >= exp_for_level(p->level + 1)) {
        p->level++;
        p->stats.max_hp += HP_PER_BAR;
        p->stats.hp = p->stats.max_hp;
        gained++;
    }
    return gained;
}
