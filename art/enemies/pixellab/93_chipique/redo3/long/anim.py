"""93 Chipique's long idle (the user, 2026-11-03: "no head turning or body turning just long conveying animation"): PixelLab's 16-frame loop of the
approved frame (pixellab-out/93-redo3-long, 2 generations): its neck rising and sinking over the canoe, drips falling one after another, its tail
curling. Frame 0 is the approved frame itself. Colours fold onto frame 0's, flattened, one outline, loose blood drops kept; the coil and canoe's lower
rows stay exactly the approved frame, so only what should move moves. One view in all 8 rows of the sheet, 150 ms a frame, a 2.4 s loop.

    python art/enemies/pixellab/93_chipique/redo3/long/anim.py   # writes f_N.png, review.png, long.gif; long.lua makes 93_long_review.aseprite
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod
W, H, FIXED_FROM = 98, 65, 50
K = (0, 0, 0)
RED = (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
BASE = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3] and p[:3] != K})
tidy_mod.SHADE = (0x2b, 0x1f, 0x40)
tidy_mod.KEEP = {RED}


def fold(p):
    if max(p) < 0x1c: return K
    return min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


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
    """The creature, and any loose piece with blood in it: PixelLab's other crumbs go."""
    left, out = set(g), {}
    pieces = []
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
        if piece is big or any(g[p] == RED for p in piece):
            out.update({p: g[p] for p in piece})
    return out


def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - 1, y - 1): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = {p: c for p, c in flat(g).items() if p[1] < FIXED_FROM}
    for y in range(FIXED_FROM, H):
        for x in range(W):
            c = BASE.getpixel((x, y))
            if c[3]: g[x, y] = c[:3]
    g = keep(g)
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
fr = [BASE] + [clean(p) for p in ps[1:16]]
for i, f in enumerate(fr):
    f.save(HERE / f'f_{i}.png')
print([f.getbbox() for f in fr[::5]])
S, G = 2, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 4, H * S * 4), G)
for i, f in enumerate(fr): b.alpha_composite(f.resize((W * S, H * S), 0), ((i % 4) * W * S, (i // 4) * H * S))
b.save(HERE / 'review.png')
big = []
for f in fr:
    bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(f); big.append(bg.resize((W * 4, H * 4), 0).convert('P', palette=Image.ADAPTIVE))
big[0].save(HERE / 'long.gif', save_all=True, append_images=big[1:], duration=150, loop=0)
