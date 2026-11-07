"""Room 2, the fisher's ranch house (one storey), NES style: the room's own
tan brick and boards, PixelLab's green-blanket bed over the old one (the
same place and size), and the fisher's things on the walls, in nobody's way:
a trophy fish on a plaque, a net hung from two pegs, a pole leaning in the
back corner, and a rug by the bed. Nothing new stands on the floor, so the
fisher's routes are as before.

    python tools/interior_nes.py 2 art/interiors_nes/house2_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': 'c18a39', 'Z': '815423', 'm': 'fce4a0', 'R': '2c6c44'}


def design():
    r = new_room()
    rug(r, 128, 100, 30, 10, border=False)
    piece(r, lambda: bed_fn(r), art('h2_bed'), choices=['2c6c44', '4fa667', 'fcfcfc', 'fce4a0'])
    # on the back wall, behind everyone
    fish, net, rod = art('h2_fish'), art('h2_net'), art('h2_rod2')
    sprite_rich(r, fish, 108, 20, BACK, choices=['815423', '4fa667', '474751', 'd7a175'])   # plaque, fish, its dark, lit edge
    sprite_rich(r, net, 132, 17, BACK, choices=['b29e5c', '34343e', 'b70000', '848694'])     # rope, mesh, float, pegs
    bb = rod.getbbox()
    sprite_rich(r, rod, 75, BACK - (bb[3] - bb[1]), BACK, choices=['8d6b4f', 'a4aaba', 'b70000'])                    # pole, reel, bobber
    return finish(r, 'house 2 nes', PAL)


def bed_fn(r):
    bed(r, 168, BACK + 8, flip=True)
