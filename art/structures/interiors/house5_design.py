"""The brown-brick house's sitting room: a green sofa against the back wall,
a rug with a low table on it, a bookcase.

    python art/structures/interiors/house5_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house5

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house5_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': '815423', 'Z': '583518', 'm': 'd89830', 'R': 'b6433d', 'C': '2c6c44'}


def design():
    r = new_room()
    sofa(r, 104, BACK + 8)
    rug(r, 92, 104, 44, 12, border=False)
    low_table(r, 106, 96)
    bookcase(r, 170, 118)
    return finish(r, 'house 5', PAL, merge=[('C', 'R')])


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
