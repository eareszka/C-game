"""43 Sazae-oni kept as drawn (PixelLab's redraw came back about the same; the user, 2026-10-29: "mark fine, fix
its colours"), its whole sheet moved onto the game palette: its 13 colours were all off it and over the
bible's eight. Each to its nearest game colour (fcremap Lab), then the near-black outline shade into black,
the pale lilac into the shell's grey, the foot's mid brown into the shell's brown -- eight colours and black.
Writes idle_sheet.png for pixellab_enemy.py install.

    python art/enemies/pixellab/43_sazae_oni/recolour.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MAP = {'8c7c4c': '967448', 'b8a870': 'b29e5c', '5c4c2c': '605028', 'c84c3c': 'b6433d', 'a88470': '967448',
       'e0c0a8': 'e8e0c0', '8c2c24': '7c0a1b', 'd8c8a0': 'e8e0c0', 'a898b8': '9797aa', '241814': '000000',
       'f0e8d8': 'e8e0c0', 'e8d8e8': '9797aa', 'f8e040': 'f0bc3c'}
im = Image.open(ROOT / 'assets/enemies/43_sazae_oni.png').convert('RGBA')
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        p = px[x, y]
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MAP:
            px[x, y] = h(MAP[k]) + (255,)
im.save(HERE / 'idle_sheet.png')
print(len({q[:3] for q in im.get_flattened_data() if q[3]}) - 1, 'colours + black')
