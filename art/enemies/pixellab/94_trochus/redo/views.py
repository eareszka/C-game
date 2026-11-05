"""94 Trochus redo: frame 0 from the picked concept (the user, 2026-11-03: concepts/c2.png, "top right, no water"): the Greek sea monster the "wheel" (Aelian; A Book of
Creatures), a spoked wheel with a spiny rim, on the standard 98x65 frame. The concept stood in water under a sky: sky, clouds and water go. Its lowest part was hidden in the
splash, so rows below SEAM are the wheel's own upper rows mirrored about its centre. Blues fold onto the palette, small clumps merge, one closed black outline.

    python art/enemies/pixellab/94_trochus/redo/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
CY, SEAM = 32, 44
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FOLD = {0x161d3c: (0x34, 0x34, 0x3e), 0x23387a: (0x37, 0x38, 0x7b), 0x3e5aa0: (0x37, 0x5a, 0x94), 0x6382c6: (0x84, 0xa7, 0xe9), 0x8099e5: (0x84, 0xa7, 0xe9), 0xc1ccfd: (0x84, 0xa7, 0xe9)}
im = Image.open(HERE / 'concepts/c2.png').convert('RGB')


def wheel(x, y):
    p = im.getpixel((x, y))
    n = p[0] << 16 | p[1] << 8 | p[2]
    return FOLD.get(n)


g = {}
for y in range(im.height):
    for x in range(im.width):
        c = wheel(x, y if y <= SEAM else 2 * CY - y) if 0 <= (y if y <= SEAM else 2 * CY - y) < im.height else None
        if c: g[x, y] = c
g = {p: c for p, c in g.items() if (p[0] - 47.5) ** 2 + (p[1] - CY) ** 2 <= 31 ** 2}     # crumbs of the splash and sky
for y in range(im.height):                                                                  # holes inside the rim the fold left
    for x in range(im.width):
        if (x, y) not in g and (x - 47.5) ** 2 + (y - CY) ** 2 <= 24 ** 2:
            n = Counter(g[x + a, y + b] for a, b in N4 if (x + a, y + b) in g)
            if n: g[x, y] = n.most_common(1)[0][0]
LIGHT, MID, DARK = (0x84, 0xa7, 0xe9), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b)
for (x, y), c in list(g.items()):                                                           # light comes from the upper left: no highlight on the mirrored underside
    if y > SEAM and c == LIGHT: g[x, y] = MID if (x - 47.5) ** 2 + (y - CY) ** 2 <= 26 ** 2 else DARK
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
    if len(piece) > 2: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
for p in [p for p, c in g.items() if c == FOLD[0x161d3c] and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: g[p] = K       # its darkest at the edge is the outline
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
xs, ys = [x for x, y in g], [y for x, y in g]
dx, dy = W // 2 - (min(xs) + max(xs)) // 2, H - 1 - max(ys)
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items(): f.putpixel((x + dx, y + dy), c + (255,))
px = f.load()                                                                               # lone pixels join what surrounds them
for y in range(1, H - 1):
    for x in range(1, W - 1):
        c = px[x, y]
        if not c[3] or c[:3] == K: continue
        near = [px[x + a, y + b] for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
        if not any(n[3] and n[:3] == c[:3] for n in near):
            pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
            if pick: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png')
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
print(f.getbbox(), len(f.getcolors(4096)))
