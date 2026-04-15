#include "overworld.h"
#include "resource_node.h"
#include "collision.h"
#include <math.h>

struct OWCollCtx { const Tilemap* map; const ResourceNodeList* res; };
static bool ow_solid(const void* ctx, float px, float py) {
    const OWCollCtx* c = static_cast<const OWCollCtx*>(ctx);
    return tilemap_pixel_solid(c->map, px, py)
        || resource_node_solid(c->res, px, py);
}

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
                      ResourceNodeList* resources, Tilemap* map, bool noclip)
{
    // Action key — hit nearby resource or map tile
    if (input_pressed(in, SDL_SCANCODE_SPACE)
     || input_pressed(in, SDL_SCANCODE_Z)
     || input_pressed(in, SDL_SCANCODE_RETURN))
    {
        float hx = ow->x + (HB_X1 + HB_X2) * 0.5f;
        float hy = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
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

    float dx, dy;
    player_read_input(player, in, &dx, &dy);

    float anim_speed;
    if (input_down(in, SDL_SCANCODE_LSHIFT))
        { ow->speed = 300.0f; anim_speed = 0.10f; }
    else
        { ow->speed = 150.0f; anim_speed = 0.20f; }

    if (dx != 0.0f || dy != 0.0f) {
        OWCollCtx ctx = { map, resources };
        float nx = ow->x + dx * ow->speed * dt;
        float ny = ow->y + dy * ow->speed * dt;
        float px = ow->x, py = ow->y;
        if (noclip || can_occupy(&ctx, nx, ow->y, ow_solid)) ow->x = nx;
        if (noclip || can_occupy(&ctx, ow->x, ny, ow_solid)) ow->y = ny;
        if (ow->x == px && ow->y == py) player->is_moving = 0;
    }

    // Dungeon entrance detection
    {
        float feet_x = ow->x + (HB_X1 + HB_X2) * 0.5f;
        float feet_y = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
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

    player_animate(player, dt, anim_speed);
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

    // Debug: draw hitbox
    SDL_Rect hb = {
        sx + (int)(HB_X1 * z),
        sy + (int)(HB_Y1 * z),
        (int)((HB_X2 - HB_X1) * z),
        (int)((HB_Y2 - HB_Y1) * z)
    };
    SDL_SetRenderDrawColor(ren, 255, 0, 255, 255);
    SDL_RenderDrawRect(ren, &hb);
}
