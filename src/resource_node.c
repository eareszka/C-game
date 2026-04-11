#include "resource_node.h"
#include <math.h>

static int abs_int(int v) 
{
    return v < 0 ? -v : v;
}

void resource_nodes_init(ResourceNodeList* list) 
{
    list->count = 0;
}

void resource_nodes_add(ResourceNodeList* list, ResourceType type, float x, float y) 
{
    if (list->count >= MAX_RESOURCE_NODES) return;

    ResourceNode* n = &list->nodes[list->count++];
    n->type = type;
    n->x = x;
    n->y = y;
    n->width = 32;
    n->height = 32;
    n->alive = 1;

    switch (type) {
        case RESOURCE_TREE:   n->hp = 3; break;
        case RESOURCE_ROCK:   n->hp = 4; break;
        case RESOURCE_FLOWER: n->hp = 1; break;
    }
}

void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren, SDL_Texture* atlas) 
{
    for (int i = 0; i < list->count; i++) 
    {
        const ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        int screen_x = (int)(n->x - cam->x);
        int screen_y = (int)(n->y - cam->y);

        SDL_Rect src = {0, 0, 16, 16};

        switch (n->type) {
            case RESOURCE_TREE:   src.x = 37;  src.y = 1; break;
            case RESOURCE_ROCK:   src.x = 73; src.y = 1; break;
            case RESOURCE_FLOWER: src.x = 37; src.y = 1; break;
        }

        SDL_Rect dst = {screen_x, screen_y, n->width, n->height};
        SDL_RenderCopy(ren, atlas, &src, &dst);
    }
}

int resource_nodes_try_hit(ResourceNodeList* list, float player_x, float player_y, int range) 
{
    for (int i = 0; i < list->count; i++) 
    {
        ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        int dx = (int)(n->x - player_x);
        int dy = (int)(n->y - player_y);

        if (abs_int(dx) <= range && abs_int(dy) <= range) {
            n->hp--;

            if (n->hp <= 0) 
            {
                n->alive = 0;
                return 1; // destroyed
            }
            return 2; // hit but not destroyed
        }
    }
    return 0; // nothing hit
}

