"""Room 3, the dark-red-brick cottage (the girl's parents'), NES style: the
room's own brick and boards, and PixelLab's stove, cupboard and two beds
over the old ones (the same places and sizes) -- the back bed the girl's,
in a patchwork quilt, the front one the sailor fisher's, navy stripes. For
life, in nobody's way: copper pans on a rail over the cupboard, a rug on the
kitchen floor. Nothing new stands on the floor, so the kitchen loop and the
walks to bed are as before.

    python tools/interior_nes.py 3 art/interiors_nes/house3_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': '792727', 'Z': '531b1c', 'm': 'e8e0c0', 'R': 'b6433d'}


def design():
    r = new_room()
    rug(r, 86, 104, 34, 10)
    piece(r, lambda: stove(r, 72), art('h3_stove'),
          choices=['a4aaba', '848694', '474751', '34343e'])           # the iron, lit to dark
    piece(r, lambda: cupboard(r, 100, w=26), art('h3_cupboard'),
          choices=['d7a175', '815423', '3c2412', 'f4ce80'])           # lit top, doors, dark side, brass
    piece(r, lambda: bed_against_wall(r, 76, 'right'), art('h3_bed_girl'),
          choices=['b6433d', 'ec8476', 'fcfcfc', 'e8e0c0'])           # the girl's patchwork
    piece(r, lambda: bed_against_wall(r, 110, 'right'), art('h3_bed_sailor'),
          choices=['37387b', 'fcfcfc', '9797aa', '785830'])           # the sailor fisher's stripes
    pans = art('h3_pans')
    sprite_rich(r, pans, 102, 24, BACK, choices=['fc9838', 'b6433d', '792727', 'f0bc3c'])
    return finish(r, 'house 3 nes', PAL)
