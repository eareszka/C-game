"""91 Kurrea redesign's battle poses: PixelLab's ripple of each view (pixellab-out/91-redo2-anim, 5 generations) cut to the game's
standard three poses (the sheet's 0 1 0 2 loop, 400/250/400/250 ms). Views were picked by eye. Each frame on frame 0's colours, flattened,
one outline. Each crystal plate is one flat colour (the user), and holds it across a view's poses: in pose 0 a plate takes its own most
common rainbow colour, in the others the colour of the nearest plate of pose 0. The right view's pose 0 is the approved frame itself.
Left, up-right and down-left mirror R, UL and DR.

    python art/enemies/pixellab/91_kurrea/redo2/anim/anim.py  # writes VIEW_N.png, review.png; review.lua makes the tagged .aseprite
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image, ImageOps
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod
W, H = 98, 65
K = (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BASE = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3] and p[:3] != K})
tidy_mod.SHADE = (0x2b, 0x1f, 0x40)
tidy_mod.KEEP = set()
PICK = {'D': (0, 2, 4), 'DR': (0, 2, 4), 'R': (0, 1, 2), 'UL': (0, 1, 2), 'U': (2, 3, 4)}
LILAC = (0xb6, 0x9c, 0xee)
RAINBOW = [(0xec, 0x84, 0x76), (0xfa, 0xe4, 0x88), (0xa8, 0xf0, 0xbc), (0x84, 0xa7, 0xe9)]
GROUND = 63


def fold(p):
    if max(p) < 0x14: return K
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


def lone(im):
    px = im.load()
    N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] == K: continue
            near = [px[x + a, y + b] for a, b in N8]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3]).most_common(1)
            if pick: px[x, y] = pick[0][0] + (255,)
    return im


def flecks(g):
    """Dark greys that folded to red: small red patches touching only the hide become black lines (gills, eyes)."""
    REDS, GREYS = {(0x53, 0x1b, 0x1c), (0x79, 0x27, 0x27), (0xb6, 0x43, 0x3d)}, {(0x84, 0x86, 0x94), (0x59, 0x59, 0x65)}
    seen = set()
    for p, c in list(g.items()):
        if c not in REDS or p in seen: continue
        piece, todo = {p}, [p]
        while todo:
            a = todo.pop()
            for dx, dy in N4:
                q = (a[0] + dx, a[1] + dy)
                if q not in piece and g.get(q) in REDS: piece.add(q); todo.append(q)
        seen |= piece
        near = {g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K}
        if len(piece) <= 12 and near and near <= GREYS:
            for a in piece: g[a] = K
    return g


def clean(path):
    im = Image.open(path).convert('RGBA')
    g = {(x - 1, y - 1): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = biggest(flat(g))
    g = flecks(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    clipped = [p for p in g if not (0 <= p[0] < W and 0 <= p[1] < H)]
    dy = GROUND - max(y for x, y in g)
    g = {(x, y + dy): c for (x, y), c in g.items()}
    clipped = [p for p in g if not (0 <= p[0] < W and 0 <= p[1] < H)]
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: out.putpixel((x, y), c + (255,))
    if clipped: print(path[-12:], 'clipped', len(clipped))
    return lone(tidy_mod.tidy(out))


def pieces(im):
    """The pastel pieces of a frame that are plates: joined rainbow-and-lilac pixels, at least a third rainbow."""
    px = im.load()
    left = {(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in set(RAINBOW) | {LILAC}}
    out = []
    while left:
        s = left.pop(); piece = [s]; todo = [s]
        while todo:
            x, y = todo.pop()
            for a, b in N4:
                q = (x + a, y + b)
                if q in left: left.discard(q); piece.append(q); todo.append(q)
        n = Counter(px[p][:3] for p in piece if px[p][:3] in RAINBOW)
        if sum(n.values()) * 3 >= len(piece): out.append((piece, n.most_common(1)[0][0]))
    return out


def centre(piece):
    return sum(p[0] for p in piece) / len(piece), sum(p[1] for p in piece) / len(piece)


def lock(fr, first_is_final):
    """One colour a plate, held across the poses."""
    ref = []
    for piece, c in pieces(fr[0]):
        if not first_is_final:
            for p in piece: fr[0].putpixel(p, c + (255,))
        ref.append((centre(piece), c))
    for f in fr[1:]:
        for piece, _ in pieces(f):
            x, y = centre(piece)
            c = min(ref, key=lambda r: (r[0][0] - x) ** 2 + (r[0][1] - y) ** 2)[1]
            for p in piece: f.putpixel(p, c + (255,))


frames = {}
for v, pick in PICK.items():
    ps = [l.strip() for l in (HERE / f'anim{v}.log').read_text().splitlines() if l.strip().endswith('.png')]
    frames[v] = [clean(ps[i]) for i in pick]
frames['R'][0] = BASE.copy()
for v in PICK: lock(frames[v], v == 'R')
frames['UR'] = [ImageOps.mirror(f) for f in frames['UL']]
frames['L'] = [ImageOps.mirror(f) for f in frames['R']]
frames['DL'] = [ImageOps.mirror(f) for f in frames['DR']]
for v, fr in frames.items():
    for i, f in enumerate(fr): f.save(HERE / f'{v}_{i}.png')
    print(v, [f.getbbox() for f in fr])
ORDER = ('D', 'DR', 'R', 'UR', 'U', 'UL', 'L', 'DL')
S, G = 3, (0x6f, 0x9e, 0x5c, 255)
b = Image.new('RGBA', (W * S * 6, H * S * 4), G)
for k, v in enumerate(ORDER):
    for i, f in enumerate(frames[v]):
        b.alpha_composite(f.resize((W * S, H * S), 0), (((k % 2) * 3 + i) * W * S, (k // 2) * H * S))
b.save(HERE / 'review.png')
