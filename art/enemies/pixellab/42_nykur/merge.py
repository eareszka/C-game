"""42 Nykur's frame 0 down to six colours and black: the clean's near-duplicate greys and weed greens folded.

    python art/enemies/pixellab/42_nykur/merge.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MERGE = {'0e2016': '142e1f', '163623': '235436', 'c6ccda': 'bcbeca', 'a4aaba': '848694', '282828': '474751'}
im = Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA')
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MERGE:
            im.putpixel((x, y), h(MERGE[k]) + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(len({q[:3] for q in im.get_flattened_data() if q[3]}) - 1, 'colours + black')
