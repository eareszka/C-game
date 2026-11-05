"""84 Kigutilik kept as drawn (PixelLab's redraw changed 5 px; the user, 2026-10-29: "mark fine, fix colours"). Its
sheet was already on the game palette but at nine colours, one over the bible's eight: the deepest violet (the
shadow inside its cup and under its jaw) folds into the dark violet beside it -- eight colours and black.
Writes idle_sheet.png for pixellab_enemy.py install.

    python art/enemies/pixellab/84_kigutilik/recolour.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MAP = {'301b5a': '3b2a58'}
im = Image.open(ROOT / 'assets/enemies/84_kigutilik.png').convert('RGBA')
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        p = px[x, y]
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MAP:
            px[x, y] = h(MAP[k]) + (255,)
im.save(HERE / 'idle_sheet.png')
print(len({q[:3] for q in im.get_flattened_data() if q[3]}) - 1, 'colours + black')
