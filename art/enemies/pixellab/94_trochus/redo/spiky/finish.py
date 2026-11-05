"""94 Trochus frame 0 from PixelLab's s2 (spiky/prompt.txt, 1 generation of 3): folded onto five palette colours as the cast's flat fills (rim one blue, spokes and shade one navy,
spikes bone with a tan shade), clumps of 3 px or fewer merged, each spike joined to the rim (the black ring at their bases would float them on the battle's black), one outline, no water.

    python art/enemies/pixellab/94_trochus/redo/spiky/finish.py   # writes ../frame0.png, ../frame0_x8.png, ../frame0_black_x8.png
"""
from pathlib import Path
from collections import Counter
import math
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K, MID, DARK, BONE, TAN = (0, 0, 0), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a)
PAL = (K, MID, DARK, BONE, TAN)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
im = Image.open(HERE / 's2.png').convert('RGBA').crop((1, 1, 99, 66))
def fold(p):
    r, g, b = p
    if max(p) < 0x18: return K
    if r > 0xb0: return BONE
    if abs(r - b) < 0x30 and g > 0x70 and g >= b - 8: return TAN        # the spikes' grey-green shade
    return MID if b > 0x78 and g > 0x48 else DARK
g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if im.getpixel((x, y))[3] > 127}
seen, out = set(), dict(g)
for p, c in g.items():
    if p in seen: continue
    piece, todo = {p}, [p]
    while todo:
        a = todo.pop()
        for dx, dy in N4:
            q = (a[0] + dx, a[1] + dy)
            if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
    seen |= piece
    if c == K or len(piece) > 3: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
hide = [p for p, c in g.items() if c in (MID, DARK)]
cx, cy = sum(p[0] for p in hide) / len(hide), sum(p[1] for p in hide) / len(hide)
print('centre', round(cx, 1), round(cy, 1))
for p, c in list(g.items()):                                             # join the spikes: gaps between a spike and the rim take the spike's colour
    if c != K and p in g: continue
for _ in range(3):
    for x in range(W):
        for y in range(H):
            if g.get((x, y)) in (K, None):
                d = math.hypot(x - cx, y - cy) or 1
                ux, uy = (x - cx) / d, (y - cy) / d
                o = [g.get((round(x + ux * s), round(y + uy * s))) for s in (1, 2)]
                i = [g.get((round(x - ux * s), round(y - uy * s))) for s in (1, 2, 3)]
                if any(c in (BONE, TAN) for c in o) and any(c in (MID, DARK) for c in i) and d > 15:
                    g[x, y] = next(c for c in o if c in (BONE, TAN))
for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
for x in range(W):                                                       # the gaps between the spokes are black, not see-through: one silhouette
    for y in range(H):
        if (x, y) not in g and math.hypot(x - cx, y - cy) <= 17: g[x, y] = K
for p, c in list(g.items()):                                             # blue flecks out on the spikes
    if c in (MID, DARK) and math.hypot(p[0] - cx, p[1] - cy) > 23.5: g[p] = BONE
for _ in range(2):                                                       # lone pixels join what surrounds them
    for (x, y), c in list(g.items()):
        if c == K: continue
        near = [g.get((x + a, y + b)) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
        if c not in near:
            pick = Counter(n for n in near if n and n != K).most_common(1)
            if pick: g[x, y] = pick[0][0]
ys = [y for x, y in g]
dy = H - 1 - max(ys)
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y + dy < H: f.putpixel((x, y + dy), c + (255,))
f.save(HERE.parent / 'frame0.png')
print(f.getbbox())
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE.parent / name)
