// tools/dngshot.cpp — Offscreen cave-dungeon screenshot: generates a
// DungeonMap and saves a PNG of a window onto it, without opening a window.
// Used to iterate on cave wall/floor art.
//
//   dngshot.exe <seed> <out.png> [tile_x tile_y] [tiles_w tiles_h]
//
// Env: DNGSHOT_TYPE=<0..8> archetype (default cave), DNGSHOT_ORE=<0..6> cave
//      material, DNGSHOT_MAYA a pyramid's step-pyramid interior, DNGSHOT_DIM simulate FOV memory-dimming, DNGSHOT_DUMP ASCII
//      floor/wall grid to stdout, DNGSHOT_GRID debug source-cell overlay.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "dungeon.h"
#include "tilemap.h"
#include "camera.h"
#include "fc_palette.h"
#include "collision.h"
#include "entity.h"
#include "input.h"

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
    g_dmap.step_pyramid = getenv("DNGSHOT_MAYA") != nullptr;   // the step pyramid's Mayan interior
    dungeon_generate(&g_dmap, dng_type, 0.5f, seed);
    dungeon_seat_portals(&g_dmap);   // as the game's binds do: each way out on the outer wall
    // DNGSHOT_WAYS=ab: the entrance type each way out returns to (digits, a
    // DungeonEntranceType each) -- a graveyard's are a ladder or a door by it
    if (const char* wv = getenv("DNGSHOT_WAYS"))
        for (int p = 0; p < g_dmap.num_portals && wv[p]; p++)
            g_dmap.portals[p].ow_type = (DungeonEntranceType)(wv[p] - '0');

    DungeonPlayer dp{};
    Camera cam;
    cam.screen_w = W; cam.screen_h = H; cam.zoom = 1.0f;
    camera_place(&cam, (float)(want_x * DMAP_TILE), (float)(want_y * DMAP_TILE));

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
    // DNGSHOT_WALK: walk the player about at random from the way in for a
    // while, by the game's own movement, and say where it got and whether it
    // ever stood where it may not (inside a wall, off a walkway's edge), and
    // how often a straight push slid along a slanted edge.
    if (getenv("DNGSHOT_WALK")) {
        static Input in;
        Player pl{};
        DungeonPlayer dp{};
        input_init(&in);
        dungeon_player_init(&dp, &pl, &g_dmap, 0);
        static bool been[DMAP_H][DMAP_W];
        int tiles = 0, bad = 0, slid = 0, frames = 40000;
        float fastest = 0, win = 0;
        int breaths = 0;                                 // the oasis: frames at a surface, breathing                      // the fastest half second's average step
        std::vector<float> steps;
        const SDL_Scancode K[4] = { SDL_SCANCODE_UP, SDL_SCANCODE_DOWN, SDL_SCANCODE_LEFT, SDL_SCANCODE_RIGHT };
        unsigned r = seed;
        int keys = 0;
        for (int f = 0; f < frames; f++) {
            if (f % 40 == 0) {
                r = r * 1664525u + 1013904223u;
                keys = (int)((r >> 16) % 8);                 // one key or two
            }
            static const int SETS[8][2] = {{0,-1},{1,-1},{2,-1},{3,-1},{0,2},{0,3},{1,2},{1,3}};
            for (int k = 0; k < 4; k++) in.keys[K[k]] = KEY_UP;
            for (int j = 0; j < 2; j++)
                if (SETS[keys][j] >= 0) in.keys[K[SETS[keys][j]]] = f % 40 == 0 ? KEY_PRESSED : KEY_HELD;
            float x0 = dp.x, y0 = dp.y;
            dungeon_player_update(&dp, &pl, &in, 1.0f / 60.0f, &g_dmap, &cam);
            if (SETS[keys][1] < 0 && dp.x != x0 && dp.y != y0) slid++;
            float moved = sqrtf((dp.x - x0) * (dp.x - x0) + (dp.y - y0) * (dp.y - y0));
            steps.push_back(moved); win += moved;
            if (steps.size() > 30) win -= steps[steps.size() - 31];
            if (steps.size() >= 30 && win / 30 > fastest) fastest = win / 30;
            if (!dungeon_player_fits(&g_dmap, &dp)) bad++;
            if (g_dmap.type == DUNGEON_ENT_OASIS && dungeon_breathing(&g_dmap, &dp)) breaths++;
            int tx = (int)((dp.x + (HB_X1 + HB_X2) * 0.5f) / DMAP_TILE), ty = (int)((dp.y + HB_Y2) / DMAP_TILE);
            if (tx >= 0 && ty >= 0 && tx < DMAP_W && ty < DMAP_H && !been[ty][tx]) { been[ty][tx] = true; tiles++; }
        }
        printf("walk: %d frames, %d tiles stood on, %d frames where it may not stand, %d straight pushes slid\n",
               frames, tiles, bad, slid);
        if (g_dmap.type == DUNGEON_ENT_OASIS) printf("walk: %d frames breathing at a surface\n", breaths);
        printf("walk: fastest half second %.2f px a frame (walking: %.2f)\n", fastest, PLAYER_WALK_SPEED / 60.0f);
    }

    // DNGSHOT_COLCHECK (stonehenge): the feet's collision against the drawn
    // base of every block -- its ground footprint, the side's foot column
    // included -- pixel for pixel over the whole maze.
    if (getenv("DNGSHOT_COLCHECK")) {
        int W = g_dmap.barrow_w + 16, H = g_dmap.barrow_h + 16, X0 = g_dmap.barrow_x0, Y0 = g_dmap.barrow_y0;
        std::vector<uint8_t> base(W * H, 0);
        for (int i = 0; i < g_dmap.num_barrow_blocks; i++) {
            int x0 = g_dmap.barrow_blocks[i].x, bd = g_dmap.barrow_blocks[i].d;
            for (int dd = bd; dd < bd + 16; dd++)
                for (int X = x0; X <= x0 + 32; X++) {      // the top's row, and the side's foot past it
                    int x = g_dmap.barrow_ox + X + dd - X0, y = g_dmap.barrow_oy - 1 - dd - Y0;
                    if (x >= 0 && y >= 0 && x < W && y < H) base[y * W + x] = 1;
                }
        }
        int solid_off = 0, open_on = 0, n = 0;
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++) {
                int d = g_dmap.barrow_oy - 1 - (Y0 + y), gx = X0 + x - g_dmap.barrow_ox - d;
                if (d < 0 || gx < 0 || gx > g_dmap.barrow_w) continue;   // the maze's ground only
                bool s = dungeon_solid_at(&g_dmap, (X0 + x) * 2.0f + 1, (Y0 + y) * 2.0f + 1);
                n++;
                if (s && !base[y * W + x]) solid_off++;
                if (!s && base[y * W + x]) open_on++;
            }
        printf("colcheck: %d ground pixels, %d solid off a base, %d open on a base\n", n, solid_off, open_on);
    }

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
        printf("entry %d,%d  exit %d,%d\n", g_dmap.entry_x, g_dmap.entry_y, g_dmap.exit_x, g_dmap.exit_y);
        printf("bbox %d %d %d %d\n", lox, loy, hix, hiy);   // for framing a whole layout
    }

    fc_draw_color(ren, 5, 5, 8, 255);   // matches STATE_DUNGEON's own clear in main.cpp
    SDL_RenderClear(ren);
    dungeon_draw(&g_dmap, &dp, &cam, ren, show_all);
    // DNGSHOT_PLAYER=x,y (dungeon pixels): a stand-in for the player's sprite,
    // then what the game draws over it (dungeon_draw_front)
    if (const char* pp = getenv("DNGSHOT_PLAYER")) {
        DungeonPlayer stand{};
        sscanf(pp, "%f,%f", &stand.x, &stand.y);
        SDL_Rect r = { cam_px(&cam, stand.x), cam_py(&cam, stand.y), 28, 40 };
        fc_draw_color(ren, 252, 116, 180, 255);
        SDL_RenderFillRect(ren, &r);
        dungeon_draw_front(&g_dmap, &stand, &cam, ren);
    }
    if (getenv("DNGSHOT_GRID")) dungeon_draw_debug_grid(&g_dmap, &cam, ren);
    SDL_RenderPresent(ren);

    if (IMG_SavePNG(surf, out) != 0) { printf("save: %s\n", IMG_GetError()); return 1; }
    printf("wrote %s (%dx%d) seed %u at %d,%d\n", out, W, H, seed, want_x, want_y);
    return 0;
}
