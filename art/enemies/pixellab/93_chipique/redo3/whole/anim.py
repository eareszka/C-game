"""93 Chipique's whole-sprite idle (the user, 2026-11-03: accepted the cleaned tail, "animate it using pixellab the whole sprite and the boat creature").
PixelLab's 16 frames of redo3/clean/c4_clean.png (pixellab-out/93-redo3-whole, 2 generations; see anim.log, action.txt). Unlike redo3/long nothing is
locked: serpent, canoe, paddle and rider all move as PixelLab drew them. Each frame folds onto the cleaned frame's colours, clumps of 2 px or fewer
merge, PixelLab's crumbs go (loose blood kept), one outline. Every other frame gives 8 poses at the game's default 260 ms, choppy like the rest.

    python art/enemies/pixellab/93_chipique/redo3/whole/anim.py   # c_N.png, review.png, whole.gif; whole.lua makes 93_whole_review.aseprite
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod
W, H, MS = 98, 65, 260
K, RED = (0, 0, 0), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
BASE = Image.open(HERE.parent / 'clean/c4_clean.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3] and p[:3] != K})
tidy_mod.SHADE = (0x2b, 0x1f, 0x40)
tidy_mod.KEEP = {RED}
PICK = (0, 2, 4, 6, 8, 10, 12, 14)


def fold(p):
    return K if max(p) < 0x1c else min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def flat(g, most=2):
    seen, out = set(), dict(g)
    for p, c in g.items():
        if p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
        seen |= piece
        if c in (K, RED) or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def keep(g):
    left, out, pieces = set(g), {}, []
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for dx, dy in N8:
                q = (a[0] + dx, a[1] + dy)
                if q in left: left.discard(q); todo.append(q)
        pieces.append(piece)
    big = max(pieces, key=len)
    for piece in pieces:
        if piece is big or any(g[p] == RED for p in piece): out.update({p: g[p] for p in piece})
    return out


def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - 1, y - 1): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = keep(flat(g))
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: out.putpixel((x, y), c + (255,))
    tidy_mod.tidy(out)
    px = out.load()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, RED): continue
            near = [px[x + a, y + b] for a, b in N8]
            if not any(n[3] and n[:3] == c[:3] for n in near):
                pick = Counter(n[:3] for n in near if n[3]).most_common(1)
                if pick: px[x, y] = pick[0][0] + (255,)
    return out


ps = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
print(len(ps), 'raw frames')
fr = [clean(ps[i]) for i in PICK]
for i, f in enumerate(fr): f.save(HERE / f'c_{i}.png')
print([f.getbbox() for f in fr])
S, G = 4, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 4, H * S * 2), G)
for k, f in enumerate(fr): b.alpha_composite(f.resize((W * S, H * S), 0), ((k % 4) * W * S, (k // 4) * H * S))
b.save(HERE / 'review.png')
big = []
for f in fr:
    bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / 'whole.gif', save_all=True, append_images=big[1:], duration=MS, loop=0)
