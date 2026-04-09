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

// ASCII placeholder colors for resource nodes
// Tree: dark green box with 'T' cross, Rock: grey box with 'o', Flower: purple with '*'
static void draw_resource_ascii(SDL_Renderer* ren, int screen_x, int screen_y,
                                int w, int h, ResourceType type) {
    // Background color
    switch (type) {
        case RESOURCE_TREE:   SDL_SetRenderDrawColor(ren,   0,  80,   0, 255); break;
        case RESOURCE_ROCK:   SDL_SetRenderDrawColor(ren,  90,  80,  70, 255); break;
        case RESOURCE_FLOWER: SDL_SetRenderDrawColor(ren, 100,   0, 120, 255); break;
    }
    SDL_Rect bg = { screen_x, screen_y, w, h };
    SDL_RenderFillRect(ren, &bg);

    // Simple foreground mark
    int cx = screen_x + w / 2;
    int cy = screen_y + h / 2;
    int t  = h / 8; // thickness

    SDL_SetRenderDrawColor(ren, 200, 200, 200, 255);
    switch (type) {
        case RESOURCE_TREE: {
            // vertical bar
            SDL_Rect v = { cx - t, screen_y + t, t * 2, h - t * 2 };
            SDL_RenderFillRect(ren, &v);
            // horizontal bar (top third)
            SDL_Rect hz = { screen_x + t, screen_y + h / 3, w - t * 2, t * 2 };
            SDL_RenderFillRect(ren, &hz);
            break;
        }
        case RESOURCE_ROCK: {
            // circle approximation: filled center square
            SDL_Rect c = { cx - w/4, cy - h/4, w/2, h/2 };
            SDL_RenderFillRect(ren, &c);
            break;
        }
        case RESOURCE_FLOWER: {
            // '*' — center dot + 4 petals
            SDL_Rect dot = { cx - t, cy - t, t * 2, t * 2 };
            SDL_RenderFillRect(ren, &dot);
            SDL_Rect up  = { cx - t, screen_y + t,  t * 2, h/3 };
            SDL_Rect dn  = { cx - t, cy + t,         t * 2, h/3 };
            SDL_Rect lt  = { screen_x + t,  cy - t, w/3, t * 2 };
            SDL_Rect rt  = { cx + t,         cy - t, w/3, t * 2 };
            SDL_RenderFillRect(ren, &up);
            SDL_RenderFillRect(ren, &dn);
            SDL_RenderFillRect(ren, &lt);
            SDL_RenderFillRect(ren, &rt);
            break;
        }
    }
}

void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren)
{
    float z = cam->zoom;
    for (int i = 0; i < list->count; i++)
    {
        const ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        int screen_x = (int)((n->x - cam->x) * z);
        int screen_y = (int)((n->y - cam->y) * z);

        draw_resource_ascii(ren, screen_x, screen_y,
                            (int)(n->width * z), (int)(n->height * z), n->type);
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

