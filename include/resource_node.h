#ifndef RESOURCE_NODE_H
#define RESOURCE_NODE_H

#include <SDL2/SDL.h>
#include "camera.h"
#include "entity.h"   // WeaponType, weapon_harvest_damage, weapon_sweeps

#define MAX_RESOURCE_NODES 512

typedef enum ResourceType
{
    RESOURCE_TREE,
    RESOURCE_ROCK,
    RESOURCE_FLOWER,
    RESOURCE_GOLD,
    RESOURCE_GRAVESTONE,
} ResourceType;

typedef struct ResourceNode
{
    ResourceType type;
    float x;
    float y;
    int width;
    int height;
    int hp;
    int alive;

    // Gravestone-specific: when hides_entrance=1 and this node is destroyed,
    // the dungeon entrance tile is stamped at (reveal_tx, reveal_ty).
    // reveal_tx is set to -1 after the reveal is processed.
    int hides_entrance;
    int reveal_tile_id;
    int reveal_tx, reveal_ty;
} ResourceNode;

typedef struct ResourceNodeList 
{
    ResourceNode nodes[MAX_RESOURCE_NODES];
    int count;
} ResourceNodeList;

void resource_nodes_init(ResourceNodeList* list);
void resource_nodes_add(ResourceNodeList* list, ResourceType type, float x, float y);
// Add a gravestone; if hides_entrance=1, destroying it reveals the dungeon tile at (reveal_tx, reveal_ty).
void resource_nodes_add_gravestone(ResourceNodeList* list, float x, float y,
                                   int hides_entrance, int reveal_tile_id,
                                   int reveal_tx, int reveal_ty);
void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren, SDL_Texture* tileset_tex);
// ── Harvest results ─────────────────────────────────────────────────────────
// One swing can now strike several things at once (a scythe sweeps everything
// in range), so a swing reports a list rather than a single outcome. Tile-based
// trees and rocks report into the same struct, which is why `resource` is a
// plain int: it holds a ResourceType, or -1 for something that awards nothing.
#define MAX_HARVEST_HITS 64

typedef struct HarvestHit {
    float x, y;      // centre of what was struck, for the floating "+1"
    int   resource;  // ResourceType awarded, or -1 for none (e.g. flowers)
    int   destroyed; // 1 if this hit finished it off
} HarvestHit;

typedef struct HarvestResult {
    int        count;
    HarvestHit hits[MAX_HARVEST_HITS];
} HarvestResult;

// Append a hit; silently ignores overflow past MAX_HARVEST_HITS.
void harvest_add(HarvestResult* r, float x, float y, int resource, int destroyed);
// True if any hit in the result finished something off.
bool harvest_any_destroyed(const HarvestResult* r);

// Strike nodes within `range` of the player. The weapon decides how much damage
// each node takes and whether every node in range is struck or only the first.
// Appends to *out. Returns the number of nodes struck this call.
int resource_nodes_try_hit(ResourceNodeList* list, float player_x, float player_y,
                           int range, WeaponType weapon, HarvestResult* out);

// Strike nodes the blade crossed this frame: those within `radius` whose
// bearing from the player falls in [rel0, rel1) measured clockwise from
// `start_ang`. Each node is therefore struck once per turn of the blade.
int resource_nodes_sweep(ResourceNodeList* list, float player_x, float player_y,
                         float radius, float start_ang, float rel0, float rel1,
                         WeaponType weapon, HarvestResult* out);

// Bearing of (x,y) from the player, folded to [0, 2PI) clockwise from start_ang.
// Shared with the tile sweep so both agree on where the blade is.
float sweep_relative_angle(float start_ang, float dx, float dy);

// Resolve an offset into distance along the thrust line and sideways off it.
// Shared with the tile thrust so both measure the corridor identically.
void thrust_project(float angle, float dx, float dy, float* out_along, float* out_side);

// Distance to the nearest node in the corridor ahead, or -1 if there is none
// within max_reach. This is the "first target" a thrust extends beyond.
float resource_nodes_first_along(const ResourceNodeList* list, float px, float py,
                                 float angle, float half_width, float max_reach);

// Strike nodes the thrust head passed this frame: those in the corridor whose
// distance along the line falls in [from, to). Half-open for the same reason as
// the sweep — each node is struck once per thrust however the frames land.
int resource_nodes_thrust(ResourceNodeList* list, float px, float py, float angle,
                          float half_width, float from, float to,
                          WeaponType weapon, HarvestResult* out);

// Strike the first node overlapping a point — used by thrown objects, which
// stop at whatever they meet. Returns 1 if something was struck.
int resource_nodes_strike_point(ResourceNodeList* list, float x, float y, float radius,
                                WeaponType weapon, HarvestResult* out);
// TileSolidFn-compatible: returns true if (px,py) is inside any alive tree or rock node.
bool resource_node_solid(const void* list, float px, float py);

#endif

