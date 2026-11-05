"""44 Itqiirpak frame 0 from PixelLab's edit t1 (the user, 2026-11-04: from a reference photo, "every fingertip is a mouth with tongues"; tips/). Folded onto the palette as flat fills on the giant 130x81 frame: flesh peach and rose with one dark fold, mouths dark red and crimson, tongues red, teeth cream.
Clumps merged, one closed outline, the wrist on the last row.

    python art/enemies/pixellab/44_itqiirpak/redo3/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 130, 81
K = (0, 0, 0)
PEACH, ROSE, FOLD, THROAT, CRIMSON, TONGUE, CREAM = (0xf0, 0xb8, 0x90), (0xec, 0x84, 0x76), (0x79, 0x27, 0x27), (0x42, 0x16, 0x18), (0x7c, 0x0a, 0x1b), (0xb6, 0x43, 0x3d), (0xe8, 0xe0, 0xc0)
PAL = (PEACH, ROSE, FOLD, THROAT, CRIMSON, TONGUE, CREAM)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'tips/t1.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:14])
def fold(p):
    return K if max(p) < 0x18 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
dx = (W - im.width) // 2
g = {(x + dx, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
seen, out = set(), dict(g)
for p, c in g.items():
    if p in seen: continue
    piece, todo = {p}, [p]
    while todo:
        a = todo.pop()
        for d in N4:
            q = (a[0] + d[0], a[1] + d[1])
            if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
    seen |= piece
    if c in (K, CREAM) or len(piece) > 3: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + d[0], a[1] + d[1]) for d in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
left, pieces = set(g), []
while left:
    piece, todo = set(), [left.pop()]
    while todo:
        a = todo.pop(); piece.add(a)
        for d in N8:
            q = (a[0] + d[0], a[1] + d[1])
            if q in left: left.discard(q); todo.append(q)
    pieces.append(piece)
print('pieces', sorted(map(len, pieces), reverse=True)[:6])
g = {p: g[p] for p in max(pieces, key=len)}
for p in [p for p, c in g.items() if c == K and any((p[0] + d[0], p[1] + d[1]) not in g for d in N4)]: del g[p]
for x, y in list(g):
    for d in N4:
        if (x + d[0], y + d[1]) not in g: g[x + d[0], y + d[1]] = K
drop = H - 1 - max(y for x, y in g)
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y + drop < H: f.putpixel((x, y + drop), c + (255,))
f.save(HERE / 'frame0.png'); print(f.getbbox(), drop)
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 6, H * 6), 0).save(HERE / name)
