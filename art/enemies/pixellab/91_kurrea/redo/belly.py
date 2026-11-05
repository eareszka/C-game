"""91 Kurrea redo: the rainbow as its whole underside (the user, 2026-11-03: "right but have the rainbow part be the entire underside
of the snake"). frame0.png's green stretches go to the coat, its bands lilac; then a continuous band along the belly's line, head to
tail, takes the torch's rainbow, slanted stripes two pixels wide, as the Celestial Stag's antlers.

    python art/enemies/pixellab/91_kurrea/redo/belly.py   # writes frame0_belly.png, frame0_belly_x8.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
RED, DARK, ORANGE = (0xb6, 0x43, 0x3d), (0x53, 0x1b, 0x1c), (0xd8, 0x98, 0x30)
GREEN, GREEN_D = (0x29, 0x63, 0x3e), (0x14, 0x2e, 0x1f)
COAT, SHADE, LILAC = (0x66, 0x4b, 0x95), (0x2b, 0x1f, 0x40), (0xb6, 0x9c, 0xee)
RAINBOW = [(0xec, 0x84, 0x76), (0xfa, 0xe4, 0x88), (0xa8, 0xf0, 0xbc), (0x84, 0xa7, 0xe9)]
K = (0, 0, 0)
W, H = 98, 65
EYE = (48, 15)                                  # frame coordinates (source 50,12 + offset -2,+3)


def stripe(x, y):
    return RAINBOW[((x + y + 64) // 2) % len(RAINBOW)]


im = Image.open(HERE / 'frame0.png').convert('RGBA')
px = im.load()
MAP = {RED: COAT, DARK: SHADE, ORANGE: LILAC, GREEN: COAT, GREEN_D: SHADE}
base = {}
for y in range(H):
    for x in range(W):
        c = px[x, y]
        if c[3]: base[x, y] = MAP.get(c[:3], c[:3])
# The belly's line, by eye on the frame, head to tail: the band follows it, one continuous stretch, clipped to the body.
LINES = [[(30, 20), (36, 18), (37, 22), (41, 30), (41, 34), (36, 39), (31, 43), (30, 48), (30, 54), (33, 60), (46, 60), (58, 59),
          (70, 58), (80, 55), (84, 51)],
         [(14, 60), (29, 60)]]
RADIUS = 2.6


def dist(p, a, b):
    ax, ay, bx, by = *a, *b
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return ((p[0] - ax - t * dx) ** 2 + (p[1] - ay - t * dy) ** 2) ** 0.5


out = dict(base)
for p, c in base.items():
    if c == K or c == (0xe8, 0xe0, 0xc0): continue
    if any(dist(p, l[i], l[i + 1]) <= RADIUS for l in LINES for i in range(len(l) - 1)):
        out[p] = stripe(*p)
for p in (EYE, (EYE[0] + 1, EYE[1])): out[p] = RAINBOW[1]
res = Image.new('RGBA', (W, H))
for p, c in out.items(): res.putpixel(p, c + (255,))
res.save(HERE / 'frame0_belly.png')
bg = Image.new('RGBA', (W, H), (0x6f, 0x9e, 0x5c, 255)); bg.alpha_composite(res)
bg.resize((W * 8, H * 8), 0).save(HERE / 'frame0_belly_x8.png')
