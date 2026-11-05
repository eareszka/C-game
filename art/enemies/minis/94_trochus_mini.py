"""94 Trochus's map mini: half under the water, its crest and spines over the surface, as Aelian has it (via A Book of Creatures), two frames (tools/minis.py).

Through PixelLab (pixellab-out/94-redo-mini, 1 generation): the hand-drawn mini-size source art/enemies/pixellab/94_trochus/redo/mini/sketch.py given a roll. It came back as a wheel surging
up out of the water and sinking again, which is the lore's rolling and diving, so frames 0 (low) and 2 (risen). A wheel has no front: one drawing in all four views. Three colours and
black: rim blue, spikes bone, water mint.

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide; risen in the lunge, low in the glide (chase_frame()).

    python art/enemies/minis/94_trochus_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'B': '375a94', 'T': 'e8e0c0', 'M': 'a8f0bc'}
CHASE = 'surf'
HEIGHT = 26
HERE = ROOT / 'art/enemies/pixellab/94_trochus/redo/mini'
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127:
                g[x - 6, y - 12] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


ROLL = [frame(0), frame(2)]
FRAMES = {v: ROLL for v in 'DULR'}

if __name__ == '__main__':
    minis.make(94, 'trochus', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(94, CHASE, FRAMES, PAL)
