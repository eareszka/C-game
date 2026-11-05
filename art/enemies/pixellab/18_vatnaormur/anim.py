"""18 Vatnaormur's animation, matched to its bullet pattern (the user, 2026-11-02). Its five sheet frames:
    0  rest                          the approved frame
    1  head reared, mouth agape      the breath frame: the gold ring leaves its mouth here (idle frame 1, as before)
    2  mouth closing
    3  spiked body heaved up         shown as a ripple ring leaves its humps (Vatnaormur::anim_frame in src/enemies.cpp)
    4  body settling

PixelLab's spit and heave (pixellab-out/18-anim, two generations) on the frame's own colours, mirrored from the left half
so every frame stays exactly symmetrical. The heave grew stray arms by the head and curled the stalks, so frames 3 and 4
take only its spiked body, under the approved head and neck. Base on the frame's bottom row throughout.

    python art/enemies/pixellab/18_vatnaormur/anim.py     # writes anim/f_N.png, anim_review.png, phase1.gif; prints shot points
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
ANIM = ROOT / 'pixellab-out/18-anim/18/animations'
W, H = 98, 65
MID = 97              # x mirrors to MID - x: frame0 is symmetrical about columns 48 and 49
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BASE = Image.open(HERE / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3]})
NECK = 36             # columns from here to the middle are head and neck: frames 3 and 4 keep the approved ones
BODY_Y = 38           # rows above this are the approved frame's too


def find(name, i):
    return next(ANIM.glob(f'*/{name}-{i:02d}.png'))


def near(p):
    return min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def grid(im):
    return {(x, y): near(im.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if im.getpixel((x, y))[3] > 127}


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
        if c == K or len(piece) > most: continue
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
    edge = {p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    out = dict(body)
    for x, y in body:
        for a, b in N4:
            if (x + a, y + b) not in body: out[x + a, y + b] = K
    return out


def finish(g):
    """Left half mirrored, one outline, the base on the bottom row."""
    left = flat({p: c for p, c in g.items() if p[0] <= MID // 2})      # before the mirror, so both sides stay the same
    both = dict(left)
    for (x, y), c in left.items(): both[MID - x, y] = c
    both = outline(biggest(both))
    drop = H - 1 - max(y for x, y in both)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in both.items():
        if 0 <= x < W and 0 <= y + drop < H: out.putpixel((x, y + drop), c + (255,))
    return out


def body_from(name, i):
    """The heave's spiked body under the approved head and neck."""
    base, h = grid(BASE), grid(Image.open(find(name, i)).convert('RGBA'))
    g = {p: c for p, c in base.items() if p[0] >= NECK or p[1] < BODY_Y}
    g.update({p: c for p, c in h.items() if p[0] < NECK and p[1] >= BODY_Y})
    return g


FRAMES = [BASE.copy(),
          finish(grid(Image.open(find('spit', 2)).convert('RGBA'))),
          finish(grid(Image.open(find('spit', 3)).convert('RGBA'))),
          finish(body_from('heave', 3)),
          finish(body_from('heave', 4))]
(HERE / 'anim').mkdir(exist_ok=True)
for i, f in enumerate(FRAMES): f.save(HERE / 'anim' / f'f_{i}.png')

S, G = 4, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 3, H * S * 2), G)
for i, f in enumerate(FRAMES):
    b.alpha_composite(f.resize((W * S, H * S), 0), ((i % 3) * W * S, (i // 3) * H * S))
    print(i, f.getbbox(), len({p[:3] for p in f.get_flattened_data() if p[3]}) - 1, 'colours + black')
b.save(HERE / 'anim_review.png')

# the shot points, art px on the 98x65 frame
px = FRAMES[1].load()
blk = [(x, y) for y in range(H) for x in range(W) if px[x, y][:3] == K and px[x, y][3] and 20 < y < 45 and 40 <= x <= 56
       and all(px[x + a, y + b][3] for a, b in N4)]
print('mouth centre on frame 1:', sum(x for x, y in blk) / len(blk), sum(y for x, y in blk) / len(blk))
g0 = BASE.load()
for x0, x1 in ((8, 39), (57, 88)):
    ys = [y for x in range(x0, x1) for y in range(H) if g0[x, y][3]]
    print('hump', x0, x1, 'mid x', (x0 + x1) / 2, 'rows', min(ys), max(ys))

# what plays in phase 1: rest, spit, close, rest, then a ripple's heave and settle every 0.9 s
seq = [0, 1, 2, 0, 0, 3, 4, 0]
big = []
for i in seq:
    bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(FRAMES[i])
    big.append(bg.resize((W * 4, H * 4), 0))
big[0].save(HERE / 'phase1.gif', save_all=True, append_images=big[1:], duration=[260, 260, 260, 130, 130, 130, 130, 260], loop=0, disposal=1)
