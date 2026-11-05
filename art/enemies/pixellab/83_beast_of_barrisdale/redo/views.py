"""83 Beast of Barrisdale, redo: grounded frame 0 from the picked blend (the user, 2026-11-02: "Top middle 100%",
pixellab-out/83-redo-blend e1, saved as blend/picked.png). Faces left, 100x65.

PixelLab's many greys and reds fold onto the old sheet's own colours: three charcoals, salmon + rib red + pale pink,
a dark mouth red, black. Patches of a few px merge (flat, as the cast). The doubled foot beside the middle leg goes,
leaving the lore's three legs (abookofcreatures: two in front, one behind). One closed black outline.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / 'tools'))
import tidy as tidy_mod

W, H, GROUND = 100, 65, 62                  # the old sheet's lowest row, so it stands where it stood
K = (0, 0, 0)
LIGHT, MID, DARK = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)
SALMON, RIB, PALE, MOUTH = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90), (0x42, 0x16, 0x18)
WARM = (SALMON, RIB, PALE, MOUTH)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
DOUBLED_FOOT = lambda x, y: x >= 50 and 49 <= y and x <= 56      # source coordinates, by eye on blend/picked_grid.png


def fold(p):
    r, g, b = p
    if max(p) < 0x14: return K
    if max(p) - min(p) < 24:                # the greys
        return LIGHT if max(p) >= 0x60 else MID if max(p) >= 0x42 else DARK
    return min(WARM, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


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
        if c == K or len(piece) > most or (c == RIB and p[0] < 30): continue   # the eye and mouth spared
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def line(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    return [(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def touch(out):
    """By hand on the finished frame (coordinates on frame0): what folding lost, and the middle leg's stump."""
    px = out.load()
    put = lambda ps, c: [px.__setitem__(p, c + (255,)) for p in ps]
    put([(23, 39), (24, 39)], RIB)                                        # the eye: a red 2 px mark in its black socket
    put([(22, 46), (23, 46), (22, 45)], MOUTH)                            # the gape, deeper
    put([(24, 46), (25, 46), (21, 47), (22, 47), (23, 47), (24, 47)], RIB)  # its tongue
    put(line((60, 22), (72, 34)) + line((58, 30), (64, 37)), K)           # the wing's two ribs, whole again
    put([(x, 49) for x in range(35, 39)] + [(x, 50) for x in range(36, 40)], DARK)   # the belly line thinner
    put([(31, 38), (32, 38), (31, 39), (32, 39)], LIGHT)                  # the neck crease one line
    put([(23, 48)], RIB)                                                  # a lone grey px under the tongue
    for p in [(51, 55), (52, 55), (53, 55), (50, 56), (51, 56), (51, 54)]:  # the removed leg's stump
        px[p] = (0, 0, 0, 0)
    put([(50, 55), (50, 54)], K)
    put([(x, y) for x in range(26, 36) for y in range(56, 62) if px[x, y][3] and px[x, y][:3] == PALE], SALMON)   # all feet one pink
    put([(62, 57)], SALMON)
    put([(26, 61), (27, 61), (28, 61), (28, 60), (40, 61), (41, 61), (42, 61), (42, 60)], SALMON)   # the toes splayed forward
    body = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    for x, y in [p for p in body if px[p][:3] == K and any((p[0] + a, p[1] + b) not in body for a, b in N4)]:
        px[x, y] = (0, 0, 0, 0)
    body = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    for x, y in body:
        for a, b in N4:
            if (x + a, y + b) not in body: px[x + a, y + b] = K + (255,)


def main():
    im = Image.open(HERE / 'blend/picked.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width)
         if im.getpixel((x, y))[3] > 127 and not DOUBLED_FOOT(x, y)}
    g = flat(g)
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, GROUND - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.tidy(out)
    touch(out)
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
