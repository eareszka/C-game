#include <cstdio>
#include "dungeon.h"
#include "collision.h"
static DungeonMap g;
int main(int, char**) {
    g.want_portals = 2;
    dungeon_generate(&g, DUNGEON_ENT_CATACOMBS, 0.5f, 7);
    float x = 4664, y = 736;
    for (int dy = 0; dy <= 200; dy += 8) {
        printf("dy %3d: occupy %d  feet-centre solid %d\n", dy, can_occupy(&g, x, y + dy, dungeon_solid_at),
               dungeon_solid_at(&g, x + 14, y + 34 + dy));
    }
    for (int dx = 0; dx >= -60; dx -= 6) printf("dx %d occupy %d\n", dx, can_occupy(&g, x + dx, y + 4, dungeon_solid_at));
}
