"""83 Beast of Barrisdale's block (the user, 2026-11-02, picked pose A: wings folded forward over it): the sheet played while it
hangs and catches shots. Five frames across its 2.0 s hang, each 0.4 s:
    0  wings sweeping forward   the tell (it starts catching at 0.35 s)
    1-3 braced, wings trembling the catch
    4  wings sweeping open      about to fly
The sweep frames are the fly sheet's own wings-low frame (PixelLab's sweep squashed the body). PixelLab's brace (pixellab-out/83-block/83b) on the fly sheet's colours, pixel for pixel to the nearest, clumps of 2 px
merged, one black outline, its lowest pixel on the fly sheet's own row so it does not jump. Faces left as its fly sheet does.

    python art/enemies/pixellab/83_beast_of_barrisdale/block/anim.py   # writes f_N.png, anim_review.png, block.gif
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[4]
OUT = ROOT / 'pixellab-out/83-block/83b'
FLY = Image.open(ROOT / 'assets/enemies/83_beast_of_barrisdale_fly.png').convert('RGBA').crop((0, 0, 100, 65))
PAL = sorted({p[:3] for p in FLY.get_flattened_data() if p[3]})
GROUND = FLY.getbbox()[3] - 1
W, H = 100, 65
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


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
        if c == K or c == (0xfc, 0xfc, 0xfc) or p[0] < 34 and p[1] > 34 or len(piece) > most: continue   # teeth and the mouth spared
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


def frame(path):
    im = Image.open(path).convert('RGBA')
    g = {(x, y): near(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = outline(biggest(flat(g)))
    drop = GROUND - max(y for x, y in g)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y + drop < H: out.putpixel((x, y + drop), c + (255,))
    return out


def find(name):
    return next(OUT.rglob(name))


WINGS_DOWN = Image.open(ROOT / 'assets/enemies/83_beast_of_barrisdale_fly.png').convert('RGBA').crop((800, 0, 900, 65))   # the fly sheet's own wings-low frame
FRAMES = [WINGS_DOWN, frame(find('brace-00.png')), frame(find('brace-02.png')), frame(find('brace-04.png')), WINGS_DOWN]
for i, f in enumerate(FRAMES): f.save(HERE / f'f_{i}.png')
S, G = 4, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 3, H * S * 2), G)
for i, f in enumerate(FRAMES):
    b.alpha_composite(f.resize((W * S, H * S), 0), ((i % 3) * W * S, (i // 3) * H * S))
    print(i, f.getbbox(), len({p[:3] for p in f.get_flattened_data() if p[3]}) - 1, 'colours + black')
b.save(HERE / 'anim_review.png')
seq = [FLY] + FRAMES + [FLY]
big = []
for f in seq:
    bg = Image.new('RGBA', (W, H), G); bg.alpha_composite(f)
    big.append(bg.resize((W * 4, H * 4), 0))
big[0].save(HERE / 'block.gif', save_all=True, append_images=big[1:], duration=[400, 400, 400, 400, 400, 400, 400], loop=0, disposal=1)
