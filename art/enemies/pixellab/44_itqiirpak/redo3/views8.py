"""44 Itqiirpak's 8 views (the user, 2026-11-04: "that current frame is its 3/4 front ... use pixellab to make a full 8 directions"). PixelLab's rotation of nothumb/source.png (rot2/, 2 generations; the user: "no mouth on thumb for all frames"). Its labels are off, so assigned by eye: D full front (south-west), DR the three-quarter t1 (south),
R side (south-east), UR back three-quarter (north), U back of the hand (north-east), UL (north-west), L side (west), DL the three-quarter mirrored. Flat colours with the tongues a saturated red kept apart from the flesh, and the mouths and teeth spared from merging. 130x88, wrist on the last row.

    python art/enemies/pixellab/44_itqiirpak/redo3/views8.py   # view_D.png ... view_DL.png, views_board.png (black), views_board_grass.png
"""
from pathlib import Path
from collections import Counter
import colorsys
from PIL import Image, ImageDraw, ImageOps
HERE = Path(__file__).resolve().parent
W, H = 130, 88
K = (0, 0, 0)
PEACH, ROSE, THROAT, RED, CREAM = (0xf0, 0xb8, 0x90), (0xec, 0x84, 0x76), (0x42, 0x16, 0x18), (0xb6, 0x43, 0x3d), (0xe8, 0xe0, 0xc0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
VIEWS = (('D', 'south-west', False), ('DR', 'south', False), ('R', 'south-east', False), ('UR', 'north', False), ('U', 'north-east', False), ('UL', 'north-west', False), ('L', 'west', False), ('DL', 'south', True))
ps = {l.strip().split('v-')[-1].rsplit('-', 1)[0]: l.strip() for l in (HERE / 'rot2/rotate.log').read_text().splitlines() if l.strip().endswith('.png')}
def fold(p):
    r, g, b = p
    v = max(p)
    if v < 0x18: return K
    h, s, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if min(p) > 0xc8: return CREAM
    if val < 0.42: return THROAT
    if s > 0.5 and val < 0.9: return RED                 # tongues and lips
    return PEACH if val > 0.85 else ROSE
def build(key, mirror):
    im = Image.open(ps[key]).convert('RGBA')
    if mirror: im = ImageOps.mirror(im)
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
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
        if c in (K, CREAM, RED, THROAT) or len(piece) > 5: continue
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
    g = {p: g[p] for p in max(pieces, key=len)}
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs)) // 2, H - 1 - max(ys)
    print(key, 'size', max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): f.putpixel((x + dx, y + dy), c + (255,))
    return f
fr = {v: build(k, m) for v, k, m in VIEWS}
for v, f in fr.items(): f.save(HERE / f'view_{v}.png')
for bgc, name in (((0, 0, 0, 255), 'views_board.png'), ((0x6f, 0x9e, 0x5c, 255), 'views_board_grass.png')):
    k = 3
    b = Image.new('RGBA', ((W * k + 6) * 4, (H * k + 18) * 2), bgc); d = ImageDraw.Draw(b)
    for i, (v, _, _) in enumerate(VIEWS):
        x, y = (i % 4) * (W * k + 6), (i // 4) * (H * k + 18)
        b.alpha_composite(fr[v].resize((W * k, H * k), 0), (x, y + 16)); d.text((x + 3, y + 2), v, fill=(255, 255, 255, 255))
    b.save(HERE / name)
