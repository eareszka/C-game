"""34 Anaye: every returned lift and slam frame onto frame 0's colours, on the 130x118 frame (redo2/anim2/anim.py's clean, feet raw row 130 -> frame row 110).

    python art/enemies/pixellab/34_anaye/redo_bc/anim/clean.py    # lift_N.png, slam_N.png, contact.png
"""
import json
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
W, H = 130, 118
OX, OY = 15, 20
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
FRAME0 = Image.open(HERE.parent / 'idle_frame0_clean.png').convert('RGBA')
PAL = sorted({p[:3] for p in FRAME0.get_flattened_data() if p[3] and p[:3] != K})
SPARE = {(0x05, 0x8f, 0x3a)}    # the gem and crest bands stay, however small


def fold(p):
    return K if max(p) < 0x14 else min(PAL, key=lambda c: sum((a - v) ** 2 for a, v in zip(c, p)))


def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - OX, y - OY): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(2):       # patches of 5 or fewer take the colour round them
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
            if c == K or c in SPARE or len(piece) > 5: continue
            n = Counter(g[q] for a in piece for q in ((a[0] + d[0], a[1] + d[1]) for d in N4) if q in g and q not in piece and g[q] != K)
            if n:
                for a in piece: out[a] = n.most_common(1)[0][0]
        g = out
    left, pieces = set(g), []
    while left:              # loose islands go, a long pale slash stays
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for d in N8:
                q = (a[0] + d[0], a[1] + d[1])
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    keep = max(pieces, key=len)
    for piece in pieces:
        if piece is not keep and len(piece) >= 20: keep = keep | piece
    g = {p: g[p] for p in keep}
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):     # a one-pixel black outline all round
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    f = Image.new('RGBA', (W, H))
    clipped = 0
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: f.putpixel((x, y), c + (255,))
        else: clipped += 1
    return f, clipped


S = 2
rows = []
for n in ('lift', 'slam'):
    files = [p for p in json.loads((HERE / f'{n}-result.json').read_text(encoding='utf-8'))['files'] if p.lower().endswith('.png')]
    row = []
    for i, p in enumerate(files):
        f, clipped = clean(p)
        f.save(HERE / f'{n}_{i}.png')
        print(n, i, 'bbox', f.getbbox(), 'clipped', clipped)
        row.append(f)
    rows.append((n, row))
cols = max(len(r) for _, r in rows)
sheet = Image.new('RGBA', (cols * W * S, len(rows) * (H * S + 12)), (0, 0, 0, 255))
d = ImageDraw.Draw(sheet)
for r, (n, row) in enumerate(rows):
    y = r * (H * S + 12)
    for c, f in enumerate(row):
        d.text((c * W * S + 4, y), f'{n} {c}', fill=(255, 255, 255, 255))
        sheet.alpha_composite(f.resize((W * S, H * S), 0), (c * W * S, y + 12))
sheet.save(HERE / 'contact.png')
