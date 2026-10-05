"""The oasis entrance, two ways, laid out for tools/draw_views.py.

    python art/structures/entrances/oasis_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/oasis

    x  0..79  in sand: a palm either side
    x 80..159 in snow: a pair of snow-capped boulders either side

Each is 80x32, five cells by two, over a 1x1 stamp in the bottom middle cell:
the ladder down a hole every 1x1 way in has (entrance_shapes.ladder_hole).

The water is not here. Every oasis grows its own pool of real pond tiles,
north of the stamp, in a shape of its own (stamp_dungeon_surround in
src/tilemap.cpp), and the game's shoreline draws its edge. What stands beside
it is: the user's palms (palm.aseprite) or the boulders, two cells out either
side of the ladder -- crown or top walked behind, trunk or foot solid -- and
in snow, steam off the water (steam.aseprite, drawn by the game).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Grid, check, outline, ladder_hole, read_sprite, LADDER_TONES, stand, depth_layers

W, H = 80, 32
PALM = {'K': '000000', 'G': '235436', 'g': '058f3a', 'l': '4edc4a', 'T': 'd7a175', 't': '605028'}
PAL = dict({'D': '595965', 'M': '9797aa', 'S': 'fcfcfc'}, **LADDER_TONES, **PALM)


def lay(g, rows, x0, y0):
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != '.':
                g.put(x0 + x, y0 + y, c)


def boulder(g, cx, cy, rx, ry):
    """A rock with snow on its top, lit on the upper left."""
    for y in range(H):
        for x in range(W):
            nx, ny = (x + .5 - cx) / rx, (y + .5 - cy) / ry
            if nx * nx + ny * ny > 1:
                continue
            v = nx * .6 + ny * .8
            g.put(x, y, 'S' if ny < -.35 else 'D' if v > .35 else 'M')


# The ladder hole lies flat in the ground: each pixel on its own row. It is the
# way in.
HOLE = (32, 16, 48, 32)
hole_way = lambda: {(x, y) for y in range(HOLE[1], HOLE[3]) for x in range(HOLE[0], HOLE[2])}


def sand():
    """Each palm stands on its trunk's foot: the whole palm on the row the
    trunk meets the ground, the trunk's last three rows the ground it stands on."""
    g = Grid(W, H)
    palm = read_sprite('entrances/palm.png', 0, 0, 16, 32, PALM)
    lay(g, palm, 0, 0)
    lay(g, palm, 64, 0)
    lay(g, ladder_hole(), 32, 16)
    bottom = max(y for y, r in enumerate(palm) if r.strip('.'))
    foot = set()
    for x0 in (0, 64):
        for y in range(bottom - 2, bottom + 1):
            xs = [x for x, c in enumerate(palm[y]) if c != '.']
            foot |= {(x0 + x, y) for x in range(min(xs), max(xs) + 1)}
    return stand(g, lambda x, y: y if HOLE[0] <= x < HOLE[2] else bottom, foot, hole_way())


BOULDERS = ((8, 22, 6, 5), (9, 14, 4, 3.5), (71, 22, 6, 5), (70, 14, 4, 3.5))


def snow():
    """Each boulder stands on the row its foot touches, the lower half of it
    the ground it stands on; where two overlap the nearer one is drawn."""
    g = Grid(W, H)
    for b in BOULDERS:
        boulder(g, *b)
    outline(g)
    lay(g, ladder_hole(), 32, 16)
    inside = lambda b, x, y, grow=0: ((x + .5 - b[0]) / (b[2] + grow)) ** 2 + ((y + .5 - b[1]) / (b[3] + grow)) ** 2 <= 1
    def footy(x, y):
        if HOLE[0] <= x < HOLE[2]:
            return y
        mine = [b for b in BOULDERS if inside(b, x, y, grow=1)]          # with its outline
        return round(max(b[1] + b[3] for b in mine)) if mine else y
    foot = {(x, y) for b in BOULDERS for y in range(H) for x in range(W) if inside(b, x, y) and y + .5 >= b[1]}
    return stand(g, footy, foot, hole_way())


def design():
    a, b = sand(), snow()
    for name, g in (('oasis sand', a), ('oasis snow', b)):
        # the palm is a part, with its own room above it in the world
        room = Grid(W, H + 1)
        room.g = [['.'] * W] + [r[:] for r in g.g]
        check(room, name, objects=True)
    return {'pal': PAL, 'view_w': W, 'order': ['sand', 'snow'],
            'views': {'sand': a.rows(), 'snow': b.rows()},
            'depth': depth_layers(2 * W, H, [(0, 0, a), (W, 0, b)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
