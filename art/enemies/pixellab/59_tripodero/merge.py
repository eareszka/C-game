"""59 Tripodero's frame 0 merged to eight colours and black: the clean's near-duplicates (PixelLab's greens and
leg browns) folded into the reference's ramps -- the green head and tail, the orange body and its dark
stripes, the brown legs (the user, 2026-10-28: look more like abookofcreatures.com's tripodero).

    python art/enemies/pixellab/59_tripodero/merge.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MERGE = {'2c6c44': '29633e', '235436': '29633e', '633e1b': '3c2412', '583518': '3c2412', '2b190e': '3c2412',
         '815423': '785830', 'e8e0c0': 'f4ce80', 'b2966a': '967448', 'c18a39': 'fc9838'}
im = Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA')
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MERGE:
            im.putpixel((x, y), h(MERGE[k]) + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(len({p[:3] for p in im.get_flattened_data() if p[3]}), 'colours with black')
