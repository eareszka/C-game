"""Tune the rock texture against the reference by measuring, not by eye.

Prints, for each (cleft count, cleft width) pair, the same four numbers
tools/ref_stats.py reports for the reference, so the settings can be chosen to
land on them. The targets below are that script's output on reference.aseprite.

    PYTHONPATH=tools python tools/sweep.py 11,12 0.75,0.85

Measuring is not the last word — a run that matches all four numbers can still
read as corduroy, and did — but it settles the questions of how much ink and
how coarse, which are otherwise argued about one render at a time.
"""
import sys
import numpy as np
from PIL import Image
import gen_cliff_tiles as G

TARGET = dict(ink_pct=35.0, ink_h=2.22, brown_h=3.66, ink_v=3.42)


def stats(arr):
    brown = np.all(arr == G.BROWN, axis=2)
    ink = np.all(arr == G.INK, axis=2)
    mass = brown | ink
    core = mass.copy()
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            core &= np.roll(np.roll(mass, dy, 0), dx, 1)
    if core.sum() < 100:
        return None

    def runs(axis):
        ri, rb = [], []
        n = core.shape[0] if axis == 0 else core.shape[1]
        for k in range(n):
            line = core[k] if axis == 0 else core[:, k]
            ln = ink[k] if axis == 0 else ink[:, k]
            idx = np.nonzero(line)[0]
            if idx.size < 8:
                continue
            cur, c = None, 0
            for t in range(idx.min(), idx.max() + 1):
                if not line[t]:
                    cur, c = None, 0
                    continue
                v = 1 if ln[t] else 0
                if v == cur:
                    c += 1
                else:
                    if cur == 1 and c:
                        ri.append(c)
                    if cur == 0 and c:
                        rb.append(c)
                    cur, c = v, 1
        return ri, rb

    hi, hb = runs(0)
    vi, _ = runs(1)
    return dict(ink_pct=100 * ink[core].sum() / core.sum(),
                ink_h=np.mean(hi), brown_h=np.mean(hb), ink_v=np.mean(vi))


def main():
    counts = [int(x) for x in sys.argv[1].split(',')]
    halves = [float(x) for x in sys.argv[2].split(',')]
    print('target      ink%% %.1f  ink_h %.2f  brown_h %.2f  ink_v %.2f' % (
        TARGET['ink_pct'], TARGET['ink_h'], TARGET['brown_h'], TARGET['ink_v']))
    for n in counts:
        for hw in halves:
            G.CLEFT_COUNT, G.CLEFT_HALF = n, hw
            sheet = np.array(Image.open('assets/tileset.png').convert('RGB'))
            G.stamp(sheet, G.ROCK_ROW0, G.rock_cell)
            G.stamp(sheet, G.EDGE_ROW0, G.edge_cell)
            G.preview('sweep_tmp.png', sheet)
            s = stats(np.array(Image.open('sweep_tmp.png').convert('RGB')))
            if s is None:
                print('n=%-3d hw=%-5s no rock in the preview' % (n, hw))
                continue
            print('n=%-3d hw=%-5s ink%% %.1f  ink_h %.2f  brown_h %.2f  ink_v %.2f' % (
                n, hw, s['ink_pct'], s['ink_h'], s['brown_h'], s['ink_v']))


if __name__ == '__main__':
    main()
