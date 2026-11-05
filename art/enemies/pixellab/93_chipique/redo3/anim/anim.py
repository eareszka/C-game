"""93 Chipique's battle poses (the user, 2026-11-03: "no rotations for this enemy just head turning"): one fixed body, the approved frame's coil,
canoe, figure and tail, in every direction; only PixelLab's neck and head (pixellab-out/93-redo3-anim, 5 generations) go on top, three poses a
direction on the sheet's 0 1 0 2 loop. PixelLab would not draw the head turned away, so the up directions reuse the nearest: UL = L, UR = R, U = D.

    python art/enemies/pixellab/93_chipique/redo3/anim/anim.py  # writes VIEW_N.png, review.png; review.lua makes the tagged .aseprite
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod
W, H = 98, 65
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BASE = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3] and p[:3] != K})
RED = (0xb6, 0x43, 0x3d)
tidy_mod.SHADE = (0x2b, 0x1f, 0x40)
tidy_mod.KEEP = {RED}
PICK = {'L': (0, 2, 3), 'DL': (0, 2, 3), 'D': (0, 2, 3), 'DR': (0, 2, 3), 'R': (0, 2, 3)}
NECK = lambda x, y: (x < 52 and y < 40) or y < 24      # what the head and neck may touch, frame coordinates; below and right, the body


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


def lone(im):
    px = im.load()
    N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, RED): continue
            near = [px[x + a, y + b] for a, b in N8]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3]).most_common(1)
            if pick: px[x, y] = pick[0][0] + (255,)
    return im


BODY = {(x, y): BASE.getpixel((x, y))[:3] for y in range(H) for x in range(W) if BASE.getpixel((x, y))[3] and not NECK(x, y)}


def clean(path):
    im = Image.open(path).convert('RGBA')
    top = {(x - 1, y - 1): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = dict(BODY)
    for p, c in flat(top).items():
        if NECK(*p): g[p] = c
    g = biggest(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: out.putpixel((x, y), c + (255,))
    tidy_mod.tidy(out)
    for p, c in BODY.items():                    # the body stays exactly the approved frame
        if c != K: out.putpixel(p, c + (255,))
    return lone(out)


frames = {}
for v, pick in PICK.items():
    ps = [l.strip() for l in (HERE / f'anim{v}.log').read_text().splitlines() if l.strip().endswith('.png')]
    frames[v] = [clean(ps[i]) for i in pick]
frames['L'][0] = BASE
frames['UL'], frames['UR'], frames['U'] = frames['L'], frames['R'], frames['D']
for v, fr in frames.items():
    for i, f in enumerate(fr): f.save(HERE / f'{v}_{i}.png')
    print(v, [f.getbbox() for f in fr])
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
S, G = 3, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 6, H * S * 3), G)
for k, v in enumerate(('L', 'DL', 'D', 'DR', 'R')):
    for i, f in enumerate(frames[v]):
        b.alpha_composite(f.resize((W * S, H * S), 0), (((k % 2) * 3 + i) * W * S, (k // 2) * H * S))
b.save(HERE / 'review.png')
