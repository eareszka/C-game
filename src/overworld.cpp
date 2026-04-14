#include "overworld.h"
#include "resource_node.h"
#include <math.h>

static const int down_cycle[4]  = {1, 0, 2, 0};
static const int up_cycle[4]    = {4, 3, 5, 3};
static const int left_cycle[2]  = {7, 6};
static const int right_cycle[2] = {9, 8};

void overworld_init(Overworld* ow, Player* player, float x, float y)
{
    ow->x     = x;
    ow->y     = y;
    ow->speed = 150.0f;

    player->width  = 32;
    player->height = 48;
    player->facing = 0;
    player->facing_locked = 0;
    player->anim_step  = 0;
    player->anim_timer = 0.0f;
    player->is_moving  = 0;
}

void overworld_update(Overworld* ow, Player* player, const Input* in, float dt,
                      ResourceNodeList* resources, Tilemap* map)
{
    float dx = 0.0f;
    float dy = 0.0f;
    float anim_speed = 0.15f;

    player->is_moving = 0;

    if ((input_pressed(in, SDL_SCANCODE_SPACE))
     || (input_pressed(in, SDL_SCANCODE_Z))
     || (input_pressed(in, SDL_SCANCODE_RETURN)))
    {
        float hx = ow->x + player->width  * 0.5f;
        float hy = ow->y + player->height - 8.0f;
        float rx, ry;
        int rn_hit  = resource_nodes_try_hit(resources, hx, hy, 40, &rx, &ry);
        int map_hit = !rn_hit && tilemap_try_hit(map, hx, hy, 40, &rx, &ry);

        if (rn_hit == 1) {
            for (int i = 0; i < resources->count; i++) {
                ResourceNode* n = &resources->nodes[i];
                if (n->type == RESOURCE_GRAVESTONE &&
                    !n->alive && n->hides_entrance && n->reveal_tx >= 0) {
                    map->tiles[n->reveal_ty][n->reveal_tx] = n->reveal_tile_id;
                    map->overlay[n->reveal_ty][n->reveal_tx] = 0;
                    n->reveal_tx = -1;
                }
            }
        }
        if (rn_hit || map_hit) {
            float ddx = rx - hx;
            float ddy = ry - hy;
            if (ddx * ddx >= ddy * ddy)
                player->facing = ddx >= 0.0f ? 8 : 6;
            else
                player->facing = ddy >= 0.0f ? 0 : 3;
            player->facing_locked = 1;
        }
    }

    if (input_pressed(in, SDL_SCANCODE_LEFT)  || input_pressed(in, SDL_SCANCODE_A) ||
        input_pressed(in, SDL_SCANCODE_RIGHT) || input_pressed(in, SDL_SCANCODE_D) ||
        input_pressed(in, SDL_SCANCODE_UP)    || input_pressed(in, SDL_SCANCODE_W) ||
        input_pressed(in, SDL_SCANCODE_DOWN)  || input_pressed(in, SDL_SCANCODE_S))
        player->facing_locked = 0;

    if (input_down(in, SDL_SCANCODE_LEFT)  || input_down(in, SDL_SCANCODE_A))
        { dx -= 1.0f; if (!player->facing_locked) player->facing = 6; player->is_moving = 1; }
    if (input_down(in, SDL_SCANCODE_RIGHT) || input_down(in, SDL_SCANCODE_D))
        { dx += 1.0f; if (!player->facing_locked) player->facing = 8; player->is_moving = 1; }
    if (input_down(in, SDL_SCANCODE_UP)    || input_down(in, SDL_SCANCODE_W))
        { dy -= 1.0f; if (!player->facing_locked) player->facing = 3; player->is_moving = 1; }
    if (input_down(in, SDL_SCANCODE_DOWN)  || input_down(in, SDL_SCANCODE_S))
        { dy += 1.0f; if (!player->facing_locked) player->facing = 0; player->is_moving = 1; }

    if (input_down(in, SDL_SCANCODE_LSHIFT))
        { ow->speed = 300.0f; anim_speed = 0.10f; }
    else
        { ow->speed = 150.0f; anim_speed = 0.20f; }

    if (dx != 0.0f || dy != 0.0f) {
        float len = sqrtf(dx * dx + dy * dy);
        dx /= len;
        dy /= len;
        ow->x += dx * ow->speed * dt;
        ow->y += dy * ow->speed * dt;
    }

    // Dungeon entrance detection
    {
        float feet_x = ow->x + player->width  * 0.5f;
        float feet_y = ow->y + player->height - 8.0f;
        int tx = (int)(feet_x / TILE_SIZE);
        int ty = (int)(feet_y / TILE_SIZE);
        ow->at_dungeon_entrance = 0;
        if (tx >= 0 && tx < MAP_WIDTH && ty >= 0 && ty < MAP_HEIGHT) {
            int tile = map->tiles[ty][tx];
            if (tile == TILE_DUNGEON || (tile >= TILE_DUNGEON_CAVE && tile <= TILE_DUNGEON_LARGE_TREE)) {
                ow->at_dungeon_entrance = 1;
                for (int i = 0; i < map->num_dungeon_entrances; i++) {
                    const DungeonEntrance& e = map->dungeon_entrances[i];
                    if (tx >= e.x && tx < e.x + e.size + 1 &&
                        ty >= e.y && ty < e.y + e.size + 1) {
                        ow->dungeon_type       = e.type;
                        ow->dungeon_difficulty = e.difficulty;
                        break;
                    }
                }
            }
        }
    }

    // Animation
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

void player_draw(const Player* player, float world_x, float world_y,
                 const Camera* cam, SDL_Renderer* ren, SDL_Texture* sprite)
{
    float z  = cam->zoom;
    int sx = (int)((world_x - cam->x) * z);
    int sy = (int)((world_y - cam->y) * z);

    int frame;
    if (player->facing >= 8)
        frame = player->is_moving ? right_cycle[player->anim_step % 2] : player->facing;
    else if (player->facing >= 6)
        frame = player->is_moving ? left_cycle[player->anim_step % 2]  : player->facing;
    else if (player->facing >= 3)
        frame = player->is_moving ? up_cycle[player->anim_step]        : player->facing;
    else
        frame = player->is_moving ? down_cycle[player->anim_step]      : player->facing;

    SDL_Rect src = { frame * 16, 0, 16, 24 };
    SDL_Rect dst = { sx, sy, (int)(player->width * z), (int)(player->height * z) };
    SDL_RenderCopy(ren, sprite, &src, &dst);
}
