"""45 Kusa Kap redo: frame 0 from the picked blend (the user, 2026-11-02: concept 1's design in concept 2's colours, edit e2).
A colossal sea eagle from the front on the standard 98x65 frame, wings spread, a dugong in its talons.

PixelLab's colours fold onto the palette: three rusts, a near-black feather brown, cream, yellow, two dugong greys.
By hand: the wing ends were solid black behind a straight band, so they become dark feathers with black lines between,
and the rust meets them feather by feather. The face was buried, so it gets a pale patch, one eye mark and a clean
hooked beak. Red scraps under the dugong go. One closed black outline.

    python art/enemies/pixellab/45_kusa_kap/redo/views.py   # writes frame0.png, frame0_x8.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'art/enemies/pixellab/83_beast_of_barrisdale'))
import tidy as tidy_mod

W, H = 98, 65
K = (0, 0, 0)
RD, RM, RL = (0x53, 0x1b, 0x1c), (0x79, 0x27, 0x27), (0xb6, 0x43, 0x3d)
TIP, CREAM, YEL = (0x2b, 0x19, 0x0e), (0xfc, 0xe4, 0xa0), (0xf0, 0xbc, 0x3c)
GL, GD = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
CX = 48                 # the body's middle, source column: the wings are drawn the same either side of it

# The feather ends: the row they start on (source), the column the rust ends at measured out from CX, the rows of lines.
RUST_REACH = {y: 26 + (((y - 8) // 4) % 3) * 3 for y in range(0, 64)}
FEATHER_LINES = [(((29, 16), (42, 13))), ((29, 20), (43, 18)), ((29, 24), (42, 23)), ((27, 28), (37, 27))]

LETTERS = {'k': K, 'r': RM, 'd': RD, 'l': RL, 'c': CREAM, 'y': YEL}
FACE_AT = (40, 14)      # source column and row of the stamp's first character
FACE = ('....krrllllrrk.',
        '...krllllllllrk',
        '..krlccccccllrk',
        '.kyykcccccccrrk',
        'kyyyykckkcccrrk',
        'kyyyyykcccccrrk',
        'kyyrrkcccccrrrk',
        '.kyrkdkcccrrrrk',
        '..krkddkccrrrrk',
        '...kkryk.rrrrrk',
        '....kryk.rrrrrk',
        '.....kkk.rrrrrk')


def fold(p):
    if max(p) < 0x14: return K
    if max(p) - min(p) < 28 and p[2] > 0x30:
        return GL if max(p) >= 0x68 else GD
    if p[0] > 0xc0 and p[2] > 0x60: return CREAM
    if p[0] > 0xa0 and p[1] > 0x68: return YEL
    if p[0] > 0x90 and p[1] > 0x50 and p[2] < 0x10: return YEL
    if p[0] > 0xa0: return RL
    if p[0] > 0x68: return RM
    if p[0] > 0x40: return RD
    return TIP


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


def main():
    im = Image.open(HERE / 'blend/e2.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    # the scraps below the dugong
    for p in [p for p, c in g.items() if p[1] >= 52 and c in (RD, RM, RL, TIP)]: del g[p]
    for p in [p for p, c in g.items() if p[1] >= 55]: del g[p]
    g = flat(g)
    # the wing ends: inside the silhouette, past each row's reach, feather brown; the rust's own shading kept nearer in
    for (x, y) in list(g):
        d = abs(x - CX)
        if d < 24 or y > 40: continue
        if d >= RUST_REACH[y]: g[x, y] = TIP
        elif g[x, y] in (K, TIP): g[x, y] = RD
    g = outline(g)
    for a, b in FEATHER_LINES:
        for x, y in line(a, b):
            for sx in (CX - x, CX + x):
                if (sx, y) in g: g[sx, y] = K
    for r, row in enumerate(FACE):
        for c, ch in enumerate(row):
            if ch != '.': g[FACE_AT[0] + c, FACE_AT[1] + r] = LETTERS[ch]
    g = outline(g)
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 3 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = TIP
    tidy_mod.tidy(out)
    for a, b in FEATHER_LINES:                       # after tidy: its lone-pixel pass breaks diagonal lines
        for x, y in line(a, b):
            for sx in (CX - x, CX + x):
                p = (sx + dx, y + dy)
                if 0 <= p[0] < W and 0 <= p[1] < H and out.getpixel(p)[3]: out.putpixel(p, K + (255,))
    for r, row in enumerate(FACE):                   # and the face stays as drawn
        for c, ch in enumerate(row):
            if ch != '.': out.putpixel((FACE_AT[0] + c + dx, FACE_AT[1] + r + dy), LETTERS[ch] + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
