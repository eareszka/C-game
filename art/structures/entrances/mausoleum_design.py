"""The large graveyard's entrance, a mausoleum, laid out for tools/draw_views.py.

    python art/structures/entrances/mausoleum_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/mausoleum

64x64, four cells by four: the 2x2 stamp is the bottom two rows of the middle
two columns, the stone either side of it is solid and the two rows above are
walked behind -- see gen_entrance_art.py.

A small stone temple in the ruins' grey and the houses' oblique projection: a
raised base, a walled cella with a dark doorway and a stair going down, two
columns before it, an entablature and a gabled roof with a cross in its
pediment.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, stair, check, rect, fill, oblique

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda'}


def mausoleum():
    B, C = 61, 'courses'
    sc = Scene(64, 64, B)
    sc.box(0, 4, 47, 0, 12, 0, 3, C)                       # the raised base
    sc.box(1, 8, 43, 5, 11, 3, 28, C)                      # the cella
    # its doorway, in the cella's front face, with a stair going down
    dx0, dy0 = oblique(19, 5, 22, B)
    dx1, dy1 = oblique(32, 5, 3, B)
    sc.flat(2, lambda g: stair(g, dx0, dx1, dy0, dy1, tread=3), 4.9)
    sc.box(3, 10, 14, 1, 3, 3, 27, 'column')
    sc.box(4, 37, 41, 1, 3, 3, 27, 'column')
    sc.box(5, 6, 45, 0, 12, 28, 32, C)                     # the entablature
    sc.gable(6, 6, 45, 0, 12, 32, 12)                      # the roof

    def cross(g):
        cx, cy = oblique(25, 0, 38, B)
        fill(g, rect(cx, cy - 3, cx + 1, cy + 3), 'D')
        fill(g, rect(cx - 2, cy - 1, cx + 3, cy), 'D')
    sc.flat(1006, cross, -0.02)                           # on the gable front (pid 6 + 1000)
    return sc.render()


def design():
    g = mausoleum()
    check(g, 'mausoleum')
    return {'pal': PAL, 'view_w': 64, 'order': ['mausoleum'], 'views': {'mausoleum': g.rows()}}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
