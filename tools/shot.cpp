// Offscreen overworld screenshot: builds a world and saves a PNG of a window
// onto it, without opening a window. Used to iterate on cliff art.
//
//   shot.exe <seed> <out.png> [tile_x tile_y] [tiles_w tiles_h]
//
// With no tile_x/tile_y it hunts for the densest patch of cliff face in the
// world and centres on that, which is what you want nine times out of ten.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include "tilemap.h"
#include "camera.h"

static Tilemap g_map;

int main(int argc, char** argv)
{
    unsigned seed = (argc > 1) ? (unsigned)strtoul(argv[1], nullptr, 10) : 387u;
    const char* out = (argc > 2) ? argv[2] : "shot.png";
    int want_x = (argc > 4) ? atoi(argv[3]) : -1;
    int want_y = (argc > 4) ? atoi(argv[4]) : -1;
    int tw = (argc > 6) ? atoi(argv[5]) : 44;
    int th = (argc > 6) ? atoi(argv[6]) : 30;

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);

    // SHOT_WALK=1 draws the whole world one pixel to the tile, black where the
    // ground cannot be crossed. Whether a plateau is sealed is a question about
    // a whole landform and its surroundings, and SHOT_MASK cannot answer it: a
    // tile that is both one level's surface and the next level's ring draws as
    // its own level there, so a ring lying on high ground is invisible.
    if (getenv("SHOT_WALK")) {
        SDL_Surface* m = SDL_CreateRGBSurfaceWithFormat(0, MAP_WIDTH, MAP_HEIGHT, 32,
                                                        SDL_PIXELFORMAT_RGBA32);
        SDL_Renderer* mr = SDL_CreateSoftwareRenderer(m);
        tilemap_init_tile_cache(mr);
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        uint32_t* px = (uint32_t*)m->pixels;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++)
                px[y * (m->pitch / 4) + x] =
                    tilemap_is_walkable(&g_map, x, y) ? 0xFFFFFFFFu : 0xFF000000u;
        IMG_SavePNG(m, out);
        printf("wrote %s (%dx%d, one pixel to the tile, black is solid) seed %u\n",
               out, MAP_WIDTH, MAP_HEIGHT, seed);
        return 0;
    }

    // SHOT_MASK=1 draws the whole world one pixel to the tile instead of a
    // window of it. The shape of a landform is a question about hundreds of
    // tiles at once, and a 44-tile window cannot answer it — every boundary
    // looks straight through a slot that narrow.
    if (getenv("SHOT_MASK")) {
        SDL_Surface* m = SDL_CreateRGBSurfaceWithFormat(0, MAP_WIDTH, MAP_HEIGHT, 32,
                                                        SDL_PIXELFORMAT_RGBA32);
        SDL_Renderer* mr = SDL_CreateSoftwareRenderer(m);
        tilemap_init_tile_cache(mr);
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        uint32_t* px = (uint32_t*)m->pixels;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int t = g_map.tiles[y][x];
                int lv = 0;
                if (t == TILE_CLIFF || t == TILE_CLIFF_SNOW_1 || t == TILE_CLIFF_WASTE_1) lv = 1;
                if (t == TILE_CLIFF_2 || t == TILE_CLIFF_SNOW_2 || t == TILE_CLIFF_WASTE_2) lv = 2;
                if (t == TILE_CLIFF_3 || t == TILE_CLIFF_SNOW_3 || t == TILE_CLIFF_WASTE_3) lv = 3;
                uint32_t c = 0xFF201810u;
                if (lv == 1) c = 0xFF4090F0u;
                if (lv == 2) c = 0xFF40F0F0u;
                if (lv == 3) c = 0xFFFFFFFFu;
                else if (!lv && tilemap_face_at(x, y)) c = 0xFF3050A0u;
                px[y * (m->pitch / 4) + x] = c;
            }
        IMG_SavePNG(m, out);
        printf("wrote %s (%dx%d, one pixel to the tile) seed %u\n", out,
               MAP_WIDTH, MAP_HEIGHT, seed);
        return 0;
    }

    int W = tw * TILE_SIZE, H = th * TILE_SIZE;
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    if (!ren) { printf("renderer: %s\n", SDL_GetError()); return 1; }

    tilemap_init_tile_cache(ren);
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);

    if (want_x < 0) {
        // Densest block of cliff top, on a coarse grid. `kind` picks which
        // family to hunt for so the snow and wasteland sets can be looked at
        // without knowing where in a 3000-tile world they landed.
        const char* kind = getenv("SHOT_KIND");
        int lo = TILE_CLIFF, hi = TILE_CLIFF_3;
        if (kind && kind[0] == 's') { lo = TILE_CLIFF_SNOW_1;  hi = TILE_CLIFF_SNOW_3; }
        if (kind && kind[0] == 'w') { lo = TILE_CLIFF_WASTE_1; hi = TILE_CLIFF_WASTE_3; }
        int best = -1, bx = MAP_WIDTH / 2, by = MAP_HEIGHT / 2;
        for (int y = 0; y + th < MAP_HEIGHT; y += th / 2)
        for (int x = 0; x + tw < MAP_WIDTH;  x += tw / 2) {
            int n = 0;
            for (int j = y; j < y + th; j += 2)
            for (int i = x; i < x + tw; i += 2) {
                int t = g_map.tiles[j][i];
                if (t >= lo && t <= hi) n++;
            }
            if (n > best) { best = n; bx = x; by = y; }
        }
        want_x = bx; want_y = by;
        printf("centred on tile %d,%d (%d cliff samples)\n", bx, by, best);
    }

    // SHOT_SOLID=1 draws the same window the picture covers, black where the
    // ground is closed — but one pixel to the art pixel rather than one to the
    // tile, which is what SHOT_WALK gives.
    //
    // Sixteen times finer, because the ground is no longer closed a tile at a
    // time. Comparing where the rock is drawn against where the player is
    // stopped is the whole of tools/collide_check.py, and a tile-resolution
    // answer cannot say anything about a disagreement that is now measured in
    // ones and twos of a pixel.
    //
    // Grey where something that is not the cliff closed the tile — a boulder, a
    // tree, a seam of ore. Those stop the player a whole tile at a time and
    // always have, and left as black they read as the cliff being a tile out:
    // one boulder standing off the foot of a face put sixteen pixels of error
    // into every column it stood in.
    if (getenv("SHOT_SOLID")) {
        int mw = tw * 16, mh = th * 16;
        SDL_Surface* m = SDL_CreateRGBSurfaceWithFormat(0, mw, mh, 32,
                                                        SDL_PIXELFORMAT_RGBA32);
        uint32_t* px = (uint32_t*)m->pixels;
        for (int j = 0; j < mh; j++)
            for (int i = 0; i < mw; i++) {
                // The middle of the art pixel, in world pixels — a tile is
                // sixteen of the one and thirty-two of the other.
                int tx = want_x + i / 16, ty = want_y + j / 16;
                float wx = ((float)(want_x * 16 + i) + 0.5f) * (TILE_SIZE / 16.0f);
                float wy = ((float)(want_y * 16 + j) + 0.5f) * (TILE_SIZE / 16.0f);
                int ov = g_map.overlay[ty][tx];
                bool other = ov == TILE_TREE || ov == TILE_DEAD_TREE
                          || ov == TILE_ROCK || ov == TILE_GOLD_ORE;
                uint32_t c = 0xFFFFFFFFu;
                if (tilemap_pixel_solid(&g_map, wx, wy)) c = other ? 0xFF808080u
                                                                   : 0xFF000000u;
                px[j * (m->pitch / 4) + i] = c;
            }
        IMG_SavePNG(m, out);
        printf("wrote %s (%dx%d, one pixel to the art pixel, black is solid,"
               " grey is solid for something other than the cliff) seed %u at %d,%d\n",
               out, mw, mh, seed, want_x, want_y);
        return 0;
    }

    Camera cam;
    cam.x = (float)(want_x * TILE_SIZE);
    cam.y = (float)(want_y * TILE_SIZE);
    cam.screen_w = W; cam.screen_h = H; cam.zoom = 1.0f;

    SDL_SetRenderDrawColor(ren, 255, 0, 255, 255);
    SDL_RenderClear(ren);
    tilemap_draw_base(&g_map, &cam, ren, 0);
    tilemap_draw_depth(&g_map, &cam, ren, 0);
    SDL_RenderPresent(ren);

    if (IMG_SavePNG(surf, out) != 0) { printf("save: %s\n", IMG_GetError()); return 1; }
    printf("wrote %s (%dx%d) seed %u at %d,%d\n", out, W, H, seed, want_x, want_y);
    return 0;
}
