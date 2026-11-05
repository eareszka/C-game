"""29 Karnabo frame 0 from concept c2 (the user, 2026-11-03; concepts/, A Book of Creatures): the near-human bogey of a sealed slate quarry, a stooped pale green figure in a huge slate robe, a trunk of a nose to its chest. Folded onto the
palette as the cast's flat fills -- skin mint and one green shade, robe slate and one darker shade, eyes a solid yellow 2 px -- clumps merged, one closed outline, on the standard 98x65 frame, its hem on the last row.

    python art/enemies/pixellab/29_karnabo/redo/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
SKIN, SKIN_D, ROBE, ROBE_D, EYE = (0xa8, 0xf0, 0xbc), (0x4f, 0xa6, 0x67), (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e), (0xf0, 0xbc, 0x3c)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts/c2.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:14])
def fold(p):
    r, g, b = p
    if max(p) < 0x18: return K
    if g > r + 6 and g > b + 6: return SKIN if g > 0xb0 else SKIN_D      # the skin's greens
    if r > 0xd0 and g > 0xb0 and b < 0x90: return EYE
    if min(p) > 0xb8: return SKIN                                        # its pale highlights
    return ROBE if max(p) > 0x58 else ROBE_D
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
    if c in (K, EYE) or len(piece) > 6: continue
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
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
bb = f.getbbox(); bg.crop((bb[0] + 15, bb[1], bb[0] + 51, bb[1] + 36)).resize((576, 576), 0).save(HERE / 'frame0_head_x16.png')
