#include "floattext.h"
#include "core.h"   // draw_text, text_width
#include <math.h>

void floattext_spawn(FloatText* ft, float wx, float wy, int amount, Uint8 r, Uint8 g, Uint8 b) {
    if (ft->active && fabsf(ft->wx - wx) < 2.0f && fabsf(ft->wy - wy) < 2.0f) {
        ft->count += amount;
        ft->life = 1.0f;
        ft->drift = 0.0f;
    } else {
        *ft = FloatText();
        ft->wx = wx; ft->wy = wy;
        ft->life = 1.0f; ft->active = true; ft->count = amount;
        ft->r = r; ft->g = g; ft->b = b;
    }
    SDL_snprintf(ft->text, sizeof(ft->text), "+%d", ft->count);
}

void floattext_spawn_from_harvest(FloatText* ft, const HarvestResult* h) {
    // One popup per thing broken, showing its whole yield -- what was paid,
    // since a blow that breaks nothing pays nothing.
    for (int i = 0; i < h->count; i++) {
        int res = h->hits[i].resource;
        if (res < 0 || !h->hits[i].destroyed) continue;
        Uint8 r = 180, g = 120, b = 60;
        if      (res == (int)RESOURCE_ROCK) { r = 160; g = 160; b = 160; }
        else if (res == (int)RESOURCE_GOLD) { r = 255; g = 210; b =  40; }
        floattext_spawn(ft, h->hits[i].x, h->hits[i].y, harvest_yield(res), r, g, b);
    }
}

void floattext_update_draw(FloatText* ft, float dt, const Camera* cam, SDL_Renderer* ren) {
    if (!ft->active) return;

    ft->drift += 60.0f * dt;
    ft->life  -= dt;
    if (ft->life <= 0.0f) {
        ft->active = false;
        return;
    }

    int sx = cam_screen_x(cam, ft->wx);
    int sy = cam_screen_y(cam, ft->wy) - (int)ft->drift;
    sx -= text_width(ft->text, 1) / 2;
    float a = ft->life;
    draw_text(ren, ft->text, sx, sy, 1,
             (Uint8)(ft->r * a), (Uint8)(ft->g * a), (Uint8)(ft->b * a));
}
