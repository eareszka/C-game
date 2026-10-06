"""A dark-red-brick cottage: a grey roof, two windows (tools/house_shapes.py).

    python art/structures/houses/house3_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house3
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': '792727', 'S': '531b1c', 'M': 'e8e0c0', 'R': '595965'}


def design():
    h = House(6, 7)
    h.wing(6, 64, 18, 34, 30)
    door = h.door(16)                                        # half a tile of brick to the window, half a tile under the eave
    h.window(40, 5.5)
    return h.finish('house 3', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
