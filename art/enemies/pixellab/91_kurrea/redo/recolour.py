"""91 Kurrea redo: frame0.png in the Celestial Stag's reality-shard colours (the user, 2026-11-03: "have the rainbow pattern be like
celestial stag/reality shard colors"): the coat's three purples, and the torch's pale rainbow as 37's stripes() draws it, slanted
stripes two pixels wide. Two versions:
  bands   the orange bands rainbow, the green stretches lilac
  coils   the green stretches rainbow too, the orange bands lilac

    python art/enemies/pixellab/91_kurrea/redo/recolour.py   # writes frame0_bands.png frame0_coils.png board_shard.png
"""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
RED, DARK, ORANGE = (0xb6, 0x43, 0x3d), (0x53, 0x1b, 0x1c), (0xd8, 0x98, 0x30)
GREEN, GREEN_D = (0x29, 0x63, 0x3e), (0x14, 0x2e, 0x1f)
COAT, SHADE, LILAC = (0x66, 0x4b, 0x95), (0x2b, 0x1f, 0x40), (0xb6, 0x9c, 0xee)
RAINBOW = [(0xec, 0x84, 0x76), (0xfa, 0xe4, 0x88), (0xa8, 0xf0, 0xbc), (0x84, 0xa7, 0xe9)]
EYE = (48, 15)                       # frame coordinates of the eye's first pixel (source 50,12 + offset -2,+3)
HEAD = lambda x, y: y <= 30 and x >= 38


def stripe(x, y):
    return RAINBOW[((x + y + 64) // 2) % len(RAINBOW)]


def make(name, band_rainbow):
    im = Image.open(HERE / 'frame0.png').convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if not c[3]: continue
            c = c[:3]
            if c == RED: n = COAT
            elif c == DARK: n = SHADE
            elif c == ORANGE: n = stripe(x, y) if band_rainbow else LILAC
            elif c == GREEN: n = LILAC if band_rainbow else stripe(x, y)
            elif c == GREEN_D: n = COAT if band_rainbow else SHADE
            else: continue
            px[x, y] = n + (255,)
    for p in (EYE, (EYE[0] + 1, EYE[1])): px[p] = (0xfa, 0xe4, 0x88, 255)   # the eye: one pale mark
    im.save(HERE / f'frame0_{name}.png')
    return im


W, H, S = 98, 65, 7
b = Image.new('RGBA', (W * S * 2, H * S), (0x6f, 0x9e, 0x5c, 255))
for i, (n, flag) in enumerate((('bands', True), ('coils', False))):
    b.alpha_composite(make(n, flag).resize((W * S, H * S), 0), (i * W * S, 0))
b.save(HERE / 'board_shard.png')
