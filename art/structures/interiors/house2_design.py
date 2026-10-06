"""The tan-brick ranch house's room: a bed with a green blanket in the back
right corner.

    python art/structures/interiors/house2_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house2

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house2_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': 'c18a39', 'Z': '815423', 'm': 'fce4a0', 'R': '2c6c44'}


def design():
    r = new_room()
    bed(r, 168, BACK + 8, flip=True)
    return finish(r, 'house 2', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
