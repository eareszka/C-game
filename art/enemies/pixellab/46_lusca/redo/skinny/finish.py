"""46 Lusca redo: the skinnier frame 0 the user picked (2026-11-03: "make it skinnier", the squeeze): the head's middle 62
columns of frame0.png taken to 46, the arms left as they were. Lone pixels merged, one closed black outline, centred.
Writes ../frame0_skinny.png; frame0.png stays as it was.

    python art/enemies/pixellab/46_lusca/redo/skinny/finish.py
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod
W, H = 98, 65
K = (0, 0, 0, 255)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
RD, CREAM = (0x53, 0x1b, 0x1c), (0xe8, 0xe0, 0xc0)
im = Image.open(HERE / 'squeeze.png').convert('RGBA')
px = im.load()
g = {(x, y): px[x, y] for y in range(H) for x in range(W) if px[x, y][3]}
for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
xs = [x for x, y in g]
dx = W // 2 - (min(xs) + max(xs) + 1) // 2
out = Image.new('RGBA', (W, H))
for (x, y), c in g.items(): out.putpixel((x + dx, y), c)
tidy_mod.SHADE = RD
tidy_mod.KEEP = {CREAM}
tidy_mod.tidy(out)
for (x, y), c in g.items():                 # the brows, eyes and nostrils back: tidy's lone-pixel pass takes diagonal lines
    if c == K and 28 <= y <= 34 and 28 <= x + dx <= 70: out.putpixel((x + dx, y), K)
out.save(HERE.parent / 'frame0_skinny.png')
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
bg.resize((W * 8, H * 8), 0).save(HERE.parent / 'frame0_skinny_x8.png')
print('bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))
