#include "fc_palette.h"
#include "interior.h"
#include "interiors.h"
#include "collision.h"
#include "tilemap.h"   // TOWN0_SHEET_COLS
#include "core.h"      // world_ms, the ambient beat
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <SDL2/SDL_image.h>
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

// The rooms redrawn with PixelLab (art/interiors_nes, tools/interior_nes.py):
// each its own art -- the room, and beside it the furniture's layer, 320x240
// each, drawn at twice -- and per art pixel each layer's drop to the floor row
// it stands on (255: nothing drawn) and whether it is ground the feet can't
// take. Read once, the first time the room is asked for; a room without
// them is drawn from the sheet as before.
#define NES_W (IMAP_W * IMAP_TILE / 2)
#define NES_H (IMAP_H * IMAP_TILE / 2)
#define MAX_NES_ROOMS 64
struct NesRoom {
    bool tried, ok;
    uint8_t drop[2][NES_H][NES_W];
    uint8_t foot[NES_H][NES_W];          // bit 0 the room's ground, bit 1 the furniture's
    char coll[IMAP_H][IMAP_W + 1];
    SDL_Texture* tex;
    // something on the wall that moves (room_N_anim.txt: layer x y w h frames,
    // room_N_anim.png the frames side by side), on the world's ambient beat
    int anim_layer, anim_x, anim_y, anim_w, anim_h, anim_n;
    bool anim_tried;
    SDL_Texture* anim_tex;
    // stairs to another floor (room_N_stairs.txt, a line each: the room they
    // reach, the feet's box that takes them x0 y0 x1 y1, and where the feet
    // arrive there, ax ay -- all in screen pixels)
    int n_stairs;
    struct { int to; float x0, y0, x1, y1, ax, ay; } stairs[4];
};
static NesRoom* nes_rooms[MAX_NES_ROOMS];

static const NesRoom* nes_room(int id)
{
    if (id < 0 || id >= MAX_NES_ROOMS) return nullptr;
    if (!nes_rooms[id]) nes_rooms[id] = (NesRoom*)SDL_calloc(1, sizeof(NesRoom));
    NesRoom* r = nes_rooms[id];
    if (!r || r->tried) return r && r->ok ? r : nullptr;
    r->tried = true;
    char path[96];
    SDL_snprintf(path, sizeof path, "assets/interiors/room_%d.txt", id);
    FILE* f = fopen(path, "r");
    if (!f) return nullptr;
    for (int y = 0; y < IMAP_H; y++) {
        char line[64] = "";
        if (!fgets(line, sizeof line, f)) line[0] = 0;
        bool ended = false;                              // past the line's end: outside
        for (int x = 0; x < IMAP_W; x++) {
            char c = ended ? 0 : line[x];
            if (!c || c == '\n') ended = true;
            r->coll[y][x] = (c == '#' || c == '.' || c == 'E') ? c : ' ';
        }
        r->coll[y][IMAP_W] = 0;
    }
    fclose(f);
    SDL_snprintf(path, sizeof path, "assets/interiors/room_%d_depth.png", id);
    SDL_Surface* raw = IMG_Load(path);
    if (!raw) return nullptr;
    SDL_Surface* s = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
    SDL_FreeSurface(raw);
    if (!s) return nullptr;
    if (s->w != NES_W || s->h != NES_H) { SDL_FreeSurface(s); return nullptr; }
    SDL_LockSurface(s);
    for (int y = 0; y < NES_H; y++) {
        const uint8_t* row = (const uint8_t*)s->pixels + y * s->pitch;
        for (int x = 0; x < NES_W; x++) {
            r->drop[0][y][x] = row[x * 4 + 0];
            r->drop[1][y][x] = row[x * 4 + 1];
            r->foot[y][x]    = row[x * 4 + 2];
        }
    }
    SDL_UnlockSurface(s);
    SDL_FreeSurface(s);
    SDL_snprintf(path, sizeof path, "assets/interiors/room_%d_stairs.txt", id);
    if (FILE* sf = fopen(path, "r")) {
        while (r->n_stairs < 4 &&
               fscanf(sf, "%d %f %f %f %f %f %f", &r->stairs[r->n_stairs].to, &r->stairs[r->n_stairs].x0,
                      &r->stairs[r->n_stairs].y0, &r->stairs[r->n_stairs].x1, &r->stairs[r->n_stairs].y1,
                      &r->stairs[r->n_stairs].ax, &r->stairs[r->n_stairs].ay) == 7)
            r->n_stairs++;
        fclose(sf);
    }
    r->ok = true;
    return r;
}

