"""95 Witkes frame 0, from PixelLab's r2 (ref/prompt.txt, the user's reference): folded onto the palette as the cast's flat fills -- hide one brown and one shade, horns one pale grey and one
shade, mask and feet one green and one shade -- small clumps merged, one closed outline, on the standard 98x65 frame. No water. By hand after the fold: the horns pale (PixelLab browned them), two solid 2 px eye marks on the mask (the
reference's yellow; the fold lost them), webbed clawed feet (FOOT, the fold lost the toes).

    python art/enemies/pixellab/95_witkes/redo/views.py   # frame0.png, frame0_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
HIDE, SHADE, HORN, HORN_D, GRN, GRN_D = (0x8d, 0x6b, 0x4f), (0x46, 0x34, 0x22), (0xbc, 0xbe, 0xca), (0x84, 0x86, 0x94), (0x4f, 0xa6, 0x67), (0x29, 0x63, 0x3e)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
EYE = (0xfa, 0xe4, 0x88)
HORN_BASE = 21
EYES = ((21, 30), (22, 30), (26, 30), (27, 30))
FEET = ((39, 52), (52, 54), (68, 55))
FOOT = ['....GGG....', '...GGGGG...', '..GGDGDGG..', '.GGDDGDDGG.', 'GGDDGGGDDGG', 'GDDGDGDGDDG', 'H..H...H..H']
im = Image.open(HERE / 'ref/r2.png').convert('RGBA').crop((1, 1, 99, 66))
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:18])
def fold(p):
    r, g, b = p
    if max(p) < 0x20: return K
    if g > r + 4 and g > b: return GRN if g > 0x70 else GRN_D
    if min(p) > 0x88 and max(p) - min(p) < 0x50: return HORN if min(p) > 0xa8 else HORN_D
    return HIDE if r > 0x60 else SHADE
g = {(x, y): fold(im.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if im.getpixel((x, y))[3] > 127}
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
    if c == K or len(piece) > 3: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
for p, c in list(g.items()):                                  # the horns, above the head
    if p[1] < HORN_BASE and p[0] < 37 and c != K: g[p] = HORN
for y in range(HORN_BASE):                                    # each horn's far edge a step darker, by form
    for x in range(W - 1):
        if g.get((x, y)) == HORN and g.get((x + 1, y), K) == K: g[x, y] = HORN_D
for x, y in EYES: g[x, y] = EYE
greens = {p for p, c in g.items() if c in (GRN, GRN_D) and p[1] >= 48}
left, feet = set(greens), []
while left:
    piece, todo = set(), [left.pop()]
    while todo:
        a = todo.pop(); piece.add(a)
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                q = (a[0] + dx, a[1] + dy)
                if q in left: left.discard(q); todo.append(q)
    feet.append(piece)
feet = sorted(feet, key=len, reverse=True)[:3]
print('feet', [(min(p[0] for p in f), max(p[0] for p in f), min(p[1] for p in f), max(p[1] for p in f)) for f in feet])
for p in greens: del g[p]
for p in [p for p, c in g.items() if c == K and p[1] >= 48 and any(q in greens for q in ((p[0] + a, p[1] + b) for a, b in N4))]: del g[p]
for cx, top in FEET:                                          # under each leg: the near foot lowest, as in the reference
    for j, r in enumerate(FOOT):
        for i, ch in enumerate(r):
            if ch != '.': g[cx - len(r) // 2 + i, top + j] = {'G': GRN, 'D': GRN_D, 'H': HORN_D}[ch]
for p in [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]: del g[p]
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
drop = H - 1 - max(y for x, y in g)                           # feet on the last row
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y + drop < H: f.putpixel((x, y + drop), c + (255,))
f.save(HERE / 'frame0.png'); print(f.getbbox())
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_x8.png')
bg.crop((10, 15, 40, 45)).resize((480, 480), 0).save(HERE / 'frame0_head_x16.png')
