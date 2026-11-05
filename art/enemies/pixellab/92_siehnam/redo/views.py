"""92 Siehnam redo: frame 0 from the picked concept (the user, 2026-11-03: concepts/c4.png, built from A Book of Creatures: the Chorote's
night-killing deer): a skull-faced deer with vast bone antlers bloodied at the tips, a dark ruff, on the standard 98x65 frame.

PixelLab's 21 colours fold onto the palette: white skull, two bone greys, tan coat and its shade, dark ruff, blood. The concept had no
outline: it gets the one closed black outline, and a black line where the ruff lies on the coat. The stray black mark on its flank and
the black marks on its ears go; its hooves take the ruff's dark.

    python art/enemies/pixellab/92_siehnam/redo/views.py   # writes frame0.png, frame0_x8.png
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
WHITE, BONE, BONE_D = (0xfc, 0xfc, 0xfc), (0xbc, 0xbe, 0xca), (0x84, 0x86, 0x94)
COAT, COAT_D, RUFF, BLOOD = (0x8d, 0x6b, 0x4f), (0x78, 0x58, 0x30), (0x42, 0x16, 0x18), (0x7c, 0x0a, 0x1b)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
MARK = lambda x, y: 48 <= x <= 58 and 42 <= y <= 50 # the flank's stray black, source coordinates
EARS = lambda x, y: y < 28 and (35 <= x <= 40 or 53 <= x <= 58)


def fold(p, x, y):
    r, g, b = p
    v = max(p)
    if v < 0x28:
        if y >= 56: return RUFF                 # the hooves: black at the silhouette's edge would go with the outline
        return COAT if MARK(x, y) or EARS(x, y) else K
    if min(p) > 0xe0: return WHITE
    if v - min(p) < 16: return BONE if v > 0xa8 else BONE_D
    if r > 0x68 and g < 0x38: return BLOOD
    if r > 0x88: return COAT
    if r > 0x58: return COAT_D
    return RUFF


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
        if c == K or c == WHITE or c == BLOOD or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def main():
    im = Image.open(HERE / 'concepts/c4.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3], x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    g = flat(g)
    for p in [p for p, c in g.items() if c in (COAT, COAT_D) and any(g.get((p[0] + a, p[1] + b)) == RUFF for a, b in N4)]:
        g[p] = K                                  # the ruff's line on the coat
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 1 - max(ys)   # its hooves on the last row: it is tall, the antlers need the top clear
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = RUFF
    tidy_mod.KEEP = {WHITE}
    tidy_mod.tidy(out)
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
