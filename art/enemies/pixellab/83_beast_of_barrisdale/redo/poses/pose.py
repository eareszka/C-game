"""83 redo: the two airborne key poses from PixelLab's edits of the approved frame0_tilt.png, each with that frame's
exact head and colours.
  fly    f2, wings up. Its tail spike goes (the design has no tail); its hidden front leg is drawn back in so three feet
         show (each fires a talon drop).
  block  b1's folded wing as the near shield. Its two raised wings go (it drew three) and the shield, darkened and
         moved up and forward, is the far wing behind it (wings folded forward, the user's pick). Lifted so its feet
         hang on the fly pose's lowest row and the sheets do not jump.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/poses/pose.py  # writes fly.png block.png board_clean.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import tidy as tidy_mod
W, H = 100, 65
K = (0, 0, 0)
LIGHT, MID, DARK = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)
SALMON, RIB, PALE, MOUTH = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90), (0x42, 0x16, 0x18)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FRAME0 = Image.open(HERE.parent / 'frame0_tilt.png').convert('RGBA')
HEAD = {(x, y): FRAME0.getpixel((x, y))[:3] for y in range(36, 55) for x in range(0, 32) if FRAME0.getpixel((x, y))[3]}


def fold(p):
    if max(p) < 0x14: return K
    if max(p) - min(p) < 24: return LIGHT if max(p) >= 0x68 else MID if max(p) >= 0x50 else DARK
    return min((SALMON, RIB, PALE, MOUTH), key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


def load(name):
    im = Image.open(HERE / name).convert('RGBA')
    return {(x, y - 2): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}


def line(a, b):
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
    return [(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(n + 1)]


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


def outline(g):
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    return g


def finish(g, head_at, name, after=()):
    g = flat(g)
    for (x, y), c in HEAD.items(): g[x + head_at[0], y + head_at[1]] = c
    g = outline(g)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: out.putpixel((x, y), c + (255,))
    tidy_mod.tidy(out)
    for p, c in after:                                # lines tidy would break: its lone-pixel pass takes diagonals
        if out.getpixel(p)[3]: out.putpixel(p, c + (255,))
    out.save(HERE / name)
    print(name, out.getbbox())
    return out


def fly():
    g = load('f2.png')
    for p in [p for p in g if p[0] <= 33 and p[1] >= 33]: del g[p]              # its head: the approved one goes on
    for p in [p for p in g if p[0] >= 69 and p[1] <= 43]:                       # the tail spike
        if p[1] > 33: del g[p]
    foot = {(x, y): c for (x, y), c in g.items() if 62 <= x <= 68 and y >= 48 and c in (SALMON, RIB, PALE)}
    for (x, y), c in foot.items(): g[x - 22, y - 2] = c                         # the front foot, a copy of the near back one
    for y in range(44, 49):                                                     # its leg, tucked
        for x in range(42, 46): g[x, y] = DARK
    return finish(g, (2, -1), 'fly.png')


def poly(points):
    """Filled polygon, scanline."""
    out, n = set(), len(points)
    for y in range(min(p[1] for p in points), max(p[1] for p in points) + 1):
        xs = []
        for i in range(n):
            (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
            if y0 != y1 and min(y0, y1) <= y < max(y0, y1): xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            out |= {(x, y) for x in range(round(a), round(b) + 1)}
    return out


def block():
    """Final-frame coordinates. Far wing a great dome over the head, ribs fanned from the shoulder; near wing b1's, in front."""
    g = load('b1.png')
    above = lambda x, y: y < 29 + (x - 36) * 5 // 20
    keep = {p: c for p, c in g.items() if p[0] >= 35 and not (p[0] < 56 and above(*p)) and not (p[0] >= 55 and p[1] < 36)}
    drop = 57 - max(y for x, y in keep)
    keep = {(x, y + drop): c for (x, y), c in keep.items()}
    SHOULDER = (60, 27)
    EDGE = [(52, 12), (38, 8), (24, 13), (15, 25), (14, 36), (19, 44), (24, 38), (28, 46), (35, 40)]
    far = poly([SHOULDER] + EDGE)
    out = {p: (SALMON if (p[0] - 60) ** 2 + (p[1] - 27) ** 2 > 24 ** 2 else RIB) for p in far}
    for x, y in far:
        for a, b in N4:
            if (x + a, y + b) not in far: out[x + a, y + b] = K
    for a, b in line(SHOULDER, (52, 12)) + line((52, 12), (38, 8)) + line((38, 8), (24, 13)) + line((24, 13), (15, 25)):   # its bony leading edge
        out[a, b] = MID
    out.update(keep)
    ribs = [(p, K) for tip in ((14, 36), (24, 38), (35, 40), (24, 13)) for p in line(SHOULDER, tip) if p in far]
    top = 29 + drop
    near = [(p, K) for tip in ((43, 54 + drop), (37, 46 + drop)) for p in line((54, 33 + drop), tip)]
    edge = [(p, MID) for p in line((38, 30 + drop), (55, 35 + drop))]
    keep_after = [(p, c) for p, c in ribs if p not in keep] + near + edge
    return finish(out, (2, -3), 'block.png', keep_after)


def cloak(name, out_name):
    """PixelLab's cleanup of block() (the wings wrapped forward round the body): folded, flattened, one outline."""
    g = flat(load(name))
    g = outline(g)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x < W and 0 <= y < H: out.putpixel((x, y), c + (255,))
    tidy_mod.tidy(out)
    out.save(HERE / out_name)
    print(out_name, out.getbbox())
    return out


cloak('c1.png', 'block_c1.png'); cloak('c2.png', 'block_c2.png')
a, b = fly(), block()
S = 6
board = Image.new('RGBA', (W * S * 3, H * S), (0x6f, 0x9e, 0x5c, 255))
for i, im in enumerate((FRAME0, a, b)): board.alpha_composite(im.resize((W * S, H * S), 0), (i * W * S, 0))
board.save(HERE / 'board_clean.png')
S = 7
board = Image.new('RGBA', (W * S * 3, H * S), (0x6f, 0x9e, 0x5c, 255))
for i, n in enumerate(('fly.png', 'block_c1.png', 'block_c2.png')):
    board.alpha_composite(Image.open(HERE / n).convert('RGBA').resize((W * S, H * S), 0), (i * W * S, 0))
board.save(HERE / 'board3.png')
