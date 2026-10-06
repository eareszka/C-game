#ifndef GAME_MENU_H
#define GAME_MENU_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"

// The TAB menu, laid out like Yume Nikki's: small windows over the world
// rather than a screen of its own -- a command window (WEAPONS / ITEMS /
// CLOSE), a preview of the selected thing's icon under it, and a list beside
// them. On WEAPONS the list is the seven weapons, and under it whatever the
// highlighted one can have done to it -- make, equip, upgrade -- each with
// its cost, so the player only ever picks a weapon and then a plain action.
// The rules (costs, forging, upgrades) are src/crafting.cpp's; this file is
// only the windows and the keys.
enum MenuFocus { FOCUS_COMMANDS, FOCUS_LIST, FOCUS_ACTIONS };

struct GameMenu {
    bool      open  = false;
    MenuFocus focus = FOCUS_COMMANDS;
    int       cmd   = 0;        // command row
    int       sel   = 0;        // list entry
    int       act   = 0;        // action row, on WEAPONS
    float     note_t = 0.0f;    // seconds left of the last action's message
    const char* note = nullptr;

    // Icon sheets, loaded on the first draw (they need the renderer).
    SDL_Texture* items   = nullptr;   // assets/items.png, one 16px cell per Item
    SDL_Texture* weapons = nullptr;   // assets/weapon_icons.png, ore x weapon
    bool         tried   = false;
};

void game_menu_toggle(GameMenu* m);
// Keys, while open. Reads the raw input: the game itself gets a blank one.
void game_menu_update(GameMenu* m, Player* p, const Input* in, float dt);
void game_menu_draw(GameMenu* m, const Player* p, SDL_Renderer* ren);
void game_menu_free(GameMenu* m);
// An item's icon, `size` pixels square, from the menu's sheet -- for the
// world to show the same picture the menu does (the book on the floor, the
// raft under the player).
void game_menu_draw_item(GameMenu* m, SDL_Renderer* ren, int item, int x, int y, int size);

#endif
