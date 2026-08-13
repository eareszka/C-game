"""Does the ground close where the rock is drawn, or somewhere else?

The two are worked out differently and can drift apart without anything looking
wrong in either on its own: the cliff is drawn from a marching-squares contour,
which runs through the middle of a cell, while the ground is closed a whole tile
at a time. Half a tile of disagreement is invisible in a screenshot and obvious
under the feet — you stand on the top of the rock, or you stop in the grass
below its foot.

So measure it, from the side the player is on. Walk in along every line of the
window from each of the four edges in turn and note two things: where the ground
first stops you, and where the rock first appears. Positive means you were
stopped short of the cliff with grass between — an invisible wall. Negative
means you walked into the rock before anything stopped you. A tile is sixteen
pixels, so anything past eight is a whole tile out.

    shot.exe <seed> render.png                (a window, at 2x)
    SHOT_SOLID=1 shot.exe <seed> solid.png    (the same window, one to the art pixel)
    python tools/collide_check.py render.png solid.png

A map one pixel to the tile works too, and is what this took before the ground
stopped being closed a tile at a time:

    SHOT_WALK=1 shot.exe <seed> walk.png      (the world, one pixel to the tile)
    python tools/collide_check.py render.png walk.png <tile_x> <tile_y>

tile_x and tile_y are the window's origin, which shot.exe prints. Which of the
two is in hand is told from its size, so the old maps still measure and the two
can be compared against one render.
"""
import sys
import numpy as np
from PIL import Image

BROWN, INK = (136, 112, 0), (0, 0, 0)
CELL = 16


def grow(m, r):
    o = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def label(mask):
    """Connected components, eight-way, numbered from one. Written out rather
    than imported so the tools need nothing but numpy and pillow, as the rest
    of them do."""
    out = np.zeros(mask.shape, dtype=np.int32)
    n = 0
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        if out[y0, x0]:
            continue
        n += 1
        stack = [(y0, x0)]
        out[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                       and mask[ny, nx] and not out[ny, nx]:
                        out[ny, nx] = n
                        stack.append((ny, nx))
    return out


def main():
    im = np.array(Image.open(sys.argv[1]).convert('RGB'))[::2, ::2]
    lvl = np.array(Image.open(sys.argv[2]).convert('L'))
    walk = lvl > 127
    # Grey, where SHOT_SOLID writes it, is ground closed by something that is
    # not the cliff — a boulder, a tree. Those are whole-tile colliders and are
    # not what is being measured, so a line stopped by one is not measured.
    other = (lvl >= 64) & (lvl < 192)

    brown = np.all(im == BROWN, axis=2)
    ink = np.all(im == INK, axis=2)
    # The cliff is the rock and the line both. At the back of a height there is
    # no rock at all — the beaded outline is the whole of what marks the drop,
    # and it is what the ground should close on, so it has to count.
    #
    # Two other things are drawn in the same brown and the same black and are
    # not the cliff: a tuft of grass, and the grains of scree spilled a tile or
    # two below the foot of a face. Neither closes anything — you walk among the
    # scree, which is the point of it — and left in, the scree in particular
    # ruins the reading from the south, because the first brown pixel coming up
    # to a face is then a grain lying two tiles short of it. Both are told from
    # the cliff by size: a landform's worth of rock and line is one lump of
    # thousands of pixels, a tuft is five and a grain is one or two.
    #
    # Size alone is not quite the test, though, because the cliff is not one
    # lump: a cleft reaching daylight cuts the tip off a tooth, and the band's
    # foot is a row of those. Those specks are rock and are drawn against the
    # rock. So take the big pieces, and then take the small ones lying within a
    # pixel or two of a big one. A grain of scree lies a tile or two out from
    # the foot and a tuft grows in open country, so neither is reached.
    lab = label(brown | ink)
    sizes = np.bincount(lab.ravel())
    big = sizes >= 24
    big[0] = False
    keep = big.copy()
    keep[np.unique(lab[grow(big[lab], 2)])] = True
    keep[0] = False
    rock = keep[lab]
    h, w = rock.shape
    if walk.shape == rock.shape:
        solid = ~walk                       # one pixel to the art pixel already
    else:
        # One pixel to the tile, blown up to the picture's scale. Those maps
        # mark nothing but solid and not solid, so nothing is set aside.
        ox, oy = int(sys.argv[3]), int(sys.argv[4])
        solid = ~walk[oy:oy + h // CELL, ox:ox + w // CELL]
        solid = np.repeat(np.repeat(solid, CELL, 0), CELL, 1)[:h, :w]
        other = np.zeros_like(solid)

    # Walk in from each side and ask two questions of every line: where does the
    # ground stop you, and where does the rock start. The gap between them is
    # what the player feels.
    #
    # Positive means you are stopped short of the cliff, with grass between you
    # and it — an invisible wall. Negative means you walk into the rock before
    # anything stops you. Measured from outside, because that is the side the
    # player is on: coming up to a cliff, not standing on top of one.
    def approach(name, lines):
        gaps = []
        for r, s, o in lines:
            if s[0]:
                continue    # the line starts inside a cliff; there is no walking up to it
            ri = np.nonzero(r)[0]
            si = np.nonzero(s)[0]
            if ri.size == 0 or si.size == 0:
                continue
            if o[si[0]]:
                continue    # stopped by a boulder or a tree, not by the cliff
            gap = ri[0] - si[0]
            if abs(gap) > 2 * CELL:      # different cliffs; nothing to compare
                continue
            gaps.append(gap)
        if not gaps:
            print('%-26s nothing to compare' % name)
            return
        g = np.array(gaps, dtype=float)
        print('%-26s n=%-5d mean %+5.1f px  median %+4.0f  within a pixel %3.0f%%'
              % (name, g.size, g.mean(), np.median(g), 100.0 * (abs(g) <= 1).mean()))

    approach('coming up from the south', [(rock[::-1, k], solid[::-1, k], other[::-1, k])
                                          for k in range(rock.shape[1])])
    approach('coming down from the north', [(rock[:, k], solid[:, k], other[:, k])
                                            for k in range(rock.shape[1])])
    approach('coming in from the west', [(rock[k, :], solid[k, :], other[k, :])
                                         for k in range(rock.shape[0])])
    approach('coming in from the east', [(rock[k, ::-1], solid[k, ::-1], other[k, ::-1])
                                         for k in range(rock.shape[0])])


if __name__ == '__main__':
    main()
