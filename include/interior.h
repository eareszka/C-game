#ifndef INTERIOR_H
#define INTERIOR_H

#include <SDL2/SDL.h>
#include <stdint.h>
#include "entity.h"
#include "input.h"

// Single-screen building interiors: 20x15 tiles of 32px fills 640x480 exactly,
// so no camera/scrolling is needed. Each building on the starting island has
// its own, drawn (art/structures/interiors) and packed into interiors.h.

#define IMAP_W    20
#define IMAP_H    15
#define IMAP_TILE 32

enum InteriorTile : uint8_t {
    INT_VOID  = 0,   // outside the room — drawn as darkness, solid
    INT_WALL  = 1,
    INT_FLOOR = 2,
    INT_EXIT  = 3,   // doormat — stand on it + confirm to leave
};

struct InteriorMap {
    uint8_t tiles[IMAP_H][IMAP_W];  // semantic layer: void/wall/floor/exit
    int     atlas[IMAP_H][IMAP_W];  // tileset.png index per cell, -1 = none (prebuilt only)
    int     furn[IMAP_H][IMAP_W];   // the furniture's layer over it: the same, -1 = none
    bool    prebuilt;               // true: draw from the atlas; false: flat placeholder colours
    float enter_x, enter_y;   // where the feet stand coming in: the middle of
                              // the way out's floor (its 'E' cells, walkable part)
    int id;
};

struct InteriorPlayer {
    float x, y;
    float speed;
    int   at_exit;   // 1 if player's feet are on an INT_EXIT tile
};

void interior_load(InteriorMap* im, int interior_id);
// Where a room keeps the raft book, as a tile: the book shop, on its counter.
// False for a room without one.
bool interior_book_spot(int interior_id, int* tx, int* ty);
// Whether the player, their sprite's top-left at (x, y), can stand there.
bool interior_feet_fit(const InteriorMap* im, float x, float y);
void interior_player_init(InteriorPlayer* ip, Player* player, const InteriorMap* im);
void interior_player_update(InteriorPlayer* ip, Player* player, const Input* in,
                            float dt, const InteriorMap* im);
// atlas_tex: the tileset.png texture (tilemap_get_town_tex()); may be null,
// in which case prebuilt interiors fall back to flat placeholder colours.
void interior_draw(const InteriorMap* im, SDL_Renderer* ren, SDL_Texture* atlas_tex);
// After the player, as tilemap_draw_over_player: what in a drawn room stands in
// front of them -- the box their sprite covers, feet meeting the floor at feet_y.
void interior_draw_over_player(const InteriorMap* im, SDL_Renderer* ren,
                               float x, float y, float w, float h, float feet_y);

#endif
