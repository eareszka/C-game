"""The source sent to PixelLab for 40's mini: the approved battle frame (../frame0.png) shrunk in blocks to mini size,
30 px wide. Writes first_small.png and first_small_x6.png."""
from pathlib import Path
from collections import Counter
from PIL import Image
here = Path(__file__).parent
im = Image.open(here.parent / 'frame0.png').convert('RGBA'); im = im.crop(im.getbbox())
TW = 30; s = TW / im.width; TH = round(im.height * s)
out = Image.new('RGBA', (40, 32))
for y in range(TH):
    for x in range(TW):
        blk = [im.getpixel((i, j)) for j in range(int(y / s), max(int(y / s) + 1, int((y + 1) / s)))
               for i in range(int(x / s), max(int(x / s) + 1, int((x + 1) / s)))]
        sol = [p for p in blk if p[3]]
        if len(sol) * 2 < len(blk): continue
        out.putpixel((x + 5, y + 32 - TH - 3), Counter(sol).most_common(1)[0][0])
out.save(here / 'first_small.png')
out.resize((240, 192), 0).save(here / 'first_small_x6.png')
print(out.getbbox())
