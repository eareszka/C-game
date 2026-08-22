#ifndef TILEMAP_H
#define TILEMAP_H

#include <SDL2/SDL.h>
#include "camera.h"
#include "resource_node.h"   // HarvestResult, WeaponType

#define MAP_WIDTH  3000
#define MAP_HEIGHT 3000
#define TILE_SIZE  32

enum TileId {
    TILE_GRASS   = 0,
    TILE_PATH    = 1,
    TILE_TREE    = 2,
    TILE_WATER   = 3,
    TILE_CLIFF   = 4,  // elevation 1 (lowest)
    TILE_ROCK    = 5,
    TILE_RIVER   = 6,
    TILE_HUB     = 7,
    TILE_CLIFF_2      = 8,  // elevation 2
    TILE_CLIFF_3      = 9,  // elevation 3
    TILE_CLIFF_4      = 10, // elevation 4
    TILE_CLIFF_5      = 11, // elevation 5 (highest)
    TILE_CLIFF_EDGE_1 = 12, // south face: drop from elev 1 → 0
    TILE_CLIFF_EDGE_2 = 13, // south face: drop from elev 2 → 1
    TILE_CLIFF_EDGE_3 = 14, // south face: drop from elev 3 → 2
    TILE_CLIFF_EDGE_4 = 15, // south face: drop from elev 4 → 3
    TILE_CLIFF_EDGE_5 = 16, // south face: drop from elev 5 → 4
    TILE_SAND         = 17, // desert biome ground
    TILE_SNOW         = 18, // snow biome (map edges)
    TILE_WASTELAND    = 19, // wasteland biome (map edges)
    TILE_LAVA         = 20, // lava pools/streams inside wasteland
    TILE_MEADOW       = 21, // open plains biome (sparse trees)
    TILE_POND         = 22, // small water features inside meadows
    TILE_GOLD_ORE     = 23, // gold ore vein — spawns at high elevation / in caves
    // Snow-biome cliff variants (body only — edges stay brown)
    TILE_CLIFF_SNOW_1 = 24,
    TILE_CLIFF_SNOW_2 = 25,
    TILE_CLIFF_SNOW_3 = 26,
    TILE_CLIFF_SNOW_4 = 27,
    TILE_CLIFF_SNOW_5 = 28,
    // Wasteland-biome cliff variants (body only — edges stay brown)
    TILE_CLIFF_WASTE_1 = 29,
    TILE_CLIFF_WASTE_2 = 30,
    TILE_CLIFF_WASTE_3 = 31,
    TILE_CLIFF_WASTE_4 = 32,
    TILE_CLIFF_WASTE_5 = 33,
    // West side-face tiles (one per elevation layer, same brown gradient as edges).
    // East faces and the north back face have their own ids further down: the
    // art draws all three differently, the west and east being mirrors of each
    // other and the back face being the rim seen from above.
    TILE_CLIFF_SIDE_1 = 34,
    TILE_CLIFF_SIDE_2 = 35,
    TILE_CLIFF_SIDE_3 = 36,
    TILE_CLIFF_SIDE_4 = 37,
    TILE_CLIFF_SIDE_5 = 38,
    // SW outer corner (where south face meets west/east side face at bottom-left)
    TILE_CLIFF_CORNER_SW_1 = 39,
    TILE_CLIFF_CORNER_SW_2 = 40,
    TILE_CLIFF_CORNER_SW_3 = 41,
    TILE_CLIFF_CORNER_SW_4 = 42,
    TILE_CLIFF_CORNER_SW_5 = 43,
    // SE outer corner (where south face meets east/west side face at bottom-right)
    TILE_CLIFF_CORNER_SE_1 = 44,
    TILE_CLIFF_CORNER_SE_2 = 45,
    TILE_CLIFF_CORNER_SE_3 = 46,
    TILE_CLIFF_CORNER_SE_4 = 47,
    TILE_CLIFF_CORNER_SE_5 = 48,
    // NW inner corner (concave: where north back-face meets west side-face)
    TILE_CLIFF_CORNER_NW_1 = 49,
    TILE_CLIFF_CORNER_NW_2 = 50,
    TILE_CLIFF_CORNER_NW_3 = 51,
    TILE_CLIFF_CORNER_NW_4 = 52,
    TILE_CLIFF_CORNER_NW_5 = 53,
    // NE inner corner (concave: where north back-face meets east side-face)
    TILE_CLIFF_CORNER_NE_1 = 54,
    TILE_CLIFF_CORNER_NE_2 = 55,
    TILE_CLIFF_CORNER_NE_3 = 56,
    TILE_CLIFF_CORNER_NE_4 = 57,
    TILE_CLIFF_CORNER_NE_5 = 58,
    // Dungeon entrance (4x4 tile stamp, solid dark archway)
    TILE_DUNGEON = 59,
    // Blueprint placeholder — marks unconfigured cells inside a town footprint
    TILE_BLUEPRINT = 60,
    // Village placeholder — orange/black checkerboard until sprites are added
    TILE_VILLAGE_PLACEHOLDER = 61,
    // Castle placeholder — black/white checkerboard until sprites are added
    TILE_CASTLE_PLACEHOLDER = 62,
    // Dungeon entrance variants — one per archetype, replaces generic TILE_DUNGEON
    TILE_DUNGEON_CAVE         = 63,
    TILE_DUNGEON_RUINS        = 64,
    TILE_DUNGEON_GRAVEYARD_SM = 65,
    TILE_DUNGEON_GRAVEYARD_LG = 66,
    TILE_DUNGEON_OASIS        = 67,
    TILE_DUNGEON_PYRAMID      = 68,
    TILE_DUNGEON_STONEHENGE   = 69,
    TILE_DUNGEON_LARGE_TREE   = 70,
    TILE_DEAD_TREE            = 71, // dead bare tree — wasteland biome, always 2-tile tall
    // Bare trail worn through the wasteland. Its own tile so the biome edge
    // system can see it as a region and give it a smoothed outline; walkable,
    // and only ever found inside wasteland.
    TILE_WASTE_TRAIL          = 72,
    // The deck a trail crosses lava on. Placeholder art: the trail routes
    // through lava rather than around it, and every lava tile it crosses
    // becomes one of these — walkable, and only ever found with lava around it.
    TILE_WASTE_BRIDGE         = 73,

