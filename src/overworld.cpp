#include "overworld.h"
#include "resource_node.h"
#include "collision.h"
#include <math.h>

// float_ok: the player has a raft, so water is somewhere to be, not a wall.
// Everything else that stops a walker still stops a raft.
struct OWCollCtx { const Tilemap* map; const ResourceNodeList* res; bool float_ok; };
static bool ow_solid(const void* ctx, float px, float py) {
    const OWCollCtx* c = static_cast<const OWCollCtx*>(ctx);
    if (c->float_ok && tilemap_pixel_water(c->map, px, py))
        return resource_node_solid(c->res, px, py);
    return tilemap_pixel_solid(c->map, px, py)
        || resource_node_solid(c->res, px, py);
}

void overworld_init(Overworld* ow, Player* player, float x, float y)
{
    ow->x       = x;
    ow->y       = y;
    ow->speed   = PLAYER_WALK_SPEED;
    ow->at_dungeon_entrance = 0;
    ow->at_interior_door    = 0;
    ow->interior_door_idx   = -1;
    ow->swing               = WeaponSwingState();
    ow->sailing             = false;
    ow->sail_t              = 0.0f;

    // Every shape has its slot; the player starts owning a stone knife.
    for (int w = 0; w < WEAPON_COUNT; w++) {
        player->arsenal[w] = Weapon{ (WeaponType)w, MAT_STONE };
        player->owned[w]   = false;
    }
    player->owned[WEAPON_KNIFE] = true;
    player->equipped = WEAPON_KNIFE;

    // 14x20 art pixels at 2x (assets/player_small.png); the feet box in collision.h sits at
    // the bottom of this frame.
    player->width  = 28;
    player->height = 40;
    player->facing = FACE_DOWN;
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
                       cam, at_prompt, -1, h);

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
    if (!weapon_swing_frozen_tick(&ow->swing, player, dt) && !ow->sailing)
        player_read_input(player, in, &dx, &dy);

    float anim_speed;
    player_gait(in, &ow->speed, &anim_speed);

    auto feet_on_water = [&]() {
        return player->raft > 0 &&
               tilemap_pixel_water(map, ow->x + (HB_X1 + HB_X2) * 0.5f, ow->y + (HB_Y1 + HB_Y2) * 0.5f);
    };

    if (ow->sailing) {
        // Afloat and under way: straight on along the course, no sliding
        // round what is in the way. It ends at land, or against something.
        // A long crossing picks up speed, for convenience: from the push off
        // it builds evenly to twice RAFT_SPEED at RAFT_RAMP_T, and holds.
        OWCollCtx ctx = { map, resources, true };
        ow->sail_t += dt;
        float speed = RAFT_SPEED * (1.0f + fminf(ow->sail_t / RAFT_RAMP_T, 1.0f));
        float nx = ow->x + ow->sail_dx * speed * dt;
        float ny = ow->y + ow->sail_dy * speed * dt;
        if (noclip || can_occupy(&ctx, nx, ny, ow_solid)) {
            ow->x = wrap_px(nx);
            ow->y = wrap_py(ny);
        } else {
            ow->sailing = false;   // run aground: wait for a push off
        }
        if (!feet_on_water()) ow->sailing = false;   // landed
        player->is_moving = 0;
    } else if (dx != 0.0f || dy != 0.0f) {
        OWCollCtx ctx = { map, resources, player->raft > 0 };
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
        // Kept canonical on the wrap axis. Beyond the seam is the same world,
        // and everything indexed by position wants it as 0..width; the camera
        // is not, and follows the player through the seam on its own.
        ow->x = wrap_px(ow->x);
        ow->y = wrap_py(ow->y);

        // Stepped onto the water with a raft: cast off the way the player was
        // walking, and hold it.
        if (feet_on_water()) {
            float len = sqrtf(dx * dx + dy * dy);
            ow->sailing = true;
            ow->sail_dx = dx / len;
            ow->sail_dy = dy / len;
            ow->sail_t  = 0.0f;
            player->is_moving = 0;
        }
    }

    // Dungeon entrance detection
    {
        float feet_x = ow->x + (HB_X1 + HB_X2) * 0.5f;
        float feet_y = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
        int tx = (int)floorf(feet_x / TILE_SIZE);
        int ty = (int)floorf(feet_y / TILE_SIZE);
        ow->at_dungeon_entrance = 0;
        if (in_world(&tx, &ty)) {
            int tile = map->tiles[ty][tx];
            if ((tile == TILE_DUNGEON || (tile >= TILE_DUNGEON_CAVE && tile <= TILE_DUNGEON_LARGE_TREE)) &&
                tilemap_way_in(map, feet_x, feet_y)) {
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
        int door_tx = wrap_x((int)floorf((feet_x + 8.0f) / TILE_SIZE));
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
    int sx = cam_screen_x(cam, world_x);
    int sy = cam_screen_y(cam, world_y);

    int frame = player_frame(player);
    SDL_Rect src = { frame * 14, 0, 14, 20 };
    SDL_Rect dst = { sx, sy, (int)(player->width * z), (int)(player->height * z) };
    SDL_RenderCopy(ren, sprite, &src, &dst);
}

void overworld_draw_swing(const Overworld* ow, const Camera* cam, SDL_Renderer* ren)
{
    float px = ow->x + (HB_X1 + HB_X2) * 0.5f;
    float py = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
    weapon_swing_draw(&ow->swing, px, py, cam, ren);
}
