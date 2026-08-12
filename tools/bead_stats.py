"""How broken is the outline the reference draws along a highland's edge?

Isolates the thin ink line — ink that is not part of the rock mass and not a
tree — and reports how long its unbroken runs are and how long the gaps
between them are. The answer decides whether the generated line should be
beaded at all, or drawn solid.
"""
import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB'))
BROWN, INK, TREE = (136, 112, 0), (0, 0, 0), (0, 168, 0)
brown = np.all(im == BROWN, axis=2)
ink = np.all(im == INK, axis=2)
tree = np.all(im == TREE, axis=2)


def near(mask, r):
    out = np.zeros_like(mask)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


line = ink & ~near(brown, 2) & ~near(tree, 2)
print('outline pixels:', line.sum())

# Walk it column by column: the line is mostly horizontal, so a column either
# carries a piece of it or is a gap in it.
cols = line.any(axis=0)
runs, gaps, cur, kind = [], [], 0, None
for c in range(im.shape[1]):
    k = bool(cols[c])
    if k == kind:
        cur += 1
    else:
        if kind is True:
            runs.append(cur)
        if kind is False and cur:
            gaps.append(cur)
        kind, cur = k, 1
if kind is True:
    runs.append(cur)

print('columns carrying the line: %d of %d (%.0f%%)' % (
    cols.sum(), len(cols), 100 * cols.sum() / len(cols)))
if gaps:
    print('gaps: %d, mean %.1f px, max %d' % (len(gaps), np.mean(gaps), max(gaps)))
else:
    print('gaps: none')
if runs:
    print('runs: %d, mean %.1f px, max %d' % (len(runs), np.mean(runs), max(runs)))

# And how thick it is where it exists.
thick = [line[:, c].sum() for c in range(im.shape[1]) if cols[c]]
print('ink per column where present: mean %.2f, max %d' % (np.mean(thick), max(thick)))
