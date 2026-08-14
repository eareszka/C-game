#ifndef CASTLES_H
#define CASTLES_H

// ---------------------------------------------------------------------------
// Castle blueprints — one per castle, designed individually.
// Same char legend as towns.h. Cells left as ' ' keep the underlying terrain.
//
// Castle 0 — ocean    : a fortress built in the sea
// Castle 1 — mountain : the highest ground with room to stand on. It asks for
//                       CLIFF_LEVELS first and steps down a storey at a time
//                       until a clear 16x16 fits, so it lands on level 3 where
//                       the peak is broad and level 2 where it is not — level 3
//                       is only 900-6500 open tiles and its largest clear square
//                       runs 10-14, so on most seeds a castle does not fit on it
//                       at all. It asked for _5 until 2026-08-14, which does not
//                       exist, and so never placed anywhere.
// Castle 2 — lava     : a citadel in the wasteland's fire fields
// Castle 3 — dungeon  : found only by dungeon diving (no blueprint yet)
// ---------------------------------------------------------------------------

#define CASTLE_W 16
#define CASTLE_H 16

static const char* castle_ocean[]    = { nullptr };
static const char* castle_mountain[] = { nullptr };
static const char* castle_lava[]     = { nullptr };

static const char** castle_blueprints[3] = {
    castle_ocean, castle_mountain, castle_lava,
};

#endif
