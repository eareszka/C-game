#pragma once
#include "legacy_player_v2.h"

// Frozen inventory-era player layout, before poison state was appended.
struct LegacyPlayerV3 {
    LegacyPlayerV2 base;
    int extra_items[98];
    unsigned long long found_extra[2];
};
