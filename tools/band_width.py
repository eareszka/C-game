"""How wide is the band of rock, across a face that runs one way or the other?

Reports the horizontal thickness of the rock mass on rows where the mass is a
vertical strip (an east or west face) and the vertical thickness on columns
where it is a horizontal strip (a south face). The contrast between the two is
what makes a plateau read as having a height rather than an outline, so it is
worth having the reference's numbers rather than guessing at them.
"""
import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB'))
if len(sys.argv) > 2 and sys.argv[2] == 'half':      # a game render, at 2x
    im = im[::2, ::2]
BROWN, INK = (136, 112, 0), (0, 0, 0)
rock = np.all(im == BROWN, axis=2) | np.all(im == INK, axis=2)


def runs_along(mask, axis):
    """Lengths of every unbroken run of rock along the given axis."""
    out = []
    n = mask.shape[1] if axis else mask.shape[0]
    for k in range(n):
        line = mask[:, k] if axis else mask[k, :]
        c = 0
        for v in line:
            if v:
                c += 1
            elif c:
                out.append(c)
                c = 0
        if c:
            out.append(c)
    return np.array(out)


h = runs_along(rock, 0)   # widths measured across a row
v = runs_along(rock, 1)   # depths measured down a column
for name, r in (('horizontal (a side face)', h), ('vertical (a front face)', v)):
    r = r[r >= 3]         # drop the specks of grain
    if r.size == 0:
        print(name, 'nothing')
        continue
    print('%-26s n=%-5d median %2d  mean %5.1f  p25 %2d  p75 %2d' % (
        name, r.size, int(np.median(r)), r.mean(),
        int(np.percentile(r, 25)), int(np.percentile(r, 75))))
