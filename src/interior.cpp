#include "interior.h"
#include "interiors.h"
#include "collision.h"
#include "tilemap.h"   // TOWN0_SHEET_COLS
#include <string.h>

// ---------------------------------------------------------------------------
// Layout legend: '#'=wall, '.'=floor, 'E'=exit doormat, ' '=void
// Top wall is 2 rows tall for pseudo-depth, matching the exterior sprites.
// ---------------------------------------------------------------------------

// interior 0 — stone house (small)
static const char* interior_stone_house[IMAP_H] = {
    "                    ",
    "                    ",
    "    ############    ",
    "    ############    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #..........#    ",
    "    #####EE#####    ",
    "                    ",
    "                    ",
    "                    ",
};

// interior 1 — white house (large)
static const char* interior_white_house[IMAP_H] = {
    "                    ",
    "  ################  ",
    "  ################  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #..............#  ",
    "  #######EE#######  ",
    "                    ",
    "                    ",
};

static const char** all_interiors[] = {
    interior_stone_house,
    interior_white_house,
};
#define NUM_INTERIORS (int)(sizeof(all_interiors) / sizeof(all_interiors[0]))

// Prebuilt blueprint per interior id (interiors.h); null = use the ASCII placeholder.
struct PrebuiltInterior {
    const int (*tiles)[IMAP_W];
    const char* const* coll;
};
static const PrebuiltInterior prebuilt_interiors[NUM_INTERIORS] = {
    { interior_0_tiles, interior_0_coll },   // 0 — spawn / stone house
    { nullptr, nullptr },                    // 1 — white house (placeholder)
};

void interior_load(InteriorMap* im, int interior_id)
{
    if (interior_id < 0 || interior_id >= NUM_INTERIORS) interior_id = 0;
    im->id = interior_id;
    im->exit_x = IMAP_W / 2;
    im->exit_y = IMAP_H - 1;

    const PrebuiltInterior& pb = prebuilt_interiors[interior_id];
    im->prebuilt = (pb.tiles != nullptr);

    // Semantic layer (collision + exit) comes from the coll strings for
    // prebuilt interiors, or from the ASCII placeholder layout otherwise.
    const char* const* layout = im->prebuilt ? pb.coll
                                             : all_interiors[interior_id];
    bool exit_found = false;
    for (int y = 0; y < IMAP_H; y++) {
        const char* row = layout[y];
        int row_len = (int)strlen(row);
        for (int x = 0; x < IMAP_W; x++) {
            char c = (x < row_len) ? row[x] : ' ';
            uint8_t t = INT_VOID;
            if      (c == '#') t = INT_WALL;
            else if (c == '.') t = INT_FLOOR;
            else if (c == 'E') {
                t = INT_EXIT;
                if (!exit_found) { im->exit_x = x; im->exit_y = y; exit_found = true; }
            }
            im->tiles[y][x] = t;
            int val = im->prebuilt ? pb.tiles[y][x] : 0;
            im->atlas[y][x] = (val >= 6) ? val - 6 : -1;
        }
    }
}

static bool interior_solid(const void* ctx, float px, float py)
{
    const InteriorMap* im = (const InteriorMap*)ctx;
    if (px < 0 || py < 0) return true;
    int tx = (int)(px / IMAP_TILE);
    int ty = (int)(py / IMAP_TILE);
    if (tx >= IMAP_W || ty >= IMAP_H) return true;
    uint8_t t = im->tiles[ty][tx];
    return t == INT_WALL || t == INT_VOID;
}

void interior_player_init(InteriorPlayer* ip, Player* player, const InteriorMap* im)
{
    // Feet centred between the two doormat tiles, facing into the room.
    float door_cx = (im->exit_x + 1) * (float)IMAP_TILE;
    float door_cy =  im->exit_y * (float)IMAP_TILE + IMAP_TILE * 0.5f;
    ip->x = door_cx - (HB_X1 + HB_X2) * 0.5f;
    ip->y = door_cy - (HB_Y1 + HB_Y2) * 0.5f;
    ip->speed   = 150.0f;
    ip->at_exit = 1;

    player->facing = 3;  // up
    player->facing_locked = 0;
    player->is_moving = 0;
    player->anim_step = 0;
    player->anim_timer = 0.0f;
}

void interior_player_update(InteriorPlayer* ip, Player* player, const Input* in,
                            float dt, const InteriorMap* im)
{
    float dx, dy;
    player_read_input(player, in, &dx, &dy);

    float anim_speed;
    if (input_down(in, SDL_SCANCODE_LSHIFT))
        { ip->speed = 300.0f; anim_speed = 0.10f; }
    else
        { ip->speed = 150.0f; anim_speed = 0.20f; }

    if (dx != 0.0f || dy != 0.0f) {
        float nx = ip->x + dx * ip->speed * dt;
        float ny = ip->y + dy * ip->speed * dt;
        float px = ip->x, py = ip->y;
        if (can_occupy(im, nx, ip->y, interior_solid)) ip->x = nx;
        if (can_occupy(im, ip->x, ny, interior_solid)) ip->y = ny;
        if (ip->x == px && ip->y == py) player->is_moving = 0;
    }

    float feet_x = ip->x + (HB_X1 + HB_X2) * 0.5f;
    float feet_y = ip->y + (HB_Y1 + HB_Y2) * 0.5f;
    int tx = (int)(feet_x / IMAP_TILE);
    int ty = (int)(feet_y / IMAP_TILE);
    ip->at_exit = (tx >= 0 && tx < IMAP_W && ty >= 0 && ty < IMAP_H &&
                   im->tiles[ty][tx] == INT_EXIT);

    player_animate(player, dt, anim_speed);
}

void interior_draw(const InteriorMap* im, SDL_Renderer* ren, SDL_Texture* atlas_tex)
{
    for (int y = 0; y < IMAP_H; y++) {
        for (int x = 0; x < IMAP_W; x++) {
            SDL_Rect r = { x * IMAP_TILE, y * IMAP_TILE,
                           IMAP_TILE, IMAP_TILE };
            if (im->prebuilt && atlas_tex) {
                int idx = im->atlas[y][x];
                if (idx < 0) continue;  // void — leave the dark clear colour
                SDL_Rect src = { (idx % TOWN0_SHEET_COLS) * 16,
                                 (idx / TOWN0_SHEET_COLS) * 16, 16, 16 };
                SDL_RenderCopy(ren, atlas_tex, &src, &r);
                continue;
            }
            switch (im->tiles[y][x]) {
                case INT_WALL:
                    SDL_SetRenderDrawColor(ren, 92, 92, 104, 255);
                    SDL_RenderFillRect(ren, &r);
                    SDL_SetRenderDrawColor(ren, 60, 60, 70, 255);
                    SDL_RenderDrawRect(ren, &r);
                    break;
                case INT_FLOOR:
                    // wood planks — alternate shade per column for a simple pattern
                    if ((x + y) & 1) SDL_SetRenderDrawColor(ren, 150, 108, 66, 255);
                    else             SDL_SetRenderDrawColor(ren, 140,  98, 58, 255);
                    SDL_RenderFillRect(ren, &r);
                    break;
                case INT_EXIT:
                    SDL_SetRenderDrawColor(ren, 196, 152, 92, 255);
                    SDL_RenderFillRect(ren, &r);
                    SDL_SetRenderDrawColor(ren, 120, 84, 40, 255);
                    SDL_RenderDrawRect(ren, &r);
                    break;
                default: break; // INT_VOID — leave the dark clear colour
            }
        }
    }
}
