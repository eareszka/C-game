#ifndef CASTLES_H
#define CASTLES_H

// ---------------------------------------------------------------------------
// Castle blueprints — one per castle, designed individually.
// Same char legend as towns.h. Cells left as ' ' keep the underlying terrain.
//
// Castle 0 — ocean    : a fortress built in the sea
// Castle 1 — mountain : perched at the world's highest peak (TILE_CLIFF_5)
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