static SDL_Texture* nes_room_tex(int id, SDL_Renderer* ren)
{
    NesRoom* r = (NesRoom*)nes_room(id);
    if (!r) return nullptr;
    if (!r->tex) {
        char path[96];
        SDL_snprintf(path, sizeof path, "assets/interiors/room_%d.png", id);
        r->tex = IMG_LoadTexture(ren, path);
    }
    if (!r->anim_tried) {
        r->anim_tried = true;
        char path[96];
        SDL_snprintf(path, sizeof path, "assets/interiors/room_%d_anim.txt", id);
        if (FILE* f = fopen(path, "r")) {
            if (fscanf(f, "%d %d %d %d %d %d", &r->anim_layer, &r->anim_x, &r->anim_y,
                       &r->anim_w, &r->anim_h, &r->anim_n) == 6 && r->anim_n > 0) {
                SDL_snprintf(path, sizeof path, "assets/interiors/room_%d_anim.png", id);
                r->anim_tex = IMG_LoadTexture(ren, path);
            }
            fclose(f);
        }
    }
    return r->tex;
}

// The room's moving piece in this beat's frame, over its layer: AMBIENT_FRAMES
// of AMBIENT_FRAME_MS, the same beat as everything ambient in the world.
static void nes_room_anim(const NesRoom* r, SDL_Renderer* ren, int layer)
{
    if (!r || !r->anim_tex || r->anim_layer != layer) return;
    const int AP = IMAP_W * IMAP_TILE / NES_W;
    int f = (int)(world_ms() / AMBIENT_FRAME_MS % (Uint32)AMBIENT_FRAMES) % r->anim_n;
    SDL_Rect src = { f * r->anim_w, 0, r->anim_w, r->anim_h };
    SDL_Rect dst = { r->anim_x * AP, r->anim_y * AP, r->anim_w * AP, r->anim_h * AP };
    SDL_RenderCopy(ren, r->anim_tex, &src, &dst);
}

