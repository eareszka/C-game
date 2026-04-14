#ifndef OVERWORLD_H
#define OVERWORLD_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "resource_node.h"
#include "tilemap.h"

typedef struct Overworld {
    float x, y;
    float speed;

    // Set each frame — 1 if the player's feet are on a dungeon entrance tile.
    // main.cpp reads this to trigger dungeon entry on keypress.
    int at_dungeon_entrance;
    DungeonEntranceType dungeon_type;   // valid when at_dungeon_entrance == 1
    float dungeon_difficulty;           // valid when at_dungeon_entrance == 1
} Overworld;

void overworld_init(Overworld* ow, Player* player, float x, float y);
void overworld_update(Overworld* ow, Player* player, const Input* in, float dt, ResourceNodeList* resources, Tilemap* map);

// Draw the player sprite at any world position — used in all game states.
void player_draw(const Player* player, float world_x, float world_y,
                 const Camera* cam, SDL_Renderer* ren, SDL_Texture* sprite);

#endif
