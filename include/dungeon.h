#ifndef DUNGEON_H
#define DUNGEON_H

#include <SDL2/SDL.h>
#include <stdint.h>
#include "entity.h"
#include "input.h"
#include "camera.h"
#include "tilemap.h"   // DungeonEntranceType
#include "resource_node.h"
#include "combat.h"

#define DMAP_W              768
#define DMAP_H              512
#define DMAP_TILE           32
// Visible tile radius around the player. Scaled with the sprite: 12 suited the
// old 46-pixel one, and 8 keeps the same reach in body lengths for the 30.
#define DUNGEON_FOV_RADIUS  8
// Array capacity, not the amount any one dungeon gets. Catacombs covers several
// times the floor area of anything else and would read as empty on the old cap,
// so the arrays grew for its sake -- but raising what every archetype PLACES
// would quietly add enemies and chests to every dungeon in the game, which is
// why the budgets below stayed where they were. See dng_spawner_budget().
#define DMAP_MAX_SPAWNERS   64
#define DMAP_MAX_LOOT       64
#define DNG_SPAWNER_BUDGET  24   // every archetype except catacombs
#define DNG_LOOT_BUDGET     32

enum DungeonTile : uint8_t {
    DNG_WALL  = 0,
    DNG_FLOOR = 1,
    DNG_ENTRY = 2,   // spawn point / stairs back up
    DNG_EXIT  = 3,   // goal / stairs deeper
};

struct DungeonSpawner {
    int  tx, ty;
    int  enemy_id;
    bool dead;
};

// Fixed loot pickup placed deterministically at generation time. Rewards
// exploration rather than combat: only reachable by walking to (tx,ty),
// and only rendered once that tile has been explored.
struct DungeonLoot {
    int  tx, ty;
    int  gold;
    bool collected;
    int  item = -1;   // -1: a gold pile; otherwise the treasure it is, an Item (crafting.h)
};

// A cave under a mountain has one mouth in the south wall and one on the top of
// each storey, so it needs more ways out than the two a paired dungeon wants.
#define DMAP_MAX_PORTALS 6

// Where a portal is underground, and which overworld tile it lets out at.
// The destination used to live in four loop-local ints in main.cpp, which is
// exactly as many as two portals need and not one more.
struct DungeonPortal {
    int tx, ty;       // tile in the dungeon
    int ow_x, ow_y;   // overworld tile it returns you to
    DungeonEntranceType ow_type;   // the entrance there: a graveyard's way out is
                                   // a ladder up to a small one, a door to a large
};

// A piece of art the pyramid lays over its walls whole: a carved stone, a
// cartouche, a mural. Sheet pixels and where they go, in art pixels (a tile is
// 16); anchor is the walkable tile whose sight lights it.
struct DungeonDecal {
    int16_t sx, sy, w, h;     // on the sheet
    int     x, y;             // in the dungeon, art pixels
    int16_t ax, ay;           // anchor tile
    bool    flip;
};
#define DMAP_MAX_DECALS   128
#define DMAP_MAX_BARROW_BLOCKS 640
#define DMAP_MAX_PYR_ROOMS 16
#define DMAP_MAX_COL_SHAPES 320
#define DMAP_MAX_GYW_RECTS 160
#define OASIS_MAX_PX 4800          // 15 screens of 20 tiles, art pixels
#define OASIS_PX_H   240           // the reference's height: 15 tiles
#define DMAP_MAX_GYW_SEGS  96

