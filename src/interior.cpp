#include "fc_palette.h"
#include "interior.h"
#include "interiors.h"
#include "collision.h"
#include "tilemap.h"   // TOWN0_SHEET_COLS
#include <string.h>
#include <initializer_list>

// A room per building on the starting island, each drawn whole
// (art/structures/interiors, packed by gen_entrance_art.py into interiors.h):
// which sheet cell each of its cells draws, and what each is to the feet.
// The furniture is a layer of its own drawn over the room (interior_N_furn),
// as an NES draws sprites over its background, so neither shares a tile's
// colours with the other.
struct PrebuiltInterior {
    const int (*tiles)[IMAP_W];
    const char* const* coll;
    const int (*furn)[IMAP_W];
};
static const PrebuiltInterior prebuilt_interiors[] = {
    { interior_0_tiles, interior_0_coll, interior_0_furn },   // 0 — the spawn house
    { interior_1_tiles, interior_1_coll, interior_1_furn },   // 1 — the book shop
    { interior_2_tiles, interior_2_coll, interior_2_furn },   // 2-6 — the other houses (gen_entrance_art.py HOUSES)
    { interior_3_tiles, interior_3_coll, interior_3_furn },
    { interior_4_tiles, interior_4_coll, interior_4_furn },
    { interior_5_tiles, interior_5_coll, interior_5_furn },
    { interior_6_tiles, interior_6_coll, interior_6_furn },
};
#define NUM_INTERIORS (int)(sizeof(prebuilt_interiors) / sizeof(prebuilt_interiors[0]))

static void interior_find_entry(InteriorMap* im);

bool interior_book_spot(int interior_id, int* tx, int* ty)
{
    // On the book shop's counter (bookshop_design.py), taken from the floor
    // before it.
    if (interior_id != 1) return false;
    *tx = 9; *ty = 8;
    return true;
}

void interior_load(InteriorMap* im, int interior_id)
{
    if (interior_id < 0 || interior_id >= NUM_INTERIORS) interior_id = 0;
    im->id = interior_id;

    const PrebuiltInterior& pb = prebuilt_interiors[interior_id];
    im->prebuilt = (pb.tiles != nullptr);

    const char* const* layout = pb.coll;
    for (int y = 0; y < IMAP_H; y++) {
        const char* row = layout[y];
        int row_len = (int)strlen(row);
        for (int x = 0; x < IMAP_W; x++) {
            char c = (x < row_len) ? row[x] : ' ';
            uint8_t t = INT_VOID;
            if      (c == '#') t = INT_WALL;
            else if (c == '.') t = INT_FLOOR;
            else if (c == 'E') t = INT_EXIT;
            im->tiles[y][x] = t;
            int val = im->prebuilt ? pb.tiles[y][x] : 0;
            im->atlas[y][x] = (val >= 6) ? val - 6 : -1;
            int fv = im->prebuilt ? pb.furn[y][x] : 0;
            im->furn[y][x] = (fv >= 6) ? fv - 6 : -1;
        }
    }
    interior_find_entry(im);
}

// The sheet cell a prebuilt interior draws at (tx, ty), as a tile id, or -1:
// the room's, or with furn the furniture's over it.
static int interior_cell(const InteriorMap* im, int tx, int ty, bool furn = false)
{
    int idx = furn ? im->furn[ty][tx] : im->atlas[ty][tx];
    if (!im->prebuilt || idx < 0) return -1;
    return TILE_TOWN0_BASE + idx;
}

// Whether the art of (tx, ty) -- the room or the furniture over it -- stands
// on the ground at art pixel (ax, ay) of the cell.
static bool cell_foot(int id, int ax, int ay)
{
    const ArtCellDepth* d = tilemap_art_depth(id);
    return d && ((d->foot[ay & 15] >> (ax & 15)) & 1);
}

static bool interior_solid(const void* ctx, float px, float py);

// The middle of the way out's floor: every walkable pixel of its 'E' cells.
static void interior_find_entry(InteriorMap* im)
{
    float sx = 0, sy = 0;
    int n = 0;
    for (int ty = 0; ty < IMAP_H; ty++)
        for (int tx = 0; tx < IMAP_W; tx++) {
            if (im->tiles[ty][tx] != INT_EXIT) continue;
            for (int py = 1; py < IMAP_TILE; py += 2)
                for (int px = 1; px < IMAP_TILE; px += 2) {
                    float x = tx * IMAP_TILE + px, y = ty * IMAP_TILE + py;
                    if (!interior_solid(im, x, y)) { sx += x; sy += y; n++; }
                }
        }
    im->enter_x = n ? sx / n : IMAP_W * IMAP_TILE * 0.5f;
    im->enter_y = n ? sy / n : IMAP_H * IMAP_TILE * 0.5f;
}

