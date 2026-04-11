#ifndef TOWNS_H
#define TOWNS_H

// ---------------------------------------------------------------------------
// Hand-authored town blueprints — ASCII art → tile IDs.
//
// Char legend (add more as needed):
//   '.' = TILE_GRASS
//   ',' = TILE_PATH
//   'H' = TILE_HUB      (placeholder for a building/house tile)
//   'W' = TILE_WATER    (decorative pond / fountain)
//   'T' = TILE_TREE     (overlay — placed on top of base tile)
//   ' ' = blueprint placeholder (magenta marker — undesigned cell)
//
// TOWN_W / TOWN_H define the stamped footprint.  Each array can have fewer
// rows than TOWN_H — missing rows are treated as all spaces (blueprint fill).
// Rows shorter than TOWN_W are padded with spaces automatically.
// End each town array with nullptr (the stamp function stops there).
// ---------------------------------------------------------------------------

#define TOWN_W 156
#define TOWN_H 156

#define VILLAGE_W 30
#define VILLAGE_H 30
#define NUM_VILLAGE_VARIANTS 4

// ---------------------------------------------------------------------------
// Town 0 — starting town (placed over the hub at map centre, every seed)
// ---------------------------------------------------------------------------
static const char* town_0[] = {
    nullptr
};

// ---------------------------------------------------------------------------
// Town 1 — coastal town (placed on the shoreline, location varies by seed)
// ---------------------------------------------------------------------------
static const char* town_1[] = {
    nullptr
};

// ---------------------------------------------------------------------------
// Town 2 — random location A
// ---------------------------------------------------------------------------
static const char* town_2[] = {
    nullptr
};

static const char** all_towns[3] = {
    town_0, town_1, town_2,
};

// ---------------------------------------------------------------------------
// Village blueprints — 4 variants, randomly assigned per village.
// Villages are smaller than towns and don't pre-fill with blueprint marker,
// so undesigned cells leave the underlying terrain unchanged.
// ---------------------------------------------------------------------------
static const char* village_0[] = { nullptr };
static const char* village_1[] = { nullptr };
static const char* village_2[] = { nullptr };
static const char* village_3[] = { nullptr };

static const char** all_villages[NUM_VILLAGE_VARIANTS] = {
    village_0, village_1, village_2, village_3,
};

#endif
