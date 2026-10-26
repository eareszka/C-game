#include "crafting.h"
#include <algorithm>
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
        case ITEM_WING_SKIN:     return p->parts[PART_WING];
        case ITEM_SAIL_BOOK:     return p->sail_book;
        case ITEM_SAIL:          return p->sail;
        default:
            if (it >= ITEM_BRONZE && it <= ITEM_REALITY_SHARD)
                return ore_count(p, (Material)(MAT_BRONZE + (it - ITEM_BRONZE)));
            return p->extra_items[(int)it - LEGACY_ITEM_COUNT];
    }
}

int item_count(const Player* p, Item it) { return item_slot(const_cast<Player*>(p), it); }

const char* item_name(Item it) {
    static const char* NAMES[ITEM_COUNT] = {
        "WOOD",
        "STONE",
        "GOLD",
        "FLOWER",
        "GRAVESTONE",
        "OILBLOOM",
        "HIDE",
        "BONE",
        "SPIRIT ESSENCE",
        "BRONZE",
        "EMERALD",
        "VEYRITE",
        "DRAVIUM",
        "KHARVITE",
        "REALITY SHARD",
        "VINE",
        "RAFT BOOK",
        "RAFT",
        "OLD SPEARHEAD",
        "MOON STEEL",
        "REAPER'S EDGE",
        "AXE BOOK",
        "KATANA BOOK",
        "SCYTHE BOOK",
        "FEATHER",
        "FUR",
        "SLEEPING BAG",
        "WING SKIN",
        "SAIL BOOK",
        "SAIL",
        "EYE LENS",
        "HORN",
        "EVERLASTING EMBER",
        "WATER RING",
        "GILLS",
        "REGENERATIVE TISSUE",
        "POISON GLAND",
        "PLAGUE RESIDUE",
        "LAVA CHARM",
        "WIND SINEW",
        "GRIP SCALES",
        "ENCHANTED WOOD",
        "BAND-AID",
        "ANTIDOTE",
        "CAMPFIRE",
        "MEDKIT",
        "BOMB",
        "SMOKE BOMB",
        "ESCAPE CHARM",
        "COLD-WEATHER GEAR",
        "SPYGLASS",
        "DIVING FINS",
        "SWIFT BOOTS",
        "COMPASS",
        "O2 CHARM",
        "BINOCULARS",
        "KNIFE BOOK",
        "DAGGER BOOK",
        "CLUB BOOK",
        "BAND-AID BOOK",
        "ANTIDOTE BOOK",
        "CAMPFIRE BOOK",
        "MEDKIT BOOK",
        "BOMB BOOK",
        "SMOKE BOMB BOOK",
        "ESCAPE CHARM BOOK",
        "COLD-WEATHER GEAR BOOK",
        "HALBERD BOOK",
        "SPYGLASS BOOK",
        "DIVING FINS BOOK",
        "SWIFT BOOTS BOOK",
        "COMPASS BOOK",
        "O2 CHARM BOOK",
        "BINOCULARS BOOK",
    };
    return (it >= 0 && it < ITEM_COUNT) ? NAMES[it] : "?";
}


const char* item_source(Item it) {
    if (item_is_book(it)) return "SOLD IN A TOWN BOOK SHOP";
    switch (it) {
        case ITEM_OLD_SPEARHEAD: return "FOUND IN RUINS";
        case ITEM_MOON_STEEL: return "FOUND AT STONEHENGE";
        case ITEM_REAPERS_EDGE: return "FOUND IN CATACOMBS";
        default: return item_is_material(it) ? nullptr : "MADE";
    }
}

void items_note_gains(Player* p, int last[ITEM_COUNT], bool prime) {
    for (int it = 0; it < ITEM_COUNT; it++) {
        if (item_count(p, (Item)it) > item_limit((Item)it)) item_slot(p, (Item)it) = item_limit((Item)it);
        int now = item_count(p, (Item)it);
        if (!prime && now > last[it]) item_mark_found(p, (Item)it);
        last[it] = now;
    }
}

void item_mark_found(Player* p, Item it) {
    if (it < 0 || it >= ITEM_COUNT) return;
    if (it < 32) p->items_found |= 1u << it;
    else p->found_extra[(it - 32) / 64] |= 1ull << ((it - 32) % 64);
}

bool item_found(const Player* p, Item it) {
    if (it < 0 || it >= ITEM_COUNT) return false;
    return it < 32 ? (p->items_found >> it) & 1u : (p->found_extra[(it - 32) / 64] >> ((it - 32) % 64)) & 1ull;
}