    // East side-face, and the north back-face: the rim of the plateau seen from
    // above, one tile deep whatever the elevation, where the side faces stack a
    // tile per layer. All three were one id until the art arrived and drew them
    // as three different things.
    TILE_CLIFF_SIDE_E_1 = 74,
    TILE_CLIFF_SIDE_E_2 = 75,
    TILE_CLIFF_SIDE_E_3 = 76,
    TILE_CLIFF_SIDE_E_4 = 77,
    TILE_CLIFF_SIDE_E_5 = 78,
    TILE_CLIFF_BACK_1   = 79,
    TILE_CLIFF_BACK_2   = 80,
    TILE_CLIFF_BACK_3   = 81,

    // The road between settlements, and the bridge that carries it over water.
    //
    // These two take the numbers of TILE_CLIFF_BACK_4 and _5, which were part of
    // the legacy cliff set that nothing has written since the band stopped being
    // a tile — an audit over five seeds and forty-five million tiles found them
    // never placed. Reusing the numbers rather than appending renumbers nothing:
    // every enumerator here has an explicit value and TILE_TOWN0_BASE is pinned
    // at 84 by two static_asserts and an eighty-four-row style table.
    //
    // The two predicates that swept 74-83 as "side of a mountain" are narrowed
    // to end at TILE_CLIFF_BACK_3, or a road would answer yes to being a cliff
    // face and never draw its own ground.
    TILE_ROAD           = 82,
    TILE_ROAD_BRIDGE    = 83,

