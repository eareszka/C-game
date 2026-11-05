"""90 Chipekwe redo: the heavy single-horned body (the user, 2026-11-03: "much fatter/stronger", "1 trunk in the middle of face",
"change pallete to blue"), PixelLab's edits o1 o2 o3 on the palette's blues by brightness, the ivory horn and claws kept.
The eye becomes one solid 2 px black mark. Flat, one closed outline, feet on the frame's last row but one.

    python art/enemies/pixellab/90_chipekwe/redo/one/blue.py   # writes blue_o1.png blue_o2.png blue_o3.png, board_blue.png
"""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / '83_beast_of_barrisdale'))
import tidy as tidy_mod

W, H = 98, 65
K = (0, 0, 0)
LIGHT, HIDE, SHADE, FAR = (0x84, 0xa7, 0xe9), (0x37, 0x5a, 0x94), (0x37, 0x38, 0x7b), (0x34, 0x34, 0x3e)
IVORY, IVORY_D = (0xe8, 0xe0, 0xc0), (0xb2, 0x96, 0x6a)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
T_LIGHT, T_MID = 0x4e, 0x38      # Igtuk's balance (the user: "like igtuk"): mostly the light periwinkle, mid blue its shade, navy deep
EYES = {'o1': (19, 28), 'o2': (21, 29), 'o3': (20, 28)}     # PixelLab's eye, source coordinates, by eye on the board


def fold(p):
    r, g, b = p
    v = max(p)
    if v < 0x1a: return K
    if min(p) > 0xa8: return IVORY
    if r > 0x90 and g > 0x70: return IVORY_D
    if g > r + 4 and g >= b:                                 # the greens, by brightness
        return LIGHT if v >= T_LIGHT else HIDE if v >= T_MID else SHADE
    return SHADE if v >= 0x20 else FAR                       # the far legs: Igtuk's navy, its charcoal only in the deepest


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


def make(name):
    im = Image.open(HERE / f'{name}.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    ex, ey = EYES[name]
    for x in range(ex - 2, ex + 3):                          # the glinting eye out
        for y in range(ey - 1, ey + 2):
            if (x, y) in g: g[x, y] = LIGHT
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
    tidy_mod.SHADE = HIDE
    tidy_mod.KEEP = {IVORY}
    tidy_mod.tidy(out)
    for p in ((ex, ey), (ex + 1, ey)): out.putpixel((p[0] + dx, p[1] + dy), K + (255,))
    out.save(HERE / f'blue_{name}.png')
    print(name, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))
    return out


S = 5
b = Image.new('RGBA', (W * S * 3, H * S), (0x6f, 0x9e, 0x5c, 255))
for i, n in enumerate(EYES): b.alpha_composite(make(n).resize((W * S, H * S), 0), (i * W * S, 0))
b.save(HERE / 'board_blue.png')
