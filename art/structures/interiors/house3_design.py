"""The dark-red-brick cottage's room: two beds side by side at the back,
a rug, a chest of drawers.

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
    bed(r, 76, BACK + 8)
    bed(r, 112, BACK + 8)
    dresser(r, 154)
    rug(r, 104, 116, 40, 10)
    return finish(r, 'house 3', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
