"""The spawn house: a red-brick bungalow, brown shingles, a chimney, white
trim and black shutters (tools/house_shapes.py).

    python art/structures/houses/house0_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house0
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': 'b6433d', 'S': '792727', 'M': 'e8e0c0', 'R': '633e1b'}


def design():
    h = House(6, 7)
    h.wing(6, 66, 20, 34, 31)                                # its ridge on a tile row (y 32)
    h.chimney(44, 10, 16, 74, depth=4)                       # behind the ridge
    door = h.door(16)                                        # half a tile of brick to the window, half a tile under the eave
    h.window(40, 5.5, shutters=True)
    return h.finish('house 0', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
