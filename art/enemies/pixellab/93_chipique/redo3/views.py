"""93 Chipique, final idea: frame 0 from the picked edit (the user, 2026-11-03: idea/dry/d4.png): the night serpent of Victoria Falls arching
high over a dugout canoe held in its coil, a hooded figure in the canoe, its small slate head above. On the standard 98x65 frame, facing left.
No water (the user).

PixelLab's 40 colours fold onto the palette: dark indigo and its shade for the coils, two slates for the head, neck and belly plates, canoe
brown and its shade, red for the blood and the figure's eyes. Speckle merges (flat, as the cast). The long string of blood becomes a few
drips; the eye's white glint becomes one solid mark. One closed black outline.

    python art/enemies/pixellab/93_chipique/redo3/views.py   # writes frame0.png, frame0_x8.png
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
HIDE, SHADE = (0x42, 0x3c, 0x70), (0x2b, 0x1f, 0x40)
SLATE, SLATE_D = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65)
WOOD, WOOD_D, RED = (0x78, 0x58, 0x30), (0x3c, 0x24, 0x12), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EYE = ((21, 10), (22, 10), (21, 11), (22, 11))             # source coordinates
DRIPS = [(19, y) for y in range(17, 23)] + [(20, y) for y in range(17, 20)] + [(19, 26), (19, 27)]


def fold(p):
    r, g, b = p
    v = max(p)
    if v < 0x1c: return K
    if min(p) > 0xd0: return SLATE
    if r > 0x60 and g < 0x38: return RED
    if r > g + 8:
        return WOOD if r > 0x6a else WOOD_D
    if v >= 0x68: return SLATE
    if v >= 0x48: return SLATE_D
    return HIDE if v >= 0x34 else SHADE


def flat(g, most=4):
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
    im = Image.open(HERE / 'idea/dry/d4.png').convert('RGBA')
    g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
    for p in [p for p in g if 16 <= p[0] <= 24 and 17 <= p[1] <= 39]: del g[p]   # the string of blood
    g = flat(g)
    for p in DRIPS: g[p] = RED
    for p in EYE: g[p] = K
    for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
    for x, y in list(g):
        for a, b in N4:
            if (x + a, y + b) not in g: g[x + a, y + b] = K
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = W // 2 - (min(xs) + max(xs) + 1) // 2, H - 2 - max(ys)
    out = Image.new('RGBA', (W, H))
    for (x, y), c in g.items(): out.putpixel((x + dx, y + dy), c + (255,))
    tidy_mod.SHADE = SHADE
    tidy_mod.KEEP = {RED}
    tidy_mod.tidy(out)
    for p in EYE: out.putpixel((p[0] + dx, p[1] + dy), K + (255,))
    out.save(HERE / 'frame0.png')
    bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
    bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
    print('offset', dx, dy, 'bbox', out.getbbox(), Counter('%02x%02x%02x' % p[:3] for p in out.get_flattened_data() if p[3]))


main()
