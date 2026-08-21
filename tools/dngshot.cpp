// tools/dngshot.cpp — Offscreen cave-dungeon screenshot: generates a
// DungeonMap and saves a PNG of a window onto it, without opening a window.
// Used to iterate on cave wall/floor art.
//
//   dngshot.exe <seed> <out.png> [tile_x tile_y] [tiles_w tiles_h]
//
// Env: DNGSHOT_TYPE=<0..8> archetype (default cave), DNGSHOT_ORE=<0..6> cave
//      material, DNGSHOT_DIM simulate FOV memory-dimming, DNGSHOT_DUMP ASCII
//      floor/wall grid to stdout, DNGSHOT_GRID debug source-cell overlay.
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

    // Which archetype to generate. Caves are the default because this tool was
    // built to iterate on cave wall art, but every type generates through the
    // same entry point and a layout that only ever gets looked at in the running
    // game is a layout nobody checks -- DNGSHOT_DUMP on a non-cave type is the
    // cheapest way to see whether its rooms actually join up.
    DungeonEntranceType dng_type = DUNGEON_ENT_CAVE;
    if (const char* tp = getenv("DNGSHOT_TYPE")) {
        int ti = atoi(tp);
        if (ti >= 0 && ti < DUNGEON_ENT_COUNT) dng_type = (DungeonEntranceType)ti;
    }

    g_dmap.want_portals = 2;        // spine fallback (want_ox/oy left zero) — fine for a preview
    dungeon_generate(&g_dmap, dng_type, 0.5f, seed);

    DungeonPlayer dp{};
    Camera cam;
    cam.x = (float)(want_x * DMAP_TILE);
    cam.y = (float)(want_y * DMAP_TILE);
    cam.screen_w = W; cam.screen_h = H; cam.zoom = 1.0f;

    // Force the cave's material, so the regression check can pin MAT_VEYRITE
    // (the identity row, which must render byte-identical to the pre-material
    // build) and so one cave can be rendered once per material for the
    // legibility comparison. Without this the material follows dngshot's
    // hardcoded 0.5 difficulty and only ever lands on one of them.
    if (const char* om = getenv("DNGSHOT_ORE")) {
        int mi = atoi(om);
        if (mi >= 0 && mi < MAT_COUNT) g_dmap.ore = (Material)mi;
    }

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

    // Whole-map summary. The ASCII dump above only covers the rendered window,
    // and the one question a window cannot answer about a layout is whether it
    // is one dungeon or several disconnected pieces -- a floor tile the player
    // can never stand on looks exactly like one they can. So flood the floor
    // from the entrance and report what the flood missed.
    if (getenv("DNGSHOT_STATS")) {
        static bool seen[DMAP_H][DMAP_W];
        static int qx[DMAP_H * DMAP_W], qy[DMAP_H * DMAP_W];
        int head = 0, tail = 0, floor_n = 0;
        int lox = DMAP_W, loy = DMAP_H, hix = -1, hiy = -1;
        for (int y = 0; y < DMAP_H; y++)
            for (int x = 0; x < DMAP_W; x++) {
                seen[y][x] = false;
                uint8_t t = g_dmap.tiles[y][x];
                if (t == DNG_FLOOR || t == DNG_ENTRY || t == DNG_EXIT) {
                    floor_n++;
                    if (x < lox) lox = x;  if (x > hix) hix = x;
                    if (y < loy) loy = y;  if (y > hiy) hiy = y;
                }
            }
        qx[tail] = g_dmap.entry_x; qy[tail] = g_dmap.entry_y; tail++;
        seen[g_dmap.entry_y][g_dmap.entry_x] = true;
        int reached = 0;
        while (head < tail) {
            int x = qx[head], y = qy[head]; head++; reached++;
            const int dx[4] = {1,-1,0,0}, dy[4] = {0,0,1,-1};
            for (int d = 0; d < 4; d++) {
                int nx = x + dx[d], ny = y + dy[d];
                if (nx < 0 || ny < 0 || nx >= DMAP_W || ny >= DMAP_H) continue;
                if (seen[ny][nx]) continue;
                uint8_t t = g_dmap.tiles[ny][nx];
                if (t != DNG_FLOOR && t != DNG_ENTRY && t != DNG_EXIT) continue;
                seen[ny][nx] = true;
                qx[tail] = nx; qy[tail] = ny; tail++;
            }
        }
        bool exit_ok = seen[g_dmap.exit_y][g_dmap.exit_x];
        printf("type %d  floor %d tiles  extent %dx%d  reachable %d (%.1f%%)  "
               "exit %s  spawners %d  loot %d%s\n",
               (int)dng_type, floor_n, hix - lox + 1, hiy - loy + 1,
               reached, floor_n ? 100.0 * reached / floor_n : 0.0,
               exit_ok ? "REACHED" : "UNREACHABLE",
               g_dmap.num_spawners, g_dmap.num_loot,
               (!exit_ok || reached != floor_n) ? "   <-- STRANDED FLOOR" : "");
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
