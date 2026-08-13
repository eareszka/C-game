#include "collision.h"
#include <cmath>

bool can_occupy(const void* map, float x, float y, TileSolidFn tile_solid) {
    const float x1 = x + HB_X1, x2 = x + HB_X2;
    const float y1 = y + HB_Y1, y2 = y + HB_Y2;
    // The corners first. Anything the size of a wall is met at one of them, and
    // open ground is the answer nearly every time this is asked, so the four
    // that settle both come before the twenty-eight that only find a line.
    if (tile_solid(map, x1, y1) || tile_solid(map, x2, y1) ||
        tile_solid(map, x1, y2) || tile_solid(map, x2, y2)) return false;
    for (float t = x1 + HB_SAMPLE; t < x2; t += HB_SAMPLE)
        if (tile_solid(map, t, y1) || tile_solid(map, t, y2)) return false;
    for (float t = y1 + HB_SAMPLE; t < y2; t += HB_SAMPLE)
        if (tile_solid(map, x1, t) || tile_solid(map, x2, t)) return false;
    return true;
}

// One axis of the move, and a slide across it if that is what it takes.
//
// Refusing the move outright is right for a wall and wrong for everything
// smaller, and until the ground was closed a tile at a time there was nothing
// smaller to be wrong about. There is now: a cliff's silhouette is a row of
// teeth two or three pixels proud of one another, and walking along one the
// feet caught on every single one — the move blocked, the player stopped dead
// against something they could see was a bump. Worse in a notch between two
// teeth, where both axes block at once and the only way out is back the way you
// came, which is not a way anyone finds by pushing forward.
//
// So when the way is blocked, ask how far across it you would have to stand to
// be past the thing blocking it, and go if the answer is small. A wall gives
// the same answer at every offset — still blocked — and still stops you. The
// slide is taken smallest first so the feet move as little as they have to.
// Walked rather than leapt, and never further than an art pixel between tests.
//
// Testing only the far end of the move is the other way a line one pixel across
// is missed, and the worse of the two: at a walk the feet cross two and a half
// pixels between frames, at a sprint five, and on a stalled frame fifteen. The
// drop was south of them one frame and north of them the next with nothing
// asked in between, so the faster you ran at a cliff the more reliably you went
// through it. Neither the width of the slide below nor the fineness of
// can_occupy above can reach that — only asking on the way.
//
// The slide has a budget for the whole move rather than one per step, so that
// a wall run along for fifteen pixels cannot walk the feet sideways by fifteen
// as well.
static bool move_axis(const void* map, float* x, float* y, float d, bool horiz,
                      TileSolidFn tile_solid) {
    int n = (int)(fabsf(d) / HB_SAMPLE) + 1;
    float step = d / (float)n;
    int budget = HB_SLIP;
    bool moved = false;
    for (int i = 0; i < n; i++) {
        float nx = horiz ? *x + step : *x;
        float ny = horiz ? *y : *y + step;
        if (can_occupy(map, nx, ny, tile_solid)) { *x = nx; *y = ny; moved = true; continue; }
        bool slid = false;
        for (int s = 1; s <= budget && !slid; s++)
            for (int k = 0; k < 2 && !slid; k++) {
                float o = k ? (float)s : -(float)s;
                float ox = horiz ? nx : nx + o;
                float oy = horiz ? ny + o : ny;
                if (can_occupy(map, ox, oy, tile_solid)) {
                    *x = ox; *y = oy; budget -= s; moved = slid = true;
                }
            }
        if (!slid) break;
    }
    return moved;
}

bool move_feet(const void* map, float* x, float* y, float dx, float dy,
               TileSolidFn tile_solid) {
    bool moved = false;
    if (dx != 0.0f) moved |= move_axis(map, x, y, dx, true,  tile_solid);
    if (dy != 0.0f) moved |= move_axis(map, x, y, dy, false, tile_solid);
    return moved;
}

bool unwedge_feet(const void* map, float* x, float* y, TileSolidFn tile_solid) {
    if (can_occupy(map, *x, *y, tile_solid)) return false;
    // Nothing above can put the feet here — it only ever accepts a place they
    // fit. The ground gets here on its own: the world finishes generating under
    // the player, or a debug jump lands them inside something. Whatever the
    // cause, every direction then reads as blocked and the only way out is
    // noclip, so walk outward until there is somewhere to stand.
    static const int DX[8] = { 1, -1,  0,  0,  1,  1, -1, -1 };
    static const int DY[8] = { 0,  0,  1, -1,  1, -1,  1, -1 };
    for (int r = 1; r <= 96; r++)
        for (int k = 0; k < 8; k++) {
            float ox = *x + (float)(DX[k] * r), oy = *y + (float)(DY[k] * r);
            if (can_occupy(map, ox, oy, tile_solid)) { *x = ox; *y = oy; return true; }
        }
    return false;
}

