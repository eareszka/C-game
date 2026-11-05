"""20 Sermilik's frame 0: PixelLab's icy draft snapped to the whole game palette (the old sheet's few colours had
turned its ice to grey), then its stray single pixels folded into their neighbours -- six colours and black.

    python art/enemies/pixellab/20_sermilik/merge.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
MERGE = {'c6ccda': 'bcbeca', '34343e': '848694', '3e91cc': '84a7e9'}
im = Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA')
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        k = '%02x%02x%02x' % p[:3]
        if p[3] and k in MERGE:
            im.putpixel((x, y), h(MERGE[k]) + (255,))
im.save(HERE / 'idle_frame0_clean.png')
print(len({q[:3] for q in im.get_flattened_data() if q[3]}) - 1, 'colours + black')
