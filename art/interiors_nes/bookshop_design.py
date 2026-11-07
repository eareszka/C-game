"""Room 1, the book shop, NES style: the room's own brick and boards, and
PixelLab's wall of shelves, counter and two bookcases over the old ones (the
same places and sizes: the feet, the clerk's and the shoppers' routes meet
them exactly as before). For life, things in nobody's way: a library ladder
against the shelves, a globe on the blue bookcase, a rug before the counter.
Nothing new stands on the floor.

    python tools/interior_nes.py 1 art/interiors_nes/bookshop_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': '967448', 'Z': '633e1b', 'm': 'fce4a0', 'T': '967448', 'R': 'b6433d', 'C': '375a94'}


def design():
    r = new_room(windows=())
    # the shelves built into the back wall, on whole tiles (interior_room.wall_shelves)
    shelves = art('shop_shelves2')
    sprite_rich(r, shelves, 80, 15, BACK, choices=colours_of(shelves, 6, drop_dark=False), room=True)
    rug(r, 100, 124, 40, 10)
    piece(r, lambda: counter(r, 96, 105), art('shop_counter'),          # orange top, red-brown front, dark side
          choices=['fc9838', '792727', '531b1c'])          # its top under the raft book (interior_book_spot)
    piece(r, lambda: bookcase(r, 150, 92), art('shop_case_red'))
    box = piece(r, lambda: bookcase(r, 182, 118, book='C'), art('shop_case_blue'))
    # the ladder: its rails and rungs, without the shelves PixelLab drew behind them
    lad = art('shop_ladder')
    bg = lad.getpixel((3, 5))[:3]                            # the dark behind the books
    lad = lad.crop((11, 0, 22, 27))
    sprite_rich(r, lad, 104, 37, BACK, choices=['d7a175', 'c18a39', '633e1b'],
                cut=lambda x, y: sum((a - b) ** 2 for a, b in zip(lad.getpixel((x, y))[:3], bg)) < 1200)
    # the globe on the blue bookcase's top, drawn as the case is
    globe = art('shop_globe')
    sprite_rich(r, globe, box[0] + 10, box[1] - 9, 118, choices=colours_of(globe, 4))
    return finish(r, 'book shop nes', PAL)