struct DungeonMap {
    uint8_t tiles[DMAP_H][DMAP_W];
    // The tile art of an interior with built walls -- the ruins, the pyramid
    // (WallArt in src/dungeon.cpp): what each tile is drawn as -- floor, a
    // face, a side wall, a flight strip -- and that piece's row and variant.
    // Zero (none) everywhere for every other kind.
    uint8_t art[DMAP_H][DMAP_W];
    uint8_t art_p[DMAP_H][DMAP_W];
    // Set before generating, from the entrance: a pyramid anywhere but the
    // desert is a step pyramid, and inside it is Mayan rather than Egyptian.
    bool step_pyramid;
    struct { int16_t cx, yb; } pyr_rooms[DMAP_MAX_PYR_ROOMS];   // each chamber: its centre column, first floor row
    int  num_pyr_rooms;
    // The pyramid's passage has two ends and a middle: alone, it is entered in
    // the middle and left by the far end; paired, it runs end to end, so the
    // near end (this) becomes the way in.
    int  alt_entry_x, alt_entry_y;
    DungeonDecal decals[DMAP_MAX_DECALS];
    int  num_decals;
    // Stonehenge's barrow: its maze's blocks (ground x across and d back, in
    // art pixels, a tile being 16), where ground (0, 0) lies on the map, and
    // the box its picture fills -- the game composites the picture from these
    // the first time it is drawn (src/dungeon.cpp barrow_bake).
    struct { int16_t x, d; } barrow_blocks[DMAP_MAX_BARROW_BLOCKS];
    int  num_barrow_blocks;
    int  barrow_ox, barrow_oy;
    int  barrow_x0, barrow_y0, barrow_w, barrow_h;
    uint32_t barrow_seed;                // its grass and carvings, laid the same every visit
    // Its two ways out: a ladder in the middle of a corridor's flat back wall,
    // the corridor's middle (ground x) and that wall's front (ground d).
    int  barrow_way_x[2], barrow_way_d[2];
    // What the player's feet collide with, in art pixels: boxes and triangles
    // only (stonehenge: each wall cell's ground footprint, a parallelogram
    // under the oblique view, cut into a box and two triangles). Inclusive.
    struct { bool box; float x[3], y[3]; } col_shapes[DMAP_MAX_COL_SHAPES];
    int  num_col_shapes;
    // The graveyard's walkways (carve_graveyard_walkways): rectangles in the
    // world under the oblique view (u across, v back, art pixels), drawn at
    // art pixel (gyw_ox + u + v, gyw_oy - v); the path's segments with the
    // distance along it at each start, for where brick gives way to boards;
    // the two way-out landings (world tiles, the landing spanning -1..+2) and
    // the box the picture fills. Composited the first time it is drawn.
    struct { int16_t u0, v0, u1, v1; } gyw_rects[DMAP_MAX_GYW_RECTS];
    int  num_gyw_rects;
    struct { int16_t ax, ay, bx, by; float arc; } gyw_segs[DMAP_MAX_GYW_SEGS];
    int  num_gyw_segs;
    float gyw_total;                     // the path's whole length
    int  gyw_ox, gyw_oy;
    int  gyw_way_u[2], gyw_way_v[2];     // 0 the way in, 1 the far end
    int  gyw_x0, gyw_y0, gyw_w, gyw_h;
    uint32_t gyw_seed;
    // The oasis (carve_oasis): a flooded cave seen from the side, a bit an art
    // pixel of rock; its air (pockets in the ceiling's hollows, and the two
    // shafts up to the spring, entries 0 and 1): columns x0..x1 above the
    // water line; its sections (0 tunnel, 1 cave, 2 cavern, 3 the
    // leviathan's pass); its weed (x, top); all in level pixels, the level
    // drawn at art pixel (oasis_x0, oasis_y0).
    uint8_t oasis_solid[OASIS_PX_H][OASIS_MAX_PX / 8];
    int  oasis_w, oasis_x0, oasis_y0;
    struct { int16_t x0, x1, line; } oasis_air[24];
    int  num_oasis_air;
    struct { uint8_t kind; int16_t x0, x1; } oasis_sec[40];
    int  num_oasis_sec;
    struct { int16_t x, y; } oasis_weed[320];
    int  num_oasis_weed;
    uint32_t oasis_seed;
    uint8_t explored[DMAP_H][DMAP_W];  // 0=never seen, 1=seen at least once
    uint8_t visible[DMAP_H][DMAP_W];   // 1=currently in FOV (wall-blocked), reset each frame
    // Portal 0 is the entry and keeps the DNG_ENTRY tile; every other portal
    // keeps DNG_EXIT. Holding to that means no new tile id, no new palette
    // entry, and none of the five render switches have to learn anything.
    // entry_x/exit_x stay as the names the layout generators write, and are
    // copied into portals 0 and 1 once the layout is done.
    DungeonPortal portals[DMAP_MAX_PORTALS];
    int num_portals;
    int want_portals;                  // asked for before generating; 2 unless a cave
    bool starter;                      // set before generating: a starting-island dungeon
    // Where this cave's mouths sit on the mountain, as offsets in overworld
    // tiles from their own centroid. Set before generating, alongside
    // want_portals, and used to lay the chambers out in the same arrangement —
    // so a mouth on the south face opens into the south of the cave and one on
    // a north top into the north of it. Zero for anything that is not a cave.
    int want_ox[DMAP_MAX_PORTALS], want_oy[DMAP_MAX_PORTALS];
    int entry_x, entry_y;
    int exit_x,  exit_y;
    DungeonEntranceType type;
    float difficulty;
    // Which material this cave's rock is, derived from difficulty by
    // dungeon_generate(). Every mouth of one cave system already shares a
    // difficulty (tilemap.cpp's cave_diff), so this agrees across mouths and
    // across re-entries with no extra state. Unread for non-cave types.
    Material ore;
    DungeonSpawner spawners[DMAP_MAX_SPAWNERS];
    int            num_spawners;
    DungeonLoot    loot[DMAP_MAX_LOOT];
    int            num_loot;
    ResourceNodeList dungeon_rocks;    // destroyable rock-node wall tiles
};

