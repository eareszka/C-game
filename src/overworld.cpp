#include "overworld.h"
#include "resource_node.h"
#include "collision.h"
#include "battle.h"
#include <math.h>

struct OWCollCtx { const Tilemap* map; const ResourceNodeList* res; };
static bool ow_solid(const void* ctx, float px, float py) {
    const OWCollCtx* c = static_cast<const OWCollCtx*>(ctx);
    return tilemap_pixel_solid(c->map, px, py)
        || resource_node_solid(c->res, px, py);
}

// Bearing the player is looking, matching the frame ranges player_draw uses.
// World y grows downward, so down is +PI/2 and up is -PI/2.
static float facing_angle(int facing) {
    if (facing >= 8) return 0.0f;           // right
    if (facing >= 6) return 3.1415927f;     // left
    if (facing >= 3) return -1.5707963f;    // up
    return 1.5707963f;                      // down
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
    ow->tool_cd = 0.0f;
    ow->at_dungeon_entrance = 0;
    ow->at_interior_door    = 0;
    ow->interior_door_idx   = -1;
    ow->sweep_t             = -1.0f;   // no swing running
    ow->sweep_start         = 0.0f;

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
                      ResourceNodeList* resources, Tilemap* map, bool noclip,
                      HarvestResult* out_harvest)
{
    if (ow->tool_cd > 0.0f) ow->tool_cd -= dt;

    // Action key — hit nearby resource or map tile.
    //
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
    WeaponType weapon = player->equipped_weapon;

    HarvestResult local = {};
    HarvestResult* h = out_harvest ? out_harvest : &local;

    if (ow->tool_cd <= 0.0f && !at_prompt
     && (input_down(in, SDL_SCANCODE_SPACE)
      || input_down(in, SDL_SCANCODE_Z)
      || input_down(in, SDL_SCANCODE_RETURN)))
    {
        if (weapon_sweeps(weapon)) {
            // Set the blade going from where the player is looking; the strikes
            // land below, as it comes round.
            ow->sweep_t     = 0.0f;
            ow->sweep_start = facing_angle(player->facing);
            // Cooldown is the turn itself, so the next swing begins exactly as
            // this one finishes rather than after a pause.
            ow->tool_cd     = SWEEP_SECONDS;
        } else {
            int rn_hit = resource_nodes_try_hit(resources, hx, hy, 40, weapon, h);
            // Map tiles are only reached when no node was in range.
            if (rn_hit == 0)
                tilemap_try_hit(map, hx, hy, 40, weapon, h);

            if (h->count > 0) {
                float ddx = h->hits[0].x - hx;
                float ddy = h->hits[0].y - hy;
                if (ddx * ddx >= ddy * ddy)
                    player->facing = ddx >= 0.0f ? 8 : 6;
                else
                    player->facing = ddy >= 0.0f ? 0 : 3;
                player->facing_locked = 1;
                ow->tool_cd = 1.0f / weapon_profile(weapon).fire_rate;
            }
        }
    }

    // Advance a running sweep and strike whatever arc the blade covered this
    // frame. Driven by elapsed time rather than per-frame steps so the swing
    // takes the same path regardless of frame rate.
    if (ow->sweep_t >= 0.0f) {
        const float TWO_PI = 6.2831853f;
        float t0 = ow->sweep_t / SWEEP_SECONDS;
        ow->sweep_t += dt;
        float t1 = ow->sweep_t / SWEEP_SECONDS;
        if (t1 > 1.0f) t1 = 1.0f;

        resource_nodes_sweep(resources, hx, hy, SWEEP_RADIUS, ow->sweep_start,
                             t0 * TWO_PI, t1 * TWO_PI, weapon, h);
        tilemap_sweep(map, hx, hy, SWEEP_RADIUS, ow->sweep_start,
                      t0 * TWO_PI, t1 * TWO_PI, weapon, h);

        if (ow->sweep_t >= SWEEP_SECONDS) ow->sweep_t = -1.0f;
    }

    for (int i = 0; i < h->count; i++)
        if (h->hits[i].resource >= 0)
            player->inventory[h->hits[i].resource]++;

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

void overworld_draw_sweep(const Overworld* ow, const Camera* cam, SDL_Renderer* ren)
{
    if (ow->sweep_t < 0.0f) return;

    const float TWO_PI = 6.2831853f;
    float z  = cam->zoom;
    float px = ow->x + (HB_X1 + HB_X2) * 0.5f;
    float py = ow->y + (HB_Y1 + HB_Y2) * 0.5f;
    int cx = (int)((px - cam->x) * z);
    int cy = (int)((py - cam->y) * z);
    float r = SWEEP_RADIUS * z;

    float prog = ow->sweep_t / SWEEP_SECONDS;
    if (prog > 1.0f) prog = 1.0f;

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);

    // Trail along the arc already cut, brightest just behind the blade so the
    // direction of travel reads at a glance.
    const int STEPS = 28;
    for (int i = 0; i < STEPS; i++) {
        float f0 = (float)i / STEPS;
        float f1 = (float)(i + 1) / STEPS;
        float a0 = ow->sweep_start + f0 * prog * TWO_PI;
        float a1 = ow->sweep_start + f1 * prog * TWO_PI;
        SDL_SetRenderDrawColor(ren, 210, 225, 255, (Uint8)(25.0f + 165.0f * f1));
        SDL_RenderDrawLine(ren,
            cx + (int)(cosf(a0) * r), cy + (int)(sinf(a0) * r),
            cx + (int)(cosf(a1) * r), cy + (int)(sinf(a1) * r));
    }

    // The blade itself.
    float cur = ow->sweep_start + prog * TWO_PI;
    int bx = cx + (int)(cosf(cur) * r);
    int by = cy + (int)(sinf(cur) * r);
    SDL_SetRenderDrawColor(ren, 255, 255, 255, 235);
    SDL_RenderDrawLine(ren, cx, cy, bx, by);
    SDL_RenderDrawLine(ren, cx, cy + 1, bx, by + 1);

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}
