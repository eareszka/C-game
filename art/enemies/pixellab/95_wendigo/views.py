"""95 Wendigo frame 0, from PixelLab's concept d4 (concepts2/, the user's description, 2026-11-03): an eldritch bone guardian, skull face with crimson eyes, huge spiked arms, dead-tree
horns, dark tar strands. Colours fold onto the palette as the cast's flat fills -- skull pale bone, limbs tan with one shade, horns grey, tar navy, eyes crimson -- small clumps merged, crumbs
gone, one closed black outline, on the standard 98x65 frame, feet on the last row.

    python art/enemies/pixellab/95_wendigo/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
PALE, TAN, DKT, GREY, TAR, RED = (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x78, 0x58, 0x30), (0x84, 0x86, 0x94), (0x37, 0x38, 0x7b), (0xb6, 0x43, 0x3d)
DK2 = (0x46, 0x34, 0x22)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts2/d4.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:26])
def fold(p):
    r, g, b = p
    if max(p) < 0x1c: return K
    if r > g + 40 and r > b + 20: return RED
    if b > r + 10: return TAR
    if max(p) - min(p) < 12 and max(p) >= 0x50: return GREY     # the horns
    if r > 0xc8: return PALE
    if r > 0x70: return TAN
    return DKT if r > 0x50 else DK2                              # what PixelLab drew near-black is a shade, not a gap: black would float the limbs on the battle's black
dx, dy = (W - im.width) // 2, 0
g = {(x + dx, y + dy): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
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
    if c in (K, RED) or len(piece) > 2: continue
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
big = max(pieces, key=len); print('pieces', sorted(map(len, pieces), reverse=True)[:8])
g = {p: g[p] for p in big}
for p in [p for p, c in g.items() if c == K and any((p[0] + d[0], p[1] + d[1]) not in g for d in N4)]: del g[p]
for x, y in list(g):
    for d in N4:
        if (x + d[0], y + d[1]) not in g: g[x + d[0], y + d[1]] = K
drop = H - 1 - max(y for x, y in g)
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y + drop < H: f.putpixel((x, y + drop), c + (255,))
px = f.load()
TOP = lambda x, y: y < 21 and not 40 <= x <= 56                 # the dead-tree horns, one colour with a shade only by the fold's grey
for y in range(H):
    for x in range(W):
        c = px[x, y]
        if c[3] and c[:3] in (DK2, DKT, TAN) and TOP(x, y): px[x, y] = GREY + (255,)
        if c[3] and c[:3] == TAR and (x < 30 or x > 66): px[x, y] = DKT + (255,)      # blue flecks out on the arms
reds = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == RED and 36 <= x <= 56]
print('eye pixels', reds)
row = round(sum(y for x, y in reds) / len(reds))
for x, y in [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == RED]: px[x, y] = K + (255,)
for x in (42, 43, 48, 49): px[x, row] = RED + (255,)             # each eye one solid 2 px mark in its black socket
for _ in range(2):
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, RED): continue
            near = [px[x + d[0], y + d[1]] for d in N8]
            if not any(n[3] and n[:3] == c[:3] for n in near):
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                if pick: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png'); print(f.getbbox())
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.crop((30, 5, 66, 41)).resize((576, 576), 0).save(HERE / 'frame0_head_x16.png')
