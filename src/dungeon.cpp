#include "fc_palette.h"
#include "dungeon.h"
#include "collision.h"
#include "core.h"
#include "resource_node.h"   // RESOURCE_GOLD inventory index
#include "combat.h"          // weapon_swing_update/draw -- shared with the overworld harvest mechanic
#include "crafting.h"        // Item, item_slot -- a dungeon's treasure
#include "enemy.h"           // enemy_is_boss: bosses are placed, never spawned at random
#include <SDL2/SDL_image.h>
#include <string.h>
#include <math.h>
#include <vector>
#include <algorithm>
#include "dungeon_wall_tiles.inc"   // tools/gen_dungeon_wall_tiles.py: where the interiors' wall pieces sit
#include "cave_rock.inc"            // tools/gen_cave_tiles.py: the cave rock's pieces in a cave's block

// ── Color palettes per dungeon type ───────────────────────────────────────
struct DngPalette { SDL_Color wall, floor, entry, exit_; };

static const DngPalette PALETTES[DUNGEON_ENT_COUNT] = {
    // CAVE — a fallback row, and only that. Both colours here are overridden
    // per material by dng_palette(): the floor comes from MaterialDef::floor
    // and the wall from MaterialDef::minimap_wall. What is left reaching this
    // row is the minimap of a cave whose ore is out of range, and the case
    // where assets/tileset.png fails to load. The main view never uses it --
    // it draws the material's own rock art, see cave_bake() below.
    {{ 60, 65,100,255},{ 90, 80, 74,255},{200,175, 40,255},{180, 45, 45,255}},
    // RUINS
    {{ 75, 65, 55,255},{110, 98, 82,255},{200,175, 40,255},{180, 45, 45,255}},
    // GRAVEYARD_SM
    {{ 32, 28, 45,255},{ 58, 52, 70,255},{200,175, 40,255},{100, 50,180,255}},
    // GRAVEYARD_LG
    {{ 28, 24, 40,255},{ 52, 47, 65,255},{200,175, 40,255},{100, 50,180,255}},
    // OASIS
    {{ 20, 75, 65,255},{ 38,115, 95,255},{200,175, 40,255},{ 30,190,170,255}},
    // PYRAMID
    {{115, 95, 42,255},{155,132, 68,255},{200,175, 40,255},{220,190, 50,255}},
    // STONEHENGE  — warm orange walls, near-black walkable corridors
    {{210,112, 20,255},{ 10,  5,  2,255},{200,175, 40,255},{ 80,110,200,255}},
    // LARGE_TREE
    {{ 20, 55, 18,255},{ 33, 85, 28,255},{200,175, 40,255},{ 55,200, 50,255}},
    // CATACOMBS — a step darker again than GRAVEYARD_LG, which is itself a step
    // darker than SM. The three read as one family getting deeper underground.
    {{ 18, 16, 28,255},{ 38, 34, 50,255},{200,175, 40,255},{100, 50,180,255}},
};

// ── ASCII chars per dungeon type [wall, floor] ────────────────────────────
struct DngAscii { char wall, floor; };
static const DngAscii ASCII_CHARS[DUNGEON_ENT_COUNT] = {
    {'#', '.'}, // CAVE
    {'+', ','}, // RUINS
    {'#', '.'}, // GRAVEYARD_SM
    {'#', '.'}, // GRAVEYARD_LG
    {'=', '.'}, // OASIS
    {'#', '.'}, // PYRAMID
    {'O', '.'}, // STONEHENGE
    {'*', '.'}, // LARGE_TREE
    {'#', ','}, // CATACOMBS — graveyard walls, older floor
};

// Both tables above are indexed by dungeon type and both need the same range
// clamp: dungeon_draw() and dungeon_minimap_draw() share this one.
static inline int dng_palette_index(const DungeonMap* dmap) {
    int ci = (int)dmap->type;
    return (ci < 0 || ci >= DUNGEON_ENT_COUNT) ? 0 : ci;
}

// ── Cave materials ────────────────────────────────────────────────────────
// One material per enemy band (see spawner_enemy_base() below), gated on the
// cave's difficulty so the strong stuff is far out or high up.
//
// Each material's rock is its OWN art. tools/gen_cave_tiles.py lays the cave
// rock's pieces into a block of assets/tileset.png for each, in that ore's
// tones, and a cave samples the one its material picks -- see cave_block_col()
// further down. Baked, not a colour-mod: a multiply can darken a hue but never
// add one, so gold and red rock were out of reach.
struct MaterialDef {
    const char* name;
    SDL_Color   floor;          // the cave floor's colour on the minimap
    SDL_Color   minimap_wall;   // per-pixel wall colour on the minimap
    float       max_difficulty; // upper bound of this material's band
    // The floor as the cave draws it (cave_bake; user, 2026-10-12): the wall's
    // own cobble lying flat -- its stones, and the lines between them;
    // ground_rounded, large rounded cobbles in the oblique view instead
    // (Reality Shard's: black stone outlined in light purple). The minimap
    // keeps `floor`: these sit too near some ores' minimap walls, and black
    // would vanish on its panel.
    SDL_Color   ground, ground_line;
    bool        ground_rounded;
};

// Thresholds are quantile-calibrated from 3026 cave systems across 8 worlds
// (`make oreprof`), NOT a linear split. difficulty averages two normalised
// terms so it clusters near 0.5, and caves are cut into mountains so its
// elevation term is never 0: the observed range is only 0.142..0.771, and a
// linear tier = difficulty*7 put 80% of caves in two middle tiers and left
// Reality Shard unreachable.
//
// How wide each band is -- what share of a world's caves holds each material
// -- is not decided here. It is the cave rows of DUNGEON_KINDS
// (include/dungeon_kinds.h), where every kind of dungeon has its place in one
// order; oreprof reads those shares and prints the cut points that realise
// them. Re-run it and paste when that table or the shape of worldgen changes.
static const MaterialDef MATERIALS[MAT_COUNT] = {
    // name             floor              minimap wall       up to
    // the ground: grey, olive brown, green, indigo, dark red, a darker olive
    // gold, and black stone outlined in light purple (the user's, an ore each)
    { "Stone",        {108,108,116,255}, { 74, 74, 80,255}, 0.3722f, {0x59,0x59,0x65,255}, {0x47,0x47,0x51,255}, false },
    { "Bronze",       {110, 88, 58,255}, { 52, 30, 16,255}, 0.4520f, {0x60,0x50,0x28,255}, {0x46,0x34,0x22,255}, false },   // its rock's shade: { 92, 74, 48} drew as the floor's own palette colour
    { "Emerald",      { 70,105, 78,255}, { 46, 78, 58,255}, 0.4935f, {0x29,0x63,0x3e,255}, {0x23,0x54,0x36,255}, false },
    { "Veyrite",      { 90, 80, 74,255}, { 60, 65,100,255}, 0.5728f, {0x37,0x38,0x7b,255}, {0x30,0x1b,0x5a,255}, false },
    { "Dravium",      {110, 64, 60,255}, { 92, 44, 44,255}, 0.6285f, {0x42,0x16,0x18,255}, {0x31,0x11,0x13,255}, false },
    { "Kharvite",     {120,105, 55,255}, {104, 88, 40,255}, 0.6958f, {0x5c,0x46,0x16,255}, {0x40,0x30,0x10,255}, false },
    { "Reality Shard",{ 30, 28, 34,255}, { 24, 22, 30,255}, 2.0f   , {0x00,0x00,0x00,255}, {0xb6,0x9c,0xee,255}, true  },
};

// Which material a cave of this difficulty holds. Monotonic by construction --
// further out or higher is never a weaker material.
Material material_for_difficulty(float difficulty) {
    for (int m = 0; m < MAT_COUNT - 1; m++)
        if (difficulty < MATERIALS[m].max_difficulty) return (Material)m;
    return (Material)(MAT_COUNT - 1);
}

float material_min_difficulty(Material m) {
    int mi = (int)m;
    if (mi <= 0) return 0.0f;
    if (mi >= MAT_COUNT) mi = MAT_COUNT - 1;
    return MATERIALS[mi - 1].max_difficulty;
}

const char* material_name(Material m) {
    int mi = (int)m;
    if (mi < 0 || mi >= MAT_COUNT) mi = 0;
    return MATERIALS[mi].name;
}

#include "ore_tones.inc"

SDL_Color material_color(Material m, int tone) {
    int mi = (int)m;
    if (mi < 0 || mi >= MAT_COUNT) mi = 0;
    const unsigned char* c = ORE_TONES[1 + mi][tone & 3];
    return SDL_Color{ c[0], c[1], c[2], 255 };
}

// Which material this cave is made of. Split out from cave_material() because
// the atlas block a cave draws its rock from is derived from the same index
// (see cave_block_col() below), and a second copy of this clamp is exactly
// how the two would drift apart.
static inline int cave_material_index(const DungeonMap* dmap) {
    int mi = (int)dmap->ore;
    if (mi < 0 || mi >= MAT_COUNT) mi = 0;
    return mi;
}

static inline const MaterialDef& cave_material(const DungeonMap* dmap) {
    return MATERIALS[cave_material_index(dmap)];
}

// The palette actually drawn with: PALETTES for every dungeon type but a cave,
// whose floor and minimap wall come from its material instead. Returned by
// value so a caller cannot write through to the const table. Both the main view
// and the minimap go through this -- route only one and the minimap stays a
// fixed colour while the cave changes around it.
static DngPalette dng_palette(const DungeonMap* dmap) {
    DngPalette p = PALETTES[dng_palette_index(dmap)];
    if (dmap->type == DUNGEON_ENT_CAVE) {
        const MaterialDef& md = cave_material(dmap);
        p.floor = md.floor;
        p.wall  = md.minimap_wall;
    }
    return p;
}

// The ways out of a dungeon, drawn on the north wall at each (gen_cave_
// entrances.py lays them on the sheet): a ladder up the wall's face for a
// dungeon entered down a hole -- a length of it (row LADDER_ROW) and its foot
// (LADDER_ROW + 1), column LADDER_COL0 + material -- or the doorway of the
// built entrance it came in by, the size of that entrance's own, standing
// with its foot on row DOOR_FOOT_ROW.
// A block of stonehenge's barrow maze (see carve_stonehenge_layout): wide, deep, tall.
static const int BRW_BW = 32, BRW_BD = 16, BRW_BZ = 64;
static const int LADDER_COL0 = 7, LADDER_ROW = 14, DOOR_FOOT_ROW = 15;
// The caves' rock: a block of the sheet an ore, stamped by
// tools/gen_cave_tiles.py. KEEP IN SYNC with OUT_COL0 / BLOCK_COLS there;
// there is no way to check that agreement from here.
static const int CAVE_ART_COL0    = 33;
static const int CAVE_ART_COLS    = 5;
static inline int cave_block_col(const DungeonMap* dmap) {     // this cave's block, its first column
    return CAVE_ART_COL0 + cave_material_index(dmap) * CAVE_ART_COLS;
}
struct WayOutDoor { int col, w, h, foot; };   // sheet column, cells wide and tall, the row its foot is on

// Which way out a kind of dungeon has: a doorway, or (null) the ladder.
static const WayOutDoor* way_out_door(const DungeonMap* dmap) {
    static const WayOutDoor RUINS = {21, 3, 3, DOOR_FOOT_ROW}, PYRAMID = {24, 2, 2, DOOR_FOOT_ROW},
                            TREE = {26, 2, 2, DOOR_FOOT_ROW}, GRAVE = {28, 1, 2, DOOR_FOOT_ROW},
                            CHURCH = {29, 1, 3, DOOR_FOOT_ROW},
                            // the step pyramid's, recoloured by tools/gen_dungeon_wall_tiles.py
                            STEP_PYRAMID = {WALL_COL0[WALL_MAYA] + PYR_DOOR_COL, 2, 2, WALL_ROW0[WALL_MAYA] + PYR_DOOR_ROW + 1};
    if (dmap->type == DUNGEON_ENT_PYRAMID && dmap->step_pyramid) return &STEP_PYRAMID;
    switch (dmap->type) {
        case DUNGEON_ENT_RUINS:        return &RUINS;
        case DUNGEON_ENT_PYRAMID:      return &PYRAMID;
        case DUNGEON_ENT_LARGE_TREE:   return &TREE;
        case DUNGEON_ENT_GRAVEYARD_SM:
        case DUNGEON_ENT_GRAVEYARD_LG: return &GRAVE;
        case DUNGEON_ENT_CATACOMBS:    return &CHURCH;
        case DUNGEON_ENT_CAVE: {                         // the arch a mouth is, in the cave's own rock
            static WayOutDoor cave;
            cave = { cave_block_col(dmap) + CAVE_PIECE[CP_ARCH][0], 2, 2, CAVE_PIECE[CP_ARCH][1] + 1 };
            return &cave;
        }
        default:                       return nullptr;   // the stonehenge pit, the oasis
    }
}

// How many tiles tall the wall's face is over a ladder out: the stonehenge's
// walls stand four tiles high, the rest one.
static int way_out_face(const DungeonMap* dmap) {
    return dmap->type == DUNGEON_ENT_STONEHENGE ? BRW_BZ / 16 : 1;     // the barrow's wall
}

// The dungeons that lie open (user): known whole from the start and all in
// sight -- stonehenge's barrow under its sky, the graveyard's walkways in the
// dark. No fog, no dimming.
static bool dungeon_open_sight(const DungeonMap* dmap) {
    return dmap->type == DUNGEON_ENT_STONEHENGE || dmap->type == DUNGEON_ENT_GRAVEYARD_SM ||
           dmap->type == DUNGEON_ENT_GRAVEYARD_LG || dmap->type == DUNGEON_ENT_OASIS;
}

// The graveyards: walkways floating in the dark (carve_graveyard_walkways).
static bool gyw_walkways(const DungeonMap* dmap) {
    return dmap->type == DUNGEON_ENT_GRAVEYARD_SM || dmap->type == DUNGEON_ENT_GRAVEYARD_LG;
}

// The dungeons whose ways out the layout stands where they belong -- the
// graveyard's walls on its landings, stonehenge's ladders on flat back walls,
// the giant tree's hollow on its middle floor, the catacombs' door at the
// hall's end -- so binding only says which is which and nothing moves them.
static bool terraced(const DungeonMap* dmap);
static bool fixed_ways(const DungeonMap* dmap) {
    return gyw_walkways(dmap) || dmap->type == DUNGEON_ENT_STONEHENGE || dmap->type == DUNGEON_ENT_OASIS ||
           terraced(dmap) || dmap->type == DUNGEON_ENT_CATACOMBS;
}
// The terraced dungeons (terraces_join): the giant tree, and the caves, a
// mouth an arch on its own level's floor.
static bool terraced(const DungeonMap* dmap) {
    return dmap->type == DUNGEON_ENT_LARGE_TREE || dmap->type == DUNGEON_ENT_CAVE;
}
// A cave's way out that is a ladder down a hole outside (the user): inside, a
// ladder up the back wall into a hatch, on its portal's tile, not the arch.
static const int CAVE_HATCH_UP = 4;                       // cells from the floor to the hatch's top
static bool cave_ladder_out(const DungeonMap* d, int p) {
    return d->type == DUNGEON_ENT_CAVE && d->want_hole[p];
}

// A way out's wall stands across the back of its landing, GYW_FOOT deep: its
// front face's foot (world v), its west end (world u), and the floor tile
// before its middle where the portal is -- the first tile row whose middle is
// in front of the wall's foot, so the tile above it is under the wall.
static const int GYW_FOOT = 8;
static int gyw_wall_v(const DungeonMap* d, int w) { return (d->gyw_way_v[w] + 3) * 16 - GYW_FOOT; }
static int gyw_wall_u(const DungeonMap* d, int w) { return (d->gyw_way_u[w] - 1) * 16; }
static void gyw_way_tile(const DungeonMap* d, int w, int* tx, int* ty) {
    int yf = d->gyw_oy - gyw_wall_v(d, w);
    *ty = (yf - 8) / 16 + 1;
    int v = d->gyw_oy - (*ty * 16 + 8);
    *tx = (d->gyw_ox + gyw_wall_u(d, w) + 32 + v) / 16;
}

// The barrow's (stonehenge's) way out w: the floor tile before its ladder --
// the first tile row in front of its wall's foot, so the tile above it is
// under the wall. The ladder itself stands where the picture has it, which is
// on no tile's middle (barrow_way_x and _d).
static void barrow_way_tile(const DungeonMap* d, int w, int* tx, int* ty) {
    int yf = d->barrow_oy - d->barrow_way_d[w];            // the first floor row before the wall
    *ty = (yf - 8 + 15) / 16;
    *tx = (d->barrow_ox + d->barrow_way_x[w] + (d->barrow_oy - 1 - (*ty * 16 + 8))) / 16;
}

// Whether art pixel (ax, ay) is walkway a player may stand on: in one of the
// rectangles once taken back into the world, and not under a way out's wall.
// with_walls: only the walls that stand (a way out with a portal on it);
// without, under either.
static bool gyw_on_path(const DungeonMap* d, int ax, int ay, bool with_walls) {
    int v = d->gyw_oy - ay, u = ax - d->gyw_ox - v;
    bool on = false;
    for (int i = 0; i < d->num_gyw_rects && !on; i++) {
        const auto& r = d->gyw_rects[i];
        on = u >= r.u0 && u <= r.u1 && v >= r.v0 && v <= r.v1;
    }
    if (!on) return false;
    for (int w = 0; w < 2; w++) {
        int wv = gyw_wall_v(d, w), wu = gyw_wall_u(d, w);
        if (v < wv || v >= wv + GYW_FOOT || u < wu || u >= wu + 64) continue;
        if (!with_walls) return false;
        int tx, ty;
        gyw_way_tile(d, w, &tx, &ty);
        for (int p = 0; p < d->num_portals; p++)
            if (d->portals[p].tx == tx && d->portals[p].ty == ty) return false;
    }
    return true;
}

// ── LCG RNG ───────────────────────────────────────────────────────────────
static uint32_t rng_next(uint32_t* s) {
    *s = *s * 1664525u + 1013904223u;
    return (*s >> 16) & 0x7FFF;
}

// ── BSP room generator ────────────────────────────────────────────────────
#define MAX_BSP_NODES 127
#define MIN_PART      12   // smallest partition we'll attempt to split
#define MIN_ROOM       5   // smallest room dimension in tiles
#define ROOM_MARGIN    2   // gap between room edge and partition edge
#define CORR_W         2   // corridor width in tiles

// Per-generation BSP tuning (reset before each BSP run)
static int s_bsp_max_depth = 4;
static int s_bsp_min_part  = MIN_PART;

struct BSPNode {
    int x, y, w, h;       // partition bounds
    int lc, rc;            // child indices (-1 = leaf)
    int rx, ry, rw, rh;   // room (leaves only)
    int rcx, rcy;          // room centre (propagated up)
};

static BSPNode s_bsp[MAX_BSP_NODES];
static int     s_bsp_n;
static int     s_leaves[MAX_BSP_NODES];
static int     s_leaf_n;

static void collect_leaves(int idx) {
    if (s_bsp[idx].lc == -1) {
        if (s_leaf_n < MAX_BSP_NODES) s_leaves[s_leaf_n++] = idx;
        return;
    }
    collect_leaves(s_bsp[idx].lc);
    collect_leaves(s_bsp[idx].rc);
}

static void bsp_split(int idx, int depth, uint32_t* rng) {
    BSPNode* n = &s_bsp[idx];
    n->lc = n->rc = -1;

    bool can_w = n->w >= 2 * s_bsp_min_part;
    bool can_h = n->h >= 2 * s_bsp_min_part;

    if (s_bsp_n + 2 > MAX_BSP_NODES || depth >= s_bsp_max_depth || (!can_w && !can_h)) {
        // Leaf — place a room inside the partition
        int span_w = n->w - 2 * ROOM_MARGIN;
        int span_h = n->h - 2 * ROOM_MARGIN;
        if (span_w < MIN_ROOM) span_w = MIN_ROOM;
        if (span_h < MIN_ROOM) span_h = MIN_ROOM;

        int rw = MIN_ROOM + (int)(rng_next(rng) % (unsigned)(span_w - MIN_ROOM + 1));
        int rh = MIN_ROOM + (int)(rng_next(rng) % (unsigned)(span_h - MIN_ROOM + 1));

        int rx_off = ROOM_MARGIN
                   + (int)(rng_next(rng) % (unsigned)(n->w - 2*ROOM_MARGIN - rw + 1));
        int ry_off = ROOM_MARGIN
                   + (int)(rng_next(rng) % (unsigned)(n->h - 2*ROOM_MARGIN - rh + 1));

        n->rx  = n->x + rx_off;
        n->ry  = n->y + ry_off;
        n->rw  = rw;
        n->rh  = rh;
        n->rcx = n->rx + rw / 2;
        n->rcy = n->ry + rh / 2;
        return;
    }

    // Split the longer axis
    bool split_w = can_w && (!can_h || n->w >= n->h);
    int lc = s_bsp_n++, rc = s_bsp_n++;
    n->lc = lc; n->rc = rc;

    if (split_w) {
        int range = n->w - 2 * s_bsp_min_part;
        int split = s_bsp_min_part + (range > 0 ? (int)(rng_next(rng) % (unsigned)range) : 0);
        s_bsp[lc] = { n->x,         n->y, split,        n->h, -1, -1 };
        s_bsp[rc] = { n->x + split, n->y, n->w - split, n->h, -1, -1 };
    } else {
        int range = n->h - 2 * s_bsp_min_part;
        int split = s_bsp_min_part + (range > 0 ? (int)(rng_next(rng) % (unsigned)range) : 0);
        s_bsp[lc] = { n->x, n->y,         n->w, split,        -1, -1 };
        s_bsp[rc] = { n->x, n->y + split, n->w, n->h - split, -1, -1 };
    }

    bsp_split(lc, depth + 1, rng);
    bsp_split(rc, depth + 1, rng);

    // Propagate left child's centre up (corridor fallback)
    n->rcx = s_bsp[lc].rcx;
    n->rcy = s_bsp[lc].rcy;
}

static void carve_rect(DungeonMap* dmap, int x, int y, int w, int h, uint8_t tile) {
    if (tile != DNG_WALL) { if (w < 1) w = 1; if (h < 1) h = 1; }
    for (int dy = 0; dy < h; dy++)
        for (int dx = 0; dx < w; dx++) {
            int tx = x + dx, ty = y + dy;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// Oblique-projection parallelogram: row r shifts left by r tiles going down.
static void carve_parallelogram(DungeonMap* dmap, int x, int y, int w, int h, uint8_t tile) {
    if (tile != DNG_WALL) { if (w < 1) w = 1; if (h < 1) h = 1; }
    for (int r = 0; r < h; r++)
        for (int c = 0; c < w; c++) {
            int tx = x - r + c, ty = y + r;
            if (tx >= 0 && tx < DMAP_W && ty >= 0 && ty < DMAP_H)
                dmap->tiles[ty][tx] = tile;
        }
}

// L-shaped corridor: horizontal leg at y1, vertical leg at x2.
static void carve_corridor(DungeonMap* dmap, int x1, int y1, int x2, int y2, int w = CORR_W) {
    if (x1 > x2) { int t; t=x1;x1=x2;x2=t; t=y1;y1=y2;y2=t; }
    carve_rect(dmap, x1, y1, x2 - x1 + w, w, DNG_FLOOR);
    int miny = y1 < y2 ? y1 : y2;
    int maxy = y1 > y2 ? y1 : y2;
    carve_rect(dmap, x2, miny, w, maxy - miny + w, DNG_FLOOR);
}

// Oblique L-shaped corridor for stonehenge-style dungeons:
// horizontal leg is a flat rectangle, vertical leg is a parallelogram
// (each row going down shifts left by 1 — matching oblique projection).
static void carve_oblique_corridor(DungeonMap* dmap, int x1, int y1, int x2, int y2) {
    if (x1 > x2) { int t; t=x1;x1=x2;x2=t; t=y1;y1=y2;y2=t; }
    // Horizontal leg — flat
    carve_rect(dmap, x1, y1, x2 - x1 + CORR_W, CORR_W, DNG_FLOOR);
    // Vertical leg — oblique parallelogram
    int miny = y1 < y2 ? y1 : y2;
    int maxy = y1 > y2 ? y1 : y2;
    carve_parallelogram(dmap, x2, miny, CORR_W, maxy - miny + CORR_W, DNG_FLOOR);
}

// ── Room-carving generator (river-style for caves and giant trees) ────────

static void paint_room_brush(DungeonMap* dmap, int ix, int iy, int room_rx, int room_ry) {
    for (int by = -room_ry; by <= room_ry; by++) {
        for (int bx = -room_rx; bx <= room_rx; bx++) {
            float nx = (room_rx > 0) ? (float)bx / room_rx : 0;
            float ny = (room_ry > 0) ? (float)by / room_ry : 0;
            if (nx*nx + ny*ny > 1.0f) continue;
            int px = ix + bx, py = iy + by;
            if (px >= 1 && px < DMAP_W-1 && py >= 1 && py < DMAP_H-1)
                dmap->tiles[py][px] = DNG_FLOOR;
        }
    }
}

static void paint_passage_brush(DungeonMap* dmap, int ix, int iy, int passage_w) {
    int half = passage_w / 2;
    for (int by = -half; by <= half; by++) {
        for (int bx = -half; bx <= half; bx++) {
            int px = ix + bx, py = iy + by;
            if (px >= 1 && px < DMAP_W-1 && py >= 1 && py < DMAP_H-1)
                dmap->tiles[py][px] = DNG_FLOOR;
        }
    }
}

static void march_room_path(DungeonMap* dmap, int sx, int sy,
                            float dir_x, float dir_y,
                            unsigned int seed,
                            int max_steps,
                            int jitter_range,
                            int room_min_rx, int room_max_rx,
                            int room_min_ry, int room_max_ry,
                            int passage_w,
                            int depth) {
    int rx = sx, ry = sy;
    int sign_x = (dir_x >= 0.0f) ? 1 : -1;
    int sign_y = (dir_y >= 0.0f) ? 1 : -1;
    bool primary_x = (fabsf(dir_x) >= fabsf(dir_y));
    float ratio = primary_x
        ? (fabsf(dir_x) > 0.0f ? fabsf(dir_y) / fabsf(dir_x) : 0.0f)
        : (fabsf(dir_y) > 0.0f ? fabsf(dir_x) / fabsf(dir_y) : 0.0f);
    float acc = 0.0f;
    int steps = 0;
    float smooth_j = 0.0f;
    int step_counter = 0;

    while (steps++ < max_steps) {
        seed = seed * 1664525u + 1013904223u;
        int range = 2 * jitter_range + 1;
        float kick = (float)((int)(seed >> 16) % range - jitter_range);
        smooth_j = smooth_j * 0.97f + kick * 0.03f;
        int jitter = (int)smooth_j;

        if (primary_x) {
            rx += sign_x;
            if (rx < 2 || rx >= DMAP_W-2) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            ry += sign_y * sec + jitter;
            if (ry < 2) ry = 2;
            if (ry >= DMAP_H-2) ry = DMAP_H - 3;
        } else {
            ry += sign_y;
            if (ry < 2 || ry >= DMAP_H-2) break;
            acc += ratio;
            int sec = (int)acc; acc -= sec;
            rx += sign_x * sec + jitter;
            if (rx < 2) rx = 2;
            if (rx >= DMAP_W-2) rx = DMAP_W - 3;
        }

        seed = seed * 1664525u + 1013904223u;
        int room_rx = room_min_rx + (int)((seed >> 16) % (unsigned)(room_max_rx - room_min_rx + 1));
        seed = seed * 1664525u + 1013904223u;
        int room_ry = room_min_ry + (int)((seed >> 16) % (unsigned)(room_max_ry - room_min_ry + 1));

        paint_room_brush(dmap, rx, ry, room_rx, room_ry);

        seed = seed * 1664525u + 1013904223u;
        int passage_len = 3 + (int)((seed >> 16) % 6);
        for (int p = 1; p <= passage_len; p++) {
            if (primary_x) {
                paint_passage_brush(dmap, rx - sign_x * p, ry, passage_w);
            } else {
                paint_passage_brush(dmap, rx, ry - sign_y * p, passage_w);
            }
        }

        if (depth == 0 && step_counter > 3) {
            seed = seed * 1664525u + 1013904223u;
            if ((seed >> 16) % 1000 == 0) {
                seed = seed * 1664525u + 1013904223u;
                float side = ((seed >> 31) ? 1.0f : -1.0f);
                float offset = (30.0f + (float)((seed >> 16) % 40)) * 3.14159f / 180.0f;
                float base_angle = atan2f(dir_y, dir_x);
                float bangle = base_angle + side * offset;
                float bdx = cosf(bangle), bdy = sinf(bangle);

                seed = seed * 1664525u + 1013904223u;
                int blen = 15 + (int)((seed >> 16) % 25);

                march_room_path(dmap, rx, ry, bdx, bdy,
                                seed, blen, jitter_range,
                                room_min_rx/2, room_max_rx/2,
                                room_min_ry/2, room_max_ry/2,
                                passage_w/2 + 1, 1);
            }
        }
        step_counter++;
    }
}

static void carve_room_layout(DungeonMap* dmap, DungeonEntranceType type, unsigned int seed) {
    int num_paths;
    int room_min_rx, room_max_rx, room_min_ry, room_max_ry;
    int passage_w;

    if (type == DUNGEON_ENT_CAVE) {
        num_paths = 3 + (int)((seed >> 16) % 3);
        room_min_rx = 4; room_max_rx = 10;
        room_min_ry = 3; room_max_ry = 8;
        passage_w = 3;
    } else {
        num_paths = 2 + (int)((seed >> 16) % 2);
        room_min_rx = 5; room_max_rx = 12;
        room_min_ry = 4; room_max_ry = 10;
        passage_w = 3;
    }

    int sx = DMAP_W / 2;
    int sy = DMAP_H / 2;

    float base_angle = 0.0f;
    for (int p = 0; p < num_paths; p++) {
        seed = seed * 1664525u + 1013904223u;
        float angle = base_angle + ((float)p / num_paths) * 2.0f * 3.14159f;
        seed = seed * 1664525u + 1013904223u;
        angle += ((float)((int)(seed >> 16) % 40) - 20.0f) * 3.14159f / 180.0f;
        float dx = cosf(angle);
        float dy = sinf(angle);

        seed = seed * 1664525u + 1013904223u;
        int path_len = 20 + (int)((seed >> 16) % 30);

        paint_room_brush(dmap, sx, sy, room_max_rx, room_max_ry);

        march_room_path(dmap, sx, sy, dx, dy,
                        seed, path_len, 3,
                        room_min_rx, room_max_rx,
                        room_min_ry, room_max_ry,
                        passage_w, 0);
    }

    dmap->entry_x = sx;
    dmap->entry_y = sy;
    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    int exit_offset_x = (int)(cosf(base_angle) * 15);
    int exit_offset_y = (int)(sinf(base_angle) * 15);
    dmap->exit_x = sx + exit_offset_x;
    dmap->exit_y = sy + exit_offset_y;
    if (dmap->exit_x < 1) dmap->exit_x = 1;
    if (dmap->exit_x >= DMAP_W) dmap->exit_x = DMAP_W - 1;
    if (dmap->exit_y < 1) dmap->exit_y = 1;
    if (dmap->exit_y >= DMAP_H) dmap->exit_y = DMAP_H - 1;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_EXIT;
}

static void carve_hybrid_layout(DungeonMap* dmap, unsigned int seed) {
    int sx = DMAP_W / 2;
    int sy = DMAP_H / 2;

    seed = seed * 1664525u + 1013904223u;
    int num_paths = 4 + (int)((seed >> 16) % 3);

    for (int p = 0; p < num_paths; p++) {
        seed = seed * 1664525u + 1013904223u;
        float angle = ((float)p / num_paths) * 2.0f * 3.14159f;
        seed = seed * 1664525u + 1013904223u;
        angle += ((float)((int)(seed >> 16) % 30) - 15.0f) * 3.14159f / 180.0f;
        float dx = cosf(angle);
        float dy = sinf(angle);

        seed = seed * 1664525u + 1013904223u;
        int path_len = 15 + (int)((seed >> 16) % 20);

        march_room_path(dmap, sx, sy, dx, dy,
                       seed, path_len, 2,
                       4, 8, 3, 6,
                       2, 0);
    }

    int bsp_margin = 15;
    s_bsp_n = 1;
    memset(s_bsp, 0, sizeof(s_bsp));
    s_bsp[0] = { bsp_margin, bsp_margin,
                 DMAP_W - 2*bsp_margin - 1, DMAP_H - 2*bsp_margin - 1,
                 -1, -1 };
    bsp_split(0, 0, &seed);

    s_leaf_n = 0;
    collect_leaves(0);

    for (int i = 1; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        if (n->rx > 0 && n->ry > 0) {
            carve_rect(dmap, n->rx, n->ry, n->rw, n->rh, DNG_FLOOR);
        }
    }

    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* a = &s_bsp[s_leaves[i]];
        BSPNode* b = &s_bsp[s_leaves[(i + 1) % s_leaf_n]];
        if (a->rcx > 0 && b->rcx > 0) {
            carve_corridor(dmap, a->rcx, a->rcy, b->rcx, b->rcy);
        }
    }

    dmap->entry_x = sx;
    dmap->entry_y = sy;
    if (dmap->tiles[dmap->entry_y][dmap->entry_x] == DNG_WALL)
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    int exit_dist = 20;
    seed = seed * 1664525u + 1013904223u;
    float exit_angle = ((seed >> 16) % 100) * 3.14159f / 50.0f;
    dmap->exit_x = sx + (int)(cosf(exit_angle) * exit_dist);
    dmap->exit_y = sy + (int)(sinf(exit_angle) * exit_dist);
    if (dmap->exit_x < 1) dmap->exit_x = 1;
    if (dmap->exit_x >= DMAP_W) dmap->exit_x = DMAP_W - 1;
    if (dmap->exit_y < 1) dmap->exit_y = 1;
    if (dmap->exit_y >= DMAP_H) dmap->exit_y = DMAP_H - 1;
    if (dmap->tiles[dmap->exit_y][dmap->exit_x] == DNG_WALL)
        dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_EXIT;
}

// ── Decoration helpers ────────────────────────────────────────────────────

// ── RUINS: Brogue-style room accretion ────────────────────────────────────
//
// 1. Place a seed room at map centre.
// 2. Collect perimeter: floor tiles that border a wall, plus outward direction.
// 3. Pick a random perimeter entry, generate a room stamp, align a "door" face
//    on the stamp with the perimeter point (optionally preceded by a hallway),
//    validate no overlap with existing floor, then carve hallway + stamp.
// 4. Repeat for N rooms, then place exit at the farthest floor tile from entry.

#define RNS_DIM   24      // max room-stamp dimension (tiles)
#define RNP_CAP   12000   // perimeter-entry buffer capacity
#ifndef RNS_SCALE
#define RNS_SCALE  3      // world tiles per logical stamp cell (each cell = 3×3 tiles: the user's pick)
#endif

struct RnPerim { int16_t x, y; int8_t dx, dy; };

static uint8_t s_rns[RNS_DIM][RNS_DIM];   // current room stamp (1 = floor)
static int     s_rns_w, s_rns_h;
static RnPerim s_rnp[RNP_CAP];             // dungeon perimeter entries
static int     s_rnp_n;

// Generate a random room stamp: rectangle (50%), L-shape (30%), cross (20%).
// Logical cells here — each cell is RNS_SCALE×RNS_SCALE tiles in world space.
static void rns_gen(uint32_t* rng) {
    memset(s_rns, 0, sizeof(s_rns));
    int shape = rng_next(rng) % 10;

    if (shape < 5) {
        // Rectangle: 3..6 cells = 12..24 world tiles per side
        s_rns_w = 3 + (int)(rng_next(rng) % 4);
        s_rns_h = 3 + (int)(rng_next(rng) % 4);
        for (int y = 0; y < s_rns_h; y++)
            for (int x = 0; x < s_rns_w; x++)
                s_rns[y][x] = 1;

    } else if (shape < 8) {
        // L-shape: body 3..5 cells, arm 2..4 cells
        int w1 = 3 + (int)(rng_next(rng) % 3);
        int h1 = 3 + (int)(rng_next(rng) % 3);
        int w2 = 2 + (int)(rng_next(rng) % 3);
        int h2 = 2 + (int)(rng_next(rng) % 3);
        int corner = rng_next(rng) % 4;

        int ox2, oy2;
        switch (corner) {
            case 0:  ox2 = 0;        oy2 = h1;       break;  // below-left
            case 1:  ox2 = w1 - w2;  oy2 = h1;       break;  // below-right
            case 2:  ox2 = w1;       oy2 = 0;         break;  // right-top
            default: ox2 = w1;       oy2 = h1 - h2;   break;  // right-bottom
        }
        if (ox2 < 0) ox2 = 0;
        if (oy2 < 0) oy2 = 0;

        s_rns_w = (w1 > ox2 + w2) ? w1 : ox2 + w2;
        s_rns_h = (h1 > oy2 + h2) ? h1 : oy2 + h2;
        if (s_rns_w > RNS_DIM) s_rns_w = RNS_DIM;
        if (s_rns_h > RNS_DIM) s_rns_h = RNS_DIM;

        for (int y = 0; y < h1 && y < s_rns_h; y++)
            for (int x = 0; x < w1 && x < s_rns_w; x++)
                s_rns[y][x] = 1;
        for (int y = oy2; y < oy2 + h2 && y < s_rns_h; y++)
            for (int x = ox2; x < ox2 + w2 && x < s_rns_w; x++)
                s_rns[y][x] = 1;

    } else {
        // Cross / plus: arm 2..4 cells, bar width 1..2 cells
        int arm = 2 + (int)(rng_next(rng) % 3);
        int hw  = 1 + (int)(rng_next(rng) % 2);

        int total = 2 * arm;
        if (total > RNS_DIM) total = RNS_DIM;
        s_rns_w = total; s_rns_h = total;

        int mid = total / 2;
        int hy0 = mid - hw / 2, hy1 = mid + (hw + 1) / 2;
        int hx0 = mid - hw / 2, hx1 = mid + (hw + 1) / 2;
        for (int y = hy0; y >= 0 && y < hy1 && y < total; y++)
            for (int x = 0; x < total; x++)
                s_rns[y][x] = 1;
        for (int x = hx0; x >= 0 && x < hx1 && x < total; x++)
            for (int y = 0; y < total; y++)
                s_rns[y][x] = 1;
    }
}

// Scan the dungeon and fill s_rnp with all floor→wall perimeter entries.
static void rnp_collect(const DungeonMap* dmap) {
    static const int DX[4] = { 0, 1, 0, -1 };
    static const int DY[4] = { -1, 0, 1,  0 };
    s_rnp_n = 0;
    for (int ty = 1; ty < DMAP_H - 1; ty++) {
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            for (int d = 0; d < 4; d++) {
                if (s_rnp_n >= RNP_CAP) break;
                int nx = tx + DX[d], ny = ty + DY[d];
                if (dmap->tiles[ny][nx] == DNG_WALL) {
                    s_rnp[s_rnp_n].x  = (int16_t)tx;
                    s_rnp[s_rnp_n].y  = (int16_t)ty;
                    s_rnp[s_rnp_n].dx = (int8_t)DX[d];
                    s_rnp[s_rnp_n].dy = (int8_t)DY[d];
                    s_rnp_n++;
                }
            }
        }
    }
}

// Try to attach s_rns to the dungeon. hlen = hallway tiles before the stamp.
// Returns true if a valid placement was found and carved.
static bool rn_attach(DungeonMap* dmap, int hlen, uint32_t* rng) {
    if (s_rnp_n == 0) return false;

    int door_sx[RNS_DIM * RNS_DIM], door_sy[RNS_DIM * RNS_DIM];

    int max_tries = (s_rnp_n < 200) ? s_rnp_n : 200;
    for (int attempt = 0; attempt < max_tries; attempt++) {
        int pi  = (int)(rng_next(rng) % (unsigned)s_rnp_n);
        int pdx = s_rnp[pi].dx, pdy = s_rnp[pi].dy;
        int px  = s_rnp[pi].x,  py  = s_rnp[pi].y;

        // Attachment point: RNS_SCALE world tiles per logical step.
        int attach_wx = px + pdx * RNS_SCALE * (1 + hlen);
        int attach_wy = py + pdy * RNS_SCALE * (1 + hlen);

        // Door candidates: stamp floor tiles whose "back" (–pdx, –pdy) is
        // outside the stamp or a wall tile within the stamp.
        int door_n = 0;
        for (int sy = 0; sy < s_rns_h; sy++) {
            for (int sx = 0; sx < s_rns_w; sx++) {
                if (!s_rns[sy][sx]) continue;
                int bx = sx - pdx, by = sy - pdy;
                bool back_open = (bx >= 0 && bx < s_rns_w &&
                                  by >= 0 && by < s_rns_h && s_rns[by][bx]);
                if (!back_open) {
                    door_sx[door_n] = sx;
                    door_sy[door_n] = sy;
                    door_n++;
                }
            }
        }
        if (door_n == 0) continue;

        int di  = (int)(rng_next(rng) % (unsigned)door_n);
        int dsx = door_sx[di], dsy = door_sy[di];

        // Stamp world origin: door cell (dsx, dsy) aligns with attachment point.
        int wo_x = attach_wx - dsx * RNS_SCALE;
        int wo_y = attach_wy - dsy * RNS_SCALE;

        // Validate: every stamp cell's RNS_SCALE×RNS_SCALE block must be
        // in-bounds and entirely wall (no overlap with existing floor).
        bool valid = true;
        for (int sy = 0; sy < s_rns_h && valid; sy++) {
            for (int sx = 0; sx < s_rns_w && valid; sx++) {
                if (!s_rns[sy][sx]) continue;
                int bx0 = wo_x + sx * RNS_SCALE;
                int by0 = wo_y + sy * RNS_SCALE;
                for (int by = 0; by < RNS_SCALE && valid; by++) {
                    for (int bx = 0; bx < RNS_SCALE && valid; bx++) {
                        int wx = bx0 + bx, wy = by0 + by;
                        if (wx < 2 || wx >= DMAP_W - 2 || wy < 2 || wy >= DMAP_H - 2)
                            { valid = false; }
                        else if (dmap->tiles[wy][wx] != DNG_WALL)
                            { valid = false; }
                    }
                }
            }
        }
        if (!valid) continue;

        // Carve hallway + doorway as a single rectangle (RNS_SCALE wide).
        int gl = RNS_SCALE * (1 + hlen);
        int gx, gy, gw, gh;
        if (pdx != 0) {
            gx = (pdx > 0) ? px + 1 : px - gl;
            gy = py;  gw = gl;  gh = RNS_SCALE;
        } else {
            gx = px;
            gy = (pdy > 0) ? py + 1 : py - gl;
            gw = RNS_SCALE;  gh = gl;
        }
        carve_rect(dmap, gx, gy, gw, gh, DNG_FLOOR);

        // Carve stamp: each logical cell → RNS_SCALE×RNS_SCALE tile block.
        for (int sy = 0; sy < s_rns_h; sy++)
            for (int sx = 0; sx < s_rns_w; sx++)
                if (s_rns[sy][sx])
                    carve_rect(dmap,
                               wo_x + sx * RNS_SCALE, wo_y + sy * RNS_SCALE,
                               RNS_SCALE, RNS_SCALE, DNG_FLOOR);

        return true;
    }
    return false;
}

// Seed room → accretion loop → exit at farthest floor tile.
static void carve_ruins_layout(DungeonMap* dmap, uint32_t* rng) {
    int cx = DMAP_W / 2, cy = DMAP_H / 2;

    // Seed room at centre.
    int seed_w = 14, seed_h = 14;
    carve_rect(dmap, cx - seed_w / 2, cy - seed_h / 2, seed_w, seed_h, DNG_FLOOR);

    dmap->entry_x = cx; dmap->entry_y = cy;
    dmap->tiles[cy][cx] = DNG_ENTRY;

    // Accretion loop.
    int num_rooms = 28 + (int)(rng_next(rng) % 13);  // 28..40
    for (int r = 0; r < num_rooms; r++) {
        rns_gen(rng);
        rnp_collect(dmap);
        int hlen = (int)(rng_next(rng) % 4);  // 0..3 hallway cells (0..12 world tiles)
        rn_attach(dmap, hlen, rng);
    }

    // Exit: farthest floor tile from entry by Manhattan distance.
    int best_dist = -1;
    dmap->exit_x = cx; dmap->exit_y = cy;
    for (int ty = 1; ty < DMAP_H - 1; ty++) {
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            if (tx == dmap->entry_x && ty == dmap->entry_y) continue;
            int dist = abs(tx - dmap->entry_x) + abs(ty - dmap->entry_y);
            if (dist > best_dist) {
                best_dist = dist;
                dmap->exit_x = tx;
                dmap->exit_y = ty;
            }
        }
    }

    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── PYRAMID: Mother 1 chambers along one linear passage ─────────────────
//
// The user's reference: screen-sized trapezoid chambers on a grid of columns
// and rows. A chamber's floor widens at 45 degrees under its two slanted side
// walls for SW rows, so each side wall's floor edge ends at the top of a door,
// then runs the full width for two rows -- the strip the corridors come in at.
// One door a side, at that front corner, so the tomb is a single passage east
// to west. A link to the next column is a level corridor across a narrow gap;
// across a wide one, a landing, a 45-degree flight one chamber row up or down,
// and a landing. Every tile records what it is drawn as (art, art_p): a wall
// stands on the wall tiles above the floor it faces, three tiles tall, so
// nothing is drawn outside its own tile.

enum WallArt : uint8_t {
    WA_NONE, WA_FLOOR, WA_BACK, WA_BAND, WA_SIDE_L, WA_SIDE_R,
    WA_DIAG_L, WA_DIAG_R, WA_END_L, WA_END_R, WA_FLIGHT,
};
// A flight tile's parameter: its row in the column's 9-tile strip, which
// column of the flight it is (0 first, 1 middle, 2 last), the flight's
// direction (0 climbing right, 1 climbing left) and the column's parity.
static inline uint8_t pyr_flight_p(int row, int kind, int dir, int ipar) {
    return (uint8_t)(row | kind << 4 | dir << 6 | ipar << 7);
}

static const int PYR_BW = 7, PYR_H = 8, PYR_SW = PYR_H - 2;
static const int PYR_HALF = PYR_BW / 2 + PYR_SW;          // centre to outer column
static const int PYR_ROOM_W = 2 * PYR_HALF + 1;
static const int PYR_ROW_H = 16;                          // a flight climbs one row: 16 steps
static const int PYR_NARROW = 6, PYR_WIDE = 2 + PYR_ROW_H + 4;   // landing, flight, landing
static const int PYR_COLS = 16, PYR_ROWS = 9;
static const int PYR_FLIGHT_ROWS = 9;                     // a flight column's strip of tiles

struct PyrTile { int16_t x, y; uint8_t a, p; };
struct PyrFlight { int fx, fy, step, n; };

static int s_pyr_colx[PYR_COLS];

static void pyr_cell_pos(int c, int r, int* cx, int* yb) {
    *cx = 40 + s_pyr_colx[c] + PYR_HALF;
    *yb = 40 + r * PYR_ROW_H;
}

static void pyr_room_tiles(int c, int r, std::vector<PyrTile>& t) {
    int cx, yb; pyr_cell_pos(c, r, &cx, &yb);
    int xl = cx - PYR_BW / 2, xr = cx + PYR_BW / 2;
    auto add = [&](int x, int y, uint8_t a, uint8_t p) { t.push_back({(int16_t)x, (int16_t)y, a, p}); };
    for (int k = 0; k < PYR_SW; k++) {
        int y = yb + k;
        for (int x = xl - k; x <= xr + k; x++) add(x, y, WA_FLOOR, 0);
        add(xl - k - 1, y, WA_DIAG_L, 0); add(xr + k + 1, y, WA_DIAG_R, 0);
        for (int x = xl - PYR_SW; x < xl - k - 1; x++) add(x, y, WA_SIDE_L, 0);
        for (int x = xr + k + 2; x <= xr + PYR_SW; x++) add(x, y, WA_SIDE_R, 0);
    }
    for (int k = PYR_SW; k < PYR_H; k++)
        for (int x = xl - PYR_SW; x <= xr + PYR_SW; x++) add(x, yb + k, WA_FLOOR, 0);
    for (int y = yb - 3; y < yb; y++) {
        for (int x = xl; x <= xr; x++) add(x, y, WA_BACK, (uint8_t)(y - (yb - 3)));
        for (int x = xl - PYR_SW; x < xl - 1; x++) add(x, y, WA_SIDE_L, 0);
        for (int x = xr + 2; x <= xr + PYR_SW; x++) add(x, y, WA_SIDE_R, 0);
        add(xl - 1, y, WA_END_L, 0); add(xr + 1, y, WA_END_R, 0);
    }
}

// Where a door's corridor leaves a chamber: just outside its front strip.
static void pyr_landing(int c, int r, int side, int* x, int* y) {
    int cx, yb; pyr_cell_pos(c, r, &cx, &yb);
    *x = cx + side * (PYR_HALF + 1);
    *y = yb + PYR_SW;
}

static void pyr_level(int x0, int x1, int y, std::vector<PyrTile>& t) {
    if (x0 > x1) { int s = x0; x0 = x1; x1 = s; }
    for (int x = x0; x <= x1; x++)
        for (int j = 0; j < 2; j++) t.push_back({(int16_t)x, (int16_t)(y + j), WA_FLOOR, 0});
}

// The link from chamber (c, r)'s east door to chamber (c + 1, r2)'s west door.
static void pyr_link(int c, int r, int r2, std::vector<PyrTile>& t, PyrFlight* fl) {
    int x0, y0, x1, y1;
    pyr_landing(c, r, 1, &x0, &y0);
    pyr_landing(c + 1, r2, -1, &x1, &y1);
    fl->n = 0;
    if (y1 == y0) { pyr_level(x0, x1, y0, t); return; }
    pyr_level(x0, x0 + 1, y0, t);
    int step = y1 < y0 ? -1 : 1, n = abs(y1 - y0);
    *fl = { x0 + 2, y0, step, n };
    int x = x0 + 2, y = y0;
    for (int i = 0; i < n; i++) {
        int kind = i == 0 ? 0 : i == n - 1 ? 2 : 1;
        for (int row = 0; row < PYR_FLIGHT_ROWS; row++) {
            if ((row == 8 && step < 0) || (row == 0 && step > 0)) continue;   // the tile that side leaves empty
            t.push_back({(int16_t)x, (int16_t)(y - 5 + row), WA_FLIGHT,
                         pyr_flight_p(row, kind, step < 0 ? 0 : 1, i & 1)});
        }
        x++; y += step;
    }
    pyr_level(x, x1, y, t);
}

// Whether tiles can go down with a margin of nothing round them; a link's
// tiles near its two ends may meet the chambers they join.
static bool pyr_free(const DungeonMap* dmap, const std::vector<PyrTile>& t,
                     const int* ex, const int* ey, int n_ends, int margin) {
    for (const PyrTile& p : t) {
        bool near_end = false;
        for (int e = 0; e < n_ends; e++)
            if (abs(p.x - ex[e]) <= 3 && abs(p.y - ey[e]) <= 3) near_end = true;
        if (near_end) continue;
        for (int j = -margin; j <= margin; j++)
            for (int i = -margin; i <= margin; i++) {
                int x = p.x + i, y = p.y + j;
                if (x < 0 || y < 0 || x >= DMAP_W || y >= DMAP_H || dmap->art[y][x] != WA_NONE)
                    return false;
            }
    }
    return true;
}

static void pyr_commit(DungeonMap* dmap, const std::vector<PyrTile>& t) {
    for (const PyrTile& p : t) { dmap->art[p.y][p.x] = p.a; dmap->art_p[p.y][p.x] = p.p; }
}

static uint32_t pyr_hash(uint32_t a, uint32_t b) {
    uint32_t h = a * 0x9E3779B1u ^ (b + 0x7F4A7C15u) * 0x85EBCA6Bu;
    h ^= h >> 13; h *= 0xC2B2AE35u; h ^= h >> 16;
    return h;
}

static void pyr_decal(DungeonMap* dmap, int col, int row, int w, int h, int x, int y, bool flip) {
    if (dmap->num_decals >= DMAP_MAX_DECALS) return;
    dmap->decals[dmap->num_decals++] = { (int16_t)(col * 16), (int16_t)(row * 16), (int16_t)w, (int16_t)h,
                                         x, y, flip };
}

// The enemy glyphs, laid whole: one in every 96 columns of corridor face, at a
// place in that stretch the hash picks, kept only if the whole stone lies on
// one face -- the Mayan carved cryptid stones, the desert's cartouches; and up
// each Mayan flight a small carved stone every 52 columns, set where it lies
// whole on the wall between the fret and the cap (nothing cut off).
static void pyr_place_decals(DungeonMap* dmap, const std::vector<PyrFlight>& flights, uint32_t* rng) {
    const int v = dmap->step_pyramid ? 1 : 0;
    const int c0 = WALL_COL0[v ? WALL_MAYA : WALL_EGYPT], r0 = WALL_ROW0[v ? WALL_MAYA : WALL_EGYPT];
    const int sw = v ? PYR_STONE_W_MAYA : PYR_STONE_W_DESERT;
    const int sh = v ? PYR_STONE_H_MAYA : PYR_STONE_H_DESERT;
    const int top_z = v ? 37 : 35;      // the stone's top row above the floor (maya_murals._big, pyramid_design._cartouche)
    uint32_t salt = rng_next(rng);
    auto face = [&](int x, int y) {     // a corridor face's full height stands over this floor tile
        return dmap->art[y][x] == WA_FLOOR && dmap->art[y - 1][x] == WA_BAND &&
               dmap->art[y - 2][x] == WA_BAND && dmap->art[y - 3][x] == WA_BAND;
    };
    for (int y = 3; y < DMAP_H; y++)
        for (int x = 1; x < DMAP_W; x++) {
            if (!face(x, y) || face(x - 1, y)) continue;
            int x1 = x;
            while (x1 < DMAP_W && face(x1, y)) x1++;
            int px0 = 16 * x, px1 = 16 * x1;
            for (int m = px0 / 96; m <= px1 / 96; m++) {
                uint32_t h = pyr_hash(salt, (uint32_t)(m * 1024 + y));
                int X0 = 96 * m + (int)(h & 1) * 48 +
                         (v ? 24 + (int)((h >> 4) % 9) - 4 - 17 : 6 + (int)((h >> 4) % 7) - 3);
                if (X0 < px0 || X0 + sw > px1) continue;
                int i = (int)((h >> 8) % PYR_CRYPTIDS), flip = (int)((h >> 12) & 1);
                pyr_decal(dmap, c0 + PYR_STONE_COL + (i * 2 + flip) * 3, r0 + PYR_STONE_ROW,
                          sw, sh, X0, 16 * y - 1 - top_z, false);
            }
        }
    if (!v) return;
    for (const PyrFlight& f : flights) {
        auto u_at = [&](int X, int Y) {                       // across the strip, as gen_dungeon_wall_tiles.strip_u
            int i = X / 16 - f.fx, x = X % 16;
            int y = Y - 16 * (f.fy + i * f.step - 5);
            return (f.step < 0 ? x + y : y - x) - 9;
        };
        auto on_wall = [&](int X, int Y) { int h = 70 - u_at(X, Y); return h >= 8 && h <= 46; };
        int lo = 16 * ((f.step < 0 ? f.fy - f.n : f.fy) - 6), hi = 16 * ((f.step < 0 ? f.fy : f.fy + f.n) + 2);
        int k = 0;
        for (int x0 = 16 * f.fx + 12; x0 < 16 * (f.fx + f.n) - PYR_SMALL_W; x0 += 52, k++) {
            int ok[512], n_ok = 0;
            for (int Y = lo; Y < hi && n_ok < 512; Y++)
                if (on_wall(x0, Y) && on_wall(x0 + PYR_SMALL_W - 1, Y) &&
                    on_wall(x0, Y + PYR_SMALL_H - 1) && on_wall(x0 + PYR_SMALL_W - 1, Y + PYR_SMALL_H - 1))
                    ok[n_ok++] = Y;
            if (!n_ok) continue;
            uint32_t h = pyr_hash(salt ^ 0x5BD1E995u, (uint32_t)(f.fx * 64 + k));
            int col = x0 / 16;
            pyr_decal(dmap, c0 + PYR_SMALL_COL + (int)(h % PYR_CRYPTIDS) * 2, r0 + PYR_SMALL_ROW,
                      PYR_SMALL_W, PYR_SMALL_H, x0, ok[n_ok / 2], ((h >> 8) & 1) != 0);
        }
    }
}

// A north face over every floor tile with nothing above it: the three tiles
// up (or as many as there are before other art), each its row of the face.
static void art_faces(DungeonMap* dmap) {
    for (int y = 3; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            if (dmap->art[y][x] != WA_FLOOR || dmap->art[y - 1][x] != WA_NONE) continue;
            for (int j = 1; j <= 3 && dmap->art[y - j][x] == WA_NONE; j++) {
                dmap->art[y - j][x] = WA_BAND;
                dmap->art_p[y - j][x] = (uint8_t)(3 - j);      // the face's row, 0 at the top
            }
        }
}

// ── Built walls: the rules their art needs ────────────────────────────────
//
// A wall with tiled art -- a three-tile north face, the wall top's rim round
// it (the ruins') -- needs room for it: behind every north face at least
// WALL_THICK tiles of wall (the face and two more, so a face never stands
// with floor just behind its top), and every wall top at least two tiles wide
// (a face counting as open), or two rims meet with no dark between. A thin
// stack is thickened by filling the floor behind it, a narrow top widened into
// the floor beside it -- unless that cuts floor off from the entry, in which
// case the thin wall is carved away to floor instead. A carved tile is never
// filled again, so it ends. (The user approved this on the ruins' cell-3 mock.)
static const int WALL_THICK = 5;

static bool wr_floor(const DungeonMap* d, int x, int y) {
    return x >= 0 && y >= 0 && x < DMAP_W && y < DMAP_H && d->tiles[y][x] != DNG_WALL;
}
static bool wr_wall(const DungeonMap* d, int x, int y) {
    return x >= 0 && y >= 0 && x < DMAP_W && y < DMAP_H && d->tiles[y][x] == DNG_WALL;
}
// A wall tile in a north face: a face's foot is a wall with floor below it and
// none above, and the face is it and the two walls over it.
static bool wr_face_foot(const DungeonMap* d, int x, int y) {
    return wr_wall(d, x, y) && wr_floor(d, x, y + 1) && !wr_floor(d, x, y - 1);
}
static bool wr_covered(const DungeonMap* d, int x, int y) {
    for (int k = 0; k < 3; k++) {
        if (!wr_wall(d, x, y + k)) return false;
        if (wr_face_foot(d, x, y + k)) return true;
    }
    return false;
}
static bool wr_open(const DungeonMap* d, int x, int y) { return wr_floor(d, x, y) || wr_covered(d, x, y); }
static bool wr_narrow(const DungeonMap* d, int x, int y) {
    return wr_wall(d, x, y) && !wr_covered(d, x, y) && wr_open(d, x - 1, y) && wr_open(d, x + 1, y);
}

// Whether every floor tile still joins the entry.
static bool wr_connected(const DungeonMap* d, int n_floor) {
    static uint8_t seen[DMAP_H][DMAP_W];
    static int q[DMAP_W * DMAP_H];
    memset(seen, 0, sizeof seen);
    int head = 0, tail = 0;
    q[tail++] = d->entry_y * DMAP_W + d->entry_x; seen[d->entry_y][d->entry_x] = 1;
    while (head < tail) {
        int x = q[head] % DMAP_W, y = q[head] / DMAP_W; head++;
        const int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
        for (int k = 0; k < 4; k++) {
            int nx = x + dx[k], ny = y + dy[k];
            if (!wr_floor(d, nx, ny) || seen[ny][nx]) continue;
            seen[ny][nx] = 1; q[tail++] = ny * DMAP_W + nx;
        }
    }
    return tail == n_floor;
}

static void wall_rules(DungeonMap* dmap) {
    static uint8_t keep[DMAP_H][DMAP_W];          // never filled: the portals, and every tile once carved
    memset(keep, 0, sizeof keep);
    for (int p = 0; p < dmap->num_portals; p++) keep[dmap->portals[p].ty][dmap->portals[p].tx] = 1;
    int x0 = DMAP_W, y0 = DMAP_H, x1 = 0, y1 = 0, n_floor = 0;   // the floor's extent, with room round it
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            if (wr_floor(dmap, x, y)) {
                n_floor++;
                if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
            }
    x0 = x0 > 8 ? x0 - 8 : 1; y0 = y0 > 8 ? y0 - 8 : 1;
    x1 = x1 + 8 < DMAP_W - 1 ? x1 + 8 : DMAP_W - 2; y1 = y1 + 8 < DMAP_H - 1 ? y1 + 8 : DMAP_H - 2;
    struct Stack { int x, y, k; };
    std::vector<Stack> stacks;
    std::vector<int> narrow;
    for (int it = 0; it < 200; it++) {
        stacks.clear(); narrow.clear();
        for (int y = y0; y <= y1; y++)
            for (int x = x0; x <= x1; x++) {
                if (wr_wall(dmap, x, y) && wr_floor(dmap, x, y + 1)) {
                    int k = 0;
                    while (wr_wall(dmap, x, y - k)) k++;
                    if (y - k >= 0 && k < WALL_THICK) stacks.push_back({x, y, k});   // floor behind it, too close
                }
                if (wr_narrow(dmap, x, y)) narrow.push_back(y * DMAP_W + x);
            }
        if (stacks.empty() && narrow.empty()) break;
        for (int t : narrow) {                    // widen into the floor beside it, else carve
            int x = t % DMAP_W, y = t / DMAP_W;
            if (!wr_narrow(dmap, x, y)) continue;
            bool done = false;
            for (int sx = 1; sx >= -1 && !done; sx -= 2) {
                int nx = x + sx;
                if (!wr_floor(dmap, nx, y) || keep[y][nx]) continue;
                uint8_t was = dmap->tiles[y][nx];
                dmap->tiles[y][nx] = DNG_WALL;
                if (wr_connected(dmap, n_floor - 1)) { n_floor--; done = true; }
                else dmap->tiles[y][nx] = was;
            }
            if (!done) { dmap->tiles[y][x] = DNG_FLOOR; keep[y][x] = 1; n_floor++; }
        }
        for (const Stack& st : stacks) {          // thicken behind it, else carve it away
            int x = st.x, y = st.y, k = st.k;
            if (!wr_wall(dmap, x, y) || !wr_floor(dmap, x, y + 1)) continue;
            int behind[WALL_THICK], nb = 0;
            bool kept = false;
            for (int j = k; j < WALL_THICK; j++)
                if (y - j >= 0 && wr_floor(dmap, x, y - j)) { behind[nb++] = y - j; kept |= keep[y - j][x] != 0; }
            if (nb && !kept) {
                uint8_t was[WALL_THICK];
                for (int i = 0; i < nb; i++) { was[i] = dmap->tiles[behind[i]][x]; dmap->tiles[behind[i]][x] = DNG_WALL; }
                if (wr_connected(dmap, n_floor - nb)) { n_floor -= nb; continue; }
                for (int i = 0; i < nb; i++) dmap->tiles[behind[i]][x] = was[i];
            }
            for (int j = 0; j < k; j++) { dmap->tiles[y - j][x] = DNG_FLOOR; keep[y - j][x] = 1; }
            n_floor += k;
        }
    }
}

// The ruins' art: floor, and a face over it wherever wall stands to its north
// -- three tiles of it, as the rules guarantee -- each face whole, cracked or
// with a block fallen out (6 : 1 : 1, as the approved mock mixed them).
static void ruins_art(DungeonMap* dmap) {
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            if (dmap->tiles[y][x] != DNG_WALL) dmap->art[y][x] = WA_FLOOR;
    art_faces(dmap);
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            if (dmap->art[y][x] == WA_BAND) {
                int yf = y + 3 - (dmap->art_p[y][x] & 15);     // the floor row the face stands over
                uint32_t h = pyr_hash((uint32_t)x, (uint32_t)yf) % 8;
                dmap->art_p[y][x] |= (uint8_t)((h < 6 ? 0 : h == 6 ? 1 : 2) << 4);
            }
}

static void carve_pyramid_layout(DungeonMap* dmap, uint32_t* rng) {
    int gaps[PYR_COLS - 1];
    for (int i = 0; i < PYR_COLS - 1; i++)
        gaps[i] = (rng_next(rng) % 3 == 0) ? PYR_NARROW : PYR_WIDE;
    s_pyr_colx[0] = 0;
    for (int i = 1; i < PYR_COLS; i++) s_pyr_colx[i] = s_pyr_colx[i - 1] + PYR_ROOM_W + gaps[i - 1];
    const int want = 12 + (int)(rng_next(rng) % 3);

    // ── 1. Chambers, grown one link at a time off the passage so far ─────
    int room_at[PYR_COLS][PYR_ROWS];
    for (int c = 0; c < PYR_COLS; c++) for (int r = 0; r < PYR_ROWS; r++) room_at[c][r] = -1;
    int rc[DMAP_MAX_PYR_ROOMS], rr[DMAP_MAX_PYR_ROOMS], nrooms = 0;
    int nbr[DMAP_MAX_PYR_ROOMS][2], deg[DMAP_MAX_PYR_ROOMS] = {};
    bool used[PYR_COLS][PYR_ROWS][2] = {};               // a door a side
    std::vector<int> frontier;                           // c * PYR_ROWS + r
    std::vector<PyrFlight> flights;
    std::vector<PyrTile> tiles, room;
    auto add_room = [&](int c, int r) {
        room_at[c][r] = nrooms; rc[nrooms] = c; rr[nrooms] = r; nrooms++;
        room.clear(); pyr_room_tiles(c, r, room); pyr_commit(dmap, room);
        frontier.push_back(c * PYR_ROWS + r);
    };
    add_room(PYR_COLS / 2, PYR_ROWS / 2);
    for (int tries = 0; nrooms < want && nrooms < DMAP_MAX_PYR_ROOMS && tries < 5000; tries++) {
        int fi = (int)(rng_next(rng) % frontier.size());
        int c = frontier[fi] / PYR_ROWS, r = frontier[fi] % PYR_ROWS;
        struct Move { int side, c2, r2; };
        std::vector<Move> moves;
        for (int side = -1; side <= 1; side += 2) {
            int c2 = c + side;
            if (c2 < 0 || c2 >= PYR_COLS || used[c][r][side > 0]) continue;
            int g = gaps[c < c2 ? c : c2];
            for (int r2 = r - 1; r2 <= r + 1; r2++) {
                if (r2 < 0 || r2 >= PYR_ROWS || room_at[c2][r2] >= 0) continue;
                int dy = abs(r2 - r) * PYR_ROW_H;
                if (dy == 0 || dy + 4 <= g)            // a flight needs its landings
                    for (int k = 0; k < (r2 != r ? 3 : 1); k++)   // favour a change of row, as the reference climbs
                        moves.push_back({side, c2, r2});
            }
        }
        if (moves.empty()) {
            frontier.erase(frontier.begin() + fi);
            if (frontier.empty()) break;
            continue;
        }
        Move m = moves[rng_next(rng) % moves.size()];
        int ac = m.side > 0 ? c : m.c2, ar = m.side > 0 ? r : m.r2;   // the west chamber
        int br = m.side > 0 ? m.r2 : r;
        PyrFlight fl;
        tiles.clear(); pyr_link(ac, ar, br, tiles, &fl);
        room.clear(); pyr_room_tiles(m.c2, m.r2, room);
        int ex[2], ey[2];
        pyr_landing(ac, ar, 1, &ex[0], &ey[0]);
        pyr_landing(ac + 1, br, -1, &ex[1], &ey[1]);
        if (!pyr_free(dmap, tiles, ex, ey, 2, 2) || !pyr_free(dmap, room, nullptr, nullptr, 0, 3)) continue;
        add_room(m.c2, m.r2);
        pyr_commit(dmap, tiles);
        if (fl.n) flights.push_back(fl);
        used[ac][ar][1] = used[ac + 1][br][0] = true;
        int ia = room_at[ac][ar], ib = room_at[ac + 1][br];
        nbr[ia][deg[ia]++] = ib; nbr[ib][deg[ib]++] = ia;
    }

    // ── 2. A face over every floor tile with nothing above it ───────────
    art_faces(dmap);

    // ── 3. What is walked on ────────────────────────────────────────────
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            uint8_t a = dmap->art[y][x], row = dmap->art_p[y][x] & 15;
            if (a == WA_FLOOR || (a == WA_FLIGHT && (row == 5 || row == 6)))
                dmap->tiles[y][x] = DNG_FLOOR;
        }

    // ── 4. The doorways, on chambers' back walls ────────────────────────
    // The passage in order, end to end. Alone, a pyramid is entered in a
    // chamber of its middle two-thirds and left by the end farther from it;
    // paired, it runs end to end (dungeon_bind_pair takes alt_entry).
    int order[DMAP_MAX_PYR_ROOMS], no = 0, prev = -1, cur = 0;
    for (int i = 0; i < nrooms; i++) if (deg[i] <= 1) { cur = i; break; }
    while (cur >= 0 && no < nrooms) {
        order[no++] = cur;
        int nx = -1;
        for (int k = 0; k < deg[cur]; k++) if (nbr[cur][k] != prev) nx = nbr[cur][k];
        prev = cur; cur = nx;
    }
    int lo = no / 6, hi = no - no / 6;
    int entry_i = lo + (int)(rng_next(rng) % (uint32_t)(hi - lo > 1 ? hi - lo : 1));
    int exit_i = (entry_i >= no - 1 - entry_i) ? 0 : no - 1;
    int alt_i = exit_i == 0 ? no - 1 : 0;
    auto door = [&](int i, int* x, int* y) { pyr_cell_pos(rc[order[i]], rr[order[i]], x, y); };
    door(entry_i, &dmap->entry_x, &dmap->entry_y);
    door(exit_i, &dmap->exit_x, &dmap->exit_y);
    door(alt_i, &dmap->alt_entry_x, &dmap->alt_entry_y);
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_EXIT;

    dmap->num_pyr_rooms = nrooms;
    for (int i = 0; i < nrooms; i++) {
        int cx, yb; pyr_cell_pos(rc[i], rr[i], &cx, &yb);
        dmap->pyr_rooms[i].cx = (int16_t)cx; dmap->pyr_rooms[i].yb = (int16_t)yb;
    }
    pyr_place_decals(dmap, flights, rng);
}

// ── OASIS: a flooded cave seen from the side ──────────────────────────────
// The user's reference (a Mother 1 cave strip, tools/gen_oasis.py -> oasis.inc)
// and its mirror end to end: a level is a stretch of that run 5-15 screens
// long, cut so both ends land in its narrow passage. Then, as the approved
// mock-up (scratchpad oasis_gen.py) laid them: each end tapers to a rounded
// point (the user's dead end); air sits in the ceiling's hollows, its water
// line at the higher of the hollow's two lips (the user's red line), a dome
// bitten into the rock where no hollow lies near, never more than 34 tiles
// from the last air; a shaft up to the spring at each end, its water line
// where it meets the ceiling; sections read off the shape; weed on the
// seabed, its foot at the lowest of the seabed under it.
#include "oasis.inc"
static inline bool oasis_rock(const DungeonMap* d, int x, int y) {
    if (x < 0 || y < 0 || x >= d->oasis_w || y >= OASIS_PX_H) return true;
    return d->oasis_solid[y][x >> 3] >> (x & 7) & 1;
}
static inline void oasis_set(DungeonMap* d, int x, int y, bool rock) {
    if (x < 0 || y < 0 || x >= d->oasis_w || y >= OASIS_PX_H) return;
    if (rock) d->oasis_solid[y][x >> 3] |= (uint8_t)(1 << (x & 7));
    else      d->oasis_solid[y][x >> 3] &= (uint8_t)~(1 << (x & 7));
}
// What stops the swimmer, in level pixels: the rock, and the air above a
// pocket's or a shaft's water line past a head's height -- one surfaces, the
// head up out of the water, and goes no higher (user).
static const int OASIS_HEAD = 10;              // how far the head comes up out of the water, art pixels
static bool oasis_blocked(const DungeonMap* d, int x, int y) {
    if (oasis_rock(d, x, y)) return true;
    for (int i = 0; i < d->num_oasis_air; i++) {
        const auto& a = d->oasis_air[i];
        if (x >= a.x0 && x < a.x1 && y < a.line - OASIS_HEAD) return true;
    }
    return false;
}
// The swimmer's body, not only its feet -- seen from the side the head comes
// up under the rock too: of its 28 x 40 frame, x 4..24 and y 10..40 (dungeon
// pixels), in level pixels.
// Shaft i's way out on the map: the tile under the swimmer's feet when it has
// surfaced there, its head up out of the water (the feet 12 below the head).
static void oasis_way_tile(const DungeonMap* d, int i, int* tx, int* ty) {
    *tx = 8 + (d->oasis_air[i].x0 + d->oasis_air[i].x1) / 2 / 16;
    *ty = 8 + (d->oasis_air[i].line - OASIS_HEAD + 12) / 16;
}
static void oasis_body(const DungeonMap* d, float x, float y, int* x0, int* y0, int* x1, int* y1) {
    *x0 = (int)floorf((x + 4) * 16 / DMAP_TILE) - d->oasis_x0;  *x1 = (int)floorf((x + 24) * 16 / DMAP_TILE) - d->oasis_x0;
    *y0 = (int)floorf((y + 10) * 16 / DMAP_TILE) - d->oasis_y0; *y1 = (int)floorf((y + 40) * 16 / DMAP_TILE) - d->oasis_y0;
}
static bool oasis_body_free(const DungeonMap* d, float x, float y) {
    int x0, y0, x1, y1;
    oasis_body(d, x, y, &x0, &y0, &x1, &y1);
    for (int py = y0; py < y1; py++)
        for (int px = x0; px < x1; px++)
            if (oasis_blocked(d, px, py)) return false;
    return true;
}

static bool oasis_narrow_col(int c) {          // a run column whose water is the narrow passage's
    int wet = 0;
    for (int y = 0; y < OASIS_ROWS; y++) {
        const unsigned short* m = OASIS_MASK[OASIS_RUN_IDS[y][c % OASIS_RUN]];
        bool water = true;
        for (int r = 0; r < 16; r++) water &= m[r] == 0;
        wet += water;
    }
    return wet < 4;
}

static void carve_oasis(DungeonMap* d, uint32_t* rng) {
    const int S = 16, TAPER = 6 * S;
    auto rr = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    int NS = 5 + rr(11), TW = NS * 20, W = TW * S;
    d->oasis_w = W;
    d->oasis_seed = rng_next(rng);
    // the stretch of the run: both ends in the narrow passage
    std::vector<int> ok;
    for (int x = 0; x < OASIS_RUN; x++)
        if (oasis_narrow_col(x + 6) && oasis_narrow_col(x + TW - 7)) ok.push_back(x);
    int x0 = ok.empty() ? rr(OASIS_RUN) : ok[rr((int)ok.size())];
    memset(d->oasis_solid, 0, sizeof d->oasis_solid);
    std::vector<bool> narrow(TW);
    for (int c = 0; c < TW; c++) {
        narrow[c] = oasis_narrow_col(x0 + c);
        for (int row = 0; row < OASIS_ROWS; row++) {
            const unsigned short* m = OASIS_MASK[OASIS_RUN_IDS[row][(x0 + c) % OASIS_RUN]];
            for (int r = 0; r < 16; r++)
                for (int b = 0; b < 16; b++)
                    if (m[r] >> b & 1) oasis_set(d, c * S + b, row * S + r, true);
        }
    }
    // the two ends taper to a rounded point, 8 px inside the level's edge
    for (int side = 0; side < 2; side++) {
        int xe = side ? W - 1 - TAPER : TAPER, c0 = -1, f0 = -1;
        for (int y = 0; y < OASIS_PX_H; y++)
            if (!oasis_rock(d, xe, y)) { if (c0 < 0) c0 = y; f0 = y; }
        if (c0 < 0) continue;
        float yc = (c0 + f0) / 2.0f, hmax = (f0 - c0) / 2.0f;
        for (int x = 0; x < TAPER; x++) {
            int px = side ? W - 1 - x : x;
            float t = std::max(0.0f, (x - 8) / (float)(TAPER - 8));
            float h = hmax * powf(t, 0.7f) + (t > 0 ? 2.5f * sinf(x / 5.0f + side) : -1.0f);
            float lo = yc - h * (((x / 10) % 2) ? 1.15f : 1.0f), hi = yc + h;
            for (int y = 0; y < OASIS_PX_H; y++)
                if (!(lo < y && y < hi)) oasis_set(d, px, y, true);
        }
    }
    // the ceiling's underside, column by column
    std::vector<int> ceil(W);
    auto ceiling = [&]() {
        for (int px = 0; px < W; px++) {
            int y = 0;
            while (y < OASIS_PX_H && oasis_rock(d, px, y)) y++;
            ceil[px] = y;
        }
    };
    ceiling();
    struct Hollow { int x0, x1, line; };
    auto hollows = [&]() {
        std::vector<int> lips;
        for (int px = 24; px < W - 24; px++) {
            int m = 0;
            for (int k = -24; k <= 24; k++) m = std::max(m, ceil[px + k]);
            if (ceil[px] == m && (px == 24 || ceil[px - 1] != ceil[px])) lips.push_back(px);
        }
        std::vector<Hollow> out;
        for (size_t i = 0; i + 1 < lips.size(); i++) {
            int a = lips[i], b = lips[i + 1], line = std::min(ceil[a], ceil[b]);
            int lo = W, hi = -1, top = OASIS_PX_H, room = 0, n = 0;
            for (int px = a + 1; px < b; px++)
                if (ceil[px] < line) { lo = std::min(lo, px); hi = std::max(hi, px); room += line - ceil[px]; n++; }
            for (int px = a + 1; px < b; px++) top = std::min(top, ceil[px]);
            if (n >= 16 && line - top >= 8 && room >= 500) out.push_back({ lo, hi + 1, line });
        }
        return out;
    };
    std::vector<Hollow> pockets;
    int last = 8 * S;                                         // the way in's shaft: air
    while ((TW - 8) * S - last > 34 * S) {
        int target = std::min(W - TAPER - 30, last + (24 + rr(11)) * S);
        std::vector<Hollow> near;
        for (auto& h : hollows()) { int c = (h.x0 + h.x1) / 2; if (c >= last + 12 * S && c <= target) near.push_back(h); }
        if (near.empty()) {                                   // a dome bitten up into the rock
            int c = ceil[target];
            for (int px = target - 20; px <= target + 20; px++)
                for (int y = std::max(2, c - 18); y <= c; y++) {
                    float u = (px - target) / 20.5f, v = (y - c) / 16.5f;
                    if (u * u + v * v <= 1) oasis_set(d, px, y, false);
                }
            ceiling();
            for (auto& h : hollows()) if (h.x0 <= target && target < h.x1) near.push_back(h);
            if (near.empty()) {                               // the dome is the hollow: its flanks its lips
                int line = std::min(ceil[target - 22], ceil[target + 22]), lo = W, hi = -1;
                for (int px = target - 21; px <= target + 21; px++)
                    if (ceil[px] < line) { lo = std::min(lo, px); hi = std::max(hi, px); }
                if (hi < 0) { lo = target - 8; hi = target + 8; }
                near.push_back({ lo, hi + 1, line });
            }
        }
        Hollow best = near[0];
        for (auto& h : near) if (h.x0 + h.x1 > best.x0 + best.x1) best = h;
        pockets.push_back(best);
        last = (best.x0 + best.x1) / 2;
    }
    // the shafts: entries 0 and 1 of the air, then the pockets
    d->num_oasis_air = 0;
    const int ends[2] = { 7, TW - 9 };
    for (int e : ends) {
        int sx0 = e * S + 2, sx1 = (e + 1) * S + 14;
        int line = std::min(ceil[sx0 - 1], ceil[sx1]), open_to = line;
        for (int px = sx0; px < sx1; px++) open_to = std::max(open_to, ceil[px]);
        for (int px = sx0; px < sx1; px++)
            for (int y = 0; y < open_to; y++) oasis_set(d, px, y, false);
        d->oasis_air[d->num_oasis_air++] = { (int16_t)sx0, (int16_t)sx1, (int16_t)line };
    }
    for (auto& h : pockets)
        if (d->num_oasis_air < 24) d->oasis_air[d->num_oasis_air++] = { (int16_t)h.x0, (int16_t)h.x1, (int16_t)h.line };
    // sections: narrow stretches are tunnels; the open ones cut 1-3 screens at
    // a time into cave, cavern and the leviathan's pass, never twice running
    d->num_oasis_sec = 0;
    int lastk = -1;
    for (int x = 0; x < TW && d->num_oasis_sec < 40;) {
        int e = x;
        while (e < TW && narrow[e] == narrow[x]) e++;
        if (narrow[x]) { d->oasis_sec[d->num_oasis_sec++] = { 0, (int16_t)(x * S), (int16_t)(e * S) }; lastk = 0; x = e; continue; }
        while (x < e && d->num_oasis_sec < 40) {
            int n = std::min(e - x, (1 + rr(3)) * 20);
            if (e - (x + n) < 10) n = e - x;
            int k;
            do k = 1 + rr(3); while (k == lastk);
            d->oasis_sec[d->num_oasis_sec++] = { (uint8_t)k, (int16_t)(x * S), (int16_t)((x + n) * S) };
            lastk = k; x += n;
        }
    }
    // weed on the seabed, out of the tunnels: its foot at the lowest of the
    // seabed under it, so none of it shows cut off above a dip
    d->num_oasis_weed = 0;
    for (int x = 0; x < TW && d->num_oasis_weed < 320; x++) {
        if (narrow[x] || pyr_hash((uint32_t)x * 31u, d->oasis_seed) % 5) continue;
        int foot = 0;
        for (int px = x * S + 2; px < x * S + 14; px++) {
            int y = ceil[px];
            while (y < OASIS_PX_H && !oasis_rock(d, px, y)) y++;
            foot = std::max(foot, y);
        }
        foot += 2;
        if (foot - 32 > ceil[x * S + 8] + 4) d->oasis_weed[d->num_oasis_weed++] = { (int16_t)(x * S), (int16_t)(foot - 32) };
    }
    // on the map: the level's top left at tile (8, 8); a tile walkable where
    // its middle is water; the ways out at the top of each shaft, the tile
    // above them rock (the ladder goes up from there)
    d->oasis_x0 = 8 * S; d->oasis_y0 = 8 * S;
    for (int ty = 8; ty < 8 + OASIS_ROWS; ty++)
        for (int tx = 8; tx < 8 + TW && tx < DMAP_W; tx++)
            if (!oasis_rock(d, (tx - 8) * S + 8, (ty - 8) * S + 8)) d->tiles[ty][tx] = DNG_FLOOR;
    // the ways out at each shaft's surface: the tile under the swimmer's feet
    // when it has surfaced, its head up out of the water (the feet 12 below the head)
    for (int i = 0; i < 2; i++) {
        int tx, ty;
        oasis_way_tile(d, i, &tx, &ty);
        if (i == 0) { d->entry_x = tx; d->entry_y = ty; } else { d->exit_x = tx; d->exit_y = ty; }
        d->tiles[ty][tx] = i == 0 ? DNG_ENTRY : DNG_EXIT;
        d->tiles[ty - 1][tx] = DNG_WALL;
    }
}

// ── STONEHENGE: the barrow, a block maze after the user's reference ──────
//
// Mother 1's ice maze, built as the barrow under the standing stones: walls of
// stone blocks one block thick with the overworld's grass on top, running
// east-west and back at 45 degrees in the game's oblique (x + d, B - z - d),
// over a starry sky (the user's picks). The maze is a logical one, odd cells
// corridors and even cells walls (shg_generate_maze); a wall cell is filled
// with blocks 32 wide, 16 deep and 64 tall -- measured off the reference at
// its own pixels -- and a corridor is 96 wide and 160 deep, so the floor that
// shows between two walls is about as deep as a corridor is wide. The tilemap
// is the picture: a tile is walkable where its middle shows floor, and solid
// where a wall stands over it, so what is seen is what is walked.

#define SHG_W 11
#define SHG_H 9
static const int BRW_CX = 96, BRW_CD = 160;                  // a corridor: wide, deep

enum { SHG_CELL_WALL = 0, SHG_CELL_FLOOR = 1 };

static bool shg_in_bounds(int x, int y) {
    return x >= 0 && x < SHG_W && y >= 0 && y < SHG_H;
}
static bool shg_is_inner_odd_cell(int x, int y) {
    return x > 0 && x < SHG_W-1 && y > 0 && y < SHG_H-1 && (x&1) && (y&1);
}
static void shg_clear(uint8_t grid[SHG_H][SHG_W]) {
    for (int y = 0; y < SHG_H; y++)
        for (int x = 0; x < SHG_W; x++)
            grid[y][x] = SHG_CELL_WALL;
}
static void shg_set_floor(uint8_t grid[SHG_H][SHG_W], int x, int y) {
    if (shg_in_bounds(x, y)) grid[y][x] = SHG_CELL_FLOOR;
}

static void shg_generate_maze(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    int stack_x[SHG_W * SHG_H], stack_y[SHG_W * SHG_H], top = 0;
    static const int DIRS[4][2] = {{0,-2},{2,0},{0,2},{-2,0}};
    shg_set_floor(grid, 1, 1);
    stack_x[top] = 1; stack_y[top] = 1; top++;
    while (top > 0) {
        int cx = stack_x[top-1], cy = stack_y[top-1];
        int order[4] = {0,1,2,3};
        for (int i = 3; i > 0; i--) {
            int j = (int)(rng_next(rng) % (unsigned)(i+1));
            int t = order[i]; order[i] = order[j]; order[j] = t;
        }
        bool moved = false;
        for (int i = 0; i < 4; i++) {
            int dx = DIRS[order[i]][0], dy = DIRS[order[i]][1];
            int nx = cx+dx, ny = cy+dy;
            if (!shg_is_inner_odd_cell(nx, ny)) continue;
            if (grid[ny][nx] == SHG_CELL_FLOOR) continue;
            shg_set_floor(grid, cx+dx/2, cy+dy/2);
            shg_set_floor(grid, nx, ny);
            stack_x[top] = nx; stack_y[top] = ny; top++;
            moved = true; break;
        }
        if (!moved) top--;
    }
}

static void shg_add_loops(uint8_t grid[SHG_H][SHG_W], uint32_t* rng) {
    int attempts = SHG_W * SHG_H / 25 + (int)(rng_next(rng) % 3);   // a few, as the reference has
    for (int i = 0; i < attempts; i++) {
        int x = 1 + (int)(rng_next(rng) % (SHG_W-2));
        int y = 1 + (int)(rng_next(rng) % (SHG_H-2));
        if (grid[y][x] != SHG_CELL_WALL) continue;
        bool horiz = (x>0 && x<SHG_W-1 && grid[y][x-1]==SHG_CELL_FLOOR && grid[y][x+1]==SHG_CELL_FLOOR);
        bool vert  = (y>0 && y<SHG_H-1 && grid[y-1][x]==SHG_CELL_FLOOR && grid[y+1][x]==SHG_CELL_FLOOR);
        if (horiz || vert) grid[y][x] = SHG_CELL_FLOOR;
    }
}

// The ways out: corridor cells (odd, odd) with a flat wall straight behind
// them, so each ladder stands in the middle of one (user) -- the first such
// cell, and the one furthest from it.
static void shg_pick_portals(uint8_t grid[SHG_H][SHG_W],
                             int* entry_u, int* entry_v,
                             int* exit_u,  int* exit_v) {
    auto ok = [&](int x, int y) {
        return (x & 1) && (y & 1) && grid[y][x] == SHG_CELL_FLOOR && grid[y - 1][x] == SHG_CELL_WALL;
    };
    int eu = 1, ev = 1;
    bool found = false;
    for (int y = 0; y < SHG_H && !found; y++)
        for (int x = 0; x < SHG_W; x++)
            if (ok(x, y)) { eu=x; ev=y; found=true; break; }
    int fu = eu, fv = ev, best = -1;
    for (int y = 0; y < SHG_H; y++)
        for (int x = 0; x < SHG_W; x++) {
            if (!ok(x, y)) continue;
            int dist = abs(x-eu) + abs(y-ev);
            if (dist > best) { best=dist; fu=x; fv=y; }
        }
    *entry_u=eu; *entry_v=ev; *exit_u=fu; *exit_v=fv;
}

// A parallelogram of ground -- x across [x0, x1), d back [da, db) -- as the
// oblique view draws it (art pixel (OX + x + d, OY - 1 - d)), added to the
// map's collision as a box and two triangles, or two triangles when it is
// deeper than it is wide. Its slanted edges sit half a pixel in, so a pixel
// is inside exactly when its middle is; the right one a pixel further, over
// the foot of the side face the view shows there.
static void col_add_ground(DungeonMap* dm, int OX, int OY, int x0, int x1, int da, int db) {
    float Yb = (float)(OY - da), Yt = (float)(OY - db), h = (float)(db - da);
    float L = OX + x0 + da - 0.5f, R = OX + x1 + 1 + da - 0.5f;
    auto add = [&](bool box, float ax, float ay, float bx, float by, float cx, float cy) {
        if (dm->num_col_shapes < DMAP_MAX_COL_SHAPES)
            dm->col_shapes[dm->num_col_shapes++] = { box, { ax, bx, cx }, { ay, by, cy } };
    };
    if (R - L >= h) {
        add(true, L + h, Yt, R, Yb, 0, 0);                    // the box between the slants
        add(false, L, Yb, L + h, Yb, L + h, Yt);              // the left slant
        add(false, R, Yb, R + h, Yt, R, Yt);                  // the right slant
    } else {
        add(false, L, Yb, R, Yb, R + h, Yt);
        add(false, L, Yb, R + h, Yt, L + h, Yt);
    }
}

// Whether art pixel (ax, ay)'s middle is in any of the map's collision shapes.
static bool col_solid(const DungeonMap* dm, int ax, int ay) {
    float px = ax + 0.5f, py = ay + 0.5f;
    for (int i = 0; i < dm->num_col_shapes; i++) {
        const auto& s = dm->col_shapes[i];
        if (s.box) {
            if (px >= s.x[0] && px <= s.x[1] && py >= s.y[0] && py <= s.y[1]) return true;
            continue;
        }
        float e[3];
        for (int k = 0; k < 3; k++) {
            int j = (k + 1) % 3;
            e[k] = (s.x[j] - s.x[k]) * (py - s.y[k]) - (s.y[j] - s.y[k]) * (px - s.x[k]);
        }
        if ((e[0] >= 0 && e[1] >= 0 && e[2] >= 0) || (e[0] <= 0 && e[1] <= 0 && e[2] <= 0)) return true;
    }
    return false;
}

static void carve_stonehenge_layout(DungeonMap* dmap, uint32_t* rng) {
    uint8_t grid[SHG_H][SHG_W];
    shg_clear(grid);
    shg_generate_maze(grid, rng);
    shg_add_loops(grid, rng);

    // the ground: x across, the cells' widths; d back from the front, row 0
    // the farthest
    int xs[SHG_W + 1], d0[SHG_H], dsz[SHG_H], depth = 0;
    xs[0] = 0;
    for (int u = 0; u < SHG_W; u++) xs[u + 1] = xs[u] + ((u & 1) ? BRW_CX : BRW_BW);
    for (int v = SHG_H - 1; v >= 0; v--) {
        dsz[v] = (v & 1) ? BRW_CD : BRW_BD;
        d0[v] = depth; depth += dsz[v];
    }
    const int OX = 64 * 16, OY = 64 * 16 + depth + BRW_BZ + BRW_BD;
    dmap->barrow_ox = OX; dmap->barrow_oy = OY;
    dmap->barrow_seed = rng_next(rng);
    dmap->barrow_x0 = OX;                            dmap->barrow_y0 = OY - depth - BRW_BZ - BRW_BD;
    dmap->barrow_w  = xs[SHG_W] + depth + BRW_BD;    dmap->barrow_h  = depth + BRW_BZ + BRW_BD;

    // every wall cell filled with blocks, its ground footprint solid
    int nb = 0;
    dmap->num_col_shapes = 0;
    for (int v = 0; v < SHG_H; v++)
        for (int u = 0; u < SHG_W; u++) {
            if (grid[v][u] != SHG_CELL_WALL) continue;
            col_add_ground(dmap, OX, OY, xs[u], xs[u + 1], d0[v], d0[v] + dsz[v]);
            for (int x = xs[u]; x < xs[u + 1]; x += BRW_BW)
                for (int d = d0[v]; d < d0[v] + dsz[v]; d += BRW_BD)
                    if (nb < DMAP_MAX_BARROW_BLOCKS)
                        dmap->barrow_blocks[nb++] = { (int16_t)x, (int16_t)d };
        }
    dmap->num_barrow_blocks = nb;

    // the tiles: walkable where the middle is the maze's ground and in no
    // wall's footprint -- behind a wall too, where the wall stands over you;
    // the rest of the picture is wall art
    auto ground = [&](int sx, int sy) {
        int d = OY - 1 - sy, x = sx - OX - d;
        return d >= 0 && d < depth && x >= 0 && x < xs[SHG_W];
    };
    int tx0 = dmap->barrow_x0 / 16, ty0 = dmap->barrow_y0 / 16;
    int tx1 = (dmap->barrow_x0 + dmap->barrow_w) / 16 + 1, ty1 = (dmap->barrow_y0 + dmap->barrow_h) / 16 + 1;
    for (int ty = ty0; ty <= ty1; ty++)
        for (int tx = tx0; tx <= tx1; tx++) {
            int cx = tx * 16 + 8, cy = ty * 16 + 8;
            if (ground(cx, cy) && !col_solid(dmap, cx, cy)) {
                dmap->tiles[ty][tx] = DNG_FLOOR; dmap->art[ty][tx] = WA_FLOOR;
            } else {
                dmap->art[ty][tx] = WA_BAND;
            }
        }

    // the ways out: a ladder in the middle of each one's flat back wall -- of
    // the part of it in sight to its foot: the wall column to the corridor's
    // east stands 64 tall in front of it and hides all but its west 32 -- the
    // portal on the first tile row in front of that wall's foot (so the tile
    // above it is under the wall)
    int eu, ev, xu, xv;
    shg_pick_portals(grid, &eu, &ev, &xu, &xv);
    auto place = [&](int w, int u, int v, int* px, int* py) {
        dmap->barrow_way_x[w] = xs[u] + BRW_BW / 2;
        dmap->barrow_way_d[w] = d0[v] + dsz[v];
        barrow_way_tile(dmap, w, px, py);
    };
    place(0, eu, ev, &dmap->entry_x, &dmap->entry_y);
    place(1, xu, xv, &dmap->exit_x, &dmap->exit_y);
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
}

// ── Portal clearing ───────────────────────────────────────────────────────
// Carves a 3×3 floor area around each portal so the player never spawns
// inside or immediately adjacent to a wall.
static void clear_portal_surroundings(DungeonMap* dmap) {
    // Every layout writes entry_x/exit_x and only the cave fills the portal
    // array, so adopt the pair here rather than at each of the half-dozen call
    // sites. Getting this wrong is silent: an unfilled array means the loop
    // below does nothing and every non-cave dungeon loses the pocket of floor
    // around its stairs.
    //
    // The destinations start at -1: dungeon_generate() zeroes num_portals but
    // leaves the LAST dungeon's landings sitting in the array, and inheriting
    // one of those is a door that opens somewhere else entirely.
    if (dmap->num_portals == 0) {
        dmap->portals[0] = { dmap->entry_x, dmap->entry_y, -1, -1 };
        dmap->portals[1] = { dmap->exit_x,  dmap->exit_y,  -1, -1 };
        dmap->num_portals = 2;
    } else {
        // A second call means the pair moved after it was carved -- which is
        // what dungeon_orient_portals() does to every partnered dungeon. The
        // array is the list of stair tiles, so it has to follow the move, or
        // the restore loop below stamps stairs straight back onto the ground
        // the move had just cleared. That is where the four sets of stairs in
        // a catacombs came from: two entries and two exits, all four of them a
        // door out, and only two of them in the array. Syncing here rather
        // than at the mover means the next thing to re-site a portal cannot
        // reintroduce it. Destinations are left alone -- this is about where a
        // portal IS, not where it goes.
        dmap->portals[0].tx = dmap->entry_x; dmap->portals[0].ty = dmap->entry_y;
        dmap->portals[1].tx = dmap->exit_x;  dmap->portals[1].ty = dmap->exit_y;
    }
    // Every portal, not just the pair: a cave's extra mouths need the same
    // pocket of floor around them or the player lands facing a wall. Not where
    // the walls are built art (the ruins, the pyramid, the barrow): the pocket
    // would knock a hole in a wall still drawn -- the ruins' rules and art are
    // done before a pair is oriented -- and each way out is seated at a wall's
    // foot with floor in front of it anyway.
    bool built = dmap->type == DUNGEON_ENT_PYRAMID || dmap->type == DUNGEON_ENT_RUINS || fixed_ways(dmap);
    for (int p = 0; p < dmap->num_portals && !built; p++) {
        for (int dy = -1; dy <= 1; dy++) {
            for (int dx = -1; dx <= 1; dx++) {
                int tx = dmap->portals[p].tx + dx, ty = dmap->portals[p].ty + dy;
                if (tx < 0 || tx >= DMAP_W || ty < 0 || ty >= DMAP_H) continue;
                if (dmap->tiles[ty][tx] == DNG_WALL)
                    dmap->tiles[ty][tx] = DNG_FLOOR;
            }
        }
    }
    // Restore portal tiles in case they were adjacent to each other. Portal 0
    // is the entry; the rest are exits.
    for (int p = 0; p < dmap->num_portals; p++)
        dmap->tiles[dmap->portals[p].ty][dmap->portals[p].tx] = p ? DNG_EXIT : DNG_ENTRY;
}

// ── Giant tree: terraces in a triangle ───────────────────────────────────
// The user's reference (Mother 1's tower): floors stepping up a wall of solid
// mass, ladders up the walls between them. Every tier is one level of the
// mass, each wall rises one level (TREE_Z) and its top IS the next tier's
// floor. In the picture depth and height both go up the screen, so a floor's
// front edge is the top of the wall rising from the level in front of it:
// F_t = B_front - TREE_Z, and the floor shows where F - B > 0. Each tier is
// one terrace across its width whose back edge steps between three rows, so
// floors run 48, 112 or 176 deep (the reference's) or pinch to nothing -- the
// gaps between walkways -- and every end tapers at 45 degrees. The whole is a
// triangle, each tier 2 units narrower a side than the one below: narrow up
// the trunk, wide through the roots; the way in is the middle tier's floor,
// the ground line, and its door (the overworld's hollow) the only way out
// (user). Mocked in the scratch tree_gen2.py, its picture by tree_bake.
static const int TREE_U = 64, TREE_P = 3, TREE_TOP = 2, TREE_Z = 144;

// Whether picture pixel (x, y) is ground the feet may stand on: a floor, or a ladder.
static bool tree_walkable(const DungeonMap* d, int x, int y) {
    if (x < 0 || y < 0 || x >= d->tree_w || y >= d->tree_h) return false;
    for (int t = 0; t < d->tree_n; t++)
        if (y >= d->tree_b[t][x] && y < d->tree_b[t + 1][x] - d->tree_z) return true;
    for (int i = 0; i < d->num_tree_ladders; i++) {
        const auto& l = d->tree_ladders[i];
        if (x >= l.x0 && x < l.x0 + 16 && y >= l.y0 && y < l.y1) return true;
    }
    return false;
}

// The ladder feet centred at picture pixel (fx, fy) are on, or are stepping
// onto -- near its middle and pressing on along it from just below its foot
// or just above its top -- or -1. dy: the way pressed, up or down.
static int tree_ladder_at(const DungeonMap* d, float fx, float fy, float dy) {
    for (int i = 0; i < d->num_tree_ladders; i++) {
        const auto& l = d->tree_ladders[i];
        if (fabsf(fx - (l.x0 + 8)) > 10) continue;
        if ((fy >= l.y0 && fy < l.y1) ||
            (dy < 0 && fy >= l.y1 && fy - l.y1 < 4) ||
            (dy > 0 && fy < l.y0 && l.y0 - fy <= 4)) return i;
    }
    return -1;
}
static bool tree_on_ladder(const DungeonMap* d, float fx, float fy) {
    for (int i = 0; i < d->num_tree_ladders; i++) {
        const auto& l = d->tree_ladders[i];
        if (fx >= l.x0 && fx < l.x0 + 16 && fy >= l.y0 && fy < l.y1) return true;
    }
    return false;
}

// ── Terraces: what the giant tree stands on ──────────────────────────────
// Levels stepping up the screen, each wall one level (tree_z) tall with the
// next tier's floor on its top; tree_b[t][x] is the back edge of tier t's floor
// at picture column x, tree_b[N] the line in front of the lowest. Given each
// tier's back edge as its layout has it (back(t, x); t == N that line), this
// stands the levels one behind another, closes a floor never 48 deep (the
// reference's least: a pinch's tip, not a floor), asks where the ways out go
// (pick), and joins the floors by ladders: up a wall between a level and the
// next behind it, wherever both are flat over 16 pixels; a tree of them from
// the first way out's floor, a fifth of the rest for loops; a floor no ladder
// can reach is closed and the lot rebuilt. A way out left on a closed floor is
// asked for again. False if pick finds no place. stand: how deep both floors
// must be where a ladder joins them -- 1 for the tree, any floor at all; a
// cave's 48, so a ladder's ends are on the floors' bodies and never on a
// taper's tip, where the tiles (terraces_tiles) lose the way the feet have.
static uint8_t s_ter_pin[TREE_MAX_TIERS][TREE_MAX_W];      // a floor closed at a column: its level has no depth there
struct TerWay { int tier, x; };                            // a way out: its floor's tier, the middle of its doorway (32 wide)
static int ter_depth(const DungeonMap* d, int t, int x) { return d->tree_b[t + 1][x] - d->tree_z - d->tree_b[t][x]; }

template <class Back, class Pick>
static bool terraces_join(DungeonMap* d, uint32_t* rng, int N, int W, int stand, Back back, Pick pick, std::vector<TerWay>& ways) {
    const int Z = d->tree_z;
    auto rnd = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    // The levels per column, front to back: each stands one wall above the one
    // in front; a level with no floor here has no depth, and the walls meet.
    auto& pin = s_ter_pin;
    memset(pin, 0, sizeof pin);
    auto build = [&]() {
        for (int x = 0; x < W; x++) {
            int bf = back(N, x);
            d->tree_b[N][x] = (int16_t)bf;
            for (int t = N - 1; t >= 0; t--) {
                int f = bf - Z, b = pin[t][x] ? f : std::min(back(t, x), f);
                d->tree_b[t][x] = (int16_t)b;
                bf = b;
            }
        }
    };
    auto depth = [&](int t, int x) { return ter_depth(d, t, x); };
    auto stack = [&](int x, int* st) {                // the tiers whose floors show at x, front to back
        int n = 0;
        for (int t = N - 1; t >= 0; t--) if (depth(t, x) >= 1) st[n++] = t;
        return n;
    };
    // a floor never 48 deep (the reference's least) is a pinch's tip, not a floor
    build();
    for (int t = 0; t < N; t++)
        for (int x = 0; x < W;) {
            if (depth(t, x) < 1) { x++; continue; }
            int x0 = x, dep = 0;
            while (x < W && depth(t, x) >= 1) dep = std::max(dep, depth(t, x++));
            if (dep < 48) for (int i = x0; i < x; i++) pin[t][i] = 1;
        }
    build();

    static int16_t comp[TREE_MAX_TIERS][TREE_MAX_W];
    struct Edge { int a, b; std::vector<int> xs; };
    std::vector<Edge> cands;
    std::vector<std::pair<int, int>> chosen;           // (edge, x0)
    for (;;) {
        ways.clear();
        if (!pick(ways)) return false;
        for (;;) {
            build();
            int ncomp = 0;
            for (int t = 0; t < N; t++) {
                bool prev = false;
                for (int x = 0; x < W; x++) {
                    bool on = depth(t, x) >= 1;
                    if (on && !prev) ncomp++;
                    comp[t][x] = on ? (int16_t)(ncomp - 1) : (int16_t)-1;
                    prev = on;
                }
            }
            cands.clear();
            for (int x0 = 0; x0 < W - 16; x0 += 16) {
                int st[TREE_MAX_TIERS], ns = stack(x0, st);
                for (int i = 0; i + 1 < ns; i++) {
                    int a = st[i], b = st[i + 1];
                    // a block clear of a way out either side (user), up to its floor or from it
                    bool by_way = false;
                    for (const TerWay& w : ways)
                        by_way = by_way || ((a == w.tier || b == w.tier) && x0 + 16 > w.x - 32 && x0 < w.x + 32);
                    if (by_way) continue;
                    bool ok = true;
                    for (int x = x0; x < x0 + 16 && ok; x++) {
                        int s2[TREE_MAX_TIERS], n2 = stack(x, s2);
                        ok = n2 > i + 1 && s2[i] == a && s2[i + 1] == b && depth(a, x) >= stand && depth(b, x) >= stand &&
                             d->tree_b[a][x] == d->tree_b[a][x0] && d->tree_b[b + 1][x] == d->tree_b[b + 1][x0];
                    }
                    if (!ok) continue;
                    int ka = comp[a][x0], kb = comp[b][x0];
                    auto it = std::find_if(cands.begin(), cands.end(), [&](const Edge& e) { return e.a == ka && e.b == kb; });
                    if (it == cands.end()) { cands.push_back({ ka, kb, {} }); it = cands.end() - 1; }
                    it->xs.push_back(x0);
                }
            }
            std::vector<char> reached(ncomp, 0);
            reached[comp[ways[0].tier][ways[0].x]] = 1;
            chosen.clear();
            for (;;) {
                std::vector<int> grow;
                for (int e = 0; e < (int)cands.size(); e++)
                    if (reached[cands[e].a] != reached[cands[e].b]) grow.push_back(e);
                if (grow.empty()) break;
                int e = grow[rnd((int)grow.size())];
                chosen.push_back({ e, cands[e].xs[rnd((int)cands[e].xs.size())] });
                reached[cands[e].a] = reached[cands[e].b] = 1;
            }
            for (int e = 0; e < (int)cands.size(); e++) {
                if (!reached[cands[e].a] || !reached[cands[e].b]) continue;
                bool have = std::any_of(chosen.begin(), chosen.end(), [&](const std::pair<int, int>& c) { return c.first == e; });
                if (!have && rnd(100) < 20) chosen.push_back({ e, cands[e].xs[rnd((int)cands[e].xs.size())] });
            }
            bool lost = false;
            for (int t = 0; t < N; t++)
                for (int x = 0; x < W; x++)
                    if (comp[t][x] >= 0 && !reached[comp[t][x]]) { pin[t][x] = 1; lost = true; }
            if (!lost) break;
        }
        bool stand = true;                             // every way out still on a floor that is left
        for (const TerWay& w : ways) stand = stand && comp[w.tier][w.x] >= 0;
        if (stand) break;
    }
    // the floors, numbered as their components are (tier by tier, left to right)
    d->num_tree_floors = 0;
    for (int t = 0; t < N; t++)
        for (int x = 0; x < W;) {
            if (comp[t][x] < 0) { x++; continue; }
            int x0 = x;
            while (x < W && comp[t][x] == comp[t][x0]) x++;
            if (d->num_tree_floors < TREE_MAX_FLOORS) d->tree_floors[d->num_tree_floors++] = { (int16_t)t, (int16_t)x0, (int16_t)x };
        }
    d->num_tree_ladders = 0;
    for (const auto& c : chosen) {
        if (d->num_tree_ladders >= TREE_MAX_LADDERS) break;
        const Edge& e = cands[c.first];
        int x0 = c.second, st[TREE_MAX_TIERS], ns = stack(x0, st);
        for (int i = 0; i + 1 < ns; i++) {
            if (comp[st[i]][x0] != e.a || comp[st[i + 1]][x0] != e.b) continue;
            d->tree_ladders[d->num_tree_ladders++] = { (int16_t)x0, (int16_t)(d->tree_b[st[i + 1] + 1][x0] - Z),
                                                       (int16_t)d->tree_b[st[i]][x0], (int16_t)e.a, (uint8_t)(st[i] > d->tree_e) };
            break;
        }
    }
    return true;
}

static bool tree_walkable(const DungeonMap* d, int x, int y);

// The tiles (sight, spawners, loot; the feet go by the pixel): floor where a
// tile's middle is ground to stand on and the tiles join it to (tx, ty) -- a
// taper's tip can leave a middle on ground with none beside it.
static void terraces_tiles(DungeonMap* d, int tx, int ty) {
    static uint8_t on[DMAP_H][DMAP_W];
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            on[y][x] = tree_walkable(d, x * 16 + 8 - d->tree_ox, y * 16 + 8 - d->tree_oy);
    std::vector<int> q = { ty * DMAP_W + tx };
    on[ty][tx] = 0;
    for (size_t h = 0; h < q.size(); h++) {
        int x = q[h] % DMAP_W, y = q[h] / DMAP_W;
        d->tiles[y][x] = DNG_FLOOR;
        const int dx[4] = { 1, -1, 0, 0 }, dy[4] = { 0, 0, 1, -1 };
        for (int k = 0; k < 4; k++) {
            int nx = x + dx[k], ny = y + dy[k];
            if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H || !on[ny][nx]) continue;
            on[ny][nx] = 0;
            q.push_back(ny * DMAP_W + nx);
        }
    }
}

static void carve_tree_terraces(DungeonMap* d, uint32_t* rng) {
    const int U = TREE_U, P = TREE_P, TOP = TREE_TOP, Z = TREE_Z;
    auto rnd = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    static const int NS[4] = { 7, 9, 11, 13 };
    const int N = NS[rnd(4)], E = N / 2;               // tiers; the way in's is the middle
    const int R0 = 2 + rnd(3);                         // the top tier's half width, units
    int R[TREE_MAX_TIERS];
    for (int t = 0; t < N; t++) R[t] = R0 + 2 * t;     // 2 units wider a side each tier down
    const int W = 2 * (R[N - 1] + 4) * U, H = (TOP + N * P + 1) * U;
    const int Cx = W / 2, Cu = Cx / U, FRONT_B = (TOP + N * P) * U;
    // the hollow: the tiers' own slope, 1.5 units clear of their ends; a floor
    // stops at it
    auto half = [&](int y) { return (R0 + 2.0f * ((float)y / U - TOP) / P) * U + 96; };
    d->tree_n = N; d->tree_e = E; d->tree_w = W; d->tree_h = H; d->tree_z = Z;
    d->tree_ox = 8 * 16; d->tree_oy = 8 * 16;
    d->tree_seed = rng_next(rng) * 65536u + rng_next(rng);

    // Each tier's back edge, a row offset (-1, 0, 1) per unit column. Floor
    // depth = 48 + 64 * (o[t+1] - o[t]). Built from the bottom up, so a tier can
    // be held to the one in front: ends 48 deep (their taper stays over the
    // tier in front), and no pinch where nothing stands behind to reach a
    // cut-off floor from -- past the next tier up's ends, the lowest tier (the
    // ground in front of it), the way in's floor (one floor, the ground line).
    static int8_t offs[TREE_MAX_TIERS][64];
    for (int t = N - 1; t >= 0; t--) {
        const int n = 2 * R[t], c0 = Cu - R[t];
        int8_t* o = offs[t];
        auto front = [&](int c) { return offs[t + 1][c - (Cu - R[t + 1])]; };
        int cur = rnd(3) - 1;
        for (int i = 0; i < n; i++) {
            if (i > 0 && rnd(100) < 35) cur = std::max(-1, std::min(1, cur + (rnd(2) ? 1 : -1)));
            o[i] = (int8_t)cur;
        }
        if (t != E && t + 1 < N)
            for (int i : { 0, n - 1 }) {
                o[i] = (int8_t)std::max(-1, std::min(1, (int)front(c0 + i)));
                int j = i == 0 ? 1 : n - 2;            // and no two-row jump beside it
                o[j] = (int8_t)std::max(o[i] - 1, std::min(o[i] + 1, (int)o[j]));
            }
        for (int i = 0; i < n; i++) {
            int c = c0 + i;
            if (t == N - 1) o[i] = (int8_t)std::min((int)o[i], 0);
            else if (t == E || t == 0 || fabsf(c - Cu + 0.5f) > R[t - 1])
                o[i] = (int8_t)std::min(o[i], front(c));
        }
        for (int k = 0; k < 3; k++)                    // steps of one row: lower a neighbour two above
            for (int i = 1; i < n; i++) {
                o[i] = (int8_t)std::min(o[i] + 0, o[i - 1] + 1);
                o[n - 1 - i] = (int8_t)std::min(o[n - 1 - i] + 0, o[n - i] + 1);
            }
    }
    // B_t(x): in a terrace, flat or 45 degrees at a step; past its ends running
    // on down at 45 degrees, so the level tapers out; none past the hollow
    const int INF = 1 << 28;
    auto back = [&](int t, int x) {
        const int n = 2 * R[t], c0 = Cu - R[t], base = TOP + t * P;
        auto row = [&](int i) { return base + offs[t][i]; };
        const int x0 = c0 * U, x1 = (c0 + n) * U;
        int b;
        if (x < x0) b = row(0) * U + (x0 - x);
        else if (x >= x1) b = row(n - 1) * U + (x - x1 + 1);
        else {
            int i = (x - x0) / U;
            b = (!i || row(i) == row(i - 1)) ? row(i) * U : row(i - 1) * U + (row(i) - row(i - 1)) * (x - x0 - i * U);
        }
        return fabsf((float)(x - Cx)) >= half(b) - 1 ? INF : b;
    };

    // The door: a flat column of the way in's floor, flat either side, nearest
    // the middle, where the floor truly is 48 deep -- a pinch in front of it
    // merges the walls there and leaves it shallower, even to nothing. Chosen
    // once the layout stands: pinching a floor out later only deepens the one
    // behind it. Failing any, the levels in front of the middle column are
    // pinched out under it.
    std::vector<TerWay> ways;
    terraces_join(d, rng, N, W, 1, [&](int t, int x) { return t == N ? FRONT_B : back(t, x); },
                  [&](std::vector<TerWay>& w) {
        auto deep = [&](int c) {
            for (int x = c * U; x < (c + 1) * U; x++) if (ter_depth(d, E, x) < 48) return false;
            return true;
        };
        int door_c = -1;
        for (int i = 1; i + 1 < 2 * R[E]; i++)
            if (offs[E][i] == offs[E][i - 1] && offs[E][i] == offs[E][i + 1] && deep(Cu - R[E] + i)) {
                int c = Cu - R[E] + i;
                if (door_c < 0 || abs(c - Cu) < abs(door_c - Cu)) door_c = c;
            }
        if (door_c < 0) {
            door_c = Cu;
            for (int t = E + 1; t < N; t++)
                for (int x = door_c * U; x < (door_c + 1) * U; x++) s_ter_pin[t][x] = 1;
        }
        w.push_back({ E, door_c * U + 32 });
        return true;
    }, ways);
    const int door_x = ways[0].x;

    // the way out: the floor before the door, which stands two tiles wide on
    // the back wall; the second tile is the layout's exit, which a solo binding
    // floors again (a giant tree never pairs)
    int tx = (d->tree_ox + door_x - 16) / 16, ty = (d->tree_oy + d->tree_b[E][door_x]) / 16;
    terraces_tiles(d, tx, ty);
    d->entry_x = tx;     d->entry_y = ty;
    d->exit_x  = tx + 1; d->exit_y  = ty;
    d->tiles[ty][tx]     = DNG_ENTRY;
    d->tiles[ty][tx + 1] = DNG_EXIT;
}

// ── Caves: terraces, a level of the mountain each ────────────────────────
// The user's reference (an EarthBound cave): floors on several levels, a tall
// band of fluted rock behind each, its top and foot flat or at 45 degrees and
// parallel, ladders up the bands between. A cave has a floor for every level
// its mountain's mouths stand on outside (want_lvl), the flat's lowest and at
// the front, and each mouth is on the back wall of its own level's floor --
// an arch for a mouth walked into outside, a ladder up into a hatch for a
// hole climbed down (want_hole) -- laid across the cave as the mouths lie
// across the mountain. The back
// wall runs on up to the top of the map; the lowest floor is a ledge, rock
// hanging CAVE_UNDER below its edge over the dark. The terraces are the giant
// tree's (terraces_join), a wall CAVE_Z tall; mocked in art/structures/
// dungeon_walls/cave_terrace_mock.py, the picture by cave_bake.
static const int CAVE_Z = 80, CAVE_TOP = 3, CAVE_UNITS = 28, CAVE_UNDER = 32, CAVE_BELOW = 96;

static void carve_cave_terraces(DungeonMap* d, uint32_t* rng) {
    const int U = TREE_U, P = TREE_P, TOP = CAVE_TOP, UNITS = CAVE_UNITS;
    auto rnd = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    const int want = d->want_portals;
    int lvl[DMAP_MAX_PORTALS], top = 0, ox0 = d->want_ox[0], ox1 = d->want_ox[0];
    for (int m = 0; m < want; m++) {
        lvl[m] = std::max(0, std::min(3, d->want_lvl[m]));
        top = std::max(top, lvl[m]);
        ox0 = std::min(ox0, d->want_ox[m]); ox1 = std::max(ox1, d->want_ox[m]);
    }
    if (top == 0) {                                    // no mountain to take levels from: two, a way out on each
        for (int m = 0; m < want; m++) lvl[m] = m & 1;
        top = 1;
    }
    const int N = top + 1, W = UNITS * U, H = (TOP + N * P + 1) * U + CAVE_BELOW;
    d->tree_n = N; d->tree_e = N; d->tree_w = W; d->tree_h = H; d->tree_z = CAVE_Z;
    d->tree_ox = 8 * 16; d->tree_oy = 8 * 16;
    d->tree_seed = rng_next(rng) * 65536u + rng_next(rng);

    // Each tier's back edge, a row offset (-1, 0, 1) per unit column, between its
    // two ends; tier N is the line the lowest floor's front edge stands Z above.
    static int8_t offs[TREE_MAX_TIERS + 1][64];
    int end0[TREE_MAX_TIERS + 1], end1[TREE_MAX_TIERS + 1];
    auto back = [&](int t, int x) {
        auto row = [&](int i) { return TOP + t * P + offs[t][i]; };
        const int a = end0[t], b = end1[t];
        if (x < a * U) return row(a) * U + (a * U - x);              // past an end: on down at 45 degrees
        if (x >= b * U) return row(b - 1) * U + (x - b * U + 1);
        const int i = x / U, lx = x % U, r0 = i > a ? row(i - 1) : row(i), r1 = row(i);
        return r0 == r1 ? r1 * U : r0 * U + (r1 > r0 ? lx + 1 : -lx);   // a step: 45 degrees across the column
    };
    // A mouth a way out: on its level's floor, a flat 64 pixels where the floor
    // is 48 deep, as far across the cave as the mouth lies across the mountain;
    // two on one floor two columns apart.
    auto pick = [&](std::vector<TerWay>& w) {
        for (int m = 0; m < want; m++) {
            const int t = N - 1 - lvl[m];
            const float f = ox1 > ox0 ? (float)(d->want_ox[m] - ox0) / (float)(ox1 - ox0) : 0.5f;
            const int target = (int)((0.25f + 0.5f * f) * UNITS);
            int best = -1;
            for (int c = 1; c + 1 < UNITS; c++) {
                bool ok = true;
                for (int x = c * U; x < (c + 1) * U && ok; x++)
                    ok = d->tree_b[t][x] == d->tree_b[t][c * U] && ter_depth(d, t, x) >= 48;
                for (const TerWay& o : w) ok = ok && !(o.tier == t && abs(o.x - (c * U + 32)) < 2 * U);
                if (ok && (best < 0 || abs(c - target) < abs(best - target))) best = c;
            }
            if (best < 0) return false;
            w.push_back({ t, best * U + 32 });
        }
        return true;
    };
    std::vector<TerWay> ways;
    for (int attempt = 0; ; attempt++) {
        const bool level = attempt >= 12;              // past any luck: level floors the whole width, which always join
        for (int t = 0; t <= N; t++) {
            end0[t] = (t == N || level) ? 0 : 4 + rnd(3);
            end1[t] = (t == N || level) ? UNITS : UNITS - 4 - rnd(3);
            int cur = rnd(3) - 1;
            for (int i = 0; i < UNITS; i++) {
                if (i > 0 && rnd(100) < 35) cur = std::max(-1, std::min(1, cur + (rnd(2) ? 1 : -1)));
                offs[t][i] = (int8_t)(level ? 0 : cur);
            }
        }
        if (terraces_join(d, rng, N, W, 48, back, pick, ways)) break;
    }

    // every mouth its own way out: the floor tile before its arch, which stands
    // two tiles wide on the back wall
    d->num_portals = 0;
    for (int m = 0; m < want; m++) {
        int tx = (d->tree_ox + ways[m].x - 16) / 16, ty = (d->tree_oy + d->tree_b[ways[m].tier][ways[m].x]) / 16;
        d->portals[d->num_portals++] = { tx, ty, -1, -1 };
    }
    terraces_tiles(d, d->portals[0].tx, d->portals[0].ty);
    d->entry_x = d->portals[0].tx; d->entry_y = d->portals[0].ty;
    d->exit_x  = d->portals[1].tx; d->exit_y  = d->portals[1].ty;
    for (int p = 0; p < d->num_portals; p++)
        d->tiles[d->portals[p].ty][d->portals[p].tx] = p ? DNG_EXIT : DNG_ENTRY;
}

// The crystals to mine: each a tile of a floor's open middle -- floor all
// round it, so none shuts a way -- marked in art[][] (a cave draws no tile
// art) and solid until mined (tile_solid). Clear of the mouths and ladders.
static void place_cave_nodes(DungeonMap* d, uint32_t* rng) {
    auto rnd = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    auto open = [&](int tx, int ty) {
        for (int j = -1; j <= 1; j++)
            for (int i = -1; i <= 1; i++)
                if (d->tiles[ty + j][tx + i] != DNG_FLOOR) return false;
        return true;
    };
    int want = 6 + rnd(5);
    for (int tries = 0; want > 0 && tries < 4000; tries++) {
        int tx = d->tree_ox / 16 + rnd(d->tree_w / 16), ty = d->tree_oy / 16 + rnd(d->tree_h / 16);
        if (tx < 1 || ty < 1 || tx >= DMAP_W - 1 || ty >= DMAP_H - 1 || !open(tx, ty)) continue;
        bool near = false;
        for (int p = 0; p < d->num_portals; p++)
            near = near || (abs(tx - d->portals[p].tx) < 4 && abs(ty - d->portals[p].ty) < 4);
        for (int i = 0; i < d->num_tree_ladders; i++) {
            const auto& l = d->tree_ladders[i];
            int lx = (d->tree_ox + l.x0) / 16, ly0 = (d->tree_oy + l.y0) / 16, ly1 = (d->tree_oy + l.y1) / 16;
            near = near || (abs(tx - lx) < 3 && ty >= ly0 - 3 && ty <= ly1 + 3);
        }
        if (near) continue;
        d->tiles[ty][tx] = DNG_WALL;
        d->art[ty][tx]   = 1;
        resource_nodes_add(&d->dungeon_rocks, RESOURCE_ROCK, (float)(tx * DMAP_TILE), (float)(ty * DMAP_TILE));
        want--;
    }
}

// ── Spawner placement ─────────────────────────────────────────────────────

static int spawner_enemy_base(DungeonEntranceType type) {
    // Returns base enemy ID for each dungeon type, reflecting the overworld
    // biome in which that dungeon entrance is found.
    // Grassland 0–6 | Forest 7–13 | Snow 14–20 | Desert 21–27
    // Wasteland 28–34 | Mountains 35–41 | Ocean 42–49
    switch (type) {
        case DUNGEON_ENT_CAVE:         return 35; // mountains
        case DUNGEON_ENT_RUINS:        return 28; // wasteland
        case DUNGEON_ENT_GRAVEYARD_SM: return  0; // grassland
        case DUNGEON_ENT_GRAVEYARD_LG: return  7; // forest
        case DUNGEON_ENT_OASIS:        return 21; // desert
        case DUNGEON_ENT_PYRAMID:      return 21; // desert
        case DUNGEON_ENT_STONEHENGE:   return 14; // snow
        case DUNGEON_ENT_LARGE_TREE:   return  7; // forest
        // The graveyard family already climbs this ladder rather than matching
        // where it is placed -- SM takes grassland, LG takes forest although it
        // spawns on flat ground and snow. Catacombs continues that by one rung.
        case DUNGEON_ENT_CATACOMBS:    return 14; // snow
        default:                       return  0;
    }
}

// How much of the spawner/loot arrays one dungeon may fill. Catacombs is the
// only archetype with the floor area to justify the extra room; see the note on
// DMAP_MAX_SPAWNERS in dungeon.h for why this is not simply the array size.
static inline int dng_spawner_budget(DungeonEntranceType type) {
    return (type == DUNGEON_ENT_CATACOMBS) ? DMAP_MAX_SPAWNERS : DNG_SPAWNER_BUDGET;
}
static inline int dng_loot_budget(DungeonEntranceType type) {
    return (type == DUNGEON_ENT_CATACOMBS) ? DMAP_MAX_LOOT : DNG_LOOT_BUDGET;
}

// Spread spawners across all floor tiles using a regular grid + local floor search.
// Spawner tiles are never visible when placed, so they only activate in darkness.
// A starting-island dungeon (dmap->starter) holds the island's own enemies,
// all three of them: the first three spawners are these, Treesqueak first --
// the vine for the raft has to be findable -- and any more are drawn from them.
static const int STARTER_ENEMIES[] = { 2, 0, 1 };
static const int STARTER_COUNT = (int)(sizeof(STARTER_ENEMIES) / sizeof(STARTER_ENEMIES[0]));

// Difficulty -> tier band. The cuts are QUANTILES of the dungeons' measured
// difficulty (tools/spawncensus.cpp prints them), so each of the five common
// tiers gets about a fifth of the world's dungeons: LOW nearest and lowest,
// SEVERE farthest and highest. Re-measure if the world's difficulty formula
// (tilemap.cpp) changes.
static const float TIER_CUTS[4] = { 0.268f, 0.345f, 0.406f, 0.463f };   // q20 q40 q60 q80, 16 seeds
static const EnemyTier BAND_TIER[5] = { T_LOW, T_MEDIUM, T_UPPER, T_HARD, T_SEVERE };
// Elites join the pool in the hardest tenth (q90) -- and always in the ruins.
static const float ELITE_DIFFICULTY = 0.510f;

int dungeon_pick_enemy(DungeonEntranceType type, float difficulty, uint32_t* rng) {
    int band = 0;
    while (band < 4 && difficulty >= TIER_CUTS[band]) band++;
    EnemyTier tier = BAND_TIER[band], below = band > 0 ? BAND_TIER[band - 1] : T_STARTER;
    int base = spawner_enemy_base(type);
    bool elites = type == DUNGEON_ENT_RUINS || difficulty >= ELITE_DIFFICULTY;
    // Weighted pool: the band's tier, the region's own enemies weighing most;
    // the tier below now and then, so a dungeon isn't one tier wall to wall;
    // elites where they live.
    int pick[ENEMY_COUNT], weight[ENEMY_COUNT], n = 0, total = 0;
    for (int e = 0; e < ENEMY_COUNT; e++) {
        EnemyTier t = enemy_tier(e);
        bool native = enemy_region(e) == base / 7;
        int w = t == tier ? (native ? 4 : 2) : t == below ? 1 : (t == T_ELITE && elites) ? 2 : 0;
        if (w) { pick[n] = e; weight[n] = w; n++; total += w; }
    }
    int r = (int)(rng_next(rng) % (uint32_t)total);
    for (int i = 0; i < n; i++) if ((r -= weight[i]) < 0) return pick[i];
    return pick[n - 1];
}

static void place_spawners(DungeonMap* dmap, uint32_t* rng) {
    dmap->num_spawners = 0;
    const int STEP   = 24;   // grid spacing in tiles — guarantees spread
    const int SEARCH = 8;    // radius to search for a floor tile near each grid point
    // Only catacombs is allowed past the budget every other archetype has always
    // had, so every existing dungeon generates exactly as it did before.
    int budget = dng_spawner_budget(dmap->type);

    int ox = (int)(rng_next(rng) % STEP);
    int oy = (int)(rng_next(rng) % STEP);

    for (int gy = oy; gy < DMAP_H && dmap->num_spawners < budget; gy += STEP) {
        for (int gx = ox; gx < DMAP_W && dmap->num_spawners < budget; gx += STEP) {
            int best_tx = -1, best_ty = -1, best_d2 = SEARCH * SEARCH + 1;
            for (int dy = -SEARCH; dy <= SEARCH; dy++) {
                for (int dx = -SEARCH; dx <= SEARCH; dx++) {
                    int tx = gx + dx, ty = gy + dy;
                    if (tx < 1 || tx >= DMAP_W - 1 || ty < 1 || ty >= DMAP_H - 1) continue;
                    if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;
                    // Keep clear of every portal, not just the pair — a cave's
                    // extra mouths would otherwise have something waiting on
                    // them the moment you stepped out.
                    bool near_portal = false;
                    for (int q = 0; q < dmap->num_portals && !near_portal; q++) {
                        int pdx = tx - dmap->portals[q].tx;
                        int pdy = ty - dmap->portals[q].ty;
                        if (pdx*pdx + pdy*pdy < STEP*STEP) near_portal = true;
                    }
                    if (near_portal) continue;
                    int d2 = dx*dx + dy*dy;
                    if (d2 < best_d2) { best_d2 = d2; best_tx = tx; best_ty = ty; }
                }
            }
            if (best_tx < 0) continue;
            int eid = dungeon_pick_enemy(dmap->type, dmap->difficulty, rng);
            if (dmap->starter)
                eid = dmap->num_spawners < STARTER_COUNT ? STARTER_ENEMIES[dmap->num_spawners]
                    : STARTER_ENEMIES[rng_next(rng) % STARTER_COUNT];
            dmap->spawners[dmap->num_spawners++] = { best_tx, best_ty, eid, false };
        }
    }

    // A starting dungeon too small for the grid to seat all three gets the
    // rest on any floor tile clear of the portals and of the others, tried
    // from random spots so they spread out. Closer in than the grid allows --
    // the grid's clearance is what left no room -- but still a room's width.
    const int FILL_PORTAL_CLEAR = 10, FILL_SPAWNER_CLEAR = 8;
    for (int tries = 0; dmap->starter && dmap->num_spawners < STARTER_COUNT && tries < 4000; tries++) {
        int tx = 1 + (int)(rng_next(rng) % (DMAP_W - 2));
        int ty = 1 + (int)(rng_next(rng) % (DMAP_H - 2));
        if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;
        bool clear = true;
        for (int q = 0; q < dmap->num_portals && clear; q++) {
            int pdx = tx - dmap->portals[q].tx, pdy = ty - dmap->portals[q].ty;
            if (pdx*pdx + pdy*pdy < FILL_PORTAL_CLEAR * FILL_PORTAL_CLEAR) clear = false;
        }
        for (int q = 0; q < dmap->num_spawners && clear; q++) {
            int sdx = tx - dmap->spawners[q].tx, sdy = ty - dmap->spawners[q].ty;
            if (sdx*sdx + sdy*sdy < FILL_SPAWNER_CLEAR * FILL_SPAWNER_CLEAR) clear = false;
        }
        if (!clear) continue;
        dmap->spawners[dmap->num_spawners] = { tx, ty, STARTER_ENEMIES[dmap->num_spawners], false };
        dmap->num_spawners++;
    }
}

// ── Loot placement ─────────────────────────────────────────────────────────

// True if (tx,ty) sits in open room interior — not a corridor pinch or a
// pocket walled on multiple sides. Requires all 8 neighbors but at most one
// to be non-wall.
static bool tile_open_interior(const DungeonMap* dmap, int tx, int ty) {
    int open = 0;
    for (int ny = ty - 1; ny <= ty + 1; ny++)
        for (int nx = tx - 1; nx <= tx + 1; nx++) {
            if (nx == tx && ny == ty) continue;
            if (nx < 0 || nx >= DMAP_W || ny < 0 || ny >= DMAP_H) continue;
            if (dmap->tiles[ny][nx] != DNG_WALL) open++;
        }
    return open >= 6;
}

static bool tile_in_the_open(const DungeonMap* dmap, int tx, int ty);   // beside tile_solid

// Spread loot across floor tiles using the same grid + local-search shape as
// place_spawners, but biased away from the entrance and away from dead ends /
// wall-hugging pockets, so it rewards exploring the dungeon's open rooms.
// One loot tile: a gold square, or a treasure as its icon (assets/items.png,
// the menu's own picture). Out of view either is a dim square -- the dark
// keeps what it is to itself.
static void draw_loot(SDL_Renderer* ren, const DungeonLoot& lo, int sx, int sy, int tsz) {
    static SDL_Texture* icons = nullptr;
    static bool tried = false;
    if (!tried) { tried = true; icons = IMG_LoadTexture(ren, "assets/items.png"); }
    if (lo.item >= 0 && icons) {
        SDL_Rect src = { lo.item * 16, 0, 16, 16 }, dst = { sx, sy, tsz, tsz };
        SDL_RenderCopy(ren, icons, &src, &dst);
        return;
    }
    int pad = tsz / 4;
    SDL_Rect loot_rect = { sx + pad, sy + pad, tsz - 2*pad, tsz - 2*pad };
    fc_draw_color(ren, 255, 215, 60, 255);
    SDL_RenderFillRect(ren, &loot_rect);
}

int dungeon_treasure_item(DungeonEntranceType type) {
    switch (type) {
        case DUNGEON_ENT_RUINS:      return ITEM_OLD_SPEARHEAD;
        case DUNGEON_ENT_STONEHENGE: return ITEM_MOON_STEEL;
        case DUNGEON_ENT_CATACOMBS:  return ITEM_REAPERS_EDGE;
        default:                     return -1;
    }
}

// A dungeon's one treasure, if its kind keeps one (every dungeon of the kind
// has it until one is found): on the floor tile farthest from the way in --
// the end of the dungeon is where it is earned -- that nothing is drawn over
// (tile_in_the_open; the user: never behind a wall that hides it), in open
// room if there is one.
static void place_treasure(DungeonMap* dmap) {
    int item = dungeon_treasure_item(dmap->type);
    if (item < 0) return;
    struct Cand { int tx, ty, d2; };
    std::vector<Cand> cands;
    for (int ty = 1; ty < DMAP_H - 1; ty++)
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;
            bool taken = false;
            for (int li = 0; li < dmap->num_loot && !taken; li++)
                taken = dmap->loot[li].tx == tx && dmap->loot[li].ty == ty;
            if (taken) continue;
            int dex = tx - dmap->entry_x, dey = ty - dmap->entry_y;
            cands.push_back({ tx, ty, dex*dex + dey*dey });
        }
    std::sort(cands.begin(), cands.end(), [](const Cand& a, const Cand& b) { return a.d2 > b.d2; });
    // farthest first; the pixel test runs only until one tile passes
    const Cand* pick = nullptr;
    for (int pass = 0; pass < 3 && !pick; pass++)   // open room and uncovered; uncovered; any floor
        for (const Cand& c : cands) {
            if (pass == 0 && !tile_open_interior(dmap, c.tx, c.ty)) continue;
            if (pass < 2 && !tile_in_the_open(dmap, c.tx, c.ty)) continue;
            pick = &c; break;
        }
    if (!pick) return;
    // Room is always made for it: a full list gives up its last gold pile.
    int slot = dmap->num_loot < DMAP_MAX_LOOT ? dmap->num_loot++ : DMAP_MAX_LOOT - 1;
    dmap->loot[slot] = { pick->tx, pick->ty, 0, false, item };
}

static void place_loot(DungeonMap* dmap, uint32_t* rng) {
    dmap->num_loot = 0;
    const int STEP   = 48;   // sparser than spawners
    const int SEARCH = 10;

    // Entry-clear radius scales with how far this dungeon's floor actually
    // reaches from the entrance, so compact layouts (e.g. the large tree's
    // 64x64 trunk) still get loot placed instead of clearing the whole map.
    long max_d2 = 0;
    for (int ty = 1; ty < DMAP_H - 1; ty++)
        for (int tx = 1; tx < DMAP_W - 1; tx++) {
            if (dmap->tiles[ty][tx] == DNG_WALL) continue;
            long dex = tx - dmap->entry_x, dey = ty - dmap->entry_y;
            long d2 = dex*dex + dey*dey;
            if (d2 > max_d2) max_d2 = d2;
        }
    int entry_clear = (int)(sqrtf((float)max_d2) * 0.35f);
    if (entry_clear < 6)  entry_clear = 6;
    if (entry_clear > 40) entry_clear = 40;

    int ox = (int)(rng_next(rng) % STEP);
    int oy = (int)(rng_next(rng) % STEP);

    int budget = dng_loot_budget(dmap->type);
    for (int gy = oy; gy < DMAP_H && dmap->num_loot < budget; gy += STEP) {
        for (int gx = ox; gx < DMAP_W && dmap->num_loot < budget; gx += STEP) {
            int best_tx = -1, best_ty = -1, best_d2 = SEARCH * SEARCH + 1;
            for (int dy = -SEARCH; dy <= SEARCH; dy++) {
                for (int dx = -SEARCH; dx <= SEARCH; dx++) {
                    int tx = gx + dx, ty = gy + dy;
                    if (tx < 1 || tx >= DMAP_W - 1 || ty < 1 || ty >= DMAP_H - 1) continue;
                    if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;

                    int dex = tx - dmap->entry_x, dey = ty - dmap->entry_y;
                    if (dex*dex + dey*dey < entry_clear*entry_clear) continue;

                    if (!tile_open_interior(dmap, tx, ty)) continue;

                    int d2 = dx*dx + dy*dy;
                    if (d2 < best_d2) { best_d2 = d2; best_tx = tx; best_ty = ty; }
                }
            }
            if (best_tx < 0) continue;
            int gold = 10 + (int)(rng_next(rng) % 21) + (int)(dmap->difficulty * 15.0f);
            dmap->loot[dmap->num_loot++] = { best_tx, best_ty, gold, false };
        }
    }

    // Fallback for tiny/cramped layouts where the grid search above found no
    // candidate passing every filter — guarantee at least one loot item.
    // Tier 1: farthest floor tile from the entrance that's still open
    // interior (keeps the dead-end/wall-hugging rule). Tier 2: if the
    // dungeon has no open-interior tile at all, fall back to any floor tile.
    if (dmap->num_loot == 0) {
        int best_tx = -1, best_ty = -1, best_d2 = -1;
        for (int ty = 1; ty < DMAP_H - 1; ty++) {
            for (int tx = 1; tx < DMAP_W - 1; tx++) {
                if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;
                if (!tile_open_interior(dmap, tx, ty)) continue;
                int dex = tx - dmap->entry_x, dey = ty - dmap->entry_y;
                int d2 = dex*dex + dey*dey;
                if (d2 > best_d2) { best_d2 = d2; best_tx = tx; best_ty = ty; }
            }
        }
        if (best_tx < 0) {
            for (int ty = 1; ty < DMAP_H - 1; ty++) {
                for (int tx = 1; tx < DMAP_W - 1; tx++) {
                    if (dmap->tiles[ty][tx] != DNG_FLOOR) continue;
                    int dex = tx - dmap->entry_x, dey = ty - dmap->entry_y;
                    int d2 = dex*dex + dey*dey;
                    if (d2 > best_d2) { best_d2 = d2; best_tx = tx; best_ty = ty; }
                }
            }
        }
        if (best_tx >= 0) {
            int gold = 10 + (int)(rng_next(rng) % 21) + (int)(dmap->difficulty * 15.0f);
            dmap->loot[dmap->num_loot++] = { best_tx, best_ty, gold, false };
        }
    }

    place_treasure(dmap);
}

// ── Public: generate ──────────────────────────────────────────────────────
// A network of walkways walked in world tiles along the world's axes -- the
// graveyard's, and the catacombs' sections (wider, longer, further apart): a
// trunk set off east from (x0, tv/2), then branches leaving it north or south.
// A run turns 90 degrees, never back against its heading, never within
// `clear` tiles of where the path has been (the two runs before it excepted:
// the heading keeps those from folding back), `margin` tiles inside the world.
struct WalkNet {
    int tw, tv, nlines, x0;
    int trunk_segs, trunk_min;            // the trunk's runs, and how many it must make
    int run_min, run_span;                // a run's length: run_min + rr(run_span)
    int set_min, set_span;                // the trunk's first run (it clears its landing)
    int margin, clear, branch_clear;      // inside the world; from the path; from a branch's root
    int branch_min, branch_span;          // a branch's runs
};
typedef std::vector<std::pair<int, int>> WalkCells;
struct WalkLine { WalkCells pts; int parent, at, last; };
static std::vector<WalkLine> walk_net(uint32_t* rng, const WalkNet& P) {
    typedef WalkCells Cells;
    const int TW = P.tw, TV = P.tv;
    const int DX[4] = {1, 0, -1, 0}, DY[4] = {0, 1, 0, -1};   // east, back, west, front
    auto rr = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    auto near = [](const Cells& a, size_t n, int x, int y, int r) {
        for (size_t i = 0; i < n; i++)
            if (abs(a[i].first - x) <= r && abs(a[i].second - y) <= r) return true;
        return false;
    };
    // first: the first run's direction, or -1 for any; *last: the last run's
    auto walk = [&](int x, int y, int dir, int nseg, const Cells& taken, int heading, int first,
                    Cells* out, int* last) {
        Cells pts{{x, y}}, mine;
        std::vector<size_t> runs{0, 0};
        for (int s = 0; s < nseg; s++) {
            static const int TURN[5] = {1, -1, 1, -1, 0};
            bool ok = false;
            int nd = 0, ln = 0;
            Cells cells;
            for (int t = 0; t < 16 && !ok; t++) {
                nd = s == 0 && first >= 0 ? first : (dir + TURN[rr(5)] + 4) % 4;
                if ((nd - heading + 4) % 4 == 2) continue;
                ln = s == 0 && first >= 0 ? P.set_min + rr(P.set_span) : P.run_min + rr(P.run_span);
                cells.clear();
                bool fits = true;
                for (int i = 1; i <= ln && fits; i++) {
                    int cx = x + DX[nd] * i, cy = y + DY[nd] * i;
                    fits = cx >= P.margin && cx < TW - P.margin && cy >= P.margin && cy < TV - P.margin;
                    cells.push_back({cx, cy});
                }
                if (!fits) continue;
                ok = true;
                for (auto& c : cells)
                    if (near(taken, taken.size(), c.first, c.second, P.clear) ||
                        near(mine, runs[runs.size() - 2], c.first, c.second, P.clear)) { ok = false; break; }
            }
            if (!ok) break;
            runs.push_back(mine.size());
            mine.insert(mine.end(), cells.begin(), cells.end());
            x += DX[nd] * ln; y += DY[nd] * ln; dir = nd;
            pts.push_back({x, y});
        }
        if (out) *out = mine;
        if (last) *last = dir;
        return pts;
    };
    std::vector<WalkLine> lines;
    Cells taken;
    for (int tries = 0; tries < 200; tries++) {                // a trunk that crosses the map
        Cells mine;
        int last;
        Cells trunk = walk(P.x0, TV / 2, 0, P.trunk_segs, Cells(), 0, 0, &mine, &last);
        if ((int)trunk.size() >= P.trunk_min || tries == 199) { lines.push_back({trunk, -1, 0, last}); taken = mine; break; }
    }
    for (int t = 0; t < 20 && (int)lines.size() < P.nlines; t++) {
        int li = rr((int)lines.size());
        if (lines[li].pts.size() < 4) continue;
        int k = 1 + rr((int)lines[li].pts.size() - 2);
        auto root = lines[li].pts[k];
        int hd = rr(2) ? 1 : 3;
        Cells near_root;                                 // the path but where the branch leaves it --
        for (auto& c : taken)                            // and never a landing, whatever its distance
            if (abs(c.first - root.first) > P.branch_clear || abs(c.second - root.second) > P.branch_clear) near_root.push_back(c);
        near_root.push_back(lines[0].pts.front());
        for (auto& l : lines) near_root.push_back(l.pts.back());
        Cells cells;
        int last;
        Cells br = walk(root.first, root.second, hd, P.branch_min + rr(P.branch_span), near_root, hd, -1, &cells, &last);
        if (br.size() > 2) {
            lines.push_back({br, li, k, last});
            taken.insert(taken.end(), cells.begin(), cells.end());
        }
    }
    return lines;
}

// ── Graveyard: walkways floating in the dark ─────────────────────────────
// One long path that splits (user), its runs 3-7 tiles, never within 5 tiles
// of where it has been (walk_net), so under the oblique view every edge lies
// flat or climbs at 45 degrees with the bricks and planks on it. Each run is a
// rectangle 2-3 tiles wide, each end a 4 x 4 landing. The way in is the
// trunk's start, the far end the landing furthest from it. The picture is
// composited from these when first drawn (graveyard_bake).
static void carve_graveyard_walkways(DungeonMap* d, uint32_t* rng, bool large) {
    typedef WalkCells Cells;
    const int TW = large ? 140 : 96, TV = large ? 56 : 40;
    auto rr = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    // A way out's wall stands across the back of its landing, so the path may
    // not pass through there: the trunk sets off east, and the far way out is
    // an end the path does not come down into from behind.
    const WalkNet NET = { TW, TV, large ? 10 : 6, 4, large ? 36 : 24, large ? 24 : 16,
                          3, 5, 5, 3, 3, 5, 6, 4, 5 };
    std::vector<WalkLine> lines = walk_net(rng, NET);

    // the rectangles, the segments and their distances along, the ends
    d->num_gyw_rects = d->num_gyw_segs = 0;
    auto rect = [&](int x0, int y0, int x1, int y1) {
        if (d->num_gyw_rects < DMAP_MAX_GYW_RECTS)
            d->gyw_rects[d->num_gyw_rects++] = { (int16_t)(x0 * 16), (int16_t)(y0 * 16),
                                                 (int16_t)(x1 * 16 + 15), (int16_t)(y1 * 16 + 15) };
    };
    std::vector<std::vector<float>> varc(lines.size());
    Cells ends;
    std::vector<bool> from_behind;                       // an end the path comes down into from the back
    float total = 0;
    for (size_t li = 0; li < lines.size(); li++) {
        const Cells& pts = lines[li].pts;
        float acc = lines[li].parent < 0 ? 0.0f : varc[lines[li].parent][lines[li].at];
        int w = 2 + rr(2);
        varc[li].push_back(acc);
        for (size_t i = 0; i + 1 < pts.size(); i++) {
            int ax = pts[i].first, ay = pts[i].second, bx = pts[i + 1].first, by = pts[i + 1].second;
            int x0 = std::min(ax, bx), x1 = std::max(ax, bx), y0 = std::min(ay, by), y1 = std::max(ay, by);
            if (ax == bx) { x0 = ax - (w - 1) / 2; x1 = ax + w / 2; }
            else          { y0 = ay - (w - 1) / 2; y1 = ay + w / 2; }
            rect(x0, y0, x1, y1);
            if (d->num_gyw_segs < DMAP_MAX_GYW_SEGS)
                d->gyw_segs[d->num_gyw_segs++] = { (int16_t)(ax * 16 + 8), (int16_t)(ay * 16 + 8),
                                                   (int16_t)(bx * 16 + 8), (int16_t)(by * 16 + 8), acc };
            acc += 16.0f * (abs(bx - ax) + abs(by - ay));
            varc[li].push_back(acc);
        }
        total = std::max(total, acc);
        if (li == 0) { ends.push_back(pts.front()); from_behind.push_back(false); }
        ends.push_back(pts.back());
        from_behind.push_back(lines[li].last == 3);
    }
    for (auto& e : ends) rect(e.first - 1, e.second - 1, e.first + 2, e.second + 2);   // the landings
    d->gyw_total = total;
    int far = -1;
    auto dist2 = [&](int i) { int a = ends[i].first - ends[0].first, b = ends[i].second - ends[0].second; return a * a + b * b; };
    for (int i = 1; i < (int)ends.size(); i++)
        if (!from_behind[i] && (far < 0 || dist2(i) > dist2(far))) far = i;
    if (far < 0) far = 1;   // ponytail: every end entered from behind -- none seen; the wall would then block it
    d->gyw_way_u[0] = ends[0].first;   d->gyw_way_v[0] = ends[0].second;
    d->gyw_way_u[1] = ends[far].first; d->gyw_way_v[1] = ends[far].second;
    d->gyw_seed = rng_next(rng) * 2654435761u ^ rng_next(rng);

    // on the map: the world's back edge 8 tiles down, its west edge 8 across
    d->gyw_ox = 8 * 16; d->gyw_oy = 8 * 16 + TV * 16 - 1;
    d->gyw_x0 = d->gyw_ox; d->gyw_y0 = 8 * 16 - 64;          // room above for the walls
    d->gyw_w = (TW + TV) * 16 + 16; d->gyw_h = TV * 16 + 64 + GYW_FOOT + 24 + 16;
    for (int ty = d->gyw_y0 / 16; ty < (d->gyw_y0 + d->gyw_h) / 16 && ty < DMAP_H; ty++)
        for (int tx = d->gyw_x0 / 16; tx < (d->gyw_x0 + d->gyw_w) / 16 && tx < DMAP_W; tx++)
            if (gyw_on_path(d, tx * 16 + 8, ty * 16 + 8, false)) d->tiles[ty][tx] = DNG_FLOOR;
    gyw_way_tile(d, 0, &d->entry_x, &d->entry_y);
    gyw_way_tile(d, 1, &d->exit_x, &d->exit_y);
    d->tiles[d->entry_y][d->entry_x] = DNG_ENTRY;
    d->tiles[d->exit_y][d->exit_x]   = DNG_EXIT;
}

// ── Catacombs: the hall and the sections below, in isometric ─────────────
// 2:1 isometric (user): a world pixel (u, v) of an area drawn at art pixel
// (ox + u - v, oy + (u + v) / 2) -- one screen pixel each, no gaps -- z
// straight up; the nearer of two is the one with the larger u + v. Walls stand
// all round the floor, CAT_T thick (a square round each pixel, so they meet at
// every corner), full height. The ways -- the hall's doors and windows, a
// section's ladder -- are each on a wall the view sees face on: cut across a
// back corner of the floor (u0, v0), K in from it, one wall thick, and
// everything behind it gone. A hole in the hall's floor leads down to its
// section's ladder, the ladder back up beside it. The picture is baked an area
// at a time (cat_bake); the player walks it on the screen, their feet taken
// back into the world (cat_floor).
enum { CAT_WINDOW, CAT_DOOR, CAT_LADDER };
static const int CAT_T = 8, CAT_PAD = 32;
static int cat_z(int area) { return area ? 48 : 80; }              // a section's walls, the hall's
static const int CAT_TC = 11;                                       // a face-on wall's thickness in u + v: round(T * sqrt 2)

static int cat_area_at(const DungeonMap* d, float ax, float ay) {
    for (int a = 0; a < d->num_cat_areas; a++) {
        const auto& A = d->cat_areas[a];
        if (ax >= A.x0 && ax < A.x1 && ay >= A.y0 && ay < A.y1) return a;
    }
    return -1;
}
static void cat_world(const DungeonMap* d, int a, float ax, float ay, float* u, float* v) {
    float x = ax - d->cat_areas[a].ox, y = ay - d->cat_areas[a].oy;     // x = u - v, y = (u + v) / 2
    *u = y + x / 2; *v = y - x / 2;
}
static void cat_screen(const DungeonMap* d, int a, float u, float v, float* ax, float* ay) {
    *ax = d->cat_areas[a].ox + u - v; *ay = d->cat_areas[a].oy + (u + v) / 2;
}
// Whether world (u, v) of area a is floor: in a rectangle, and not a cut's.
static bool cat_floor(const DungeonMap* d, int a, float u, float v) {
    bool on = false;
    for (int i = d->cat_areas[a].r0; i < d->cat_areas[a].r1 && !on; i++) {
        const auto& r = d->cat_rects[i];
        on = u >= r.u0 && u < r.u1 && v >= r.v0 && v < r.v1;
    }
    for (int i = 0; i < d->num_cat_cuts && on; i++) {
        const auto& c = d->cat_cuts[i];
        on = !(c.area == a && u >= c.u0 - CAT_T - 2 && u <= c.u0 + c.k && v >= c.v0 - CAT_T - 2 &&
               v <= c.v0 + c.k && u + v < c.u0 + c.v0 + c.k);
    }
    return on;
}
// Art pixel (ax, ay) walkable: in an area, its floor.
static bool cat_walkable(const DungeonMap* d, float ax, float ay) {
    int a = cat_area_at(d, ax, ay);
    if (a < 0) return false;
    float u, v;
    cat_world(d, a, ax, ay, &u, &v);
    return cat_floor(d, a, u, v);
}

static void carve_catacombs(DungeonMap* d, uint32_t* rng) {
    auto rr = [&](int n) { return (int)(rng_next(rng) % (uint32_t)n); };
    const int T = CAT_T, P = CAT_PAD;
    struct Rect { int u0, v0, u1, v1; };
    struct Cut { int kind, u0, v0, k; };
    struct Area { std::vector<Rect> rects; std::vector<Cut> cuts; };
    std::vector<Area> areas(1);
    auto floor_in = [](const Area& A, int u, int v) {
        for (const Rect& r : A.rects)
            if (u >= r.u0 && u < r.u1 && v >= r.v0 && v < r.v1) return true;
        return false;
    };

    // The hall (user): a zig-zag hallway, runs along +u and back along -v in
    // turn, stepping up the screen to the right -- so the top-left of every run
    // along u is a back corner, cut face on, a window in each (every one one
    // size), the church's door, the only way in or out, at the right end: the
    // catacombs never link to another dungeon (user).
    const int WC = 224, L = 224, N = 11, KW = (64 + 12) / 2, KD = 16;
    {
        Area& H = areas[0];
        int u = P, v = P + (N / 2) * L;
        for (int i = 0; i < N; i++) {
            if (i % 2 == 0) { H.rects.push_back({ u, v, u + L + WC, v + WC }); u += L; }
            else            { H.rects.push_back({ u, v - L, u + WC, v + WC }); v -= L; }
        }
        for (int i = 0; i < N; i += 2) {
            bool right = i == N - 1;
            H.cuts.push_back({ right ? CAT_DOOR : CAT_WINDOW, H.rects[i].u0, H.rects[i].v0, right ? KD : KW });
        }
    }

    // The sections (user): the graveyard's walkways (walk_net), wider, longer,
    // further apart, walled in bone all round; one ladder up, on the true back
    // corner -- floor with none behind it either way, nor within 3T behind --
    // nearest the trunk's start.
    const WalkNet NET = { 200, 112, 6, 10, 24, 8, 6, 7, 6, 7, 9, 14, 16, 4, 5 };
    int nsec = 3 + rr(3);
    for (int s = 0; s < nsec; s++) {
        std::vector<WalkLine> lines = walk_net(rng, NET);
        Area A;
        auto rect = [&](int x0, int y0, int x1, int y1) { A.rects.push_back({ x0 * 16 + P, y0 * 16 + P, (x1 + 1) * 16 + P, (y1 + 1) * 16 + P }); };
        for (const WalkLine& l : lines) {
            int w = 8 + rr(2);
            for (size_t i = 0; i + 1 < l.pts.size(); i++) {
                int ax = l.pts[i].first, ay = l.pts[i].second, bx = l.pts[i + 1].first, by = l.pts[i + 1].second;
                int x0 = std::min(ax, bx), x1 = std::max(ax, bx), y0 = std::min(ay, by), y1 = std::max(ay, by);
                if (ax == bx) { x0 = ax - (w - 1) / 2; x1 = ax + w / 2; }
                else          { y0 = ay - (w - 1) / 2; y1 = ay + w / 2; }
                rect(x0, y0, x1, y1);
            }
        }
        std::vector<std::pair<int, int>> ends{ lines[0].pts.front() };
        for (const WalkLine& l : lines) ends.push_back(l.pts.back());
        for (auto& e : ends) rect(e.first - 4, e.second - 4, e.first + 5, e.second + 5);   // the landings
        const int K = 32;
        int cu = (ends[0].first + 1) * 16 + P, cv = (ends[0].second + 1) * 16 + P;
        auto behind_clear = [&](int u, int v) {
            for (int y = v - 3 * T; y < v + K + 1; y++)
                for (int x = u - 3 * T; x < (y < v ? u + K + 1 : u); x++)
                    if (floor_in(A, x, y)) return false;
            return true;
        };
        long best = -1;
        int bu = 0, bv = 0;
        for (int pass = 0; pass < 2 && best < 0; pass++)         // a true back corner; failing one, any
            for (const Rect& r : A.rects) {
                int u = r.u0, v = r.v0;                          // a back corner is a rectangle's top-left
                if (floor_in(A, u - 1, v) || floor_in(A, u, v - 1) || !floor_in(A, u + K, v + K)) continue;
                if (pass == 0 && !behind_clear(u, v)) continue;
                long dd = (long)(u - cu) * (u - cu) + (long)(v - cv) * (v - cv);
                if (best < 0 || dd < best) { best = dd; bu = u; bv = v; }
            }
        A.cuts.push_back({ CAT_LADDER, bu, bv, K });
        areas.push_back(A);
    }

    // Packed onto the map in rows, each in the box its walls fill; a section
    // with no room left is not dug.
    const int MW = DMAP_W * 16, MH = DMAP_H * 16, M = 64;
    int px = M, py = M, shelf = 0;
    d->num_cat_areas = d->num_cat_rects = d->num_cat_cuts = d->num_cat_holes = 0;
    for (size_t a = 0; a < areas.size() && d->num_cat_areas < CAT_MAX_AREAS; a++) {
        const Area& A = areas[a];
        int xmin = 1 << 30, xmax = -(1 << 30), ymin = 1 << 30, ymax = -(1 << 30);
        for (const Rect& r : A.rects)
            for (int u : { r.u0 - T - 2, r.u1 + T + 2 })
                for (int v : { r.v0 - T - 2, r.v1 + T + 2 }) {
                    xmin = std::min(xmin, u - v); xmax = std::max(xmax, u - v);
                    ymin = std::min(ymin, (u + v) / 2); ymax = std::max(ymax, (u + v) / 2);
                }
        ymin -= cat_z(d->num_cat_areas) + 2;
        int w = xmax - xmin, h = ymax - ymin;
        if (px + w > MW - M) { px = M; py += shelf + M; shelf = 0; }
        if (py + h > MH - M || d->num_cat_rects + (int)A.rects.size() > CAT_MAX_RECTS) continue;
        int n = d->num_cat_areas++;
        auto& D = d->cat_areas[n];
        D = { (int16_t)(px - xmin), (int16_t)(py - ymin), (int16_t)px, (int16_t)py, (int16_t)(px + w), (int16_t)(py + h),
              (int16_t)d->num_cat_rects, 0 };
        for (const Rect& r : A.rects)
            d->cat_rects[d->num_cat_rects++] = { (int16_t)r.u0, (int16_t)r.v0, (int16_t)r.u1, (int16_t)r.v1 };
        D.r1 = (int16_t)d->num_cat_rects;
        for (const Cut& c : A.cuts)
            if (d->num_cat_cuts < CAT_MAX_CUTS)
                d->cat_cuts[d->num_cat_cuts++] = { (uint8_t)n, (uint8_t)c.kind, (int16_t)c.u0, (int16_t)c.v0, (int16_t)c.k, -1, -1 };
        px += w + M; shelf = std::max(shelf, h);
    }

    // A hole down to each section, in the middle of a run of the hall's, no
    // two in one run; the sections numbered as their holes come along the
    // hall, left to right (user: Catacombs I, II, ...).
    std::vector<int> runs;
    for (int i = 1; i < N; i++) runs.push_back(i);
    for (int i = (int)runs.size() - 1; i > 0; i--) std::swap(runs[i], runs[rr(i + 1)]);
    runs.resize(std::min(runs.size(), (size_t)(d->num_cat_areas - 1)));
    std::sort(runs.begin(), runs.end());                 // a run further along lies further right
    for (int s = 1; s <= (int)runs.size(); s++) {
        const auto& r = d->cat_rects[runs[s - 1]];
        int ladder = 0;
        for (int i = 0; i < d->num_cat_cuts; i++)
            if (d->cat_cuts[i].area == s && d->cat_cuts[i].kind == CAT_LADDER) ladder = i;
        d->cat_holes[d->num_cat_holes++] = { (int16_t)((r.u0 + r.u1) / 2), (int16_t)((r.v0 + r.v1) / 2), (uint8_t)s, (uint8_t)ladder };
    }
    for (int a = 0; a < d->num_cat_areas; a++) {
        const auto& A = d->cat_areas[a];
        for (int ty = A.y0 / 16; ty <= A.y1 / 16 && ty < DMAP_H; ty++)
            for (int tx = A.x0 / 16; tx <= A.x1 / 16 && tx < DMAP_W; tx++)
                if (cat_walkable(d, tx * 16 + 8.0f, ty * 16 + 8.0f)) d->tiles[ty][tx] = DNG_FLOOR;
    }
    // the door's portal tile; the exit every layout names (bind_solo floors it
    // again) on the floor before the window at the left end
    for (int i = 0; i < d->num_cat_cuts; i++) {
        auto& c = d->cat_cuts[i];
        if (c.area != 0 || (c.kind != CAT_DOOR && i != 0)) continue;
        float ax, ay, m = c.k / 2.0f + 10;                      // 20 out from the face, on its middle
        cat_screen(d, c.area, c.u0 + m, c.v0 + m, &ax, &ay);
        c.tx = (int16_t)(ax / 16); c.ty = (int16_t)(ay / 16);
        if (c.kind == CAT_DOOR) { d->entry_x = c.tx; d->entry_y = c.ty; }
        else                    { d->exit_x = c.tx;  d->exit_y = c.ty; }
    }
    d->tiles[d->entry_y][d->entry_x] = DNG_ENTRY;
    d->tiles[d->exit_y][d->exit_x]   = DNG_EXIT;
    d->cat_seed = rng_next(rng) * 65536u + rng_next(rng);
}

static void generate_layout(DungeonMap* dmap, DungeonEntranceType type,
                            float difficulty, unsigned int seed) {
    memset(dmap->tiles,    DNG_WALL, sizeof(dmap->tiles));
    dmap->type       = type;
    memset(dmap->explored, dungeon_open_sight(dmap), sizeof(dmap->explored));
    memset(dmap->visible,  dungeon_open_sight(dmap), sizeof(dmap->visible));
    dmap->difficulty = difficulty;
    dmap->ore        = material_for_difficulty(difficulty);
    // The map is reused between visits, so the portal count has to be cleared
    // or the last dungeon's extra mouths survive into this one. want_portals is
    // set by the caller before it gets here and only a cave asks for more.
    dmap->num_portals = 0;
    memset(dmap->art,   0, sizeof(dmap->art));
    memset(dmap->art_p, 0, sizeof(dmap->art_p));
    dmap->num_decals = 0;
    dmap->num_pyr_rooms = 0;
    dmap->alt_entry_x = dmap->alt_entry_y = -1;
    if (dmap->want_portals < 2)                 dmap->want_portals = 2;
    if (dmap->want_portals > DMAP_MAX_PORTALS)  dmap->want_portals = DMAP_MAX_PORTALS;
    resource_nodes_init(&dmap->dungeon_rocks);

    uint32_t rng = seed ^ ((uint32_t)type * 0xBEEF1234u);

    // ── Cave: cellular automata + stalactite clusters ────────────────────
    if (type == DUNGEON_ENT_CAVE) {
        carve_cave_terraces(dmap, &rng);
        place_cave_nodes(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Giant tree: terraces in a triangle, ladders between ──────────────
    if (type == DUNGEON_ENT_LARGE_TREE) {
        carve_tree_terraces(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Stonehenge: the barrow, a block maze under a starry sky ──────────
    if (type == DUNGEON_ENT_STONEHENGE) {
        carve_stonehenge_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Pyramid: Mother 1 chambers along one passage ────────────────────
    if (type == DUNGEON_ENT_PYRAMID) {
        carve_pyramid_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Oasis: BSP + circular pool (corridors carved after pool) ─────────
    if (type == DUNGEON_ENT_OASIS) {
        carve_oasis(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Graveyards: walkways in the dark, one long path that splits ──────
    if (type == DUNGEON_ENT_GRAVEYARD_SM) {
        carve_graveyard_walkways(dmap, &rng, false);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    if (type == DUNGEON_ENT_GRAVEYARD_LG) {
        carve_graveyard_walkways(dmap, &rng, true);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Catacombs: the hall of windows, the sections below ───────────────
    if (type == DUNGEON_ENT_CATACOMBS) {
        carve_catacombs(dmap, &rng);
        clear_portal_surroundings(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── Ruins: Brogue-style room accretion ───────────────────────────────
    if (type == DUNGEON_ENT_RUINS) {
        carve_ruins_layout(dmap, &rng);
        clear_portal_surroundings(dmap);
        wall_rules(dmap);
        ruins_art(dmap);
        place_spawners(dmap, &rng);
        place_loot(dmap, &rng);
        return;
    }

    // ── BSP-based types ───────────────────────────────────────────────────
    s_bsp_max_depth = 4;
    s_bsp_min_part  = MIN_PART;

    s_bsp_n = 1;
    memset(s_bsp, 0, sizeof(s_bsp));
    s_bsp[0] = { 1, 1, DMAP_W - 2, DMAP_H - 2, -1, -1 };
    bsp_split(0, 0, &rng);

    s_leaf_n = 0;
    collect_leaves(0);

    // Carve rooms
    for (int i = 0; i < s_leaf_n; i++) {
        BSPNode* n = &s_bsp[s_leaves[i]];
        carve_rect(dmap, n->rx, n->ry, n->rw, n->rh, DNG_FLOOR);
    }

    // Connect consecutive rooms with corridors
    for (int i = 0; i + 1 < s_leaf_n; i++) {
        BSPNode* a = &s_bsp[s_leaves[i]];
        BSPNode* b = &s_bsp[s_leaves[i + 1]];
        carve_corridor(dmap, a->rcx, a->rcy, b->rcx, b->rcy);
    }

    // Entry in first room, exit in last room
    BSPNode* first = &s_bsp[s_leaves[0]];
    BSPNode* last  = &s_bsp[s_leaves[s_leaf_n - 1]];
    dmap->entry_x = first->rcx; dmap->entry_y = first->rcy;
    dmap->exit_x  = last->rcx;  dmap->exit_y  = last->rcy;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;

    clear_portal_surroundings(dmap);
    place_spawners(dmap, &rng);
    place_loot(dmap, &rng);
}

// ── The fog's regions ─────────────────────────────────────────────────────
// Sight goes by region, not by tile (user): a dungeon is found a room, a
// stretch of corridor, a floor at a time, each seen whole -- a tile ray
// against tiles drew stepped edges across the oblique walls and lit a wall in
// halves. Rooms are the open cores of the floor (five tiles across and more,
// eight-joined), each grown two tiles back to its walls; what is left -- the
// corridors, the narrows -- joins into stretches; scraps under six tiles go to
// a neighbour. The giant tree's regions are its floors, a ladder its foot's.
// A wall is seen with the floor it faces: the one below it in its column (a
// face stands on the floor south of it), else above, else beside.
static int tree_floor_at(const DungeonMap* d, int x, int y) {
    for (int i = 0; i < d->num_tree_floors; i++) {
        const auto& f = d->tree_floors[i];
        if (x >= f.x0 && x < f.x1 && y >= d->tree_b[f.t][x] && y < d->tree_b[f.t + 1][x] - d->tree_z) return i;
    }
    for (int i = 0; i < d->num_tree_ladders; i++) {
        const auto& l = d->tree_ladders[i];
        if (x >= l.x0 && x < l.x0 + 16 && y >= l.y0 && y < l.y1) return l.floor;
    }
    return -1;
}

static bool dng_walk(const DungeonMap* d, int x, int y) {
    if (x < 0 || y < 0 || x >= DMAP_W || y >= DMAP_H) return false;
    uint8_t t = d->tiles[y][x];
    return t == DNG_FLOOR || t == DNG_ENTRY || t == DNG_EXIT;
}

static void build_regions(DungeonMap* d) {
    memset(d->region, 0, sizeof d->region);
    d->num_regions = 0;
    d->num_lit = 0;
    if (dungeon_open_sight(d)) return;
    static int q[DMAP_W * DMAP_H];
    const int d4x[4] = { 1, -1, 0, 0 }, d4y[4] = { 0, 0, 1, -1 };
    auto fresh = [&]() { return (uint16_t)(d->num_regions < DMAP_MAX_REGIONS ? ++d->num_regions : DMAP_MAX_REGIONS); };
    if (terraced(d)) {
        d->num_regions = std::min(d->num_tree_floors, DMAP_MAX_REGIONS);
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++)
                if (dng_walk(d, x, y)) {
                    int f = tree_floor_at(d, x * 16 + 8 - d->tree_ox, y * 16 + 8 - d->tree_oy);
                    if (f >= 0 && f < DMAP_MAX_REGIONS) d->region[y][x] = (uint16_t)(f + 1);
                }
    } else {
        // how far each floor tile is from the nearest wall, eight ways
        static uint8_t dist[DMAP_H][DMAP_W];
        int h = 0, t = 0;
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) {
                bool w = dng_walk(d, x, y);
                dist[y][x] = w ? 255 : 0;
                if (!w) q[t++] = y * DMAP_W + x;
            }
        while (h < t) {
            int x = q[h] % DMAP_W, y = q[h] / DMAP_W; h++;
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++) {
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H || dist[ny][nx] != 255) continue;
                    dist[ny][nx] = (uint8_t)std::min(254, dist[y][x] + 1);
                    q[t++] = ny * DMAP_W + nx;
                }
        }
        const int CORE = 3;
        // the rooms' cores
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) {
                if (dist[y][x] < CORE || d->region[y][x]) continue;
                uint16_t r = fresh();
                h = t = 0; q[t++] = y * DMAP_W + x; d->region[y][x] = r;
                while (h < t) {
                    int cx = q[h] % DMAP_W, cy = q[h] / DMAP_W; h++;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int nx = cx + dx, ny = cy + dy;
                            if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H) continue;
                            if (dist[ny][nx] < CORE || d->region[ny][nx]) continue;
                            d->region[ny][nx] = r; q[t++] = ny * DMAP_W + nx;
                        }
                }
            }
        // grown back to their walls, CORE - 1 steps
        static uint8_t step[DMAP_H][DMAP_W];
        h = t = 0;
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++)
                if (d->region[y][x]) { step[y][x] = 0; q[t++] = y * DMAP_W + x; }
        while (h < t) {
            int x = q[h] % DMAP_W, y = q[h] / DMAP_W; h++;
            if (step[y][x] >= CORE - 1) continue;
            for (int k = 0; k < 4; k++) {
                int nx = x + d4x[k], ny = y + d4y[k];
                if (!dng_walk(d, nx, ny) || d->region[ny][nx]) continue;
                d->region[ny][nx] = d->region[y][x]; step[ny][nx] = step[y][x] + 1;
                q[t++] = ny * DMAP_W + nx;
            }
        }
        // the corridors: what is left, each joined stretch one region
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) {
                if (!dng_walk(d, x, y) || d->region[y][x]) continue;
                uint16_t r = fresh();
                h = t = 0; q[t++] = y * DMAP_W + x; d->region[y][x] = r;
                while (h < t) {
                    int cx = q[h] % DMAP_W, cy = q[h] / DMAP_W; h++;
                    for (int k = 0; k < 4; k++) {
                        int nx = cx + d4x[k], ny = cy + d4y[k];
                        if (!dng_walk(d, nx, ny) || d->region[ny][nx]) continue;
                        d->region[ny][nx] = r; q[t++] = ny * DMAP_W + nx;
                    }
                }
            }
        // scraps go to a neighbour
        std::vector<int> size(d->num_regions + 1, 0);
        std::vector<uint16_t> into(d->num_regions + 1, 0);
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) size[d->region[y][x]]++;
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) {
                uint16_t r = d->region[y][x];
                if (!r || size[r] >= 6 || into[r]) continue;
                for (int k = 0; k < 4; k++) {
                    int nx = x + d4x[k], ny = y + d4y[k];
                    if (dng_walk(d, nx, ny) && d->region[ny][nx] != r && size[d->region[ny][nx]] >= 6) {
                        into[r] = d->region[ny][nx]; break;
                    }
                }
            }
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++)
                if (uint16_t r = d->region[y][x]; r && into[r]) d->region[y][x] = into[r];
    }
    // the walls, each with the floor it faces
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            if (dng_walk(d, x, y) || d->region[y][x]) continue;
            uint16_t r = 0;
            for (int k = 1; k <= 4 && !r; k++) if (dng_walk(d, x, y + k)) r = d->region[y + k][x];
            for (int k = 1; k <= 2 && !r; k++) if (dng_walk(d, x, y - k)) r = d->region[y - k][x];
            for (int dy = -1; dy <= 1 && !r; dy++)
                for (int dx = -1; dx <= 1 && !r; dx++) if (dng_walk(d, x + dx, y + dy)) r = d->region[y + dy][x + dx];
            d->region[y][x] = r;
        }
    // each region's bounds, and one of its floor tiles
    for (int r = 0; r <= d->num_regions; r++) d->regions[r] = { DMAP_W, DMAP_H, -1, -1, -1, -1 };
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++) {
            uint16_t r = d->region[y][x];
            if (!r) continue;
            auto& g = d->regions[r];
            g.x0 = (int16_t)std::min((int)g.x0, x); g.y0 = (int16_t)std::min((int)g.y0, y);
            g.x1 = (int16_t)std::max((int)g.x1, x); g.y1 = (int16_t)std::max((int)g.y1, y);
            if (g.rx < 0 || (dng_walk(d, x, y) && !dng_walk(d, g.rx, g.ry))) { g.rx = (int16_t)x; g.ry = (int16_t)y; }
        }
}

// Lit: the regions of the floor within three steps of the feet -- the one
// stood in, and the next across a doorway, a corridor's mouth, a ladder's top
// or foot. Each lit region is remembered (explored) from then on.
void dungeon_update_sight(DungeonMap* d, int ptx, int pty) {
    if (dungeon_open_sight(d)) { memset(d->visible, 1, sizeof(d->visible)); return; }
    if (ptx < 0 || pty < 0 || ptx >= DMAP_W || pty >= DMAP_H) return;
    uint16_t now[64];
    int n = 0;
    auto add = [&](uint16_t r) {
        if (!r) return;
        for (int i = 0; i < n; i++) if (now[i] == r) return;
        if (n < 64) now[n++] = r;
    };
    struct S { int x, y, k; };
    S q[64];
    int h = 0, t = 0;
    q[t++] = { ptx, pty, 0 };
    add(d->region[pty][ptx]);
    while (h < t) {
        S s = q[h++];
        if (s.k == 3) continue;
        const int dx[4] = { 1, -1, 0, 0 }, dy[4] = { 0, 0, 1, -1 };
        for (int k = 0; k < 4; k++) {
            int nx = s.x + dx[k], ny = s.y + dy[k];
            if (!dng_walk(d, nx, ny)) continue;
            bool seen = false;
            for (int i = 0; i < t && !seen; i++) seen = q[i].x == nx && q[i].y == ny;
            if (seen || t >= 64) continue;
            q[t++] = { nx, ny, s.k + 1 };
            add(d->region[ny][nx]);
        }
    }
    std::sort(now, now + n);
    if (n == d->num_lit && std::equal(now, now + n, d->lit)) return;
    for (int i = 0; i < d->num_lit; i++) {
        const auto& g = d->regions[d->lit[i]];
        for (int y = g.y0; y <= g.y1; y++)
            for (int x = g.x0; x <= g.x1; x++) d->visible[y][x] = 0;
    }
    for (int i = 0; i < n; i++) {
        const auto& g = d->regions[now[i]];
        for (int y = g.y0; y <= g.y1; y++)
            for (int x = g.x0; x <= g.x1; x++)
                if (d->region[y][x] == now[i]) d->visible[y][x] = d->explored[y][x] = 1;
    }
    std::copy(now, now + n, d->lit);
    d->num_lit = n;
}

void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type, float difficulty, unsigned int seed) {
    generate_layout(dmap, type, difficulty, seed);
    build_regions(dmap);
    // The box the floor fills, a wall ring round it (the ring is where
    // dungeon_seat_portals later stands the ways out): the minimap's frame.
    int x0 = DMAP_W, y0 = DMAP_H, x1 = -1, y1 = -1;
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            if (dmap->tiles[y][x] != DNG_WALL) {
                x0 = std::min(x0, x); x1 = std::max(x1, x);
                y0 = std::min(y0, y); y1 = std::max(y1, y);
            }
    if (x1 < 0) { x0 = y0 = 0; x1 = DMAP_W - 1; y1 = DMAP_H - 1; }   // no floor at all: the grid
    dmap->floor_x0 = std::max(x0 - 1, 0);        dmap->floor_y0 = std::max(y0 - 1, 0);
    dmap->floor_x1 = std::min(x1 + 1, DMAP_W - 1); dmap->floor_y1 = std::min(y1 + 1, DMAP_H - 1);
}

// ── Public: orient portals to match overworld direction ───────────────────
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle) {
    // Direction vectors: exit side points along exit_angle, entry is opposite.
    float ex_dx = cosf(exit_angle), ex_dy = sinf(exit_angle);

    float cx = DMAP_W * 0.5f, cy = DMAP_H * 0.5f;

    // First pass: find best exit tile (highest projection onto exit direction).
    float best_exit_score  = -1e30f;
    int   best_exit_tx     = dmap->exit_x,  best_exit_ty  = dmap->exit_y;

    // Second pass: find best entry tile (highest projection onto entry = -exit direction),
    // excluding the tile already claimed for exit.
    float best_entry_score = -1e30f;
    int   best_entry_tx    = dmap->entry_x, best_entry_ty = dmap->entry_y;

    for (int ty = 0; ty < DMAP_H; ty++) {
        for (int tx = 0; tx < DMAP_W; tx++) {
            uint8_t t = dmap->tiles[ty][tx];
            if (t == DNG_WALL) continue;
            float rx = (float)tx - cx, ry = (float)ty - cy;
            float score = rx * ex_dx + ry * ex_dy;
            if (score > best_exit_score) {
                best_exit_score = score;
                best_exit_tx = tx; best_exit_ty = ty;
            }
        }
    }

    for (int ty = 0; ty < DMAP_H; ty++) {
        for (int tx = 0; tx < DMAP_W; tx++) {
            if (tx == best_exit_tx && ty == best_exit_ty) continue;
            uint8_t t = dmap->tiles[ty][tx];
            if (t == DNG_WALL) continue;
            float rx = (float)tx - cx, ry = (float)ty - cy;
            float score = -(rx * ex_dx + ry * ex_dy); // opposite direction
            if (score > best_entry_score) {
                best_entry_score = score;
                best_entry_tx = tx; best_entry_ty = ty;
            }
        }
    }

    // Clear old special tiles, then place at the new positions.
    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_FLOOR;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;

    dmap->exit_x  = best_exit_tx;  dmap->exit_y  = best_exit_ty;
    dmap->entry_x = best_entry_tx; dmap->entry_y = best_entry_ty;

    dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
    dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;

    clear_portal_surroundings(dmap);
}

// ── Public: which dungeon does this entrance open? ───────────────────
//
// Three quantities decide it -- seed, difficulty, archetype -- and they used to
// be worked out by four overlapping `if` blocks in main.cpp's input handler,
// applied last-writer-wins with no precedence written anywhere. That is not a
// tidiness complaint: the partner block ran after the cave-anchor block and
// overwrote it, so a partnered mouth opened a different interior from its own
// siblings on the same mountain -- 13.4% of multi-mouth systems measured over
// ten worlds. Difficulty had no rule at all and was simply taken from whichever
// entrance the player touched, so a linked pair sharing one layout did not share
// its rock: the same cave was Bronze from one mouth and Kharvite from the other.
//
// So: one function, one answer, and the precedence spelled out. It takes a map
// and an index and nothing else, which is what lets tools/dngportals.cpp ask the
// question the game asks instead of a reconstruction of it.

static unsigned int dng_hash_xy(unsigned int map_seed, int x, int y) {
    return map_seed ^ ((unsigned int)x * 73856093u) ^ ((unsigned int)y * 19349663u);
}

DungeonWiring dungeon_wiring_for(const Tilemap* map, unsigned int map_seed,
                                 int entrance_idx) {
    DungeonWiring w = {};
    w.connect_angle = NAN;
    w.n_mouths      = 0;
    w.my_mouth      = -1;
    w.from_exit     = 0;

    if (!map || entrance_idx < 0 || entrance_idx >= map->num_dungeon_entrances) {
        // No record under the player. Nothing sane to open, so hand back a solo
        // dungeon at the origin rather than reading past the array.
        w.seed = map_seed;
        w.difficulty = 0.5f;
        w.type = DUNGEON_ENT_CAVE;
        return w;
    }

    const DungeonEntrance* e = &map->dungeon_entrances[entrance_idx];

    // Defaults are the solo case, rule 4: this entrance alone, keyed to its
    // canonical top-left so any tile of a 2x2 stamp opens the same interior.
    w.type        = e->type;
    w.difficulty  = e->difficulty;
    w.seed        = dng_hash_xy(map_seed, e->x, e->y);
    w.entry_ow_x  = e->x; w.entry_ow_y = e->y;
    w.exit_ow_x   = e->x; w.exit_ow_y  = e->y;
    w.entry_type  = w.exit_type = e->type;
    w.starter     = dungeon_is_starter(e);
    // A pyramid off the desert is a step pyramid, Mayan inside. Its partner,
    // if it has one, is one too: pyramids only pair with their own exterior.
    w.step_pyramid = e->type == DUNGEON_ENT_PYRAMID && e->biome != TILE_SAND;

    // Gather the mouths of this mountain first -- in array order, so the mapping
    // from portal to mouth is the same whichever one you walked in by -- because
    // whether there are two of them is what decides rule 2 below.
    if (e->cave_anchor_x >= 0) {
        for (int i = 0; i < map->num_dungeon_entrances &&
                        w.n_mouths < DMAP_MAX_PORTALS; i++) {
            const DungeonEntrance* m = &map->dungeon_entrances[i];
            if (m->cave_anchor_x != e->cave_anchor_x ||
                m->cave_anchor_y != e->cave_anchor_y) continue;
            if (i == entrance_idx) w.my_mouth = w.n_mouths;
            w.mouth_ow_x[w.n_mouths] = m->x;
            w.mouth_ow_y[w.n_mouths] = m->y;
            // where you stand to walk in: the flat before a foot mouth (whose
            // cliff_level is the wall's, 1), the plateau a ladder hole is cut in
            w.want_lvl[w.n_mouths]   = tilemap_cliff_elev_at(m->x, m->y);
            w.n_mouths++;
        }
        // One mouth is not a system. Clear my_mouth with it: leaving it at 0
        // while n_mouths says there are no mouths is an index into nothing, and
        // every reader guards on n_mouths today only by habit.
        if (w.n_mouths < 2) { w.n_mouths = 0; w.my_mouth = -1; }
    }

    // Hand the carve the shape of the mountain: each mouth's offset from where
    // the mouths average out. It lays the chambers out to match, so the
    // south-face mouth opens into the south of the cave and a north top into the
    // north of it.
    // Measured from the first mouth through the wrap, so a mountain lying
    // across the seam is still one shape and not two halves a world apart.
    if (w.n_mouths >= 2) {
        int sx = 0, sy = 0;
        for (int m = 0; m < w.n_mouths; m++) {
            sx += wrap_dx(w.mouth_ow_x[m] - w.mouth_ow_x[0]);
            sy += wrap_dy(w.mouth_ow_y[m] - w.mouth_ow_y[0]);
        }
        sx /= w.n_mouths; sy /= w.n_mouths;
        for (int m = 0; m < w.n_mouths; m++) {
            w.want_ox[m] = wrap_dx(w.mouth_ow_x[m] - w.mouth_ow_x[0]) - sx;
            w.want_oy[m] = wrap_dy(w.mouth_ow_y[m] - w.mouth_ow_y[0]) - sy;
        }
    }

    // ── Precedence. Exactly one of these sets the seed. ─────────────────
    //
    // Written as one chain rather than four independent ifs so that "which wins"
    // is a property of the code and not of the order somebody happened to paste
    // the blocks in. Highest claim on a dungeon's identity first.

    if (e->x == DNG_FIXED_CAVE_X && e->y == DNG_FIXED_CAVE_Y) {
        // 1. The hand-authored cave: the same layout in every world. It carries
        //    no cave anchor and sits inside the start zone where nothing pairs,
        //    so it can never reach the rules below -- it is first anyway so that
        //    stays true if either of those ever changes.
        w.seed = DNG_FIXED_CAVE_SEED;

    } else if (w.starter) {
        // 1b. The starting graveyard: solo by name, so nothing below -- a
        //     partner, a mountain -- can ever give it a way out anywhere but
        //     its own mouth. The defaults above are exactly that.

    } else if (w.n_mouths >= 2) {
        // 2. A cave system. Every mouth of one mountain opens one cave: that is
        //    the whole of "several ways in", and it outranks a partner link,
        //    which the binding already ignores here for want of a single bearing
        //    between four holes. Difficulty needs no rule -- cave_diff in
        //    tilemap.cpp is already one number for the whole system.
        w.seed = dng_hash_xy(map_seed, e->cave_anchor_x, e->cave_anchor_y);

    } else if (e->partner_idx >= 0 && e->partner_idx < map->num_dungeon_entrances) {
        // 3. A partnered pair: one interior reached from two places, so all
        //    three quantities have to be symmetric or the two ends disagree
        //    about what they are sharing.
        const DungeonEntrance* p = &map->dungeon_entrances[e->partner_idx];
        int ax = e->x, ay = e->y, bx = p->x, by = p->y;
        int minx = ax < bx ? ax : bx, miny = ay < by ? ay : by;
        int maxx = ax > bx ? ax : bx, maxy = ay > by ? ay : by;
        w.seed = map_seed
               ^ ((unsigned int)minx * 73856093u)
               ^ ((unsigned int)miny * 19349663u)
               ^ ((unsigned int)maxx * 83492791u)
               ^ ((unsigned int)maxy * 31729253u);

        // The harder of the two ends. Symmetric, so unlike the seed it needs no
        // tiebreak, and it reads the way a shortcut should: a passage joining a
        // shallow cave to a deep one is the deep one. Both ends then agree on
        // their rock and their loot by construction.
        w.difficulty = (p->difficulty > e->difficulty) ? p->difficulty : e->difficulty;

        // Two graveyards linked across scales share one interior, and it is the
        // larger of the two. A rank comparison rather than the SM->LG case it
        // used to be: with three scales, naming pairs means a catacombs mouth
        // partnered to a small graveyard would drop you into the small one.
        if (dungeon_graveyard_rank(p->type) > dungeon_graveyard_rank(w.type))
            w.type = p->type;

        // Lexicographic order on stamp top-left: lower = DNG_ENTRY side.
        bool we_are_primary = (ax < bx) || (ax == bx && ay < by);
        if (we_are_primary) {
            w.entry_ow_x = ax; w.entry_ow_y = ay;
            w.exit_ow_x  = bx; w.exit_ow_y  = by;
            w.entry_type = e->type; w.exit_type = p->type;
            w.from_exit     = 0;
            w.connect_angle = atan2f((float)wrap_dy(by - ay), (float)wrap_dx(bx - ax));
        } else {
            w.entry_ow_x = bx; w.entry_ow_y = by;
            w.exit_ow_x  = ax; w.exit_ow_y  = ay;
            w.entry_type = p->type; w.exit_type = e->type;
            w.from_exit     = 1;
            w.connect_angle = atan2f((float)wrap_dy(ay - by), (float)wrap_dx(ax - bx));
        }
    }
    // 4. Otherwise solo, which is what the defaults above already say.

    // A cave's ways out are what its entrances are: a hole's a ladder, a
    // mouth's an arch. By portal -- a system's mouths, or the pair's two ends.
    if (w.type == DUNGEON_ENT_CAVE) {
        w.want_hole[0] = tilemap_cave_hole_at(map, w.entry_ow_x, w.entry_ow_y);
        w.want_hole[1] = tilemap_cave_hole_at(map, w.exit_ow_x, w.exit_ow_y);
        for (int m = 0; m < w.n_mouths; m++)
            w.want_hole[m] = tilemap_cave_hole_at(map, w.mouth_ow_x[m], w.mouth_ow_y[m]);
    }

    return w;
}

// ── Public: bind a generated dungeon to the overworld ────────────────
//
// A dungeon comes out of dungeon_generate() with a layout and no idea where its
// stairs let out. There are exactly three answers to that, and they used to sit
// as three inline branches in the overworld input handler in main.cpp -- the one
// place a headless tool cannot reach, which is why nothing had ever counted the
// stairs of a dungeon the way the game actually wires them. They live here now,
// taking nothing but numbers, so the check in tools/dngportals.cpp asks the
// shipped code the question rather than a copy of it.
//
// All three leave the same invariant behind: portals[0..num_portals-1] IS the
// list of stair tiles on the map, portal 0 the entry and the rest exits.

// Every way out stands at the foot of the dungeon's outer wall, facing south
// into it, so its ladder or doorway is on that wall: each portal moves to the
// nearest floor tile it can walk to whose north is perimeter wall -- wall
// joined to the map's edge, not a pillar or a wall inside -- across the
// doorway's whole width, with the face's height of wall above for a ladder,
// floor to its south to step off onto, and no other portal, loot or spawner
// on it. Only the tile moves; where it leads stays. A portal with no such tile
// in reach stays where it is (tools/dngportals.cpp reports it).
void dungeon_seat_portals(DungeonMap* dmap) {
    if (fixed_ways(dmap)) return;            // its ways out stand where they belong already
    static bool perim[DMAP_H][DMAP_W];
    static int qx[DMAP_H * DMAP_W], qy[DMAP_H * DMAP_W];
    static uint8_t seen[DMAP_H][DMAP_W];
    auto walk = [&](int x, int y) {
        uint8_t t = dmap->tiles[y][x];
        return t == DNG_FLOOR || t == DNG_ENTRY || t == DNG_EXIT;
    };
    // the perimeter: wall flooded in from the map's edge
    int head = 0, tail = 0;
    memset(perim, 0, sizeof perim);
    for (int y = 0; y < DMAP_H; y++)
        for (int x = 0; x < DMAP_W; x++)
            if ((x == 0 || y == 0 || x == DMAP_W - 1 || y == DMAP_H - 1) && dmap->tiles[y][x] == DNG_WALL) {
                perim[y][x] = true; qx[tail] = x; qy[tail] = y; tail++;
            }
    while (head < tail) {
        int x = qx[head], y = qy[head]; head++;
        const int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H || perim[ny][nx]) continue;
            if (dmap->tiles[ny][nx] != DNG_WALL) continue;
            perim[ny][nx] = true; qx[tail] = nx; qy[tail] = ny; tail++;
        }
    }
    const WayOutDoor* door = way_out_door(dmap);
    int w = door ? door->w : 1, face = door ? 1 : way_out_face(dmap);
    auto taken = [&](int x, int y, int self) {
        for (int i = 0; i < dmap->num_portals; i++)
            if (i != self && dmap->portals[i].tx == x && dmap->portals[i].ty == y) return true;
        for (int i = 0; i < dmap->num_loot; i++)
            if (dmap->loot[i].tx == x && dmap->loot[i].ty == y) return true;
        for (int i = 0; i < dmap->num_spawners; i++)
            if (dmap->spawners[i].tx == x && dmap->spawners[i].ty == y) return true;
        return false;
    };
    auto seat = [&](int x, int y, int self) {
        if (x < 2 || y < face + 1 || x >= DMAP_W - 2 || y >= DMAP_H - 2) return false;
        if (taken(x, y, self) || !walk(x, y + 1)) return false;
        int x0 = x - (w - 1) / 2;
        for (int i = 0; i < w; i++) {
            if (!walk(x0 + i, y)) return false;                   // the doorway's foot on floor
            if (!perim[y - 1][x0 + i]) return false;              // perimeter wall above it
        }
        for (int k = 2; k <= face; k++)
            if (dmap->tiles[y - k][x] != DNG_WALL) return false;  // the ladder's face
        return true;
    };
    for (int p = 0; p < dmap->num_portals; p++) {
        DungeonPortal& po = dmap->portals[p];
        memset(seen, 0, sizeof seen);
        head = tail = 0;
        qx[tail] = po.tx; qy[tail] = po.ty; tail++; seen[po.ty][po.tx] = 1;
        int fx = -1, fy = -1;
        while (head < tail) {
            int x = qx[head], y = qy[head]; head++;
            if (seat(x, y, p)) { fx = x; fy = y; break; }
            const int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
            for (int d = 0; d < 4; d++) {
                int nx = x + dx[d], ny = y + dy[d];
                if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H || seen[ny][nx] || !walk(nx, ny)) continue;
                seen[ny][nx] = 1; qx[tail] = nx; qy[tail] = ny; tail++;
            }
        }
        if (fx < 0 || (fx == po.tx && fy == po.ty)) continue;
        dmap->tiles[po.ty][po.tx] = DNG_FLOOR;
        dmap->tiles[fy][fx] = p ? DNG_EXIT : DNG_ENTRY;
        po.tx = fx; po.ty = fy;
        if (p == 0) { dmap->entry_x = fx; dmap->entry_y = fy; }
        if (p == 1) { dmap->exit_x = fx; dmap->exit_y = fy; }
    }
}

void dungeon_bind_solo(DungeonMap* dmap, int ow_x, int ow_y) {
    // A lone pyramid is entered in the middle of its passage and left by the
    // far end (the user's design): both doorways lead back out where it stands.
    if (dmap->type == DUNGEON_ENT_PYRAMID) {
        dmap->portals[0] = { dmap->entry_x, dmap->entry_y, ow_x, ow_y, dmap->type };
        dmap->portals[1] = { dmap->exit_x,  dmap->exit_y,  ow_x, ow_y, dmap->type };
        dmap->num_portals = 2;
        dungeon_seat_portals(dmap);
        return;
    }
    // No partner, so the exit the layout carved is a door to nowhere: the way
    // you came in is the way back out. Said as one portal rather than as two
    // with the second's tile quietly floored -- a portal that is not a tile is
    // the disagreement between the array and the map that this file exists to
    // keep out.
    dmap->tiles[dmap->exit_y][dmap->exit_x] = DNG_FLOOR;
    dmap->portals[0] = { dmap->entry_x, dmap->entry_y, ow_x, ow_y, dmap->type };
    dmap->num_portals = 1;
    dungeon_seat_portals(dmap);
}

void dungeon_bind_pair(DungeonMap* dmap, float exit_angle,
                       int entry_ow_x, int entry_ow_y, DungeonEntranceType entry_type,
                       int exit_ow_x,  int exit_ow_y,  DungeonEntranceType exit_type) {
    // Orient first so the underground direction matches the overworld direction
    // between the two entrances, then give each end of the passage its landing.
    if (dmap->type == DUNGEON_ENT_PYRAMID) {
        // Two pyramids joined run end to end: a doorway at each end of the
        // passage, the exit at the end toward the partner. Only the doorways
        // move, so the chambers' back walls stay whole.
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_FLOOR;
        dmap->entry_x = dmap->alt_entry_x; dmap->entry_y = dmap->alt_entry_y;
        float ex = cosf(exit_angle), ey = sinf(exit_angle);
        if (dmap->exit_x * ex + dmap->exit_y * ey < dmap->entry_x * ex + dmap->entry_y * ey) {
            int x = dmap->exit_x, y = dmap->exit_y;
            dmap->exit_x = dmap->entry_x; dmap->exit_y = dmap->entry_y;
            dmap->entry_x = x; dmap->entry_y = y;
        }
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
        dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
    } else if (fixed_ways(dmap)) {
        // The two ways out stand where the layout put them: the one further
        // along the bearing to the partner is the way there.
        float ex = cosf(exit_angle), ey = sinf(exit_angle);
        if (dmap->exit_x * ex + dmap->exit_y * ey < dmap->entry_x * ex + dmap->entry_y * ey) {
            int x = dmap->exit_x, y = dmap->exit_y;
            dmap->exit_x = dmap->entry_x; dmap->exit_y = dmap->entry_y;
            dmap->entry_x = x; dmap->entry_y = y;
        }
        dmap->tiles[dmap->entry_y][dmap->entry_x] = DNG_ENTRY;
        dmap->tiles[dmap->exit_y][dmap->exit_x]   = DNG_EXIT;
    } else {
        dungeon_orient_portals(dmap, exit_angle);
    }
    dmap->portals[0] = { dmap->entry_x, dmap->entry_y, entry_ow_x, entry_ow_y, entry_type };
    dmap->portals[1] = { dmap->exit_x,  dmap->exit_y,  exit_ow_x,  exit_ow_y,  exit_type  };
    dmap->num_portals = 2;
    dungeon_seat_portals(dmap);
}

void dungeon_want(DungeonMap* dmap, const DungeonWiring* w) {
    dmap->want_portals = (w->n_mouths >= 2) ? w->n_mouths : 2;
    dmap->starter      = w->starter;
    dmap->step_pyramid = w->step_pyramid;
    for (int m = 0; m < DMAP_MAX_PORTALS; m++) {
        bool mine = m < w->n_mouths;
        dmap->want_ox[m]  = mine ? w->want_ox[m]  : 0;
        dmap->want_oy[m]  = mine ? w->want_oy[m]  : 0;
        dmap->want_lvl[m] = mine ? w->want_lvl[m] : 0;
        dmap->want_hole[m] = w->want_hole[m];
    }
}

void dungeon_bind_cave_mouths(DungeonMap* dmap, const int* ow_x, const int* ow_y, int n) {
    // A cave keeps all its ways out and each one leads to its own mouth.
    // Orienting is a two-mouth idea -- it aligns the underground direction with
    // the bearing between a pair -- and there is no single bearing when there
    // are four, so it is skipped.
    for (int p = 0; p < dmap->num_portals; p++) {
        int mi = (p < n) ? p : 0;
        dmap->portals[p].ow_x = ow_x[mi];
        dmap->portals[p].ow_y = ow_y[mi];
        dmap->portals[p].ow_type = dmap->type;
    }
    dungeon_seat_portals(dmap);
}

// ── Public: player init ───────────────────────────────────────────────────
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit) {
    int spawn_tx = from_exit ? dmap->exit_x  : dmap->entry_x;
    int spawn_ty = from_exit ? dmap->exit_y  : dmap->entry_y;
    dp->x        = (float)(spawn_tx * DMAP_TILE);
    dp->y        = (float)(spawn_ty * DMAP_TILE + DMAP_TILE / 2 - 24);
    dp->speed    = PLAYER_WALK_SPEED;
    dp->at_exit  = 0;
    dp->at_way   = -1;
    dp->at_entry = 0;
    if (dmap->type == DUNGEON_ENT_OASIS && dmap->num_oasis_air >= 2) {   // up at the shaft's surface
        const auto& a = dmap->oasis_air[from_exit ? 1 : 0];
        dp->x = (float)(((dmap->oasis_x0 + (a.x0 + a.x1) / 2) * DMAP_TILE / 16) - 14);
        dp->y = (float)(((dmap->oasis_y0 + a.line - OASIS_HEAD + 1) * DMAP_TILE / 16) - 10);
        dp->vx = dp->vy = 0;
    }

    dp->swing = WeaponSwingState();

    // Reset animation state on the shared player
    player->facing        = FACE_DOWN;
    player->facing_locked = 0;
    player->anim_step     = 0;
    player->anim_timer    = 0.0f;
    player->is_moving     = 0;
}

// ── Tile collision ─────────────────────────────────────────────────────────
static bool tile_solid(const void* map, float px, float py) {
    const DungeonMap* dmap = static_cast<const DungeonMap*>(map);

    int tx = (int)(px / DMAP_TILE);
    int ty = (int)(py / DMAP_TILE);
    if (tx < 0 || tx >= DMAP_W || ty < 0 || ty >= DMAP_H) return true;
    // the graveyard's walkways to the art pixel: their slanted edges block
    // where they are drawn, not on the tile grid
    if (gyw_walkways(dmap))
        return !gyw_on_path(dmap, (int)floorf(px * 16 / DMAP_TILE), (int)floorf(py * 16 / DMAP_TILE), true);
    if (dmap->type == DUNGEON_ENT_STONEHENGE)
        return col_solid(dmap, (int)floorf(px * 16 / DMAP_TILE), (int)floorf(py * 16 / DMAP_TILE));
    if (dmap->type == DUNGEON_ENT_OASIS)
        return oasis_blocked(dmap, (int)floorf(px * 16 / DMAP_TILE) - dmap->oasis_x0,
                             (int)floorf(py * 16 / DMAP_TILE) - dmap->oasis_y0);
    if (dmap->type == DUNGEON_ENT_CATACOMBS)                 // the feet taken back into the world
        return !cat_walkable(dmap, px * 16 / DMAP_TILE, py * 16 / DMAP_TILE);
    if (terraced(dmap)) {                                    // floors and ladders to the art pixel
        if (dmap->type == DUNGEON_ENT_CAVE && dmap->art[ty][tx]) return true;   // a crystal, the tile it stands on
        return !tree_walkable(dmap, (int)floorf(px * 16 / DMAP_TILE) - dmap->tree_ox,
                              (int)floorf(py * 16 / DMAP_TILE) - dmap->tree_oy);
    }
    return dmap->tiles[ty][tx] == DNG_WALL;
}

bool dungeon_solid_at(const void* dmap, float px, float py) { return tile_solid(dmap, px, py); }

// Where way out p is drawn: the middle of its ladder or door at the foot of
// the wall it stands on, in world pixels, and half its drawn width. Every
// kind says it here, from what draws it -- the hitbox, where the player is
// stood on arriving and which way out was taken all read this, so they can
// not drift from the picture again (they did: a two-wide door is drawn from
// its tile to the next, a projected one wherever the projection puts it).
static void way_point(const DungeonMap* d, int p, float* wx, float* wy, float* half) {
    const float A = DMAP_TILE / 16.0f;                     // world pixels an art pixel
    int tx = d->portals[p].tx, ty = d->portals[p].ty;
    *wx = (tx + 0.5f) * DMAP_TILE; *wy = (float)(ty * DMAP_TILE); *half = 8 * A;   // a ladder on its tile
    switch (d->type) {
        case DUNGEON_ENT_STONEHENGE:                       // the barrow's ladders, where the picture has them
            for (int w = 0; w < 2; w++) {
                int x, y;
                barrow_way_tile(d, w, &x, &y);
                if (x != tx || y != ty) continue;
                *wx = (d->barrow_ox + d->barrow_way_x[w] + d->barrow_way_d[w]) * A;
                *wy = (d->barrow_oy - d->barrow_way_d[w]) * A;
            }
            return;
        case DUNGEON_ENT_GRAVEYARD_SM: case DUNGEON_ENT_GRAVEYARD_LG:
            for (int w = 0; w < 2; w++) {                  // the ladder or door 24 in on its wall, 16 wide
                int x, y;
                gyw_way_tile(d, w, &x, &y);
                if (x != tx || y != ty) continue;
                int vf = gyw_wall_v(d, w);
                *wx = (d->gyw_ox + gyw_wall_u(d, w) + vf + 32) * A;
                *wy = (d->gyw_oy - vf) * A;
            }
            return;
        case DUNGEON_ENT_CATACOMBS:                        // the cut's door, at its projected foot
            for (int i = 0; i < d->num_cat_cuts; i++) {
                const auto& c = d->cat_cuts[i];
                if (c.area != 0 || c.tx != tx || c.ty != ty) continue;
                float ax, ay;
                cat_screen(d, 0, c.u0 + c.k / 2.0f, c.v0 + c.k / 2.0f, &ax, &ay);
                *wx = ax * A; *wy = ay * A;
            }
            return;
        case DUNGEON_ENT_OASIS:                            // the shaft's ladder, at its water line
            for (int i = 0; i < 2 && i < d->num_oasis_air; i++) {
                int x, y;
                oasis_way_tile(d, i, &x, &y);
                if (x != tx || y != ty) continue;
                *wx = (d->oasis_x0 + (d->oasis_air[i].x0 + d->oasis_air[i].x1) / 2) * A;
                *wy = (d->oasis_y0 + d->oasis_air[i].line) * A;
            }
            return;
        default:
            if (cave_ladder_out(d, p)) return;                // a ladder on its tile
            if (const WayOutDoor* door = way_out_door(d)) {   // draw_ways_out: from tx - (w-1)/2, w wide
                *wx = (tx - (door->w - 1) / 2 + door->w * 0.5f) * DMAP_TILE;
                *half = door->w * 8 * A;
            }
            return;
    }
}

int dungeon_way_at(const DungeonMap* dmap, float cx, float cy) {
    for (int p = 0; p < dmap->num_portals; p++) {
        float wx, wy, half;
        way_point(dmap, p, &wx, &wy, &half);
        if (dmap->type == DUNGEON_ENT_OASIS) {
            // Surfaced under the ladder: the head up out of the water (as
            // dungeon_breathing has it), the body's middle under the ladder.
            int x0, y0, x1, y1;
            oasis_body(dmap, cx - (HB_X1 + HB_X2) * 0.5f, cy - (HB_Y1 + HB_Y2) * 0.5f, &x0, &y0, &x1, &y1);
            float mid = (x0 + x1) * 0.5f + dmap->oasis_x0, lx = wx * 16 / DMAP_TILE;
            if (fabsf(mid - lx) <= 8 && y0 <= wy * 16 / DMAP_TILE - dmap->oasis_y0 - 2) return p;
            continue;
        }
        // The box at its foot: its drawn width and a little, from a little up
        // the wall to WAY_REACH out before it.
        if (fabsf(cx - wx) <= half + 2 && cy >= wy - 10 && cy <= wy + 8 + WAY_REACH) return p;
    }
    return -1;
}

void dungeon_stand_before_way(const DungeonMap* dmap, DungeonPlayer* dp) {
    // The way out the player was put on: the nearest.
    float cx = dp->x + (HB_X1 + HB_X2) * 0.5f, cy = dp->y + (HB_Y1 + HB_Y2) * 0.5f;
    int best = -1;
    float bd = 0;
    for (int p = 0; p < dmap->num_portals; p++) {
        float dx = (dmap->portals[p].tx + 0.5f) * DMAP_TILE - cx, dy = (dmap->portals[p].ty + 0.5f) * DMAP_TILE - cy;
        if (best < 0 || dx * dx + dy * dy < bd) { best = p; bd = dx * dx + dy * dy; }
    }
    if (best < 0) return;
    float wx, wy, half;
    way_point(dmap, best, &wx, &wy, &half);
    if (dmap->type == DUNGEON_ENT_OASIS) {
        // under the ladder, the head a pixel short of surfacing: one stroke up
        // and out (oasis_body: the head is 10 below the frame's top)
        dp->x = wx - 14;
        dp->y = (wy * 16 / DMAP_TILE - 1) * DMAP_TILE / 16 - 10;
        return;
    }
    if (!stand_clear(&wx, &wy, 0, 1,
            [&](float x, float y) { return dungeon_way_at(dmap, x, y) >= 0; },
            [&](float x, float y) { return can_occupy(dmap, x - (HB_X1 + HB_X2) * 0.5f, y - (HB_Y1 + HB_Y2) * 0.5f, tile_solid); }))
        return;
    dp->x = wx - (HB_X1 + HB_X2) * 0.5f;
    dp->y = wy - (HB_Y1 + HB_Y2) * 0.5f;
}

// How far a wall stands above its foot on the screen, in art pixels: how much
// of the floor behind it it can hide. Walls drawn inside their own tiles (the
// ruins', the pyramids', the caves') hide nothing.
static int wall_rise(const DungeonMap* d, int tx, int ty) {
    if (d->type == DUNGEON_ENT_STONEHENGE) return BRW_BZ + 1;           // the block and its grass row
    if (d->type == DUNGEON_ENT_CATACOMBS) {
        int a = cat_area_at(d, tx * 16 + 8.0f, ty * 16 + 8.0f);
        return a < 0 ? 0 : cat_z(a) + 1;                                 // the wall and its top row
    }
    return 0;
}

// A tile with nothing drawn over it: all floor, and so is the screen column
// straight below it as far as a wall rises -- every view draws height straight
// up, so whatever could hide the tile has its foot there.
static bool tile_in_the_open(const DungeonMap* d, int tx, int ty) {
    int rise = wall_rise(d, tx, ty);
    for (int ay = ty * 16; ay < ty * 16 + 16 + rise; ay++)
        for (int ax = tx * 16; ax < tx * 16 + 16; ax++)
            if (tile_solid(d, (ax + 0.5f) * DMAP_TILE / 16, (ay + 0.5f) * DMAP_TILE / 16)) return false;
    return true;
}

// The check on it, from the other side: a baked picture (its origin on the
// map and its pixels' rank, -1 where only the floor shows) must have nothing
// on a treasure's tile. Says so on stderr if it has.
static void warn_treasure_covered(const DungeonMap* d, int x0, int y0, int W, int H, const std::vector<int8_t>& rank) {
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.item < 0) continue;
        int n = 0;
        for (int y = lo.ty * 16 - y0; y < lo.ty * 16 + 16 - y0; y++)
            for (int x = lo.tx * 16 - x0; x < lo.tx * 16 + 16 - x0; x++)
                if (x >= 0 && y >= 0 && x < W && y < H && rank[y * W + x] >= 0) n++;
        if (n) fprintf(stderr, "treasure under a wall: type %d tile %d,%d (%d px)\n", (int)d->type, lo.tx, lo.ty, n);
    }
}


// The catacombs' ways between areas, taken as a door is (user): standing on a
// hole in the hall's floor, down to the foot of its section's ladder; at the
// ladder, back up beside the hole. 2h is hole h, 2h + 1 its ladder; -1 none.
static int cat_link_at(const DungeonMap* d, const DungeonPlayer* dp) {
    float ax = (dp->x + (HB_X1 + HB_X2) * 0.5f) * 16 / DMAP_TILE, ay = (dp->y + (HB_Y1 + HB_Y2) * 0.5f) * 16 / DMAP_TILE;
    int a = cat_area_at(d, ax, ay);
    for (int h = 0; h < d->num_cat_holes && a >= 0; h++) {
        const auto& H = d->cat_holes[h];
        float hx, hy, u, v;
        cat_screen(d, 0, H.u, H.v, &hx, &hy);
        if (a == 0 && fabsf(ax - hx) < 10 && fabsf(ay - hy) < 7) return 2 * h;
        const auto& c = d->cat_cuts[H.ladder];
        cat_world(d, a, ax, ay, &u, &v);
        if (a == c.area && fabsf((u - v) - (c.u0 - c.v0)) < 12 && u + v < c.u0 + c.v0 + c.k + 16) return 2 * h + 1;
    }
    return -1;
}

const char* dungeon_link_name(const DungeonMap* d, const DungeonPlayer* dp) {
    static const char* NAMES[CAT_MAX_AREAS] = { "MAIN NAVE", "CATACOMBS I", "CATACOMBS II", "CATACOMBS III",
                                                "CATACOMBS IV", "CATACOMBS V" };
    if (d->type != DUNGEON_ENT_CATACOMBS || dp->at_link < 0) return nullptr;
    return dp->at_link & 1 ? NAMES[0] : NAMES[d->cat_holes[dp->at_link / 2].to];
}

void dungeon_take_link(const DungeonMap* d, DungeonPlayer* dp) {
    if (d->type != DUNGEON_ENT_CATACOMBS || dp->at_link < 0) return;
    const auto& H = d->cat_holes[dp->at_link / 2];
    const auto& c = d->cat_cuts[H.ladder];
    float x, y;
    if (dp->at_link & 1) cat_screen(d, 0, H.u + 24, H.v + 24, &x, &y);                        // just in front of the hole
    else cat_screen(d, c.area, c.u0 + c.k / 2.0f + 20, c.v0 + c.k / 2.0f + 20, &x, &y);  // 40 out from the wall
    dp->x = x * DMAP_TILE / 16 - (HB_X1 + HB_X2) * 0.5f;
    dp->y = y * DMAP_TILE / 16 - (HB_Y1 + HB_Y2) * 0.5f;
    dp->at_link = cat_link_at(d, dp);
}

// ── Public: player update ─────────────────────────────────────────────────
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, DungeonMap* dmap, const Camera* cam,
                           bool noclip, HarvestResult* out_harvest) {
    float anim_speed;

    float hx = dp->x + (HB_X1 + HB_X2) * 0.5f;
    float hy = dp->y + (HB_Y1 + HB_Y2) * 0.5f;

    HarvestResult local = {};
    HarvestResult* h = out_harvest ? out_harvest : &local;

    // Same trigger/dispatch/advance machinery as overworld_update()
    // (src/overworld.cpp) -- tiles is null since a dungeon has no tile-based
    // harvest system, only rock nodes.
    weapon_swing_update(&dp->swing, player, in, dt, hx, hy, &dmap->dungeon_rocks,
                       nullptr, cam, (int)dmap->ore, h);

    // A destroyed rock node carves the wall tile it sat in open into floor --
    // the dungeon's equivalent of the gravestone-reveal tile write in
    // overworld_update() (src/overworld.cpp).
    for (int i = 0; i < h->count; i++) {
        if (!h->hits[i].destroyed) continue;
        int rtx = (int)(h->hits[i].x / DMAP_TILE);
        int rty = (int)(h->hits[i].y / DMAP_TILE);
        if (rtx < 0 || rtx >= DMAP_W || rty < 0 || rty >= DMAP_H) continue;
        dmap->tiles[rty][rtx] = DNG_FLOOR;
        dmap->art[rty][rtx]   = 0;                     // a cave's crystal stood here (place_cave_nodes)
    }

    float dx = 0.0f, dy = 0.0f;
    if (!weapon_swing_frozen_tick(&dp->swing, player, dt))
        player_read_input(player, in, &dx, &dy);

    player_gait(in, &dp->speed, &anim_speed);

    // The giant tree's ladders, climbed as EarthBound's are (user): pressing
    // up or down at one draws the player across onto it -- a slide at walking
    // pace, not a jump -- and on it they go only up or down. LADDER_LEAN: where
    // on it, art pixels left of its middle (user: one).
    const float ART = 16.0f / DMAP_TILE;                   // art pixels a world pixel
    auto feet_art = [&](float* fx, float* fy) {
        *fx = (dp->x + (HB_X1 + HB_X2) * 0.5f) * ART - dmap->tree_ox;
        *fy = (dp->y + (HB_Y1 + HB_Y2) * 0.5f) * ART - dmap->tree_oy;
    };
    if (terraced(dmap) && !noclip) {
        float fx, fy;
        feet_art(&fx, &fy);
        bool on = tree_on_ladder(dmap, fx, fy);
        int lad = tree_ladder_at(dmap, fx, fy, dy);
        if (lad >= 0 && (dy != 0.0f || on)) {
            const float LADDER_LEAN = 1;
            float sx = (dmap->tree_ox + dmap->tree_ladders[lad].x0 + 8 - LADDER_LEAN) / ART - (HB_X1 + HB_X2) * 0.5f;
            float step = dp->speed * dt, nx = dp->x + std::max(-step, std::min(step, sx - dp->x));
            if (nx != dp->x && can_occupy(dmap, nx, dp->y, tile_solid)) { dp->x = nx; player->is_moving = 1; }
            dx = 0.0f;
            dy = dy < 0.0f ? -1.0f : dy > 0.0f ? 1.0f : 0.0f;
        }
    }

    if (dmap->type == DUNGEON_ENT_OASIS) {
        // Swimming (the oasis): the way pressed is where the swimmer heads, at
        // three quarters of walking pace, eased into and out of -- the drift --
        // each axis stopping where the rock does. It faces left or right only.
        float k = std::min(1.0f, dt * 5.0f), sp = dp->speed * 0.75f;
        dp->vx += (dx * sp - dp->vx) * k;
        dp->vy += (dy * sp - dp->vy) * k;
        float nx = dp->x + dp->vx * dt, ny = dp->y + dp->vy * dt;
        if (noclip || oasis_body_free(dmap, nx, dp->y)) dp->x = nx; else dp->vx = 0;
        if (noclip || oasis_body_free(dmap, dp->x, ny)) dp->y = ny; else dp->vy = 0;
        if (dx < 0) player->facing = FACE_LEFT;
        if (dx > 0) player->facing = FACE_RIGHT;
        if (player->facing != FACE_LEFT && player->facing != FACE_RIGHT) player->facing = FACE_RIGHT;
        player->is_moving = fabsf(dp->vx) + fabsf(dp->vy) > 8.0f;
        dx = dy = 0.0f;                                   // the walk below has nothing to do
    }
    if (dx != 0.0f || dy != 0.0f) {
        float nx = dp->x + dx * dp->speed * dt;
        float ny = dp->y + dy * dp->speed * dt;
        float px = dp->x, py = dp->y;
        if (noclip || can_occupy(dmap, nx, dp->y, tile_solid)) dp->x = nx;
        if (noclip || can_occupy(dmap, dp->x, ny, tile_solid)) dp->y = ny;
        // Where walls slant (the graveyard's walkways, stonehenge's maze) a
        // straight push against a 45-degree edge slides along it, so up or
        // down follows a slanted run. A full step on both axes keeps to the
        // edge's pixel staircase (a shorter one snags on its corners), so it
        // is taken on 1 frame in 1.414 -- walking speed along the slant.
        bool iso = dmap->type == DUNGEON_ENT_CATACOMBS;
        if (dp->x == px && dp->y == py && iso) {
            // The catacombs' walls run 2:1 on the screen (and flat): a push
            // into one slides along whichever of its ways the push has the
            // most of, at that much of the pace.
            float m = sqrtf(dx * dx + dy * dy), best = 0.2f, bx = px, by = py;
            for (int k = 0; k < 4; k++) {
                float wx = (k & 1 ? -2.0f : 2.0f) / sqrtf(5.0f), wy = (k & 2 ? -1.0f : 1.0f) / sqrtf(5.0f);
                float dot = (dx * wx + dy * wy) / m;
                if (dot <= best) continue;
                float st = dot * m * dp->speed * dt;
                if (can_occupy(dmap, px + wx * st, py + wy * st, tile_solid)) { best = dot; bx = px + wx * st; by = py + wy * st; }
            }
            dp->x = bx; dp->y = by;
        }
        if (dp->x == px && dp->y == py && fixed_ways(dmap) && !iso && (dx == 0.0f) != (dy == 0.0f)) {
            float step = (dx != 0.0f ? fabsf(dx) : fabsf(dy)) * dp->speed * dt;
            bool along = false;
            for (int sgn = -1; sgn <= 1 && !along; sgn += 2) {
                float sx = dx != 0.0f ? nx : px + sgn * step, sy = dy != 0.0f ? ny : py + sgn * step;
                if (!can_occupy(dmap, sx, sy, tile_solid)) continue;
                along = true;
                dp->slide += 0.70710678f;
                if (dp->slide >= 1.0f) { dp->x = sx; dp->y = sy; dp->slide -= 1.0f; }
            }
            if (!along) dp->slide = 0;                       // a flat wall: no way along it
            else player->is_moving = 1;                      // between steps, still walking
        }
        if (dp->x == px && dp->y == py && !(fixed_ways(dmap) && player->is_moving && dp->slide > 0))
            player->is_moving = 0;
    }
    if (terraced(dmap)) {                                  // facing the ladder, up it or down
        float fx, fy;
        feet_art(&fx, &fy);
        if (tree_on_ladder(dmap, fx, fy)) player->facing = FACE_UP;
    }

    dp->at_link = dmap->type == DUNGEON_ENT_CATACOMBS ? cat_link_at(dmap, dp) : -1;

    // which way out (entry or exit) the player has walked into.
    float cx = dp->x + (HB_X1 + HB_X2) * 0.5f;
    float cy = dp->y + (HB_Y1 + HB_Y2) * 0.5f;
    int tx = (int)(cx / DMAP_TILE);
    int ty = (int)(cy / DMAP_TILE);
    int way = dungeon_way_at(dmap, cx, cy);
    uint8_t wt = way >= 0 ? dmap->tiles[dmap->portals[way].ty][dmap->portals[way].tx] : 0;
    dp->at_way   = way;
    dp->at_exit  = wt == DNG_EXIT;
    dp->at_entry = wt == DNG_ENTRY;

    // Loot pickup: auto-collect when standing on an unclaimed loot tile --
    // gold into the purse, a treasure into the inventory.
    dp->picked_item = -1;
    for (int li = 0; li < dmap->num_loot; li++) {
        DungeonLoot& lo = dmap->loot[li];
        if (lo.collected) continue;
        if (lo.tx == tx && lo.ty == ty) {
            lo.collected = true;
            if (lo.item >= 0) {
                item_slot(player, (Item)lo.item) += 1;
                dp->picked_item = lo.item;
            } else {
                player->inventory[(int)RESOURCE_GOLD] += lo.gold;
            }
        }
    }

    player_animate(player, dt, anim_speed);

    // ── Sight: the regions in reach lit, and remembered ──
    dungeon_update_sight(dmap, (int)((dp->x + (HB_X1 + HB_X2) * 0.5f) / DMAP_TILE),
                         (int)((dp->y + (HB_Y1 + HB_Y2) * 0.5f) / DMAP_TILE));
}

// ── Built walls: drawing (the ruins, the pyramid) ────────────────────────────────────────────────────────────────────────────
//
// Every tile draws the piece its art says (tools/gen_dungeon_wall_tiles.py baked
// them from the approved designs): faces and a flight's wall by their column
// phase, so the carving runs on unbroken from wall to wall; a flight column
// in two layers, its steps and caps and then its upright wall; the wall top's
// rim as a quarter autotile round everything but the flights, which carry
// their own caps (the pyramid has neither: no perimeter outline, the user's
// call). Over them the pieces laid whole -- the Mayan murals, the
// carved stones and cartouches -- and a black line wherever two wall segments
// meet.

static bool art_walk(const DungeonMap* d, int x, int y) {
    return x >= 0 && y >= 0 && x < DMAP_W && y < DMAP_H && d->tiles[y][x] != DNG_WALL;
}

static bool art_open(const DungeonMap* d, int x, int y) {      // what the rim runs round
    if (x < 0 || y < 0 || x >= DMAP_W || y >= DMAP_H) return false;
    uint8_t a = d->art[y][x];
    return a != WA_NONE && a != WA_FLIGHT;
}

static void draw_ways_out(const DungeonMap* dmap, const Camera* cam, SDL_Renderer* ren,
                          int tx0, int ty0, int tx1, int ty1, int tsz);

// ── Torches (user: caves and ruins have torches) ─────────────────────────
// One drawing, assets/torch.png: frames 16 x 32 side by side, the flame in a
// frame's upper 16 rows, the cup and handle below. Nothing of it is a wall's
// tone (user: "match the them of the dungeon but not look exactly like the
// stone or walls"): the flame is drawn as fire, and a dungeon may show it in a
// colour of its own. Round it a glow on the wall, which grows and shrinks with
// the flame (user).
static const Uint32 TORCH_MS = 150;               // a frame's time
static const int GLOW_G = 30;                     // a glow's cell: the widest disc, 14 px, about the flame's middle
// A flame's colours: its heart, body and edge (0xRRGGBB), a set a hue. With
// more than one it is a rainbow (user: "the individual flame is rainbow
// colored", its stripes "alternating", "sideways ... instead of purly vertical
// or horizontal", and "the circle should reflect that its rainbow"): slanted
// stripes 2 px wide, moving along a stripe a frame, and the glow striped with
// them. Kept soft (user: "more sutle maybe mixxing some white"): a stripe is
// its hue's pale tone, and the flame's heart stays white, as the white flame's
// is. None: fire, as drawn.
struct Flame {
    const uint32_t (*tones)[3] = nullptr;
    int hues = 0;
};
struct TorchArt {
    SDL_Surface* sw = nullptr;                    // the drawing
    SDL_Renderer* ren = nullptr;
    SDL_Texture* tex = nullptr;                   // it with the flame last asked for
    uint32_t key = 0;
    Flame flame;
    std::vector<int> glow;                        // each frame's glow: a disc of this many px
    uint32_t body = 0;                            // the flame's body tone, which its glow leans to
};
static TorchArt s_torch;
static SDL_Surface* sheet_pixels();

static uint32_t rgba32(uint32_t rgb) {            // 0xRRGGBB as an RGBA32 pixel
    const uint8_t b[4] = { (uint8_t)(rgb >> 16), (uint8_t)(rgb >> 8), (uint8_t)rgb, 255 };
    uint32_t c;
    memcpy(&c, b, 4);
    return c;
}

// The tone the torch's light is at (x, y) of its cell in frame f: the flame's
// body -- a rainbow's, the stripe's there, the stripes `wide` px. (x, y) may
// lie off the cell: the glow reads it too, in stripes twice the flame's, so
// the rock's own texture does not chop them to specks.
static uint32_t torch_light(int x, int y, int f, int wide) {
    const Flame& fl = s_torch.flame;
    return fl.hues > 1 ? rgba32(fl.tones[((x + y + 64) / wide + f) % fl.hues][0]) : s_torch.body;
}

static SDL_Texture* torch_tex(SDL_Renderer* ren, Flame flame) {
    const uint32_t key = flame.hues ? flame.tones[0][1] * 31u + (uint32_t)flame.hues : 0u;
    if (s_torch.tex && s_torch.ren == ren && s_torch.key == key) return s_torch.tex;
    if (!s_torch.sw)
        if (SDL_Surface* raw = IMG_Load("assets/torch.png")) {
            s_torch.sw = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
            SDL_FreeSurface(raw);
        }
    if (!s_torch.sw) return nullptr;
    if (s_torch.tex) SDL_DestroyTexture(s_torch.tex);
    s_torch.tex = nullptr;
    SDL_Surface* s = SDL_ConvertSurface(s_torch.sw, s_torch.sw->format, 0);
    if (!s) return nullptr;
    auto px = [&](int x, int y) -> uint32_t& { return *(uint32_t*)((uint8_t*)s->pixels + y * s->pitch + x * 4); };
    auto ink = [](uint32_t c) { const uint8_t* b = (const uint8_t*)&c; return b[3] && (b[0] | b[1] | b[2]); };   // not black, not clear
    auto lum = [](uint32_t c) { const uint8_t* b = (const uint8_t*)&c; return b[0] * 299 + b[1] * 587 + b[2] * 114; };
    std::vector<uint32_t> tones;                  // the flame's as drawn, lightest first
    for (int y = 0; y < 16; y++)
        for (int x = 0; x < s->w; x++)
            if (ink(px(x, y)) && std::find(tones.begin(), tones.end(), px(x, y)) == tones.end()) tones.push_back(px(x, y));
    std::sort(tones.begin(), tones.end(), [&](uint32_t a, uint32_t b) { return lum(a) > lum(b); });
    s_torch.flame = flame;
    s_torch.body = flame.hues ? rgba32(flame.tones[0][1]) : tones.empty() ? 0 : tones[tones.size() / 2];
    s_torch.glow.clear();
    for (int f = 0; f < s->w / 16; f++) {         // a frame's glow by its flame's height: 11 rows, the steady one, 12 px
        int rows = 0;
        for (int y = 0; y < 16; y++)
            for (int x = 0; x < 16; x++)
                if (px(f * 16 + x, y) >> 24) { rows++; break; }
        s_torch.glow.push_back(10 + 2 * std::max(0, std::min(2, rows - 10)));
    }
    for (int y = 0; flame.hues && y < 16; y++)    // each tone of the flame to the dungeon's -- the lightest drawn is the
        for (int x = 0; x < s->w; x++)            // heart, then the body, the edge; a rainbow's heart white, the rest by its stripe
            if (ink(px(x, y))) {
                const int part = (int)((std::find(tones.begin(), tones.end(), px(x, y)) - tones.begin()) * 3 / tones.size());
                px(x, y) = flame.hues == 1 ? rgba32(flame.tones[0][part]) : part ? torch_light(x % 16, y, x / 16, 2) : rgba32(0xfcfcfc);
            }
    s_torch.tex = SDL_CreateTextureFromSurface(ren, s);
    SDL_FreeSurface(s);
    if (s_torch.tex) SDL_SetTextureBlendMode(s_torch.tex, SDL_BLENDMODE_BLEND);
    s_torch.ren = ren; s_torch.key = key;
    return s_torch.tex;
}

// The glows of n torches, a row each, a cell a frame: the wall behind the
// torch (wall(i, x, y), a cell's pixel, 0 where there is none to light) inside
// that frame's disc, each pixel pulled two fifths of the way to the torch's
// light there (torch_light) and put back on the palette -- nothing blends.
template <class Wall> static SDL_Texture* torch_glow_tex(SDL_Renderer* ren, int n, Wall wall) {
    const int nf = (int)s_torch.glow.size();
    SDL_Surface* s = SDL_CreateRGBSurfaceWithFormat(0, nf * GLOW_G, n * GLOW_G, 32, SDL_PIXELFORMAT_RGBA32);
    if (!s) return nullptr;
    SDL_FillRect(s, nullptr, 0);
    for (int i = 0; i < n; i++)
        for (int k = 0; k < nf; k++)
            for (int y = 0; y < GLOW_G; y++)
                for (int x = 0; x < GLOW_G; x++) {
                    const uint32_t light = torch_light(x - 7, y - 4, k, 4);         // the cell's corner is (-7, -4) of the torch's
                    const uint8_t* to = (const uint8_t*)&light;
                    const int dx = 2 * x - (GLOW_G - 1), dy = 2 * y - (GLOW_G - 1), r = 2 * s_torch.glow[k] + 1;   // half pixels
                    const uint32_t c = dx * dx + dy * dy <= r * r ? wall(i, x, y) : 0;
                    if (!(c >> 24)) continue;
                    const uint8_t* w = (const uint8_t*)&c;
                    const SDL_Color m = fc_snap((uint8_t)(w[0] + (to[0] - w[0]) * 2 / 5), (uint8_t)(w[1] + (to[1] - w[1]) * 2 / 5),
                                                (uint8_t)(w[2] + (to[2] - w[2]) * 2 / 5));
                    const uint8_t out[4] = { m.r, m.g, m.b, 255 };
                    memcpy((uint8_t*)s->pixels + (i * GLOW_G + y) * s->pitch + (k * GLOW_G + x) * 4, out, 4);
                }
    SDL_Texture* t = SDL_CreateTextureFromSurface(ren, s);
    SDL_FreeSurface(s);
    if (t) SDL_SetTextureBlendMode(t, SDL_BLENDMODE_BLEND);
    return t;
}

// A torch, its 16 x 32 cell at (ax, ay) in art pixels on the map (16 a tile),
// and its glow, row i of `glow`. Neighbours burn out of step.
static void draw_torch(const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex, SDL_Texture* glow, int i, int ax, int ay, int tsz) {
    const int nf = (int)s_torch.glow.size();
    if (!nf) return;
    const int f = (int)((SDL_GetTicks() / TORCH_MS + (Uint32)(ax / 16 + ay / 16) * 2u) % (Uint32)nf);
    auto at = [&](int x, int y, int w, int h) {
        return SDL_Rect{ cam_px(cam, (float)(x * DMAP_TILE / 16)), cam_py(cam, (float)(y * DMAP_TILE / 16)), w * tsz / 16, h * tsz / 16 };
    };
    if (glow) {
        SDL_Rect src = { f * GLOW_G, i * GLOW_G, GLOW_G, GLOW_G }, dst = at(ax - 7, ay - 4, GLOW_G, GLOW_G);
        SDL_RenderCopy(ren, glow, &src, &dst);
    }
    SDL_Rect src = { f * 16, 0, 16, 32 }, dst = at(ax, ay, 16, 32);
    SDL_RenderCopy(ren, tex, &src, &dst);
}

// Where torches hang along a straight run of n wall cells: one for about every
// eight, spread evenly, each moved to the nearest cell within two that can
// take one (ok) -- no such cell, no torch. A run under three cells has none.
template <class Ok, class Put> static void torch_run(int n, Ok ok, Put put) {
    if (n < 3) return;
    const int k = std::max(1, (n + 4) / 8);
    for (int i = 0; i < k; i++) {
        const int c = (2 * i + 1) * n / (2 * k);
        for (int o : { 0, 1, -1, 2, -2 })
            if (c + o >= 0 && c + o < n && ok(c + o)) { put(c + o); break; }
    }
}

static void draw_tile_art(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex,
                         int tx0, int ty0, int tx1, int ty1, int tsz) {
    const int blk = d->type == DUNGEON_ENT_RUINS ? WALL_RUINS : d->step_pyramid ? WALL_MAYA : WALL_EGYPT;
    const int c0 = WALL_COL0[blk], r0 = WALL_ROW0[blk];
    auto piece = [&](int col, int row, int sx, int sy) {
        SDL_Rect src = { (c0 + col) * 16, (r0 + row) * 16, 16, 16 }, dst = { sx, sy, tsz, tsz };
        SDL_RenderCopy(ren, tex, &src, &dst);
    };
    auto ground = [&](int tx, int ty, int sx, int sy) {       // the block's floor, laid by where the tile is (WALL_FLOOR)
        const int* f = WALL_FLOOR[blk];
        piece(f[0] + tx % f[2], f[1] + ty % f[3], sx, sy);
    };
    for (int ty = ty0; ty < ty1; ty++)
        for (int tx = tx0; tx < tx1; tx++) {
            int sx = cam_px(cam, tx * DMAP_TILE), sy = cam_py(cam, ty * DMAP_TILE);
            uint8_t a = d->art[ty][tx], p = d->art_p[ty][tx];
            switch (a) {
                case WA_FLOOR:  ground(tx, ty, sx, sy); break;
                case WA_BACK:   piece(PYR_FACE_BACK + tx % 6, p, sx, sy); break;
                case WA_BAND:                                // the ruins' picked per face, the pyramids' by phase
                    piece(PYR_FACE_CORR + (blk == WALL_RUINS ? p >> 4 : tx % 6), p & 15, sx, sy);
                    break;
                case WA_SIDE_L:
                case WA_SIDE_R: piece(PYR_SIDE_COL, PYR_RIM_ROW, sx, sy); break;
                case WA_DIAG_L:
                case WA_DIAG_R:
                    ground(tx, ty, sx, sy);
                    piece(PYR_SIDE_COL + (a == WA_DIAG_L ? 1 : 2), PYR_RIM_ROW, sx, sy);
                    break;
                case WA_END_L:
                case WA_END_R:  piece(PYR_SIDE_COL + (a == WA_END_L ? 3 : 4), PYR_RIM_ROW, sx, sy); break;
                case WA_FLIGHT: {
                    int row = p & 15, kind = (p >> 4) & 3, dir = (p >> 6) & 1, ipar = p >> 7;
                    piece(PYR_FLIGHT_COL + dir * 3 + kind, row, sx, sy);
                    if (row >= 1 && row <= 5)
                        piece(PYR_FWALL_COL + dir * 12 + (tx % 6) * 2 + ipar, row, sx, sy);
                    break;
                }
                default: {                                   // the rim, a quarter at a time --
                    if (blk != WALL_RUINS) break;            // the ruins' only: the pyramid has no perimeter outline (user)
                    static const int Q[4][4] = { {0, 0, -1, -1}, {8, 0, 1, -1}, {0, 8, -1, 1}, {8, 8, 1, 1} };
                    for (const int* q : Q) {
                        bool h = art_open(d, tx + q[2], ty), v = art_open(d, tx, ty + q[3]);
                        bool dg = art_open(d, tx + q[2], ty + q[3]);
                        int k = (h && v) ? 0 : h ? 1 : v ? 2 : dg ? 3 : -1;   // outer, vedge, hedge, inner
                        if (k < 0) continue;
                        int qx = q[0] * tsz / 16, qy = q[1] * tsz / 16;
                        SDL_Rect src = { (c0 + PYR_RIM_COL + k) * 16 + q[0], (r0 + PYR_RIM_ROW) * 16 + q[1], 8, 8 };
                        SDL_Rect dst = { sx + qx, sy + qy, q[0] ? tsz - qx : tsz / 2, q[1] ? tsz - qy : tsz / 2 };
                        SDL_RenderCopy(ren, tex, &src, &dst);
                    }
                    break;
                }
            }
            if (d->tiles[ty][tx] == DNG_FLOOR)
                for (int li = 0; li < d->num_loot; li++) {
                    const DungeonLoot& lo = d->loot[li];
                    if (!lo.collected && lo.tx == tx && lo.ty == ty)
                        draw_loot(ren, lo, sx, sy, tsz);
                }
        }

    // the ruins' torches (user: fire), as drawn: along each straight run of faces, in
    // the middle of a face's height -- on a whole face between two whole ones
    // (not a cracked one, or one with a block fallen out), clear of a doorway
    if (SDL_Texture* torch = blk == WALL_RUINS ? torch_tex(ren, Flame{}) : nullptr) {
        // one glow serves them all: a torch only hangs on a whole face between
        // two whole ones, so the wall behind each is the same three by three
        static SDL_Texture* glow = nullptr;
        static SDL_Renderer* glow_ren = nullptr;
        if (SDL_Surface* sh = !glow || glow_ren != ren ? sheet_pixels() : nullptr) {
            glow = torch_glow_tex(ren, 1, [&](int, int x, int y) {       // the cell's corner is 7 left of the torch's, 12 down the face
                return *(const uint32_t*)((const uint8_t*)sh->pixels + ((r0 + (y + 4) / 16) * 16 + (y + 4) % 16) * sh->pitch +
                                          ((c0 + PYR_FACE_CORR) * 16 + (x + 9) % 16) * 4);
            });
            glow_ren = ren;
        }
        auto top = [&](int x, int y) { return x >= 0 && x < DMAP_W && d->art[y][x] == WA_BAND && !(d->art_p[y][x] & 15); };
        for (int ty = std::max(ty0 - 2, 0); ty < ty1; ty++)
            for (int tx = tx0; tx < tx1; tx++) {
                if (!top(tx, ty)) continue;
                int x0 = tx, n = 1;
                while (top(x0 - 1, ty)) x0--;
                while (top(x0 + n, ty)) n++;
                torch_run(n, [&](int i) {
                    for (int q = 0; q < d->num_portals; q++)
                        if (abs(d->portals[q].tx - (x0 + i)) <= 2 && abs(d->portals[q].ty - (ty + 2)) <= 2) return false;
                    for (int o = -1; o <= 1; o++)
                        if (i + o < 0 || i + o >= n || d->art_p[ty][x0 + i + o] >> 4) return false;
                    return true;
                }, [&](int i) { if (x0 + i == tx) draw_torch(cam, ren, torch, glow, 0, tx * 16, ty * 16 + 8, tsz); });
            }
    }

    // the pieces laid whole: a chamber's mural (Mayan; the gate scene where it
    // has a doorway), then the carved stones and cartouches
    auto decal = [&](const DungeonDecal& dc) {
        SDL_Rect src = { dc.sx, dc.sy, dc.w, dc.h };
        SDL_Rect dst = { cam_px(cam, dc.x * DMAP_TILE / 16), cam_py(cam, dc.y * DMAP_TILE / 16),
                         dc.w * tsz / 16, dc.h * tsz / 16 };
        SDL_RenderCopyEx(ren, tex, &src, &dst, 0.0, nullptr, dc.flip ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);
    };
    if (blk == WALL_MAYA)
        for (int i = 0; i < d->num_pyr_rooms; i++) {
            int cx = d->pyr_rooms[i].cx, yb = d->pyr_rooms[i].yb;
            bool doorway = false;
            for (int p = 0; p < d->num_portals; p++)
                if (d->portals[p].tx == cx && d->portals[p].ty == yb) doorway = true;
            int m = doorway ? PYR_MURALS - 1 : (int)(pyr_hash((uint32_t)cx, (uint32_t)yb) % (PYR_MURALS - 1));
            decal({ (int16_t)((c0 + PYR_MURAL_COL + m * 7) * 16), (int16_t)(r0 * 16), PYR_MURAL_W, PYR_MURAL_H,
                    (cx - PYR_BW / 2) * 16, (yb - 3) * 16, false });
        }
    for (int i = 0; i < d->num_decals; i++) decal(d->decals[i]);

    // a black line down the join of a corridor face and a chamber's side
    // wall (the user's rule; not at a flight's ends, which the user had
    // taken out)
    int lw = tsz / 16 > 0 ? tsz / 16 : 1;
    for (int ty = ty0; ty < ty1; ty++)
        for (int tx = tx0 + 1; tx < tx1 - 1; tx++) {
            uint8_t a = d->art[ty][tx];
            if (a != WA_SIDE_L && a != WA_SIDE_R && a != WA_DIAG_L && a != WA_DIAG_R) continue;
            int sx = cam_px(cam, tx * DMAP_TILE), sy = cam_py(cam, ty * DMAP_TILE);
            fc_draw_color(ren, 0, 0, 0, 255);
            for (int side = -1; side <= 1; side += 2)
                if (d->art[ty][tx + side] == WA_BAND) {
                    SDL_Rect r = { side < 0 ? sx : sx + tsz - lw, sy, lw, tsz };
                    SDL_RenderFillRect(ren, &r);
                }
        }
}

// ── STONEHENGE: drawing the barrow ───────────────────────────────────────
//
// The maze's picture is composited once, the first time it is drawn, from the
// pieces gen_dungeon_wall_tiles.py baked (WALL_BARROW), the way the approved
// mock-up made it: every block back to front, each face sampled by where it
// is (the front by (X, z), the side by (d, z), the top plain grass), a carving
// on one plain stone in three or so (rarely the eye); then the black line on
// the walls' outline, where faces meet, and where a near wall stands before a
// far one; then the overworld grass's bunches, each laid only where all of it
// lands on top -- never sliced by an edge (user). It is drawn a tile at a time
// over a sky that scrolls at half the camera's speed, its stars twinkling (user).

static SDL_Surface* sheet_pixels() {
    static SDL_Surface* s = nullptr;
    if (!s) {
        if (SDL_Surface* raw = IMG_Load("assets/tileset.png")) {
            s = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
            SDL_FreeSurface(raw);
        }
    }
    return s;
}

struct BarrowArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture *lit = nullptr;
    int tw = 0, th = 0;
    std::vector<uint8_t> has;                     // a tile with any of the picture on it
    int w = 0, h = 0;
    std::vector<uint32_t> px;                     // the picture's pixels, and each one's ground
    std::vector<int16_t> dep;                     // depth (-1: none) -- for drawing walls over the player
};
static BarrowArt s_barrow;

static void barrow_bake(const DungeonMap* d, SDL_Renderer* ren) {
    uint32_t key = d->barrow_seed * 2654435761u ^ (uint32_t)d->num_barrow_blocks ^ 1u;
    for (int p = 0; p < d->num_portals; p++) key = key * 31u + (uint32_t)(d->portals[p].tx * 977 + d->portals[p].ty);
    if (s_barrow.key == key && s_barrow.ren == ren && s_barrow.lit) return;
    SDL_Surface* sh = sheet_pixels();
    if (!sh) return;
    if (s_barrow.lit) SDL_DestroyTexture(s_barrow.lit);
    s_barrow = BarrowArt();

    const int c0 = WALL_COL0[WALL_BARROW] * 16, r0 = WALL_ROW0[WALL_BARROW] * 16;
    auto sheet = [&](int x, int y) -> uint32_t {
        const uint8_t* p = (const uint8_t*)sh->pixels + y * sh->pitch + x * 4;
        if (p[0] == 255 && p[1] == 0 && p[2] == 0) return 0;      // the colour key
        return (uint32_t)p[0] | p[1] << 8 | p[2] << 16 | 0xFF000000u;
    };
    const int X0 = d->barrow_x0, Y0 = d->barrow_y0, W = d->barrow_w + 16, H = d->barrow_h + 16;
    const int OX = d->barrow_ox, OY = d->barrow_oy;
    std::vector<int8_t> rank(W * H, -1);
    std::vector<int16_t> dep(W * H, 0);
    std::vector<uint32_t> col(W * H, 0);
    auto put = [&](int sx, int sy, int r, int dd, uint32_t c) {
        int x = sx - X0, y = sy - Y0;
        if (x < 0 || y < 0 || x >= W || y >= H || !c) return;
        rank[y * W + x] = (int8_t)r; dep[y * W + x] = (int16_t)dd; col[y * W + x] = c;
    };
    const uint32_t grass = sheet(c0 + BARROW_GRASS_COL * 16, r0 + BARROW_GRASS_ROW * 16);

    // the blocks, back to front: the far row first, west to east
    std::vector<int> order(d->num_barrow_blocks);
    for (int i = 0; i < d->num_barrow_blocks; i++) order[i] = i;
    std::sort(order.begin(), order.end(), [&](int a, int b) {
        if (d->barrow_blocks[a].d != d->barrow_blocks[b].d) return d->barrow_blocks[a].d > d->barrow_blocks[b].d;
        return d->barrow_blocks[a].x < d->barrow_blocks[b].x;
    });
    for (int i : order) {
        int x0 = d->barrow_blocks[i].x, bd = d->barrow_blocks[i].d;
        for (int z = 0; z < BRW_BZ; z++)                                  // the front
            for (int X = x0; X < x0 + BRW_BW; X++)
                put(OX + X + bd, OY - bd - z - 1, 1, bd,
                    sheet(c0 + BARROW_FRONT_COL * 16 + X % 96, r0 + 63 - z));
        // a carving on its upper course: on the plain block of the three (no
        // crack or root through it), one in three; rarely, the eye
        uint32_t h = pyr_hash((uint32_t)x0 * 7919u + d->barrow_seed, (uint32_t)bd);
        int ci = (x0 % 96) ? -1 : (h % 60 == 0) ? 4 : (h % 3 == 0) ? (int)((h >> 8) % 4) : -1;
        if (ci >= 0)
            for (int cy = 0; cy < 24; cy++)
                for (int cx = 0; cx < 24; cx++)
                    put(OX + x0 + 4 + cx + bd, OY - bd - (58 - cy) - 1, 1, bd,
                        sheet(c0 + BARROW_CARVE_COL * 16 + (ci % 4) * 24 + cx, r0 + (ci / 4) * 24 + cy));
        for (int dd = bd; dd < bd + BRW_BD; dd++) {
            for (int z = 0; z < BRW_BZ; z++)                              // the side
                put(OX + x0 + BRW_BW + dd, OY - dd - z - 1, 2, dd,
                    sheet(c0 + BARROW_SIDE_COL * 16 + dd % 48, r0 + 63 - z));
            for (int X = x0; X < x0 + BRW_BW; X++)                        // the top
                put(OX + X + dd, OY - dd - BRW_BZ - 1, 0, dd, grass);
        }
    }

    // the black line: on the outline, where faces meet (the top's front, the
    // side's corner), and where one wall stands before another (the farther)
    std::vector<uint32_t> out(W * H, 0);
    std::vector<uint8_t> plain(W * H, 0);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            int k = y * W + x;
            if (rank[k] < 0) continue;
            bool line = false;
            const int nx[4] = {x + 1, x - 1, x, x}, ny[4] = {y, y, y + 1, y - 1};
            for (int n = 0; n < 4; n++) {
                if (nx[n] < 0 || ny[n] < 0 || nx[n] >= W || ny[n] >= H || rank[ny[n] * W + nx[n]] < 0) { line = true; continue; }
                int q = ny[n] * W + nx[n];
                if (rank[q] != rank[k]) line |= rank[k] > rank[q];
                else if (abs(dep[q] - dep[k]) > 1) line |= dep[k] > dep[q];
            }
            out[k] = line ? 0xFF000000u : col[k];
            plain[k] = !line && rank[k] == 0 && col[k] == grass;
        }

    // the grass's bunches, whole: each only where all of it lands on plain top,
    // a pixel clear of the others; some gathered into thick patches
    struct Px { int8_t x, y; uint32_t c; };
    std::vector<std::vector<Px>> bunch(BARROW_BUNCHES);
    for (int b = 0; b < BARROW_BUNCHES; b++)
        for (int y = 0; y < 16; y++)
            for (int x = 0; x < 16; x++)
                if (uint32_t c = sheet(c0 + (BARROW_BUNCH_COL + b) * 16 + x, r0 + y))
                    bunch[b].push_back({ (int8_t)x, (int8_t)y, c });
    std::vector<uint8_t> used(W * H, 0);
    uint32_t rs = d->barrow_seed | 1;
    auto lay = [&](const std::vector<Px>& sp, int ox, int oy) {
        for (const Px& p : sp) {
            int x = ox + p.x, y = oy + p.y;
            if (x < 1 || y < 1 || x >= W - 1 || y >= H - 1 || !plain[y * W + x]) return false;
            for (int j = -1; j <= 1; j++)
                for (int i = -1; i <= 1; i++)
                    if (used[(y + j) * W + x + i]) return false;
        }
        for (const Px& p : sp) { out[(oy + p.y) * W + ox + p.x] = p.c; used[(oy + p.y) * W + ox + p.x] = 1; }
        return true;
    };
    for (int ty = 0; ty < H / 16; ty++)
        for (int tx = 0; tx < W / 16; tx++) {
            int r = (int)(rng_next(&rs) % 10);
            if (r < 2) {
                int cx = tx * 16 + (int)(rng_next(&rs) % 16), cy = ty * 16 + (int)(rng_next(&rs) % 16);
                for (int t = 0; t < 40; t++)
                    lay(bunch[rng_next(&rs) % BARROW_BUNCHES],
                        cx + (int)(rng_next(&rs) % 24) - 14, cy + (int)(rng_next(&rs) % 14) - 8);
            } else if (r < 5) {
                const std::vector<Px>& sp = bunch[rng_next(&rs) % BARROW_BUNCHES];
                for (int t = 0; t < 30; t++)
                    if (lay(sp, tx * 16 + (int)(rng_next(&rs) % 16), ty * 16 + (int)(rng_next(&rs) % 16))) break;
            }
        }

    // the ways out that have a portal: a ladder in the middle of the flat back
    // wall, from its foot up the whole face to the grass
    for (int w = 0; w < 2; w++) {
        int bd = d->barrow_way_d[w], yf = OY - bd;
        int ptx, pty;
        barrow_way_tile(d, w, &ptx, &pty);
        bool stands = false;
        for (int p = 0; p < d->num_portals; p++) stands |= d->portals[p].tx == ptx && d->portals[p].ty == pty;
        if (!stands) continue;
        int lx = OX + d->barrow_way_x[w] - 8 + bd;
        for (int z = 0; z < BRW_BZ; z++)
            for (int i = 0; i < 16; i++) {
                int cy = z < 16 ? LADDER_ROW + 1 : LADDER_ROW;
                uint32_t c = sheet(LADDER_COL0 * 16 + i, cy * 16 + 15 - z % 16);
                int x = lx + i - X0, y = OY - bd - 1 - z - Y0;
                if (!c || x < 0 || y < 0 || x >= W || y >= H) continue;
                if (rank[y * W + x] >= 0 && dep[y * W + x] < bd) continue;   // behind something nearer
                out[y * W + x] = c; rank[y * W + x] = 1; dep[y * W + x] = (int16_t)bd;
            }
    }

    warn_treasure_covered(d, X0, Y0, W, H, rank);
    SDL_Surface* lit = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    if (!lit) return;
    s_barrow.tw = W / 16 + 1; s_barrow.th = H / 16 + 1;
    s_barrow.has.assign(s_barrow.tw * s_barrow.th, 0);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            uint32_t c = rank[y * W + x] >= 0 ? out[y * W + x] : 0;
            ((uint32_t*)((uint8_t*)lit->pixels + y * lit->pitch))[x] = c;
            if (c) s_barrow.has[(y / 16) * s_barrow.tw + x / 16] = 1;
        }
    s_barrow.w = W; s_barrow.h = H;
    s_barrow.px.assign(W * H, 0);
    s_barrow.dep.assign(W * H, -1);
    for (int i = 0; i < W * H; i++)
        if (rank[i] >= 0) { s_barrow.px[i] = out[i]; s_barrow.dep[i] = dep[i]; }
    s_barrow.lit = SDL_CreateTextureFromSurface(ren, lit);
    SDL_FreeSurface(lit);
    if (s_barrow.lit) SDL_SetTextureBlendMode(s_barrow.lit, SDL_BLENDMODE_BLEND);
    s_barrow.key = key; s_barrow.ren = ren;
}

static inline int floordiv(int a, int b) { return a >= 0 ? a / b : -((-a + b - 1) / b); }

// Small lights behind a picture, at half the camera's speed: one in about
// `one_in` 16 px cells, a third of them twinkling between their two shapes --
// a 2 x 2 at (sx, sy) of `tex` and a 3 x 3 cross four to its right. The
// barrow's stars, and the glints in a cave's dark.
static void draw_twinkles(const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex, int sx, int sy, int tsz, uint32_t one_in) {
    int offx = cam->ox / 2, offy = cam->oy / 2;
    Uint32 now = SDL_GetTicks();
    for (int j = floordiv(offy, tsz); j * tsz - offy < cam->screen_h; j++)
        for (int i = floordiv(offx, tsz); i * tsz - offx < cam->screen_w; i++) {
            uint32_t h = pyr_hash((uint32_t)i * 92821u, (uint32_t)j * 68917u);
            if (h % one_in) continue;
            int kind = (h >> 4) & 1;
            if ((h >> 7) % 3 == 0) kind ^= (int)((now / 700 + (h >> 9)) & 1);
            int ox = 2 + (int)((h >> 12) % 11), oy = 2 + (int)((h >> 16) % 11);
            SDL_Rect src = kind ? SDL_Rect{ sx + 4, sy, 3, 3 } : SDL_Rect{ sx, sy, 2, 2 };
            SDL_Rect dst = { i * tsz - offx + ox * tsz / 16, j * tsz - offy + oy * tsz / 16,
                             src.w * tsz / 16, src.h * tsz / 16 };
            SDL_RenderCopy(ren, tex, &src, &dst);
        }
}

// The sky behind it all, floor and void alike: half the camera's speed, a
// star in about one sky cell of five, a third of them twinkling between their
// two shapes; and the cryptids' constellations, one in a stretch of sky in
// three (user: parallax, twinkle).
static void draw_barrow_sky(const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex, int tsz) {
    const int c0 = WALL_COL0[WALL_BARROW] * 16, r0 = WALL_ROW0[WALL_BARROW] * 16;
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
    SDL_RenderFillRect(ren, &all);
    int offx = cam->ox / 2, offy = cam->oy / 2;
    int big = 48 * tsz, bigh = 32 * tsz;                          // a stretch of sky, a constellation's
    for (int J = floordiv(offy, bigh); J * bigh - offy < cam->screen_h; J++)
        for (int I = floordiv(offx, big); I * big - offx < cam->screen_w; I++) {
            uint32_t h = pyr_hash((uint32_t)I * 40503u, (uint32_t)J * 9973u);
            if (h % 3) continue;
            int k = (int)((h >> 4) % BARROW_CONSTS);
            SDL_Rect src = { c0 + (BARROW_CONST_COL + 6 * k) * 16, r0, 96, 64 };
            SDL_Rect dst = { I * big - offx + (int)((h >> 8) % 32) * tsz, J * bigh - offy + (int)((h >> 16) % 24) * tsz,
                             6 * tsz, 4 * tsz };
            SDL_RenderCopy(ren, tex, &src, &dst);
        }
    draw_twinkles(cam, ren, tex, c0 + BARROW_STAR_COL * 16, r0, tsz, 5);
}

static void draw_barrow(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex,
                        int tx0, int ty0, int tx1, int ty1, int tsz) {
    barrow_bake(d, ren);
    draw_barrow_sky(cam, ren, tex, tsz);
    if (!s_barrow.lit) return;
    int bx0 = d->barrow_x0 / 16, by0 = d->barrow_y0 / 16;
    for (int ty = ty0; ty < ty1; ty++)
        for (int tx = tx0; tx < tx1; tx++) {
            int ix = tx - bx0, iy = ty - by0;
            int sx = cam_px(cam, tx * DMAP_TILE), sy = cam_py(cam, ty * DMAP_TILE);
            bool in = ix >= 0 && iy >= 0 && ix < s_barrow.tw && iy < s_barrow.th && s_barrow.has[iy * s_barrow.tw + ix];
            if (in) {
                SDL_Rect src = { tx * 16 - d->barrow_x0, ty * 16 - d->barrow_y0, 16, 16 };
                SDL_Rect dst = { sx, sy, tsz, tsz };
                SDL_RenderCopy(ren, s_barrow.lit, &src, &dst);
            }
            if (d->tiles[ty][tx] == DNG_FLOOR)
                for (int li = 0; li < d->num_loot; li++) {
                    const DungeonLoot& lo = d->loot[li];
                    if (!lo.collected && lo.tx == tx && lo.ty == ty) draw_loot(ren, lo, sx, sy, tsz);
                }
        }
}

// ── Graveyard: the picture ───────────────────────────────────────────────
// The walkways composited once, as the mock-up drew them (graveyard_design.py
// for the pieces): each top its swatch read in the oblique view, (x + y, y);
// red brick and boardwalk by stretches along the path, cut every 260-519
// pixels; within 56 of a cut each 16 x 8 cell (running bond -- a plank's
// depth, so planks and bricks share the grid) is plank or brick by a hash
// against how far into the board's side it is, so the planks thin out cell by
// cell into the brick. Straight under each top's edge its slab face, 8 deep --
// south where the world in front of the edge is empty, else east, in shade --
// then what hangs below. A black line round each top, and where a south face
// turns east. Each way out: a wall across the back of its landing in the
// landing's material, a ladder up it to a small graveyard, the doorway to a
// large. The brick underside's roots are kept apart: they sway, each moved
// whole, drawn every frame (draw_graveyard).
struct GywArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture* tex = nullptr;
    int w = 0, h = 0;
    std::vector<uint8_t> occ;                     // tops, faces, walls: what hides a root swung behind it
    struct Root { int16_t x, y, j; int col; uint32_t c; };
    std::vector<Root> roots;
    struct Wall { int g, x, y; bool ladder; };    // a way out, drawn again over the player behind it
    std::vector<Wall> walls;
};
static GywArt s_gyw;
static const int GYW_T = 8, GYW_HANG = 24;
static const int GYW_DOOR_COL = 28, GYW_DOOR_ROW = 14;   // way_out_door's GRAVE, 1 x 2

static void graveyard_bake(const DungeonMap* d, SDL_Renderer* ren) {
    uint32_t key = d->gyw_seed ^ (uint32_t)d->num_gyw_rects * 7919u;
    for (int p = 0; p < d->num_portals; p++)
        key = key * 31u + (uint32_t)(d->portals[p].tx * 977 + d->portals[p].ty) * 131u + (uint32_t)d->portals[p].ow_type;
    if (s_gyw.key == key && s_gyw.ren == ren && s_gyw.tex) return;
    SDL_Surface* sh = sheet_pixels();
    if (!sh) return;
    if (s_gyw.tex) SDL_DestroyTexture(s_gyw.tex);
    s_gyw = GywArt();

    const int c0 = WALL_COL0[WALL_GRAVEYARD] * 16, r0 = WALL_ROW0[WALL_GRAVEYARD] * 16;
    auto sheet = [&](int x, int y) -> uint32_t {
        const uint8_t* p = (const uint8_t*)sh->pixels + y * sh->pitch + x * 4;
        if (p[0] == 255 && p[1] == 0 && p[2] == 0) return 0;      // the colour key
        return (uint32_t)p[0] | p[1] << 8 | p[2] << 16 | 0xFF000000u;
    };
    auto piece = [&](int g, int x, int y) {
        return sheet(c0 + GY_PIECE[g].col * 16 + x, r0 + GY_PIECE[g].row * 16 + y);
    };
    const int X0 = d->gyw_x0, Y0 = d->gyw_y0, W = d->gyw_w, H = d->gyw_h, OX = d->gyw_ox, OY = d->gyw_oy;
    const uint32_t BLACK = 0xFF000000u, EARTH = 0xFF123749u;   // 493712, the plank gap's
    std::vector<uint8_t> fl(W * H, 0);
    for (int i = 0; i < d->num_gyw_rects; i++) {                 // the floor, each rectangle projected
        const auto& r = d->gyw_rects[i];
        for (int v = r.v0; v <= r.v1; v++)
            for (int u = r.u0; u <= r.u1; u++) {
                int x = OX + u + v - X0, y = OY - v - Y0;
                if (x >= 0 && y >= 0 && x < W && y < H) fl[y * W + x] = 1;
            }
    }
    auto FL = [&](int x, int y) { return x >= 0 && y >= 0 && x < W && y < H && fl[y * W + x]; };

    // how far along the path each top pixel is, and the stretches
    enum { BRICK = 0, BOARD = 1 };
    std::vector<float> cuts;
    std::vector<int> seq;
    uint32_t rs = d->gyw_seed;
    seq.push_back((int)(rng_next(&rs) & 1));
    for (float t = 0; t < d->gyw_total;) {
        t += 260 + (float)(rng_next(&rs) % 260);
        cuts.push_back(t); seq.push_back(1 - seq.back());
    }
    std::vector<int8_t> mat(W * H, -1), other(W * H, -1);
    std::vector<float> sdist(W * H, 1e9f);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            if (!fl[y * W + x]) continue;
            int v = OY - (Y0 + y), u = X0 + x - OX - v;
            float best = 1e9f, arc = 0;
            for (int i = 0; i < d->num_gyw_segs; i++) {
                const auto& sg = d->gyw_segs[i];
                float vx = sg.bx - sg.ax, vy = sg.by - sg.ay, L2 = vx * vx + vy * vy;
                float t = L2 > 0 ? ((u - sg.ax) * vx + (v - sg.ay) * vy) / L2 : 0;
                t = t < 0 ? 0 : t > 1 ? 1 : t;
                float ex = u - sg.ax - t * vx, ey = v - sg.ay - t * vy, dd = ex * ex + ey * ey;
                if (dd < best) { best = dd; arc = sg.arc + t * sqrtf(L2); }
            }
            int idx = (int)(std::lower_bound(cuts.begin(), cuts.end(), arc) - cuts.begin());
            float before = idx > 0 ? arc - cuts[idx - 1] : 1e9f;
            float after = idx < (int)cuts.size() ? cuts[idx] - arc : 1e9f;
            mat[y * W + x] = (int8_t)seq[idx];
            other[y * W + x] = (int8_t)(before < after ? seq[idx > 0 ? idx - 1 : 0] : seq[idx + 1 < (int)seq.size() ? idx + 1 : idx]);
            sdist[y * W + x] = before < after ? before : after;
        }
    // the join, by whole cells
    std::vector<int8_t> fm(W * H, -1);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            int i = y * W + x;
            if (!fl[i]) continue;
            int gx = X0 + x, gy = Y0 + y, row = gy >> 3, odd = row & 1;
            int col = floordiv(gx + gy + 8 * odd, 16);
            int cy = row * 8 + 4 - Y0, cx = col * 16 - 8 * odd + 8 - (row * 8 + 4) - X0;
            int ci = FL(cx, cy) ? cy * W + cx : i;
            float f = sdist[ci] / 56.0f; if (f > 1) f = 1;
            float pb = mat[ci] == BOARD ? (other[ci] == BRICK ? 0.5f + 0.5f * f : 1.0f)
                                        : (other[ci] == BOARD ? 0.5f - 0.5f * f : 0.0f);
            float h = (float)(((uint32_t)row * 73856093u ^ (uint32_t)col * 19349663u) % 1000u) / 1000.0f;
            fm[i] = h < pb ? BOARD : BRICK;
        }

    std::vector<uint32_t> out(W * H, 0);
    s_gyw.occ.assign(W * H, 0);
    // the brick underside's roots: below its black foot, column by column
    int root_top[64];
    for (int c = 0; c < 64; c++) {
        root_top[c] = 99;
        for (int y = 0; y < GYW_HANG; y++)
            if (piece(GY_UNDER_BRICK, c, y) == BLACK) { root_top[c] = y + 1; break; }
    }
    // straight down from each top: its face, then the hang
    std::vector<int8_t> side(W * H, -1);
    for (int x = 0; x < W; x++) {
        int last = -1000;
        for (int y = 0; y < H; y++) {
            if (fl[y * W + x]) { last = y; continue; }
            int k = y - last;
            if (k > GYW_T + GYW_HANG) continue;
            int ye = last, m = fm[ye * W + x], gx = X0 + x, gye = Y0 + ye;
            if (k <= GYW_T) {
                bool south = !FL(x - 1, ye + 1);
                side[y * W + x] = south ? 0 : 1;
                int g, c;
                if (m == BRICK) { g = south ? GY_FACE_BRICK_S : GY_FACE_BRICK_E;
                                  c = south ? (gx + gye - 8 * ((gye % 64) / 8 % 2)) & 63 : (63 - gye) & 63; }
                else            { g = south ? GY_FACE_BOARD_S : GY_FACE_BOARD_E;
                                  c = south ? gx & 63 : (62 - gye) & 63; }
                out[y * W + x] = piece(g, c, k - 1);
                s_gyw.occ[y * W + x] = 1;
            } else {
                int r = k - GYW_T - 1, c = gx & 63;
                uint32_t px = piece(m == BRICK ? GY_UNDER_BRICK : GY_UNDER_BOARD, c, r);
                if (!px) continue;
                if (m == BRICK && r >= root_top[c])
                    s_gyw.roots.push_back({ (int16_t)x, (int16_t)y, (int16_t)(r - root_top[c]), gx, px });
                else
                    out[y * W + x] = px;
            }
        }
    }
    for (int y = 0; y < H; y++)                          // a south face turning east: its edge
        for (int x = 1; x < W; x++)
            if (side[y * W + x] == 1 && side[y * W + x - 1] == 0) out[y * W + x] = BLACK;
    // the tops; a plank's end against a brick is its butt joint; the outline
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            int i = y * W + x;
            if (!fl[i]) continue;
            int gx = X0 + x, gy = Y0 + y;
            out[i] = piece(fm[i] == BRICK ? GY_TOP_BRICK : GY_TOP_BOARD, (gx + gy) & 63, gy & 63);
            if (fm[i] == BOARD && ((FL(x - 1, y) && fm[i - 1] == BRICK) || (FL(x + 1, y) && fm[i + 1] == BRICK)))
                out[i] = EARTH;
            if (!FL(x - 1, y) || !FL(x + 1, y) || !FL(x, y - 1) || !FL(x, y + 1)) out[i] = BLACK;
            s_gyw.occ[i] = 1;
        }
    // the ways out that stand: a wall in the landing's material, its fitting
    auto blit = [&](int g, int sx0, int sy0, int px0, int py0, int w, int h) {
        for (int yy = 0; yy < h; yy++)
            for (int xx = 0; xx < w; xx++) {
                int x = px0 + xx, y = py0 + yy;
                if (x < 0 || y < 0 || x >= W || y >= H) continue;
                uint32_t c = g >= 0 ? piece(g, sx0 + xx, sy0 + yy) : sheet(sx0 + xx, sy0 + yy);
                if (c) { out[y * W + x] = c; s_gyw.occ[y * W + x] = 1; }
            }
    };
    for (int w = 0; w < 2; w++) {
        int tx, ty, p = -1;
        gyw_way_tile(d, w, &tx, &ty);
        for (int q = 0; q < d->num_portals; q++)
            if (d->portals[q].tx == tx && d->portals[q].ty == ty) p = q;
        if (p < 0) continue;
        int vf = gyw_wall_v(d, w), sx = OX + gyw_wall_u(d, w) + vf - X0, sy = OY - vf - Y0;
        int g = FL(sx + 32, sy + 4) && fm[(sy + 4) * W + sx + 32] == BOARD ? GY_WALL_BOARD : GY_WALL_BRICK;
        bool ladder = d->portals[p].ow_type == DUNGEON_ENT_GRAVEYARD_SM;
        s_gyw.walls.push_back({ g, X0 + sx, Y0 + sy, ladder });
        blit(g, 0, 0, sx, sy - 63, 72, 64);
        if (ladder) {                                    // a length, a length, its foot: to the wall's top
            blit(GY_LADDER, 0, 0, sx + 24, sy - 47, 16, 16);
            blit(GY_LADDER, 0, 0, sx + 24, sy - 31, 16, 16);
            blit(GY_LADDER, 0, 16, sx + 24, sy - 15, 16, 16);
        } else {
            blit(-1, GYW_DOOR_COL * 16, GYW_DOOR_ROW * 16, sx + 24, sy - 31, 16, 32);
        }
    }

    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return;
    for (int y = 0; y < H; y++)
        memcpy((uint8_t*)surf->pixels + y * surf->pitch, &out[y * W], W * 4);
    s_gyw.tex = SDL_CreateTextureFromSurface(ren, surf);
    SDL_FreeSurface(surf);
    if (s_gyw.tex) SDL_SetTextureBlendMode(s_gyw.tex, SDL_BLENDMODE_BLEND);
    s_gyw.w = W; s_gyw.h = H; s_gyw.key = key; s_gyw.ren = ren;
}

// The dark behind the walkways: faint ghosts and wisps far off at a quarter of
// the camera's pace, skulls (turning, now and then) and loose bones nearer,
// twice the size, at half -- placed by a hash of their cell, as the barrow's
// stars are.
static void draw_graveyard_dark(const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex, int tsz) {
    const int c0 = WALL_COL0[WALL_GRAVEYARD] * 16, r0 = WALL_ROW0[WALL_GRAVEYARD] * 16;
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
    SDL_RenderFillRect(ren, &all);
    Uint32 now = SDL_GetTicks();
    for (int layer = 0; layer < 2; layer++) {
        int cell = (layer ? 64 : 96) * tsz / 16, scale = layer ? 2 : 1;
        int offx = layer ? cam->ox / 2 : cam->ox / 4, offy = layer ? cam->oy / 2 : cam->oy / 4;
        for (int J = floordiv(offy, cell) - 1; J * cell - offy < cam->screen_h; J++)
            for (int I = floordiv(offx, cell) - 1; I * cell - offx < cam->screen_w; I++) {
                uint32_t h = pyr_hash((uint32_t)I * 7919u + layer * 31u, (uint32_t)J * 104729u);
                if (h % 4) continue;
                int g;
                if (layer == 0) g = h % 8 < 4 ? GY_GHOST : GY_WISP;
                else if (h % 8 < 4) g = ((now / 900 + (h >> 9)) & 7) == 0 ? GY_SKULL1 : GY_SKULL0;
                else g = GY_BONE;
                const GyPiece& pc = GY_PIECE[g];
                SDL_Rect src = { c0 + pc.col * 16, r0 + pc.row * 16, pc.w, pc.h };
                int q = cell * 16 / tsz / 2;
                SDL_Rect dst = { I * cell - offx + (int)((h >> 4) % q) * tsz / 16,
                                 J * cell - offy + (int)((h >> 8) % q) * tsz / 16,
                                 pc.w * scale * tsz / 16, pc.h * scale * tsz / 16 };
                SDL_RenderCopy(ren, tex, &src, &dst);
            }
    }
}

static void draw_graveyard(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren, SDL_Texture* tex,
                           int tx0, int ty0, int tx1, int ty1, int tsz) {
    draw_graveyard_dark(cam, ren, tex, tsz);
    graveyard_bake(d, ren);
    if (!s_gyw.tex) return;
    int bx = cam_px(cam, (float)(d->gyw_x0 * DMAP_TILE / 16)), by = cam_py(cam, (float)(d->gyw_y0 * DMAP_TILE / 16));
    SDL_Rect dst = { bx, by, s_gyw.w * tsz / 16, s_gyw.h * tsz / 16 };
    SDL_RenderCopy(ren, s_gyw.tex, nullptr, &dst);
    // the roots, swaying: three poses, a second each round a three-second loop
    // (user: three frames, as the NES would); the top of each holds, its tip
    // swings 3; each pixel moved, never resampled, so none comes or goes
    // (user); hidden where it swings behind a nearer slab
    float t = (float)(SDL_GetTicks() / 1000u % 3u) / 3.0f;
    int px = tsz / 16 > 0 ? tsz / 16 : 1;
    std::vector<SDL_Rect> rects;
    uint32_t colour = 0;
    auto flush = [&]() {
        if (rects.empty()) return;
        fc_draw_color(ren, colour & 255, (colour >> 8) & 255, (colour >> 16) & 255, 255);
        SDL_RenderFillRects(ren, rects.data(), (int)rects.size());
        rects.clear();
    };
    for (const auto& r : s_gyw.roots) {
        int dx = (int)lroundf(3.0f * powf(r.j / 13.0f, 1.5f) * sinf(6.2831853f * t + r.col / 9.0f));
        int x = r.x + dx;
        if (x < 0 || x >= s_gyw.w || s_gyw.occ[r.y * s_gyw.w + x]) continue;
        if (r.c != colour) { flush(); colour = r.c; }
        rects.push_back({ bx + x * tsz / 16, by + r.y * tsz / 16, px, px });
    }
    flush();
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.collected || lo.tx < tx0 || lo.tx >= tx1 || lo.ty < ty0 || lo.ty >= ty1) continue;
        draw_loot(ren, lo, cam_px(cam, (float)(lo.tx * DMAP_TILE)), cam_py(cam, (float)(lo.ty * DMAP_TILE)), tsz);
    }
}

// ── Giant tree: the picture ──────────────────────────────────────────────
// Baked once from assets/tree_interior.png (art/structures/dungeon_walls/
// tree_design.py's swatches, 64 wide each), as the scratch tree_gen2.py mock
// draws it: column by column, bottom up -- the ground's face, then each floor
// that shows with the wall under its lip; every wall in the texture of the
// level each stretch of it stands on (user): heartwood up the trunk, soil
// below the ground line, deep soil further down; a wall on a 45-degree edge a
// tone down, its courses following the edge; a black line where a wall's
// plane turns. Shelf fungus floors above the way in, packed dirt from it down.
// Ladders, wood or root; the way out the overworld's hollow (way_out_door).
struct TreeArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture* tex = nullptr;
    SDL_Surface* sw = nullptr;                     // assets/tree_interior.png
};
static TreeArt s_tree;
enum { TS_HEART, TS_HEART_SH, TS_SOIL, TS_SOIL_SH, TS_DEEP, TS_DEEP_SH, TS_FUNGUS, TS_FUNGUS_LIP,
       TS_DIRT, TS_DIRT_LIP, TS_LADDER_WOOD, TS_LADDER_ROOT };

static void tree_bake(const DungeonMap* d, SDL_Renderer* ren) {
    uint32_t key = d->tree_seed ^ (uint32_t)d->tree_w * 7919u ^ (uint32_t)d->num_tree_ladders * 104729u;
    if (s_tree.key == key && s_tree.ren == ren && s_tree.tex) return;
    if (!s_tree.sw)
        if (SDL_Surface* raw = IMG_Load("assets/tree_interior.png")) {
            s_tree.sw = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
            SDL_FreeSurface(raw);
        }
    SDL_Surface* sh = sheet_pixels();
    if (!s_tree.sw || !sh) return;
    if (s_tree.tex) SDL_DestroyTexture(s_tree.tex);
    s_tree.tex = nullptr;

    const int W = d->tree_w, H = d->tree_h, N = d->tree_n, E = d->tree_e, Z = d->tree_z;
    const int FRONT_B = d->tree_b[N][0];
    const uint32_t BLACK = 0xFF000000u;
    auto sw = [&](int k, int x, int y) {
        return *(const uint32_t*)((const uint8_t*)s_tree.sw->pixels + y * s_tree.sw->pitch + (k * 64 + x) * 4);
    };
    auto wall_sw = [&](int t) { return t <= E ? TS_HEART : t <= E + 2 ? TS_SOIL : TS_DEEP; };
    std::vector<uint32_t> out((size_t)W * H, BLACK);
    std::vector<int> plane(H), prev(H, -1);
    for (int x = 0; x < W; x++) {
        std::fill(plane.begin(), plane.end(), -1);
        auto slope_of = [&](int t) { return x + 1 < W ? d->tree_b[t][x + 1] - d->tree_b[t][x] : 0; };
        // rows [y0, y1) of a wall standing on level t's back edge (base); a wall
        // climbing past levels of no depth stands on each in turn
        auto put_wall = [&](int y0, int y1, int t, int base, int slope) {
            int s = t;
            for (int y = std::min(H, y1) - 1; y >= std::max(0, y0); y--) {
                while (s >= 0 && y < d->tree_b[s][x] - Z) s--;
                int k = y >= FRONT_B ? wall_sw(N) : s < 0 ? TS_HEART : wall_sw(s);
                int ph = y - base, sx = (x + 23 * t) % 64;
                if (k == TS_HEART) {                       // the grain runs up: each 64 column slides, knots off the grid
                    ph += (int)(((uint64_t)(x / 64) * 2654435761ull >> 7) % 64);
                    sx = x % 64;
                }
                out[(size_t)y * W + x] = sw(k + (slope ? 1 : 0), sx, (ph % 64 + 64) % 64);
                plane[y] = t * 4 + (slope ? 1 + (slope > 0) : 0);
            }
        };
        put_wall(FRONT_B, H, N, FRONT_B, 0);               // the ground's face, in front of everything
        int bf = FRONT_B, tf = N;
        for (int t = N - 1; t >= 0; t--) {
            int b = d->tree_b[t][x], f = d->tree_b[t + 1][x] - Z;
            if (f - b < 1) continue;
            put_wall(f, bf, tf, bf, slope_of(tf));
            int fl = t < E ? TS_FUNGUS : TS_DIRT, lip = t < E ? TS_FUNGUS_LIP : TS_DIRT_LIP;
            for (int y = std::max(0, f); y < std::min(H, f + 8); y++)
                out[(size_t)y * W + x] = sw(lip, x % 64, y - f);   // the floor's front edge, on the wall's top
            for (int y = b; y < f; y++)
                out[(size_t)y * W + x] = sw(fl, x % 64, (y - b + 7 * t) % 64);
            if (b >= 1) out[(size_t)(b - 1) * W + x] = BLACK;     // where the floor meets the wall behind
            bf = b; tf = t;
        }
        put_wall(0, bf - 1, tf, bf, slope_of(tf));         // above the top level its wall rises on
        if (bf >= 1 && tf < N) out[(size_t)(bf - 1) * W + x] = BLACK;
        if (x > 0)                                         // a line where a wall's plane turns
            for (int y = 0; y < H; y++)
                if (plane[y] >= 0 && prev[y] >= 0 && plane[y] != prev[y]) out[(size_t)y * W + x] = BLACK;
        std::swap(plane, prev);
    }
    for (int i = 0; i < d->num_tree_ladders; i++) {
        const auto& l = d->tree_ladders[i];
        for (int y = std::max(0, (int)l.y0); y < std::min(H, (int)l.y1); y++)
            for (int k = 0; k < 16; k++)
                out[(size_t)y * W + l.x0 + k] = sw(l.root ? TS_LADDER_ROOT : TS_LADDER_WOOD, k, y % 8 + 8);
    }
    if (const WayOutDoor* door = way_out_door(d))          // the hollow, its foot on the floor's back edge:
        for (int p = 0; p < std::min(1, d->num_portals); p++) {   // the way in, the only way out
            int px0 = d->portals[p].tx * 16 - d->tree_ox, py1 = d->portals[p].ty * 16 - d->tree_oy;
            int sx0 = door->col * 16, sy0 = (door->foot - door->h + 1) * 16;
            for (int y = 0; y < door->h * 16; y++)
                for (int x = 0; x < door->w * 16; x++) {
                    int ox = px0 + x, oy = py1 - door->h * 16 + y;
                    const uint8_t* s = (const uint8_t*)sh->pixels + (sy0 + y) * sh->pitch + (sx0 + x) * 4;
                    if ((s[0] == 255 && s[1] == 0 && s[2] == 0) || s[3] == 0) continue;   // the colour key
                    if (ox >= 0 && oy >= 0 && ox < W && oy < H) out[(size_t)oy * W + ox] = *(const uint32_t*)s;
                }
        }

    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return;
    for (int y = 0; y < H; y++)
        memcpy((uint8_t*)surf->pixels + y * surf->pitch, &out[(size_t)y * W], W * 4);
    s_tree.tex = SDL_CreateTextureFromSurface(ren, surf);
    SDL_FreeSurface(surf);
    s_tree.key = key; s_tree.ren = ren;
}

static void draw_tree(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren,
                      int tx0, int ty0, int tx1, int ty1, int tsz) {
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
    SDL_RenderFillRect(ren, &all);
    tree_bake(d, ren);
    if (s_tree.tex) {
        SDL_Rect dst = { cam_px(cam, (float)(d->tree_ox * DMAP_TILE / 16)), cam_py(cam, (float)(d->tree_oy * DMAP_TILE / 16)),
                         d->tree_w * tsz / 16, d->tree_h * tsz / 16 };
        SDL_RenderCopy(ren, s_tree.tex, nullptr, &dst);
    }
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.collected || lo.tx < tx0 || lo.tx >= tx1 || lo.ty < ty0 || lo.ty >= ty1) continue;
        draw_loot(ren, lo, cam_px(cam, (float)(lo.tx * DMAP_TILE)), cam_py(cam, (float)(lo.ty * DMAP_TILE)), tsz);
    }
}

// ── Caves: the picture ───────────────────────────────────────────────────
// Baked once from the cave's block of the sheet (the 16 x 16 pieces of
// art/structures/dungeon_walls/cave_rock_design.py, in its ore's tones), as
// cave_terrace_mock.py lays it: a whole cell at a time, never a texture bent
// to an edge (user). The terraces' edges are level or at 45 degrees and meet
// the 16px grid at a cell's corners or its middle, so each of a cell's four
// quarters -- the triangles its diagonals cut -- is wholly rock or not, and one
// piece serves each way they can fall. Rock over the dark hangs ragged; the
// floor is the material's flat fill; the mouths' arches and the ladders (the
// dungeons' own, in the ore's colour) go on top. What is dark stays clear, for
// the ore's glints to show through (draw_cave).
struct CaveArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture *tex = nullptr, *glint = nullptr;  // the picture; the dark's two glints, as draw_twinkles reads them
    SDL_Texture* glow = nullptr;                   // its torches' glows, a row each (torch_glow_tex)
    int misfits = 0;                               // cells whose quarters no piece fits: none, by the terraces' rules
    std::vector<SDL_Point> torches;                // each torch's cell, in the picture
};
// A cave's flame, by its ore (user): fire in stone and bronze, white in emerald
// and veyrite, black fire in dravium and kharvite, a rainbow in reality shard.
static Flame cave_flame(const DungeonMap* d) {
    static const uint32_t WHITE[1][3] = { { 0xfcfcfc, 0xdcf0ff, 0xbcbeca } };
    static const uint32_t BLACK[1][3] = { { 0x000000, 0x181224, 0x9797aa } };      // black to its heart, a pale rim to be seen by
    static const uint32_t RAINBOW[6][3] = { { 0xec8476, 0xb70000, 0x7c0a1b }, { 0xf0b890, 0xfc9838, 0xb6433d },   // the pale tone is the stripe's
                                            { 0xfae488, 0xf0bc3c, 0xc9a433 }, { 0xa8f0bc, 0x4edc4a, 0x058f3a },
                                            { 0x84a7e9, 0x5c94fc, 0x2850a0 }, { 0xb69cee, 0x664b95, 0x301b5a } };
    switch (cave_material_index(d)) {
        case MAT_EMERALD: case MAT_VEYRITE:  return { WHITE, 1 };
        case MAT_DRAVIUM: case MAT_KHARVITE: return { BLACK, 1 };
        case MAT_REALITY_SHARD:              return { RAINBOW, 6 };
        default:                             return {};
    }
}
static CaveArt s_cave;
int dungeon_cave_misfits() { return s_cave.misfits; }

// The piece for a cell some of whose quarters are rock: bit 0 the top quarter,
// 1 the bottom, 2 the left, 3 the right.
static int cave_quarter_piece(int rock) {
    switch (rock) {
        case 1 | 4:     return CP_FOOT_UP;     case 2 | 8:     return CP_TOP_UP;
        case 1 | 8:     return CP_FOOT_DOWN;   case 2 | 4:     return CP_TOP_DOWN;
        case 1 | 2 | 4: return CP_TIP_L;       case 1 | 2 | 8: return CP_TIP_R;
        case 2 | 4 | 8: return CP_VALLEY;      case 1 | 4 | 8: return CP_VAULT;
        case 2:         return CP_PEAK;        case 1:         return CP_FANG;
        default:        return -1;
    }
}

// How a piece of wall stands (user: "make it obvious which is a corner tile and
// whats a straight up and down tile"): 0 a level run, facing you; -1 / 1 a
// sloped run, turned away, rising / falling to the right; 2 a turn's own piece.
static int cave_piece_lean(int p) {
    switch (p) {
        case CP_FACE0: case CP_FACE1: case CP_FACE2: case CP_TOP_FLAT: case CP_FOOT_FLAT: case CP_HANG_FLAT: return 0;
        case CP_LEAN_UP: case CP_TOP_UP: case CP_FOOT_UP: case CP_HANG_UP: return -1;
        case CP_LEAN_DOWN: case CP_TOP_DOWN: case CP_FOOT_DOWN: case CP_HANG_DOWN: return 1;
        default: return 2;
    }
}

static void cave_bake(const DungeonMap* d, SDL_Renderer* ren) {
    const int mat = cave_material_index(d);
    uint32_t key = d->tree_seed ^ (uint32_t)d->tree_w * 7919u ^ (uint32_t)d->num_tree_ladders * 104729u ^
                   (uint32_t)(mat + 1) * 2654435761u;
    for (int p = 0; p < d->num_portals; p++)
        key = key * 31u + (uint32_t)(d->portals[p].tx * 131 + d->portals[p].ty) * 2u + cave_ladder_out(d, p);
    if (s_cave.key == key && s_cave.ren == ren && s_cave.tex) return;
    SDL_Surface* sh = sheet_pixels();
    if (!sh) return;
    if (s_cave.tex) SDL_DestroyTexture(s_cave.tex);
    if (s_cave.glint) SDL_DestroyTexture(s_cave.glint);
    if (s_cave.glow) SDL_DestroyTexture(s_cave.glow);
    s_cave.tex = s_cave.glint = s_cave.glow = nullptr;

    const int W = d->tree_w, H = d->tree_h, N = d->tree_n, Z = d->tree_z, C = 16;
    const int bx = cave_block_col(d) * C;
    auto sheet = [&](int x, int y) { return *(const uint32_t*)((const uint8_t*)sh->pixels + y * sh->pitch + x * 4); };
    auto clear = [](uint32_t c) {                          // the sheet's colour key
        const uint8_t* s = (const uint8_t*)&c;
        return (s[0] == 255 && s[1] == 0 && s[2] == 0) || s[3] == 0;
    };
    auto rgba = [](uint8_t r, uint8_t g, uint8_t b) { uint32_t c; const uint8_t s[4] = { r, g, b, 255 }; memcpy(&c, s, 4); return c; };
    // what a pixel is: rock behind a floor (on up to the top of the map, and
    // hanging under the lowest floor's edge), floor, or the dark
    enum { DARK, ROCK, FLOOR };
    auto cls = [&](int x, int y) {
        if (x < 0 || x >= W || y >= H) return (int)DARK;
        if (y < d->tree_b[0][x]) return (int)ROCK;
        for (int t = 0; t < N; t++) {
            if (y >= d->tree_b[t][x] && y < d->tree_b[t + 1][x] - Z) return (int)FLOOR;
            if (y >= d->tree_b[t][x] - Z && y < d->tree_b[t][x]) return (int)ROCK;
        }
        const int front = d->tree_b[N][x] - Z;
        return y >= front && y < front + CAVE_UNDER ? (int)ROCK : (int)DARK;
    };
    // the floor (user: "somewhat similar to the cave wall texture"): the wall's
    // own cobble as it is drawn there, lying flat -- its stones the ore's
    // ground colour, the dark between them the ground's lines -- laid by where
    // a pixel is in the world, so it runs on unbroken from floor to floor. A
    // rounded ground is CAVE_COBBLE instead (user: "the other stone texture";
    // of four shown, the large rounded cobbles), read at (x + y, y) -- the
    // oblique view, as the pyramids' floors are read
    const MaterialDef& md = cave_material(d);
    const uint32_t ground_px = rgba(md.ground.r, md.ground.g, md.ground.b);
    const uint32_t line_px = rgba(md.ground_line.r, md.ground_line.g, md.ground_line.b);
    auto floor_line = [&](int x, int y) {                  // is a pixel of the picture on one of the floor's lines
        const int wx = d->tree_ox + x, wy = d->tree_oy + y;
        if (md.ground_rounded) {
            const int u = (wx + wy) % CAVE_COBBLE_W;
            return (CAVE_COBBLE[wy % CAVE_COBBLE_H][u / 8] >> u % 8 & 1) != 0;
        }
        return sheet(bx + CAVE_PIECE[CP_FACE0][0] * C + wx % C, CAVE_PIECE[CP_FACE0][1] * C + wy % C) == rgba(0, 0, 0);
    };
    std::vector<uint32_t> out((size_t)W * H, 0);
    std::vector<uint8_t> isfloor((size_t)W * H, 0);        // a pixel showing floor: laid as floor, nothing drawn over it
    auto put = [&](int sx, int sy, int w, int h, int ox, int oy) {   // the sheet's (sx, sy), w x h, onto the picture
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                uint32_t c = sheet(sx + x, sy + y);
                if (!clear(c) && ox + x >= 0 && oy + y >= 0 && ox + x < W && oy + y < H) {
                    out[(size_t)(oy + y) * W + ox + x] = c;
                    isfloor[(size_t)(oy + y) * W + ox + x] = 0;
                }
            }
    };
    auto piece = [&](int p, int cx, int cy) { put(bx + CAVE_PIECE[p][0] * C, CAVE_PIECE[p][1] * C, C, C, cx, cy); };
    // how the band the rock at (x, y) is in runs across its cell: its foot (and
    // its top, parallel) rising to the right (-1), falling (1), or level
    auto lean = [&](int x, int y) {
        int t = 0;
        if (y >= d->tree_b[0][x])
            while (t < N && !(y >= d->tree_b[t][x] - Z && y < d->tree_b[t][x])) t++;
        const int x0 = x - x % C, dy = d->tree_b[t][std::min(x0 + C - 1, W - 1)] - d->tree_b[t][x0];
        return dy >= 12 ? 1 : dy <= -12 ? -1 : 0;
    };
    const int cw = W / C, ch = H / C;
    std::vector<int8_t> kind((size_t)cw * ch, 2);          // each cell's cave_piece_lean
    std::vector<uint8_t> hang((size_t)cw * ch, 0);         // a face cell: 1 a torch may hang on it, 2 not (a gem, a ladder, a mouth)
    auto cover = [&](int x, int y, int w, int h) {         // what is drawn over the rock: no torch there,
        for (int gy = std::max(y / C, 0); gy < ch && gy * C < y + h; gy++)                // nor a cell either side
            for (int gx = std::max(x / C - 1, 0); gx < cw && gx * C < x + w + C; gx++)
                if (hang[(size_t)gy * cw + gx]) hang[(size_t)gy * cw + gx] = 2;
    };
    s_cave.misfits = 0;
    for (int cy = 0; cy + C <= H; cy += C)
        for (int cx = 0; cx + C <= W; cx += C) {
            const int t = cls(cx + 8, cy + 3), b = cls(cx + 8, cy + 12), l = cls(cx + 3, cy + 8), r = cls(cx + 12, cy + 8);
            const int rock = (t == ROCK) | (b == ROCK) << 1 | (l == ROCK) << 2 | (r == ROCK) << 3;
            // the ground first: the floor, and under a piece's clear edge the
            // floor it stands by (a level top's is the cell's above)
            uint8_t cl[16][16];
            bool ground = false;
            for (int y = 0; y < C; y++)
                for (int x = 0; x < C; x++) ground = ((cl[y][x] = (uint8_t)cls(cx + x, cy + y)) == FLOOR) || ground;
            if (!ground && rock == 15)
                for (int x = 0; x < C && !ground; x++) ground = cls(cx + x, cy - 1) == FLOOR;
            for (int y = 0; y < C; y++)
                for (int x = 0; x < C; x++)
                    if (cl[y][x] == FLOOR || (ground && cl[y][x] == ROCK)) {
                        out[(size_t)(cy + y) * W + cx + x] = floor_line(cx + x, cy + y) ? line_px : ground_px;
                        isfloor[(size_t)(cy + y) * W + cx + x] = 1;
                    }
            int p = -1;                                    // the cell's piece of wall, if it has one
            if (rock == 15) {
                const int up = cls(cx + 8, cy - C + 12), down = cls(cx + 8, cy + C + 3);
                const int way = lean(cx + 8, cy + 8), k = (int)(pyr_hash((uint32_t)cx, (uint32_t)cy) % 10);
                p = up != ROCK ? CP_TOP_FLAT : down == DARK ? CP_HANG_FLAT : down != ROCK ? CP_FOOT_FLAT
                    : way < 0 ? CP_LEAN_UP : way > 0 ? CP_LEAN_DOWN
                    : k == 0 ? CP_FACE2 : k < 4 ? CP_FACE1 : CP_FACE0;     // a gem in one cell in ten
            } else if (rock) {
                p = cave_quarter_piece(rock);
                if (b == DARK && p == CP_FOOT_UP) p = CP_HANG_UP;          // over the dark a foot hangs ragged
                if (b == DARK && p == CP_FOOT_DOWN) p = CP_HANG_DOWN;
                if (p < 0) s_cave.misfits++;
            } else if (t == FLOOR && b == FLOOR && l == FLOOR && r == FLOOR &&
                       pyr_hash((uint32_t)cx * 5u + 1u, (uint32_t)cy) % 60 == 0) {
                piece(CP_FLOOR1, cx, cy);                                  // a stalagmite, now and then
            }
            if (p >= 0) {
                piece(p, cx, cy);
                kind[(size_t)(cy / C) * cw + cx / C] = (int8_t)cave_piece_lean(p);
                hang[(size_t)(cy / C) * cw + cx / C] = p == CP_FACE0 || p == CP_FACE1 ? 1 : p == CP_FACE2 ? 2 : 0;
            }
        }
    // the corner where a front turns to a side: a black line down it, as the
    // bible has for a front meeting a side
    for (int gy = 0; gy < H / C; gy++)
        for (int gx = 0; gx < cw; gx++) {
            const int k = kind[(size_t)gy * cw + gx], cx = gx * C, cy = gy * C;
            auto turns = [&](int nx, int ny) {
                if (nx >= cw || ny >= H / C) return false;
                const int n = kind[(size_t)ny * cw + nx];
                return k != 2 && n != 2 && n != k;
            };
            if (turns(gx + 1, gy))
                for (int y = 0; y < C; y++)
                    if (cls(cx + C - 1, cy + y) == ROCK && cls(cx + C, cy + y) == ROCK)
                        out[(size_t)(cy + y) * W + cx + C - 1] = rgba(0, 0, 0), isfloor[(size_t)(cy + y) * W + cx + C - 1] = 0;
            if (turns(gx, gy + 1))
                for (int x = 0; x < C; x++)
                    if (cls(cx + x, cy + C - 1) == ROCK && cls(cx + x, cy + C) == ROCK)
                        out[(size_t)(cy + C - 1) * W + cx + x] = rgba(0, 0, 0), isfloor[(size_t)(cy + C - 1) * W + cx + x] = 0;
        }
    for (int p = 0; p < d->num_portals; p++) {             // the mouths, each its foot on its floor's back edge
        const int x = d->portals[p].tx * 16 - d->tree_ox, y = d->portals[p].ty * 16 - d->tree_oy;
        if (!cave_ladder_out(d, p)) {                      // an arch
            put(bx + CAVE_PIECE[CP_ARCH][0] * C, CAVE_PIECE[CP_ARCH][1] * C, 2 * C, 2 * C, x, y - 2 * C);
            cover(x, y - 2 * C, 2 * C, 2 * C);
            continue;
        }
        cover(x, y - CAVE_HATCH_UP * C, C, CAVE_HATCH_UP * C);
        piece(CP_HATCH, x, y - CAVE_HATCH_UP * C);         // a ladder up to its hatch
        for (int k = 1; k < CAVE_HATCH_UP; k++)
            put((LADDER_COL0 + mat) * C, (k == 1 ? LADDER_ROW + 1 : LADDER_ROW) * C, C, C, x, y - k * C);
    }
    for (int i = 0; i < d->num_tree_ladders; i++) {        // the ladders: lengths, and the foot on the floor
        const auto& l = d->tree_ladders[i];
        for (int y = l.y0; y < l.y1; y += C)
            put((LADDER_COL0 + mat) * C, (y + C >= l.y1 ? LADDER_ROW + 1 : LADDER_ROW) * C, C, C, l.x0, y);
        cover(l.x0, l.y0, C, l.y1 - l.y0);
    }
    // where the quiet floor meets the walls' black (user: "find a way to make
    // the transitions between the pure black of the walls and the more sutle
    // floors work"): a shadow along every wall. Within 3 px of anything that
    // is not floor, the floor is a tone down -- its stones the line colour,
    // its lines black. Not a black ground, which has no tone to fall to.
    if (ground_px != rgba(0, 0, 0)) {
        std::vector<uint8_t> near(isfloor.size());
        for (size_t k = 0; k < near.size(); k++) near[k] = !isfloor[k];
        for (int step = 0; step < 3; step++) {
            std::vector<uint8_t> grown = near;
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++) {
                    const size_t k = (size_t)y * W + x;
                    if ((x > 0 && near[k - 1]) || (x + 1 < W && near[k + 1]) || (y > 0 && near[k - W]) || (y + 1 < H && near[k + W])) grown[k] = 1;
                }
            near.swap(grown);
        }
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
                if (isfloor[(size_t)y * W + x] && near[(size_t)y * W + x]) out[(size_t)y * W + x] = floor_line(x, y) ? rgba(0, 0, 0) : line_px;
    }
    // the torches (user): on the rock that faces you, never the turned --
    // along each level run of face cells of one height, in the middle of that
    // height, by torch_run
    s_cave.torches.clear();
    auto rows = [&](int gx, int gy) {                      // the face cells down from this one, where a run of them starts
        if (gx >= cw || !hang[(size_t)gy * cw + gx] || (gy > 0 && hang[(size_t)(gy - 1) * cw + gx])) return 0;
        int m = 0;
        while (gy + m < ch && hang[(size_t)(gy + m) * cw + gx]) m++;
        return m;
    };
    for (int gy = 0; gy < ch; gy++)
        for (int gx = 0, n; gx < cw; gx += n) {
            const int m = rows(gx, gy);
            for (n = 1; m >= 2 && rows(gx + n, gy) == m; n++) {}
            if (m < 2) continue;
            const int y = gy * C + (m - 2) * C / 2;        // its cell is 32 tall
            torch_run(n, [&](int i) {
                for (int j = y / C; j <= (y + 2 * C - 1) / C; j++)
                    if (hang[(size_t)j * cw + gx + i] != 1) return false;
                return true;
            }, [&](int i) { s_cave.torches.push_back({ (gx + i) * C, y }); });
        }
    if (!s_cave.torches.empty() && torch_tex(ren, cave_flame(d)))        // their glows: on rock only, never the floor or the dark
        s_cave.glow = torch_glow_tex(ren, (int)s_cave.torches.size(), [&](int i, int x, int y) {
            const int px = s_cave.torches[i].x - 7 + x, py = s_cave.torches[i].y - 4 + y;
            return cls(px, py) == ROCK && py >= 0 ? out[(size_t)py * W + px] : 0u;
        });

    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Surface* gl = SDL_CreateRGBSurfaceWithFormat(0, 8, 4, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf || !gl) { if (surf) SDL_FreeSurface(surf); if (gl) SDL_FreeSurface(gl); return; }
    for (int y = 0; y < H; y++)
        memcpy((uint8_t*)surf->pixels + y * surf->pitch, &out[(size_t)y * W], W * 4);
    // the dark's glints (user: "just glints of the material color"), in the
    // rock's own two tones: the gem's lit one, the lightest in the gem's face,
    // and the rock's base, the lightest in a plain face -- a 2 x 2 of the lit,
    // and a cross of it with the base for arms
    auto lightest = [&](int p) {
        uint32_t best = 0;
        int lum = -1;
        for (int y = 0; y < C; y++)
            for (int x = 0; x < C; x++) {
                uint32_t c = sheet(bx + CAVE_PIECE[p][0] * C + x, CAVE_PIECE[p][1] * C + y);
                const uint8_t* s = (const uint8_t*)&c;
                const int l = s[0] * 299 + s[1] * 587 + s[2] * 114;
                if (!clear(c) && l > lum) { lum = l; best = c; }
            }
        return best;
    };
    const uint32_t lit = lightest(CP_FACE2), base = lightest(CP_FACE0);
    SDL_FillRect(gl, nullptr, 0);
    auto dot = [&](int x, int y, uint32_t c) { *(uint32_t*)((uint8_t*)gl->pixels + y * gl->pitch + x * 4) = c; };
    dot(0, 0, lit); dot(1, 0, lit); dot(0, 1, lit); dot(1, 1, lit);
    dot(5, 1, lit); dot(5, 0, base); dot(4, 1, base); dot(6, 1, base); dot(5, 2, base);
    s_cave.tex = SDL_CreateTextureFromSurface(ren, surf);
    s_cave.glint = SDL_CreateTextureFromSurface(ren, gl);
    SDL_FreeSurface(surf);
    SDL_FreeSurface(gl);
    if (s_cave.tex) SDL_SetTextureBlendMode(s_cave.tex, SDL_BLENDMODE_BLEND);
    if (s_cave.glint) SDL_SetTextureBlendMode(s_cave.glint, SDL_BLENDMODE_BLEND);
    s_cave.key = key; s_cave.ren = ren;
}

static void draw_cave(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren,
                      int tx0, int ty0, int tx1, int ty1, int tsz) {
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
    SDL_RenderFillRect(ren, &all);
    cave_bake(d, ren);
    SDL_Rect dst = { cam_px(cam, (float)(d->tree_ox * DMAP_TILE / 16)), cam_py(cam, (float)(d->tree_oy * DMAP_TILE / 16)),
                     d->tree_w * tsz / 16, d->tree_h * tsz / 16 };
    SDL_Texture* sheet = tilemap_get_town_tex();
    const int bx = cave_block_col(d) * 16;
    // The dark below (user: not the game's sprites -- "just glints of the
    // material color"): glints in the cave's own ore, scattered and twinkling
    // as the barrow's stars are. Only under the cave's own width, and only
    // where the picture is clear: below the ledge.
    if (s_cave.glint) {
        SDL_Rect clip = { dst.x, dst.y, dst.w, cam->screen_h - dst.y };
        SDL_RenderSetClipRect(ren, &clip);
        draw_twinkles(cam, ren, s_cave.glint, 0, 0, tsz, 6);
        SDL_RenderSetClipRect(ren, nullptr);
    }
    if (s_cave.tex) SDL_RenderCopy(ren, s_cave.tex, nullptr, &dst);
    if (SDL_Texture* torch = s_cave.torches.empty() ? nullptr : torch_tex(ren, cave_flame(d)))
        for (int i = 0; i < (int)s_cave.torches.size(); i++)
            draw_torch(cam, ren, torch, s_cave.glow, i, d->tree_ox + s_cave.torches[i].x, d->tree_oy + s_cave.torches[i].y, tsz);
    if (sheet)                                             // the crystals to mine, each on its tile
        for (int i = 0; i < d->dungeon_rocks.count; i++) {
            const ResourceNode& n = d->dungeon_rocks.nodes[i];
            if (!n.alive) continue;
            SDL_Rect src = { bx + 4 * 16, 0, 16, 16 }, to = { cam_px(cam, n.x), cam_py(cam, n.y), tsz, tsz };
            SDL_RenderCopy(ren, sheet, &src, &to);
        }
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.collected || lo.tx < tx0 || lo.tx >= tx1 || lo.ty < ty0 || lo.ty >= ty1) continue;
        draw_loot(ren, lo, cam_px(cam, (float)(lo.tx * DMAP_TILE)), cam_py(cam, (float)(lo.ty * DMAP_TILE)), tsz);
    }
}

// ── Catacombs: the picture ───────────────────────────────────────────────
// The area the player is in, baked as the approved mock-ups drew it
// (art/structures/dungeon_walls/catacombs_design.py for the swatches, copied
// to assets/catacombs.png, a view every 128 across): the floor each world
// pixel's swatch, flagstones in the hall, the graveyard's brick below; every
// wall pixel a column ZW tall -- its +v face where nothing of the wall is in
// front of it (or an inside corner), its +u face in shade, a cut's face square
// to the screen -- and its top, the nearest written last; black where faces
// meet, round the silhouette, and where one wall stands before another. On
// each cut: an enemy's window, the church's door, the 16 x 16 ladder; the
// ladder holes on the hall's floor.
struct CatArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture* tex = nullptr;
    SDL_Surface* sw = nullptr;                    // assets/catacombs.png
    int area = -1, w = 0, h = 0;
    std::vector<uint32_t> px;                     // the walls' pixels and each one's
    std::vector<int16_t> dep;                     // depth (-1: none), for drawing them over the player
};
static CatArt s_cat;
enum { CS_BRICK, CS_BONES, CS_FLAGS, CS_ASHLAR, CS_ASHLAR_SIDE, CS_CAP, CS_PANE0 };
static const int CAT_DEPTH0 = 32000;              // a pixel's depth: CAT_DEPTH0 - (u + v), less is nearer

static void cat_bake(const DungeonMap* d, int a, SDL_Renderer* ren) {
    uint32_t key = d->cat_seed * 2654435761u ^ (uint32_t)(a + 1) * 7919u;
    if (s_cat.key == key && s_cat.ren == ren && s_cat.tex) return;
    if (!s_cat.sw)
        if (SDL_Surface* raw = IMG_Load("assets/catacombs.png")) {
            s_cat.sw = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
            SDL_FreeSurface(raw);
        }
    SDL_Surface* sh = sheet_pixels();
    if (!s_cat.sw || !sh) return;
    if (s_cat.tex) SDL_DestroyTexture(s_cat.tex);
    s_cat.tex = nullptr;

    const auto& A = d->cat_areas[a];
    const bool hall = a == 0;
    const int T = CAT_T, Z = cat_z(a), W = A.x1 - A.x0, H = A.y1 - A.y0;
    auto sw = [&](int k, int x, int y) {
        return *(const uint32_t*)((const uint8_t*)s_cat.sw->pixels + y * s_cat.sw->pitch + (k * 128 + x) * 4);
    };
    auto sheet = [&](int x, int y) -> uint32_t {
        const uint8_t* p = (const uint8_t*)sh->pixels + y * sh->pitch + x * 4;
        return p[0] == 255 && p[1] == 0 && p[2] == 0 ? 0 : *(const uint32_t*)p;   // the colour key
    };
    auto rgb = [](uint32_t c) { return 0xFF000000u | ((c & 255) << 16) | (c & 0xFF00) | (c >> 16 & 255); };
    auto pmod = [](int x, int m) { return ((x % m) + m) % m; };
    const uint32_t BLACK = 0xFF000000u;
    // the bones' +u face a tone down
    auto shade = [&](uint32_t c) {
        static const uint32_t FROM[3] = { 0xb2966a, 0x8d6b4f, 0x34343e }, TO[3] = { 0x8d6b4f, 0x595965, 0x292931 };
        for (int i = 0; i < 3; i++) if (c == rgb(FROM[i])) return rgb(TO[i]);
        return c;
    };

    // the world round this area's floor
    int umin = 1 << 30, vmin = 1 << 30, umax = 0, vmax = 0;
    for (int i = A.r0; i < A.r1; i++) {
        const auto& r = d->cat_rects[i];
        umin = std::min(umin, (int)r.u0); vmin = std::min(vmin, (int)r.v0);
        umax = std::max(umax, (int)r.u1); vmax = std::max(vmax, (int)r.v1);
    }
    umin -= T + 4; vmin -= T + 4; umax += T + 4; vmax += T + 4;
    const int NU = umax - umin, NV = vmax - vmin;
    enum { FW = 1, FP = 2, BAND = 4, FACE_ON = 8, CORNER = 16, BEHIND = 32, GROWN = 64 };
    std::vector<uint8_t> g(NU * NV, 0);
    auto at = [&](int u, int v) -> uint8_t& { return g[(v - vmin) * NU + (u - umin)]; };
    auto has = [&](int u, int v, int f) { return u >= umin && v >= vmin && u < umax && v < vmax && (at(u, v) & f); };
    for (int i = A.r0; i < A.r1; i++) {
        const auto& r = d->cat_rects[i];
        for (int v = r.v0; v < r.v1; v++)
            for (int u = r.u0; u < r.u1; u++) at(u, v) |= FW;
    }
    for (int i = 0; i < d->num_cat_cuts; i++) {
        const auto& c = d->cat_cuts[i];
        if (c.area != a) continue;
        int cc = c.u0 + c.v0 + c.k;
        for (int v = c.v0 - T - 2; v <= c.v0 + c.k; v++)
            for (int u = c.u0 - T - 2; u <= c.u0 + c.k; u++) {
                int s = u + v;
                uint8_t& f = at(u, v);
                if (s < cc && s >= cc - CAT_TC && ((f & FW) || (u >= c.u0 - T && v >= c.v0 - T))) f |= CORNER;
                if (s < cc && s >= cc - 2 && (f & FW)) f |= FACE_ON;
                if (s < cc - CAT_TC) f |= BEHIND;
            }
    }
    for (auto& f : g) if ((f & FW) && !(f & (CORNER | BEHIND))) f |= FP;
    // the walls: within T of the floor (a square round it), not floor -- one
    // thickness everywhere -- and each cut's; none behind a cut
    {
        std::vector<uint8_t> row(NU * NV, 0);
        for (int v = vmin; v < vmax; v++) {
            int run = -1 << 20;                                  // the last floor pixel along u, then the next
            for (int u = umin; u < umax; u++) { if (at(u, v) & FP) run = u; if (u - run <= T) row[(v - vmin) * NU + u - umin] = 1; }
            run = 1 << 20;
            for (int u = umax - 1; u >= umin; u--) { if (at(u, v) & FP) run = u; if (run - u <= T) row[(v - vmin) * NU + u - umin] = 1; }
        }
        for (int u = umin; u < umax; u++) {
            int run = -1 << 20;
            for (int v = vmin; v < vmax; v++) { if (row[(v - vmin) * NU + u - umin]) run = v; if (v - run <= T) at(u, v) |= GROWN; }
            run = 1 << 20;
            for (int v = vmax - 1; v >= vmin; v--) { if (row[(v - vmin) * NU + u - umin]) run = v; if (run - v <= T) at(u, v) |= GROWN; }
        }
    }
    for (auto& f : g)
        if ((((f & GROWN) && !(f & FP)) || (f & CORNER)) && !(f & BEHIND)) f |= BAND;

    std::vector<uint32_t> out(W * H, 0);
    std::vector<int8_t> rank(W * H, -1);
    std::vector<int32_t> dep(W * H, -1);
    std::vector<uint8_t> fl(W * H, 0);
    auto SX = [&](int u, int v) { return u - v + A.ox - A.x0; };
    auto SY = [&](int u, int v) { return (u + v) / 2 + A.oy - A.y0; };
    auto blit = [&](int x0, int y0, int w, int h, auto pix, int dp) {   // dp >= 0: a wall's, at that depth
        for (int j = 0; j < h; j++)
            for (int i = 0; i < w; i++) {
                uint32_t c = pix(i, j);
                int x = x0 + i, y = y0 + j;
                if (!(c >> 24) || x < 0 || y < 0 || x >= W || y >= H) continue;
                out[y * W + x] = c;
                if (dp >= 0) { rank[y * W + x] = 3; dep[y * W + x] = dp; }
            }
    };

    for (int v = vmin; v < vmax; v++)
        for (int u = umin; u < umax; u++) {
            if (!(at(u, v) & FP)) continue;
            int x = SX(u, v), y = SY(u, v);
            if (x < 0 || y < 0 || x >= W || y >= H) continue;
            out[y * W + x] = sw(hall ? CS_FLAGS : CS_BRICK, pmod(u, 64), pmod(v, 64));
            fl[y * W + x] = 1;
        }
    for (int h = 0; hall && h < d->num_cat_holes; h++) {                 // the ladder holes, flat on the floor
        const auto& o = d->cat_holes[h];
        blit(SX(o.u, o.v) - 8, SY(o.u, o.v) - 8, 16, 16, [&](int i, int j) { return sheet(i, 14 * 16 + j); }, -1);
    }

    auto put = [&](int x, int y, int dp, int rk, uint32_t c) {
        if (x < 0 || y < 0 || x >= W || y >= H) return;
        int k = y * W + x;
        if (rank[k] >= 0 && (long)dp * 4 + (3 - rk) < (long)dep[k] * 4 + (3 - rank[k])) return;   // something nearer
        out[k] = c; rank[k] = (int8_t)rk; dep[k] = dp;
    };
    auto face = [&](int u, int v) {                    // the face a wall cell shows: 1 its +v, 2 its +u, 3 face-on
        if (!has(u, v, BAND)) return 0;
        if (at(u, v) & FACE_ON) return 3;
        bool eu = !has(u + 1, v, BAND);
        return !has(u, v + 1, BAND) || (!has(u + 1, v + 1, BAND) && !eu) ? 1 : eu ? 2 : 0;
    };
    // A section's skulls (user: to the interior bible -- laid whole, never
    // sheared, never sliced by an edge): along each straight run of a face as
    // many as fit whole, 16 apart, centred; on a face-on wall either side of
    // its ladder. Per cell: the column of the bones' picture it shows, and
    // how many rows it sits below its skull's first column -- taken back out
    // when it is drawn, so a skull stands upright on a slanted wall while
    // the bone courses lean with it.
    // The sections take two walls in turn, so one catacomb is told from the next
    // (user): odd ones a row of skulls over courses of long bones, even ones
    // skulls all the way down -- the left and right half of the bones' picture.
    const int bones_x = a % 2 ? 0 : 64, skull_rows = a % 2 ? 24 : 48;   // its skull courses: 24 tall each, from the top
    std::vector<int16_t> skull(hall ? 0 : NU * NV, -1);
    if (!hall) {
        auto lay = [&](int n, auto cell) {                               // a run of n cells, cell(t) its t-th
            int k = n / 16, off = (n - 16 * k) / 2;
            for (int t = 0; t < 16 * k; t++) {
                auto [u, v] = cell(off + t);
                auto [us, vs] = cell(off + t / 16 * 16);
                skull[(v - vmin) * NU + u - umin] = (int16_t)(t % 64 | ((u + v) / 2 - (us + vs) / 2) << 6);
            }
        };
        for (int v = vmin; v < vmax; v++)
            for (int u = umin, n; u < umax; u += n + 1) {
                for (n = 0; face(u + n, v) == 1; n++) {}
                lay(n, [&](int t) { return std::make_pair(u + t, v); });
            }
        for (int u = umin; u < umax; u++)
            for (int v = vmin, n; v < vmax; v += n + 1) {
                for (n = 0; face(u, v + n) == 2; n++) {}
                lay(n, [&](int t) { return std::make_pair(u, v + t); });
            }
        for (int i = 0; i < d->num_cat_cuts; i++) {
            const auto& c = d->cat_cuts[i];
            if (c.area != a) continue;
            const int k = (c.k - 9) / 16, off = (c.k - 9 - 16 * k) / 2;   // a side of the ladder: c.k - 9 across
            for (int v = c.v0; v < c.v0 + c.k; v++)
                for (int u = c.u0; u < c.u0 + c.k; u++) {
                    int dx = u - v - (c.u0 - c.v0), t = (dx >= 0 ? dx - 8 : -dx - 9) - off;
                    if (face(u, v) == 3 && t >= 0 && t < 16 * k) skull[(v - vmin) * NU + u - umin] = (int16_t)(t % 64 | 3 << 6);
                }
        }
    }
    auto bones = [&](int col, int zr, int16_t sk) {                      // a section's wall, col along its face
        if (zr < skull_rows) {
            const int top = zr / 24 * 24, j = (sk >> 6) + zr - top - 8;  // the skull's row: 14 of them, 5 down its course
            return sk >= 0 && j >= 0 && j < 14 ? sw(CS_BONES, bones_x + (sk & 63), top + 5 + j) : sw(CS_BONES, bones_x, top);
        }
        return sw(CS_BONES, bones_x + pmod(col, 64), zr);
    };
    for (int v = vmin; v < vmax; v++)
        for (int u = umin; u < umax; u++) {
            const int f = face(u, v);
            if (!(at(u, v) & BAND)) continue;
            const int16_t sk = hall ? -1 : skull[(v - vmin) * NU + u - umin];
            int x = SX(u, v), y = SY(u, v), dp = u + v;
            for (int z = 0; z < Z; z++) {
                int zr = Z - 1 - z;
                if (f == 1) put(x, y - z, dp, 1, hall ? sw(CS_ASHLAR, pmod(u, 96), zr % 80) : bones(u, zr, sk));
                else if (f == 2) put(x, y - z, dp, 2, hall ? sw(CS_ASHLAR_SIDE, pmod(v, 48), zr % 80) : shade(bones(v, zr, sk)));
                else if (f == 3) put(x, y - z, dp, 3, hall ? sw(CS_ASHLAR, pmod(u - v, 96), zr % 80) : bones(u - v, zr, sk));
            }
            uint32_t top = hall ? ((u + v) / 2 % 16 ? rgb(0xc6ccda) : rgb(0x9797aa)) : rgb(0xb2966a);   // bone: the plain base
            put(x, y - Z, dp, 0, top);
        }
    // the lines: the silhouette, a top's edge over a face, where two faces
    // meet, and on the farther of two walls one before the other
    std::vector<uint8_t> line(W * H, 0);
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++) {
            int k = y * W + x, w = rank[k];
            if (w < 0) continue;
            static const int DX[4] = { 1, -1, 0, 0 }, DY[4] = { 0, 0, 1, -1 };
            for (int n = 0; n < 4 && !line[k]; n++) {
                int xx = x + DX[n], yy = y + DY[n];
                int r2 = xx < 0 || yy < 0 || xx >= W || yy >= H ? -1 : rank[yy * W + xx];
                int d2 = r2 < 0 ? 0 : dep[yy * W + xx];
                line[k] = r2 < 0 || (r2 != w && (w == 0 || (r2 > 0 && w > r2))) || (abs(d2 - dep[k]) > 2 && dep[k] < d2);
            }
        }
    for (int k = 0; k < W * H; k++) if (line[k]) out[k] = BLACK;
    if (!hall)                                                          // a section's floor edged in black
        for (int y = 1; y < H - 1; y++)
            for (int x = 1; x < W - 1; x++) {
                int k = y * W + x;
                if (fl[k] && rank[k] < 0 && !(fl[k - 1] && fl[k + 1] && fl[k - W] && fl[k + W])) out[k] = BLACK;
            }

    // on each cut, in the middle of its face: the door, an enemy's window
    // (its foot 8 up), the ladder from the floor to the wall's top
    int npanes = s_cat.sw->w / 128 - CS_PANE0, nwin = 0;
    std::vector<int> panes(std::max(npanes, 1));
    for (int i = 0; i < (int)panes.size(); i++) panes[i] = i;
    uint32_t prs = d->cat_seed;
    for (int i = (int)panes.size() - 1; i > 0; i--) std::swap(panes[i], panes[rng_next(&prs) % (uint32_t)(i + 1)]);
    for (int i = 0; i < d->num_cat_cuts; i++) {
        const auto& c = d->cat_cuts[i];
        if (c.area != a) continue;
        int cc = c.u0 + c.v0 + c.k, xc = c.u0 - c.v0 + A.ox - A.x0, base = (cc - 1) / 2 + A.oy - A.y0 + 1;
        if (c.kind == CAT_DOOR)
            blit(xc - 8, base - 48, 16, 48, [&](int x, int y) { return sheet(29 * 16 + x, 13 * 16 + y); }, cc - 1);
        else if (c.kind == CAT_WINDOW && npanes > 0) {
            int p = CS_PANE0 + panes[nwin++ % npanes];
            blit(xc - 32, base - 8 - 64, 64, 64, [&](int x, int y) { return sw(p, x, y); }, cc - 1);
        } else if (c.kind == CAT_LADDER)
            for (int k = 0; k < Z / 16; k++)                                // its foot, then lengths
                blit(xc - 8, base - 16 - 16 * k, 16, 16,
                     [&](int x, int y) { return sheet(LADDER_COL0 * 16 + x, (k ? LADDER_ROW : LADDER_ROW + 1) * 16 + y); }, cc - 1);
    }

    warn_treasure_covered(d, A.x0, A.y0, W, H, rank);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return;
    for (int y = 0; y < H; y++)
        memcpy((uint8_t*)surf->pixels + y * surf->pitch, &out[y * W], W * 4);
    s_cat.tex = SDL_CreateTextureFromSurface(ren, surf);
    SDL_FreeSurface(surf);
    if (s_cat.tex) SDL_SetTextureBlendMode(s_cat.tex, SDL_BLENDMODE_BLEND);
    s_cat.px.assign(W * H, 0);
    s_cat.dep.assign(W * H, -1);
    for (int k = 0; k < W * H; k++)
        if (rank[k] >= 0) { s_cat.px[k] = out[k]; s_cat.dep[k] = (int16_t)(CAT_DEPTH0 - dep[k]); }
    s_cat.w = W; s_cat.h = H; s_cat.area = a; s_cat.key = key; s_cat.ren = ren;
}

// The area under the player's feet (art pixels), or -1.
static int cat_player_area(const DungeonMap* d, const DungeonPlayer* dp) {
    return cat_area_at(d, (dp->x + (HB_X1 + HB_X2) * 0.5f) * 16 / DMAP_TILE, (dp->y + (HB_Y1 + HB_Y2) * 0.5f) * 16 / DMAP_TILE);
}

static void draw_catacombs(const DungeonMap* d, const DungeonPlayer* dp, const Camera* cam, SDL_Renderer* ren,
                           int tx0, int ty0, int tx1, int ty1, int tsz) {
    int a = cat_player_area(d, dp);
    SDL_Texture* sheet = tilemap_get_town_tex();
    if (a > 0 && sheet) draw_graveyard_dark(cam, ren, sheet, tsz);   // the basements: the graveyards' dark (user)
    else {
        fc_draw_color(ren, 0, 0, 0, 255);
        SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
        SDL_RenderFillRect(ren, &all);
    }
    if (a < 0) return;
    cat_bake(d, a, ren);
    if (s_cat.tex) {
        const auto& A = d->cat_areas[a];
        SDL_Rect dst = { cam_px(cam, (float)(A.x0 * DMAP_TILE / 16)), cam_py(cam, (float)(A.y0 * DMAP_TILE / 16)),
                         s_cat.w * tsz / 16, s_cat.h * tsz / 16 };
        SDL_RenderCopy(ren, s_cat.tex, nullptr, &dst);
    }
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.collected || lo.tx < tx0 || lo.tx >= tx1 || lo.ty < ty0 || lo.ty >= ty1) continue;
        draw_loot(ren, lo, cam_px(cam, (float)(lo.tx * DMAP_TILE)), cam_py(cam, (float)(lo.ty * DMAP_TILE)), tsz);
    }
}

// ── Oasis: the picture ───────────────────────────────────────────────────
// Baked once: the rock filled with the overworld cliffs' texture, each stone
// one flat tone (OASIS_ROCK, tools/gen_oasis.py), in the oasis's darker olive
// -- line, 2d230c, 5c4616 -- outlined black; the water's dot lattice; the air. Every frame,
// behind it: the water, the far wall and its light at a quarter of the
// camera's pace (brighter shafts over a cavern), the far leviathan at a sixth,
// the sunken town's walls and the eyes at half, the close leviathan swimming
// through its pass and the bubbles at three quarters, the tunnels darker;
// the weed (behind the rock, its foot in it); in front: the air pockets'
// water lines and the shafts' ladders. Weed and water lines step through
// three poses a second each (the graveyard roots' beat).
struct OasisArt {
    uint32_t key = 0;
    SDL_Renderer* ren = nullptr;
    SDL_Texture* tex = nullptr;                    // the baked level
    SDL_Texture* art = nullptr;                    // assets/oasis.png
    SDL_Texture* swim = nullptr;                   // assets/player_swim.png
    SDL_Surface* art_px = nullptr;                 // assets/oasis.png, for the water lines' pixels
};
static OasisArt s_oasis;

static void oasis_load(SDL_Renderer* ren) {
    if (s_oasis.ren == ren && s_oasis.art) return;
    s_oasis.ren = ren;
    s_oasis.art = IMG_LoadTexture(ren, "assets/oasis.png");
    s_oasis.swim = IMG_LoadTexture(ren, "assets/player_swim.png");
    if (!s_oasis.art_px)
        if (SDL_Surface* raw = IMG_Load("assets/oasis.png")) {
            s_oasis.art_px = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_RGBA32, 0);
            SDL_FreeSurface(raw);
        }
}

static void oasis_bake(const DungeonMap* d, SDL_Renderer* ren) {
    uint32_t key = d->oasis_seed * 2654435761u ^ (uint32_t)d->oasis_w;
    if (s_oasis.key == key && s_oasis.ren == ren && s_oasis.tex) return;
    if (s_oasis.tex) SDL_DestroyTexture(s_oasis.tex);
    s_oasis.tex = nullptr;
    const int W = d->oasis_w, H = OASIS_PX_H;
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    if (!surf) return;
    const uint32_t RAMP[3] = { 0xFF000000u, 0xFF0C232Du, 0xFF16465Cu };   // RGBA32 as ABGR words
    const uint32_t DOT = 0xFF582A3Bu, AIR = 0xFF703C42u, BLACK = 0xFF000000u;
    for (int y = 0; y < H; y++) {
        uint32_t* row = (uint32_t*)((uint8_t*)surf->pixels + y * surf->pitch);
        for (int x = 0; x < W; x++) {
            uint32_t c = 0;
            if (oasis_rock(d, x, y)) {
                bool edge = !oasis_rock(d, x - 1, y) || !oasis_rock(d, x + 1, y) ||
                            !oasis_rock(d, x, y - 1) || !oasis_rock(d, x, y + 1);
                c = edge ? BLACK : RAMP[OASIS_ROCK[y % OASIS_ROCK_N][x % OASIS_ROCK_N] - '0'];
            } else {
                for (int i = 0; i < d->num_oasis_air; i++) {
                    const auto& a = d->oasis_air[i];
                    if (x >= a.x0 && x < a.x1 && y < a.line) c = AIR;
                }
                if (!c)
                    for (const auto& dt : OASIS_DOTS)
                        if (x % 8 == dt[0] && y % 8 == dt[1]) c = DOT;
            }
            row[x] = c;
        }
    }
    s_oasis.tex = SDL_CreateTextureFromSurface(ren, surf);
    SDL_FreeSurface(surf);
    if (s_oasis.tex) SDL_SetTextureBlendMode(s_oasis.tex, SDL_BLENDMODE_BLEND);
    s_oasis.key = key;
}

static void oasis_piece(SDL_Renderer* ren, int p, int sx, int sy, int s, int clip_x0 = -100000, int clip_x1 = 100000) {
    if (!s_oasis.art) return;
    const short* q = OASIS_PIECE[p];
    SDL_Rect src = { q[0], q[1], q[2], q[3] }, dst = { sx, sy, q[2] * s, q[3] * s };
    if (dst.x + dst.w <= clip_x0 || dst.x >= clip_x1) return;
    if (dst.x < clip_x0) { int cut = (clip_x0 - dst.x + s - 1) / s; src.x += cut; src.w -= cut; dst.x += cut * s; dst.w -= cut * s; }
    if (dst.x + dst.w > clip_x1) { int cut = (dst.x + dst.w - clip_x1 + s - 1) / s; src.w -= cut; dst.w -= cut * s; }
    if (src.w > 0) SDL_RenderCopy(ren, s_oasis.art, &src, &dst);
}

static void draw_oasis(const DungeonMap* d, const Camera* cam, SDL_Renderer* ren, int tx0, int ty0, int tx1, int ty1, int tsz) {
    oasis_load(ren);
    oasis_bake(d, ren);
    const int s = tsz / 16 > 0 ? tsz / 16 : 1;
    const int bx = cam_px(cam, (float)(d->oasis_x0 * DMAP_TILE / 16)), by = cam_py(cam, (float)(d->oasis_y0 * DMAP_TILE / 16));
    const int W = d->oasis_w, H = OASIS_PX_H, camx = -bx / s;   // the level's pixel at the screen's left
    const Uint32 now = SDL_GetTicks();
    fc_draw_color(ren, 0, 0, 0, 255);
    SDL_Rect all = { 0, 0, cam->screen_w, cam->screen_h };
    SDL_RenderFillRect(ren, &all);
    fc_draw_color(ren, 0x2b, 0x1f, 0x40, 255);
    SDL_Rect lvl = { bx, by, W * s, H * s };
    SDL_RenderFillRect(ren, &lvl);
    SDL_RenderSetClipRect(ren, &lvl);                         // the background stays in the level
    auto span_px = [&](int k, int i) { return std::make_pair(bx + d->oasis_sec[i].x0 * s, bx + d->oasis_sec[i].x1 * s); };
    // a quarter: the far wall, and over a cavern its brighter light
    for (int k = -1; k * 128 * s - (camx / 4) * s < cam->screen_w + 128 * s; k++)
        oasis_piece(ren, OP_FAR, k * 128 * s - (camx / 4) % 128 * s - 0 + 0, by + 16 * s, s);
    for (int i = 0; i < d->num_oasis_sec; i++) {
        if (d->oasis_sec[i].kind != 2) continue;
        auto sp = span_px(2, i);
        for (int k = -1; k * 96 * s < cam->screen_w + 96 * s; k++)
            oasis_piece(ren, OP_SHAFT, k * 96 * s - (camx / 4) % 96 * s, by + 16 * s, s, sp.first, sp.second);
    }
    // a sixth: the leviathan far off
    for (int cx = (camx / 6) / 900 - 1; cx * 900 - camx / 6 < cam->screen_w / s + 300; cx++) {
        uint32_t h = pyr_hash((uint32_t)cx * 31337u, d->oasis_seed);
        if (h % 2 == 0) oasis_piece(ren, OP_LEVI, (cx * 900 + (int)(h % 300) - camx / 6) * s, by + (70 + (int)((h >> 4) % 50)) * s, s);
    }
    // a half: the town's broken walls, and eyes open in the dark
    for (int cx = (camx / 2) / 160 - 1; cx * 160 - camx / 2 < cam->screen_w / s + 160; cx++) {
        uint32_t h = pyr_hash((uint32_t)cx * 7919u, d->oasis_seed);
        if (h % 2 == 0) oasis_piece(ren, OP_RUIN, (cx * 160 + (int)(h % 80) - camx / 2) * s, by + (H - 40 - 64) * s, s);
    }
    for (int cx = (camx / 2) / 96 - 1; cx * 96 - camx / 2 < cam->screen_w / s + 96; cx++) {
        uint32_t h = pyr_hash((uint32_t)cx * 92821u, d->oasis_seed * 7u);
        if (h % 5) continue;
        int t = (int)((now / 250 + (h >> 7)) % 24);                         // a blink now and then
        oasis_piece(ren, t == 0 ? OP_EYE2 : t == 1 ? OP_EYE1 : OP_EYE0,
                    (cx * 96 + (int)(h % 60) - camx / 2) * s, by + (80 + (int)((h >> 6) % 70)) * s, s);
    }
    // three quarters: the leviathan close, swimming through its pass; bubbles
    for (int i = 0; i < d->num_oasis_sec; i++) {
        if (d->oasis_sec[i].kind != 3) continue;
        auto sp = span_px(3, i);
        int len = d->oasis_sec[i].x1 - d->oasis_sec[i].x0 + 256;
        int base = d->oasis_sec[i].x1 - (int)((now / 60) % (Uint32)len);     // drifting right to left
        oasis_piece(ren, OP_LEVI_NEAR, bx + (base + camx / 4) * s, by + 80 * s, s, sp.first, sp.second);
    }
    for (int cx = (camx * 3 / 4) / 48 - 1; cx * 48 - camx * 3 / 4 < cam->screen_w / s + 48; cx++) {
        uint32_t h = pyr_hash((uint32_t)cx * 104729u, d->oasis_seed * 3u);
        if (h % 2) continue;
        int b = (int)((h >> 3) % 3);
        oasis_piece(ren, OP_BUB0 + b, (cx * 48 + (int)(h % 40) - camx * 3 / 4) * s, by + (70 + (int)((h >> 6) % 90)) * s, s);
    }
    // the tunnels, a step darker, their ends dithered
    fc_draw_color(ren, 0x14, 0x10, 0x1e, 255);
    for (int i = 0; i < d->num_oasis_sec; i++) {
        if (d->oasis_sec[i].kind != 0) continue;
        int a = d->oasis_sec[i].x0 + 16, b = d->oasis_sec[i].x1 - 16;
        if (b > a) { SDL_Rect r = { bx + a * s, by, (b - a) * s, H * s }; SDL_RenderFillRect(ren, &r); }
        std::vector<SDL_Rect> dots;
        for (int x : { (int)d->oasis_sec[i].x0, b })
            for (int yy = 0; yy < H; yy++)
                for (int xx = x; xx < x + 16; xx++)
                    if ((xx + yy) % 2 == 0) dots.push_back({ bx + xx * s, by + yy * s, s, s });
        if (!dots.empty()) SDL_RenderFillRects(ren, dots.data(), (int)dots.size());
    }
    // the weed, behind the rock, three poses a second each
    for (int i = 0; i < d->num_oasis_weed; i++) {
        const auto& w = d->oasis_weed[i];
        int sx = bx + w.x * s;
        if (sx + 16 * s < 0 || sx > cam->screen_w) continue;
        oasis_piece(ren, OP_WEED0 + (int)((now / 1000 + w.x / 32) % 3), sx, by + w.y * s, s);
    }
    SDL_RenderSetClipRect(ren, nullptr);
    // the level: rock, the water's dots, the air
    if (s_oasis.tex) SDL_RenderCopy(ren, s_oasis.tex, nullptr, &lvl);
    // the water lines, between each hollow's lips, rolling a frame a second
    if (s_oasis.art_px) {
        const short* q = OASIS_PIECE[OP_SURF0 + (int)((now / 1000) % 3)];
        for (int i = 0; i < d->num_oasis_air; i++) {
            const auto& a = d->oasis_air[i];
            for (int px = a.x0; px < a.x1; px++) {
                int sx = bx + px * s;
                if (sx + s < 0 || sx > cam->screen_w) continue;
                for (int j = 0; j < 6; j++) {
                    int y = a.line - 3 + j;
                    if (y < 0 || oasis_rock(d, px, y)) continue;
                    const uint8_t* p = (const uint8_t*)s_oasis.art_px->pixels + (q[1] + j) * s_oasis.art_px->pitch + (q[0] + px % 64) * 4;
                    if (!p[3]) continue;
                    fc_draw_color(ren, p[0], p[1], p[2], 255);
                    SDL_Rect r = { sx, by + y * s, s, s };
                    SDL_RenderFillRect(ren, &r);
                }
            }
        }
    }
    // the shafts' ladders, up to the spring
    if (SDL_Texture* sheet = tilemap_get_town_tex())
        for (int i = 0; i < 2 && i < d->num_oasis_air; i++) {
            const auto& a = d->oasis_air[i];
            int lx = bx + ((a.x0 + a.x1) / 2 - 8) * s;
            for (int y = 0; y < a.line - 4; y += 16) {
                int h = std::min(16, a.line - 4 - y);
                SDL_Rect src = { LADDER_COL0 * 16, LADDER_ROW * 16, 16, h };
                SDL_Rect dst = { lx, by + y * s, 16 * s, h * s };
                SDL_RenderCopy(ren, sheet, &src, &dst);
            }
        }
    for (int li = 0; li < d->num_loot; li++) {
        const DungeonLoot& lo = d->loot[li];
        if (lo.collected || lo.tx < tx0 || lo.tx >= tx1 || lo.ty < ty0 || lo.ty >= ty1) continue;
        draw_loot(ren, lo, cam_px(cam, (float)(lo.tx * DMAP_TILE)), cam_py(cam, (float)(lo.ty * DMAP_TILE)), tsz);
    }
}

bool dungeon_player_fits(const DungeonMap* d, const DungeonPlayer* dp) {
    return d->type == DUNGEON_ENT_OASIS ? oasis_body_free(d, dp->x, dp->y) : can_occupy(d, dp->x, dp->y, tile_solid);
}

bool dungeon_breathing(const DungeonMap* d, const DungeonPlayer* dp) {
    if (d->type != DUNGEON_ENT_OASIS) return true;
    // surfaced: the head up out of the water, under a pocket or in a shaft
    int x0, y0, x1, y1;
    oasis_body(d, dp->x, dp->y, &x0, &y0, &x1, &y1);
    int cx = (x0 + x1) / 2;
    for (int i = 0; i < d->num_oasis_air; i++) {
        const auto& a = d->oasis_air[i];
        if (cx >= a.x0 && cx < a.x1 && y0 <= a.line - 2) return true;
    }
    return false;
}

void dungeon_frame_camera(const DungeonMap* d, Camera* cam) {
    if (d->type != DUNGEON_ENT_OASIS) return;
    int left = d->oasis_x0 * DMAP_TILE / 16, right = left + d->oasis_w * DMAP_TILE / 16;
    int ox = cam->ox;
    if (ox > right - cam->screen_w) ox = right - cam->screen_w;
    if (ox < left) ox = left;
    cam->ox = ox;
    cam->oy = d->oasis_y0 * DMAP_TILE / 16;                     // the level's top at the screen's
    cam->x = (float)cam->ox; cam->y = (float)cam->oy;
}

bool dungeon_draw_swimmer(const DungeonMap* d, const DungeonPlayer* dp, const Player* player,
                          const Camera* cam, SDL_Renderer* ren) {
    if (d->type != DUNGEON_ENT_OASIS) return false;
    oasis_load(ren);
    if (!s_oasis.swim) return false;
    Uint32 now = SDL_GetTicks();
    int f = player->is_moving ? (int)((now / 180) % 3) : (int)((now / 450) % 3);   // stroking, or treading water
    int col = (player->facing == FACE_LEFT ? 3 : 0) + f;
    SDL_Rect src = { col * 14, 0, 14, 20 };
    SDL_Rect dst = { cam_px(cam, dp->x), cam_py(cam, dp->y), (int)(28 * cam->zoom), (int)(40 * cam->zoom) };
    SDL_RenderCopy(ren, s_oasis.swim, &src, &dst);
    return true;
}

void dungeon_draw_oxygen(SDL_Renderer* ren, float oxygen, int x, int y) {
    oasis_load(ren);
    if (!s_oasis.art) return;
    int full = (int)ceilf(oxygen * 8 - 0.001f);
    bool flash = oxygen < 0.25f && (SDL_GetTicks() / 250) % 2;
    const short* q = OASIS_PIECE[OP_HUD];
    for (int i = 0; i < 8; i++) {
        int frame = i < full ? 0 : 2;                         // a bubble, or where one was
        if (i < full && i == full - 1 && oxygen * 8 - i < 0.5f) frame = 1;   // going: popping
        if (flash && i >= full - 2 && i < full) continue;
        SDL_Rect src = { q[0] + frame * 8, q[1], 8, 8 }, dst = { x + i * 18, y, 16, 16 };
        SDL_RenderCopy(ren, s_oasis.art, &src, &dst);
    }
}

// Stonehenge's walls nearer than the player, drawn over them (user): over the
// player's sprite, every pixel of the picture whose ground depth is nearer
// than the player's feet. On one pixel the nearer of two points is the one
// with the smaller depth (the view's ray runs (x + t, d - t, z + t)), so a
// wall's side beside the player never covers them.
// A baked picture's walls drawn again over the player where they stand
// nearer (depth under pdep; -1 none): the pixels round the player's sprite,
// the picture's (x0, y0) on the map, art pixels.
static void draw_front_px(const std::vector<uint32_t>& px, const std::vector<int16_t>& dep, int W, int H,
                          int x0, int y0, int pdep, const DungeonPlayer* dp, const Camera* cam, SDL_Renderer* ren) {
    if (px.empty()) return;
    int tsz = (int)(DMAP_TILE * cam->zoom); if (tsz < 1) tsz = 1;
    int ax0 = (int)floorf(dp->x * 16 / DMAP_TILE), ay0 = (int)floorf(dp->y * 16 / DMAP_TILE);
    int bx = cam_px(cam, (float)(x0 * DMAP_TILE / 16)), by = cam_py(cam, (float)(y0 * DMAP_TILE / 16));
    int ps = tsz / 16 > 0 ? tsz / 16 : 1;
    std::vector<std::pair<uint32_t, SDL_Rect>> todo;
    for (int y = ay0 - y0; y < ay0 - y0 + 21; y++)
        for (int x = ax0 - x0; x < ax0 - x0 + 15; x++) {
            if (x < 0 || y < 0 || x >= W || y >= H) continue;
            int k = y * W + x;
            if (dep[k] < 0 || dep[k] >= pdep) continue;
            todo.push_back({ px[k], { bx + x * tsz / 16, by + y * tsz / 16, ps, ps } });
        }
    std::sort(todo.begin(), todo.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    std::vector<SDL_Rect> rects;
    for (size_t i = 0; i < todo.size(); i++) {
        rects.push_back(todo[i].second);
        if (i + 1 == todo.size() || todo[i + 1].first != todo[i].first) {
            uint32_t c = todo[i].first;
            fc_draw_color(ren, c & 255, (c >> 8) & 255, (c >> 16) & 255, 255);
            SDL_RenderFillRects(ren, rects.data(), (int)rects.size());
            rects.clear();
        }
    }
}

void dungeon_draw_front(const DungeonMap* dmap, const DungeonPlayer* dp, const Camera* cam, SDL_Renderer* ren) {
    if (dmap->type == DUNGEON_ENT_STONEHENGE) {
        int fy = (int)floorf((dp->y + HB_Y2) * 16 / DMAP_TILE) - 1;               // the feet's last row
        draw_front_px(s_barrow.px, s_barrow.dep, s_barrow.w, s_barrow.h, dmap->barrow_x0, dmap->barrow_y0,
                      dmap->barrow_oy - 1 - fy, dp, cam, ren);
        return;
    }
    if (dmap->type == DUNGEON_ENT_CATACOMBS) {                                     // depth is the feet's row
        int a = cat_player_area(dmap, dp);
        if (a < 0 || a != s_cat.area) return;
        int fy = (int)floorf((dp->y + HB_Y2) * 16 / DMAP_TILE) - 1;
        draw_front_px(s_cat.px, s_cat.dep, s_cat.w, s_cat.h, dmap->cat_areas[a].x0, dmap->cat_areas[a].y0,
                      CAT_DEPTH0 - 2 * (fy - dmap->cat_areas[a].oy), dp, cam, ren);
        return;
    }
    if (!gyw_walkways(dmap) || !s_gyw.tex) return;
    SDL_Texture* tex = tilemap_get_town_tex();
    if (!tex) return;
    int tsz = (int)(DMAP_TILE * cam->zoom); if (tsz < 1) tsz = 1;
    const int c0 = WALL_COL0[WALL_GRAVEYARD] * 16, r0 = WALL_ROW0[WALL_GRAVEYARD] * 16;
    // the player's feet, in art pixels
    float fx = (dp->x + (HB_X1 + HB_X2) * 0.5f) * 16 / DMAP_TILE, fy = (dp->y + HB_Y2) * 16 / DMAP_TILE;
    for (const auto& w : s_gyw.walls) {
        if (fy >= w.y || fx < w.x - 8 || fx > w.x + 80) continue;   // in front of it, or beside it
        auto copy = [&](int sx, int sy, int x, int y, int ww, int hh) {
            SDL_Rect src = { sx, sy, ww, hh };
            SDL_Rect dst = { cam_px(cam, (float)(x * DMAP_TILE / 16)), cam_py(cam, (float)(y * DMAP_TILE / 16)),
                             ww * tsz / 16, hh * tsz / 16 };
            SDL_RenderCopy(ren, tex, &src, &dst);
        };
        const GyPiece& pw = GY_PIECE[w.g];
        copy(c0 + pw.col * 16, r0 + pw.row * 16, w.x, w.y - 63, 72, 64);
        if (w.ladder) {
            const GyPiece& pl = GY_PIECE[GY_LADDER];
            copy(c0 + pl.col * 16, r0 + pl.row * 16, w.x + 24, w.y - 47, 16, 32);
            copy(c0 + pl.col * 16, r0 + pl.row * 16 + 16, w.x + 24, w.y - 15, 16, 16);
        } else {
            copy(GYW_DOOR_COL * 16, GYW_DOOR_ROW * 16, w.x + 24, w.y - 31, 16, 32);
        }
    }
}

void dungeon_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                  const Camera* cam, SDL_Renderer* ren) {
    float z   = cam->zoom;
    int   tsz = (int)(DMAP_TILE * z);
    if (tsz < 1) tsz = 1;

    int ci = dng_palette_index(dmap);
    const DngPalette  pal    = dng_palette(dmap);
    const DngAscii&   ascii  = ASCII_CHARS[ci];
    int scale = tsz / 8;
    if (scale < 1) scale = 1;
    int coff = (tsz - 8 * scale) / 2;   // centering offset within tile

    // visible tile range
    int tx0 = (int)(cam->x / DMAP_TILE) - 1;
    int ty0 = (int)(cam->y / DMAP_TILE) - 1;
    int tx1 = tx0 + (int)(cam->screen_w / tsz) + 3;
    int ty1 = ty0 + (int)(cam->screen_h / tsz) + 3;
    if (tx0 < 0)       tx0 = 0;
    if (ty0 < 0)       ty0 = 0;
    if (tx1 > DMAP_W)  tx1 = DMAP_W;
    if (ty1 > DMAP_H)  ty1 = DMAP_H;

    if (gyw_walkways(dmap)) {
        if (SDL_Texture* tex = tilemap_get_town_tex()) {
            draw_graveyard(dmap, cam, ren, tex, tx0, ty0, tx1, ty1, tsz);
            return;
        }
    }
    if (dmap->type == DUNGEON_ENT_OASIS) {
        draw_oasis(dmap, cam, ren, tx0, ty0, tx1, ty1, tsz);
        return;
    }
    if (dmap->type == DUNGEON_ENT_CATACOMBS) {
        draw_catacombs(dmap, dplayer, cam, ren, tx0, ty0, tx1, ty1, tsz);   // its doors are in the picture
        return;
    }
    if (dmap->type == DUNGEON_ENT_LARGE_TREE) {
        draw_tree(dmap, cam, ren, tx0, ty0, tx1, ty1, tsz);   // its way out is in the picture
        return;
    }
    if (dmap->type == DUNGEON_ENT_CAVE) {
        draw_cave(dmap, cam, ren, tx0, ty0, tx1, ty1, tsz);   // its mouths and ladders are in the picture
        return;
    }
    if (dmap->type == DUNGEON_ENT_STONEHENGE) {
        if (SDL_Texture* tex = tilemap_get_town_tex()) {
            draw_barrow(dmap, cam, ren, tex, tx0, ty0, tx1, ty1, tsz);   // its ladders are in the picture
            return;
        }
    }
    if (dmap->type == DUNGEON_ENT_PYRAMID || dmap->type == DUNGEON_ENT_RUINS) {
        if (SDL_Texture* tex = tilemap_get_town_tex()) {
            draw_tile_art(dmap, cam, ren, tex, tx0, ty0, tx1, ty1, tsz);
            draw_ways_out(dmap, cam, ren, tx0, ty0, tx1, ty1, tsz);
            return;
        }
    }

    for (int ty = ty0; ty < ty1; ty++) {
        for (int tx = tx0; tx < tx1; tx++) {
            uint8_t tile = dmap->tiles[ty][tx];

            // Outline walls: skip wall tiles not adjacent to any open tile
            if (tile == DNG_WALL) {
                bool border = false;
                for (int ny = ty-1; ny <= ty+1 && !border; ny++)
                    for (int nx = tx-1; nx <= tx+1 && !border; nx++)
                        if (nx>=0 && nx<DMAP_W && ny>=0 && ny<DMAP_H)
                            if (dmap->tiles[ny][nx] != DNG_WALL)
                                border = true;
                if (!border) continue;
            }

            const SDL_Color* c;
            switch (tile) {
                case DNG_FLOOR:                                // the ways out stand on the floor;
                case DNG_ENTRY:                                // their ladders are drawn last
                case DNG_EXIT:  c = &pal.floor; break;
                default:        c = &pal.wall;  break;
            }
            int sx = cam_px(cam, tx * DMAP_TILE);
            int sy = cam_py(cam, ty * DMAP_TILE);

            SDL_Rect rect = { sx, sy, tsz, tsz };
            fc_draw_color(ren, c->r, c->g, c->b, 255);
            SDL_RenderFillRect(ren, &rect);

            // Loot: plain gold square drawn over the floor tile.
            bool has_loot = false;
            if (tile == DNG_FLOOR) {
                for (int li = 0; li < dmap->num_loot; li++) {
                    const DungeonLoot& lo = dmap->loot[li];
                    if (lo.collected || lo.tx != tx || lo.ty != ty) continue;
                    draw_loot(ren, lo, sx, sy, tsz);
                    has_loot = true;
                    break;
                }
            }
            if (has_loot) continue;   // skip the ASCII floor dot — keep the square clean
            if (tile == DNG_ENTRY || tile == DNG_EXIT) continue;   // a ladder, drawn last

            // ASCII char overlay
            char ch; Uint8 cr, cg, cb;
            switch (tile) {
                case DNG_FLOOR:
                    ch = ascii.floor;
                    cr = c->r / 2; cg = c->g / 2; cb = c->b / 2;
                    break;
                case DNG_ENTRY:
                    ch = '<';
                    cr = 255; cg = 240; cb = 80;
                    break;
                case DNG_EXIT:
                    ch = '>';
                    cr = 255; cg = 100; cb = 100;
                    break;
                default: // wall
                    ch = ascii.wall;
                    cr = (Uint8)((c->r + 255) / 2);
                    cg = (Uint8)((c->g + 255) / 2);
                    cb = (Uint8)((c->b + 255) / 2);
                    break;
            }
            char buf[2] = {ch, '\0'};
            draw_text(ren, buf, sx + coff, sy + coff, scale, cr, cg, cb);
        }
    }

    draw_ways_out(dmap, cam, ren, tx0, ty0, tx1, ty1, tsz);
}

// The ways out -- the entry and every exit -- last, on the north wall
// each stands at the foot of (dungeon_seat_portals): a ladder up the
// wall's whole face in the cave's own rock or the stone, its foot on the
// face's lowest row; or the doorway of the entrance the dungeon is entered
// by, centred over the way out, its foot on the wall's.
static void draw_ways_out(const DungeonMap* dmap, const Camera* cam, SDL_Renderer* ren,
                          int tx0, int ty0, int tx1, int ty1, int tsz) {
    if (SDL_Texture* tex = tilemap_get_town_tex()) {
        const WayOutDoor* door = way_out_door(dmap);
        int face = way_out_face(dmap);
        for (int ty = ty0; ty < ty1; ty++)
            for (int tx = tx0; tx < tx1; tx++) {
                uint8_t tile = dmap->tiles[ty][tx];
                if (tile != DNG_ENTRY && tile != DNG_EXIT) continue;
                int sx = cam_px(cam, tx * DMAP_TILE), sy = cam_py(cam, ty * DMAP_TILE);
                if (door) {
                    SDL_Rect src = { door->col * 16, (door->foot + 1 - door->h) * 16, door->w * 16, door->h * 16 };
                    SDL_Rect dst = { sx - (door->w - 1) / 2 * tsz, sy - door->h * tsz, door->w * tsz, door->h * tsz };
                    SDL_RenderCopy(ren, tex, &src, &dst);
                    continue;
                }
                for (int k = 1; k <= face; k++) {   // up the face from its foot
                    SDL_Rect src = { LADDER_COL0 * 16, (k == 1 ? LADDER_ROW + 1 : LADDER_ROW) * 16, 16, 16 };
                    SDL_Rect dst = { sx, sy - k * tsz, tsz, tsz };
                    SDL_RenderCopy(ren, tex, &src, &dst);
                }
            }
    }
}

// Weapon swing/throw visual for the dungeon player -- thin wrapper
// around weapon_swing_draw() (combat.h), the same one overworld_draw_swing()
// (src/overworld.cpp) calls.
void dungeon_draw_swing(const DungeonPlayer* dp, const Camera* cam, SDL_Renderer* ren)
{
    float px = dp->x + (HB_X1 + HB_X2) * 0.5f;
    float py = dp->y + (HB_Y1 + HB_Y2) * 0.5f;
    weapon_swing_draw(&dp->swing, px, py, cam, ren);
}

// ── Public: debug tile-grid overlay ───────────────────────────────────────
// One line per DMAP_TILE boundary in view.
void dungeon_draw_debug_grid(const DungeonMap*, const Camera* cam, SDL_Renderer* ren) {
    float z   = cam->zoom;
    int   tsz = (int)(DMAP_TILE * z);
    if (tsz < 1) tsz = 1;

    int tx0 = (int)(cam->x / DMAP_TILE) - 1;
    int ty0 = (int)(cam->y / DMAP_TILE) - 1;
    int tx1 = tx0 + (int)(cam->screen_w / tsz) + 3;
    int ty1 = ty0 + (int)(cam->screen_h / tsz) + 3;
    if (tx0 < 0) tx0 = 0;
    if (ty0 < 0) ty0 = 0;
    if (tx1 > DMAP_W) tx1 = DMAP_W;
    if (ty1 > DMAP_H) ty1 = DMAP_H;

    fc_draw_color(ren, 0, 255, 0, 110);
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_BLEND);
    for (int ty = ty0; ty < ty1; ty++) {
        for (int tx = tx0; tx < tx1; tx++) {
            int sx = cam_px(cam, tx * DMAP_TILE);
            int sy = cam_py(cam, ty * DMAP_TILE);
            SDL_Rect r = { sx, sy, tsz, tsz };
            SDL_RenderDrawRect(ren, &r);
        }
    }
    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}

// ── Public: minimap overlay ───────────────────────────────────────────────
// The map's frame: the box the dungeon's floor fills with the wall ring round
// it, scaled to fill 80% of the screen: a cave's tile is an 8-pixel block, the
// catacombs' not quite one pixel. The frame used to be the whole 768x512 grid
// at half scale, which drew a cave's 62x30 tiles as a 31x15 smudge in an empty
// panel. Draw and click share it: the click is this scaling run backwards.
struct DngMiniFrame {
    int x0, y0, x1, y1, ox, oy, mw, mh; float s;   // tiles framed, panel origin and size, pixels a tile
    int px(int k) const { return (int)(k * s); }   // where the k-th tile's block starts, from the panel's edge
};
static DngMiniFrame dng_mini_frame(const DungeonMap* d, int screen_w, int screen_h) {
    DngMiniFrame f = { d->floor_x0, d->floor_y0, d->floor_x1, d->floor_y1, 0, 0, 0, 0, 1 };
    int bw = f.x1 - f.x0 + 1, bh = f.y1 - f.y0 + 1;
    f.s = std::min(screen_w * 0.8f / bw, screen_h * 0.8f / bh);
    f.mw = (int)(bw * f.s); f.mh = (int)(bh * f.s);
    f.ox = (screen_w - f.mw) / 2; f.oy = (screen_h - f.mh) / 2;
    return f;
}

void dungeon_minimap_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                          SDL_Renderer* ren, int screen_w, int screen_h,
                          bool show_all) {
    const DngMiniFrame f = dng_mini_frame(dmap, screen_w, screen_h);
    const DngPalette pal = dng_palette(dmap);

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
    draw_nes_panel(ren, f.ox - 4, f.oy - 4, f.mw + 8, f.mh + 8);

    // Every explored tile as its block of the frame; a block narrower than a
    // pixel (the map shrunk) is the tile that sampling drops.
    for (int ty = f.y0; ty <= f.y1; ty++) {
        for (int tx = f.x0; tx <= f.x1; tx++) {
            if (!show_all && !dmap->explored[ty][tx]) continue;
            int bx = f.px(tx - f.x0), by = f.px(ty - f.y0);
            SDL_Rect r = { f.ox + bx, f.oy + by, f.px(tx - f.x0 + 1) - bx, f.px(ty - f.y0 + 1) - by };
            if (!r.w || !r.h) continue;
            uint8_t tile = dmap->tiles[ty][tx];
            const SDL_Color* c;
            switch (tile) {
                case DNG_FLOOR: c = &pal.floor; break;
                case DNG_ENTRY: c = &pal.entry; break;
                case DNG_EXIT:  c = &pal.exit_; break;
                default:        c = &pal.wall;  break;
            }
            fc_draw_color(ren, c->r, c->g, c->b, 255);
            SDL_RenderFillRect(ren, &r);
        }
    }

    // Player -- their feet, a flashing 5x5 square, matching the overworld minimap marker.
    int px = f.ox + (int)(((dplayer->x + (HB_X1 + HB_X2) * 0.5f) / DMAP_TILE - f.x0) * f.s);
    int py = f.oy + (int)(((dplayer->y + HB_Y2) / DMAP_TILE - f.y0) * f.s);
    if ((SDL_GetTicks() / MINIMAP_FLASH_MS) & 1)
        fc_draw_color(ren, 0, 255, 255, 255);
    else
        fc_draw_color(ren, 255, 255, 255, 255);
    SDL_Rect dot = { px - 2, py - 2, 5, 5 };
    SDL_RenderFillRect(ren, &dot);

    SDL_SetRenderDrawBlendMode(ren, SDL_BLENDMODE_NONE);
}

bool dungeon_minimap_click_to_world(const DungeonMap* dmap,
                                    int screen_w, int screen_h, int mx, int my,
                                    bool show_all,
                                    float* out_world_x, float* out_world_y)
{
    const DngMiniFrame f = dng_mini_frame(dmap, screen_w, screen_h);
    if (mx < f.ox || mx >= f.ox + f.mw || my < f.oy || my >= f.oy + f.mh)
        return false;

    // The tile whose block holds the pixel: the scaling run backwards, then
    // settled against the block edges the draw uses, since truncating p / s
    // and k * s separately puts a click one tile off wherever s is a fraction.
    auto tile_at = [&](int p, int n) {
        int k = (int)(p / f.s);
        while (k > 0 && f.px(k) > p) k--;
        while (k < n - 1 && f.px(k + 1) <= p) k++;
        return k;
    };
    int tx = f.x0 + tile_at(mx - f.ox, f.x1 - f.x0 + 1);
    int ty = f.y0 + tile_at(my - f.oy, f.y1 - f.y0 + 1);

    // Don't send the player into a wall, or into fog they can't see on the
    // very minimap they're clicking.
    if (!show_all && !dmap->explored[ty][tx]) return false;
    if (dmap->tiles[ty][tx] == DNG_WALL) return false;

    *out_world_x = (float)(tx * DMAP_TILE);
    *out_world_y = (float)(ty * DMAP_TILE);
    return true;
}
