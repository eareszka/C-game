"""Which of the ground the cliff draws can the feet not reach?

collide_check.py asks whether the ground closes where the rock is drawn, and
snag_check.py whether walking along the rock catches. This asks the question
between them: given that the ground closes exactly where the ink is, is every
strip of open ground the art draws wide enough for the feet to stand in?

Mother 1's landforms draw ground the feet may not fit. Two flanks stand half a
tile apart with the back line dipping between them; a flank's foot or a
notch's line hangs straight over the teeth of a front. Each leaves a strip of
plain ground inside the wall sprites -- eight art pixels across, or eight to
twelve tall -- that the eye reads as a way through. Feet that need more than
that stop dead in front of it, and no tile-level check can see why, because
the strip lies wholly inside tiles the map calls wall.

So ask it of the collision itself. Take the window's ground one pixel to the
art pixel (SHOT_SOLID), find every position the feet's box fits, and mark the
open ground no such box covers: that is ground the player can see and never
stand on. The box is the feet of include/collision.h, sampled every art
pixel, so it is BOX samples on a side.

    shot.exe <seed> render.png <tile_x> <tile_y> [w h]
    SHOT_SOLID=1 shot.exe <seed> solid.png <tile_x> <tile_y> [w h]
    python tools/feet_check.py render.png solid.png [box ...]

Prints, per box size, how many drawn pixels of open ground are out of reach,
and writes render_feet.png: the render at art scale with that ground in red,
one panel per box size, largest first. Ground closed by something other than
the cliff (grey in solid.png: a tree, a rock, a seam of ore) is left alone.
"""
import os
import sys
import numpy as np
from PIL import Image

BOX = 7      # (HB_X2 - HB_X1) / 2 + 1 of include/collision.h: samples across the feet


def standable(solid, f):
    """Top-left corners of every f x f box of open ground."""
    H, W = solid.shape
    p = np.zeros((H + 1, W + 1), np.int32)
    p[1:, 1:] = np.cumsum(np.cumsum(solid, axis=0), axis=1)
    tot = p[f:, f:] - p[:-f, f:] - p[f:, :-f] + p[:-f, :-f]
    st = np.zeros((H, W), bool)
    st[:H - f + 1, :W - f + 1] = tot == 0
    return st


def coverable(st, f):
    """Every pixel some standable box covers."""
    H, W = st.shape
    p = np.zeros((H + 1, W + 1), np.int32)
    p[1:, 1:] = np.cumsum(np.cumsum(st, axis=0), axis=1)
    y1 = np.arange(H) + 1
    x1 = np.arange(W) + 1
    y0 = np.maximum(0, np.arange(H) - f + 1)
    x0 = np.maximum(0, np.arange(W) - f + 1)
    tot = p[np.ix_(y1, x1)] - p[np.ix_(y0, x1)] - p[np.ix_(y1, x0)] + p[np.ix_(y0, x0)]
    return tot > 0


def main():
    render, solid_png = sys.argv[1], sys.argv[2]
    sizes = [int(a) for a in sys.argv[3:]] or [BOX]
    sol = np.array(Image.open(solid_png).convert('RGB'))
    pic = np.array(Image.open(render).convert('RGB'))
    cliff = np.all(sol == 0, axis=2)               # black: closed by the cliff
    other = ~cliff & ~np.all(sol == 255, axis=2)   # grey: closed by something else
    if pic.shape[0] == 2 * sol.shape[0]:
        pic = pic[::2, ::2]                         # the render is at 2x
    panels = []
    for f in sorted(sizes, reverse=True):
        walk = ~cliff & ~other
        pin = walk & ~(coverable(standable(cliff | other, f), f))
        print('box %d: %d pixels of drawn ground the feet cannot reach' % (f, int(pin.sum())))
        im = pic.copy()
        im[pin] = (255, 40, 40)
        panels.append(im)
    sep = np.full((pic.shape[0], 4, 3), 255, np.uint8)
    row = panels[0]
    for im in panels[1:]:
        row = np.concatenate([row, sep, im], axis=1)
    out = os.path.splitext(render)[0] + '_feet.png'
    Image.fromarray(row).resize((row.shape[1] * 3, row.shape[0] * 3), Image.NEAREST).save(out)
    print('wrote', out)


if __name__ == '__main__':
    main()
