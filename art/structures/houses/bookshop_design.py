"""The book shop: a brick storefront with a flat roof behind its parapet,
a sign, a striped awning over the display window (tools/house_shapes.py).

    python art/structures/houses/bookshop_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/bookshop
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': '967448', 'S': '633e1b', 'M': 'fce4a0', 'R': '595965'}


def design():
    h = House(9, 6)
    h.wing(4, 120, 16, 64, 0)                                # its wall's top on a tile row
    h.sign(30, 50, 'BOOKS')
    h.awning(13, 39, 35, 0)                                  # over the display window
    h.window(8, 4.5, tiles=2)
    door = h.door(48)
    for x in (72, 96):                                       # two windows right of the door, half a tile apart
        h.window(x, 4.5)
    return h.finish('book shop', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
