"""56 Moskitto's map mini: Paul Bunyan's mosquito crossed with his Texas fighting bumblebees, bee-striped, red-eyed,
needle-nosed, never landing, buzzing at you, at the player's scale, four views, two frames (tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/56_moskitto/mini,
pixellab-out/56-mini, four generations): eight rotations of its battle front, then its front, back and left side
each given a hover (the back is not used: its back is its front's shape, back()) -- wings beating, legs dangling. Each mini frame is one of those on the mini's palette
(minis.recolour), shrunk (minis.shrink, a view's frames by one box so they line up), cleaned (minis.clean), one
black outline round it: its wings up, then level. The right view is the left mirrored.
It flies: on the map it hovers above its shadow (mini_hover() in src/main.cpp, the user: "hover + ground shadow"),
bobbing with its wingbeat.
20 px tall: its battle height (56 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
wing grey (the wings, the needle), its bee yellow (body, legs), its red (eyes). Its stripes are the black.

Its chase: the buzz (chase_speed() and chase_bend(), src/main.cpp) -- straight at you, weaving side to side.

    python art/enemies/minis/56_moskitto_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis

PAL = {'K': '000000', 'C': 'c6ccda', 'Y': 'f0bc3c', 'R': 'b6433d'}
CHASE = 'buzz'
HEIGHT = 20
HOVER = 6                                        # its shadow's half width, art px (mini_hover() in src/main.cpp)
SRC = ROOT / 'pixellab-out/56-mini/animations'
FLIGHTS = {'D': ('v1/flyd', (0, 3)), 'L': ('v2/flyl', (0, 2))}   # wings up, wings down


def tone(h, s, v):
    """Its darkest black (the shrink drops it: the stripes go back on by stripes()), its greys and blues the wings, its deep reds the eyes, the rest bee yellow."""
    if v < 0.25: return 'K'
    if s < 0.25 or 180 <= h <= 260: return 'C'
    if (h < 20 or h > 330) and v < 0.8: return 'R'
    return 'Y'


def view(name, picks):
    ims = [minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    return [minis.clean(minis.shrink(im, HEIGHT, letters, box)) for im in ims]


def stripes(g, side):
    """Its bee stripes, a black line every other one across the yellow of its abdomen: rows down its lower half from
    the front and back, columns behind its thorax from the side (its head to the left)."""
    ys = [y for (x, y), c in g.items() if c == 'Y']
    xs = [x for (x, y), c in g.items() if c == 'Y']
    if side:
        x0 = min(xs) + (max(xs) - min(xs)) // 2
        return {(x, y): 'K' if c == 'Y' and x > x0 and (x - x0) % 2 == 0 else c for (x, y), c in g.items()}
    y0 = min(ys) + (max(ys) - min(ys)) // 2
    return {(x, y): 'K' if c == 'Y' and y > y0 and (y - y0) % 2 == 1 else c for (x, y), c in g.items()}


def back(g):
    """Its back, from its front: the same body and wings (PixelLab's back spread its wings wider; the user, of 48:
    the views' proportions match), from the eyes down all yellow -- no eyes, no needle, no black inside -- for
    stripes() to stripe."""
    y0 = min(y for (x, y), c in g.items() if c == 'R')
    inside = lambda p: all((p[0] + dx, p[1] + dy) in g for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    return {p: 'Y' if p[1] >= y0 and (c in 'RC' or c == 'K' and inside(p)) else c for p, c in g.items()}


FRONT = {v: view(*FLIGHTS[v]) for v in 'DL'}
FRAMES = {'D': [stripes(g, False) for g in FRONT['D']], 'U': [stripes(back(g), False) for g in FRONT['D']],
          'L': [stripes(g, True) for g in FRONT['L']]}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(56, 'moskitto', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(56, CHASE, FRAMES, PAL, hover=HOVER)