    // Tiles sampled from assets/tileset.png (256 cols × 256 rows = 65536 tiles).
    // Index within sheet = (tile_id - TILE_TOWN0_BASE).
    // col = index % TOWN0_SHEET_COLS,  row = index / TOWN0_SHEET_COLS.
    TILE_TOWN0_BASE = 84,
    TILE_TOWN0_END  = TILE_TOWN0_BASE + 256 * 256 - 1,

    // Tiles sampled from assets/overworld_0.png (18 cols × 8 rows = 144 tiles).
    TILE_OW0_BASE = TILE_TOWN0_BASE + 256 * 256,
    TILE_OW0_END  = TILE_OW0_BASE + 18 * 8 - 1,
};

#define TOWN0_SHEET_COLS 256
#define TOWN0_SHEET_ROWS 256

typedef enum {
    DUNGEON_ENT_CAVE         = 0,
    DUNGEON_ENT_RUINS        = 1,
    DUNGEON_ENT_GRAVEYARD_SM = 2,
    DUNGEON_ENT_GRAVEYARD_LG = 3,
    DUNGEON_ENT_OASIS        = 4,
    DUNGEON_ENT_PYRAMID      = 5,
    DUNGEON_ENT_STONEHENGE   = 6,
    DUNGEON_ENT_LARGE_TREE   = 7,
    // A massive graveyard. Appended rather than slotted beside the other two
    // graveyards on purpose: `type` is XOR'd into the interior seed
    // (dungeon.cpp's dungeon_generate), so renumbering the enum would silently
    // regenerate every existing world's dungeon interiors.
    //
    // It has no tile id of its own and reuses TILE_DUNGEON_GRAVEYARD_LG. The
    // tile decides only the overworld square's art and answers the two
    // contiguous "is this a dungeon" range tests; the archetype is read from
    // this record, not from the ground. Every entrance tile but LARGE_TREE
    // draws the same solid black square anyway, so a dedicated id would buy
    // nothing today and cost the renumbering described above TILE_ROAD.
    DUNGEON_ENT_CATACOMBS    = 8,
    // Keep last — the number of archetypes, not an archetype. Every table keyed
    // by type and every range clamp on one is sized from this, because the way
    // this enum grows is somebody adding a value and a [8] somewhere quietly
    // reading past its end or clamping the new type back onto CAVE.
    DUNGEON_ENT_COUNT
} DungeonEntranceType;

// The graveyard family is three scales of one archetype. Three separate things
// need to agree on who belongs to it and which of two is bigger: the pairing
// pass links them across scales, entering through a smaller one's mouth
// generates its partner's larger interior, and the gravestone spawner has to
// recognise all of them. Each used to hard-code the SM/LG pair inline, which is
// how a third scale gets silently left out of one of the three.
static inline int dungeon_graveyard_rank(DungeonEntranceType t) {
    switch (t) {
        case DUNGEON_ENT_GRAVEYARD_SM: return 0;
        case DUNGEON_ENT_GRAVEYARD_LG: return 1;
        case DUNGEON_ENT_CATACOMBS:    return 2;
        default:                       return -1;   // not a graveyard at all
    }
}
static inline bool dungeon_is_graveyard(DungeonEntranceType t) {
    return dungeon_graveyard_rank(t) >= 0;
}

typedef struct {
    int x, y;                  // top-left tile coordinate of the entrance stamp
    int size;                  // 0 = small (1×1 tile), 1 = large (2×2 tiles)
    DungeonEntranceType type;  // entrance archetype — drives interior layout + skin
    int cliff_level;           // 0 = flat, 1–5 = elevation tier at placement
    float difficulty;          // 0.0–1.0: straight average of dist_norm and elev_norm
    int gravestones_spawned;   // every graveyard kind: 0 until resource nodes are spawned
    int partner_idx;           // index into dungeon_entrances[] of connected partner, or -1
    // A cave system's mouths all carry the same anchor — the top-left of the
    // landform they were cut into — and the interior is seeded from it rather
    // than from each mouth's own position, which is what makes every mouth of
    // one mountain open the same cave. -1,-1 on everything else.
    //
    // The struct is built with positional aggregate initialisers in three
    // places, so a field added here silently zero-inits at any site not updated
    // with it — and 0,0 is a legal tile. All three sites set these explicitly.
    int cave_anchor_x, cave_anchor_y;
} DungeonEntrance;

