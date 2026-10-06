"""The cream-brick house's kitchen: a cupboard and an iron stove against the
back wall.

    python art/structures/interiors/house4_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/house4

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/house4_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': 'e8e0c0', 'Z': 'b29e5c', 'm': 'cebe82', 'R': 'b6433d'}


def design():
    r = new_room()
    cupboard(r, 108)
    stove(r, 148)
    return finish(r, 'house 4', PAL)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
