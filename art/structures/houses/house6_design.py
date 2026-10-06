"""A two-storey red-brick house: a dark grey roof, two rows of shuttered
windows (tools/house_shapes.py).

    python art/structures/houses/house6_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house6
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': '7c0a1b', 'S': '5d1e1f', 'M': 'bcbeca', 'R': '474751'}


def design():
    h = House(6, 8)
    h.wing(6, 66, 18, 66, 26)
    door = h.door(16)                                        # half a tile of brick to the window
    h.window(40, 6, shutters=True)
    for x in (16, 40):                                       # the upper floor's over them, half a tile between and under the eave
        h.window(x, 4.5, shutters=True)
    return h.finish('house 6', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
