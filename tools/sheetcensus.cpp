// Which cells of assets/tileset.png does the game draw? Run from the repo root:
//
//     make sheetcensus && ./sheetcensus.exe [out.png] [seed ...]
//
// Draws everything the game can put on screen from the sheet -- whole worlds
// for each seed, every dungeon type in every material, every interior -- with
// the game's own drawing code, compiled so each SDL_RenderCopy reports its
// source rect (include/sheet_trace.h). Nothing is guessed from the sources: a
// cell counts as used only if a real draw read it.
//
// out.png holds one pixel per 16px cell of the sheet: white where some draw
// read that cell, black where none did. Default art/_work/sheet_usage.png.
//
// What a census cannot see is art the code does not reach yet (drawn but not
// wired in). That is a question for whoever drew it, so the pruning script
// takes a list of protected cells rather than trusting this map alone.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "tilemap.h"
#include "camera.h"
#include "dungeon.h"
#include "interior.h"

static const int COLS = 256, ROWS = 256;
static bool s_used[ROWS][COLS];
static long s_draws = 0;

void sheet_trace(SDL_Texture* tex, const SDL_Rect* src) {
    if (!tex || tex != tilemap_get_town_tex()) return;
    s_draws++;
    int w, h;
    SDL_QueryTexture(tex, nullptr, nullptr, &w, &h);
    SDL_Rect r = src ? *src : SDL_Rect{ 0, 0, w, h };
    for (int y = r.y / 16; y <= (r.y + r.h - 1) / 16 && y < ROWS; y++)
        for (int x = r.x / 16; x <= (r.x + r.w - 1) / 16 && x < COLS; x++)
            if (x >= 0 && y >= 0) s_used[y][x] = true;
}

static int count_used() {
    int n = 0;
    for (int y = 0; y < ROWS; y++) for (int x = 0; x < COLS; x++) n += s_used[y][x];
    return n;
}

static Tilemap    g_map;
static DungeonMap g_dmap;

int main(int argc, char** argv) {
    const char* out = argc > 1 ? argv[1] : "art/_work/sheet_usage.png";
    std::vector<unsigned> seeds;
    for (int i = 2; i < argc; i++) seeds.push_back((unsigned)strtoul(argv[i], nullptr, 10));
    if (seeds.empty()) seeds = { 387u, 630u, 678u, 700u };

    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 1; }
    IMG_Init(IMG_INIT_PNG);
    // A small target: draws landing outside it are clipped, which is all a
    // census needs -- the copy call, and so the trace, still happens.
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);
    if (!tilemap_get_town_tex()) { printf("assets/tileset.png did not load\n"); return 1; }

    // The overworld, whole, in windows the size of a large screen.
    const int WT = 160;
    for (unsigned seed : seeds) {
        tilemap_build_overworld_phase1(&g_map, seed);
        tilemap_build_overworld_phase2(&g_map, seed);
        for (int ty = 0; ty < MAP_HEIGHT; ty += WT)
            for (int tx = 0; tx < MAP_WIDTH; tx += WT) {
                Camera cam;
                cam.x = (float)(tx * TILE_SIZE); cam.y = (float)(ty * TILE_SIZE);
                cam.screen_w = WT * TILE_SIZE; cam.screen_h = WT * TILE_SIZE; cam.zoom = 1.0f;
                tilemap_draw_base(&g_map, &cam, ren, 0);
                tilemap_draw_depth(&g_map, &cam, ren, 0);
            }
        printf("world %u: %d cells used so far\n", seed, count_used());
    }

    // Every dungeon type in every material, a few layouts of each, drawn whole.
    for (int t = 0; t < DUNGEON_ENT_COUNT; t++)
        for (int m = 0; m < MAT_COUNT; m++)
            for (unsigned s = 1; s <= 3; s++) {
                g_dmap.want_portals = 2;
                dungeon_generate(&g_dmap, (DungeonEntranceType)t, 0.5f, s * 7919u + t * 31u);
                g_dmap.ore = (Material)m;
                DungeonPlayer dp{};
                Camera cam;
                cam.x = 0; cam.y = 0; cam.zoom = 1.0f;
                cam.screen_w = DMAP_W * DMAP_TILE; cam.screen_h = DMAP_H * DMAP_TILE;
                dungeon_draw(&g_dmap, &dp, &cam, ren, true);
            }
    printf("dungeons: %d cells used so far\n", count_used());

    static InteriorMap im;
    for (int i = 0; i < 8; i++) {           // interior_load clamps unknown ids to 0
        interior_load(&im, i);
        interior_draw(&im, ren, tilemap_get_town_tex());
    }
    printf("interiors: %d cells used, %ld draws traced\n", count_used(), s_draws);

    SDL_Surface* map = SDL_CreateRGBSurfaceWithFormat(0, COLS, ROWS, 32, SDL_PIXELFORMAT_RGBA32);
    uint32_t* px = (uint32_t*)map->pixels;
    for (int y = 0; y < ROWS; y++)
        for (int x = 0; x < COLS; x++)
            px[y * (map->pitch / 4) + x] = s_used[y][x] ? 0xFFFFFFFFu : 0xFF000000u;
    if (IMG_SavePNG(map, out) != 0) { printf("save: %s\n", IMG_GetError()); return 1; }
    printf("wrote %s\n", out);
    return 0;
}
