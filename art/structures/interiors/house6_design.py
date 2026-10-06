"""The two-storey house's room: a bed with a blue blanket in the back
right corner, a red sofa, a rug.

    python art/structures/interiors/house6_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house6

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house6_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': '7c0a1b', 'Z': '5d1e1f', 'm': 'bcbeca', 'R': '375a94', 'C': 'b6433d'}


def design():
    r = new_room()
    bed(r, 168, BACK + 8, flip=True)
    sofa(r, 80, BACK + 8)
    rug(r, 66, 116, 30, 8)
    return finish(r, 'house 6', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
