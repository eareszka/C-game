"""19 Skeljaskrimsli has no eyes (the user, 2026-10-29: "no eyes for this monster"): the two green glints at the
top corners of its turned head, which read as eyes, painted over in the head's dark plate colour. Only the
green above the teeth's ring (rows 21-22) goes; the teeth stay. Run after merge.py.

    python art/enemies/pixellab/19_skeljaskrimsli/no_eyes.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
GREENS = {(0xa8, 0xf0, 0xbc), (0x2c, 0x6c, 0x44)}
PLATE = (0x34, 0x34, 0x3e)
im = Image.open(HERE / 'idle_frame0_clean.png').convert('RGBA')
gone = 0
for y in (21, 22):
    for x in range(0, 30):
        p = im.getpixel((x, y))
        if p[3] and p[:3] in GREENS:
            im.putpixel((x, y), PLATE + (255,))
            gone += 1
im.save(HERE / 'idle_frame0_clean.png')
print(gone, 'eye px gone')
