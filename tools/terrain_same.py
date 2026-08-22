"""Prove a change to the route layer left terrain and biome generation alone.

Routes are painted over the ground, last of all the worldgen passes, so two
builds cannot simply be compared tile for tile: move a road by one tile and the
ground it used to cover reappears, which is a difference in the routes and not
in the terrain. Set aside every tile that EITHER build painted a route on, and
what is left must match exactly. Anything that does not is the route change
having reached back into the world it was only supposed to cross.

    SHOT_TILES=1 ./shot.exe 387 before.bin      # on the old build
    SHOT_TILES=1 ./shot.exe 387 after.bin       # on the new one
    python tools/terrain_same.py before.bin after.bin
"""
import sys

import numpy as np

MAP = 3000
# Must match include/tilemap.h.
ROUTE = (72, 73, 82, 83)   # WASTE_TRAIL, WASTE_BRIDGE, ROAD, ROAD_BRIDGE


def load(p):
    a = np.fromfile(p, dtype=np.int32)
    if a.size != MAP * MAP:
        raise SystemExit('%s holds %d tiles, expected %d' % (p, a.size, MAP * MAP))
    return a.reshape(MAP, MAP)


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    route = np.zeros_like(a, dtype=bool)
    for t in ROUTE:
        route |= (a == t) | (b == t)

    diff = (a != b)
    stray = diff & ~route
    n_stray = int(stray.sum())

    print('tiles differing anywhere:            %d' % int(diff.sum()))
    print('tiles either build routed over:      %d' % int(route.sum()))
    print('differing OUTSIDE any route:         %d' % n_stray)
    if n_stray:
        ys, xs = np.nonzero(stray)
        print('  first few: ' + ', '.join(
            '(%d,%d) %d->%d' % (x, y, a[y, x], b[y, x])
            for y, x in list(zip(ys.tolist(), xs.tolist()))[:8]))
        print('TERRAIN CHANGED — the route change did not stay in its lane.')
        sys.exit(1)
    print('terrain and biomes identical.')


main()
