"""29 Karnabo, darker (the user, 2026-11-03: "same design but darker colors"): frame0_light.png's exact shapes, one colour swap: skin mint to green 4fa667, its shade to 2c6c44, robe slate to 474751, its shade to 34343e -> 282828 kept apart from the black outline. Eyes stay.

    python art/enemies/pixellab/29_karnabo/redo/darker.py   # frame0.png, frame0_x8.png, frame0_black_x8.png, frame0_compare.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
MAP = {(0xa8, 0xf0, 0xbc): (0x4f, 0xa6, 0x67), (0x4f, 0xa6, 0x67): (0x2c, 0x6c, 0x44), (0x59, 0x59, 0x65): (0x47, 0x47, 0x51), (0x34, 0x34, 0x3e): (0x28, 0x28, 0x28)}
src = Image.open(HERE / 'frame0_light.png').convert('RGBA')
W, H = src.size
f = Image.new('RGBA', (W, H))
for y in range(H):
    for x in range(W):
        p = src.getpixel((x, y))
        if p[3]: f.putpixel((x, y), MAP.get(p[:3], p[:3]) + (255,))
f.save(HERE / 'frame0.png')
for name, col in (('frame0_x8.png', (0x6f, 0x9e, 0x5c, 255)), ('frame0_black_x8.png', (0, 0, 0, 255))):
    bg = Image.new('RGBA', (W, H), col); bg.alpha_composite(f); bg.resize((W * 8, H * 8), 0).save(HERE / name)
c = Image.new('RGBA', (W * 12 + 10, H * 6), (0, 0, 0, 255))
c.alpha_composite(src.resize((W * 6, H * 6), 0), (0, 0)); c.alpha_composite(f.resize((W * 6, H * 6), 0), (W * 6 + 10, 0)); c.save(HERE / 'frame0_compare.png')
