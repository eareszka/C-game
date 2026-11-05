"""94 Trochus's idle: 3 poses (the user, 2026-11-03: "3 frame animation"), one view in every direction, a wheel having no front. PixelLab's turn of the approved frame
(pixellab-out/94-redo-anim, 1 generation; anim.log, action.txt): frame 0 is the approved frame itself, 1 and 2 are PICK. Colours fold onto the approved frame's, each pose is lined up on its
hub so the wheel turns in place, gaps between the spokes black, one outline. In the default 0 1 0 2 loop it rocks round its hub.

    python art/enemies/pixellab/94_trochus/redo/anim/anim.py   # c_N.png, review.png, 94.gif, 94_redo_review.aseprite
"""
from pathlib import Path
from collections import Counter
import math, subprocess
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 69, 260      # 69 rows, not the standard 65: the turning spikes reach further down than the approved frame's
K, MID, DARK, BONE, TAN = (0, 0, 0), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a)
PAL = (MID, DARK, BONE, TAN)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
PICK = (2, 3)   # pose 1 smudged its spikes; 4 hardly differs from the approved frame
BASE = Image.new('RGBA', (W, H)); BASE.paste(Image.open(HERE.parent / 'frame0.png').convert('RGBA'), (0, 0))
def centre(g):
    hide = [p for p, c in g.items() if c in (MID, DARK)]
    return sum(p[0] for p in hide) / len(hide), sum(p[1] for p in hide) / len(hide)
b = {(x, y): BASE.getpixel((x, y))[:3] for y in range(H) for x in range(W) if BASE.getpixel((x, y))[3]}
CX, CY = centre(b)
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x20 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    cx, cy = centre(g)
    dx, dy = round(CX - cx), round(CY - cy)
    g = {(x + dx, y + dy): c for (x, y), c in g.items()}
    for x in range(W):
        for y in range(H):
            if (x, y) not in g and math.hypot(x - CX, y - CY) <= 17: g[x, y] = K
    for p, c in list(g.items()):
        if c in (MID, DARK) and math.hypot(p[0] - CX, p[1] - CY) > 23.5: g[p] = BONE
    for _ in range(2):
        for (x, y), c in list(g.items()):
            if c == K: continue
            near = [g.get((x + a, y + d)) for a in (-1, 0, 1) for d in (-1, 0, 1) if a or d]
            if c not in near:
                pick = Counter(n for n in near if n and n != K).most_common(1)
                if pick: g[x, y] = pick[0][0]
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + d) not in g for a, d in N4)]: del g[p]
    for x, y in list(g):
        for a, d in N4:
            if (x + a, y + d) not in g: g[x + a, y + d] = K
    ys = [y for x, y in g]
    print('rows', min(ys), max(ys))
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
fr = [BASE] + [clean(ps[i]) for i in PICK]
import sys
if len(sys.argv) > 1:                                     # python anim.py all: every pose on a board, to choose PICK
    al = [clean(p) for p in ps[1:]]
    b2 = Image.new('RGBA', (W * 5 * len(al), H * 5), (0, 0, 0, 255))
    for i, f in enumerate(al): b2.alpha_composite(f.resize((W * 5, H * 5), 0), (i * W * 5, 0))
    b2.save(HERE / 'all.png'); raise SystemExit
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '94.gif', save_all=True, append_images=big[1:], duration=MS, loop=0)
