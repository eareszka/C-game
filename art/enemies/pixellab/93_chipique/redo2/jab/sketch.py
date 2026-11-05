"""93 Chipique redraw, second sketch (the user, 2026-11-03: "canoe should look painfully jabbed through the snake, snake should be thick enough
so the canoe can fit through it"). A body far wider than the hull; the canoe at a slant, its middle HIDDEN inside the body, its ends coming out
through raw wounds on either side, blood running from them. A source for PixelLab, not final art. Writes jab/sketch.png.

    python art/enemies/pixellab/93_chipique/redo2/jab/sketch.py
"""
from pathlib import Path
import math
from PIL import Image
HERE = Path(__file__).resolve().parent
K, NAVY, NAVY_D = (0, 0, 0), (0x23, 0x38, 0x5c), (0x14, 0x22, 0x3c)
BELLY, BELLY_D, SLATE = (0xd8, 0xc8, 0x9c), (0xa8, 0x94, 0x6c), (0x74, 0x80, 0x90)
WOOD, WOOD_D, RED, RED_D = (0x8a, 0x5a, 0x34), (0x55, 0x34, 0x20), (0xb6, 0x2c, 0x2c), (0x6c, 0x10, 0x18)
W, H = 96, 64
g = {}


def disc(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and 0 <= x < W and 0 <= y < H: g[x, y] = c


AX, AY, BX, BY = 2, 16, 94, 44     # the canoe's line, bow high on the left, stern low on the right
def canoe(p):
    x, y = p
    t = ((x - AX) * (BX - AX) + (y - AY) * (BY - AY)) / ((BX - AX) ** 2 + (BY - AY) ** 2)
    if not 0 <= t <= 1: return None
    d = abs((BX - AX) * (AY - y) - (AX - x) * (BY - AY)) / math.hypot(BX - AX, BY - AY)
    half = 1.5 + 5.5 * min(1, 2.6 * min(t, 1 - t))
    if d > half: return None
    return WOOD_D if d > half - 1.6 and ((BX - AX) * (y - AY) - (BY - AY) * (x - AX)) > 0 else WOOD


for x in range(W):                 # the canoe first: the body goes over its middle
    for y in range(H):
        c = canoe((x, y))
        if c: g[x, y] = c
for x in range(26, 72): disc(x, 57, 6, NAVY_D)     # its low coil
body = {}
for y in range(16, 60):            # the great thick body
    r = 17 + round(3 * math.exp(-((y - 32) / 8) ** 2))   # swollen round the wound
    cx = 48
    for x in range(cx - r, cx + r + 1):
        if 0 <= x < W: body[x, y] = NAVY
g.update(body)
for (x, y) in body:                # the pale belly down its front
    if abs(x - 44) <= 8 and y >= 22: g[x, y] = BELLY_D if abs(x - 44) >= 7 else BELLY
for r, (cx, cy) in zip((10, 9, 7), ((48, 14), (42, 11), (36, 11))): disc(cx, cy, r, SLATE)   # the head, small for that body
for (cx, cy), n in (((28, 24), 6), ((68, 36), 6)):  # the wounds: raw round where the hull goes in and comes out
    disc(cx, cy, n, RED_D); disc(cx, cy, n - 2, RED)
for x in range(W):                 # the hull's ends again over the wound's outer half
    for y in range(H):
        c = canoe((x, y))
        if c and (x < 28 or x > 68): g[x, y] = c
for x, y0, n in ((26, 30, 12), (30, 30, 7), (66, 42, 10), (70, 42, 6)):   # blood running down
    for y in range(y0, y0 + n): g[x, y] = RED; g[x + 1, y] = RED_D
out = Image.new('RGBA', (W, H))
for p, c in g.items():
    if 0 <= p[0] < W and 0 <= p[1] < H: out.putpixel(p, c + (255,))
px = out.load()
for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]]:
    if any(0 <= x + a < W and 0 <= y + b < H and px[x + a, y + b][3] and px[x + a, y + b][:3] != K for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        px[x, y] = K + (255,)
out.save(HERE / 'sketch.png')
print(out.getbbox())
