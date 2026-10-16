#pragma once
#include "entity.h"
typedef struct {
    Stats stats;
    int level;

    // Visual/animation state — shared across all game states
    int   width, height;    // sprite size in pixels (28x40)
    int   facing;           // a Facing: the idle frame on the map sheet
    int   facing_locked;    // true after a hit/action until next direction key
    int   anim_step;
    float anim_timer;
    int   is_moving;

    // Last-pressed direction for resolving opposing key conflicts
    int   last_hdir;        // -1=left, +1=right
    int   last_vdir;        // -1=up,   +1=down

    // Inventory: counts indexed by ResourceType (include/resource_node.h,
    // which checks it has exactly this many).
    int   inventory[6];
    // Monster parts from battle drops, indexed by MonsterPart.
    int   parts[7];
    // Ore mined in caves, by Material. Stone is not kept here: it is the
    // ROCK inventory slot -- read both through ore_count().
    int   ore[7];
    // The raft and the book that teaches it (src/crafting.cpp): counts, as
    // every other item, though one of each is all there is.
    int   raft_book;
    int   raft;
    // The weapons' special parts (old spearhead, moon steel, reaper's edge),
    // each found once: every dungeon of its kind holds it until one is taken
    // (items_found says so), and the books that teach the axe, katana and
    // scythe -- crafting.h's ITEM_* order.
    int   treasures[3];
    int   books[3];
    // The sleeping bag: the uses left in it (0 = none; one bag at a time).
    int   sleeping_bag;
    // The boat's sail and the book that teaches it (the lighthouse keeper's,
    // src/story.cpp): one of each is all there is.
    int   sail_book;
    int   sail;
    // Aboard the boat (src/story.cpp story_boat_*): the sea is the floor and
    // the land a wall, until the boy docks at the wharf's tip again.
    int   at_sea;
    // Every item ever held, a bit per Item (include/crafting.h): what makes a
    // drop NEW on the victory panel. See items_note_gains().
    unsigned items_found;

    // Every weapon the player could own, one per shape; owned[] says which
    // they have. equipped is the one in hand -- read it via equipped_weapon().
    Weapon     arsenal[7];
    bool       owned[7];
    WeaponType equipped;
} LegacyPlayerV2;