typedef struct {
    int x, y;    // top-left tile coordinate where the town was stamped
    int index;   // which of the hand-crafted towns this is
} TownPlacement;

#define MAX_INTERIOR_DOORS 128

typedef struct {
    int x, y;        // world tile of the door's left tile (bottom row of the building sprite)
    int w;           // door width in tiles
    int interior_id; // which interior layout this door opens into
} InteriorDoor;

typedef struct {
    int x, y;    // top-left tile coordinate where the village was stamped
    int variant; // which of the village blueprint variants was used
} VillagePlacement;

typedef struct {
    int x, y;
    int type; // 0=ocean, 1=mountain, 2=lava, 3=dungeon (placed via dungeon diving)
} CastlePlacement;

// The placement pass aims for TARGET *ordinary* entrances and the array used to
// be exactly that many, so it ran to capacity with nothing spare. Cave systems
// are placed first and separately — a mountain spends up to four records on one
// site, a mouth in the face and one on each storey's top — and on a world with
// many small landforms that is a few hundred records before the ordinary rolls
// begin. The array carries both, so it needs room for both.
#define MAX_DUNGEON_ENTRANCES 2048

enum RouteKind { ROUTE_NONE = 0, ROUTE_TRAIL = 1, ROUTE_ROAD = 2 };

typedef struct Tilemap {
    int tiles[MAP_HEIGHT][MAP_WIDTH];
    int overlay[MAP_HEIGHT][MAP_WIDTH]; // trees, rocks, gold ore — drawn on top of base tile
    uint8_t coll[MAP_HEIGHT][MAP_WIDTH];        // solid collision footprint from editor _coll layer
    uint8_t depth_layer[MAP_HEIGHT][MAP_WIDTH]; // Y-sorted tiles drawn after the player
    // A track worn over the ground rather than replacing it: ROUTE_NONE/TRAIL/ROAD.
    // Its own layer for the same reason a cliff face has one -- the ground it runs
    // over is still there and still has to draw, and a track that overwrote the
    // tile threw away the very thing it needed to know to pick its own colour.
    //
    // Bridges are NOT here. A deck replaces the surface -- you walk on the deck,
    // not on the lava -- so it stays a real tile, and three separate solidity
    // paths depend on it being one.
    uint8_t route[MAP_HEIGHT][MAP_WIDTH];
    float cliff_peak_x, cliff_peak_y; // debug: gradient peak for minimap dot
    DungeonEntrance dungeon_entrances[MAX_DUNGEON_ENTRANCES];
    int num_dungeon_entrances;
    TownPlacement    towns[3];         // filled during phase2
    VillagePlacement villages[15];     // filled during phase2
    int num_villages;
    InteriorDoor doors[MAX_INTERIOR_DOORS]; // building doors, registered at stamp time
    int num_doors;
    CastlePlacement  castles[4];       // [0-2] placed in phase2; [3] placed via dungeon diving
} Tilemap;

// Forward declare to avoid circular include — resource_node.h includes no tilemap types.
struct ResourceNodeList;

void tilemap_build_starting_area(Tilemap* map, unsigned int seed);
// Phase 1: core map + detail within PHASE_RADIUS of center (call before game loop)
void tilemap_build_overworld_phase1(Tilemap* map, unsigned int seed);
// Phase 2: detail outside PHASE_RADIUS (run on a background thread)
void tilemap_build_overworld_phase2(Tilemap* map, unsigned int seed);

