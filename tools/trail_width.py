"""Measure how wide the trail and road actually are, everywhere, at every angle.

The stroke is meant to be three tiles across. It is not: swept along an axis it
is three, but the brush that paints it is a diamond with no idea which way the
path is going, so on a diagonal its support perpendicular to travel collapses to
about 0.71 tiles a side and the stroke comes out two. At a corner two stamps
overlap and it comes out four.

Measuring that correctly is the whole difficulty, because the obvious measure is
wrong. Counting an unbroken run along a row -- what tools/band_width.py does for
the cliff band -- overstates a diagonal stroke by 1/sin(angle): a horizontal cut
through a stroke running at 45 degrees is 1.41 times its real width, so the very
stretches that are too narrow measure as if they were fine. (band_width.py also
drops runs shorter than three outright, which is exactly the case being chased.)

So this measures PERPENDICULAR width, without needing to know the direction:

  distance transform   how far each trail tile is from the nearest tile that is
                       not trail, by 4-connected BFS inward from the boundary.
  ridge                a tile at a local maximum of that distance -- the middle
                       of the stroke. Its distance d is the inscribed radius, so
                       the stroke there is about 2d-1 tiles across, whatever
                       angle it runs at.

  d = 1  ->  two tiles or fewer.  d = 2  ->  three, the target.  d >= 3 -> wider.

Two further numbers, because the histogram alone does not say what it looks like:

  interior fraction    tiles whose four cardinal neighbours are all the same
                       network. This is exactly what nineslice_variant() needs to
                       draw a centre fill, so it maps onto the visible defect
                       rather than onto geometry: a two-wide stretch scores zero
                       and every one of its tiles draws a border cell.
  worst gap            the largest connected clump of stroke carrying no interior
                       tile at all -- the stretch the eye actually catches.

Input is the one-pixel-to-the-tile PNG that SHOT_TRAIL writes:

    SHOT_TRAIL=1 ./shot.exe 387 trail_387.png
    python tools/trail_width.py trail_387.png
"""
import sys
from collections import deque

import numpy as np
from PIL import Image

# Must match the colours tools/shot.cpp writes under SHOT_TRAIL.
NETWORKS = [('trail', (0, 255, 0)), ('road', (0, 128, 255))]
BRIDGE = (0, 255, 255)


def distance_in(mask):
    """4-connected distance from each True tile to the nearest False one.

    Multi-source BFS from the boundary inward. A tile on the edge of the stroke
    is 1, the middle of a three-wide stroke is 2. Off-map counts as outside, so
    a stroke running to the border is not credited with width it does not have.
    """
    h, w = mask.shape
    dist = np.zeros((h, w), dtype=np.int32)
    q = deque()
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if ny < 0 or nx < 0 or ny >= h or nx >= w or not mask[ny, nx]:
                dist[y, x] = 1
                q.append((y, x))
                break
    while q:
        y, x = q.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and dist[ny, nx] == 0:
                dist[ny, nx] = dist[y, x] + 1
                q.append((ny, nx))
    return dist


def ridge_of(dist, mask):
    """Tiles no lower than every 4-neighbour: the middle of the stroke.

    Taking every tile would just count the edges, which are 1 by construction
    whatever the width is.
    """
    d = dist.astype(np.int32)
    pad = np.pad(d, 1, constant_values=0)
    up, dn = pad[:-2, 1:-1], pad[2:, 1:-1]
    lf, rt = pad[1:-1, :-2], pad[1:-1, 2:]
    return mask & (d >= up) & (d >= dn) & (d >= lf) & (d >= rt) & (d > 0)


