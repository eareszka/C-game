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
from entrance_shapes import Grid, check, outline, ladder_hole, read_sprite, LADDER_TONES

W, H = 80, 32
PALM = {'K': '000000', 'G': '235436', 'g': '058f3a', 'l': '4edc4a', 'T': 'd7a175', 't': '605028'}
PAL = dict({'D': '595965', 'M': '9797aa', 'S': 'fcfcfc'}, **LADDER_TONES, **PALM)
ROLES = {'sand': "^...^#.E.#", 'snow': "^...^#.E.#"}


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


def sand():
    g = Grid(W, H)
    palm = read_sprite('entrances/palm.png', 0, 0, 16, 32, PALM)
    lay(g, palm, 0, 0)
    lay(g, palm, 64, 0)
    lay(g, ladder_hole(), 32, 16)
    return g


def snow():
    g = Grid(W, H)
    for b in ((8, 22, 6, 5), (9, 14, 4, 3.5), (71, 22, 6, 5), (70, 14, 4, 3.5)):
        boulder(g, *b)
    outline(g)
    lay(g, ladder_hole(), 32, 16)
    return g


def design():
    a, b = sand(), snow()
    for name, g in (('oasis sand', a), ('oasis snow', b)):
        # the palm is a part, with its own room above it in the world
        room = Grid(W, H + 1)
        room.g = [['.'] * W] + [r[:] for r in g.g]
        check(room, name, objects=True)
    return {'pal': PAL, 'view_w': W, 'order': ['sand', 'snow'],
            'views': {'sand': a.rows(), 'snow': b.rows()}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
