#pragma once
#include "crafting.h"
struct LootRolls { int ore[MAT_COUNT]; int common_start; };
void battle_loot(int enemy, int cancellations, const LootRolls& rolls, int out[ITEM_COUNT]);
void credit_loot(Player* p, const int rolled[ITEM_COUNT], int actual[ITEM_COUNT], bool fresh[ITEM_COUNT]);
