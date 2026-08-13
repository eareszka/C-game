"""How thick is the band where it runs down a side, against where it faces you?

band_width.py reports every run in the picture and so mixes the two together;
its median is the average of a 30px front and a 6px flank and describes
neither. The contrast between them is the thing being drawn — a plateau reads
as having a height because the drop you look into is deep and the one that
runs away from you is a line — so it wants measuring on its own.

Each pixel of rock is asked how long its horizontal run is and how long its
vertical one. A pixel in a flank has a short horizontal run inside a long
vertical one, and the horizontal run is that flank's thickness; a pixel in a
front face is the same the other way up. Pixels where the two are comparable
are corners and are not counted.

Usage: python tools/flank_width.py <png> [half]
"""
import sys
import numpy as np
from PIL import Image

BROWN, INK = (136, 112, 0), (0, 0, 0)


def runs(mask, axis):
    """For every set pixel, the length of the run of set pixels it lies in."""
    m = mask if axis == 0 else mask.T
    out = np.zeros(m.shape, dtype=np.int32)
    for k in range(m.shape[0]):
        line = m[k]
        i = 0
        while i < line.size:
            if not line[i]:
                i += 1
                continue
            j = i
            while j < line.size and line[j]:
                j += 1
            out[k, i:j] = j - i
            i = j
    return out if axis == 0 else out.T


def grow(m, r):
    o = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o |= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


def main():
    im = np.array(Image.open(sys.argv[1]).convert('RGB'))
    if len(sys.argv) > 2 and sys.argv[2] == 'half':
        im = im[::2, ::2]
    # Ink counts as rock only where it belongs to rock — a tuft of grass is
    # drawn in black too, and there are thousands of them in open country.
    brown = np.all(im == BROWN, axis=2)
    mass = brown | (np.all(im == INK, axis=2) & grow(brown, 2))

    h = runs(mass, 0)
    v = runs(mass, 1)
    # Grains of scree are ink-and-brown too; a run of one or two pixels is one
    # of those rather than a piece of a face.
    flank = mass & (v >= 2 * h) & (h >= 2)
    front = mass & (h >= 2 * v) & (v >= 2)
    for name, sel, thick in (('flank (runs N-S)', flank, h), ('front (faces you)', front, v)):
        t = thick[sel]
        if t.size == 0:
            print('%-18s nothing' % name)
            continue
        print('%-18s n=%-6d median %2d  mean %5.1f  p25 %2d  p75 %2d' % (
            name, t.size, int(np.median(t)), t.mean(),
            int(np.percentile(t, 25)), int(np.percentile(t, 75))))


if __name__ == '__main__':
    main()
