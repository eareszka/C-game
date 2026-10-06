"""A cream-brick house: a blue roof, shuttered windows (tools/house_shapes.py).

    python art/structures/houses/house4_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/houses/house4
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from house_shapes import House

# brick (and side face), its shade (and door), mortar (and trim and panes), roof
PAL = {'K': '000000', 'B': 'e8e0c0', 'S': 'b29e5c', 'M': 'cebe82', 'R': '375a94'}


def design():
    h = House(6, 6)
    h.wing(6, 64, 18, 34, 24, side='M')                      # its brick's base is its lightest tone
    door = h.door(16)                                        # half a tile of brick to the window, half a tile under the eave
    h.window(40, 4.5, shutters=True)
    return h.finish('house 4', PAL, door)


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
