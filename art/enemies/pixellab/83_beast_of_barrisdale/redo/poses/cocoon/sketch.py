"""83 redo: rough source for the block (the user: "the wings should completely cover instead of being extended, use
pixellab"): both wings wrapped right round the body like a roosting bat, only the feet below. Not final art: PixelLab
redraws it. Writes sketch.png (100x68, feet on the fly pose's row + the 2-row padding).

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/poses/cocoon/sketch.py
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
K, MID, DARK = (0, 0, 0), (0x59, 0x59, 0x65), (0x47, 0x47, 0x51)
SALMON, RIB = (0xec, 0x84, 0x76), (0xb6, 0x43, 0x3d)
W, H = 100, 68
g = {}
CX, CY, RX, RY = 50, 33, 23, 25
inside = lambda x, y: ((x - CX) / RX) ** 2 + ((y - CY) / RY) ** 2 <= 1
for y in range(H):
    for x in range(W):
        if inside(x, y) and not (y > 50 and (x // 7) % 2 == 0 and y > 54):     # scalloped hem
            g[x, y] = RIB if x > 55 or x < 33 else SALMON
for y in range(H):                                                              # the near wing's edge lapping over, the ribs
    for x in range(W):
        if (x, y) in g:
            if x == 54 - (y - 8) // 6: g[x, y] = K
            if x in (38, 66) and y > 16 and y % 1 == 0: g[x, y] = RIB
            if x == 44 + (y - 12) // 8 or x == 62 - (y - 12) // 10: g[x, y] = K
for x, y0 in ((36, 8), (64, 8)):                                                # the wrists on top
    for y in range(y0, y0 + 8):
        for dx in (-1, 0, 1, 2): g[x + dx, y + (x - 50) // 8 + 2] = MID
for fx in (40, 50, 60):                                                         # three feet below the hem
    for y in range(54, 60):
        for dx in range(0, 3): g.setdefault((fx + dx, y), DARK)
    for dx in range(-2, 5):
        g[fx + dx, 59] = SALMON
        g[fx + dx, 58] = SALMON
out = Image.new('RGBA', (W, H))
for p, c in g.items(): out.putpixel(p, c + (255,))
px = out.load()
for x, y in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]]:
    if any(0 <= x + a < W and 0 <= y + b < H and px[x + a, y + b][3] and px[x + a, y + b][:3] != K for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        px[x, y] = K + (255,)
out.save(HERE / 'sketch.png')
print(out.getbbox())
