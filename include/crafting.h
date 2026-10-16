#ifndef CRAFTING_H
#define CRAFTING_H

#include "entity.h"

// Everything the player carries, as one list: map resources, monster parts and
// the cave ores. Costs are written in it, the menu's ITEMS page lists it, and
// its order is the column order of the icon sheet (assets/items.png), so an
// item's icon is just its index. Stone is the ore of a stone weapon and the
// ROCK resource at once (see ore_count in resource_node.h).
// Existing IDs are stable; new items are appended and discovery spans multiple words.
enum Item {
    ITEM_WOOD, ITEM_STONE, ITEM_GOLD, ITEM_FLOWER, ITEM_GRAVESTONE, ITEM_OILBLOOM,
    ITEM_HIDE, ITEM_BONE, ITEM_ESSENCE,
    ITEM_BRONZE, ITEM_EMERALD, ITEM_VEYRITE, ITEM_DRAVIUM, ITEM_KHARVITE, ITEM_REALITY_SHARD,
    ITEM_VINE, ITEM_RAFT_BOOK, ITEM_RAFT,
    ITEM_OLD_SPEARHEAD, ITEM_MOON_STEEL, ITEM_REAPERS_EDGE,   // found once: every dungeon of its kind holds it until one is taken
    ITEM_AXE_BOOK, ITEM_KATANA_BOOK, ITEM_SCYTHE_BOOK,          // teach a weapon, kept
    ITEM_FEATHER, ITEM_WHITE_FUR,                               // dropped: Qique; the bears
    ITEM_SLEEPING_BAG,                                          // retired; retained only for old save IDs
    ITEM_WING_SKIN, ITEM_SAIL_BOOK, ITEM_SAIL,                  // the boat's sail: Ebigane's wing, the keeper's book, the sail itself (kept)
    ITEM_EYE_LENS,
    ITEM_HORN,
    ITEM_EVERLASTING_EMBER,
    ITEM_WATER_RING,
    ITEM_GILLS,
    ITEM_REGENERATIVE_TISSUE,
    ITEM_POISON_GLAND,
    ITEM_PLAGUE_RESIDUE,
    ITEM_LAVA_CHARM,
    ITEM_WIND_SINEW,
    ITEM_GRIP_SCALES,
    ITEM_ENCHANTED_WOOD,
    ITEM_BAND_AID,
    ITEM_ANTIDOTE,
    ITEM_CAMPFIRE,
    ITEM_MEDKIT,
    ITEM_BOMB,
    ITEM_SMOKE_BOMB,
    ITEM_ESCAPE_CHARM,
    ITEM_COLD_GEAR,
    ITEM_SPYGLASS,
    ITEM_DIVING_FINS,
    ITEM_SWIFT_BOOTS,
    ITEM_COMPASS,
    ITEM_O2_CHARM,
    ITEM_BINOCULARS,
    ITEM_KNIFE_BOOK,
    ITEM_DAGGER_BOOK,
    ITEM_CLUB_BOOK,
    ITEM_BAND_AID_BOOK,
    ITEM_ANTIDOTE_BOOK,
    ITEM_CAMPFIRE_BOOK,
    ITEM_MEDKIT_BOOK,
    ITEM_BOMB_BOOK,
    ITEM_SMOKE_BOMB_BOOK,
    ITEM_ESCAPE_CHARM_BOOK,
    ITEM_COLD_GEAR_BOOK,
    ITEM_HALBERD_BOOK,
    ITEM_SPYGLASS_BOOK,
    ITEM_DIVING_FINS_BOOK,
    ITEM_SWIFT_BOOTS_BOOK,
    ITEM_COMPASS_BOOK,
    ITEM_O2_CHARM_BOOK,
    ITEM_BINOCULARS_BOOK,
    ITEM_COUNT   // keep last -- number of items, not an item
};
static_assert(ITEM_COUNT <= INVENTORY_ITEM_CAPACITY, "inventory capacity");

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
// No count goes past this (the user, 2026-10-14): items_note_gains clamps
// every item each frame, so every way of gaining one is covered at once.
const int   ITEM_MAX = 999;
void        item_mark_found(Player* p, Item it);
bool        item_found(const Player* p, Item it);
// A material -- something gathered, mined or dropped, of which there is
// always more -- rather than a thing made, found once or learned (the raft,
// the special parts, the books).
bool item_is_material(Item it);
bool item_is_book(Item it);
int item_limit(Item it);
const char* item_description(Item it);
int item_icon(Item it);
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
    Cost       in[4];
    int        ore;       // plus this many of an ore (0: none)
    Item       needs;     // held but not used up -- the book that teaches it; ITEM_COUNT for none
    int        max;       // the most of it there is any use having; 0 for no limit
    Item       once;      // first-craft dungeon part
    int        price;     // reusable recipe book, in Gold
};

int          craft_count();
bool craft_buy_book(Player* p, const Craft& c);
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
