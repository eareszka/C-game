"""60 Rumptifusel's map mini: the flat, flexible thing in a pelt like mink that lies like an abandoned fur coat,
gliding flat along the ground at you like a magic carpet, a wave rolling down it from its head to its tail, at the
player's scale, four views, three frames (tools/minis.py; the user: "glide on the ground like a magic carpet",
"make sure it follows bible").

Drawn by hand, as a map object of the bible (art/direction/OVERWORLD_STYLE.md): one silhouette, one 1-px black
outline round it, three colours and black in one ramp placed by form -- the mid brown most of it, the dark massed low
and to the right (its underside, its tail end), the light sparse, high and on the left (the crests of its back) --
flat fills, no lines inside but its eyes. It is only ever seen from the side (the user: its front "looks
awkward"): it still goes all four ways, and going up or down shows the side it last faced (mini_sideways() in
src/main.cpp); its sheet's D and U cells hold its left and right. PixelLab (pixellab-out/60-mini, three generations) gave its rotations and
lunges; it does not rear on the map, so they are not drawn from. Its battle frame's shape is kept: a long low pelt,
its small round head at the front with two little eyes.
Seen as the map sees things, from above: its top, a flat pelt, over a dark edge, under a travelling wave, a third
of a wave on each frame: a 1-2 px ripple rolls from its head to its tail. Three frames a view, so it rolls on smoothly
(mini_frames() in src/main.cpp; a strip of its own, assets/enemies/minis_60.png). The right view is the left
mirrored.
31 px long, its battle frame's width (87 px) at the minis' one scale, 28/79; flat, so lower than its battle height's
21. Three of its battle colours and black: its light, mid and dark browns. Its purple belly goes (the ramp).

Its chase: straight at you at the chase pace, never stopping (the default in chase_speed(), src/main.cpp): a glide.

    python art/enemies/minis/60_rumptifusel_mini.py
"""
from pathlib import Path
import math, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'L': '94703d', 'M': '633e1b', 'D': '3c2412'}
CHASE = 'straight'
HEIGHT = 21
LONG = 31                                        # its length from the side
TOP = 5                                          # how much of its top shows from the side
PHASES = (0, 2 * math.pi / 3, 4 * math.pi / 3)   # its wave a third on, each frame
BASE = minis.H - 2                               # its lowest row; the outline under it


def wave(x, length, phase, amp):
    return round(amp + amp * math.sin(2 * math.pi * x / length - phase))


def side(phase):
    """Head to the left: its top seen from above, TOP rows deep over a dark edge, a wave of 16 px rolling tailward
    lifting it 0-2 px; its tail end's corners rounded; its small round head out in front at the near edge.
    Returns the fill and where its eyes go."""
    g = {}
    for x in range(LONG):
        lift = wave(x, 16, phase, 1)
        bottom = BASE - lift
        for y in range(bottom - TOP, bottom): g[x, y] = 'M'
        g[x, bottom] = 'D'                                                    # its edge, under it
        if x >= LONG - 6: g[x, bottom - 1] = 'D'                              # its tail end: the dark low and right
        if 2 <= x < LONG // 2 and lift == 2: g[x, bottom - TOP] = 'L'         # the crests of its back, high and left
    for x in (LONG - 1,):                                                     # its tail end's corners
        col = [y for (i, y) in g if i == x]
        g.pop((x, min(col))); g.pop((x, max(col)))
    hb = BASE - wave(0, 16, phase, 1)                                         # its head, low at the front
    for x in range(-4, 0):
        for y in range(hb - 3, hb + 1): g[x, y] = 'M'
        g[x, hb] = 'D'
    g.pop((-4, hb - 3)); g.pop((-4, hb))
    return g, [(-3, hb - 2), (-1, hb - 2)]


def place(drawn):
    """Centred, one outline round it all, then its eyes."""
    g, eyes = drawn
    xs = [x for x, y in g]
    dx = minis.W // 2 - (min(xs) + max(xs) + 1) // 2
    out = ff.outline({(x + dx, y): c for (x, y), c in g.items()})
    for x, y in eyes: out[x + dx, y] = 'K'
    return out


LEFT = [place(side(p)) for p in PHASES]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': LEFT, 'U': RIGHT}   # only ever side on (the user: its front "looks awkward";
                                                         # mini_sideways() in src/main.cpp shows the side it last faced)

if __name__ == '__main__':
    minis.make(60, 'rumptifusel', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(60, CHASE, FRAMES, PAL)
