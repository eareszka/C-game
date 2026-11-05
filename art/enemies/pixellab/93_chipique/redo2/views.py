"""93 Chipique redraw: frame 0 from the picked edit (the user, 2026-11-03: jab/j4.png): a huge fat snake with one dugout canoe jabbed right
through it, on the standard 98x65 frame. Lore: the Barotse river serpent of Victoria Falls, with its small slate head (A Book of Creatures).

PixelLab drew an extra whole canoe on its flank, and no body behind it. Here that goes: the flank is painted out to the stern's wound (EDGE),
so one canoe goes in at the bow's wound and comes out at the stern's, its middle hidden inside the snake. Colours fold onto the palette: two
navies, slate, cream and its shade, canoe brown and its shade, blood. The eye's glint goes. One closed black outline.

    python art/enemies/pixellab/93_chipique/redo2/views.py   # writes frame0.png, frame0_x8.png
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
NAVY, NAVY_D, SLATE = (0x37, 0x38, 0x7b), (0x2b, 0x1f, 0x40), (0x84, 0x86, 0x94)
CREAM, CREAM_D, WOOD, WOOD_D, RED = (0xce, 0xbe, 0x82), (0xb2, 0x96, 0x6a), (0x81, 0x54, 0x23), (0x58, 0x35, 0x18), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EDGE = {15: 50, 18: 52, 21: 55, 24: 59, 27: 63, 30: 66, 33: 68, 36: 69, 40: 69, 44: 69, 48: 70, 52: 72, 56: 72}   # the flank's right edge by row
EYE = ((41, 5), (42, 5), (41, 6), (42, 6))          # one solid mark, source coordinates


def edge(y):
    keys = sorted(EDGE)
    for a, b in zip(keys, keys[1:]):
        if a <= y <= b: return EDGE[a] + (EDGE[b] - EDGE[a]) * (y - a) / (b - a)
    return None


def fold(p):
    r, g, b = p
    v = max(p)
    if v < 0x20: return K
    if min(p) > 0xd0: return SLATE
    if r > 0x60 and g < 0x38 and b < 0x50: return RED
    if b > r + 10:
        if v >= 0x68 and v - min(p) < 0x40: return SLATE
        return NAVY if v >= 0x34 else NAVY_D
    if r > 0xb8: return CREAM
    if r > 0x90 and g > 0x70: return CREAM_D
    if r > 0x68: return WOOD
    return WOOD_D


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
        if c in (K, RED) or len(piece) > most: continue
        n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
        if n:
            for a in piece: out[a] = n.most_common(1)[0][0]
    return out


def main():
    im = Image.open(HERE / 'jab/j4.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for y in sorted(EDGE)[0:1] + list(range(15, 57)):        # the extra canoe out: its flank painted in, up to the stern's wound
        e = edge(y)
        for x in range(45, int(e) + 1):
            wound = g.get((x, y)) == RED and x >= 64
            if wound or (x >= 66 and g.get((x, y)) == WOOD and 30 <= y <= 44): continue
            g[x, y] = NAVY_D if x >= e - 2 else NAVY
    for p in [p for p in g if p[1] <= 34 and 48 <= p[0] <= 72 and (p[1] < 15 or p[0] > edge(p[1])) and g[p] in (WOOD, WOOD_D, K, RED)]:
        if not (p[0] >= 66 and p[1] >= 30): del g[p]           # the old hull's scrap above the flank
    for y in range(28, 54):                                    # its stray black line, the drips' dark streak
        for x in (43, 44, 45, 46):
            if g.get((x, y)) == K: g[x, y] = NAVY
        for x in range(69, 74):
            if y >= 44 and g.get((x, y)) in (NAVY_D, K): g[x, y] = NAVY
    for x in range(66, 80):                                    # a last dark square on the lower body
        for y in range(50, 60):
            if g.get((x, y)) == NAVY_D and all((x + a, y + b) in g for a, b in N4) and x < 76: g[x, y] = NAVY
    g = flat(g)
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items():
        if 0 <= x + dx < W and 0 <= y + dy < H: out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = NAVY_D
    tidy_mod.KEEP = {RED}
    tidy_mod.tidy(out)
    for x in range(40, 45):                                  # the glint out, one mark in
        for y in range(4, 8):
            if out.getpixel((x + dx, y + dy))[3]: out.putpixel((x + dx, y + dy), SLATE + (255,))
    for p in EYE: out.putpixel((p[0] + dx, p[1] + dy), K + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
