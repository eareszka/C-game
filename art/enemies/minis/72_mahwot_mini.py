"""72 Mahwot's map mini: the lizard-like amphibious monster of the Meuse that runs back and forth along the
riverbed and pulls in the children who play too close -- drawn, as its battle is, as a swimming mini-Godzilla --
swimming at you fast, weaving, a wave rolling down its body from its head to its tail, at the player's scale, only
ever from the side, three frames (tools/minis.py).

Its battle sheet is drawn from the side only (the user: "it swims left and right"), so the mini is too: it still
goes all four ways, and going up or down shows the side it last faced (mini_sideways() in src/main.cpp); its
sheet's D and U cells hold its left and right. PixelLab (pixellab-out/72-mini, one generation) gave its swim from
its battle side; drawn here by hand to it (side()): its long low body in its green, its heavy head out in front
with its eye, its tan belly and jaw underneath, its row of pale dorsal plates along its back, tallest mid-back and
smaller down its tail, its short legs tucked back and paddling, its tail tapering. Three frames a view (mini_frames() in src/main.cpp; a strip of its own, assets/enemies/
minis_72.png): a third of a wave on each, its head steady, its tail swinging most, its legs stroking. One black
outline round it all. The right view is the left mirrored.
36 px long and 15 tall, a little larger than its battle frame (89 x 30 px) at the minis' one scale, 28/79, would
make it (the user wanted 70 and 71 bigger). Three of its battle colours and black: its green, its tan (belly,
jaw), its plate grey (its dorsal plates, high and light). Its light and dark greens go into its green.

Its chase: the wiggle (chase_speed() and chase_bend(), src/main.cpp) -- fast and never stopping, weaving in an S
as it runs its river in battle.

    python art/enemies/minis/72_mahwot_mini.py
"""
from pathlib import Path
import math, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '235436', 'T': 'b29e5c', 'S': 'c6ccda'}
CHASE = 'wiggle'
HEIGHT = 15
LONG = 36                                        # snout to tail tip
BASE = minis.H - 2                               # its feet's row; the outline under them
MID = BASE - 4                                   # its body's middle row, at rest
PHASES = (0, 2 * math.pi / 3, 4 * math.pi / 3)   # its wave a third on, each frame
PLATES = {11: 2, 14: 3, 17: 3, 20: 2, 23: 2, 27: 1}   # a dorsal plate's x and its height over its back, two px
                                                 # wide: tallest mid-back, smaller down its tail


def thick(x):
    """Its body's depth at x: a blunt snout, its head, its neck, a deep torso, a tail tapering to a point."""
    if x < 3: return 3
    if x < 9: return 5
    if x < 11: return 4
    if x < 25: return 6
    return max(1, round(5 - (x - 25) * 0.45))


def side(phase):
    """Head to the left. Its middle line swings by a wave rolling tailward, still at its head and swinging most at
    its tail; under its torso and head its belly and jaw are tan; along its back its plates stand up; its legs
    stroke fore and back with the wave."""
    g = {}
    tops = {}
    for x in range(LONG):
        swing = min(1.0, max(0.0, (x - 6) / 18))
        mid = MID + round(1.5 * swing * math.sin(2 * math.pi * (x - 6) / 22 - phase))
        th = thick(x)
        top = mid - th // 2
        tops[x] = top
        for y in range(top, top + th):
            belly = x < 27 and y >= top + th - (2 if th >= 5 else 1)
            g[x, y] = 'T' if belly else 'M'
    for px, h in PLATES.items():
        for i in range(h):
            g[px, tops[px] - 1 - i] = 'S'
            if i < h - 1 or h == 1: g[px + 1, tops[px + 1] - 1 - i] = 'S'   # its trailing edge, a step lower
    stroke = round(math.sin(phase))
    for lx in (12 + stroke, 22 - stroke):        # its short fore and hind legs, tucked back, paddling opposite ways
        bottom = max(y for (x, y) in g if x == lx)
        for y in range(bottom + 1, BASE):
            g[lx, y] = g[lx + 1, y] = 'M'
        g[lx + 1, BASE] = g[lx + 2, BASE] = 'M'                       # its foot, swept back
    eye = (4, tops[4] + 1)
    return g, eye


def place(drawn):
    """Centred, one outline round it all, then its eye."""
    g, (ex, ey) = drawn
    dx = minis.W // 2 - LONG // 2
    out = ff.outline({(x + dx, y): c for (x, y), c in g.items()})
    out[ex + dx, ey] = 'K'
    return out


LEFT = [place(side(p)) for p in PHASES]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': LEFT, 'U': RIGHT}   # only ever side on (mini_sideways() in src/main.cpp)

if __name__ == '__main__':
    minis.make(72, 'mahwot', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(72, CHASE, FRAMES, PAL)
