// Nothing comes back: the dungeon half of persist.h, through the shipped
// dungeon_generate.
//
//   killcheck.exe   (from the repo root: the tile cache reads assets/)
//
//   1. every starter dungeon (cave and small graveyard, many seeds) holds at
//      least two Treesqueaks -- with no respawns, the raft's 3 Vine must be
//      there to be had
//   2. spawners marked beaten come back dead on the next generation, and only
//      they; a dungeon with no record comes back whole
//   3. a broken cave vein comes back broken, its wall tile floor
//   4. the overworld grown again from its seed: felled trees stay felled, and
//      the island graveyard whose hiding stone was broken stands open, its
//      stone not spawned again
//
// Exits non-zero if any check fails.
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#include <cstdio>
#include "tilemap.h"
#include "dungeon.h"
#include "persist.h"
#include "resource_node.h"

static DungeonMap g_dmap;
static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: " __VA_ARGS__); printf("\n"); fails++; } } while (0)

static void make(DungeonEntranceType type, unsigned seed, bool starter) {
    DungeonWiring w = {};
    w.seed = seed; w.type = type; w.difficulty = 0.2f; w.starter = starter;
    dungeon_want(&g_dmap, &w);
    dungeon_generate(&g_dmap, type, w.difficulty, seed);
}

