"""45 Kusa Kap redo: concept c1's design in c2's colours (the user, 2026-11-02: "top left design with top rights colors").
Slate wings: rust near the body and along the leading edge, black out at the feather ends. White head: rust; pale
breast: cream. Beak, talons and dugong stay. A rough source for a PixelLab edit, not final art. Writes source.png.

    python art/enemies/pixellab/45_kusa_kap/redo/blend/recolour.py
"""
from pathlib import Path
import colorsys
from PIL import Image
HERE = Path(__file__).resolve().parent
im = Image.open(HERE.parent / 'concepts/c1.png').convert('RGBA')
px = im.load()
RUST_L, RUST, RUST_D, BLK_L, BLK = (0xb6, 0x5a, 0x3a), (0x8c, 0x3a, 0x26), (0x5c, 0x22, 0x1c), (0x2c, 0x1c, 0x1e), (0x12, 0x0c, 0x0e)
CREAM, CREAM_D = (0xf0, 0xdc, 0xa8), (0xc8, 0xa8, 0x78)
CX = 47
for y in range(im.height):
    for x in range(im.width):
        r, g, b, a = px[x, y]
        if not a: continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        warm = (h < 0.17 or h > 0.95) and s > 0.35                     # the beak and talons
        if warm: continue
        d = abs(x - CX)
        if y >= 42 and s < 0.22: continue                               # the dugong, grey and unsaturated
        if d <= 7 and 16 <= y <= 29 and v > 0.55: c = RUST_L if v > 0.8 else RUST                     # the head
        elif d <= 7 and 26 <= y <= 36 and v > 0.5: c = CREAM if v > 0.75 else CREAM_D                 # the breast
        elif d <= 10:                                                   # the body
            c = RUST if v > 0.28 else RUST_D if v > 0.16 else BLK
        else:                                                           # the wings, rust to black going out
            t = (d - 10) / 34
            if v < 0.1: c = BLK
            elif t < 0.45: c = RUST_L if v > 0.42 else RUST if v > 0.28 else RUST_D
            elif t < 0.65: c = RUST_D if v > 0.28 else BLK_L
            else: c = BLK_L if v > 0.28 else BLK
        px[x, y] = c + (255,)
im.save(HERE / 'source.png')
