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
// The three windows (logical 640x480): command, preview under it, list
// beside them. The debug menus (F2, F3) use the same places.
static const int CMD_X = 20,  CMD_Y = 36,  CMD_W = 150, CMD_H = 92;
static const int PRE_X = 20,  PRE_Y = 136, PRE_W = 150, PRE_H = 196;
static const int LST_X = 184, LST_Y = 36,  LST_W = 436, LST_H = 380;

enum MenuFocus { FOCUS_COMMANDS, FOCUS_LIST, FOCUS_ACTIONS };

struct GameMenu {
    bool      open  = false;
    MenuFocus focus = FOCUS_COMMANDS;
    int       cmd   = 0;        // command row
    int       sel   = 0;        // list entry
    int       act   = 0;        // action row, on WEAPONS
    float     note_t = 0.0f;    // seconds left of the last action's message
    const char* note = nullptr;
    // Set by the game each frame: something is chasing the player, so the
    // sleeping bag can't be used.
    bool      chased = false;

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
// A weapon's icon in its ore, the same picture the menu shows; shade < 255
// dims it (the battle box's previous and next weapons).
void game_menu_draw_weapon(GameMenu* m, SDL_Renderer* ren, WeaponType w, Material ore,
                           int x, int y, int size, Uint8 shade = 255);
// An ore's name as the menu writes it before a weapon ("IRON", "SHARD").
const char* game_menu_ore_name(Material m);

#endif
