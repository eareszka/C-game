"""The impact key with less reach (the user, 2026-11-18: "make it extend out less"): k-slam-96 with the duplicate
columns of its straight tail shaft removed (each run of identical columns kept once), everything right of them slid
in -- no px drawn, the ball and its dust unchanged. Writes pixellab/k-short-96.png."""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); PL = os.path.join(HERE, 'pixellab')
DROP = (52, 53, 56, 61, 62, 63, 64)   # in runs 51-53, 55-56, 60-64 of identical columns
k = Image.open(os.path.join(PL, 'k-slam-96.png')).convert('RGBA'); W, H = k.size
col = lambda x: [k.getpixel((x, y)) for y in range(H)]
assert all(col(x) == col(x - 1) for x in DROP), 'not duplicate columns'
out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); nx = 0
for x in range(W):
    if x in DROP: continue
    out.paste(k.crop((x, 0, x + 1, H)), (nx, 0)); nx += 1
out.save(os.path.join(PL, 'k-short-96.png')); print('reach in by', len(DROP), 'px')