struct DungeonPlayer {
    float x, y;
    float speed;
    int   at_exit;    // 1 if player centre is over DNG_EXIT tile
    int   at_entry;   // 1 if player centre is over DNG_ENTRY tile (exit back to overworld)
    float slide = 0;  // sliding along a 45-degree edge: how far owed (see dungeon_player_update)
    float vx = 0, vy = 0;   // swimming (the oasis): the drift kept from frame to frame

    // Weapon swing/thrust/throw state -- see combat.h. Shared machinery with
    // the overworld (Overworld, include/overworld.h).
    WeaponSwingState swing;

    // The treasure picked up this frame, an Item; -1 for none. The caller
    // says so, and remembers this dungeon's treasure as taken.
    int picked_item = -1;
};

// The special part a dungeon of this kind keeps as its one treasure (an Item,
// crafting.h): the halberd's in ruins, the katana's at stonehenge, the
// scythe's in catacombs. -1 for a kind with none.
int dungeon_treasure_item(DungeonEntranceType type);

// Which material a cave of this difficulty holds. Exposed so tools/oreprof.cpp
// censuses the SHIPPED thresholds instead of its own copy of them -- a second
// copy is exactly how a calibration silently goes stale.
Material material_for_difficulty(float difficulty);

// The enemy a spawner in a dungeon of this type and difficulty holds. Picked
// by TIER from difficulty -- the far-out, high-up dungeons get the hard
// tiers wherever they are -- with the dungeon's region only as flavour (its
// own enemies weigh more). Never a boss; elites only in the wastelands and
// the hard-to-reach dungeons. See src/dungeon.cpp; tools/spawncensus.cpp
// measures what it does across worlds.
int dungeon_pick_enemy(DungeonEntranceType type, float difficulty, uint32_t* rng);
// The lowest difficulty that still yields this material: the bottom edge of
// its band. material_for_difficulty(material_min_difficulty(m)) == m exactly,
// because the lookup tests strictly below each band's top. The guarantee pass
// in tilemap.cpp moves one cave system's difficulty here when a world grew no
// cave of a material at all.
float material_min_difficulty(Material m);
// Display name of a material -- "Stone", "Reality Shard", ... Exposed for the
// same reason as material_for_difficulty(): the debug menu and
// tools/oreprof.cpp name the tiers from the table the game renders them from,
// rather than each keeping a copy that can drift out of step with it.
const char* material_name(Material m);

// One tone of a material's colour ramp: the same ramps the ore's rock is
// painted in (src/ore_tones.inc), so a weapon reads as the ore it came from.
enum { ORE_SHADE = 1, ORE_BASE = 2, ORE_LIT = 3 };
SDL_Color material_color(Material m, int tone);

void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type,
                      float difficulty, unsigned int seed);
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle);

// Everything that has to be decided about a dungeon before it is generated:
// which interior it is, how hard, and where its stairs come out. See the
// precedence block in dungeon_wiring_for() (src/dungeon.cpp) for what wins when
// an entrance could be described by more than one rule.
struct DungeonWiring {
    unsigned int        seed;         // interior layout, and the fog-cache key
    float               difficulty;   // ore band and chest gold
    DungeonEntranceType type;         // which archetype's generator runs
    int   from_exit;                  // spawn at portal 0 (0) or portal 1 (1)
    float connect_angle;              // NAN unless a partnered pair
    int   entry_ow_x, entry_ow_y;     // portal 0 destination
    int   exit_ow_x,  exit_ow_y;      // portal 1 destination
    DungeonEntranceType entry_type, exit_type;   // the entrances there
    // A cave system's mouths, in entrance-array order, and each one's offset
    // from their centroid for the carve to lay chambers out against. n_mouths is
    // 0 for anything that is not a mountain with two or more ways in.
    int   mouth_ow_x[DMAP_MAX_PORTALS], mouth_ow_y[DMAP_MAX_PORTALS];
    int   want_ox[DMAP_MAX_PORTALS],    want_oy[DMAP_MAX_PORTALS];
    int   n_mouths;
    int   my_mouth;                   // which mouth was walked into, or -1
    bool  starter;                    // one of the starting island's two (dungeon_is_starter)
    bool  step_pyramid;               // a pyramid off the desert: the Mayan interior
};

