"""46 Lusca redo: frame 0 from the picked concept (the user, 2026-11-03: concepts/c1.png). The blue-hole monster head on: a huge
shark's head on crimson octopus arms, on the standard 98x65 frame.

PixelLab's 44 colours fold onto the palette: two hide greys, cream and its shade for the jaw, three reds and a pink tongue
for the arms and mouth. Patches of a few px merge (flat, as the cast), the teeth spared. By hand: the ringed, glinting eyes
become one solid 2 px mark each under a slanted brow (the bible's tiny eye marks); the red nostrils go black. One closed
black outline.

    python art/enemies/pixellab/46_lusca/redo/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / '83_beast_of_barrisdale'))
import tidy as tidy_mod

W, H = 98, 65
K = (0, 0, 0)
HIDE, SHADE = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65)
CREAM, CREAM_D = (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a)
RD, RM, RL, TONGUE = (0x53, 0x1b, 0x1c), (0x79, 0x27, 0x27), (0xb6, 0x43, 0x3d), (0xec, 0x84, 0x76)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
AXIS = 96               # source columns x and AXIS - x mirror across the face
MOUTH = lambda x, y: 26 <= x <= 70 and 36 <= y <= 56


def fold(p):
    r, g, b = p
    if max(p) < 0x3a and not (r > g + 0x10): return K          # outline and mouth blacks
    if b >= r and b >= g:                                      # the blue-grey hide
        return HIDE if max(p) >= 0x78 else SHADE if max(p) >= 0x50 else K
    if min(p) > 0xc8: return CREAM
    if r > 0xd0 and g < 0x60: return RL                        # the old nostril red
    if r > 0xc8 and g > 0x90: return CREAM
    if r > 0x90 and g > 0x70: return CREAM_D
    if r > 0xd0: return TONGUE
    if r > 0x90: return RL
    if r > 0x68: return RM
    return RD


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
        if c == K or len(piece) > most or (c == CREAM and MOUTH(*p)): continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def face(g):
    for x in range(28, 39):                       # the ringed eyes out, both sides
        for y in range(26, 35):
            for sx in (x, AXIS - x):
                if (sx, y) in g: g[sx, y] = HIDE
    for sx in (lambda x: x, lambda x: AXIS - x):
        for p in ((30, 28), (31, 28), (32, 29), (33, 29), (34, 30)): g[sx(p[0]), p[1]] = K    # the brow, slanting in
        for p in ((32, 30), (33, 30)): g[sx(p[0]), p[1]] = K                                  # the eye, under the brow
        for p in ((42, 32), (43, 32)): g[sx(p[0]), p[1]] = K                                  # the nostril
    return g


def main():
    im = Image.open(HERE / 'concepts/c1.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = face(flat(g))
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 3 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = RD
    tidy_mod.KEEP = {CREAM}
    tidy_mod.tidy(out)
    marks = {(sx(p[0]), p[1]) for sx in (lambda x: x, lambda x: AXIS - x)
             for p in ((30, 28), (31, 28), (32, 29), (33, 29), (34, 30), (32, 30), (33, 30), (42, 32), (43, 32))}
    for x, y in marks: out.putpixel((x + dx, y + dy), K + (255,))    # after tidy: it thins lone black pixels
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
