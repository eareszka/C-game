"""The dark-red-brick cottage's room (the girl's parents'): an iron stove and
a kitchen counter on the back wall, two beds with their heads against the
right wall -- the back one the girl's, the front one the sailor fisher's.

    python art/structures/interiors/house3_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house3

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house3_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': '792727', 'Z': '531b1c', 'm': 'e8e0c0', 'R': 'b6433d'}


def design():
    r = new_room()
    stove(r, 72)                       # left of the counter, iron and wood a tile apart
    cupboard(r, 100, w=26)
    bed_against_wall(r, 76, 'right')   # the girl's
    bed_against_wall(r, 110, 'right')  # the sailor fisher's
    return finish(r, 'house 3', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
