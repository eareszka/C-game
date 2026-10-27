"""Two of the overworld's trees, redrawn to the props' standard, 16x32 -- the crown's cell
over the trunk's, the trunk cell the one the tree stands on.

    python art/structures/trees/trees_design.py            # both
    python art/structures/trees/trees_design.py palm       # one

  dead_tree  the wasteland's (sheet col 20; written into the sheet's cells 20,0-1)
  palm       the oasis's (entrances/palm.png; entrances/oasis_design.py stands it by the pool)

The user, 2026-10-27: the older pieces brought up to the new props. The round and tall trees
and the conifers were redrawn too and put back: in the world they read as rows of poles, not
woods (trees_fit_old_vs_new). PixelLab drafts under pixellab-out/old-trees-*/ gave the shapes.
The trees' rule (OVERWORLD_STYLE.md): one black line round the silhouette and between parts,
three tones and black, the light sparse and high on the left, the dark low and on the right;
no cell over four colours (keep4).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'props', 'forest'))
sys.path.insert(0, os.path.join(HERE, '..', 'props', 'snow'))
from forest_design import blank, outline, stroke, write
from snow_design import piece, keep4

FOLIAGE = ('05c43a', '058f3a', '235436')
BARK = ('605028', '463422', '2d230c')
SNOW = 'fcfcfc'
W, H = 16, 32


def dead():
    g = blank(W, H)
    pick = lambda x, y, t, side: 'l' if side < -0.05 else 'd' if side > 0.5 else 'm'
    stroke(g, [(8, 30, 3.6), (8, 22, 3.0), (7.5, 14, 2.6), (8, 9, 2.0)], 'm', pick)
    for pts in ([(7.8, 17, 2.0), (4.5, 12, 1.5), (3, 6, 1.0)],
                [(8, 13, 1.8), (11.5, 8, 1.3), (12.5, 3, 1.0)],
                [(8, 9, 1.4), (7, 4, 1.0), (7.5, 2, 0.9)],
                [(4.5, 12, 1.0), (2.5, 11, 0.9)],
                [(11.5, 8, 1.0), (13.5, 9.5, 0.9)],
                [(8.5, 21, 1.4), (12, 18, 1.0)]):
        stroke(g, pts, 'm', pick)
    for x, y in ((5, 30), (6, 30), (10, 30), (11, 30), (4, 31), (12, 31)):   # the roots splayed
        if 0 <= y < H - 0:
            g[min(y, 30)][x] = 'd'
    pal = {'l': BARK[0], 'm': BARK[1], 'd': BARK[2], 'K': '000000'}
    return keep4(outline(g), pal), pal


def palm():
    g = blank(W, H)
    pick = lambda x, y, t, side: 'b' if side < 0.2 else 'B'
    stroke(g, [(9.5, 30, 2.8), (9.5, 22, 2.6), (8, 15, 2.4), (6.5, 10, 2.2)], 'b', pick)
    for y in range(11, 30, 3):                                      # the trunk's rings
        for x in range(W):
            if g[y][x] in 'bB':
                g[y][x] = 'B'
    fronds = blank(W, H)
    fpick = lambda x, y, t, side: 'd' if side > 0.3 else 'l' if t < 0.35 and side < -0.2 else 'm'
    for pts in ([(6.5, 8, 2.2), (3, 8.5, 1.8), (2, 13, 1.0)],
                [(6.5, 8, 2.2), (3.5, 4.5, 1.6), (2.5, 3, 1.0)],
                [(6.5, 8, 2.2), (8, 3.5, 1.6), (10.5, 2.5, 1.0)],
                [(6.5, 8, 2.2), (11, 5.5, 1.8), (13.5, 9, 1.0)],
                [(6.5, 8, 2.2), (10, 9.5, 1.8), (12, 14, 1.0)]):
        stroke(fronds, pts, 'm', fpick)
    piece(g, fronds)
    pal = {'l': FOLIAGE[0], 'm': FOLIAGE[1], 'd': FOLIAGE[2], 'b': FOLIAGE[2], 'B': FOLIAGE[1], 'K': '000000'}   # its trunk in the fronds' greens
    return keep4(outline(g), pal), pal


TREES = [('dead_tree', dead), ('palm', palm)]

if __name__ == '__main__':
    want = sys.argv[1:]
    for name, make in TREES:
        if want and name not in want and name.split('_')[-1] not in want:
            continue
        g, pal = make()
        out = os.path.join(HERE, '..', 'entrances', 'palm.png') if name == 'palm' else os.path.join(HERE, name + '.png')
        write(g, pal, out)
        print(name)
