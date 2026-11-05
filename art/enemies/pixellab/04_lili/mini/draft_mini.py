"""04 Lili's new map mini, DRAFT (art/enemies/minis/04_lili_mini.* stays until the user approves): the pig-like scuttler at the player's scale, four views, two frames
(tools/minis.py). The old mini had one frame a view and hopped; this one runs on its four legs. Through PixelLab (pixellab-out/04-mini, 3 generations): the hand-drawn
sources in source.py each given a trot; frames 0 and 1 (the later ones lost the ears). The right view is the left mirrored. Three colours and black, as the old mini.
Its chase stays the one the user chose: straight at you, head on (2026-10-14). Writes into draft/.

    python art/enemies/pixellab/04_lili/mini/draft_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': 'ec8476', 'L': 'f0b890', 'P': 'fc74b4'}
CHASE = 'straight'
HEIGHT = 18
OFF = {'D': (-8, -6), 'U': (-8, -6), 'L': (-4, 2)}     # where the cell's corner lands on the source canvas (source.py)
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(v, i):
    ps = [l.strip() for l in (HERE / f'anim{v}.log').read_text().splitlines() if l.strip().endswith('.png')]
    im = Image.open(ps[i]).convert('RGBA')
    ox, oy = OFF[v]
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127:
                g[x - ox, y - oy] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    bottom = max(y for x, y in g)
    g = {(x, y + minis.H - 2 - bottom): c for (x, y), c in g.items()}   # feet on the cell's last row but one
    return ff.outline(g)


FRAMES = {v: [frame(v, 0), frame(v, 1)] for v in 'DUL'}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.HERE = HERE / 'draft'
    minis.make(4, 'lili', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(4, CHASE, FRAMES, PAL)
    for v, gs in FRAMES.items():
        for g in gs:
            print(v, max(x for x, y in g) - min(x for x, y in g) + 1, 'x', max(y for x, y in g) - min(y for x, y in g) + 1)
