"""89 Cuero's ripple (approved frame, the user 2026-11-02): PixelLab's animation of it (pixellab-out/89-flop/89/animations/v1,
1 generation) on the frame's own colours, pixel by pixel to the nearest. Five frames, as its sheet has; frame 2 the heave
(its old sheet's "frame 2 heaves up, claws flared"), frame 0 the approved frame itself. Its base stays on the frame's
bottom row, no sliding. PixelLab shut its eyes on frame 4: sockets and marks put back.

    python art/enemies/pixellab/89_cuero/anim.py     # writes anim/ripple_N.png, anim_review.png, ripple.gif
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
SRC = ROOT / 'pixellab-out/89-flop/89/animations/v1'
W, H = 98, 65
K = (0, 0, 0)
EYE = (0xfc, 0x74, 0xb4)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BASE = Image.open(HERE / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3]})
SHUT = {4: ((45, 20), (54, 20))}     # frame: where each shut eye's lid sits, source coordinates, by eye


def near(p):
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
        if c == K or c == EYE or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def biggest(g):
    left, best = set(g), set()
    while left:
        piece, todo = set(), [left.pop()]
        while todo:
            a = todo.pop(); piece.add(a)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (a[0] + dx, a[1] + dy)
                    if q in left: left.discard(q); todo.append(q)
        if len(piece) > len(best): best = piece
    return {p: g[p] for p in best}


def outline(g):
    edge = {p for p, c in g.items() if c == K and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    out = dict(body)
    for x, y in body:
        for dx, dy in N4:
            if (x + dx, y + dy) not in body: out[x + dx, y + dy] = K
    return out


def frame(i):
    if i == 0: return BASE.copy()
    im = Image.open(SRC / f'ripple-{i:02d}.png').convert('RGBA')
    g = {(x, y): near(im.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if im.getpixel((x, y))[3] > 127}
    g = outline(flat(biggest(g)))
    for cx, cy in SHUT.get(i, ()):
        for x in range(cx - 2, cx + 2):
            for y in range(cy - 1, cy + 2): g[x, y] = K
        g[cx - 1, cy] = g[cx, cy] = EYE
    drop = H - 1 - max(y for x, y in g)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= y + drop < H and 0 <= x < W: out.putpixel((x, y + drop), c + (255,))
    return out


FRAMES = [frame(i) for i in range(5)]
(HERE / 'anim').mkdir(exist_ok=True)
for i, f in enumerate(FRAMES): f.save(HERE / 'anim' / f'ripple_{i}.png')
S, GREEN = 4, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 3, H * S * 2), GREEN)
for i, f in enumerate(FRAMES):
    b.alpha_composite(f.resize((W * S, H * S), 0), ((i % 3) * W * S, (i // 3) * H * S))
    print(i, f.getbbox(), len({p[:3] for p in f.get_flattened_data() if p[3]}) - 1, 'colours + black')
b.save(HERE / 'anim_review.png')
big = []
for f in FRAMES:
    bg = Image.new('RGBA', (W, H), GREEN); bg.alpha_composite(f)
    big.append(bg.resize((W * 4, H * 4), 0))
big[0].save(HERE / 'ripple.gif', save_all=True, append_images=big[1:], duration=250, loop=0, disposal=1)
