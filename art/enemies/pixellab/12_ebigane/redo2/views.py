"""12 Ebigane frame 0 from concept r1 (the user, 2026-11-03; concepts/, the user's description): a hunched rat-bodied predator, round ear, jagged tan fins, long ringed rat tail, snarling. Folded onto the
palette as the cast's flat fills -- body charcoal brown and one shade (the concept's purple), fins and ear peach and tan, mouth and tail rings magenta and dark, teeth and talons ivory (its magenta feet) -- clumps
merged, one closed outline, on the 98x65 frame.

    python art/enemies/pixellab/12_ebigane/redo2/views.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_head_x16.png
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 98, 65
K = (0, 0, 0)
BODY, SHADE, PEACH, TAN, IVORY, PINK, RED = (0x59, 0x59, 0x65), (0x34, 0x34, 0x3e), (0xf0, 0xb8, 0x90), (0xb2, 0x96, 0x6a), (0xe8, 0xe0, 0xc0), (0xfc, 0x74, 0xb4), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
im = Image.open(HERE / 'concepts/r1.png').convert('RGBA')
print(sorted(((n, '%02x%02x%02x' % c[:3]) for n, c in im.getcolors(4096) if c[3]), reverse=True)[:22])
def fold(p, x, y):
    r, g, b = p
    if max(p) < 0x2b: return K                                # its darkest lines stay black: the masses read apart
    if r > 0x90 and b > 0x70 and b > g + 20:                 # the feet's magenta and the ear's and tail's pink
        return IVORY if y >= 52 else PINK
    if r > 0xd8 and g > 0xa8: return IVORY if b > 0xb0 else PEACH
    if r > 0xb8 and g > 0x68: return PEACH
    if r > 0x90 and g > 0x70: return TAN
    if r > 0xc0 and g < 0x60: return RED                      # the eye, the brow
    return BODY if max(p) > 0x48 else SHADE
dx = (W - im.width) // 2
g = {(x + dx, y): fold(im.getpixel((x, y))[:3], x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] > 127}
seen, out = set(), dict(g)
for p, c in g.items():
    if p in seen: continue
    piece, todo = {p}, [p]
    while todo:
        a = todo.pop()
        for d in N4:
            q = (a[0] + d[0], a[1] + d[1])
            if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
    seen |= piece
    if c in (K, RED, PINK, IVORY) or len(piece) > 6: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + d[0], a[1] + d[1]) for d in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
g = out
for p, c in list(g.items()):                                  # the tail: peach with dark rings (the user's description)
    if p[0] >= 69 and p[1] >= 40 and c != K: g[p] = SHADE if c in (PINK, RED) else PEACH
left, pieces = set(g), []
while left:
    piece, todo = set(), [left.pop()]
    while todo:
        a = todo.pop(); piece.add(a)
        for d in N8:
            q = (a[0] + d[0], a[1] + d[1])
            if q in left: left.discard(q); todo.append(q)
    pieces.append(piece)
print('pieces', sorted(map(len, pieces), reverse=True)[:6])
g = {p: g[p] for p in max(pieces, key=len)}
for p in [p for p, c in g.items() if c == K and any((p[0] + d[0], p[1] + d[1]) not in g for d in N4)]: del g[p]
for x, y in list(g):
    for d in N4:
        if (x + d[0], y + d[1]) not in g: g[x + d[0], y + d[1]] = K
drop = H - 1 - max(y for x, y in g)
f = Image.new('RGBA', (W, H))
for (x, y), c in g.items():
    if 0 <= x < W and 0 <= y + drop < H: f.putpixel((x, y + drop), c + (255,))
px = f.load()
for _ in range(2):                                            # lone pixels join what surrounds them
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            c = px[x, y]
            if not c[3] or c[:3] in (K, RED, IVORY): continue
            near = [px[x + d[0], y + d[1]] for d in N8]
            if not any(n[3] and n[:3] == c[:3] for n in near):
                pick = Counter(n[:3] for n in near if n[3] and n[:3] != K).most_common(1)
                if pick: px[x, y] = pick[0][0] + (255,)
f.save(HERE / 'frame0.png'); print(f.getbbox(), drop)
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(f); bg.crop((6, 14, 42, 50)).resize((576, 576), 0).save(HERE / 'frame0_head_x16.png')
