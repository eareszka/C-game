"""65 at the small sprites' size (the user: "small sized like the small sized sprites"; 01 and 03 are 20x20): frame0.png
shrunk in blocks to `TW` px wide, a source for PixelLab and a comparison. Writes small_shrink.png on a 32x32 canvas.

    python art/enemies/pixellab/65_mice_that_eat_iron/small.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).parent
TW = 28
im = Image.open(HERE / 'frame0.png').convert('RGBA')
im = im.crop(im.getbbox())
s = TW / im.width
TH = round(im.height * s)
out = Image.new('RGBA', (32, 32))
for y in range(TH):
    for x in range(TW):
        blk = [im.getpixel((i, j)) for j in range(int(y / s), max(int(y / s) + 1, int((y + 1) / s)))
               for i in range(int(x / s), max(int(x / s) + 1, int((x + 1) / s)))]
        sol = [p for p in blk if p[3]]
        if len(sol) * 2 < len(blk): continue
        col = [p for p in sol if p[:3] != (0, 0, 0)]
        out.putpixel((x + 2, y + 32 - TH - 2), Counter(col or sol).most_common(1)[0][0])
out.save(HERE / 'small_shrink.png')
print(out.getbbox())
