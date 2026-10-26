"""71 Namungumi's map mini: the "whale" of Lake Malawi that has four limbs, webbing between them, prominent tusks,
and a "whole body ... covered in a complex grid pattern", its wounds healing as soon as they are cut -- crawling
heavily at you out of the lake on its four short legs, at the player's scale, four views, three frames
(tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/71_namungumi/mini, pixellab-out/
71-mini, one generation): eight rotations of its battle front -- its back the plain dome, its side its head out in
front with its tusks. Drawn here after them (the user: "larger please"): its low purple dome, its grid in pale
lines radiating from its glowing eye as its battle dome's does -- a ring round the eye and four spokes out, few
enough that it reads as a grid and not as hatching (dome()) -- its red webbed frill thick and scalloped round its
middle, its pale tusks hanging under it, its four short wide legs; one black outline round it all, its pupil black.
Three frames a view (the user: "3 frames per cycle"; mini_frames() in src/main.cpp, a strip of its own,
assets/enemies/minis_71.png): one pair of legs lifted, all four planted, the other pair lifted -- a heavy crawl.
The right view is the left mirrored.
18 px tall and 30 across, larger than its battle height (33 px) at the minis' one scale, 28/79, would make it.
Three of its battle colours and black: its purple, its pale grid grey (the grid, its eye, its tusks), its red (the
frill).

Its chase: the plod (chase_speed(), src/main.cpp) -- slow and steady, 0.8 of the chase pace.

    python art/enemies/minis/71_namungumi_mini.py
"""
from pathlib import Path
import math, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '3b2a58', 'L': 'bcbeca', 'R': 'b6433d'}
CHASE = 'plod'
HEIGHT = 18
BASE = minis.H - 2                               # its feet's row; the outline under them
TOP = BASE - 15                                  # its dome's top row
CX = minis.W // 2


def dome(cx, a, eye, pupil):
    """Its dome, a half ellipse a px either side of cx and 10 rows tall, its grid in its grey radiating from eye
    (dx, row): a ring round it and four spokes out; its eye there if pupil."""
    g, b = {}, 10.0
    ex, ey = eye
    for y in range(10):
        for x in range(-int(a), int(a) + 1):
            n = (x / a) ** 2 + ((b - y - 0.5) / b) ** 2
            if n > 1: continue
            rx, ry = x - ex, y - ey
            d = math.hypot(rx, ry * 1.4)
            ang = math.degrees(math.atan2(-ry, rx)) % 180
            spoke = d > 3.5 and any(abs(ang - s) < 8 for s in (25, 65, 115, 155))
            ring = 3.0 <= d < 4.0
            g[cx + x, TOP + y] = 'L' if spoke or ring else 'M'
    if pupil:
        for dx, dy in ((-1, -1), (0, -1), (-2, 0), (1, 0), (-1, 1), (0, 1)): g[cx + ex + dx, TOP + ey + dy] = 'L'
        for dx in (-1, 0): g[cx + ex + dx, TOP + ey] = 'K'
    return g


def frill(g, x0, x1):
    """Its red webbed frill round its middle, three rows, its lower edge scalloped."""
    for x in range(x0, x1 + 1):
        g[x, TOP + 10] = g[x, TOP + 11] = 'R'
        if (x - x0) % 4 != 3: g[x, TOP + 12] = 'R'


def leg(g, x, w, lift):
    """A stubby leg w px wide from under its frill down to the ground, lift px short of it when raised."""
    for y in range(TOP + 12, BASE + 1 - lift):
        for i in range(w): g.setdefault((x + i, y), 'M')


def front(step, eye):
    """From the front (eye) or back: its dome, frill, tusks (front only), its near legs and its far legs wide
    behind them; step 0 its left pair lifted, 1 all planted, 2 its right pair lifted."""
    g = dome(CX, 14.0, (0, 6), eye)
    frill(g, CX - 15, CX + 14)
    if eye:
        for x in (CX - 3, CX - 2, CX + 1, CX + 2):
            for y in range(TOP + 12, TOP + 14 + (x in (CX - 2, CX + 1))): g[x, y] = 'L'
    up = {0: (1, 0), 1: (0, 0), 2: (0, 1)}[step]
    leg(g, CX - 11, 4, up[0]); leg(g, CX + 7, 4, up[1])
    leg(g, CX - 15, 3, up[1]); leg(g, CX + 12, 3, up[0])
    return g


def side(step):
    """Head to the left: its dome, its blunt head out in front with a tusk hanging under it, the frill, its near
    fore and hind legs swung forward and back by turns."""
    g = dome(CX + 3, 12.0, (-7, 6), True)
    for y in range(TOP + 5, TOP + 11):
        for x in range(CX - 13, CX - 8): g.setdefault((x, y), 'M')
    g.pop((CX - 13, TOP + 5))
    for y in range(TOP + 11, TOP + 15): g[CX - 12, y] = 'L'
    frill(g, CX - 9, CX + 15)
    swing = (-1, 0, 1)[step]
    leg(g, CX - 6 + swing, 4, 0); leg(g, CX + 8 - swing, 4, 0)
    return g


def finish(g):
    """One black outline round it, its pupil black inside."""
    out = ff.outline({p: ('M' if c == 'K' else c) for p, c in g.items()})
    out.update({p: 'K' for p, c in g.items() if c == 'K'})
    return out


FRAMES = {'D': [finish(front(s, True)) for s in range(3)],
          'U': [finish(front(s, False)) for s in range(3)],
          'L': [finish(side(s)) for s in range(3)]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(71, 'namungumi', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(71, CHASE, FRAMES, PAL)
