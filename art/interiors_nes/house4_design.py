"""Room 4, the cream-brick house's kitchen (and, until the lighthouse has a
room of its own, the lighthouse keeper's), NES style: the room's own cream
brick and boards, PixelLab's pale blue painted cupboard and cream enamel
stove over the old ones (the same places and sizes), and in nobody's way a
rack of blue-and-white plates over the cupboard and a rug. Nothing new
stands on the floor, so the keeper's spot and every route are as before.

    python tools/interior_nes.py 4 art/interiors_nes/house4_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': 'e8e0c0', 'Z': 'b29e5c', 'm': 'cebe82', 'R': '375a94'}


def design():
    r = new_room()
    rug(r, 120, 112, 38, 12)
    piece(r, lambda: cupboard(r, 108), art('h4_cupboard'),
          choices=['d7a175', 'bcbeca', '375a94', '2b1f40'])           # wooden top, pale blue doors, blue, dark side
    piece(r, lambda: stove(r, 148), art('h4_stove'),
          choices=['e8e0c0', '34343e', 'b2966a', 'a4aaba'])           # enamel, black top, its shade, chrome
    plates = art('h4_plates').crop((0, 0, 32, 23))                    # the rack, not the brick PixelLab put under it
    sprite_rich(r, plates, 112, 30, BACK, choices=['fcfcfc', '375a94', '785830', '463422'])
    return finish(r, 'house 4 nes', PAL)
