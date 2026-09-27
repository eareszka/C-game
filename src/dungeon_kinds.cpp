#include "dungeon_kinds.h"
#include "dungeon.h"   // material_for_difficulty
#include <stdio.h>

// Commonest first. The cave rows are written as counts so the whole column
// reads in one unit, but only their ratios matter (see the header).
constexpr DungeonKindDef DUNGEON_KINDS[DUNGEON_KIND_COUNT] = {
    // name            type                       material           target
    { "stone",         DUNGEON_ENT_CAVE,          MAT_STONE,         140 },
    { "bronze",        DUNGEON_ENT_CAVE,          MAT_BRONZE,        105 },
    { "grv_sm",        DUNGEON_ENT_GRAVEYARD_SM,  -1,                 85 },
    { "tree",          DUNGEON_ENT_LARGE_TREE,    -1,                 65 },
    { "emerald",       DUNGEON_ENT_CAVE,          MAT_EMERALD,        46 },
    { "veyrite",       DUNGEON_ENT_CAVE,          MAT_VEYRITE,        43 },
    { "grv_lg",        DUNGEON_ENT_GRAVEYARD_LG,  -1,                 36 },
    { "ruins",         DUNGEON_ENT_RUINS,         -1,                 30 },
    { "pyramid",       DUNGEON_ENT_PYRAMID,       -1,                 24 },
    { "oasis",         DUNGEON_ENT_OASIS,         -1,                 18 },
    { "dravium",       DUNGEON_ENT_CAVE,          MAT_DRAVIUM,        10 },
    { "kharvite",      DUNGEON_ENT_CAVE,          MAT_KHARVITE,        8 },
    { "stonehenge",    DUNGEON_ENT_STONEHENGE,    -1,                  6 },
    { "catacombs",     DUNGEON_ENT_CATACOMBS,     -1,                  5 },
    { "reality_shard", DUNGEON_ENT_CAVE,          MAT_REALITY_SHARD,   4 },
};

// Measured over 32 seeds (`make dngcensus`) against these numbers: the
// quota-capped kinds land exactly on target every world; tree, ruins and
// oasis come in a little under because their biomes run out of sites
// before they do; cave rows scale with how many mountains a world grew.
// That is the order holding on average -- a single world can still swap two
// neighbours whose counts are within a few of each other.

// A new archetype or material has to get a row here, and a row that names the
// wrong thing has to fail the build rather than make one kind unplaceable and
// another counted twice.
static_assert(DUNGEON_KIND_COUNT == 15, "the table above is written for 15 rows");
namespace {
constexpr bool kinds_cover_everything() {
    for (int t = 0; t < (int)DUNGEON_ENT_COUNT; t++) {
        if (t == (int)DUNGEON_ENT_CAVE) continue;
        int n = 0;
        for (const DungeonKindDef& k : DUNGEON_KINDS)
            if ((int)k.type == t && k.material < 0) n++;
        if (n != 1) return false;
    }
    for (int m = 0; m < (int)MAT_COUNT; m++) {
        int n = 0;
        for (const DungeonKindDef& k : DUNGEON_KINDS)
            if (k.type == DUNGEON_ENT_CAVE && k.material == m) n++;
        if (n != 1) return false;
    }
    for (const DungeonKindDef& k : DUNGEON_KINDS)
        if (k.target < 1) return false;   // a target of 0 is a kind nobody meets
    return true;
}
static_assert(kinds_cover_everything(),
              "every non-cave type and every material must appear exactly once");
}

int dungeon_kind_for_type(DungeonEntranceType t) {
    if (t == DUNGEON_ENT_CAVE) return -1;
    for (int k = 0; k < DUNGEON_KIND_COUNT; k++)
        if (DUNGEON_KINDS[k].type == t) return k;
    return -1;
}

int dungeon_kind_for_material(Material m) {
    for (int k = 0; k < DUNGEON_KIND_COUNT; k++)
        if (DUNGEON_KINDS[k].type == DUNGEON_ENT_CAVE && DUNGEON_KINDS[k].material == (int)m)
            return k;
    return -1;
}

int dungeon_kind_of(const DungeonEntrance* e) {
    if (e->type == DUNGEON_ENT_CAVE)
        return dungeon_kind_for_material(material_for_difficulty(e->difficulty));
    return dungeon_kind_for_type(e->type);
}

float dungeon_cave_share(Material m) {
    int sum = 0, mine = 0;
    for (int k = 0; k < DUNGEON_KIND_COUNT; k++) {
        if (DUNGEON_KINDS[k].type != DUNGEON_ENT_CAVE) continue;
        sum += DUNGEON_KINDS[k].target;
        if (DUNGEON_KINDS[k].material == (int)m) mine = DUNGEON_KINDS[k].target;
    }
    return sum ? (float)mine / (float)sum : 0.0f;
}

const char* dungeon_kind_label(int kind, char* buf, int n) {
    if (kind < 0 || kind >= DUNGEON_KIND_COUNT) { snprintf(buf, (size_t)n, "?"); return buf; }
    const DungeonKindDef& k = DUNGEON_KINDS[kind];
    if (k.type == DUNGEON_ENT_CAVE) snprintf(buf, (size_t)n, "cave:%s", k.name);
    else                            snprintf(buf, (size_t)n, "%s", k.name);
    return buf;
}
