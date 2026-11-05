"""19 Skeljaskrimsli redrawn after the user's reference (reference_user.jpg, 2026-10-29: "this is the reference
for it: redo it please but make sure its still 4 directional"). The creature cut from its white ground (the
map inset and the pink size figures left out), shrunk to fit the 86x43 canvas, on the game palette's nearest
colours, outlined in black: the rough sketch PixelLab's edit cleans into the house style (source_idle.png).

    python art/enemies/pixellab/19_skeljaskrimsli/sketch.py
"""
from pathlib import Path
import shutil, sys
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(ROOT / 'tools'))
import fcremap as fc, first_frame as ff

W, H, GROUND = 86, 43, 41
FIT = (80, 36)          # inside the canvas with padding all round (the bible; the user: "fit the game's enemy sizes")
im = Image.open(HERE / 'reference_user.jpg').convert('RGB')
a = Image.new('L', im.size, 0)
px, ap = im.load(), a.load()
for y in range(im.height):
    for x in range(im.width):
        if min(px[x, y]) < 205:
            ap[x, y] = 255
for x0, y0, x1, y1 in ((10, 10, 130, 90), (455, 0, 650, 80)):     # the map inset, the size figures
    for y in range(y0, y1):
        for x in range(x0, x1):
            ap[x, y] = 0
a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
rgba = im.convert('RGBA')
rgba.putalpha(a)
c = rgba.crop(a.getbbox())
s = min(FIT[0] / c.width, FIT[1] / c.height)
sm = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
pal = list(ff.game_palette())
lab = {p: fc._lab(p) for p in pal}
out = Image.new('RGBA', (W, H))
ox, oy = (W - sm.width) // 2, GROUND - sm.height
for y in range(sm.height):
    for x in range(sm.width):
        p = sm.getpixel((x, y))
        if p[3] < 140:
            continue
        l = fc._lab(p[:3])
        out.putpixel((ox + x, oy + y), min(pal, key=lambda q: sum((u - v) ** 2 for u, v in zip(l, lab[q]))) + (255,))
o = out.copy()
for y in range(H):
    for x in range(W):
        if out.getpixel((x, y))[3] and out.getpixel((x, y))[:3] != (0, 0, 0):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if 0 <= q[0] < W and 0 <= q[1] < H and not out.getpixel(q)[3]:
                    o.putpixel(q, (0, 0, 0, 255))
if not (HERE / 'source_idle_old_sheet.png').exists():
    shutil.copy(HERE / 'source_idle.png', HERE / 'source_idle_old_sheet.png')
o.save(HERE / 'source_idle.png')
print('sketch', o.getbbox(), sm.size)
