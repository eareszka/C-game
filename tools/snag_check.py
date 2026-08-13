"""How often does walking along a cliff stop dead?

collide_check.py asks whether the ground closes where the rock is drawn. This
asks the other question, the one you feel rather than see: once you are up
against the rock, can you walk along it?

A cliff's silhouette is drawn toothed — a column of brown standing two or three
pixels proud of the ones beside it, with a wedge of black driven down between
them, which is what makes a face read as rock rather than as a torn edge. Every
one of those is something for the feet to catch on, and the notch between two of
them is a slot to drop into and be held by. None of it shows up as a
disagreement between the art and the ground, because there is none: the ground
is exactly the art, teeth and all.

So walk it. Take every standable position that is pressed up against the cliff,
step one pixel along the face, and count how often that step is refused.

    SHOT_SOLID=1 shot.exe <seed> solid.png <tile_x> <tile_y>
    python tools/snag_check.py solid.png

`--noslip` reports the same without the small sideways slide the collider is
allowed (HB_SLIP in include/collision.h), which is what the numbers were before
there was one.
"""
import sys
import numpy as np
from PIL import Image

BOX = 8    # the feet, in art pixels: sixteen world pixels, eight of the art's
SLIP = 1   # HB_SLIP, likewise: two world pixels


def standable(solid):
    """Where the feet fit — nothing solid anywhere around the box, which is what
    can_occupy tests."""
    f = ~solid
    ok = np.ones((f.shape[0] - BOX, f.shape[1] - BOX), dtype=bool)
    for k in range(BOX + 1):
        ok &= f[k:f.shape[0] - BOX + k, :-BOX]      # west edge
        ok &= f[k:f.shape[0] - BOX + k, BOX:]       # east
        ok &= f[:-BOX, k:f.shape[1] - BOX + k]      # north
        ok &= f[BOX:, k:f.shape[1] - BOX + k]       # south
    return ok


def shift(m, dy, dx):
    """m translated, with everything moving in from outside taken as blocked."""
    o = np.zeros_like(m)
    h, w = m.shape
    ys = slice(max(0, -dy), h - max(0, dy))
    xs = slice(max(0, -dx), w - max(0, dx))
    yd = slice(max(0, dy), h - max(0, -dy))
    xd = slice(max(0, dx), w - max(0, -dx))
    o[yd, xd] = m[ys, xs]
    return o


def main():
    slip = '--noslip' not in sys.argv
    lvl = np.array(Image.open(sys.argv[1]).convert('L'))
    ok = standable(lvl < 192)

    # Along each face in turn: pressed against the rock on one side, walking at
    # right angles to it. Pressed means the step into the rock is refused —
    # anywhere else you are not walking along anything.
    ways = (('north-facing rock, walking east', (-1, 0), (0, 1)),
            ('north-facing rock, walking west', (-1, 0), (0, -1)),
            ('south-facing rock, walking east', (1, 0), (0, 1)),
            ('west-facing rock, walking south', (0, -1), (1, 0)),
            ('east-facing rock, walking south', (0, 1), (1, 0)))
    for name, into, along in ways:
        pressed = ok & ~shift(ok, -into[0], -into[1])
        free = shift(ok, -along[0], -along[1])
        if slip:
            # The collider may stand a little to either side of where it was
            # going to, if that is what gets it past. Across the way it is
            # travelling, so along the face's own normal.
            for s in range(1, SLIP + 1):
                for d in (s, -s):
                    free |= shift(ok, -(along[0] + into[0] * d),
                                      -(along[1] + into[1] * d))
        n = int(pressed.sum())
        if not n:
            print('%-34s nothing pressed against' % name)
            continue
        stuck = int((pressed & ~free).sum())
        print('%-34s n=%-6d refused %5.1f%%' % (name, n, 100.0 * stuck / n))


if __name__ == '__main__':
    main()
