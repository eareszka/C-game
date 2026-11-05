"""The source sent to PixelLab for 18's mini: the approved battle frame shrunk in blocks to its mini's size. The user's standing wish
for this mini (2026-10-14): big and intimidating, one drawing every way, moving pretty much straight. 42 px tall on a 80x48 canvas."""
from pathlib import Path
from collections import Counter
from PIL import Image
here = Path(__file__).parent
im = Image.open(here.parent / 'frame0.png').convert('RGBA'); im = im.crop(im.getbbox())
TH = 42; s = TH / im.height; TW = round(im.width * s)
out = Image.new('RGBA', (80, 48))
for y in range(TH):
    for x in range(TW):
        blk = [im.getpixel((i, j)) for j in range(int(y / s), max(int(y / s) + 1, int((y + 1) / s)))
               for i in range(int(x / s), max(int(x / s) + 1, int((x + 1) / s)))]
        sol = [p for p in blk if p[3]]
        if not sol: continue
        col = [p for p in sol if p[:3] != (0, 0, 0)]
        out.putpixel((x + (80 - TW) // 2, y + 48 - TH - 3), Counter(col or sol).most_common(1)[0][0])
out.save(here / 'first_small.png'); print(out.getbbox(), TW, TH)
