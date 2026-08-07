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
    n->hides_entrance = 0;
    n->reveal_tile_id = 0;
    n->reveal_tx = -1;
    n->reveal_ty = -1;

    switch (type) {
        case RESOURCE_TREE:        n->hp = 3; break;
        case RESOURCE_ROCK:        n->hp = 4; break;
        case RESOURCE_FLOWER:      n->hp = 1; break;
        case RESOURCE_GOLD:        n->hp = 5; break;
        case RESOURCE_GRAVESTONE:  n->hp = 2; break;
    }
}

void resource_nodes_add_gravestone(ResourceNodeList* list, float x, float y,
                                   int hides_entrance, int reveal_tile_id,
                                   int reveal_tx, int reveal_ty)
{
    if (list->count >= MAX_RESOURCE_NODES) return;
    resource_nodes_add(list, RESOURCE_GRAVESTONE, x, y);
    ResourceNode* n = &list->nodes[list->count - 1];
    n->hides_entrance  = hides_entrance;
    n->reveal_tile_id  = reveal_tile_id;
    n->reveal_tx       = hides_entrance ? reveal_tx : -1;
    n->reveal_ty       = hides_entrance ? reveal_ty : -1;
}

// ASCII placeholder colors for resource nodes
// Tree: dark green box with 'T' cross, Rock: grey box with 'o', Flower: purple with '*'
static void draw_resource_ascii(SDL_Renderer* ren, int screen_x, int screen_y,
                                int w, int h, ResourceType type) {
    // Background color
    switch (type) {
        case RESOURCE_TREE:       SDL_SetRenderDrawColor(ren,   0,  80,   0, 255); break;
        case RESOURCE_ROCK:       SDL_SetRenderDrawColor(ren,  90,  80,  70, 255); break;
        case RESOURCE_FLOWER:     SDL_SetRenderDrawColor(ren, 100,   0, 120, 255); break;
        case RESOURCE_GOLD:       SDL_SetRenderDrawColor(ren,  60,  55,  50, 255); break;
        case RESOURCE_GRAVESTONE: SDL_SetRenderDrawColor(ren,  55,  55,  60, 255); break;
    }
    SDL_Rect bg = { screen_x, screen_y, w, h };
    SDL_RenderFillRect(ren, &bg);

    // Simple foreground mark
    int cx = screen_x + w / 2;
    int cy = screen_y + h / 2;
    int t  = h / 8; // thickness

    SDL_SetRenderDrawColor(ren, type == RESOURCE_GOLD ? 255 : 200,
                               type == RESOURCE_GOLD ? 210 : 200,
                               type == RESOURCE_GOLD ?  40 : 200, 255);
    switch (type) {
        case RESOURCE_GOLD: {
            // diamond shape
            SDL_Rect top = { cx - w/4, cy - h/2 + t, w/2, h/4 };
            SDL_Rect mid = { cx - w/3, cy - h/4,     w*2/3, h/2 };
            SDL_Rect bot = { cx - w/4, cy + h/4 - t, w/2, h/4 };
            SDL_RenderFillRect(ren, &top);
            SDL_RenderFillRect(ren, &mid);
            SDL_RenderFillRect(ren, &bot);
            break;
        }
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
        case RESOURCE_GRAVESTONE: {
            // Tombstone: rounded top slab + cross
            SDL_SetRenderDrawColor(ren, 160, 160, 168, 255);
            // slab body
            SDL_Rect slab = { screen_x + w/5, screen_y + h/4, w*3/5, h*2/3 };
            SDL_RenderFillRect(ren, &slab);
            // rounded top (small rect above slab)
            SDL_Rect top = { screen_x + w/4, screen_y + h/8, w/2, h/4 + t };
            SDL_RenderFillRect(ren, &top);
            // cross engraved (darker)
            SDL_SetRenderDrawColor(ren, 80, 80, 88, 255);
            SDL_Rect cv = { cx - t, screen_y + h/3, t*2, h/3 };
            SDL_Rect ch = { screen_x + w/3, screen_y + h*5/12, w/3, t*2 };
            SDL_RenderFillRect(ren, &cv);
            SDL_RenderFillRect(ren, &ch);
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

void resource_nodes_draw(const ResourceNodeList* list, const Camera* cam, SDL_Renderer* ren, SDL_Texture* tileset_tex)
{
    float z = cam->zoom;
    for (int i = 0; i < list->count; i++)
    {
        const ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        int screen_x = (int)((n->x - cam->x) * z);
        int screen_y = (int)((n->y - cam->y) * z);
        int w = (int)(n->width * z);
        int h = (int)(n->height * z);

        if (n->type == RESOURCE_TREE && tileset_tex) {
            // Single-tile tree resource: (row=1, col=15) in the tileset atlas
            SDL_Rect src = { 15 * 16, 1 * 16, 16, 16 };
            SDL_Rect dst = { screen_x, screen_y, w, h };
            SDL_RenderCopy(ren, tileset_tex, &src, &dst);
        } else {
            draw_resource_ascii(ren, screen_x, screen_y, w, h, n->type);
        }
    }
}

bool resource_node_solid(const void* vlist, float px, float py) {
    const ResourceNodeList* list = static_cast<const ResourceNodeList*>(vlist);
    for (int i = 0; i < list->count; i++) {
        const ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;
        if (px >= n->x && px < n->x + n->width &&
            py >= n->y && py < n->y + n->height) return true;
    }
    return false;
}

void harvest_add(HarvestResult* r, float x, float y, int resource, int destroyed)
{
    if (!r || r->count >= MAX_HARVEST_HITS) return;
    HarvestHit* h = &r->hits[r->count++];
    h->x = x;
    h->y = y;
    h->resource  = resource;
    h->destroyed = destroyed;
}

bool harvest_any_destroyed(const HarvestResult* r)
{
    if (!r) return false;
    for (int i = 0; i < r->count; i++)
        if (r->hits[i].destroyed) return true;
    return false;
}

// Flowers are hittable but pay nothing, so they report -1 and no inventory
// entry is credited for them.
static int node_award(ResourceType t)
{
    switch (t) {
        case RESOURCE_TREE:       return (int)RESOURCE_TREE;
        case RESOURCE_ROCK:       return (int)RESOURCE_ROCK;
        case RESOURCE_GOLD:       return (int)RESOURCE_GOLD;
        case RESOURCE_GRAVESTONE: return (int)RESOURCE_ROCK;  // gravestones give rock
        default:                  return -1;
    }
}

// World y grows downward, so atan2(dy, dx) increases clockwise on screen — the
// blade just needs its angle to rise over the swing.
float sweep_relative_angle(float start_ang, float dx, float dy)
{
    const float TWO_PI = 6.2831853f;
    float rel = atan2f(dy, dx) - start_ang;
    rel = fmodf(rel, TWO_PI);
    if (rel < 0.0f) rel += TWO_PI;
    return rel;
}

int resource_nodes_sweep(ResourceNodeList* list, float player_x, float player_y,
                         float radius, float start_ang, float rel0, float rel1,
                         WeaponType weapon, HarvestResult* out)
{
    int struck = 0;
    for (int i = 0; i < list->count; i++)
    {
        ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        float cx = n->x + n->width  * 0.5f;
        float cy = n->y + n->height * 0.5f;
        float dx = cx - player_x, dy = cy - player_y;
        if (dx*dx + dy*dy > radius * radius) continue;

        // Half-open span, so a node is struck exactly once per turn however the
        // frame boundaries happen to fall.
        float rel = sweep_relative_angle(start_ang, dx, dy);
        if (rel < rel0 || rel >= rel1) continue;

        n->hp -= weapon_harvest_damage(weapon, n->type == RESOURCE_TREE);
        int destroyed = 0;
        if (n->hp <= 0) { n->alive = 0; destroyed = 1; }

        harvest_add(out, cx, cy, node_award(n->type), destroyed);
        struck++;
    }
    return struck;
}

int resource_nodes_try_hit(ResourceNodeList* list, float player_x, float player_y,
                           int range, WeaponType weapon, HarvestResult* out)
{
    const bool sweep = weapon_sweeps(weapon);
    int struck = 0;

    for (int i = 0; i < list->count; i++)
    {
        ResourceNode* n = &list->nodes[i];
        if (!n->alive) continue;

        float cx = n->x + n->width  * 0.5f;
        float cy = n->y + n->height * 0.5f;
        int dx = (int)(cx - player_x);
        int dy = (int)(cy - player_y);
        if (abs_int(dx) > range || abs_int(dy) > range) continue;

        n->hp -= weapon_harvest_damage(weapon, n->type == RESOURCE_TREE);
        int destroyed = 0;
        if (n->hp <= 0) { n->alive = 0; destroyed = 1; }

        harvest_add(out, cx, cy, node_award(n->type), destroyed);
        struck++;

        if (!sweep) break;   // single-target weapons stop at the first node
    }
    return struck;
}

