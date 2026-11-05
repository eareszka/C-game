"""The source sent to PixelLab for 40's mini: its approved battle frame shrunk in blocks to about mini size
(a PixelLab mini gets its first frame at about the size it should come back at). Writes first_tiny.png, x6 too."""
from pathlib import Path
from collections import Counter
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis
im = minis.battle_views(40)['D']; im = im.crop(im.getbbox())
TW = 28; s = TW / im.width; TH = round(im.height * s)
out = Image.new('RGBA', (40, 32))
for y in range(TH):
    for x in range(TW):
        blk = [im.getpixel((i, j)) for j in range(int(y / s), max(int(y / s) + 1, int((y + 1) / s)))
               for i in range(int(x / s), max(int(x / s) + 1, int((x + 1) / s)))]
        sol = [p for p in blk if p[3]]
        if len(sol) * 2 < len(blk): continue
        c = Counter(sol).most_common(1)[0][0]
        out.putpixel((x + (40 - TW) // 2, y + 32 - TH - 2), c)
here = Path(__file__).parent
out.save(here / 'first_tiny.png')
out.resize((240, 192), 0).save(here / 'first_tiny_x6.png')
print(out.getbbox())
