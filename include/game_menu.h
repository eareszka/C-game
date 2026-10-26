#ifndef GAME_MENU_H
#define GAME_MENU_H

#include <SDL2/SDL.h>
#include "entity.h"
#include "input.h"
#include "crafting.h"

// Three windows shared with the debug menus: commands, item preview, and a
// scrolling item/recipe list. Recipe costs support four ingredients plus a
// separately displayed, retained book. Shops reuse these panels.
static const int CMD_X = 20,  CMD_Y = 36,  CMD_W = 112, CMD_H = 116;
static const int PRE_X = 20,  PRE_Y = 160, PRE_W = 112, PRE_H = 196;
static const int LST_X = CMD_X + CMD_W + 14, LST_Y = 36, LST_W = 620 - LST_X, LST_H = 380;

enum MenuFocus { FOCUS_COMMANDS, FOCUS_LIST, FOCUS_ACTIONS };

struct GameMenu {
    bool      open  = false;
    bool      shop  = false;
    const Item* stock = nullptr; // the shop's books (game_menu_open_shop)
    int       stock_n  = 0;
    int       shop_cmd = 0;      // BUY / LEAVE
    MenuFocus focus = FOCUS_COMMANDS;
    int       cmd   = 0;        // command row
    int       sel   = 0;        // list entry
    int       act   = 0;        // action row, on WEAPONS
    float     note_t = 0.0f;    // seconds left of the last action's message
    const char* note = nullptr;
    // World chase state, reserved for future item activation restrictions.
    bool      chased = false;
    // SAVE: why it can't be done here (set by the game each frame; null when
    // it can), and the request the game answers by writing the file.
    const char* save_block   = nullptr;
    bool        save_request = false;
    // Null only when dungeon exploration permits using the Escape Charm.
    const char* escape_block = "ONLY IN A DUNGEON";
    bool escape_request = false;
    const char* healing_block = nullptr; // exploration only, outside transitions
    const char* raft_block = nullptr;    // set while the raft holds the player up: it can't come off

    // Icon sheets, loaded on the first draw (they need the renderer).
    SDL_Texture* items   = nullptr;   // assets/items.png, one 16px cell per Item
    SDL_Texture* weapons = nullptr;   // assets/weapon_icons.png, ore x weapon
    bool         tried   = false;
};

void game_menu_toggle(GameMenu* m);
// A shop selling these books: BUY / LEAVE on the left, the stock on the right.
void game_menu_open_shop(GameMenu* m, const Item* stock, int n);
// A line in the menu's message place for a moment ("SAVED").
void game_menu_say(GameMenu* m, const char* note);
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
