"""Room 5, the brown-brick house's sitting room, NES style: the room's own
brick, boards and rug, PixelLab's green sofa and a dark bookcase over the
old ones (the same places and sizes), and -- the house's chimney is at its
left end -- a brick fireplace set into the back wall there, a fire in it,
where the left window was. It is drawn against the wall, behind everyone,
and nothing new stands on the floor, so every route is as before.

The fire moves on the world's ambient beat (core.h, 3 frames a second each):
PixelLab's flame, the same mirrored in its opening, and the first drawn a row
taller -- the logs and the brick stay put.

    python tools/interior_nes.py 5 art/interiors_nes/house5_design.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tools'))
from interior_nes import *

PAL = {'W': '815423', 'Z': '583518', 'm': 'd89830', 'R': 'b6433d', 'C': '2c6c44', 'c': '4fa667'}


FRAMES = 3
FLAME = (8, 13, 23, 23)          # the opening's flame in the drawing, x0 y0 x1 y1; the logs below


def fire_frame(im, frame):
    """Frame 0 PixelLab's fire; 1 its flame mirrored (the opening is
    symmetric about the drawing's middle); 2 the flame a row taller."""
    if frame == 0:
        return im
    out = im.copy()
    src, dst = im.load(), out.load()
    x0, y0, x1, y1 = FLAME
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if frame == 1:
                dst[x, y] = src[x0 + x1 - x, y]
            else:                                        # each row from the one below it
                dst[x, y] = src[x, min(y1, y + 1)]
    return out


def design(frame=0):
    r = new_room(windows=((160, 15),))
    rug(r, 92, 108, 44, 12)                                  # the old room's, where it was
    piece(r, lambda: sofa(r, 104, BACK + 8), art('h5_sofa'),
          choices=['4fa667', '2c6c44', '235436', 'd0c078'])           # lit, green, shadow, piping
    piece(r, lambda: bookcase(r, 170, 118), art('h5_case'),
          choices=['3c2412', '785830', '29633e', 'd89830'])           # dark wood, lit edge, green and yellow books
    fire = fire_frame(art('h5_fire'), frame)
    bb = fire.getbbox()
    sprite_rich(r, fire, 74, BACK - (bb[3] - bb[1]), BACK,
                choices=['8d6b4f', '531b1c', 'fc9838', 'fce4a0'])     # brick, the dark inside, fire, flame
    return finish(r, 'house 5 nes', PAL)
