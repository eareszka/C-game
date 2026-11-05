"""94 Trochus's mini, its source for PixelLab: half under the water as its lore has it, its crest and spines over the surface (Aelian, via A Book of Creatures). The wheel's upper
half: blue rim, black between the spokes, bone spikes, pale water where it enters the surface. Drawn at mini size. Three colours and black.

    python art/enemies/pixellab/94_trochus/redo/mini/sketch.py
"""
from pathlib import Path
import math, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff
PAL = {'K': '000000', 'B': '375a94', 'T': 'e8e0c0', 'M': 'a8f0bc'}
CX, WY = 20, minis.H - 5                 # hub on the waterline
g = {}
for y in range(minis.H):
    for x in range(minis.W):
        dx, dy = x - CX + 0.5, y - WY + 0.5
        r = math.hypot(dx, dy)
        if y >= WY: continue
        a = math.atan2(dy, dx) % (2 * math.pi)
        if r <= 1.8: g[x, y] = 'B'
        elif r <= 6.2:
            s = (a / (2 * math.pi) * 8) % 1
            g[x, y] = 'B' if min(s, 1 - s) * 2 * math.pi * r / 8 <= 0.6 else 'K'
        elif r <= 9: g[x, y] = 'B'
        else:
            for i in range(7):
                c = math.pi + (i + 0.5) * math.pi / 7
                d = (a - c + math.pi) % (2 * math.pi) - math.pi
                L = 6 if i % 2 == 0 else 4.5
                if i == 3: L = 8
                if r - 9 < L and abs(d) <= 0.2 * (1 - (r - 9) / L) + 0.015: g[x, y] = 'T'
for x in range(CX - 16, CX + 16):
    g[x, WY] = g[x, WY + 1] = 'M'
for x in range(CX - 13, CX + 13): g[x, WY + 2] = 'M'
gg = ff.outline(g)
im = ff.image(gg, PAL, minis.W, minis.H)
ys = [y for x, y in gg]; xs = [x for x, y in gg]
print('box', max(xs) - min(xs) + 1, 'x', max(ys) - min(ys) + 1, 'rows', min(ys), max(ys))
ff.image(gg, PAL, minis.W, minis.H, bg=minis.GRASS).resize((minis.W * 10, minis.H * 10), 0).save(HERE / 'first_x10.png')
from PIL import Image
pad = Image.new('RGBA', (52, 52)); pad.paste(im, (6, 12)); pad.save(HERE / 'input.png')     # cell (x, y) lands at (x + 6, y + 12)
