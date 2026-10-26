"""47 Moha-Moha's map mini: the long-necked turtle of the Queensland shore, hauled up out of the sea, flopping at
you on its four flippers, at the player's scale, four views, three frames (tools/minis.py; the user: "move in 3
frames in each direction ... I like the idea of it flopping around").

Its battle sheet has one view, its side. Through PixelLab (art/enemies/pixellab/47_moha_moha/mini,
pixellab-out/47-mini, six generations): eight rotations of its side shrunk to 40 px, then its side and front each
given a flop -- heaved up on its front flippers, flopping down flat on its belly, flippers splayed -- and its back a
crawl, the heave lifted a pixel. Each mini frame is one of those frames on the mini's palette (minis.recolour), shrunk to its height (minis.shrink, a view's frames by one
box so they line up), its lone pixels taken into the colour round them (minis.clean), one black outline round it.
The right view is the left mirrored, as its battle sheet mirrors.
19 px tall: its battle height (55 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
green (neck, flippers, the fan tail), its shell grey, its cream (belly, the underside of its neck).

Its chase: the flop (as the Lodsilungur's, chase_speed() and chase_bend(), src/main.cpp) -- flung forward, then lying
there, each flop veering the other way; chase_frame() plays its three frames: heaved up, flopping down, lying flat.

    python art/enemies/minis/47_moha_moha_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis

PAL = {'K': '000000', 'G': '4fa667', 'M': '595965', 'B': 'cebe82'}
CHASE = 'flop'
HEIGHT = 19
SRC = ROOT / 'pixellab-out/47-mini/animations'
# Three frames a view, as its chase plays them (chase_frame() in src/main.cpp): lying flat, heaved up on its front
# flippers, flopping down. The back has no flop of its own: its crawl, the heave a pixel up.
FLOPS = {'D': ('v4/flopd', (4, 2, 3), (0, 0, 0)), 'U': ('v2/crawlu', (1, 2, 3), (0, 1, 0)), 'L': ('v5/flopl', (4, 2, 3), (0, 0, 0))}


def tone(h, s, v):
    """Its greens and its brown tail green, its greys the shell, its pale tans the cream, the darkest black."""
    if v < 0.12: return 'K'
    if s < 0.2: return 'M'
    if 70 <= h <= 170: return 'G'
    return 'B' if v > 0.6 else 'G'


def view(name, picks, lifts):
    ims = [minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    gs = [minis.clean(minis.shrink(im, HEIGHT, letters, box)) for im in ims]
    return [{(x, y - k): c for (x, y), c in g.items()} for g, k in zip(gs, lifts)]


EYES = {'D': [[(19, 21), (21, 21)], [(18, 12), (21, 12)], [(19, 21), (21, 21)]],   # by hand: the shrink loses them
        'L': [[(12, 15)], [(16, 12)], [(13, 14)]]}

FRAMES = {v: view(*FLOPS[v]) for v in 'DUL'}
for v, fs in EYES.items():
    for g, eyes in zip(FRAMES[v], fs):
        for p in eyes:
            assert g[p] == 'G', (v, p)
            g[p] = 'K'
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(47, 'moha_moha', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(47, CHASE, FRAMES, PAL)
