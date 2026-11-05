"""94 Trochus, spikier and flatter (the user, 2026-11-03: "needs to be more spiky and match the other enemies sprites flatness and appearance"). A source for PixelLab:
the picked concept's spoked wheel laid out flat, with long and short spikes round the rim and a taller crest on top (the lore's crest and spines). Hide one blue and one
shade, spokes, hub and spikes one pale blue, black between the spokes and at the part lines, one outline.

    python art/enemies/pixellab/94_trochus/redo/spiky/sketch.py   # sketch.png, input.png (padded for PixelLab), sketch_x8.png
"""
from pathlib import Path
import math
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K, LIGHT, MID, DARK = (0, 0, 0), (0x84, 0xa7, 0xe9), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b)
CX, CY = 49.0, 33.0
RIM, RIM_IN, HUB = 21.0, 14.5, 5.0
N, SPOKES = 14, 8
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
g = {}
for y in range(H):
    for x in range(W):
        dx, dy = x - CX, y - CY
        r, a = math.hypot(dx, dy), math.atan2(dy, dx) + math.pi / 2       # a = 0 at the top
        if r <= HUB: g[x, y] = LIGHT if dx + dy < 2 else MID
        elif r <= RIM_IN:
            s = (a / (2 * math.pi) * SPOKES) % 1
            g[x, y] = LIGHT if min(s, 1 - s) * 2 * math.pi * r / SPOKES <= 1.1 else K
        elif r <= RIM:
            g[x, y] = MID if dx + dy < 11 else DARK
        else:
            for i in range(N):
                c = i * 2 * math.pi / N
                d = (a - c + math.pi) % (2 * math.pi) - math.pi
                long = 11.0 if i % 2 == 0 else 6.5
                if i in (0, 1, N - 1): long += 1.5                       # the crest
                half = 2 * math.pi / N * 0.42 * (1 - (r - RIM) / long)
                if r - RIM < long and abs(d) <= half: g[x, y] = LIGHT
xs, ys = [p[0] for p in g], [p[1] for p in g]
for p in [p for p, c in g.items() if c == LIGHT and math.hypot(p[0] - CX, p[1] - CY) > RIM and math.hypot(p[0] - CX, p[1] - CY) <= RIM + 1.2]: g[p] = K   # the line where a spike meets the rim
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
print('box', f.getbbox())
f.save(HERE / 'sketch.png')
pad = Image.new('RGBA', (100, 68)); pad.paste(f, (1, 1)); pad.save(HERE / 'input.png')
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / 'sketch_x8.png')
