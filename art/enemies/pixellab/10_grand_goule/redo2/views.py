"""10 Grand'Goule frame 0 from concept k2 (the user, 2026-11-03; concepts/, the user's description): a tall gaunt gargoyle, hunched, long beak, ribbed chest, arched bat wings. Folded onto the
palette as flat fills -- hide slate blue and navy, beak and ribs bone and tan, wing membrane charcoal, its red turned to an ember rim -- clumps merged, one closed outline, on a 98x65 frame.

    python art/enemies/pixellab/10_grand_goule/redo2/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
HIDE, NAVY, BONE, TAN, CHAR, EMBER, CLAW = (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x34, 0x34, 0x3e), (0xf0, 0xbc, 0x3c), (0xb7, 0x00, 0x00)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EYES = ((43, 24), (44, 24), (49, 24), (50, 24))             # two solid 2 px marks, deep in the head
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts/k2.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:24])
def fold(p, x, y):
    r, g, b = p
    if max(p) < 0x14: return K
    if r > g + 40 and b < g + 30 and g < 0x60:                 # the red: wing membrane charcoal, its top edge an ember; toes keep their red
        return CLAW if y > 50 else CHAR
    if r > 0xb8 and g > 0x90: return BONE
    if r > 0x88 and g > 0x60 and b < g + 8: return TAN
    if r > g + 12 and r > b + 8: return EMBER if y < 26 else TAN  # the horns' orange
    return HIDE if b > 0x60 else NAVY
dx = (W - im.width) // 2
g = {(x + dx, y): fold(im.getpixel((x, y))[:3], x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
for p, c in list(g.items()):                                   # no ember on the face: only the horns' tips and the wing rims carry it
    if c == EMBER: g[p] = TAN
for x in range(W):                                             # the ember rim: the top of each column of membrane, as a line along the wing's upper edge
    ys = [y for y in range(H) if g.get((x, y)) == CHAR]
    if ys: g[x, min(ys)] = EMBER
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
    if c in (K, EMBER, CLAW) or len(piece) > 4: continue
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
for x, y in EYES: px[x, y] = EMBER + (255,)
for _ in range(2):                                             # lone pixels join what surrounds them
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, EMBER, CLAW): continue
            near = [px[x + d[0], y + d[1]] for d in N8]
            if not any(n[3] and n[:3] == c[:3] for n in near):
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                if pick: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png'); print(f.getbbox(), drop)
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.crop((32, 0, 68, 36)).resize((576, 576), 0).save(HERE / 'frame0_head_x16.png')