void tilemap_update(float dt); // advance hit-jitter timers
void tilemap_draw_base (const Tilemap* map, const Camera* cam, SDL_Renderer* renderer, float = 0);
void tilemap_draw_depth(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer, float = 0);
// Debug overlay: thin lines around every TILE_SIZE grid cell in view, labeled
// with the tileset (col,row) the tile draws from -- see definition for the
// ground-cover-variant caveat.
void tilemap_draw_debug_grid(const Tilemap* map, const Camera* cam, SDL_Renderer* renderer);

// Pre-render all tile types into small textures so tilemap_draw uses one RenderCopy
// per tile instead of ~65 RenderFillRect calls. Call once after creating the renderer.
void tilemap_init_tile_cache(SDL_Renderer* renderer);
void tilemap_free_tile_cache(void);
// Returns the town/overworld tileset texture (16px-per-tile atlas). Valid after tilemap_init_tile_cache.
SDL_Texture* tilemap_get_town_tex(void);

// Hit a tree or rock tile near (px, py) within `range` pixels.
// Tall trees (two stacked TILE_TREE) share an HP pool and require more hits.
// Strike harvestable overlay tiles (trees, rocks, ore) within `range`. The
// weapon decides damage and whether every tile in range is struck or only the
// nearest. Destroys tiles on depletion, appends to *out, returns tiles struck.
int tilemap_try_hit(Tilemap* map, float px, float py, int range,
                    WeaponType weapon, HarvestResult* out);

// Tile counterpart of resource_nodes_sweep: strike harvestable overlay tiles
// whose centre the blade crossed this frame.
int tilemap_sweep(Tilemap* map, float px, float py, float radius,
                  float start_ang, float rel0, float rel1,
                  WeaponType weapon, HarvestResult* out);

// Tile counterparts of the thrust pair.
float tilemap_first_along(const Tilemap* map, float px, float py,
                          float angle, float half_width, float max_reach);
int tilemap_thrust(Tilemap* map, float px, float py, float angle,
                   float half_width, float from, float to,
                   WeaponType weapon, HarvestResult* out);

// Strike the harvestable tile a point lands on, if any. Returns 1 if struck.
int tilemap_strike_point(Tilemap* map, float x, float y,
                         WeaponType weapon, HarvestResult* out);

void minimap_draw(const Tilemap* map, SDL_Renderer* renderer,
                  int screen_w, int screen_h,
                  float player_x, float player_y);

bool tilemap_is_walkable(const Tilemap* map, int tile_x, int tile_y);
// TileSolidFn-compatible wrapper: returns true if pixel (px,py) is on a non-walkable tile.
bool tilemap_pixel_solid(const void* map, float px, float py);

// GRAVEYARD_SM entrances hide their entrance tile under gravestones.
// Call this from the main thread (not the gen thread) when the player gets close.
// Scatters 5–10 RESOURCE_GRAVESTONE nodes; one hides the entrance tile.
// seed should be derived from the world seed + entrance position.
// GRAVEYARD_SM: hidden entrance under one of 5–10 randomly scattered gravestones.
void tilemap_spawn_graveyard_nodes(Tilemap* map, ResourceNodeList* resources,
                                   int entrance_idx, unsigned int seed);

// The two visible-yard scales, GRAVEYARD_LG and CATACOMBS: gravestones in rows
// inside the fence, filling half to three quarters of the slots the yard has
// room for — 18–28 for a large graveyard, proportionally more for a catacombs.
void tilemap_spawn_graveyard_lg_nodes(Tilemap* map, ResourceNodeList* resources,
                                      int entrance_idx, unsigned int seed);

// Convert a minimap screen click (mx, my) to world pixel coords.
// Returns true if the click was inside the minimap area.
bool minimap_click_to_world(int screen_w, int screen_h, int mx, int my,
                             float* out_world_x, float* out_world_y);

// Signal the background generation thread to abort early (call before join on shutdown).
void tilemap_cancel_gen();
void tilemap_reset_gen_cancel();

bool tilemap_face_at(int x, int y);

#endif
