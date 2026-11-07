"""Room 6, the tall red-brick house downstairs, NES style -- the woodcutter's
and the courier's: the room's own brick, boards and rug; PixelLab's log bed
with a plaid wool blanket and a worn leather sofa with a folded blanket (the
courier sleeps on it) over the old ones (the same places and sizes); the
house has two storeys, so a staircase goes up into the back wall between
them, to room 7. The stairs are wall, drawn behind everyone, and nothing new
stands on the floor, so the two residents' routes are as before.

    python tools/interior_nes.py 6 art/interiors_nes/house6_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': '7c0a1b', 'Z': '5d1e1f', 'm': 'bcbeca', 'R': '375a94', 'C': 'b6433d', 'c': 'ec8476'}

# up: feet at the stairs' foot, before the opening -> room 7, below its stairwell
_ME, _THEM = stairs_cols('stairs_up', STAIRS_RIGHT), stairs_cols('stairs_down', STAIRS_LEFT)   # the slots as the user drew them
STAIRS = [stairs_trigger(7, _ME[0], _THEM[0], w=_ME[1], arrive_w=_THEM[1])]   # the slot in the side wall, as Mother 1's (the user's reference)


def design():
    r = new_room()
    rug(r, 66, 116, 30, 8)                                   # the old room's, where it was
    piece(r, lambda: bed(r, 168, BACK + 8, flip=True), art('h6_bed'),
          choices=['b6433d', '792727', 'fcfcfc', 'b2966a'])            # plaid, its dark check, pillow, the logs
    piece(r, lambda: sofa(r, 80, BACK + 8), art('h6_sofa'),
          choices=['815423', '583518', 'd89830', 'c18a39'])            # leather, its shade, the blanket, the lit edge
    # the staircase: the user's hand-drawn stairs_up.png (Aseprite) over the coded one
    stairs_from_sprite(r, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stairs_up.png'), STAIRS_RIGHT)
    for wx in (80, 160):                                     # curtains, as in the house next door
        sprite(r, art('s_curtains'), wx, 14, {'K': '000000', 'm': 'e8e0c0', 'a': 'a4aaba'}, BACK,
               cut=lambda x, y: 8 <= x <= 15 and y >= 8)
    return finish(r, 'house 6 nes', PAL)
