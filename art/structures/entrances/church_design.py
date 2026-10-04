"""The catacombs' entrance, an ancient church, laid out for tools/draw_views.py.

    python art/structures/entrances/church_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/church

160x160, ten cells by ten, over a 2x2 stamp in the bottom two rows of the
middle two columns; the stone beside the doorway is solid and the rows above
are walked behind (gen_entrance_art.py works that out, as for a building).

A tall stone church after the Temple of Time, in the ruins' grey stone and the
houses' oblique projection: a great central tower over a tall arched door on
the stamp, lancets and a rose window up its face and a steep spire on it; a
tall nave behind under a steep roof, its windows down the side; a turret at
each front corner. Ruined -- the spire snapped partway up, one turret broken,
a stretch of the nave roof fallen in with the rafters showing, the stone
chipped and cracked -- but its coloured glass still in the windows. Where a
window's glass needs a cell's colours, the stone's lit and shaded edges give
way to its base grey (four_per_cell).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, check, rect, fill, oblique, weather, four_per_cell, drop_crumbs

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda',     # the ruins' stone
       'r': 'b70000', 'b': '5c94fc', 'y': 'f0bc3c'}                      # glass
W, H, B = 160, 160, 157
CX = 80                                   # the doorway's middle: the stamp's middle
NX0, NX1, ND0, ND1 = 42, 117, 8, 34       # the nave: across, and from how far back to
WALL, GABLE = 52, 30                      # its walls' height, and its roof's above them
TX0, TX1, TD = 63, 96, 10                 # the central tower: across, and how deep
TALL, SPIRE = 92, 40                      # its height, and its spire's above that
C = 'courses'


def glass_window(sc, pid, plane, a0, a1, z0, z1, colours):
    """A tall window with a pointed head, its glass in two colours in quarters
    with a black leading cross: plane is ('front', d) for a face looking at the
    viewer, ('side', x) for a face looking to the right."""
    pts = []
    mid = (a0 + a1) / 2
    half = (a1 - a0) / 2
    for i in range(int((a1 - a0) * 4) + 1):
        a = a0 + i / 4
        for j in range(int((z1 - z0) * 4) + 1):
            z = z0 + j / 4
            head = z1 - (z1 - z0) * .3
            if z > head and abs(a - mid) > half * (1 - (z - head) / (z1 - head)):
                continue
            lead = abs(a - mid) < .5 or abs(z - (z0 + (z1 - z0) * .45)) < .5 \
                or abs(a - a0) < .6 or abs(a - a1) < .6 or z - z0 < .6
            c = 'K' if lead else colours[(a < mid) ^ (z > (z0 + z1) / 2)]
            pts.append((a, plane[1] - .05, z, c) if plane[0] == 'front' else (plane[1], a, z, c))
    sc.points(pid, pts, nearer=.05)


def rose(sc, pid, cx, d, cz, rr):
    pts = []
    for i in range(-rr * 4, rr * 4 + 1):
        for j in range(-rr * 4, rr * 4 + 1):
            a, z = i / 4, j / 4
            r = math.hypot(a, z)
            if r > rr:
                continue
            ang = math.atan2(z, a)
            spoke = r > 2 and abs(math.sin(ang * 4)) < .18
            c = 'K' if r > rr - .8 or spoke or r < 1 else ('r' if (int(ang / (math.pi / 4)) % 2) else 'b')
            pts.append((cx + a, d - .05, cz + z, c))
    sc.points(pid, pts, nearer=.05)


def church():
    sc = Scene(W, H, B)
    rng = random.Random(7)
    # what time has taken, decided before anything is drawn so what stood
    # behind shows through: the spire snapped partway up, and the right
    # turret's cap and the top of it gone
    sc.break_off({9, 1009}, TX0 - 4, TX1 + 12, B - TALL - 36, 3, seed=11)
    sc.break_off({7, 17, 1017}, NX1 - 10, NX1 + 18, B - 62 - ND0, 3, seed=12)
    # the nave behind, and its steep roof with a hole fallen through it
    sc.box(0, NX0, NX1, ND0, ND1, 0, WALL, 'M')
    sc.gable(1, NX0, NX1, ND0, ND1, WALL, GABLE, shingles=True)
    xm, half = (NX0 + NX1) / 2, (NX1 - NX0) / 2
    top = lambda x: WALL + GABLE * (1 - abs(x - xm) / half)
    hole = []
    for k in range(0, 4 * 24):
        x = xm + 4 + k / 4
        lo, hi = 14 + rng.random() * 2, 27 - rng.random() * 2
        dd = lo
        while dd <= hi:
            rafter = abs(dd - 18) < .5 or abs(dd - 22.5) < .5
            hole.append((x, dd, top(x) + .05, 'M' if rafter else 'K'))
            dd += .25
    sc.points(2, hole, nearer=1)
    for k, d0 in enumerate((12, 20, 28)):                        # windows down its side
        glass_window(sc, 3 + k, ('side', NX1), d0, d0 + 4, 14, 42, 'by')
    # a turret at each front corner of the nave
    for pid, x0 in ((6, NX0 - 4), (7, NX1 - 8)):
        sc.box(pid, x0, x0 + 12, ND0 - 6, ND0 + 4, 0, 70, C)
        sc.gable(pid + 10, x0 - 1, x0 + 13, ND0 - 7, ND0 + 5, 70, 18, shingles=True)
    # the great central tower, its spire, its glass and its door
    sc.box(8, TX0, TX1, 0, TD, 0, TALL, C)
    sc.gable(9, TX0 - 2, TX1 + 2, -1, TD + 1, TALL, SPIRE, shingles=True)
    glass_window(sc, 20, ('front', 0), TX0 + 6, TX0 + 12, 38, 64, 'rb')
    glass_window(sc, 21, ('front', 0), TX1 - 12, TX1 - 6, 38, 64, 'br')
    rose(sc, 22, CX, 0, 78, 8)

    def door(g):
        x0, x1 = CX - 8, CX + 7
        for y in range(B - 32, B + 1):
            for x in range(x0, x1 + 1):
                if y < B - 24 and ((x + .5 - CX) / 8) ** 2 + ((y + .5 - (B - 24)) / 8) ** 2 > 1:
                    continue
                g.put(x, y, 'K')
        for x in range(x0 + 1, x1):                              # a worn step inside
            g.put(x, B - 2, 'D')
    sc.flat(23, door, -.2)
    g = sc.render()
    weather(g, 41, 'M', 'D', chips=34, cracks=36,
            keep=[(CX - 10, B - 35, CX + 10, B + 2), (CX - 10, B - 88, CX + 10, B - 69)])
    four_per_cell(g, [('L', 'M'), ('y', 'b'), ('D', 'M')])
    drop_crumbs(g)                       # the weathering can leave its own
    return g


def design():
    g = church()
    check(g, 'church', objects=True)
    return {'pal': PAL, 'view_w': W, 'order': ['church'], 'views': {'church': g.rows()}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
