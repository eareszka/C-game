"""The ruins' walls seen from inside, in the seven cells every dungeon type's
walls are built from (tools/dungeon_walls.py): the north face whole, cracked,
and with a block fallen out, then the wall top's rim.

    python art/structures/dungeon_walls/ruins_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/dungeon_walls/ruins

Stone is the bible's (art/direction/INTERIOR_STYLE.md). The faces are its
dark stone (user: "much darker, almost surreal darkness"): a their base, b
their shade, black joints. The rim keeps the pale stone, L, M, D.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from dungeon_walls import Grid, recess, views
from interior_style import MATERIALS, masonry

PAL = {'K': '000000', **dict(zip('LMD', MATERIALS['stone']['tones'])), **dict(zip('ab', MATERIALS['dark stone']['tones']))}


def band(hole=None, crack=()):
    g = Grid(16, 48)
    g.g = masonry(16, 48, [(1 + 8 * c, 8, 16, 8 * (c % 2)) for c in range(6)], 'a', 'b', 'K')   # blocks 16 x 8: a face tiles every 16px
    for x in range(16):
        g.put(x, 0, 'b')                       # in the shadow of the cap above
        g.put(x, 47, 'K')                      # the foot against the floor
    if hole:
        recess(g, *hole, shade='K')
    for x, y in crack:
        g.put(x, y, 'K')
    return g.rows()


def design():
    crack = [(5, 15), (6, 16), (6, 17), (7, 18), (12, 27), (11, 28), (11, 29), (12, 30), (13, 31)]
    v = views([band(), band(crack=crack), band(hole=(0, 17, 14, 23))])    # a whole block of the third course
    return {'pal': PAL, 'view_w': 16, 'order': list(v), 'views': v}


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
