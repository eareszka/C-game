"""87 Corocotta's animated frames (idle-animate-*) brought to the bible as its approved views were. PixelLab's
untouched frames are kept in anim_raw/; this reads them and rewrites idle_anim_*.png with views.py's own steps:
fold() (the game palette, its eight colours, the grey lifted), holes() (its open jaws filled red), eyes()
(tiny marks), then tidy.tidy() (specks, the closed outline, interior black to 14%). Any colour of its mouth,
teeth or eyes touching empty canvas outside its outline (a halo) is peeled away first.

    python art/enemies/pixellab/87_corocotta/anim.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from views import fold, holes, eyes, h
from tidy import tidy

HALO = {h('e8e0c0'), h('b6433d'), h('ec8476'), h('fae488')}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
for v in ('D', 'DR', 'R', 'UR', 'U'):
    for i in range(1, 5):
        im = fold(Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA'))
        px, W, H = im.load(), im.width, im.height
        at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
        for _ in range(3):
            ring = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in HALO
                    and any(not at(x + dx, y + dy)[3] for dx, dy in N4)]
            for p in ring: px[p] = (0, 0, 0, 0)
            if not ring: break
        tidy(eyes(holes(im, v))).save(HERE / f'idle_anim_{v}_{i}.png')
    print(v, 'done')
