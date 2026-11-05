"""83 redo: PixelLab's wrapped-wing blocks (s1, s2) on the battle palette: folded, flattened, one outline, the third
foot added (PixelLab drew two; each of the three fires), lowest row on the fly pose's. s1 also loses two dashes on its
wing that read as a face.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/poses/cocoon/fold.py   # writes block_s1.png block_s2.png board_clean.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import tidy as tidy_mod
W, H, FLOOR = 100, 65, 56
K = (0, 0, 0)
LIGHT, MID, DARK = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)
SALMON, RIB, PALE = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fold(p):
    if max(p) < 0x14: return K
    if max(p) - min(p) < 24: return LIGHT if max(p) >= 0x68 else MID if max(p) >= 0x50 else DARK
    return min((SALMON, RIB, PALE), key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def flat(g, most=3):
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


def make(name, foot_box, foot_dx, wipe=()):
    im = Image.open(HERE / f'{name}.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for p in wipe: g[p] = SALMON
    bottom = max(y for x, y in g)
    x0, x1, y0 = foot_box
    for (x, y), c in [(p, c) for p, c in g.items() if x0 <= p[0] <= x1 and p[1] >= y0]:
        g.setdefault((x + foot_dx, y), c)               # behind the hem: only where nothing is drawn
    g = flat(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    drop = FLOOR - max(y for x, y in g)
    xs = [x for x, y in g]
    dx = 50 - (min(xs) + max(xs) + 1) // 2
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + drop), c + (255,))
    tidy_mod.tidy(out)
    out.save(HERE / f'block_{name}.png')
    print(name, 'bottom was', bottom, 'bbox', out.getbbox())
    return out


DASHES = [(x, y) for x in range(44, 58) for y in range(22, 28)]
s1 = make('s1', (36, 45, 56), 10, DASHES)
s2 = make('s2', (40, 49, 56), 9)
S = 7
b = Image.new('RGBA', (W * S * 2, H * S), (0x6f, 0x9e, 0x5c, 255))
for i, im in enumerate((s1, s2)): b.alpha_composite(im.resize((W * S, H * S), 0), (i * W * S, 0))
b.save(HERE / 'board_clean.png')
