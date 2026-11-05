"""34 Anaye's battle frames (the user, 2026-11-04: "two axe animations, one where it lifts it in the air, one when it slams it on the ground"). One view in all directions, 130x110 so the raised and slammed axe fit, feet on the last row. Frames: 0 the approved frame;
1 breathing in (idle); 2 axe rising, mask screaming; 3 axe overhead -- the LIFT; 4 axe down on the ground -- the SLAM. PixelLab (pixellab-out/34-redo2-anim, 3 generations; anim.log, action.txt), raw frames PICK, folded onto the approved colours, the blade kept pure lilac and violet.

    python art/enemies/pixellab/34_anaye/redo2/anim/anim.py   # c_N.png, review.png, lift.gif, slam.gif, both.gif; review.lua makes 34_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 130, 110
OX, OY = 15, 22
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (2, 5, 6, 7)
LILAC, VIOLET = (0xb6, 0x9c, 0xee), (0x66, 0x4b, 0x95)
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x14 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(2):
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
            if c == K or len(piece) > 5: continue
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
    drop = H - 1 - max(y for x, y in g)
    g = {(x, y + drop): c for (x, y), c in g.items()}
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'drop', drop)
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
base = Image.new('RGBA', (W, H)); base.paste(FRAME0, (13 - OX, H - FRAME0.height))
fr = [base] + [clean(ps[i]) for i in PICK]
for i, f in enumerate(fr):
    f.save(HERE / f'c_{i}.png')
    px = f.load()
    lil = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == LILAC]
    if lil: print(i, 'blade centre', sum(p[0] for p in lil) // len(lil), sum(p[1] for p in lil) // len(lil), len(lil), 'lowest', max(p[1] for p in lil))
S = 3
rev = Image.new('RGBA', (W * S * 5, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
def gif(seq, name, ms):
    big = []
    for f in seq:
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / name, save_all=True, append_images=big[1:], duration=ms, loop=0)
gif([fr[0], fr[2], fr[3]], 'lift.gif', [300, 200, 700])
gif([fr[3], fr[4], fr[0]], 'slam.gif', [300, 500, 500])
gif([fr[0], fr[1], fr[0], fr[2], fr[3], fr[4]], 'both.gif', [400, 300, 300, 180, 500, 700])