def largest_clump(mask):
    """Size of the biggest 8-connected component of `mask`, how many there are,
    and where the biggest one is (x0, y0, x1, y1) -- so it can be dumped with
    SHOT_TRAIL's window rather than hunted for."""
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    best, n, where = 0, 0, None
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys.tolist(), xs.tolist()):
        if seen[sy, sx]:
            continue
        n += 1
        size = 0
        x0 = x1 = sx
        y0 = y1 = sy
        q = deque([(sy, sx)])
        seen[sy, sx] = True
        while q:
            y, x = q.popleft()
            size += 1
            x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if (0 <= ny < h and 0 <= nx < w
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        q.append((ny, nx))
        if size > best:
            best, where = size, (x0, y0, x1, y1)
    return best, n, where


# The world wraps on one axis (x for a north or south ocean, y for a west or
# east one), and a track crossing the seam leaves the image at one edge and
# comes back at the other. Measured as it stands, the image edge is "not
# track" and every crossing reads as a narrow stump. --wrap x|y pads the image
# round that axis with its own far side, measures, and crops back, so each tile
# is counted once and a crossing is as wide as it is.
WRAP_PAD = 24


def wrapped(fn, mask, axis):
    """fn(mask) computed on the mask padded round `axis`, cropped back."""
    if axis is None:
        return fn(mask)
    ax = 1 if axis == 'x' else 0
    widths = [(0, 0), (0, 0)]
    widths[ax] = (WRAP_PAD, WRAP_PAD)
    out = fn(np.pad(mask, widths, mode='wrap'))
    return out[:, WRAP_PAD:-WRAP_PAD] if ax == 1 else out[WRAP_PAD:-WRAP_PAD, :]


def report(name, mask, axis=None):
    total = int(mask.sum())
    if not total:
        print('  %-6s no tiles' % name)
        return
    dist = wrapped(distance_in, mask, axis)
    ridge = wrapped(lambda m: ridge_of(distance_in(m), m), mask, axis)

    counts = {}
    for d in dist[ridge].tolist():
        counts[d] = counts.get(d, 0) + 1
    nridge = sum(counts.values())

    # Cardinal neighbours all the same network -- what the nine-slice needs.
    def interior_of(m):
        pad = np.pad(m, 1, constant_values=False)
        return m & pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:]
    interior = wrapped(interior_of, mask, axis)
    gap = mask & ~interior
    worst, nclump, worst_at = largest_clump(gap & (dist == 1) & ridge)
    # And the same for the other direction: the biggest clump of stroke five
    # or more tiles across, which is what a track that swells reads as.
    wide, nwide, wide_at = largest_clump(dist >= 3)

    print('  %-6s %6d tiles, %5d ridge, interior %5.1f%%'
          % (name, total, nridge, 100.0 * int(interior.sum()) / total))
    for d in sorted(counts):
        wide = 2 * d - 1
        tag = ('  <-- TOO NARROW' if d == 1 else
               '  <-- target' if d == 2 else '  <-- wide')
        print('         d=%d (~%d wide) %6d  %5.1f%%%s'
              % (d, wide, counts[d], 100.0 * counts[d] / nridge, tag))
    print('         narrow stretches: %d, largest %d tiles at %s' % (nclump, worst, worst_at))
    print('         wide cores (5+):  %d, largest %d tiles at %s' % (nwide, wide, wide_at))


def main():
    im = np.array(Image.open(sys.argv[1]).convert('RGB'))
    axis = None
    for a in sys.argv[2:]:
        if a.startswith('--wrap='):
            axis = a.split('=', 1)[1]
    print(sys.argv[1] + ('  (wrapping in %s)' % axis if axis else ''))
    for name, rgb in NETWORKS:
        own = np.all(im == np.array(rgb, dtype=np.uint8), axis=2)
        # A bridge is a deck laid square across a gap, three wide by
        # construction, and it belongs to whichever stroke runs through it --
        # count it as part of the mask so a crossing is not read as two stumps.
        bridge = np.all(im == np.array(BRIDGE, dtype=np.uint8), axis=2)
        report(name, own | (bridge & _touches(own)), axis)


def _touches(mask):
    """Bridge tiles adjacent to this network, grown a little along the deck."""
    grown = mask.copy()
    for _ in range(4):
        pad = np.pad(grown, 1, constant_values=False)
        grown = grown | pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    return grown


main()
