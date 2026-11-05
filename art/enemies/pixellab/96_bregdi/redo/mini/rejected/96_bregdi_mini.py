"""96 Bregdi's map mini: half under the water, its head, open jaws and long fin over the surface, side on as its battle sprite is, two frames (tools/minis.py).

Through PixelLab (pixellab-out/96-redo-mini, 1 generation): the hand-drawn mini-size source art/enemies/pixellab/96_bregdi/redo/mini/source.py given a surge; frames 0 and 1 (the later ones shrank the
water and thinned the fin to a stick). The water's shape is frame 0's in both; a stray speck goes. Only ever side on (mini_sideways(), src/main.cpp). Three colours and black: hide gray, fin taupe,
water mint (eye and teeth take the mint).

Its chase: the surf (chase_speed(), src/main.cpp) -- a lunge through the water, then a glide.

    python art/enemies/minis/96_bregdi_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '848694', 'T': '8d6b4f', 'M': 'a8f0bc'}
CHASE = 'surf'
HEIGHT = 26
HERE = ROOT / 'art/enemies/pixellab/96_bregdi/redo/mini'
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}
N8 = ff.N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def fill(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x - 4, y - 8] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    left, pieces = set(g), []
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    g = {p: g[p] for p in max(pieces, key=len)}
    return {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}


f0, f1 = fill(0), fill(1)
water = {p for p, c in f0.items() if c == 'M' and p[1] >= minis.H - 6}
top = min(p[1] for p in water)
f1 = {p: c for p, c in f1.items() if not (c == 'M' and p[1] >= top - 1) and p[1] < minis.H - 1}
for p in water: f1.setdefault(p, 'M')
LEFT = [ff.outline(f0), ff.outline(f1)]
RIGHT = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': LEFT, 'U': RIGHT}

if __name__ == '__main__':
    minis.make(96, 'bregdi', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(96, CHASE, FRAMES, PAL)
