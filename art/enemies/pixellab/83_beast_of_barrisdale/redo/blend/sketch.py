"""83 redo: concept 2 (the wolf, mirrored to face left) with the original's colours roughly painted on, as a source
for a PixelLab edit (the user: "top right but more similar to the original"). Salmon wings ribbed red, pink face and
feet, tail removed. Writes sketch.png.

    python art/enemies/pixellab/83_beast_of_barrisdale/redo/blend/sketch.py
"""
from pathlib import Path
import colorsys
from PIL import Image
HERE = Path(__file__).parent
im = Image.open(HERE.parent / 'c2_left.png').convert('RGBA')
px = im.load()
E, L, R, DK, K = (0xec, 0x84, 0x76), (0xf0, 0xb8, 0x90), (0xb6, 0x43, 0x3d), (0x42, 0x16, 0x18), (0, 0, 0)
for y in range(im.height):
    for x in range(im.width):
        r, g, b, a = px[x, y]
        if not a: continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if x > 62 and y > 34:                       # the tail: gone
            px[x, y] = (0, 0, 0, 0); continue
        if y < 34 and x > 26 and s > 0.2 and v > 0.2:   # the wing membranes
            px[x, y] = (E if v > 0.33 else R) + (255,)
        elif y >= 50 and v > 0.14:                  # the feet
            px[x, y] = (E if v > 0.3 else L) + (255,)
        elif x < 27 and 26 < y < 45 and s < 0.25 and v > 0.25:   # the face
            px[x, y] = (L if v > 0.42 else E) + (255,)
im.save(HERE / 'sketch.png')
