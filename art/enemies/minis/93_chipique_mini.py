"""93 Chipique's map mini: swimming SUBMERGED (the user, 2026-11-03: "mini should be submerged"), side on, two frames (tools/minis.py).

Under the water all but what breaks the surface: its head and neck, the canoe with its rider and paddle, its tail's hook, the pale water round them (as 85 and 88).
Through PixelLab (pixellab-out/93-redo3-mini, 1 generation): the hand-drawn mini-size source art/enemies/pixellab/93_chipique/redo3/mini/first.png given a swim; the
later frames lost the paddle and stiffened the tail, so frames 0 and 1. Only ever side on, as the battle sprite never turns (the user): going up or down it shows the
side it last faced (mini_sideways(), src/main.cpp). Three colours and black: hide purple, canoe brown, water mint (the rider's eyes take the mint).

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide.

    python art/enemies/minis/93_chipique_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'P': '423c70', 'B': '785830', 'M': 'a8f0bc'}
CHASE = 'surf'
HEIGHT = 24
HERE = ROOT / 'art/enemies/pixellab/93_chipique/redo3/mini'
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
OFF = 8     # the source's padding (PixelLab wants room round it)
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127:
                g[x - OFF, y - OFF] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    return ff.outline(g)


LEFT = [frame(0), frame(1)]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': LEFT, 'U': RIGHT}   # only ever side on (mini_sideways() in src/main.cpp)

if __name__ == '__main__':
    minis.make(93, 'chipique', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(93, CHASE, FRAMES, PAL)
