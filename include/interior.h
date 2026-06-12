#ifndef INTERIOR_H
#define INTERIOR_H

#include <SDL2/SDL.h>
#include <stdint.h>
#include "entity.h"
#include "input.h"

// Single-screen building interiors: 20x15 tiles of 32px fills 640x480 exactly,
// so no camera/scrolling is needed. Layouts are hand-authored ASCII blueprints.

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
    bool    prebuilt;               // true: draw from the atlas; false: flat placeholder colours
    int exit_x, exit_y;   // left tile of the (2-wide) exit doormat
    int id;
};

struct InteriorPlayer {
    float x, y;
    float speed;
    int   at_exit;   // 1 if player's feet are on an INT_EXIT tile
};

void interior_load(InteriorMap* im, int interior_id);
void interior_player_init(InteriorPlayer* ip, Player* player, const InteriorMap* im);
void interior_player_update(InteriorPlayer* ip, Player* player, const Input* in,
                            float dt, const InteriorMap* im);
// atlas_tex: the tileset.png texture (tilemap_get_town_tex()); may be null,
// in which case prebuilt interiors fall back to flat placeholder colours.
void interior_draw(const InteriorMap* im, SDL_Renderer* ren, SDL_Texture* atlas_tex);

#endif
