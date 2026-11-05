"""93 Chipique redraw: a rough sketch for PixelLab (the user, 2026-11-03: "a tall girthy snake with a canoe through the middle of it like a
stick through the heart"). A thick upright column of snake rising from a low coil, a small slate head on top, a brown dugout canoe crossing
straight through its middle, both ends showing. Not final art. Writes concepts/sketch.png.

    python art/enemies/pixellab/93_chipique/redo2/sketch.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
K, NAVY, NAVY_D = (0, 0, 0), (0x23, 0x38, 0x5c), (0x14, 0x22, 0x3c)
BELLY, SLATE, WOOD, WOOD_D = (0x84, 0x96, 0xa8), (0x74, 0x80, 0x90), (0x8a, 0x5a, 0x34), (0x55, 0x34, 0x20)
W, H = 96, 64
g = {}
def disc(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and 0 <= x < W and 0 <= y < H: g[x, y] = c
for y in range(14, 58):                                 # the tall thick body, a slow lean
    cx = 48 + round(3 * __import__('math').sin((y - 14) / 44 * 3.14))
    disc(cx, y, 11, NAVY)
for x in range(30, 74):                                 # its low coil
    disc(x, 55, 6, NAVY_D)
for y in range(20, 58):                                 # the pale belly down its front
    cx = 45 + round(3 * __import__('math').sin((y - 14) / 44 * 3.14))
    for x in range(cx - 4, cx + 4): g[x, y] = BELLY
for r, (cx, cy) in zip((6, 5, 4), ((48, 12), (44, 10), (40, 10))):   # the small slate head
    disc(cx, cy, r, SLATE)
for x in range(10, 88):                                 # the canoe, straight through
    half = max(1, 5 - abs(x - 49) // 9)
    for y in range(34 - half, 34 + half + 1):
        g[x, y] = WOOD_D if y >= 34 + half - 1 else WOOD
for x in range(38, 60):                                 # its hull's hollow
    g[x, 32] = WOOD_D
out = Image.new('RGBA', (W, H))
for p, c in g.items(): out.putpixel(p, c + (255,))
px = out.load()
for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]]:
    if any(0 <= x + a < W and 0 <= y + b < H and px[x + a, y + b][3] and px[x + a, y + b][:3] != K for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        px[x, y] = K + (255,)
out.save(HERE / 'concepts/sketch.png')
print(out.getbbox())
