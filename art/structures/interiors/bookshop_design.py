"""The book shop: its back wall shelves of books from floor to near the
ceiling, a counter by the door where the raft book lies, two bookcases.

    python art/structures/interiors/bookshop_design.py <design.json>
    python tools/draw_views.py <design.json> art/structures/interiors/bookshop

Built from tools/interior_room.py; its brick and mortar are the house's own
outside (art/structures/houses/bookshop_design.py).
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
from interior_room import *

PAL = {'W': '967448', 'Z': '633e1b', 'm': 'fce4a0', 'T': '967448', 'e': '633e1b', 'L': 'b29e5c', 'R': 'b6433d', 'C': '375a94'}


def design():
    r = new_room(windows=())
    wall_shelves(r, 80, 175, 15, 62)
    counter(r, 96, 105)                                      # its top under the raft book (interior_book_spot)
    bookcase(r, 150, 92)
    bookcase(r, 182, 118)
    return finish(r, 'book shop', PAL, merge=[('C', 'R')])


if __name__ == '__main__':
    json.dump(design(), open(sys.argv[1], 'w'))
