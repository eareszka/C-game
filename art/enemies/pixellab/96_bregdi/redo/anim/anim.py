"""96 Bregdi's idle: 3 poses (the user: "3 frame animation"), one view in every direction. PixelLab's move of the approved frame (pixellab-out/96-redo-anim, 2 generations; anim.log,
action.txt): its long fins sweep out and up, its jaws work, its tail curls. Pose 0 is the approved frame itself; 1 and 2 are raw frames PICK, folded onto the approved colours, flecks merged, one
outline. 98x72, not the standard 98x65: the raised fins need the rows. In the default 0 1 0 2 loop, 260 ms a step.

    python art/enemies/pixellab/95_wendigo/anim/anim.py   # c_N.png, review.png, 96.gif; review.lua makes 96_review.aseprite
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H, MS = 98, 72, 260
OX, OY = 1, 13            # raw canvas -> frame: input pasted at (1, 20), the art 7 rows lower in the taller frame
K, RED = (0, 0, 0), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
PICK = (2, 3)
FRAME0 = Image.open(HERE.parent / "frame0.png").convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
def fold(p):
    return K if max(p) < 0x1c else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))
def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(3):
        for (x, y), c in list(g.items()):
            if c in (K, RED): continue
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
    big = max(pieces, key=len)
    g = {p: g[p] for p in big}
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    print('cols', min(xs), max(xs), 'rows', min(ys), max(ys), 'reds', sum(c == RED for c in g.values()))
    f = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
    return f
base = Image.new('RGBA', (W, H)); base.paste(FRAME0, (0, 7))
fr = [base] + [clean(ps[i]) for i in PICK]
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
S = 4
rev = Image.new('RGBA', (W * S * 3, H * S), (0, 0, 0, 255))
for i, f in enumerate(fr): rev.alpha_composite(f.resize((W * S, H * S), 0), (i * W * S, 0))
rev.save(HERE / 'review.png')
big = []
for i in (0, 1, 0, 2):
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255)); bg.alpha_composite(fr[i]); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / '96.gif', save_all=True, append_images=big[1:], duration=MS, loop=0)
