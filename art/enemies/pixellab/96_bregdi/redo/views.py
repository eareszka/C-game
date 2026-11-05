"""96 Bregdi frame 0 from concept b4 (the user, 2026-11-03; concepts/, A Book of Creatures): a tall sinister sea beast of Shetland, long drooping fins, gaping mouth, no water. Folded onto the
palette as the cast's flat fills -- hide one green and one shade, belly pale with one shade, mouth dark red and red, teeth pale -- clumps merged, one closed outline, on the standard 98x65 frame.

    python art/enemies/pixellab/96_bregdi/redo/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
HIDE, SHADE, PALE, PALE_D, MOUTH, TOOTH = (0x2c, 0x6c, 0x44), (0x16, 0x36, 0x23), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x7c, 0x0a, 0x1b), (0xfc, 0xfc, 0xfc)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts/b4.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:20])
def fold(p):
    r, g, b = p
    if max(p) < 0x14: return K
    if r > g + 18 and r > b: return MOUTH
    if min(p) > 0xd8: return TOOTH
    if r > 0x90 and g > 0x88: return PALE if r > 0xb8 else PALE_D
    return HIDE if g > 0x48 else SHADE
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
    if c in (K, TOOTH) or len(piece) > 3: continue
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
px = f.load()
for y in range(13, 21):                                       # the eye: one solid 2 px mark in its black socket (concept's ringed eye gone)
    for x in range(34, 42):
        if px[x, y][3] and px[x, y][:3] == MOUTH: px[x, y] = K + (255,)
for x in (37, 38): px[x, 16] = (0xfa, 0xe4, 0x88, 255)
f.save(HERE / 'frame0.png'); print(f.getbbox())
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.crop((10, f.getbbox()[1] - 1, 46, f.getbbox()[1] + 25)).resize((576, 416), 0).save(HERE / 'frame0_head_x16.png')
