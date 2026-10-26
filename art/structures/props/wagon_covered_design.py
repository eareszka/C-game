"""The covered wagon, overworld scenery, laid out for tools/draw_views.py.

    python art/structures/props/wagon_covered_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/props/wagon_covered

48x32, three cells by two, in the houses' projection: a plank bed in wood on
two spoked wheels, its tongue dropped to the ground on the left, under a
canvas bonnet in white paint drawn over its hoops -- the bonnet's top lit, its
front the paint's mid tone, the hoops' folds in its shade, and the end turned
away (the east) an arch of canvas round the dark inside. The design came from
a PixelLab draft (pixellab-out/wagon-covered/sprites/v3), rebuilt here so the
projection, the line and the materials are the bible's. The burnt wagon
(landmarks/wagon_design.py) is the same build after the fire.

The bonnet sits wholly in the top row of cells and the bed and wheels in the
bottom row, so canvas and wood never share a cell: four colours a cell.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
sys.path.insert(0, os.path.join(HERE, '..', 'landmarks'))
from landmark_shapes import export, main
from entrance_shapes import Scene, rect, fill, check, four_per_cell

# tools/overworld_style.py MATERIALS: wood, white paint -- light, mid, dark
PAL = {'K': '000000',
       'L': '967448', 'M': '785830', 'D': '493712',      # wood
       'a': 'fcfcfc', 'b': 'c6ccda', 'c': '9797aa'}      # white paint (the canvas)

BASE = 29                         # the ground line
BED = (5, 37, 0, 8, 6, 13)        # x0, x1, d0, d1, z0, z1: the bed's top front edge on row 16
HOOD = (6, 36, 0, 8, 13.5, 7.0)   # x0, x1, d0, d1, eave, rise
HOOPS = (12, 18, 24, 30)


def bonnet(sc):
    x0, x1, d0, d1, z0, rise = HOOD
    dm, rad = (d0 + d1) / 2, (d1 - d0) / 2 + 0.6
    arch = lambda d: z0 + rise * max(0.0, 1 - ((d - dm) / rad) ** 2) ** 0.5
    step = 0.25
    pts, end = [], []
    d = d0
    while d <= d1:
        z = arch(d)
        steep = abs(arch(min(d + step, d1)) - arch(max(d - step, d0))) / (2 * step) > 1.1
        x = x0
        while x <= x1:
            hoop = any(abs(x - h) < 0.5 for h in HOOPS)
            tone = 'c' if hoop else ('b' if steep and d < dm else 'a')
            pts.append((x, d, z, tone))
            x += step
        # the end turned away: a rim of canvas round the dark inside
        zz = z0
        while zz <= z:
            inside = d0 + 0.9 < d < d1 - 0.6 and zz < z - 0.9
            end.append((x1 + 0.01, d, zz, 'K' if inside else 'c'))
            zz += step
        d += step
    sc.points(10, pts)
    # the front face hangs straight down to the eave as well, so it closes on the bed
    sc.points(10, [(x, d0, z, 'b') for x in [x0 + i * step for i in range(int((x1 - x0) / step) + 1)]
                   for z in [z0 + j * step for j in range(int((arch(d0) - z0) / step) + 1)]])
    # each hoop a fold in the canvas, over the top and down the front, unbroken
    folds = []
    for h in HOOPS:
        d = d0
        while d <= d1:
            folds.append((h, d, arch(d), 'c'))
            d += step / 2
        z = z0
        while z <= arch(d0):
            folds.append((h, d0, z, 'c'))
            z += step / 2
    sc.points(10, folds, nearer=0.05)
    sc.points(11, end, nearer=0.02)


def wheel(cx, cz=5, r=5.2):
    def draw(t):
        cy = BASE - cz + 1          # in front of the bed, a step nearer the viewer
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dx, dy = x - cx, y - cy
                rr = (dx * dx + dy * dy) ** 0.5
                if rr > r:
                    continue
                if rr < 1.3:
                    c = 'L'                                      # the hub
                elif rr > r - 1.4:
                    c = 'M'                                      # the felloe
                elif dx == 0 or dy == 0 or abs(abs(dx) - abs(dy)) < 0.5:
                    c = 'M'                                      # eight spokes
                else:
                    c = 'D'
                t.put(x, y, c)
    return draw


def wagon():
    sc = Scene(48, 32, BASE)
    x0, x1, d0, d1, z0, z1 = BED
    sc.box(0, x0, x1, d0, d1, z0, z1, front='M')
    bonnet(sc)
    sc.flat(3, wheel(11.5), -1)
    sc.flat(4, wheel(30.5), -1)
    # the tongue, dropped to the ground on the left
    sc.flat(5, lambda t: fill(t, rect(2, BASE - 3, 7, BASE - 2), 'M') or fill(t, rect(2, BASE - 3, 7, BASE - 3), 'L'), -0.5)
    sc.ground(x0, x1, d0, d1)
    g = sc.render()
    # the bed's boards: a seam along the middle of its front, a stake at each end and either side of the middle
    for y in range(g.h):
        for x in range(g.w):
            if sc.pid[y][x] != 0 or g.g[y][x] != 'M':
                continue
            if y == 19 or x in (x0 + 1, 21, x1 - 1):
                g.g[y][x] = 'D'
    four_per_cell(g, [('c', 'b'), ('L', 'M')])
    check(g, 'covered wagon')
    return g


def design():
    return export('wagon_covered', PAL, 3, 2, [(0, 0, wagon())], None, 3)


if __name__ == '__main__':
    main(design)
