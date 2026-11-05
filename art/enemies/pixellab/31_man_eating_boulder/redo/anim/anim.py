"""31 Man-Eating Boulder's idle, timed to its fire. One view in all directions. 0 the approved frame, jaws open; 1 jaws shut to a grim line; 2 the top rearing back, jaws as wide as they go -- shown as a shot
leaves its gullet. PixelLab (pixellab-out/31-redo-anim, 3 generations; anim.log, action.txt), frames PICK, folded onto the approved colours, feet on the last row, one outline. Idle loop 0 1 0 1; the fight forces pose 2 at each shot.

    python art/enemies/pixellab/31_man_eating_boulder/redo/anim/anim.py   # c_N.png, review.png, spawn.png, 31.gif; review.lua makes 31_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 65, 260
OX, OY = 17, 34
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (4, 7)
MOUTH = (36, 42)          # pose 2: the middle of the gullet, frame pixels
FRAME0 = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x14 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(3):
        for (x, y), c in list(g.items()):
            if c == K or c == (0xe8, 0xe0, 0xc0): continue
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
fr = [FRAME0, clean(ps[PICK[0]]), clean(ps[PICK[1]])]
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
sp = rev.copy()
for a in range(-3, 4):
    for b in range(-3, 4):
        if abs(a) == 3 or abs(b) == 3: sp.putpixel((2 * W * S + MOUTH[0] * S + a + 2, MOUTH[1] * S + b + 2), (255, 255, 255, 255))
sp.save(HERE / 'spawn.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '31.gif', save_all=True, append_images=big[1:], duration=[400, 250, 400, 250], loop=0)
