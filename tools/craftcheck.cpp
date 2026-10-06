// The crafting rules, checked: the recipe table, best-ore choice, re-forging
// keeping upgrades, caps, the raft and its book, and what USED FOR says.
// Exits non-zero on the first broken rule.  make craftcheck && ./craftcheck
#include "crafting.h"
#include "battle.h"     // weapon_profile, faster_fire_rate, faster_damage
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static const Craft& craft_for(WeaponType w) {
    for (int i = 0; i < craft_count(); i++)
        if (craft_at(i).is_weapon && craft_at(i).weapon == w) return craft_at(i);
    assert(!"no craft for that weapon");
    return craft_at(0);
}

static const Craft& craft_for(Item it) {
    for (int i = 0; i < craft_count(); i++)
        if (!craft_at(i).is_weapon && craft_at(i).item == it) return craft_at(i);
    assert(!"no craft for that item");
    return craft_at(0);
}

int main() {
    Player p = {};
    for (int w = 0; w < WEAPON_COUNT; w++) p.arsenal[w] = Weapon{ (WeaponType)w, MAT_STONE };
    p.owned[WEAPON_KNIFE] = true;
    p.equipped = WEAPON_KNIFE;
    const Craft& axe = craft_for(WEAPON_AXE);

    // Holding nothing: no ore on offer, nothing ready.
    assert(craft_best_ore(&p, axe) == -1 && !craft_ready(&p, axe));

    // A bronze axe takes 3 bronze, 2 wood and 2 vine, and its book; the best
    // affordable ore wins over stone.
    item_slot(&p, ITEM_BRONZE) = 3;
    item_slot(&p, ITEM_WOOD)   = 2;
    item_slot(&p, ITEM_VINE)   = 2;
    item_slot(&p, ITEM_STONE)  = 3;
    assert(!craft_ready(&p, axe) && craft_missing(&p, axe) == ITEM_AXE_BOOK);   // no book yet
    assert(!craft_make(&p, axe));
    item_slot(&p, ITEM_AXE_BOOK) = 1;
    assert(craft_best_ore(&p, axe) == MAT_BRONZE);
    assert(craft_make(&p, axe));
    assert(p.owned[WEAPON_AXE] && p.equipped == WEAPON_AXE && p.arsenal[WEAPON_AXE].material == MAT_BRONZE);
    assert(item_count(&p, ITEM_BRONZE) == 0 && item_count(&p, ITEM_WOOD) == 0 && item_count(&p, ITEM_VINE) == 0);
    assert(item_count(&p, ITEM_AXE_BOOK) == 1);   // kept

    // The club is bone, not wood.
    const Craft& club = craft_for(WEAPON_CLUB);
    item_slot(&p, ITEM_STONE) = 3;
    item_slot(&p, ITEM_WOOD)  = 9;
    assert(!craft_ready(&p, club));
    item_slot(&p, ITEM_BONE)  = 3;
    assert(craft_make(&p, club) && item_count(&p, ITEM_BONE) == 0 && item_count(&p, ITEM_WOOD) == 9);
    assert(craft_equip(&p, WEAPON_AXE));

    // The scythe: its book, then its special part, used up the first time only.
    const Craft& scythe = craft_for(WEAPON_SCYTHE);
    item_slot(&p, ITEM_STONE) = 3;
    item_slot(&p, ITEM_WOOD)  = 2;
    assert(craft_missing(&p, scythe) == ITEM_SCYTHE_BOOK);
    item_slot(&p, ITEM_SCYTHE_BOOK) = 1;
    assert(craft_missing(&p, scythe) == ITEM_REAPERS_EDGE && !craft_make(&p, scythe));
    item_slot(&p, ITEM_REAPERS_EDGE) = 1;
    assert(craft_make(&p, scythe) && item_count(&p, ITEM_REAPERS_EDGE) == 0 && item_count(&p, ITEM_SCYTHE_BOOK) == 1);
    // Re-made in a better ore, no edge is wanted again.
    item_slot(&p, ITEM_BRONZE) = 3;
    item_slot(&p, ITEM_WOOD)   = 2;
    assert(craft_missing(&p, scythe) == ITEM_COUNT && craft_make(&p, scythe));
    assert(p.arsenal[WEAPON_SCYTHE].material == MAT_BRONZE);
    assert(craft_equip(&p, WEAPON_AXE));
    item_slot(&p, ITEM_WOOD) = 0;

    // Upgrades: oil costs a flower a level, and stops at the cap of 10.
    item_slot(&p, ITEM_OILBLOOM) = WEAPON_OIL_MAX + 9;
    assert(!craft_oil(&p, WEAPON_KATANA));          // not owned
    for (int i = 0; i < WEAPON_OIL_MAX; i++) assert(craft_oil(&p, WEAPON_AXE));
    assert(!craft_oil(&p, WEAPON_AXE));
    assert(WEAPON_OIL_MAX == 10);
    assert(p.arsenal[WEAPON_AXE].oil == WEAPON_OIL_MAX && item_count(&p, ITEM_OILBLOOM) == 9);

    item_slot(&p, ITEM_ESSENCE) = 2;
    assert(craft_echo(&p, WEAPON_AXE) && p.arsenal[WEAPON_AXE].echo == 1);
    assert(!craft_echo(&p, WEAPON_AXE));            // the next level wants 4

    // A bronze axe is never offered stone, even with stone and wood to hand.
    item_slot(&p, ITEM_WOOD) = 2;
    assert(craft_best_ore(&p, axe) == -1);

    // Re-making it in emerald keeps the levels.
    item_slot(&p, ITEM_EMERALD) = 3;
    item_slot(&p, ITEM_VINE)    = 2;
    assert(craft_make(&p, axe));
    assert(p.arsenal[WEAPON_AXE].material == MAT_EMERALD && p.arsenal[WEAPON_AXE].oil == WEAPON_OIL_MAX);
    assert(craft_equip(&p, WEAPON_KNIFE) && p.equipped == WEAPON_KNIFE);
    assert(!craft_equip(&p, WEAPON_KATANA));

    // The raft: wood and vine are not enough without the book.
    item_slot(&p, ITEM_RAFT_BOOK) = 0;
    const Craft& raft = craft_for(ITEM_RAFT);
    item_slot(&p, ITEM_WOOD) = 10;
    item_slot(&p, ITEM_VINE) = 3;
    assert(!craft_ready(&p, raft) && !craft_make(&p, raft));
    // With the book it is made, the book kept and the materials spent ...
    item_slot(&p, ITEM_RAFT_BOOK) = 1;
    assert(craft_ready(&p, raft) && craft_make(&p, raft));
    assert(item_count(&p, ITEM_RAFT) == 1 && item_count(&p, ITEM_RAFT_BOOK) == 1);
    assert(item_count(&p, ITEM_WOOD) == 0 && item_count(&p, ITEM_VINE) == 0);
    // ... and one is all there is any use for.
    item_slot(&p, ITEM_WOOD) = 10;
    item_slot(&p, ITEM_VINE) = 3;
    assert(craft_at_max(&p, raft) && !craft_ready(&p, raft));

    // USED FOR: wood goes into weapons and the raft; vine into the raft and
    // the axe; bone into the club; each part and book into its weapon;
    // oilbloom into faster weapons; gold into nothing yet.
    const char* uses[8];
    int n = item_uses(ITEM_WOOD, uses, 8);
    assert(n == 2 && !strcmp(uses[0], "RAFT") && !strcmp(uses[1], "WEAPONS"));
    n = item_uses(ITEM_VINE, uses, 8);
    assert(n == 2 && !strcmp(uses[0], "RAFT") && !strcmp(uses[1], "AXE"));
    n = item_uses(ITEM_BONE, uses, 8);
    assert(n == 1 && !strcmp(uses[0], "CLUB"));
    n = item_uses(ITEM_REAPERS_EDGE, uses, 8);
    assert(n == 1 && !strcmp(uses[0], "SCYTHE"));
    n = item_uses(ITEM_KATANA_BOOK, uses, 8);
    assert(n == 1 && !strcmp(uses[0], "KATANA"));
    n = item_uses(ITEM_RAFT_BOOK, uses, 8);
    assert(n == 1 && !strcmp(uses[0], "RAFT"));
    n = item_uses(ITEM_OILBLOOM, uses, 8);
    assert(n == 1 && !strcmp(uses[0], "FASTER WEAPONS"));
    assert(item_uses(ITEM_GOLD, uses, 8) == 0);

    // Materials are what there is always more of; books and parts are not.
    assert(item_is_material(ITEM_VINE) && !item_is_material(ITEM_RAFT) && !item_is_material(ITEM_RAFT_BOOK));
    assert(!item_is_material(ITEM_REAPERS_EDGE) && !item_is_material(ITEM_SCYTHE_BOOK));
    assert(!strcmp(item_source(ITEM_REAPERS_EDGE), "FOUND IN CATACOMBS"));

    // Stone is the rock slot.
    item_slot(&p, ITEM_STONE) = 7;
    assert(p.inventory[1] == 7);

    // FASTER's scaling: level 0 is the weapon as it is; at the top every
    // weapon fires at Touhou's rate; damage per second grows by the same
    // factor for all; and so the weapons keep their order at every level.
    printf("FASTER   lvl0 rate/dmg/dps         lvl5 rate/dmg/dps         lvl10 rate/dmg/dps\n");
    float prev[WEAPON_COUNT];
    for (int lv = 0; lv <= WEAPON_OIL_MAX; lv++) {
        float dps[WEAPON_COUNT];
        for (int w = 0; w < WEAPON_COUNT; w++) {
            ProjectileProfile pp = weapon_profile((WeaponType)w);
            float r = faster_fire_rate(pp.fire_rate, lv), d = faster_damage(pp.fire_rate, pp.damage, lv);
            dps[w] = r * d;
            if (lv == 0) assert(fabsf(r - pp.fire_rate) < 1e-4f && fabsf(d - pp.damage) < 1e-4f);
            if (lv == WEAPON_OIL_MAX) {
                assert(fabsf(r - TOUHOU_FIRE_RATE) < 1e-3f);
                assert(fabsf(dps[w] / (pp.fire_rate * pp.damage) - FASTER_DPS_AT_MAX) < 1e-3f);
            }
        }
        if (lv > 0)   // same order as the level before, for every pair
            for (int a = 0; a < WEAPON_COUNT; a++)
                for (int b = 0; b < WEAPON_COUNT; b++)
                    assert((prev[a] < prev[b]) == (dps[a] < dps[b]));
        for (int w = 0; w < WEAPON_COUNT; w++) prev[w] = dps[w];
    }
    for (int w = 0; w < WEAPON_COUNT; w++) {
        ProjectileProfile pp = weapon_profile((WeaponType)w);
        printf("%-8s", weapon_name((WeaponType)w));
        for (int lv = 0; lv <= WEAPON_OIL_MAX; lv += WEAPON_OIL_MAX / 2) {
            float r = faster_fire_rate(pp.fire_rate, lv), d = faster_damage(pp.fire_rate, pp.damage, lv);
            printf("  %5.2f/s %5.2f %6.1f   ", r, d, r * d);
        }
        printf("\n");
    }

    puts("craftcheck: ok");
    return 0;
}
