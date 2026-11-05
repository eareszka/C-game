"""96 Bregdi's map mini: half under the water, jaws open, fins up, side on as its battle sprite is, two frames (tools/minis.py).

Drawn by PixelLab alone (the user, 2026-11-03: "minis should use pixellab"): sprite at the mini's size and palette (pixellab-out/96-mini2, concept m1, 1 of 4 generations), then a surge
(pixellab-out/96-mini2-anim, 1 generation); frames 0 and 2. Each pixel folds onto the palette, lone flecks merge, one black outline. Only ever side on (mini_sideways(), src/main.cpp). Three colours and
black: hide gray, fins taupe, water mint.

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide.

    python art/enemies/minis/96_bregdi_mini.py
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'T': '8d6b4f', 'M': 'a8f0bc'}
CHASE = 'surf'
HEIGHT = 26
HERE = ROOT / 'art/enemies/pixellab/96_bregdi/redo/mini2'
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}
N8 = ff.N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def frame(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    for (x, y), c in list(g.items()):
        near = [g.get((x + a, y + b)) for a, b in N8]
        if c != 'K' and c not in near:
            pick = Counter(n for n in near if n and n != 'K').most_common(1)
            if pick: g[x, y] = pick[0][0]
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


LEFT = [frame(0), frame(2)]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': LEFT, 'U': RIGHT}

if __name__ == '__main__':
    minis.make(96, 'bregdi', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(96, CHASE, FRAMES, PAL)
