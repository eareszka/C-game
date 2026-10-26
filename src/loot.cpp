#include "loot.h"
#include <algorithm>
#include <cstring>
struct Drop { int enemy; Item item; };
static const Drop DROPS[] = {
    { 0, ITEM_HIDE },
    { 1, ITEM_HIDE },
    { 9, ITEM_HIDE },
    { 17, ITEM_HIDE },
    { 50, ITEM_HIDE },
    { 53, ITEM_HIDE },
    { 55, ITEM_HIDE },
    { 79, ITEM_HIDE },
    { 86, ITEM_HIDE },
    { 87, ITEM_HIDE },
    { 2, ITEM_VINE },
    { 58, ITEM_VINE },
    { 61, ITEM_VINE },
    { 63, ITEM_VINE },
    { 3, ITEM_FEATHER },
    { 57, ITEM_FEATHER },
    { 67, ITEM_FEATHER },
    { 68, ITEM_FEATHER },
    { 75, ITEM_FEATHER },
    { 8, ITEM_FLOWER },
    { 22, ITEM_FLOWER },
    { 51, ITEM_FLOWER },
    { 70, ITEM_FLOWER },
    { 8, ITEM_OILBLOOM },
    { 22, ITEM_OILBLOOM },
    { 51, ITEM_OILBLOOM },
    { 70, ITEM_OILBLOOM },
    { 20, ITEM_WHITE_FUR },
    { 28, ITEM_WHITE_FUR },
    { 41, ITEM_WHITE_FUR },
    { 48, ITEM_WHITE_FUR },
    { 62, ITEM_WHITE_FUR },
    { 10, ITEM_WING_SKIN },
    { 12, ITEM_WING_SKIN },
    { 83, ITEM_WING_SKIN },
    { 38, ITEM_BONE },
    { 59, ITEM_BONE },
    { 62, ITEM_BONE },
    { 64, ITEM_BONE },
    { 66, ITEM_BONE },
    { 6, ITEM_EYE_LENS },
    { 11, ITEM_EYE_LENS },
    { 52, ITEM_EYE_LENS },
    { 77, ITEM_HORN },
    { 84, ITEM_HORN },
    { 90, ITEM_HORN },
    { 7, ITEM_EVERLASTING_EMBER },
    { 24, ITEM_EVERLASTING_EMBER },
    { 73, ITEM_EVERLASTING_EMBER },
    { 81, ITEM_EVERLASTING_EMBER },
    { 97, ITEM_EVERLASTING_EMBER },
    { 18, ITEM_WATER_RING },
    { 49, ITEM_WATER_RING },
    { 51, ITEM_WATER_RING },
    { 14, ITEM_GILLS },
    { 15, ITEM_GILLS },
    { 43, ITEM_GILLS },
    { 46, ITEM_GILLS },
    { 96, ITEM_GILLS },
    { 60, ITEM_REGENERATIVE_TISSUE },
    { 71, ITEM_REGENERATIVE_TISSUE },
    { 89, ITEM_REGENERATIVE_TISSUE },
    { 5, ITEM_POISON_GLAND },
    { 21, ITEM_POISON_GLAND },
    { 25, ITEM_POISON_GLAND },
    { 32, ITEM_POISON_GLAND },
    { 35, ITEM_POISON_GLAND },
    { 56, ITEM_POISON_GLAND },
    { 69, ITEM_POISON_GLAND },
    { 74, ITEM_POISON_GLAND },
    { 29, ITEM_ESSENCE },
    { 30, ITEM_ESSENCE },
    { 34, ITEM_ESSENCE },
    { 36, ITEM_ESSENCE },
    { 37, ITEM_ESSENCE },
    { 42, ITEM_ESSENCE },
    { 44, ITEM_ESSENCE },
    { 80, ITEM_ESSENCE },
    { 88, ITEM_ESSENCE },
    { 95, ITEM_ESSENCE },
    { 99, ITEM_PLAGUE_RESIDUE },
    { 7, ITEM_LAVA_CHARM },
    { 13, ITEM_LAVA_CHARM },
    { 97, ITEM_LAVA_CHARM },
    { 16, ITEM_WIND_SINEW },
    { 45, ITEM_WIND_SINEW },
    { 27, ITEM_GRIP_SCALES },
    { 39, ITEM_GRIP_SCALES },
    { 72, ITEM_GRIP_SCALES },
    { 85, ITEM_GRIP_SCALES },
    { 93, ITEM_GRIP_SCALES },
    { 98, ITEM_GRIP_SCALES },
    { 78, ITEM_ENCHANTED_WOOD },
};
void battle_loot(int enemy, int cancellations, const LootRolls& rolls, int out[ITEM_COUNT]) {
    std::fill(out, out + ITEM_COUNT, 0);
    for (const Drop& d : DROPS) if (d.enemy == enemy) out[d.item]++;
    // The great bat drops a whole sail's worth (6): beaten once, it never
    // roosts again (persist.h), and the sail must not be out of reach.
    if (enemy == 12) out[ITEM_WING_SKIN] += 5;
    if (enemy == 31 || enemy == 33) {
        static const int chances[MAT_COUNT] = { 10000, 4000, 2000, 1000, 500, 200, 50 };
        for (int m = 0; m < MAT_COUNT; m++)
            if (m == MAT_STONE || (rolls.ore[m] >= 0 && rolls.ore[m] < chances[m])) out[ore_item((Material)m)]++;
    }
    const int bonus = std::min(6, std::max(0, cancellations));
    for (int i = 0; i < bonus; i++) out[((i + rolls.common_start) & 1) ? ITEM_STONE : ITEM_WOOD]++;
}
void credit_loot(Player* p, const int rolled[ITEM_COUNT], int actual[ITEM_COUNT], bool fresh[ITEM_COUNT]) {
    for (int i = 0; i < ITEM_COUNT; i++) {
        Item it = (Item)i;
        actual[i] = std::min(std::max(0, rolled[i]), std::max(0, item_limit(it) - item_count(p, it)));
        fresh[i] = actual[i] > 0 && !item_found(p, it);
        item_slot(p, it) += actual[i];
        if (actual[i]) item_mark_found(p, it);
    }
}
