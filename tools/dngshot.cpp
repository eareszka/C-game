// tools/dngshot.cpp — Offscreen cave-dungeon screenshot: generates a
// DungeonMap and saves a PNG of a window onto it, without opening a window.
// Used to iterate on cave wall/floor art.
//
//   dngshot.exe <seed> <out.png> [tile_x tile_y] [tiles_w tiles_h]
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include "dungeon.h"
#include "tilemap.h"
#include "camera.h"

static DungeonMap g_dmap;

int main(int argc, char** argv) {
    unsigned seed = (argc > 1) ? (unsigned)strtoul(argv[1], nullptr, 10) : 387u;
    const char* out = (argc > 2) ? argv[2] : "dngshot.png";
    int tw = (argc > 6) ? atoi(argv[5]) : 44;
    int th = (argc > 6) ? atoi(argv[6]) : 30;
    int want_x = (argc > 4) ? atoi(argv[3]) : DMAP_W/2 - tw/2;
    int want_y = (argc > 4) ? atoi(argv[4]) : DMAP_H/2 - th/2;

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "0");   // matches main.cpp's own hint

    int W = tw * DMAP_TILE, H = th * DMAP_TILE;
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    if (!ren) { printf("renderer: %s\n", SDL_GetError()); return 1; }

    tilemap_init_tile_cache(ren);   // loads assets/tileset.png — same atlas dungeon_draw() reads

    g_dmap.want_portals = 2;        // spine fallback (want_ox/oy left zero) — fine for a preview
    dungeon_generate(&g_dmap, DUNGEON_ENT_CAVE, 0.5f, seed);

    DungeonPlayer dp{};
    Camera cam;
    cam.x = (float)(want_x * DMAP_TILE);
    cam.y = (float)(want_y * DMAP_TILE);
    cam.screen_w = W; cam.screen_h = H; cam.zoom = 1.0f;

    bool force_dim = getenv("DNGSHOT_DIM") != nullptr;
    bool show_all = true;
    if (force_dim) {
        show_all = false;
        int radius = 6;
        int cx = want_x + tw/2, cy = want_y + th/2;
        for (int y = 0; y < DMAP_H; y++) for (int x = 0; x < DMAP_W; x++) {
            if (x < want_x-2 || x > want_x+tw+2 || y < want_y-2 || y > want_y+th+2) continue;
            g_dmap.explored[y][x] = true;
            int dx = x-cx, dy = y-cy;
            g_dmap.visible[y][x] = (dx*dx+dy*dy) <= radius*radius;
        }
    }

    if (getenv("DNGSHOT_DUMP")) {
        for (int y = want_y; y < want_y + th; y++) {
            for (int x = want_x; x < want_x + tw; x++) {
                uint8_t t = g_dmap.tiles[y][x];
                bool floor = (t == DNG_FLOOR || t == DNG_ENTRY || t == DNG_EXIT);
                putchar(floor ? '.' : '#');
            }
            putchar('\n');
        }
    }

    SDL_SetRenderDrawColor(ren, 5, 5, 8, 255);   // matches STATE_DUNGEON's own clear, main.cpp:955
    SDL_RenderClear(ren);
    dungeon_draw(&g_dmap, &dp, &cam, ren, show_all);
    if (getenv("DNGSHOT_GRID")) dungeon_draw_debug_grid(&g_dmap, &cam, ren);
    SDL_RenderPresent(ren);

    if (IMG_SavePNG(surf, out) != 0) { printf("save: %s\n", IMG_GetError()); return 1; }
    printf("wrote %s (%dx%d) seed %u at %d,%d\n", out, W, H, seed, want_x, want_y);
    return 0;
}
