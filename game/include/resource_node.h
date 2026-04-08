#ifndef RESOURCE_NODE_H
#define RESOURCE_NODE_H

#include <SDL2/SDL.h>
#include "camera.h"

#define MAX_RESOURCE_NODES 128

typedef enum ResourceType 
{
    RESOURCE_TREE,
    RESOURCE_ROCK,
    RESOURCE_FLOWER
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
} ResourceNode;

typedef struct ResourceNodeList 
{
    ResourceNode nodes[MAX_RESOURCE_NODES];
    int count;
} ResourceNodeList;

void resource_nodes_init(ResourceNodeList* list);
void resource_nodes_add(ResourceNodeList* list, ResourceType type, float x, float y);
void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren);
int resource_nodes_try_hit(ResourceNodeList* list, float player_x, float player_y, int range);

#endif

