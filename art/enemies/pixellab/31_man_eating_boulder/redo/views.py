"""31 Man-Eating Boulder frame 0 from concept c1 (the user, 2026-11-03; concepts/, A Book of Creatures): a moss-draped boulder that is mostly mouth. Folded onto the palette as the cast's flat fills -- stone one grey and one shade, moss one green and one
shade, gullet one dark red, fangs one pale, teeth roots tan -- clumps merged, eyes solid marks, one closed outline, on the standard 98x65 frame, bottom on the last row.

    python art/enemies/pixellab/31_man_eating_boulder/redo/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_face_x16.png
"""
from pathlib import Path
from collections import Counter
import colorsys, re
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
W, H = 98, 65
K = (0, 0, 0)
gpl = [tuple(int(v) for v in m.groups()) for m in (re.match(r'\s*(\d+)\s+(\d+)\s+(\d+)', l) for l in (ROOT / 'art/direction/game_palette.gpl').read_text().splitlines()) if m]
def near(c): return min(gpl, key=lambda q: sum((a - b) ** 2 for a, b in zip(q, c)))
STONE, STONE_D, MOSS, MOSS_D, RED, FANG, TAN = near((0x6c, 0x70, 0x80)), (0x34, 0x34, 0x3e), (0x4f, 0xa6, 0x67), (0x2c, 0x6c, 0x44), (0x7c, 0x0a, 0x1b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a)
print(['%02x%02x%02x' % c for c in (STONE, MOSS, MOSS_D)])
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts/c1.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:16])
def fold(p):
    r, g, b = p
    if max(p) < 0x1c: return K
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if 0.14 < h < 0.33 and s > 0.35: return MOSS if v > 0.45 else MOSS_D
    if r > g + 25 and r > b + 8: return FANG if v > 0.8 and s < 0.5 else (TAN if g > 0.6 * r else RED)
    if v > 0.75: return FANG
    return STONE if v > 0.3 else STONE_D
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
    if c in (K, FANG) or len(piece) > 5: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + d[0], a[1] + d[1]) for d in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
GULLET = (0x42, 0x16, 0x18)
inner = [(x, y) for (x, y), c in g.items() if c == K and 22 <= x <= 58 and 30 <= y <= 56 and sum(g.get((x + a, y + b)) == K for a, b in N8) >= 6]
for p in inner: g[p] = GULLET                 # the gullet: the mouth's black is its dark red, a black line kept round the teeth
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