void interior_load(InteriorMap* im, int interior_id)
{
    // a room past the sheet's (an upstairs) is its own art or nothing
    if (interior_id < 0 || interior_id >= MAX_NES_ROOMS ||
        (interior_id >= NUM_INTERIORS && !nes_room(interior_id))) interior_id = 0;
    im->id = interior_id;

    static const PrebuiltInterior none = {};
    const PrebuiltInterior& pb = interior_id < NUM_INTERIORS ? prebuilt_interiors[interior_id] : none;
    im->prebuilt = (pb.tiles != nullptr);
    const NesRoom* nr = nes_room(interior_id);
    im->nes = nr != nullptr;

    const char* const* layout = pb.coll;
    for (int y = 0; y < IMAP_H; y++) {
        const char* row = nr ? nr->coll[y] : layout ? layout[y] : "";
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
    if (im->nes) {                                       // the room's own art says to the pixel
        const NesRoom* nr = nes_room(im->id);
        int ax = (int)(px * NES_W / (IMAP_W * IMAP_TILE)), ay = (int)(py * NES_H / (IMAP_H * IMAP_TILE));
        return !nr || ax >= NES_W || ay >= NES_H || nr->foot[ay][ax] != 0;
    }
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

// The door in a drawn room's left wall, every room's alike (door() in
// tools/interior_room.py: the frame's columns 34 to 43, at OX, OY = 32, 49), in
// room pixels: the columns it stands over, and the foot of the wall it is in,
// which runs up to the right along x + y = DOOR_WALL. Its hitbox is the floor
// before it (user's sketch): as long as the door, DOOR_REACH out from the wall
// straight across, so a slanted box as the wall is slanted.
static const float DOOR_X0 = 2 * (32 + 34), DOOR_X1 = 2 * (32 + 44);
static const float DOOR_WALL = 2 * (32 + 49 + 63 + 72), DOOR_REACH = 24;

void interior_player_init(InteriorPlayer* ip, Player* player, const InteriorMap* im)
{
    // Feet before the middle of the door, a pixel clear of its hitbox, facing
    // into the room; a placeholder room's, on its doormat.
    float fx = (DOOR_X0 + DOOR_X1) * 0.5f, fy = DOOR_WALL - fx;
    bool stood = im->prebuilt && stand_clear(&fx, &fy, 1, 0,
        [&](float x, float y) { return interior_at_exit(im, x, y); },
        [&](float x, float y) { return interior_feet_fit(im, x - (HB_X1 + HB_X2) * 0.5f, y - (HB_Y1 + HB_Y2) * 0.5f); });
    if (!stood) { fx = im->enter_x; fy = im->enter_y; }
    ip->x = fx - (HB_X1 + HB_X2) * 0.5f;
    ip->y = fy - (HB_Y1 + HB_Y2) * 0.5f;
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
    player_gait(in, &ip->speed, &anim_speed, player);

    if (dx != 0.0f || dy != 0.0f) {
        float nx = ip->x + dx * ip->speed * dt;
        float ny = ip->y + dy * ip->speed * dt;
        float px = ip->x, py = ip->y;
        if (can_occupy(im, nx, ip->y, interior_solid)) ip->x = nx;
        if (can_occupy(im, ip->x, ny, interior_solid)) ip->y = ny;
        if (ip->x == px && ip->y == py) player->is_moving = 0;
    }

    ip->at_exit = interior_at_exit(im, ip->x + (HB_X1 + HB_X2) * 0.5f, ip->y + (HB_Y1 + HB_Y2) * 0.5f);

    player_animate(player, dt, anim_speed);
}

bool interior_at_exit(const InteriorMap* im, float feet_x, float feet_y)
{
    if (!im->prebuilt) {                                   // a placeholder room: its doormat
        int tx = (int)(feet_x / IMAP_TILE), ty = (int)(feet_y / IMAP_TILE);
        return tx >= 0 && tx < IMAP_W && ty >= 0 && ty < IMAP_H && im->tiles[ty][tx] == INT_EXIT;
    }
    float out  = feet_x + feet_y - DOOR_WALL;              // from the wall, straight across
    float wall = feet_x - out;                             // the wall's column there
    return out >= 0 && out <= DOOR_REACH && wall >= DOOR_X0 && wall <= DOOR_X1;
}

int interior_stairs(const InteriorMap* im, float feet_x, float feet_y, float* arrive_x, float* arrive_y)
{
    const NesRoom* nr = im->nes ? nes_room(im->id) : nullptr;
    for (int i = 0; nr && i < nr->n_stairs; i++) {
        const auto& s = nr->stairs[i];
        if (feet_x >= s.x0 && feet_x <= s.x1 && feet_y >= s.y0 && feet_y <= s.y1) {
            *arrive_x = s.ax; *arrive_y = s.ay;
            return s.to;
        }
    }
    return -1;
}

void interior_draw_over_player(const InteriorMap* im, SDL_Renderer* ren,
                               float x, float y, float w, float h, float feet_y)
{
    if (im->nes) {
        const NesRoom* nr = nes_room(im->id);
        SDL_Texture* tex = nes_room_tex(im->id, ren);
        if (!nr || !tex) return;
        const float AP = (float)(IMAP_W * IMAP_TILE) / NES_W;     // screen pixels an art pixel
        int ay0 = SDL_max(0, (int)floorf(y / AP)), ay1 = SDL_min(NES_H, (int)ceilf((y + h) / AP));
        int ax0 = SDL_max(0, (int)floorf(x / AP)), ax1 = SDL_min(NES_W, (int)ceilf((x + w) / AP));
        for (int layer = 0; layer < 2; layer++)                   // the room, then its furniture
            for (int ay = ay0; ay < ay1; ay++) {
                auto front = [&](int ax) {
                    int dr = nr->drop[layer][ay][ax];
                    return dr != 255 && (ay + dr + 0.5f) * AP > feet_y;
                };
                for (int ax = ax0; ax < ax1; ) {
                    if (!front(ax)) { ax++; continue; }
                    int run = ax;
                    while (ax < ax1 && front(ax)) ax++;
                    SDL_Rect src = { layer * NES_W + run, ay, ax - run, 1 };
                    SDL_Rect dst = { (int)(run * AP), (int)(ay * AP), (int)((ax - run) * AP), (int)AP };
                    SDL_RenderCopy(ren, tex, &src, &dst);
                }
            }
        return;
    }
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
    if (im->nes) {
        if (SDL_Texture* tex = nes_room_tex(im->id, ren)) {
            SDL_Rect dst = { 0, 0, IMAP_W * IMAP_TILE, IMAP_H * IMAP_TILE };
            for (int layer = 0; layer < 2; layer++) {
                SDL_Rect src = { layer * NES_W, 0, NES_W, NES_H };
                SDL_RenderCopy(ren, tex, &src, &dst);
                nes_room_anim(nes_room(im->id), ren, layer);
            }
            return;
        }
    }
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
