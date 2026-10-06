#ifndef CRAFTING_H
#define CRAFTING_H

#include "entity.h"

// Everything the player carries, as one list: map resources, monster parts and
// the cave ores. Costs are written in it, the menu's ITEMS page lists it, and
// its order is the column order of the icon sheet (assets/items.png), so an
// item's icon is just its index. Stone is the ore of a stone weapon and the
// ROCK resource at once (see ore_count in resource_node.h).
// (items_found in Player keeps a bit per item: no more than 32 of them.)
enum Item {
    ITEM_WOOD, ITEM_STONE, ITEM_GOLD, ITEM_FLOWER, ITEM_GRAVESTONE, ITEM_OILBLOOM,
    ITEM_HIDE, ITEM_BONE, ITEM_ESSENCE,
    ITEM_BRONZE, ITEM_EMERALD, ITEM_VEYRITE, ITEM_DRAVIUM, ITEM_KHARVITE, ITEM_REALITY_SHARD,
    ITEM_VINE, ITEM_RAFT_BOOK, ITEM_RAFT,
    ITEM_OLD_SPEARHEAD, ITEM_MOON_STEEL, ITEM_REAPERS_EDGE,   // found, one per dungeon of a kind
    ITEM_AXE_BOOK, ITEM_KATANA_BOOK, ITEM_SCYTHE_BOOK,          // teach a weapon, kept
    ITEM_COUNT   // keep last -- number of items, not an item
};

int&        item_slot(Player* p, Item it);    // the counter itself
int         item_count(const Player* p, Item it);
const char* item_name(Item it);               // capitals, for the menu font
Item        ore_item(Material m);             // the item a weapon of this ore is made from
Item        part_item(int part);              // the item a MonsterPart is
// Found means gained in play -- picked, mined, made, won -- not merely held:
// what a save or a debug gift put in the inventory has not
// been found. Called each frame with last frame's counts: an item whose count
// went up is found. `last` starts as a snapshot (items_note_gains with
// prime = true), which marks nothing.
void        items_note_gains(Player* p, int last[ITEM_COUNT], bool prime);
void        item_mark_found(Player* p, Item it);
bool        item_found(const Player* p, Item it);
// A material -- something gathered, mined or dropped, of which there is
// always more -- rather than a thing made, found once or learned (the raft,
// the special parts, the books).
inline bool item_is_material(Item it) { return it <= ITEM_VINE; }
// Where a thing that is not a material comes from, for the menu to say: "FOUND
// IN CATACOMBS", "SOLD IN A TOWN BOOK SHOP". Null for a material.
const char* item_source(Item it);

// What something costs: a few items and how many of each.
struct Cost   { Item item; int amount; };
struct Recipe { int n; Cost c[4]; };
bool can_afford(const Player* p, const Recipe& r);

// ── The recipe table ─────────────────────────────────────────────────────────
// Everything that can be made, one row each (src/crafting.cpp): what it makes,
// what goes in, and -- for a weapon -- how much of an ore on top, any ore, the
// best the player can pay for. A new thing to make (a raft, a sail, a bandage)
// is a new row and an icon; the menu reads only this.
struct Craft {
    bool       is_weapon;
    WeaponType weapon;    // the result, if is_weapon
    Item       item;      // the result otherwise
    int        n;         // fixed ingredients
    Cost       in[3];
    int        ore;       // plus this many of an ore (0: none)
    Item       needs;     // held but not used up -- the book that teaches it; ITEM_COUNT for none
    int        max;       // the most of it there is any use having; 0 for no limit
    Item       once;      // a weapon's special part, spent only the first time it is made; ITEM_COUNT for none
};

int          craft_count();
const Craft& craft_at(int i);
const char*  craft_name(const Craft& c);
// The ore it would be made in now: the best one the player can pay for --
// and, for a weapon they own, better than what it is made of, so it never
// offers a step down. -1 if none, or if it takes no ore.
int    craft_best_ore(const Player* p, const Craft& c);
// The full cost in a given ore (ignored if it takes none), for this player:
// a weapon they already own is re-made without its special part again.
Recipe craft_recipe(const Player* p, const Craft& c, int ore);
// What stops it being made that no amount of wood or ore will fix: the book
// it needs, or -- for a weapon not yet owned -- its special part. ITEM_COUNT
// if nothing.
Item   craft_missing(const Player* p, const Craft& c);
// Can it be made right now? Not without the book it needs, nor past its max.
bool   craft_ready(const Player* p, const Craft& c);
// Is the player holding all they can use of it already?
bool   craft_at_max(const Player* p, const Craft& c);
// Make it: pay, then add the item, or forge the weapon (re-forging one
// already owned keeps its upgrades) and take it in hand. False if not ready.
bool   craft_make(Player* p, const Craft& c);

// What an item is good for, by name: the crafts it goes into and any upgrade
// it pays for. Returns how many were written to out.
int item_uses(Item it, const char* out[], int max);

// ── Weapon upgrades, and taking a weapon in hand ─────────────────────────────
Recipe oil_recipe(const Weapon& w);           // its next oil level
Recipe echo_recipe(const Weapon& w);          // its next echo level
// Forge `type` in `m` directly (craft_make picks the ore for you).
bool craft_forge(Player* p, WeaponType type, Material m);
// Take an owned weapon in hand. False if it is not owned.
bool craft_equip(Player* p, WeaponType type);
// The next oil / echo level for an owned weapon. False if not owned, at the
// cap, or if it cannot be paid.
bool craft_oil(Player* p, WeaponType type);
bool craft_echo(Player* p, WeaponType type);

#endif
