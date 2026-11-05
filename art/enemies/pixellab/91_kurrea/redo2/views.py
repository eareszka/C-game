"""91 Kurrea redesign: frame 0 from the picked edit (the user, 2026-11-03: concepts c3, thickened in thick/t1): a serpent of reality
shard, arching in one great loop as if digging through a bank, rainbow crystal plates along its spine, on the standard 98x65 frame.

PixelLab's colours fold onto the shard set: the Celestial Stag's three purples and the torch's pink, yellow, mint and blue. Patches of
a few px merge (flat, as the cast). The eye's white glint goes: one solid 2 px mark. One closed black outline. Each crystal plate is
one flat colour (the user: "each scale should be the same color"), cycling pink, yellow, mint, blue from tail to head.

    python art/enemies/pixellab/91_kurrea/redo2/views.py   # writes frame0.png, frame0_x8.png
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
SHADE, COAT, LILAC = (0x2b, 0x1f, 0x40), (0x66, 0x4b, 0x95), (0xb6, 0x9c, 0xee)
RAINBOW = [(0xec, 0x84, 0x76), (0xfa, 0xe4, 0x88), (0xa8, 0xf0, 0xbc), (0x84, 0xa7, 0xe9)]
PAL = [SHADE, COAT, LILAC] + RAINBOW
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fold(p):
    if max(p) < 0x18: return K
    return min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


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


# The plates tail to head, each by the (left, top) of its pieces on the frame as placed: a plate may be two pieces.
PLATES = [[(8, 30)], [(14, 22)], [(19, 15)], [(30, 10)], [(41, 17)], [(48, 25)], [(51, 32), (55, 33)], [(53, 40)], [(55, 47)], [(61, 49)],
          [(70, 38)], [(64, 31)], [(65, 24)], [(69, 16), (70, 15)]]
SPLIT = (69, 16, 76)      # that last piece is two plates fused: x <= 75 keeps the list's colour, a black column at 76, the rest its own
PASTEL = set(RAINBOW) | {LILAC}


def plates(out):
    px = out.load()
    left = {(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in PASTEL}
    pieces = {}
    while left:
        s = left.pop(); piece = [s]; todo = [s]
        while todo:
            x, y = todo.pop()
            for a, b in N4:
                q = (x + a, y + b)
                if q in left: left.discard(q); piece.append(q); todo.append(q)
        pieces[min(p[0] for p in piece), min(p[1] for p in piece)] = piece
    n = 0
    for keys in PLATES:
        c = RAINBOW[n % 4]
        for k in keys:
            for p in pieces[k]: px[p] = c + (255,)
        n += 1
    sx, sy, cut = SPLIT
    for p in pieces[sx, sy]:
        if p[0] == cut: px[p] = K + (255,)
        elif p[0] > cut: px[p] = RAINBOW[n % 4] + (255,)


def main():
    im = Image.open(HERE / 'thick/t1.png').convert('RGBA')
    src = {(x, y): im.getpixel((x, y))[:3] for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = {p: fold(c) for p, c in src.items()}
    glint = [p for p, c in src.items() if min(c) > 0xd0 and p[0] > 60 and p[1] < 30]      # the eye's white pixels, up on the head
    print('glint', glint)
    for p in glint: g[p] = SHADE
    g = flat(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = SHADE
    tidy_mod.KEEP = set()
    tidy_mod.tidy(out)
    plates(out)
    if glint:
        ex, ey = min(glint)
        for p in ((ex, ey), (ex + 1, ey)): out.putpixel((p[0] + dx, p[1] + dy), RAINBOW[1] + (255,))   # a pale mark on its dark head
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
