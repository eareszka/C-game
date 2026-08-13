"""How far does the top of a face wander, and how tall are the clefts in it?

Two numbers the other tools do not reach, both measured off mother1.png so
there is something to aim at rather than an opinion.

    band top edge, peak to peak over a window of
        8 px      5        (reference median)
       16 px      8
       32 px     15
       64 px     24        — the edge wanders its own depth over 64 px

    ink vertical run (cleft height)   median 3, p90 7
    ink horizontal run (vein width)   median 2, p90 4
    brown horizontal run (rib width)  median 4, p90 7
    vein-to-vein spacing              median 7

The first is what "the flanks look too flat and uniform" turns out to mean: not
the shape of the landform, which is a tile-scale question, but the roughness of
the drawn silhouette, which is a pixel-scale one.

    python tools/edge_rough.py <render.png> [half]

`half` for a 2x game render.
"""
import sys
import numpy as np
from PIL import Image

BROWN, INK = (136, 112, 0), (0, 0, 0)


def runs(mask, axis):
    """Lengths of every run of set pixels along the given axis."""
    m = mask if axis == 0 else mask.T
    out = []
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
            out.append(j - i)
            i = j
    return np.array(out) if out else np.zeros(0)


def main():
    im = np.array(Image.open(sys.argv[1]).convert('RGB'))
    if len(sys.argv) > 2 and sys.argv[2] == 'half':
        im = im[::2, ::2]
    brown = np.all(im == BROWN, axis=2)
    ink = np.all(im == INK, axis=2)

    # The mass, and only where it is deep enough to have a top edge worth
    # measuring — a flank is a few pixels across and its "top" is a corner.
    mass = brown | ink
    deep = mass.copy()
    for d in range(1, 12):
        deep &= np.roll(mass, d, 0)
    cols = np.nonzero(deep.any(axis=0))[0]

    top = np.full(im.shape[1], -1)
    for x in cols:
        idx = np.nonzero(deep[:, x])[0]
        if idx.size:
            # the top of the mass this deep column belongs to
            y = idx[0]
            while y > 0 and mass[y - 1, x]:
                y -= 1
            top[x] = y

    print('band top edge, peak to peak over a window   (reference median)')
    for w in (8, 16, 32, 64):
        p2p = []
        run = []
        for x in range(im.shape[1]):
            if top[x] < 0:
                if len(run) >= w:
                    a = np.array(run)
                    for i in range(a.size - w):
                        p2p.append(a[i:i + w].ptp())
                run = []
            else:
                if run and abs(top[x] - run[-1]) > 24:
                    run = []
                run.append(top[x])
        if len(run) >= w:
            a = np.array(run)
            for i in range(a.size - w):
                p2p.append(a[i:i + w].ptp())
        ref = {8: 5, 16: 8, 32: 15, 64: 24}[w]
        if p2p:
            g = np.array(p2p, dtype=float)
            print('  %3d px   median %5.1f   p75 %5.1f   (reference %2d)'
                  % (w, np.median(g), np.percentile(g, 75), ref))
        else:
            print('  %3d px   nothing long enough to measure' % w)

    # The texture inside the mass. Eroded, so the rim and the ragged silhouette
    # do not count as veins.
    core = mass.copy()
    for dy in (-2, -1, 1, 2):
        for dx in (-2, -1, 1, 2):
            core &= np.roll(np.roll(mass, dy, 0), dx, 1)
    ci, cb = ink & core, brown & core
    print('\ntexture inside the mass                      (reference median / p90)')
    for name, m, axis, ref in (('ink vertical run (cleft height)', ci, 1, (3, 7)),
                               ('ink horizontal run (vein width)', ci, 0, (2, 4)),
                               ('brown horizontal run (rib width)', cb, 0, (4, 7))):
        r = runs(m, axis)
        if r.size:
            print('  %-34s median %3d   p90 %3d   (reference %d / %d)'
                  % (name, int(np.median(r)), int(np.percentile(r, 90)), ref[0], ref[1]))
    if ci.sum():
        print('  %-34s %4.1f%%   (reference 43.8%%)'
              % ('ink share of the mass', 100.0 * ci.sum() / core.sum()))


if __name__ == '__main__':
    main()