// Which dungeon the entrance at this index opens, and where its ways out lead.
// Takes a map and an index so a headless tool can ask exactly what the game
// asks -- the decision used to live in main.cpp's input handler, out of reach of
// anything that could check it.
DungeonWiring dungeon_wiring_for(const Tilemap* map, unsigned int map_seed,
                                 int entrance_idx);
// Bind a freshly generated dungeon to the overworld. Exactly three answers to
// "where do these stairs let out", and every one of them leaves portals[] as the
// list of stair tiles on the map -- portal 0 the entry, the rest exits. See the
// block above dungeon_bind_solo() in src/dungeon.cpp.
//
// Solo: the way in is the only way out, so one portal and no DNG_EXIT tile.
void dungeon_bind_solo(DungeonMap* dmap, int ow_x, int ow_y);
// Each way out moved to the foot of the dungeon's outer wall, its ladder or
// doorway on that wall. The binds call it; exposed for tools/dngshot.cpp.
void dungeon_seat_portals(DungeonMap* dmap);
// Partnered: orient the pair along the overworld bearing between the two linked
// entrances, then give each end its landing.
void dungeon_bind_pair(DungeonMap* dmap, float exit_angle,
                       int entry_ow_x, int entry_ow_y, DungeonEntranceType entry_type,
                       int exit_ow_x,  int exit_ow_y,  DungeonEntranceType exit_type);
// Cave system: one portal per mouth, each returning to the mouth it belongs to.
// ow_x/ow_y are n overworld tiles, in the same order the portals were carved.
void dungeon_bind_cave_mouths(DungeonMap* dmap, const int* ow_x, const int* ow_y, int n);
// from_exit=0: spawn at DNG_ENTRY; from_exit=1: spawn at DNG_EXIT (connected entrance)
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit);
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, DungeonMap* dmap, const Camera* cam,
                           bool noclip = false, HarvestResult* out_harvest = nullptr);
// The oasis: whether the swimmer's head is in air (a pocket under the
// ceiling, or a shaft) -- always true anywhere else, where there is no water.
bool dungeon_breathing(const DungeonMap* dmap, const DungeonPlayer* dp);
// Whether the player fits where they stand: their feet clear of walls, or in
// the oasis their whole swimming body clear of rock and below the surface.
bool dungeon_player_fits(const DungeonMap* dmap, const DungeonPlayer* dp);
// A side-view dungeon (the oasis) holds its camera to the level: zoom 1, the
// level's top at the screen's, following across only, never past either end.
// Nothing for any other kind.
void dungeon_frame_camera(const DungeonMap* dmap, Camera* cam);
// The swimmer, drawn in place of the walking player in the oasis; false
// anywhere else (the caller draws the player as usual).
bool dungeon_draw_swimmer(const DungeonMap* dmap, const DungeonPlayer* dp, const Player* player,
                          const Camera* cam, SDL_Renderer* ren);
// The oxygen row in the HUD: eight bubbles, full to empty, the last two
// flashing when it runs low.
void dungeon_draw_oxygen(SDL_Renderer* ren, float oxygen, int x, int y);
// Whether a point (dungeon pixels) is solid to the player's feet -- the
// collision the game moves them by. Exposed for the tools.
bool dungeon_solid_at(const void* dmap, float px, float py);
void dungeon_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                  const Camera* cam, SDL_Renderer* ren, bool show_all = false);
// What stands in front of the player, drawn after them: a graveyard's way-out
// wall when they are behind it. Nothing for any other kind.
void dungeon_draw_front(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                        const Camera* cam, SDL_Renderer* ren);
// Weapon swing/thrust/throw visual for the dungeon player -- thin wrapper
// around weapon_swing_draw() (combat.h), the same one overworld_draw_swing()
// (src/overworld.cpp) calls.
void dungeon_draw_swing(const DungeonPlayer* dp, const Camera* cam, SDL_Renderer* ren);
// Debug overlay: thin lines around every DMAP_TILE grid cell in view,
// labeled with the tileset (col,row) a cave wall tile actually draws from
// (blank for floor tiles, non-cave dungeon types, and deep-interior void,
// none of which source from the tileset).
void dungeon_draw_debug_grid(const DungeonMap* dmap, const Camera* cam, SDL_Renderer* ren);
void dungeon_minimap_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                          SDL_Renderer* ren, int screen_w, int screen_h,
                          bool show_all = false);
bool dungeon_minimap_click_to_world(const DungeonMap* dmap,
                                    int screen_w, int screen_h, int mx, int my,
                                    bool show_all,
                                    float* out_world_x, float* out_world_y);

#endif
