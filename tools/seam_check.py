"""Check that the band shows no seam where two tiles meet.

The whole scheme rests on neighbouring cells being two windows onto one
continuous field, so the test is direct: measure how often the colour changes
across a column boundary that falls on a tile edge, and compare it with the
boundaries that do not. If the cells were stamps butted together, the tile
edges would change far more often than the rest, and a grid would be visible.

Pass `half` for a game render, which is drawn at two screen pixels to the
picture's one. It matters more than it looks: at 2x every other row boundary
falls inside a doubled pixel and can never change, which halves the figure for
"elsewhere" while leaving the tile edges — always even — alone, and doubles the
ratio out of nothing.

Usage: python tools/seam_check.py <render.png> [tile px] [half]
"""
import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(np.int16)
step = int(sys.argv[2]) if len(sys.argv) > 2 else 32
if 'half' in sys.argv[3:]:
    im = im[::2, ::2]
    step //= 2

BROWN = np.array([136, 112, 0])
INK = np.array([0, 0, 0])
brown = np.all(im == BROWN, axis=2)
ink = np.all(im == INK, axis=2)


def grow(m, r):
    o = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


# Ink counts as rock only where it belongs to rock. Black is also what a tuft of
# grass is drawn in, and a screen of open country carries thousands of them: they
# were being counted as cliff, which put a scatter of "rock" over every line of
# the picture and quietly halved the figure for "elsewhere". Same rule as
# join_check.py — brown, and the ink within two pixels of it.
rock = brown | (ink & grow(brown, 2))

# Normalised by how much rock the boundaries touch at all: away from the cliffs
# there is nothing for a seam to show in, and counting flat grass as agreement
# would bury the signal.
#
# Pooled across the group rather than averaged line by line. A per-line mean
# weights a line crossing two pixels of rock as heavily as one crossing four
# hundred, and a two-pixel line reads 0.0 or 1.0 and nothing between: on a quiet
# seed that noise was most of the answer, and it moved the figure by half again
# either way. Total changes over total chances says what the eye would see.
for name, along in (('vertical (columns)', 1), ('horizontal (rows)', 0)):
    if along:
        change, live = rock[:, 1:] != rock[:, :-1], rock[:, 1:] | rock[:, :-1]
        idx = np.arange(1, im.shape[1])
    else:
        change, live = rock[1:, :] != rock[:-1, :], rock[1:, :] | rock[:-1, :]
        idx = np.arange(1, im.shape[0])
    per = change.sum(axis=1 - along).astype(float)
    liv = live.sum(axis=1 - along).astype(float)
    on = (idx % step == 0)
    rate_on = per[on].sum() / max(liv[on].sum(), 1.0)
    rate_off = per[~on].sum() / max(liv[~on].sum(), 1.0)
    print('%-20s tile edges %.4f   elsewhere %.4f   ratio %.2f' % (
        name, rate_on, rate_off, rate_on / max(rate_off, 1e-9)))

    # The same figure at each position within the tile, which is the control
    # the ratio above badly needs.
    #
    # The rock has a rhythm of its own — the clefts run top to bottom on a
    # spacing of their own choosing — so the rate is not flat across the tile
    # even when nothing is wrong, and comparing one position against the average
    # of the other fifteen reads that rhythm as a seam. It has said 1.15 on a
    # picture whose tile rows were quieter than three of the four positions
    # sampled. What the eye is asking is whether position zero stands out from
    # its neighbours, so print them and look.
    by = []
    for ph in range(0, step, max(1, step // 4)):
        sel = (idx % step == ph)
        by.append('%2d:%.3f' % (ph, per[sel].sum() / max(liv[sel].sum(), 1.0)))
    print('%-20s by position in the tile (0 is the seam):  %s' % ('', '  '.join(by)))
