"""13 Beast of the Charred Forests' idle, timed to its fire (the user: animation should match its bullets). One view in all directions. 0 the approved frame, jaws open; 1 head drawn up, jaws half shut, breathing in; 2 reared, ember ring
round its neck, jaws wide -- shown as a shot leaves. PixelLab (pixellab-out/13-redo-anim, 2 generations; anim.log, action.txt), frames PICK, folded onto the old colours. PixelLab's eye marks are painted out: it has no eyes (the user).
98x68, taller than 65 for the reared head. Feet on the last row. Gullets for the fight: (47, 53) (48, 44) (48, 43).

    python art/enemies/pixellab/13_beast_of_the_charred_forests/redo/anim/anim.py   # c_N.png, review.png, 13.gif; review.lua makes 13_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 68, 260
OX, OY = -3, 11              # raw canvas to frame, before feet are set on the last row
K, COAL, CHAR, EMBER, WHITE = (0, 0, 0), (0x59, 0x59, 0x65), (0x28, 0x28, 0x28), (0xfc, 0x98, 0x38), (0xfc, 0xfc, 0xfc)
PAL = (COAL, CHAR, EMBER, WHITE)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (3, 5)
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x18 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    ember = [p for p, c in g.items() if c == EMBER and 34 <= p[0] <= 64]
    mouth_top = min(p[1] for p in ember)
    for p, c in list(g.items()):             # no eyes: white on the head, above the jaws, is coal
        if c == WHITE and p[1] < mouth_top + 2 and 34 <= p[0] <= 64: g[p] = COAL
    for _ in range(3):
        for (x, y), c in list(g.items()):
            if c in (K, EMBER, WHITE): continue
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
    drop = H - 1 - max(y for x, y in g)
    g = {(x, y + drop): c for (x, y), c in g.items()}
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'drop', drop)
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
base = Image.new('RGBA', (W, H)); base.paste(FRAME0, (0, 3))
fr = [base] + [clean(ps[PICK[0]]), clean(ps[PICK[1]])]
for i, f in enumerate(fr):
    f.save(HERE / f'c_{i}.png')
    px = f.load()
    pts = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == EMBER and 38 <= x <= 60 and y >= 40]
    print(i, 'gullet', sum(p[0] for p in pts) // max(1, len(pts)), sum(p[1] for p in pts) // max(1, len(pts)), len(pts))
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '13.gif', save_all=True, append_images=big[1:], duration=[400, 250, 400, 250], loop=0)
