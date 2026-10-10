#include "crafting.h"
#include "resource_node.h"   // ResourceType, ore_count
#include "battle.h"          // weapon_name

int& item_slot(Player* p, Item it) {
    switch (it) {
        case ITEM_WOOD:       return p->inventory[RESOURCE_TREE];
        case ITEM_STONE:      return ore_count(p, MAT_STONE);
        case ITEM_GOLD:       return p->inventory[RESOURCE_GOLD];
        case ITEM_FLOWER:     return p->inventory[RESOURCE_FLOWER];
        case ITEM_GRAVESTONE: return p->inventory[RESOURCE_GRAVESTONE];
        case ITEM_OILBLOOM:   return p->inventory[RESOURCE_OILBLOOM];
        case ITEM_HIDE:       return p->parts[PART_HIDE];
        case ITEM_BONE:       return p->parts[PART_BONE];
        case ITEM_ESSENCE:    return p->parts[PART_ESSENCE];
        case ITEM_VINE:       return p->parts[PART_VINE];
        case ITEM_RAFT_BOOK:  return p->raft_book;
        case ITEM_RAFT:       return p->raft;
        case ITEM_OLD_SPEARHEAD: case ITEM_MOON_STEEL: case ITEM_REAPERS_EDGE:
            return p->treasures[it - ITEM_OLD_SPEARHEAD];
        case ITEM_AXE_BOOK: case ITEM_KATANA_BOOK: case ITEM_SCYTHE_BOOK:
            return p->books[it - ITEM_AXE_BOOK];
        case ITEM_FEATHER:       return p->parts[PART_FEATHER];
        case ITEM_WHITE_FUR:     return p->parts[PART_FUR];
        case ITEM_SLEEPING_BAG:  return p->sleeping_bag;
        default:              return ore_count(p, (Material)(MAT_BRONZE + (it - ITEM_BRONZE)));
    }
}

int item_count(const Player* p, Item it) { return item_slot(const_cast<Player*>(p), it); }

const char* item_name(Item it) {
    static const char* NAMES[ITEM_COUNT] = {
        "WOOD", "STONE", "GOLD", "FLOWER", "GRAVESTONE", "OILBLOOM",
        "HIDE", "BONE", "ESSENCE",
        "BRONZE", "EMERALD", "VEYRITE", "DRAVIUM", "KHARVITE", "REALITY SHARD",
        "VINE", "RAFT BOOK", "RAFT",
        "OLD SPEARHEAD", "MOON STEEL", "REAPER'S EDGE",
        "AXE BOOK", "KATANA BOOK", "SCYTHE BOOK",
        "FEATHER", "WHITE FUR", "SLEEPING BAG",
    };
    return (it >= 0 && it < ITEM_COUNT) ? NAMES[it] : "?";
}

static_assert(ITEM_COUNT <= 32, "Player::items_found has a bit per Item");

const char* item_source(Item it) {
    switch (it) {
        case ITEM_OLD_SPEARHEAD: return "FOUND IN RUINS";
        case ITEM_MOON_STEEL:    return "FOUND AT STONEHENGE";
        case ITEM_REAPERS_EDGE:  return "FOUND IN CATACOMBS";
        case ITEM_RAFT_BOOK:     return "FOUND IN THE FIRST TOWN";
        case ITEM_AXE_BOOK: case ITEM_KATANA_BOOK: case ITEM_SCYTHE_BOOK:
            return "SOLD IN A TOWN BOOK SHOP";
        case ITEM_RAFT:          return "MADE";
        case ITEM_SLEEPING_BAG:  return "MADE";
        default:                 return nullptr;
    }
}

void items_note_gains(Player* p, int last[ITEM_COUNT], bool prime) {
    for (int it = 0; it < ITEM_COUNT; it++) {
        int now = item_count(p, (Item)it);
        if (!prime && now > last[it]) item_mark_found(p, (Item)it);
        last[it] = now;
    }
}

void item_mark_found(Player* p, Item it) { p->items_found |= 1u << it; }

bool item_found(const Player* p, Item it) { return (p->items_found >> it) & 1u; }

Item part_item(int part) {
    switch (part) {
        case PART_BONE:    return ITEM_BONE;
        case PART_ESSENCE: return ITEM_ESSENCE;
        case PART_VINE:    return ITEM_VINE;
        case PART_FEATHER: return ITEM_FEATHER;
        case PART_FUR:     return ITEM_WHITE_FUR;
        default:           return ITEM_HIDE;
    }
}

