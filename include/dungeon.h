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
#define DUNGEON_FOV_RADIUS  12   // visible tile radius around player
#define DMAP_MAX_SPAWNERS   24
#define DMAP_MAX_LOOT       32

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
};

struct DungeonMap {
    uint8_t tiles[DMAP_H][DMAP_W];
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

    // Weapon swing/thrust/throw state -- see combat.h. Shared machinery with
    // the overworld (Overworld, include/overworld.h).
    WeaponSwingState swing;
};

// Which material a cave of this difficulty holds. Exposed so tools/oreprof.cpp
// censuses the SHIPPED thresholds instead of its own copy of them -- a second
// copy is exactly how a calibration silently goes stale.
Material material_for_difficulty(float difficulty);
// Display name of a material -- "Stone", "Reality Shard", ... Exposed for the
// same reason as material_for_difficulty(): the debug menu and
// tools/oreprof.cpp name the tiers from the table the game renders them from,
// rather than each keeping a copy that can drift out of step with it.
const char* material_name(Material m);

void dungeon_generate(DungeonMap* dmap, DungeonEntranceType type,
                      float difficulty, unsigned int seed);
void dungeon_orient_portals(DungeonMap* dmap, float exit_angle);
// from_exit=0: spawn at DNG_ENTRY; from_exit=1: spawn at DNG_EXIT (connected entrance)
void dungeon_player_init(DungeonPlayer* dp, Player* player, const DungeonMap* dmap, int from_exit);
void dungeon_player_update(DungeonPlayer* dp, Player* player, const Input* in,
                           float dt, DungeonMap* dmap, const Camera* cam,
                           bool noclip = false, HarvestResult* out_harvest = nullptr);
void dungeon_draw(const DungeonMap* dmap, const DungeonPlayer* dplayer,
                  const Camera* cam, SDL_Renderer* ren, bool show_all = false);
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
