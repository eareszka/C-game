#pragma once
#include "legacy_player_v3.h"

// Frozen poison-era player layout, before toggleable footwear.
struct LegacyPlayerV4 {
    LegacyPlayerV3 base;
    int poisoned;
    float poison_timer;
};
