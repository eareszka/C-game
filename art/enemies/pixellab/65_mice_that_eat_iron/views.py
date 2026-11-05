"""65 Mice That Eat Iron's battle frame (the user, 2026-11-02, picked the three mice sharing a bar:
pixellab-out/65-concepts/65/sprites/v3/c3.png). The Panchatantra's mice, who were said to have eaten a merchant's iron
balance beam: three of them, the beam in their paws, its ends bitten.

Fur one grey and one shade, muzzles pale, ears and paws pink, bellies one tan, the beam iron (light over the fur's
shade) instead of PixelLab's wood. Small clumps merged, flat as the cast (the user on 40: "too detailed"). Eyes one
solid black mark. One black outline round it, native size on a 64x48 frame, feet on the bottom row.

    python art/enemies/pixellab/65_mice_that_eat_iron/views.py     # writes frame0.png, frame0_x10.png
"""
from pathlib import Path
from collections import Counter
import colorsys
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
SRC = ROOT / 'pixellab-out/65-concepts/65/sprites/v3/c3.png'
W, H = 64, 48
K = '000000'
FUR, SHADE, PALE = '848694', '474751', 'c6ccda'
PINK, PINK_D, TAN = 'ec8476', 'b6433d', 'd7a175'
IRON = 'bcbeca'
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BEAM = lambda x, y: 26 <= y <= 30 and 8 <= x <= 62            # the beam's rows, by eye off the concept


def fold(p, x, y):
    r, g, b = p
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if v < 0.2: return K
    warm = h < 45 or h > 335
    if warm and s > 0.3 and v > 0.5 and (h > 335 or h < 8): return PINK if v > 0.8 else PINK_D
    if warm and not BEAM(x, y): return TAN                     # bellies
    if warm and BEAM(x, y): return IRON if y <= 28 else SHADE  # the beam: iron, not wood
    if v > 0.8: return PALE
    if v > 0.45: return FUR
    return SHADE


def load():
    im = Image.open(SRC).convert('RGBA')
    return {(x, y): fold(im.getpixel((x, y))[:3], x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}


def flat(g, most, spare=(PALE,)):
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
        if c == K or c in spare or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def outline(g):
    edge = {p for p, c in g.items() if c == K and any((p[0] + dx, p[1] + dy) not in g for dx, dy in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    out = dict(body)
    for x, y in body:
        for dx, dy in N4:
            if (x + dx, y + dy) not in body: out[x + dx, y + dy] = K
    return out


def rgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


EYES = {(19, 23, 22, 26): [(20, 24), (20, 25)], (28, 22, 31, 25): [(29, 23), (29, 24)],
        (34, 23, 37, 26): [(35, 24), (35, 25)], (44, 25, 47, 28): [(45, 26), (45, 27)]}   # box of PixelLab's eye, its 2 px mark
BITES = (57, 58, 59)                       # columns of the bite out of the beam's right end, by eye


def finish(im):
    """The eyes down to a solid 2 px mark each; one bite out of the beam, its edge outlined."""
    black = rgb(K)
    for (x0, y0, x1, y1), mark in EYES.items():
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if im.getpixel((x, y)) == black and all(im.getpixel((x + a, y + b))[3] for a, b in N4):
                    im.putpixel((x, y), rgb(FUR))
        for p in mark: im.putpixel(p, black)
    rows = [y for y in range(H) if im.getpixel((BITES[0], y)) == rgb(IRON)]
    if rows:
        top = rows[0]
        for x in BITES:
            for y in (top - 1, top):              # the beam's own outline and top row, nothing above it
                im.putpixel((x, y), (0, 0, 0, 0))
            im.putpixel((x, top + 1), black)
        for y in (top - 1, top):
            for x in (BITES[0] - 1, BITES[-1] + 1):
                if im.getpixel((x, y))[3]: im.putpixel((x, y), black)


def main():
    g = outline(flat(load(), 3))
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = (W - (max(xs) - min(xs) + 1)) // 2 - min(xs), H - 1 - max(ys)
    im = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        im.putpixel((x + dx, y + dy), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    finish(im)
    im.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(im)
    bg.resize((W * 12, H * 12), 0).save(HERE / 'frame0_x12.png')
    print('bbox', im.getbbox(), 'colours', len(set(g.values())) - 1, '+ black', dict(Counter(g.values())))


main()
