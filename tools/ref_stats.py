import sys
import numpy as np
from PIL import Image

im = np.array(Image.open(sys.argv[1]).convert('RGB'))
BROWN = (136, 112, 0)
INK = (0, 0, 0)
brown = np.all(im == BROWN, axis=2)
ink = np.all(im == INK, axis=2)
mass = brown | ink


def erode(m, r):
    o = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            o &= np.roll(np.roll(m, dy, 0), dx, 1)
    return o


core = erode(mass, 3)
print('mass px', mass.sum(), 'core px', core.sum())
print('inside core: brown %.1f%% ink %.1f%%' % (
    100 * brown[core].sum() / core.sum(), 100 * ink[core].sum() / core.sum()))

runs_i, runs_b = [], []
for y in range(im.shape[0]):
    xs = np.nonzero(core[y])[0]
    if xs.size < 8:
        continue
    cur, n = None, 0
    for x in range(xs.min(), xs.max() + 1):
        if not core[y, x]:
            cur, n = None, 0
            continue
        v = 1 if ink[y, x] else 0
        if v == cur:
            n += 1
        else:
            if cur == 1 and n:
                runs_i.append(n)
            if cur == 0 and n:
                runs_b.append(n)
            cur, n = v, 1
print('ink   run mean %.2f median %d p90 %d' % (
    np.mean(runs_i), np.median(runs_i), np.percentile(runs_i, 90)))
print('brown run mean %.2f median %d p90 %d' % (
    np.mean(runs_b), np.median(runs_b), np.percentile(runs_b, 90)))

# vertical runs say how tall the clefts are
vi = []
for x in range(im.shape[1]):
    ys = np.nonzero(core[:, x])[0]
    if ys.size < 8:
        continue
    cur, n = None, 0
    for y in range(ys.min(), ys.max() + 1):
        if not core[y, x]:
            cur, n = None, 0
            continue
        v = 1 if ink[y, x] else 0
        if v == cur:
            n += 1
        else:
            if cur == 1 and n:
                vi.append(n)
            cur, n = v, 1
print('ink   vertical run mean %.2f median %d p90 %d' % (
    np.mean(vi), np.median(vi), np.percentile(vi, 90)))
