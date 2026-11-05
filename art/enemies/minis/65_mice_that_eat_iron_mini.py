"""65 Mice That Eat Iron's map mini: the three mice scurrying off with their iron beam, at the small enemies' 12 px
height (01, 03, 04 are 12 tall), four views, two frames (tools/minis.py).

Drawn by hand, fill only, one black outline round it: PixelLab lost the three mice at its battle size already, smaller
still it has nothing to work with. Same trio as its battle sheet, the middle mouse a row taller, the beam across them.
Front: faces and beam. Back: ears and tails, no faces. Side: the three in a file, noses to the left, carrying it; the
right view is the left mirrored. Two frames step their feet, the outer and middle mice out of step. Three of its
battle colours and black: fur, ear pink, the pale of muzzle and beam.

Its chase: the dart (chase_speed(), src/main.cpp), as the Treesqueak's -- a mouse's scurry, a freeze.

    python art/enemies/minis/65_mice_that_eat_iron_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'F': '848694', 'P': 'ec8476', 'M': 'c6ccda'}
CHASE = 'dart'
HEIGHT = 12

FRONT = """
PP...PP
PPPFPPP
.PFFFP.
.FKFKF.
.FFMFF.
.FFFFF.
.FFFFF.
.FF.FF.
"""
BACK = """
PP...PP
PPPFPPP
.PFFFP.
.FFFFF.
.FFFFF.
.FFFFF.
.FFFFF.
.FFFFF.
"""
FEET = (".PP.PP.", "..P.P..")
SIDE = """
..PPP....
.PPPPFFF.
.PPFFFFFF
FFKFFFFFF
MMFFFFFFF
.FFFFFFFF
.FFFFFFFF
"""
SIDE_FEET = ("..P...P..", "...P.P...")


def rows(s):
    return s.strip().split(chr(10))


def trio(face, f):
    """Three side by side with a black line between them, the middle one a row taller; the beam across their paws."""
    g = {}
    for m, (ox, oy) in enumerate(((0, 1), (16, 1), (8, 0))):
        for y, r in enumerate(rows(face) + [FEET[(f + (m == 2)) % 2]]):
            for x, c in enumerate(r):
                if c != '.': g[ox + x, oy + y] = c
    for x in range(-1, 24): g[x, 6] = 'M'
    return g


def file_(f):
    """Three in a file, noses left, the beam along them."""
    g = {}
    for m, (ox, oy) in enumerate(((0, 1), (18, 1), (9, 0))):
        for y, r in enumerate(rows(SIDE) + [SIDE_FEET[(f + (m == 2)) % 2]]):
            for x, c in enumerate(r):
                if c != '.': g[ox + x, oy + y] = c
    for x in range(-1, 28): g[x, 6] = 'M'
    return g


def place(g):
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


def mirror(g):
    return {(minis.W - 1 - x, y): c for (x, y), c in g.items()}


FRAMES = {'D': [place(trio(FRONT, f)) for f in (0, 1)], 'U': [place(trio(BACK, f)) for f in (0, 1)],
          'L': [place(file_(f)) for f in (0, 1)]}
FRAMES['R'] = [mirror(g) for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(65, 'mice_that_eat_iron', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(65, CHASE, FRAMES, PAL)
