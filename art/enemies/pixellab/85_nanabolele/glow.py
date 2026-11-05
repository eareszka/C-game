"""85 Nanabolele's glowing scale lights put back where PixelLab's rotate left them off (the front and the
three-quarter; the side and back views kept theirs). Its attacks leave from them (src/enemies.cpp), so every
view shows them: a row of small glow-green spines along the top of its back, each its own outlined shape on
the black seam of the back, and on the three-quarter a glow flame at its tail tip, as the side view's.
Run after eyes.py and before tidy.py (it closes the outline round what it adds; tidy then thins the black).

    python art/enemies/pixellab/85_nanabolele/glow.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
G, BLACK = (0x4e, 0xdc, 0x4a, 255), (0, 0, 0, 255)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SPINES = {'idle_view_DR.png': [(x, 0) for x in range(31, 55, 3)],   # along its back, tail root to neck
          'idle_frame0_clean.png': [(37, 30), (59, 30)]}       # each shoulder: searched from row 30, below the horns
FLAME = {'idle_view_DR.png': [(20, 28), (21, 28), (22, 28), (21, 27), (20, 27), (21, 26), (22, 27), (19, 27), (20, 26)]}
for f in SPINES:
    im = Image.open(HERE / f).convert('RGBA')
    px, W, H = im.load(), im.width, im.height
    for x, below in SPINES[f]:
        y = next(y for y in range(below, H) if px[x, y][3])    # the top of its back here: the outline
        for p in ((x, y - 1), (x + 1, y - 1), (x, y - 2)):
            px[p] = G
    for p in FLAME.get(f, ()):
        px[p] = G
    at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    for (x, y) in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]
                   and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != BLACK[:3] for dx, dy in N4)]:
        px[x, y] = BLACK
    im.save(HERE / f)
    print(f, 'lights painted')
