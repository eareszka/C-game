"""The slab, desert scenery: a low shelf of rock lying on the sand, cracked into plates.

    python art/structures/props/desert/slab_design.py

48x32, three cells by two, after a PixelLab draft
(pixellab-out/desert-slab/sprites/v1): a rounded slab a few pixels thick, its
top split by cracks into plates, the cracks running on down its front, and a
few pebbles broken off beside it. A solid in the houses' projection
(tools/prop_paint.py voxels), in the cliffs' rock: the top lit, the front mid,
the east side dark; cracks and the line round each piece black.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import voxels, save
from entrance_shapes import check

W, H, BASE = 48, 32, 28
X0, X1, D0, D1, TALL = 5, 31, 0, 11, 4       # the slab's footprint and thickness
ROUND = 3.5                                   # how round its corners are
# the cracks across its top, as runs of (x, d) -- each meets an edge or another crack
CRACKS = [
    [(13, 0), (13, 1), (14, 2), (14, 3), (15, 4), (16, 5), (16, 6), (17, 7), (17, 8), (18, 9), (18, 10), (18, 11)],
    [(5, 6), (6, 6), (7, 6), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5), (13, 4), (14, 4), (15, 4)],
    [(16, 6), (17, 6), (18, 5), (19, 5), (20, 5), (21, 5), (22, 4), (23, 4), (24, 4), (25, 3), (26, 3), (27, 2), (28, 2), (29, 1), (30, 1), (31, 1)],
    [(24, 4), (24, 5), (25, 6), (25, 7), (26, 8), (26, 9), (27, 10), (27, 11)],
]
PEBBLES = [(2, 0, 0), (37, -2, 1), (41, 0, 0), (39, 3, 0)]   # x, d, size (0: one cell)


def inside(x, d):
    cx = min(max(x, X0 + ROUND), X1 - ROUND)
    cd = min(max(d, D0 + ROUND), D1 - ROUND)
    return (x - cx) ** 2 + (d - cd) ** 2 <= ROUND ** 2 + 0.5


def solid():
    cells, part = set(), {}
    for x in range(X0, X1 + 1):
        for d in range(D0, D1 + 1):
            if inside(x, d):
                for z in range(TALL):
                    cells.add((x, d, z)); part[(x, d, z)] = 0
    for i, (px, pd, size) in enumerate(PEBBLES):
        for x in range(px, px + 1 + size):
            for d in range(pd, pd + 1 + size):
                for z in range(1 + size):
                    cells.add((x, d, z)); part[(x, d, z)] = 1 + i
    return cells, part


CELLS, PART = solid()
SPLIT = {p for run in CRACKS for p in run}


def tone(x, d, z, face):
    if PART[(x, d, z)] == 0 and face == 'south' and (x, 0) in SPLIT and z >= 1:
        return 'K'                         # a crack running on down the front
    return None


def crack(g):
    """The cracks drawn on the screen, not cell by cell: a step back in d is a step up and to
    the right, so a crack laid in cells falls apart into dots. Each run is joined point to
    point across the lit top only."""
    for run in CRACKS:
        pts = [(x + d, BASE - TALL - d) for x, d in run]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            n = max(abs(xb - xa), abs(yb - ya), 1)
            for i in range(n + 1):
                x, y = round(xa + (xb - xa) * i / n), round(ya + (yb - ya) * i / n)
                if g.g[y][x] == 'L':
                    g.g[y][x] = 'K'



if __name__ == '__main__':
    g = voxels(W, H, BASE, CELLS, tone, lambda x, d, z: PART[(x, d, z)])
    crack(g)
    check(g, 'slab', objects=True, speck=4)
    save(g.g, os.path.join(HERE, 'slab.png'), 'rock', {'L': 'b29e5c', 'M': '887000', 'D': '493712'})
