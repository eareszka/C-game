"""91 Kurrea redo: frame 0 from the picked concept (the user, 2026-11-03: concepts/c4.png): the Boobera Lagoon serpent in big loops,
banded like the rainbow serpent it may be, on the standard 98x65 frame, its head to the right.

PixelLab's 46 colours fold onto the palette: red and dark red, orange bands, two dark greens, a tongue pink, cream teeth. Its pale
highlights and glossy patches merge into what surrounds them (flat, as the cast). The eye is one 2 px orange mark in its dark
socket. One closed black outline.

    python art/enemies/pixellab/91_kurrea/redo/views.py   # writes frame0.png, frame0_x8.png
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
RED, DARK, ORANGE = (0xb6, 0x43, 0x3d), (0x53, 0x1b, 0x1c), (0xd8, 0x98, 0x30)
GREEN, GREEN_D = (0x29, 0x63, 0x3e), (0x14, 0x2e, 0x1f)
TONGUE, TOOTH = (0xec, 0x84, 0x76), (0xe8, 0xe0, 0xc0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EYE = ((50, 12), (51, 12))                # source coordinates
HEAD = lambda x, y: 44 <= x <= 64 and 8 <= y <= 24


def fold(p, x, y):
    r, g, b = p
    v = max(p)
    if v < 0x1c: return K
    if min(p) > 0x78: return TOOTH if HEAD(x, y) else None     # pale: teeth in the head, a highlight anywhere else
    if g > r + 6: return GREEN if v >= 0x40 else GREEN_D
    if r > 0xc0 and b > 0x50 and g < 0x60: return TONGUE if HEAD(x, y) else RED
    if r > 0xc0 and g > 0x50: return ORANGE
    if r > 0x80: return RED
    if r > 0x38: return DARK
    return GREEN_D


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
        if c in (K, TOOTH, TONGUE) or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def main():
    im = Image.open(HERE / 'concepts/c4.png').convert('RGBA')
    raw = {(x, y): fold(im.getpixel((x, y))[:3], x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for _ in range(4):                       # highlights take the colour round them
        for (x, y), c in list(raw.items()):
            if c is None:
                n = Counter(raw.get((x + a, y + b)) for a, b in N4)
                n.pop(None, None); n.pop(K, None)
                if n: raw[x, y] = n.most_common(1)[0][0]
    g = {p: (c if c is not None else RED) for p, c in raw.items()}
    g = flat(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = DARK
    tidy_mod.KEEP = {TOOTH}
    tidy_mod.tidy(out)
    for p in EYE: out.putpixel((p[0] + dx, p[1] + dy), ORANGE + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