Item ore_item(Material m) {
    return m == MAT_STONE ? ITEM_STONE : (Item)(ITEM_BRONZE + (m - MAT_BRONZE));
}

bool can_afford(const Player* p, const Recipe& r) {
    for (int i = 0; i < r.n; i++)
        if (item_count(p, r.c[i].item) < r.c[i].amount) return false;
    return true;
}

static bool pay(Player* p, const Recipe& r) {
    if (!can_afford(p, r)) return false;
    for (int i = 0; i < r.n; i++) item_slot(p, r.c[i].item) -= r.c[i].amount;
    return true;
}

// ── The recipe table ─────────────────────────────────────────────────────────
// Every weapon takes three of an ore, which sets how hard it hits, and its
// own makings: a wooden haft for most; bone for the club; the raft's vine to
// lash the axe's head on; and for the halberd, katana and scythe a special
// part found once in a dungeon of their kind -- spent the first time only.
// The axe, katana and scythe also need their book. The raft is the way off the
// starting island: logs lashed with the vine a Treesqueak drops, made by
// following the book in the town.
#define NO ITEM_COUNT
static const Craft CRAFTS[] = {
    //       weapon          item       n  ingredients                            ore needs              max once
    { true,  WEAPON_KNIFE,   NO,        1, { { ITEM_WOOD, 2 } },                    3, NO,                 0, NO },
    { true,  WEAPON_CLUB,    NO,        1, { { ITEM_BONE, 3 } },                    3, NO,                 0, NO },
    { true,  WEAPON_DAGGER,  NO,        1, { { ITEM_WOOD, 2 } },                    3, NO,                 0, NO },
    { true,  WEAPON_AXE,     NO,        2, { { ITEM_WOOD, 2 }, { ITEM_VINE, 2 } },  3, ITEM_AXE_BOOK,      0, NO },
    { true,  WEAPON_HALBERD, NO,        1, { { ITEM_WOOD, 2 } },                    3, NO,                 0, ITEM_OLD_SPEARHEAD },
    { true,  WEAPON_KATANA,  NO,        1, { { ITEM_WOOD, 2 } },                    3, ITEM_KATANA_BOOK,   0, ITEM_MOON_STEEL },
    { true,  WEAPON_SCYTHE,  NO,        1, { { ITEM_WOOD, 2 } },                    3, ITEM_SCYTHE_BOOK,   0, ITEM_REAPERS_EDGE },
    { false, WEAPON_KNIFE,   ITEM_RAFT, 2, { { ITEM_WOOD, 10 }, { ITEM_VINE, 3 } }, 0, ITEM_RAFT_BOOK,     1, NO },
    // The sleeping bag: hard to make on purpose -- a hide shell, Qique's
    // feathers, and the white fur only the hard bears drop.
    { false, WEAPON_KNIFE,   ITEM_SLEEPING_BAG, 3, { { ITEM_HIDE, 4 }, { ITEM_FEATHER, 6 }, { ITEM_WHITE_FUR, 3 } }, 0, NO, 1, NO },
};
#undef NO
static const int CRAFT_COUNT = (int)(sizeof(CRAFTS) / sizeof(CRAFTS[0]));

int          craft_count()       { return CRAFT_COUNT; }
const Craft& craft_at(int i)     { return CRAFTS[i]; }
const char*  craft_name(const Craft& c) { return c.is_weapon ? weapon_name(c.weapon) : item_name(c.item); }

static bool owns_result(const Player* p, const Craft& c) {
    return c.is_weapon ? p->owned[c.weapon] : item_count(p, c.item) > 0;
}

Recipe craft_recipe(const Player* p, const Craft& c, int ore) {
    Recipe r = {};
    for (int i = 0; i < c.n; i++) r.c[r.n++] = c.in[i];
    if (c.once != ITEM_COUNT && !owns_result(p, c)) r.c[r.n++] = { c.once, 1 };
    if (c.ore > 0 && ore >= 0) r.c[r.n++] = { ore_item((Material)ore), c.ore };
    return r;
}

Item craft_missing(const Player* p, const Craft& c) {
    if (c.needs != ITEM_COUNT && item_count(p, c.needs) <= 0) return c.needs;
    if (c.once != ITEM_COUNT && !owns_result(p, c) && item_count(p, c.once) <= 0) return c.once;
    return ITEM_COUNT;
}

int craft_best_ore(const Player* p, const Craft& c) {
    if (c.ore <= 0) return -1;
    int floor = (c.is_weapon && p->owned[c.weapon]) ? (int)p->arsenal[c.weapon].material : -1;
    for (int m = MAT_COUNT - 1; m > floor; m--)
        if (can_afford(p, craft_recipe(p, c, m))) return m;
    return -1;
}

