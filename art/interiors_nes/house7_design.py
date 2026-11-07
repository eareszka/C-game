"""Room 7, upstairs in the tall red-brick house (room 6 below), NES style: a
loft for the woodcutter's tools and the courier's parcels. Same brick and
boards as downstairs, one window; PixelLab's workbench with a saw and hammer
under it, crossed axes on the wall, a shelf of parcels tied with string, and the stairs down in a doorway in the back wall (every
way in and out is on a wall, the user's rule) -- the downstairs doorway's own
drawing: one staircase, the same up and down (the user's). No door: the
stairs are the way out. Nobody lives up here, so no
route to keep clear but the player's to the stairs.

    python tools/interior_nes.py 7 art/interiors_nes/house7_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': '7c0a1b', 'Z': '5d1e1f', 'm': 'bcbeca', 'R': '375a94'}

# down: feet at the doorway, before it -> room 6, before its stairs
_ME, _THEM = stairs_cols('stairs_down', STAIRS_LEFT), stairs_cols('stairs_up', STAIRS_RIGHT)   # the slots as the user drew them
STAIRS = [stairs_trigger(6, _ME[0], _THEM[0], w=_ME[1], arrive_w=_THEM[1])]   # the slot in the side wall, as Mother 1's (the user's reference)


def design():
    r = new_room(windows=((80, 15),), door=False)
    rug(r, 100, 114, 40, 10)
    piece(r, lambda: counter(r, 80, BACK + 8, w=40, high=13), art('h7_bench'),
          choices=['d7a175', 'b2966a', '815423', 'a4aaba'])            # top, its shade, the front's dark, the tools' iron
    # the staircase: the user's hand-drawn stairs_down.png (Aseprite) over the coded one
    stairs_from_sprite(r, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stairs_down.png'), STAIRS_LEFT)
    # on the back wall, behind everyone
    pb = art('h7_parcels')
    sprite_rich(r, pb, 158, 26, BACK, cut=lambda x, y: y > 20,
                choices=['d7a175', 'b2966a', '815423', '37387b'])      # paper, its fold, the shelf, a stamp
    sprite_rich(r, art('h7_axes'), 102, 22, BACK,
                choices=['815423', 'bcbeca', '848694', 'b6433d'])      # plaque, blades, their edge, handles
    sprite(r, art('s_curtains'), 80, 14, {'K': '000000', 'm': 'e8e0c0', 'a': 'a4aaba'}, BACK,
           cut=lambda x, y: 8 <= x <= 15 and y >= 8)
    d = finish(r, 'house 7 nes', PAL)
    d['exit'] = []                       # no door up here
    return d
