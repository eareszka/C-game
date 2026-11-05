"""44 Itqiirpak's battle poses, every view, timed to its fire. PixelLab (pixellab-out/44-redo3-anim, 1 generation a view; anim_V.log, action.txt), three poses a view, stepped like the cast at 260 ms: 0 the approved view (idle), 1 tongues moving (idle), 2 mouths wide with tongues out, held as a shot leaves (the front's frame 4 lost its tongue: the user approved frame 2 instead). DL is DR mirrored.
Folded as views8.py: flat flesh, tongues saturated red, mouths and teeth spared from merging. 130x88, the wrist on the last row, each view's later poses placed by its first so the wrist stays put.

    python art/enemies/pixellab/44_itqiirpak/redo3/anim/anim.py   # V_N.png, review.png, 44.gif; review.lua makes 44_review.aseprite
"""
from pathlib import Path
from collections import Counter
import colorsys
from PIL import Image, ImageOps
HERE = Path(__file__).resolve().parent
W, H, MS = 130, 88, 260
K = (0, 0, 0)
PEACH, ROSE, THROAT, RED, CREAM = (0xf0, 0xb8, 0x90), (0xec, 0x84, 0x76), (0x42, 0x16, 0x18), (0xb6, 0x43, 0x3d), (0xe8, 0xe0, 0xc0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
PICK = {'D': (0, 3, 2), 'DR': (0, 2, 4), 'R': (0, 1, 3), 'UR': (0, 2, 4), 'U': (0, 2, 4), 'UL': (0, 2, 3), 'L': (0, 2, 4)}
def fold(p):
    r, g, b = p
    if max(p) < 0x18: return K
    h, s, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if min(p) > 0xc8: return CREAM
    if val < 0.42: return THROAT
    if s > 0.5 and val < 0.9: return RED
    return PEACH if val > 0.85 else ROSE
def grid(path):
    im = Image.open(path).convert('RGBA')
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
    return g
frames = {}
for v, pick in PICK.items():
    ps = [l.strip() for l in (HERE / f'anim_{v}.log').read_text().splitlines() if l.strip().endswith('.png')]
    gs = [grid(ps[i]) for i in pick]
    allx = [x for g in gs for x, y in g]; low = max(y for g in gs for x, y in g)
    dx, dy = W // 2 - (min(allx) + max(allx)) // 2, H - 1 - low
    row = []
    for g in gs:
        xs, ys = [x + dx for x, y in g], [y + dy for x, y in g]
        print(v, 'cols', min(xs), max(xs), 'rows', min(ys), max(ys))
        assert min(xs) >= 1 and max(xs) < W - 1 and min(ys) >= 1, v
        f = Image.new('RGBA', (W, H))
        for (x, y), c in g.items(): f.putpixel((x + dx, y + dy), c + (255,))
        row.append(f)
    frames[v] = row
frames['DL'] = [ImageOps.mirror(f) for f in frames['DR']]
for v, row in frames.items():
    for i, f in enumerate(row): f.save(HERE / f'{v}_{i}.png')
S = 2
rev = Image.new('RGBA', (W * S * 6 + 20, (H * S + 4) * 4), (0, 0, 0, 255))
for n, v in enumerate(ORDER):
    x0, y0 = (n % 2) * (W * S * 3 + 20), (n // 2) * (H * S + 4)
    for i, f in enumerate(frames[v]): rev.alpha_composite(f.resize((W * S, H * S), 0), (x0 + i * W * S, y0))
rev.save(HERE / 'review.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(frames['D'][i]); big.append(bg.resize((W * 3, H * 3), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '44.gif', save_all=True, append_images=big[1:], duration=MS, loop=0)
