"""The ruins entrance, laid out for tools/draw_views.py.

    python art/structures/entrances/ruins_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/entrances/ruins

Two sizes on one canvas, side by side:

    x  0..95  large (2x2 stamp): a ruined temple the size of a town house,
              96x80, six cells by five; the stamp is the bottom two rows of
              the middle two columns
    x 96..143 small (1x1 stamp): a broken gateway, 48x48, three cells by
              three; the stamp is the bottom middle cell

Drawn in the houses' oblique projection (entrance_shapes.oblique): every wall
is a block with a front face, a shaded right side going back at 45 degrees and
a lit top -- broken walls show the tops of their courses. Like a house, the
stone beside the doorway is solid and the upper rows are walked behind.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import Scene, stair, check, depth_layers

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda'}


def build(w, h, base, parts, hull, way):
    """parts: [[(x0, x1, d0, d1, z0, z1, front), ...] | ('door', x0, x1, z1, tread, d)].
    Each list is one piece of stone (no line between its blocks); the scene's
    depth buffer decides what is in front. The ruin is stood on whole, hull
    (x0, x1, d0, d1) -- walls, rubble and what lies between them -- but for
    way (sx0, sx1, d0, d1), the doorway, walked into as far as its stair."""
    sc = Scene(w, h, base)
    sc.ground(*hull)
    sc.carve(*way)
    for pid, part in enumerate(parts):
        if part[0] == 'door':
            _, x0, x1, z1, tread, d = part
            sc.flat(pid, lambda g: stair(g, x0, x1, base - z1, base, tread=tread), d)
            continue
        for b in part:
            sc.box(pid, *b)
    return sc.render()


def large():
    B, C = 77, 'courses'                      # B: the front faces' ground row
    return build(96, 80, B, [
        # the back wall, broken off at uneven heights
        [(4, 15, 16, 18, 0, 42, C), (16, 21, 16, 18, 0, 36, C), (22, 33, 16, 18, 0, 50, C),
         (34, 39, 16, 18, 0, 41, C), (40, 51, 16, 18, 0, 46, C), (52, 57, 16, 18, 0, 30, C),
         (58, 67, 16, 18, 0, 34, C), (68, 75, 16, 18, 0, 18, C)],
        # side walls running back: tall on the left, crumbled low on the right
        [(4, 6, 9, 15, 0, 38, C), (4, 6, 4, 8, 0, 27, C), (4, 6, 0, 3, 0, 20, C)],
        [(73, 75, 8, 15, 0, 16, C), (73, 75, 0, 7, 0, 11, C)],
        # the front wall either side of the gate
        [(7, 17, 0, 2, 0, 29, C), (18, 29, 0, 2, 0, 23, C)],
        [(64, 72, 0, 2, 0, 11, C)],
        ('door', 36, 57, 33, 4, 3.5),         # behind the posts' faces, in front of the back wall
        [(30, 35, 0, 3, 0, 33, 'column')],
        [(58, 63, 0, 3, 0, 33, 'column')],
        [(28, 65, 0, 3, 34, 40, C)],          # the beam over the gate
        [(78, 89, 0, 3, 0, 5, 'column')],     # a fallen column
    ], hull=(4, 75, 0, 18), way=(36, 57, -1, 5))


def small():
    B, C = 45, 'courses'
    return build(48, 48, B, [
        [(6, 13, 8, 9, 0, 22, C), (14, 21, 8, 9, 0, 30, C), (22, 27, 8, 9, 0, 25, C),
         (28, 33, 8, 9, 0, 16, C)],
        ('door', 18, 29, 22, 3, 2.5),
        [(13, 17, 0, 2, 0, 21, 'column')],
        [(30, 34, 0, 2, 0, 21, 'column')],
        [(11, 36, 0, 2, 22, 26, C)],
        [(3, 9, 0, 2, 0, 4, C)],
        [(37, 42, 0, 2, 0, 5, C)],
    ], hull=(3, 42, 0, 9), way=(18, 29, -1, 6))


def design():
    lg, sm = large(), small()
    check(lg, 'ruins large'); check(sm, 'ruins small')
    return {'pal': PAL, 'view_w': 96, 'order': ['large'], 'views': {'large': lg.rows()},
            'extras': [[96, 0, sm.rows()]],
            'depth': depth_layers(144, 80, [(0, 0, lg), (96, 0, sm)])}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
