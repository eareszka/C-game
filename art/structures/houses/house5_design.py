"""A brown-brick house: a dark red roof, a chimney at the left end (tools/house_shapes.py).

    python art/structures/houses/house5_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house5
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': '815423', 'S': '583518', 'M': 'd89830', 'R': '7c0a1b'}


def design():
    h = House(6, 6)
    h.wing(6, 64, 18, 34, 17)                                # its ridge on a tile row (y 32)
    h.chimney(12, 10, 15, 60, depth=3)                       # behind the ridge
    door = h.door(16)                                        # half a tile of brick to the window, half a tile under the eave
    h.window(40, 4.5, shutters=True)
    return h.finish('house 5', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
