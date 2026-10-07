"""The ruins' walls seen from inside, in the seven cells every dungeon type's
walls are built from (tools/dungeon_walls.py): the north face whole, cracked,
and with a block fallen out, then the wall top's rim.

    python art/structures/dungeon_walls/ruins_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/ruins

Stone is the ruins entrance's (entrances/ruins_design.py): K line, D shade,
M base, L lit, laid by entrance_shapes.courses -- 8-wide blocks rather than
the exterior's 6 so a face tiles every 16px.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from entrance_shapes import courses
from dungeon_walls import Grid, recess, views

PAL = {'K': '000000', 'D': '595965', 'M': '9797aa', 'L': 'c6ccda'}


def band(hole=None, crack=()):
    g = Grid(16, 48)
    face = {(x, y) for x in range(16) for y in range(1, 47)}
    courses(g, face, block_w=8, course_h=4, y0=1, shade_right=0)
    for x in range(16):
        g.put(x, 0, 'D')                       # in the shadow of the cap above
        g.put(x, 47, 'K')                      # the foot against the floor
    if hole:
        recess(g, *hole)
    for x, y in crack:
        g.put(x, y, 'K')
    return g.rows()


def design():
    crack = [(5, 15), (6, 16), (6, 17), (7, 18), (12, 27), (11, 28), (11, 29), (12, 30), (13, 31)]
    v = views([band(), band(crack=crack), band(hole=(8, 21, 15, 25))])
    return {'pal': PAL, 'view_w': 16, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
