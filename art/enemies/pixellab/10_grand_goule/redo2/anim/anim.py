"""10 Grand'Goule's idle, timed to its fire (the user, 2026-11-03: "make sure its animation match its bullets spawning"). 3 poses in the default 0 1 0 2 loop, one view in all directions:
0 the approved frame; 1 its head drawn back, beak shut, the wind-up; 2 the beak gaping, gullet red -- the frame its ring leaves on (Enemy::breathe, breath_frame 2). PixelLab (pixellab-out/10-redo2-anim,
2 generations; anim.log, action.txt), frames PICK. PixelLab drew flames over the jaw: they become jaw, the game's fireballs being the fire. MOUTH is where shots leave, per pose; marked in spawn.png.

    python art/enemies/pixellab/10_grand_goule/redo2/anim/anim.py   # c_N.png, review.png, spawn.png, 10.gif; review.lua makes 10_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 65, 260
OX, OY = 1, 17
K, RED = (0, 0, 0), (0xb7, 0x00, 0x00)
HIDE, NAVY, BONE, TAN, CHAR, EMBER = (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a), (0x34, 0x34, 0x3e), (0xf0, 0xbc, 0x3c)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (3, 5)
MOUTH = ((41, 38), (31, 25), (38, 31))        # (frame x, y) of the beak tip or gullet in poses 0, 1, 2
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = (HIDE, NAVY, BONE, TAN, CHAR, EMBER, RED)
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x18 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path, gape):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    if gape:                                 # the flame over the lower jaw is jaw again; the wing rims keep their ember
        for (x, y), c in list(g.items()):
            if x < 42 and 26 <= y <= 46 and c in (EMBER, BONE): g[x, y] = TAN
    for _ in range(3):
        for (x, y), c in list(g.items()):
            if c in (K, RED, EMBER): continue
            near = [g.get((x + a, y + b)) for a, b in N8]
            if c not in near:
                pick = Counter(n for n in near if n and n != K).most_common(1)
                if pick: g[x, y] = pick[0][0]
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
    drop = H - 1 - max(y for x, y in g)        # feet on the last row in every pose, or they would jitter
    g = {(x, y + drop): c for (x, y), c in g.items()}
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'drop', drop)
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
fr = [FRAME0] + [clean(ps[PICK[0]], False), clean(ps[PICK[1]], True)]
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
sp = rev.copy()
for i, (mx, my) in enumerate(MOUTH):
    for a in range(-3, 4):
        for b in range(-3, 4):
            if abs(a) == 3 or abs(b) == 3: sp.putpixel((i * W * S + mx * S + a + 2, my * S + b + 2), (255, 255, 255, 255))
sp.save(HERE / 'spawn.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '10.gif', save_all=True, append_images=big[1:], duration=[400, 250, 400, 250], loop=0)
