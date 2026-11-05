"""34 Anaye's battle frames (the user, 2026-11-04: "lift should be several frames of him lifting it up, slam should be him raising slightly then slamming it into the ground"). One view in all directions, 130x118, its feet on one row in every frame.
Frames: 0 the approved frame; 1 breathing, also where the lift starts. LIFT 1-6: the axe rising in steps to overhead, the mask screaming at the top. SLAM 7-13: raises slightly, swings up and over, sweeps down with a pale slash, the blade in the ground, on the same side. PixelLab
(pixellab-out/34-redo2-anim2, 3 generations each; lift.log, slam.log), folded onto the approved colours.

    python art/enemies/pixellab/34_anaye/redo2/anim2/anim.py   # c_N.png, review.png, lift.gif, slam.gif; review.lua makes 34_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 130, 118
OX, OY = 15, 20      # raw canvas to frame: the feet, raw row 130, land on frame row 110
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
LIFT = (1, 2, 3, 4, 5, 6)
SLAM = (1, 2, 3, 5, 6, 7, 8)
LILAC = (0xb6, 0x9c, 0xee)
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
def logged(n): return [l.strip() for l in (HERE / f'{n}.log').read_text().splitlines() if l.strip().endswith('.png')]
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
    keep = max(pieces, key=len)
    for piece in pieces:                 # the slash arc can sit apart from the body: keep any long pale piece
        if piece is not keep and len(piece) >= 20: keep = keep | piece
    g = {p: g[p] for p in keep}
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys))
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
L, S = logged('lift'), logged('slam')
base = Image.new('RGBA', (W, H)); base.paste(FRAME0, (13 - OX, 50 - OY))
fr = [base] + [clean(L[i]) for i in LIFT] + [clean(S[i]) for i in SLAM]
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
for n in (6, 9, 10, 13):
    px = fr[n].load()
    lil = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == LILAC]
    print(n, 'blade', sum(p[0] for p in lil) // max(1, len(lil)), sum(p[1] for p in lil) // max(1, len(lil)), len(lil))
S_ = 2
rev = Image.new('RGBA', (W * S_ * 7, H * S_ * 2), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S_, H * S_), 0), ((i % 7) * W * S_, (i // 7) * H * S_))
rev.save(HERE / 'review.png')
def gif(seq, name, ms):
    big = []
    for f in seq:
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(f); big.append(bg.resize((W * 3, H * 3), 0).convert('P', palette=Image.ADAPTIVE))
    big[0].save(HERE / name, save_all=True, append_images=big[1:], duration=ms, loop=0)
gif([fr[0]] + fr[1:7], 'lift.gif', [300, 150, 150, 150, 150, 150, 700])
gif([fr[0]] + fr[7:14], 'slam.gif', [300, 150, 150, 120, 120, 80, 80, 800])
