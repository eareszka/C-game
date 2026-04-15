#ifndef RESOURCE_NODE_H
#define RESOURCE_NODE_H

#include <SDL2/SDL.h>
#include "camera.h"

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
void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren);
int resource_nodes_try_hit(ResourceNodeList* list, float player_x, float player_y, int range, float* out_rx, float* out_ry);
// TileSolidFn-compatible: returns true if (px,py) is inside any alive tree or rock node.
bool resource_node_solid(const void* list, float px, float py);

#endif

