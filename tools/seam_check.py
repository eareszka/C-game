"""Check that the band shows no seam where two tiles meet.

The whole scheme rests on neighbouring cells being two windows onto one
continuous field, so the test is direct: measure how often the colour changes
across a column boundary that falls on a tile edge, and compare it with the
boundaries that do not. If the cells were stamps butted together, the tile
edges would change far more often than the rest, and a grid would be visible.

Usage: python tools/seam_check.py <render.png> <tile px>
"""
import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(np.int16)
step = int(sys.argv[2]) if len(sys.argv) > 2 else 32

BROWN = np.array([136, 112, 0])
INK = np.array([0, 0, 0])
rock = (np.all(im == BROWN, axis=2) | np.all(im == INK, axis=2))

# Normalised per line by how much rock that line touches at all: elsewhere
# there is nothing for a seam to show in, and counting flat grass as agreement
# would bury the signal.
for name, along in (('vertical (columns)', 1), ('horizontal (rows)', 0)):
    if along:
        change, live = rock[:, 1:] != rock[:, :-1], rock[:, 1:] | rock[:, :-1]
        idx = np.arange(1, im.shape[1])
    else:
        change, live = rock[1:, :] != rock[:-1, :], rock[1:, :] | rock[:-1, :]
        idx = np.arange(1, im.shape[0])
    per = change.sum(axis=1 - along).astype(float)
    liv = live.sum(axis=1 - along).astype(float)
    ok = liv > 0
    rate = np.zeros_like(per)
    rate[ok] = per[ok] / liv[ok]
    on = (idx % step == 0) & ok
    off = (idx % step != 0) & ok
    print('%-20s tile edges %.4f   elsewhere %.4f   ratio %.2f' % (
        name, rate[on].mean(), rate[off].mean(),
        rate[on].mean() / max(rate[off].mean(), 1e-9)))
