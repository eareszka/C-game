#pragma once
#include "legacy_player_v4.h"

// Frozen footwear-era player layout (save versions 5 to 20): the worn
// footwear (1, now retired, is read as the bicycle worn) and, from version
// 18, the raft in use -- before the bicycle's own flag was appended.
struct LegacyPlayerV5 {
    LegacyPlayerV4 base;
    int footwear;
    int raft_worn;
};
