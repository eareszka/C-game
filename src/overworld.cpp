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
    ow->x       = x;
    ow->y       = y;
    ow->speed   = 150.0f;
    ow->at_dungeon_entrance = 0;
    ow->at_interior_door    = 0;
    ow->interior_door_idx   = -1;
    ow->swing               = WeaponSwingState();

    player->equipped_weapon = WEAPON_KNIFE;
    player->width  = 32;
    player->height = 48;
    player->facing = 0;
    player->facing_locked = 0;
    player->anim_step  = 0;
    player->anim_timer = 0.0f;
    player->is_moving  = 0;
}

void overworld_update(Overworld* ow, Player* player, const Input* in, float dt,
                      ResourceNodeList* resources, Tilemap* map, const Camera* cam,
                      bool noclip, HarvestResult* out_harvest)
{
    // Standing on a door or dungeon entrance, the interact key belongs to the
    // ENTER prompt, so don't also swing at whatever is beside the doorway. The
    // at_* flags were computed at the end of the previous call, which is what we
    // want: they describe the tile the player is standing on right now, before
    // this frame's movement. Graveyards are unaffected — a hidden entrance is
    // not an entrance tile until a gravestone reveals it, so the tool still
    // works for every hit that does the revealing.
    bool at_prompt = ow->at_dungeon_entrance || ow->at_interior_door;

    float hx = ow->x + (HB_X1 + HB_X2) * 0.5f;
    float hy = ow->y + (HB_Y1 + HB_Y2) * 0.5f;

    HarvestResult local = {};
    HarvestResult* h = out_harvest ? out_harvest : &local;

    weapon_swing_update(&ow->swing, player, in, dt, hx, hy, resources, map,
                       cam, at_prompt, h);

    // Any destroyed gravestone may have been hiding a dungeon entrance.
    if (harvest_any_destroyed(h)) {
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

    float dx = 0.0f, dy = 0.0f;
    if (!weapon_swing_frozen_tick(&ow->swing, player, dt))
        player_read_input(player, in, &dx, &dy);

    float anim_speed;
    if (input_down(in, SDL_SCANCODE_LSHIFT))
        { ow->speed = 300.0f; anim_speed = 0.10f; }
    else
        { ow->speed = 150.0f; anim_speed = 0.20f; }

    if (dx != 0.0f || dy != 0.0f) {
        OWCollCtx ctx = { map, resources };
        if (noclip) {
            ow->x += dx * ow->speed * dt;
            ow->y += dy * ow->speed * dt;
        } else {
            // Asked before the move rather than after it, so that a player who
            // is somewhere they cannot be gets out by walking, which is the
            // only thing they will think to try.
            unwedge_feet(&ctx, &ow->x, &ow->y, ow_solid);
            if (!move_feet(&ctx, &ow->x, &ow->y,
                           dx * ow->speed * dt, dy * ow->speed * dt, ow_solid))
                player->is_moving = 0;
        }
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

        // Interior door detection — on the door tiles or the tile row below them.
        // Biased 8px left: the feet hitbox sits right of the sprite centre, so
        // an unshifted check makes doors detect too far to the right visually.
        int door_tx = (int)((feet_x + 8.0f) / TILE_SIZE);
        ow->at_interior_door = 0;
        for (int i = 0; i < map->num_doors; i++) {
            const InteriorDoor& d = map->doors[i];
            if (door_tx >= d.x && door_tx < d.x + d.w && (ty == d.y || ty == d.y + 1)) {
                ow->at_interior_door  = 1;
                ow->interior_door_idx = i;
                break;
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
}

void overworld_draw_swing(const Overworld* ow, const Camera* cam, SDL_Renderer* ren)
{
    float px = ow->x + (HB_X1 + HB_X2) * 0.5f;
    float py = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
    weapon_swing_draw(&ow->swing, px, py, cam, ren);
}
