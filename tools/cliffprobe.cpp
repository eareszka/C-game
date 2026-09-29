// Which cliff pass gave a window of the world its shape?
//
//     make cliffprobe && ./cliffprobe.exe <seed> <x> <y> <w> <h>
//
// Prints the height grid of the window after every stage of place_cliffs(),
// one digit per tile, so that a shape nobody asked for -- a slot cut into a
// terrace, a limb that should have gone -- can be traced to the pass that
// made it. Built with GEN_TRACE like coastprobe, which is what turns the
// GEN_STAGE hook into a call.
#include <SDL2/SDL.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "tilemap.h"

static int g_x, g_y, g_w, g_h;

void gen_trace_stage(const Tilemap* map, const char* stage) {
    (void)map;
    if (strncmp(stage, "cliff:", 6) != 0) return;
    printf("== %s\n", stage);
    for (int ty = g_y; ty < g_y + g_h; ty++) {
        for (int tx = g_x; tx < g_x + g_w; tx++)
            putchar((char)('0' + tilemap_cliff_elev_at(tx, ty)));
        putchar('\n');
    }
}
void gen_trace_shore(const ShoreTally*) {}

static Tilemap g_map;

int main(int argc, char** argv) {
    if (argc < 6) { printf("usage: cliffprobe <seed> <x> <y> <w> <h>\n"); return 1; }
    unsigned seed = (unsigned)strtoul(argv[1], nullptr, 10);
    g_x = atoi(argv[2]); g_y = atoi(argv[3]); g_w = atoi(argv[4]); g_h = atoi(argv[5]);
    SDL_SetMainReady();
    tilemap_build_overworld_phase1(&g_map, seed);
    tilemap_build_overworld_phase2(&g_map, seed);
    return 0;
}