Item part_item(int part) {
    switch (part) {
        case PART_BONE:    return ITEM_BONE;
        case PART_ESSENCE: return ITEM_ESSENCE;
        case PART_VINE:    return ITEM_VINE;
        case PART_FEATHER: return ITEM_FEATHER;
        case PART_FUR:     return ITEM_WHITE_FUR;
        case PART_WING:    return ITEM_WING_SKIN;
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
#include "craft_catalog.inc"
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
    item_slot(p, c.item)++;
    item_mark_found(p, c.item);
    if (c.item == ITEM_RAFT) p->raft_worn = 1;   // made to be used: worn at once
    return true;
}

int item_uses(Item it, const char* out[], int max) {
    int n = 0;
    if (it == ITEM_GOLD && max > 0) out[n++] = "RECIPE BOOKS";
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
    if (type < 0 || type >= WEAPON_COUNT || m < 0 || m >= MAT_COUNT) return false;
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

bool item_is_material(Item it) {
    return (it >= ITEM_WOOD && it <= ITEM_VINE) || it == ITEM_FEATHER || it == ITEM_WHITE_FUR || it == ITEM_WING_SKIN || (it >= ITEM_EYE_LENS && it <= ITEM_ENCHANTED_WOOD);
}
bool item_is_book(Item it) {
    for (const Craft& c : CRAFTS) if (c.needs == it) return true;
    return false;
}
int item_limit(Item it) {
    if (it == ITEM_SLEEPING_BAG) return 0;
    if (item_is_book(it)) return 1;
    for (const Craft& c : CRAFTS) if (!c.is_weapon && c.item == it) return c.max;
    return ITEM_MAX;
}
bool craft_buy_book(Player* p, const Craft& c) {
    if (item_count(p, c.needs) || item_count(p, ITEM_GOLD) < c.price) return false;
    item_slot(p, ITEM_GOLD) -= c.price;
    item_slot(p, c.needs) = 1;
    item_mark_found(p, c.needs);
    return true;
}
int item_icon(Item it) {
    if (it < LEGACY_ITEM_COUNT) return it;
    if (item_is_book(it)) return ITEM_RAFT_BOOK;
    if (item_is_material(it)) return it == ITEM_EVERLASTING_EMBER ? ITEM_OILBLOOM : ITEM_ESSENCE;
    return ITEM_RAFT;
}
bool item_use_band_aid(Player* p) {
    if (item_count(p, ITEM_BAND_AID) <= 0 || p->stats.hp <= 0 || p->stats.hp >= p->stats.max_hp) return false;
    p->stats.hp += std::min(HP_PER_BAR, p->stats.max_hp - p->stats.hp);
    item_slot(p, ITEM_BAND_AID)--;
    return true;
}

bool item_use_medkit(Player* p) {
    if (item_count(p, ITEM_MEDKIT) <= 0 || p->stats.hp <= 0 || p->stats.hp >= p->stats.max_hp) return false;
    p->stats.hp = p->stats.max_hp;
    item_slot(p, ITEM_MEDKIT)--;
    return true;
}

bool item_use_antidote(Player* p) {
    if (!p->poisoned || p->stats.hp <= 0 || item_count(p, ITEM_ANTIDOTE) <= 0) return false;
    p->poisoned = 0;
    p->poison_timer = 0;
    item_slot(p, ITEM_ANTIDOTE)--;
    return true;
}

static int footwear_kind(Item it) {
    return it==ITEM_SWIFT_BOOTS?FOOTWEAR_SWIFT_BOOTS:it==ITEM_DIVING_FINS?FOOTWEAR_DIVING_FINS:FOOTWEAR_NONE;
}
bool item_footwear_equipped(const Player* p, Item it) {
    int kind=footwear_kind(it);
    return kind!=FOOTWEAR_NONE && p->footwear==kind && item_count(p,it)>0;
}
bool item_equip_footwear(Player* p, Item it, bool equip) {
    int kind=footwear_kind(it);
    if (kind==FOOTWEAR_NONE || (equip && item_count(p,it)<=0)) return false;
    if (equip) p->footwear=kind;
    else if (p->footwear==kind) p->footwear=FOOTWEAR_NONE;
    return true;
}
bool item_equip_swift_boots(Player* p, bool equip) {
    return item_equip_footwear(p,ITEM_SWIFT_BOOTS,equip);
}

bool item_raft_worn(const Player* p) { return p->raft_worn && p->raft > 0; }
bool item_equip_raft(Player* p, bool equip) {
    if (equip && p->raft <= 0) return false;
    p->raft_worn = equip ? 1 : 0;
    return true;
}

const char* item_description(Item it) {
    switch (it) {
        case ITEM_RAFT: return "WHILE WORN, CARRIES YOU OVER WATER.";
        case ITEM_BAND_AID: return "RESTORES 1 HEALTH BAR. EXPLORATION ONLY.";
        case ITEM_MEDKIT: return "RESTORES FULL HEALTH. EXPLORATION ONLY.";
        case ITEM_ANTIDOTE: return "CURES POISON. EXPLORATION ONLY.";
        case ITEM_CAMPFIRE: return "PLACES A PERMANENT WARP POINT";
        case ITEM_BOMB: return "AN EXPLOSIVE FOR BATTLES";
        case ITEM_SMOKE_BOMB: return "BREAKS ENEMY PURSUIT";
        case ITEM_ESCAPE_CHARM: return "RETURNS INSIDE THE ENTRANCE YOU USED. REUSABLE.";
        case ITEM_COLD_GEAR: return "PROTECTS AGAINST COLD";
        case ITEM_SWIFT_BOOTS: return "50% FASTER WALKING AND SPRINTING.";
        case ITEM_DIVING_FINS: return "50% FASTER SWIMMING. SHARES THE FOOTWEAR SLOT.";
        case ITEM_O2_CHARM: return "PREVENTS UNDERWATER OXYGEN LOSS";
        case ITEM_SPYGLASS: return "SEE TIER 2 WHEN ZOOMED OUT";
        case ITEM_BINOCULARS: return "SEE TIER 1 WHEN ZOOMED OUT";
        case ITEM_COMPASS: return "REVEALS THE ENTIRE DUNGEON MAP";
        case ITEM_LAVA_CHARM: return "RAFT PROTECTION AGAINST LAVA";
        case ITEM_PLAGUE_RESIDUE: return "POISON COATING FOR A WEAPON";
        default: return nullptr;
    }
}