static bool interior_solid(const void* ctx, float px, float py)
{
    const InteriorMap* im = (const InteriorMap*)ctx;
    if (px < 0 || py < 0) return true;
    int tx = (int)(px / IMAP_TILE);
    int ty = (int)(py / IMAP_TILE);
    if (tx >= IMAP_W || ty >= IMAP_H) return true;
    uint8_t t = im->tiles[ty][tx];
    if (t == INT_VOID) return true;
    // A drawn room says to the pixel where the floor is, its furniture what
    // stands on it.
    if (tilemap_art_depth(interior_cell(im, tx, ty))) {
        int ax = (int)((px - tx * IMAP_TILE) * 16.0f / IMAP_TILE);
        int ay = (int)((py - ty * IMAP_TILE) * 16.0f / IMAP_TILE);
        return cell_foot(interior_cell(im, tx, ty), ax, ay) ||
               cell_foot(interior_cell(im, tx, ty, true), ax, ay);
    }
    return t == INT_WALL;
}

bool interior_feet_fit(const InteriorMap* im, float x, float y)
{
    return can_occupy(im, x, y, interior_solid);
}

void interior_player_init(InteriorPlayer* ip, Player* player, const InteriorMap* im)
{
    // Feet on the way out's floor, facing into the room.
    ip->x = im->enter_x - (HB_X1 + HB_X2) * 0.5f;
    ip->y = im->enter_y - (HB_Y1 + HB_Y2) * 0.5f;
    ip->speed   = PLAYER_WALK_SPEED;
    ip->at_exit = 1;

    float dx = IMAP_W * IMAP_TILE * 0.5f - im->enter_x, dy = IMAP_H * IMAP_TILE * 0.5f - im->enter_y;
    player->facing = fabsf(dx) > fabsf(dy) ? (dx < 0 ? FACE_LEFT : FACE_RIGHT)
                                           : (dy < 0 ? FACE_UP : FACE_DOWN);
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
    player_gait(in, &ip->speed, &anim_speed);

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

void interior_draw_over_player(const InteriorMap* im, SDL_Renderer* ren,
                               float x, float y, float w, float h, float feet_y)
{
    for (int ty = (int)(y / IMAP_TILE); ty <= (int)((y + h - 1) / IMAP_TILE); ty++)
        for (int tx = (int)(x / IMAP_TILE); tx <= (int)((x + w - 1) / IMAP_TILE); tx++) {
            if (tx < 0 || ty < 0 || tx >= IMAP_W || ty >= IMAP_H) continue;
            for (bool furn : { false, true }) {              // the room, then its furniture
                int id = interior_cell(im, tx, ty, furn);
                if (id >= 0)
                    tilemap_draw_cell_over(ren, id, tx * IMAP_TILE, ty * IMAP_TILE, IMAP_TILE,
                                           (float)(tx * IMAP_TILE), (float)(ty * IMAP_TILE), x, y, w, h, feet_y);
            }
        }
}

void interior_draw(const InteriorMap* im, SDL_Renderer* ren, SDL_Texture* atlas_tex)
{
    for (int y = 0; y < IMAP_H; y++) {
        for (int x = 0; x < IMAP_W; x++) {
            SDL_Rect r = { x * IMAP_TILE, y * IMAP_TILE,
                           IMAP_TILE, IMAP_TILE };
            if (im->prebuilt && atlas_tex) {
                for (int idx : { im->atlas[y][x], im->furn[y][x] }) {   // the room, the furniture over it
                    if (idx < 0) continue;  // void — leave the dark clear colour
                    SDL_Rect src = { (idx % TOWN0_SHEET_COLS) * 16,
                                     (idx / TOWN0_SHEET_COLS) * 16, 16, 16 };
                    SDL_RenderCopy(ren, atlas_tex, &src, &r);
                }
                continue;
            }
            switch (im->tiles[y][x]) {
                case INT_WALL:
                    fc_draw_color(ren, 92, 92, 104, 255);
                    SDL_RenderFillRect(ren, &r);
                    fc_draw_color(ren, 60, 60, 70, 255);
                    SDL_RenderDrawRect(ren, &r);
                    break;
                case INT_FLOOR:
                    // wood planks — alternate shade per column for a simple pattern
                    if ((x + y) & 1) fc_draw_color(ren, 150, 108, 66, 255);
                    else             fc_draw_color(ren, 140,  98, 58, 255);
                    SDL_RenderFillRect(ren, &r);
                    break;
                case INT_EXIT:
                    fc_draw_color(ren, 196, 152, 92, 255);
                    SDL_RenderFillRect(ren, &r);
                    fc_draw_color(ren, 120, 84, 40, 255);
                    SDL_RenderDrawRect(ren, &r);
                    break;
                default: break; // INT_VOID — leave the dark clear colour
            }
        }
    }
}