int main(int, char**) {
    SDL_SetMainReady();
    if (SDL_Init(SDL_INIT_VIDEO) != 0) { printf("SDL_Init: %s\n", SDL_GetError()); return 2; }
    IMG_Init(IMG_INIT_PNG);
    SDL_Surface* surf = SDL_CreateRGBSurfaceWithFormat(0, 64, 64, 32, SDL_PIXELFORMAT_RGBA32);
    SDL_Renderer* ren = SDL_CreateSoftwareRenderer(surf);
    tilemap_init_tile_cache(ren);
    persist_clear();

    // 1. Two Treesqueaks in every starter dungeon.
    const DungeonEntranceType STARTERS[] = { DUNGEON_ENT_CAVE, DUNGEON_ENT_GRAVEYARD_SM };
    int fewest = 99;
    for (DungeonEntranceType t : STARTERS)
        for (unsigned s = 0; s < 40; s++) {
            unsigned seed = s == 0 && t == DUNGEON_ENT_CAVE ? DNG_FIXED_CAVE_SEED : 0x51A7u + s * 7919u;
            make(t, seed, true);
            int squeaks = 0;
            for (int i = 0; i < g_dmap.num_spawners; i++) squeaks += g_dmap.spawners[i].enemy_id == 2;
            if (squeaks < fewest) fewest = squeaks;
            CHECK(squeaks >= 2, "starter type %d seed %u: %d Treesqueaks of %d spawners", (int)t, seed, squeaks, g_dmap.num_spawners);
        }
    printf("starters: fewest Treesqueaks in one dungeon %d\n", fewest);

    // 2. Beaten spawners stay beaten, and only those.
    const unsigned SEED = 0xBEA7u;
    make(DUNGEON_ENT_RUINS, SEED, false);
    int n = g_dmap.num_spawners;
    CHECK(n >= 4, "ruins has %d spawners", n);
    for (int i = 0; i < n; i++) CHECK(!g_dmap.spawners[i].dead, "fresh spawner %d dead", i);
    persist_spawner_beaten(SEED, 1);
    persist_spawner_beaten(SEED, 3);
    make(DUNGEON_ENT_RUINS, SEED, false);
    CHECK(g_dmap.num_spawners == n, "spawner count changed %d -> %d", n, g_dmap.num_spawners);
    for (int i = 0; i < g_dmap.num_spawners; i++)
        CHECK(g_dmap.spawners[i].dead == (i == 1 || i == 3), "spawner %d dead=%d", i, (int)g_dmap.spawners[i].dead);
    make(DUNGEON_ENT_RUINS, SEED + 1, false);
    for (int i = 0; i < g_dmap.num_spawners; i++) CHECK(!g_dmap.spawners[i].dead, "other dungeon's spawner %d dead", i);
    printf("kills: spawners 1 and 3 of %d stay beaten, a different dungeon untouched\n", n);

    // 3. A broken vein stays broken.
    const unsigned CAVE = 0xCA7Eu;
    make(DUNGEON_ENT_CAVE, CAVE, false);
    int vein = -1;
    for (int i = 0; i < g_dmap.dungeon_rocks.count && vein < 0; i++)
        if (g_dmap.dungeon_rocks.nodes[i].type == RESOURCE_ROCK && g_dmap.dungeon_rocks.nodes[i].chest == 0) vein = i;
    CHECK(vein >= 0, "cave has no ore vein");
    if (vein >= 0) {
        const ResourceNode v = g_dmap.dungeon_rocks.nodes[vein];
        int tx = (int)(v.x / DMAP_TILE), ty = (int)(v.y / DMAP_TILE);
        CHECK(g_dmap.tiles[ty][tx] == DNG_WALL, "vein tile not wall before");
        persist_node_broken(CAVE, vein);
        make(DUNGEON_ENT_CAVE, CAVE, false);
        CHECK(!g_dmap.dungeon_rocks.nodes[vein].alive, "broken vein alive again");
        CHECK(g_dmap.tiles[ty][tx] == DNG_FLOOR, "broken vein's tile not floor");
        int alive = 0;
        for (int i = 0; i < g_dmap.dungeon_rocks.count; i++) alive += g_dmap.dungeon_rocks.nodes[i].alive;
        printf("veins: node %d stays broken, %d other nodes standing\n", vein, alive);
    }

    // 4. The overworld, grown twice from one seed.
    persist_clear();
    const unsigned WORLD = 1114u;
    Tilemap* map = new Tilemap();
    tilemap_build_overworld_phase1(map, WORLD);
    tilemap_build_overworld_phase2(map, WORLD);
    int felled[8][2], nf = 0;
    for (int y = MAP_HEIGHT / 2 - 80; y < MAP_HEIGHT / 2 + 80 && nf < 8; y += 3)
        for (int x = MAP_WIDTH / 2 - 80; x < MAP_WIDTH / 2 + 80 && nf < 8; x += 7)
            if (map->overlay[y][x] == TILE_TREE) { felled[nf][0] = x; felled[nf][1] = y; nf++; }
    CHECK(nf == 8, "found only %d trees near the island's middle", nf);
    int grave = -1;
    for (int i = 0; i < map->num_dungeon_entrances; i++) {
        const DungeonEntrance& e = map->dungeon_entrances[i];
        if (e.x == DNG_FIXED_GRAVE_X && e.y == DNG_FIXED_GRAVE_Y) grave = i;
    }
    CHECK(grave >= 0 && map->dungeon_entrances[grave].partner_idx < 0, "no hidden island graveyard");
    int gx = DNG_FIXED_GRAVE_X, gy = DNG_FIXED_GRAVE_Y;
    CHECK(map->tiles[gy][gx] != TILE_DUNGEON_GRAVEYARD_SM, "island graveyard already open before its stone broke");
    for (int i = 0; i < nf; i++) persist_tile_add(tilemap_tile_key(felled[i][0], felled[i][1]));
    persist_tile_add(tilemap_tile_key(gx, gy));   // its hiding stone, broken
    delete map;
    map = new Tilemap();
    tilemap_build_overworld_phase1(map, WORLD);
    tilemap_build_overworld_phase2(map, WORLD);
    for (int i = 0; i < nf; i++)
        CHECK(map->overlay[felled[i][1]][felled[i][0]] == 0, "tree at %d,%d grew back", felled[i][0], felled[i][1]);
    CHECK(map->tiles[gy][gx] == TILE_DUNGEON_GRAVEYARD_SM, "island graveyard hidden again");
    static ResourceNodeList nodes;
    resource_nodes_init(&nodes);
    if (grave >= 0) tilemap_spawn_graveyard_nodes(map, &nodes, grave, WORLD);
    int hiding = -1, standing = 0;
    for (int i = 0; i < nodes.count; i++) {
        if (nodes.nodes[i].hides_entrance) hiding = i;
        standing += nodes.nodes[i].alive;
    }
    CHECK(hiding >= 0 && !nodes.nodes[hiding].alive, "the hiding stone stands again");
    printf("world: %d felled trees stay felled, island graveyard open, %d of its other stones standing\n", nf, standing);
    delete map;

    persist_clear();
    printf(fails ? "killcheck: %d FAILED\n" : "killcheck: ok\n", fails);
    return fails ? 1 : 0;
}
