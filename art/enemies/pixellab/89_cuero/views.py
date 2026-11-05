"""89 Cuero's battle frame (the user, 2026-11-02, picked the star-shaped hide: pixellab-out/89-concepts/89/sprites/v4/a1.png).
The Chilean lake monster that is a living stretched cowhide, its rim set with claws: a pale hide spread flat, a round
face in the middle.

Hide one cream and one shade, claws one maroon and one dark, flat as the cast; PixelLab's glossy highlight on the
head goes. Each eye one 2 px mark in its black socket. One black outline, on the 98x65 frame, its lowest point on
the bottom row.

    python art/enemies/pixellab/89_cuero/views.py     # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
SRC = ROOT / 'pixellab-out/89-concepts/89/sprites/v4/a1.png'
W, H = 98, 65
K = '000000'
HIDE, SHADE, CLAW, CLAW_D, EYE = 'fce4a0', 'b2966a', '792727', '421618', 'fc74b4'
FOLD = {'fcdea1': HIDE, 'fefede': HIDE, 'b89b70': SHADE, '8a7954': SHADE, '6c424b': CLAW, '4d202c': CLAW_D, '130d10': K, 'f33f82': K}
EYES = ((44, 25), (45, 25), (54, 25), (55, 25))      # the 2 px marks, source coordinates, by eye
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


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


def main():
    im = Image.open(SRC).convert('RGBA')
    g = {(x, y): FOLD['%02x%02x%02x' % im.getpixel((x, y))[:3]] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = flat(g)
    edge = {p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)}
    body = {p: c for p, c in g.items() if p not in edge}
    g = dict(body)
    for x, y in body:                     # one closed black outline
        for a, b in N4:
            if (x + a, y + b) not in body: g[x + a, y + b] = K
    for p in EYES: g[p] = EYE
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = (W - (max(xs) - min(xs) + 1)) // 2 - min(xs), H - 1 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        out.putpixel((x + dx, y + dy), tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('bbox', out.getbbox(), 'colours', len(set(g.values())) - 1, '+ black', dict(Counter(g.values())))


main()
