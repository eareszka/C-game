"""A tan-brick ranch house: long and low, a green roof, shutters, a
picture window (tools/house_shapes.py).

    python art/structures/houses/house2_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house2
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': 'c18a39', 'S': '815423', 'M': 'fce4a0', 'R': '2c6c44'}


def design():
    h = House(7, 7)
    h.wing(5, 80, 16, 34, 22)
    door = h.door(16)                                        # half a tile of brick to the window, half a tile under the eave
    h.window(40, 5.5, tiles=2)
    return h.finish('house 2', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
