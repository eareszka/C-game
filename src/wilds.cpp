#include "wilds.h"
#include "dungeon.h"   // pick_enemy_in_region
#include "towns.h"     // TOWN_W, TOWN_H
#include <math.h>

static uint32_t wild_hash(uint32_t h) {
    h ^= h >> 16; h *= 0x7FEB352Du;
    h ^= h >> 15; h *= 0x846CA68Bu;
    h ^= h >> 16;
    return h;
}

int wild_road_distance(const Tilemap* map, int tx, int ty, int cap) {
    for (int r = 0; r < cap; r++)
        for (int dy = -r; dy <= r; dy++) {
            // The ring only: its top and bottom rows whole, its sides' two ends.
            int step = (dy == -r || dy == r) ? 1 : 2 * r;
            for (int dx = -r; dx <= r; dx += step ? step : 1) {
                int x = tx + dx, y = ty + dy;
                if (in_world(&x, &y) && map->route[y][x] == ROUTE_ROAD) return r;   // a trail does not keep them off
            }
        }
    return cap;
}

// Ground a pack may stand on: open, dry, off every track (a road or a trail:
// beside a trail is fine, wild_road_distance; on it is not), out of the towns
// and villages, and not on top of anything the player comes to the place for.
static bool wild_ground(const Tilemap* map, int tx, int ty) {
    if (!in_world(&tx, &ty) || !tilemap_is_walkable(map, tx, ty)) return false;
    if (map->overlay[ty][tx] != 0 || map->route[ty][tx] != ROUTE_NONE) return false;
    int t = map->tiles[ty][tx];
    if (t == TILE_HUB || t >= TILE_TOWN0_BASE) return false;
    if (village_at(map, tx, ty) >= 0) return false;
    auto near = [&](int x, int y, int r) {
        return abs(wrap_dx(tx - x)) <= r && abs(wrap_dy(ty - y)) <= r;
    };
    // The towns, and round the start the whole island and its ring of water.
    for (int i = 0; i < 3; i++)
        if (near(map->towns[i].x + TOWN_W / 2, map->towns[i].y + TOWN_H / 2, TOWN_W / 2 + WILD_CHUNK))
            return false;
    for (int i = 0; i < map->num_dungeon_entrances; i++)
        if (near(map->dungeon_entrances[i].x, map->dungeon_entrances[i].y, 6)) return false;
    for (int i = 0; i < map->num_landmarks; i++)
        if (near(map->landmarks[i].x, map->landmarks[i].y, 8)) return false;
    for (int i = 0; i < BOSS_SITE_COUNT; i++)
        if (map->boss_sites[i].x >= 0 && near(map->boss_sites[i].x, map->boss_sites[i].y, 12)) return false;
    return true;
}

// enemy_region's numbering: 0 grassland, 1 forest, 2 snow, 3 desert,
// 4 wasteland, 5 mountains. The hills' own enemies on any green height.
static int wild_region(const Tilemap* map, int tx, int ty) {
    switch (tilemap_biome_at(map, tx, ty)) {
        case TILE_SNOW:      return 2;
        case TILE_SAND:      return 3;
        case TILE_WASTELAND: return 4;
        case TILE_TREE:      return tilemap_cliff_elev_at(tx, ty) > 0 ? 5 : 1;
        default:             return tilemap_cliff_elev_at(tx, ty) > 0 ? 5 : 0;
    }
}

void wild_pack(const Tilemap* map, unsigned seed, int cx, int cy, WildPack* out) {
    out->n = 0;
    out->road = 0;
    out->difficulty = 0.0f;
    if (cx < 0 || cy < 0 || cx >= WILD_CHUNKS_X || cy >= WILD_CHUNKS_Y) return;
    uint32_t rng = wild_hash(seed ^ wild_hash(0x57A1D000u + (uint32_t)(cy * WILD_CHUNKS_X + cx)));
    auto roll = [&](uint32_t n) { rng = wild_hash(rng + 0x9E3779B9u); return rng % n; };

    // Where in the square: a few tries at open ground, else nothing.
    int tx = -1, ty = -1;
    for (int tries = 0; tries < 8 && tx < 0; tries++) {
        int x = cx * WILD_CHUNK + (int)roll(WILD_CHUNK), y = cy * WILD_CHUNK + (int)roll(WILD_CHUNK);
        if (x < MAP_WIDTH && y < MAP_HEIGHT && wild_ground(map, x, y)) { tx = x; ty = y; }
    }
    if (tx < 0) return;

    int road = wild_road_distance(map, tx, ty, WILD_ROAD_DEEP + 1);
    if (road < WILD_ROAD_CLEAR) return;
    float deep = fminf(1.0f, (float)(road - WILD_ROAD_CLEAR) / (float)(WILD_ROAD_DEEP - WILD_ROAD_CLEAR));
    if ((float)roll(1000) >= 1000.0f * (0.1f + 0.35f * deep)) return;   // a tenth at the edge, near half deep in

    // How hard: a dungeon's formula (distance out and height), and a little
    // more the deeper in.
    float fdx = (float)(tx - MAP_WIDTH / 2), fdy = (float)(ty - MAP_HEIGHT / 2);
    float max_dist = sqrtf((float)(MAP_WIDTH / 2) * (MAP_WIDTH / 2) + (float)(MAP_HEIGHT / 2) * (MAP_HEIGHT / 2));
    float difficulty = (sqrtf(fdx * fdx + fdy * fdy) / max_dist + tilemap_cliff_elev_at(tx, ty) / 5.0f) * 0.5f
                     + 0.04f * deep;
    int region = wild_region(map, tx, ty);

    int n = 1 + (deep >= 0.4f) + (deep >= 0.8f && roll(2));
    out->road = road;
    out->difficulty = difficulty;
    for (int i = 0; i < n; i++) {
        // Close round the spot, on open ground; the spot itself if none is.
        int mx = tx, my = ty;
        for (int tries = 0; i > 0 && tries < 6; tries++) {
            int x = tx + (int)roll(5) - 2, y = ty + (int)roll(5) - 2;
            if (wild_ground(map, x, y)) { mx = x; my = y; break; }
        }
        in_world(&mx, &my);
        out->x[i] = (mx + 0.5f) * TILE_SIZE + (float)roll(9) - 4.0f;
        out->y[i] = (my + 0.5f) * TILE_SIZE + (float)roll(9) - 4.0f;
        out->enemy[i] = pick_enemy_in_region(region, false, difficulty, &rng);
    }
    out->n = n;
}