bool craft_at_max(const Player* p, const Craft& c) {
    return !c.is_weapon && c.max > 0 && item_count(p, c.item) >= c.max;
}

bool craft_ready(const Player* p, const Craft& c) {
    if (craft_missing(p, c) != ITEM_COUNT) return false;
    if (craft_at_max(p, c)) return false;
    return c.ore > 0 ? craft_best_ore(p, c) >= 0 : can_afford(p, craft_recipe(p, c, -1));
}

bool craft_make(Player* p, const Craft& c) {
    if (c.is_weapon) {
        int ore = craft_best_ore(p, c);
        return ore >= 0 && craft_forge(p, c.weapon, (Material)ore);
    }
    if (!craft_ready(p, c) || !pay(p, craft_recipe(p, c, -1))) return false;
    item_slot(p, c.item) += c.item == ITEM_SLEEPING_BAG ? SLEEPING_BAG_USES : 1;
    return true;
}

bool craft_sleep(Player* p) {
    if (p->sleeping_bag <= 0 || p->stats.hp >= p->stats.max_hp) return false;
    p->stats.hp = p->stats.max_hp;
    p->sleeping_bag--;
    return true;
}

int item_uses(Item it, const char* out[], int max) {
    int n = 0;
    bool ore = false;
    for (int m = 0; m < MAT_COUNT; m++) if (ore_item((Material)m) == it) ore = true;
    // What it goes into. Something most weapons take (wood, any ore) reads as
    // one word, WEAPONS, rather than a list of six names.
    const char* weapons[WEAPON_COUNT];
    int nw = 0;
    for (int i = 0; i < CRAFT_COUNT; i++) {
        const Craft& c = CRAFTS[i];
        bool in = (ore && c.ore > 0) || c.needs == it || c.once == it;
        for (int k = 0; k < c.n; k++) if (c.in[k].item == it) in = true;
        if (!in) continue;
        if (c.is_weapon) weapons[nw++] = weapon_name(c.weapon);
        else if (n < max) out[n++] = item_name(c.item);
    }
    if (nw >= 4) { if (n < max) out[n++] = "WEAPONS"; }
    else for (int i = 0; i < nw && n < max; i++) out[n++] = weapons[i];
    if (it == ITEM_OILBLOOM && n < max) out[n++] = "FASTER WEAPONS";
    if (it == ITEM_ESSENCE && n < max)  out[n++] = "MORE SHOTS";
    return n;
}

// ── Weapon upgrades ──────────────────────────────────────────────────────────
// Oil is an oilbloom a level, ten levels a weapon; echo is two essence more a
// level -- the rarer drop for the stronger upgrade.
Recipe oil_recipe(const Weapon& w)   { (void)w; return { 1, { { ITEM_OILBLOOM, 1 } } }; }
Recipe echo_recipe(const Weapon& w)  { return { 1, { { ITEM_ESSENCE, 2 * (w.echo + 1) } } }; }

// The table's row for a weapon.
static const Craft& weapon_craft(WeaponType type) {
    for (int i = 0; i < CRAFT_COUNT; i++)
        if (CRAFTS[i].is_weapon && CRAFTS[i].weapon == type) return CRAFTS[i];
    return CRAFTS[0];
}

bool craft_forge(Player* p, WeaponType type, Material m) {
    Weapon& w = p->arsenal[type];
    const Craft& c = weapon_craft(type);
    if (!(p->owned[type] && w.material == m)) {
        if (craft_missing(p, c) != ITEM_COUNT) return false;   // no book, or no special part
        if (!pay(p, craft_recipe(p, c, m))) return false;
        w.material = m;
        p->owned[type] = true;
    }
    p->equipped = type;
    return true;
}

bool craft_equip(Player* p, WeaponType type) {
    if (!p->owned[type]) return false;
    p->equipped = type;
    return true;
}

bool craft_oil(Player* p, WeaponType type) {
    Weapon& w = p->arsenal[type];
    if (!p->owned[type] || w.oil >= WEAPON_OIL_MAX || !pay(p, oil_recipe(w))) return false;
    w.oil++;
    return true;
}

bool craft_echo(Player* p, WeaponType type) {
    Weapon& w = p->arsenal[type];
    if (!p->owned[type] || w.echo >= WEAPON_ECHO_MAX || !pay(p, echo_recipe(w))) return false;
    w.echo++;
    return true;
}
