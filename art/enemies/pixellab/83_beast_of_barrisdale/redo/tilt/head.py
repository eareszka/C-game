"""83 redo: the head from PixelLab's tilt t1 (the user: "have the face tilted downward toward the player using
pixellab") grafted onto the approved frame0.png. t1 also grew an extra leg and shifted the body, so only the head is
taken. Its colours fold onto frame0's; two 1-2 px eye marks kept; one closed outline. frame0.png itself is left alone.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/tilt/head.py   # writes frame0_tilt.png/.x8 beside frame0.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
W, H = 100, 65
K = (0, 0, 0)
LIGHT, MID, DARK = (0x84, 0x86, 0x94), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)
SALMON, RIB, PALE, MOUTH = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d), (0xf0, 0xb8, 0x90), (0x42, 0x16, 0x18)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
RIGHT, TOP, BOTTOM = 33, 32, 54     # the graft's box on the frame (t1 sits 2 rows lower: its padding)


def fold(p, x):
    r, g, b = p
    if max(p) < 0x14: return K
    if max(p) - min(p) < 24:
        return LIGHT if max(p) >= 0x68 else MID if max(p) >= 0x50 else DARK
    if x >= 31: return LIGHT                       # t1's stray wing-red on the neck
    return min((SALMON, RIB, PALE, MOUTH), key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))


base = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
t = Image.open(HERE / 't1.png').convert('RGBA')
g = {(x, y): base.getpixel((x, y))[:3] for y in range(H) for x in range(W) if base.getpixel((x, y))[3]}
# frame0's own head and neck front go
for p in [p for p in g if p[0] <= RIGHT and TOP <= p[1] <= BOTTOM - 3]: del g[p]
for y in range(TOP, BOTTOM + 1):
    for x in range(0, RIGHT + 1):
        c = t.getpixel((x, y + 2))
        if c[3] > 127: g[x, y] = fold(c[:3], x)
# drop what no longer joins the body
start = (60, 45); seen = {start}; todo = [start]
while todo:
    a = todo.pop()
    for dx, dy in N4:
        q = (a[0] + dx, a[1] + dy)
        if q in g and q not in seen: seen.add(q); todo.append(q)
g = {p: g[p] for p in seen}
edge = [p for p, c in g.items() if c == K and any((p[0] + a, p[1] + b) not in g for a, b in N4)]
for p in edge: del g[p]
for x, y in list(g):
    for a, b in N4:
        if (x + a, y + b) not in g: g[x + a, y + b] = K
for p, c in {(33, 33): LIGHT, (29, 37): K, (29, 38): LIGHT, (21, 42): PALE, (28, 50): MOUTH, (24, 52): K}.items():
    g[p] = c                                        # lone pixels merged into what surrounds them (not the eye at 28,45)
out = Image.new('RGBA', (W, H))
for p, c in g.items(): out.putpixel(p, c + (255,))
out.save(HERE.parent / 'frame0_tilt.png')
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(out)
bg.resize((W * 8, H * 8), 0).save(HERE.parent / 'frame0_tilt_x8.png')
L = {K: '#', LIGHT: 'l', MID: 'm', DARK: 'd', SALMON: 's', RIB: 'r', PALE: 'p', MOUTH: 'x'}
for y in range(30, 58): print('%2d ' % y + ''.join(L.get(g.get((x, y)), '.') for x in range(16, 42)))
