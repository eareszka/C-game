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

    // SHOT_TILES=1 writes the raw tile grid, four bytes to the tile, so two
    // builds can be compared exactly. Changing how a route is laid must not
    // change how the world it crosses was generated, and that is not something
    // a picture can be trusted to show: the routes are painted over terrain, so
    // a tile differing between builds is only meaningful once the tiles either
    // build painted a route on are set aside. tools/terrain_same.py does that.
    if (getenv("SHOT_TILES")) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        FILE* f = fopen(out, "wb");
        if (!f) { printf("cannot write %s\n", out); return 1; }
        for (int y = 0; y < MAP_HEIGHT; y++)
            fwrite(g_map.tiles[y], sizeof(int), MAP_WIDTH, f);
        fclose(f);
        printf("wrote %s (%dx%d tile ids, %d bytes each) seed %u\n",
               out, MAP_WIDTH, MAP_HEIGHT, (int)sizeof(int), seed);
        return 0;
    }

    // SHOT_TRAIL=1 draws the whole world one pixel to the tile, colour-coded by
    // which route network a tile belongs to. Width is the question here, and it
    // is the one thing the existing views throw away: SHOT_MASK gives trail and
    // road no colour of their own, and genprof's ROADMAP_DIR reduces four tiles
    // to a pixel, where its own comment admits "a 3-wide road survives as a
    // hairline". One pixel to the tile is exact, and tools/trail_width.py reads
    // this straight back.
    if (getenv("SHOT_TRAIL")) {
        SDL_Surface* m = SDL_CreateRGBSurfaceWithFormat(0, MAP_WIDTH, MAP_HEIGHT, 32,
                                                        SDL_PIXELFORMAT_RGBA32);
        SDL_Renderer* mr = SDL_CreateSoftwareRenderer(m);
        tilemap_init_tile_cache(mr);
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        uint32_t* px = (uint32_t*)m->pixels;
        // RGBA32 puts red in the LOW byte, so a literal written as 0xAARRGGBB
        // comes out with red and blue swapped -- which is why SHOT_MASK's
        // 0xFF4090F0 reads back as (240,144,64) in tools/outline_check.py.
        // Spell the channels out rather than leave the next reader to work it
        // out from a constant.
        auto rgba = [](int r, int g, int b) -> uint32_t {
            return 0xFF000000u | ((uint32_t)b << 16) | ((uint32_t)g << 8) | (uint32_t)r;
        };
        int n_trail = 0, n_road = 0, n_bridge = 0;
        for (int y = 0; y < MAP_HEIGHT; y++)
            for (int x = 0; x < MAP_WIDTH; x++) {
                int t = g_map.tiles[y][x];
                uint8_t rt = g_map.route[y][x];
                uint32_t c = rgba(0, 0, 0);
                // The track lives in its own layer; only the deck is a tile.
                if      (rt == ROUTE_TRAIL)      { c = rgba(0, 255, 0);   n_trail++; }
                else if (rt == ROUTE_ROAD)       { c = rgba(0, 128, 255); n_road++;  }
                else if (t == TILE_WASTE_BRIDGE ||
                         t == TILE_ROAD_BRIDGE)  { c = rgba(0, 255, 255); n_bridge++; }
                // Context, so a narrow stretch can be told apart from a
                // clipped one. The stroke is refused wherever it would leave
                // its own region, and these are the grounds it is usually
                // refused against; without them on the map a track thinned by
                // its surroundings and one thinned by the brush look identical.
                else if (t >= TILE_TOWN0_BASE || t == TILE_BLUEPRINT ||
                         t == TILE_VILLAGE_PLACEHOLDER ||
                         t == TILE_CASTLE_PLACEHOLDER) c = rgba(255, 255, 0);
                else if (t == TILE_PATH)          c = rgba(255, 0, 255);
                // The trail's region is wasteland and nothing else, so the edge
                // of the wasteland is an edge the stroke gets refused at just
                // like a shoreline is.
                else if (t == TILE_WASTELAND)     c = rgba(120, 60, 30);
                else if (t == TILE_LAVA)          c = rgba(80, 0, 0);
                else if (t == TILE_WATER || t == TILE_RIVER ||
                         t == TILE_POND  || t == TILE_HUB)  c = rgba(0, 0, 80);
                px[y * (m->pitch / 4) + x] = c;
            }
        IMG_SavePNG(m, out);
        printf("wrote %s (%dx%d, one pixel to the tile) seed %u  "
               "trail %d, road %d, bridge %d\n",
               out, MAP_WIDTH, MAP_HEIGHT, seed, n_trail, n_road, n_bridge);

        // With a window given, also print what the ground is made of there. The
        // picture says how wide a stretch came out; only this says what it was
        // refused against, and the two questions kept getting confused for each
        // other -- a track thinned by the brush and one thinned by whatever it
        // was running alongside look exactly alike from above.
        if (want_x >= 0) {
            printf("tiles %d,%d %dx%d  R road T trail B bridge ~ water L lava "
                   "# cliff O structure p path . plain ? other\n",
                   want_x, want_y, tw, th);
            for (int y = want_y; y < want_y + th; y++) {
                printf("  %5d ", y);
                for (int x = want_x; x < want_x + tw; x++) {
                    char ch = '?';
                    if (x < 0 || y < 0 || x >= MAP_WIDTH || y >= MAP_HEIGHT) {
                        putchar(' '); continue;
                    }
                    int t = g_map.tiles[y][x];
                    uint8_t rt = g_map.route[y][x];
                    if      (rt == ROUTE_ROAD)          ch = 'R';
                    else if (rt == ROUTE_TRAIL)         ch = 'T';
                    else if (t == TILE_ROAD_BRIDGE ||
                             t == TILE_WASTE_BRIDGE)    ch = 'B';
                    else if (t == TILE_WATER || t == TILE_RIVER ||
                             t == TILE_POND  || t == TILE_HUB) ch = '~';
                    else if (t == TILE_LAVA)            ch = 'L';
                    else if (t == TILE_PATH)            ch = 'p';
                    else if (t >= TILE_TOWN0_BASE || t == TILE_BLUEPRINT ||
                             t == TILE_VILLAGE_PLACEHOLDER ||
                             t == TILE_CASTLE_PLACEHOLDER) ch = 'O';
                    else if (tilemap_face_at(x, y)) ch = '#';
                    else if (t == TILE_GRASS || t == TILE_MEADOW || t == TILE_SAND ||
                             t == TILE_SNOW  || t == TILE_WASTELAND) ch = '.';
                    putchar(ch);
                }
                putchar('\n');
            }
        }
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
