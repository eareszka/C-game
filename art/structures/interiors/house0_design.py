"""The spawn house's room: red brick, a bed with a blue blanket in the back
right corner, a chest of drawers between the windows. The layout is the user's.

    python art/structures/interiors/house0_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house0

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house0_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': 'b6433d', 'Z': '792727', 'm': 'e8e0c0', 'R': '375a94'}


def design():
    r = new_room()
    bed(r, 168, BACK + 8, flip=True)
    dresser(r, 112)
    return finish(r, 'house 0', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
