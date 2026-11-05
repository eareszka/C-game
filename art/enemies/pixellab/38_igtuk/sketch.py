"""38 Igtuk redrawn from scratch after A Book of Creatures' illustration (reference_abookofcreatures.jpg, from
abookofcreatures.com/2019/07/22/igtuk; the user, 2026-10-30: "it should look like the book of creatures
reference", none of four PixelLab concepts). The Inuit spirit whose jaws make the booming in the mountains: its
limbs on the back of its body, one large eye level with them, ears in line with the eye, its nose inside its
cavernous mouth, a tuft of hair on its chin (Anarqaq's account) -- drawn there as a long blue-grey beast on four
long legs with curled feet, the great eye, a huge upturned jaw, a dark shaggy beard and a hair tuft at its
snout's tip. The creature cut from its white ground (the map inset and the pink size figures left out), shrunk
onto the 98x65 canvas, on the game palette's nearest colours, outlined in black: the rough sketch PixelLab's
edit cleans into the house style (source_idle.png). Also writes base/38_igtuk.png: the old sheet padded into
98x65 cells, the job's "png", sized as the sheet it will become.

    python art/enemies/pixellab/38_igtuk/sketch.py
"""
from pathlib import Path
import sys
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(ROOT / 'tools'))
import fcremap as fc, first_frame as ff

W, H, GROUND = 98, 65, 64
FIT = (86, 58)          # inside the canvas with padding all round (the bible)
old = Image.open(ROOT / 'assets/enemies/38_igtuk.png').convert('RGBA')
CW, CH = old.width // 24, old.height
base = Image.new('RGBA', (W * 24, H))
for i in range(24):
    base.alpha_composite(old.crop((i * CW, 0, i * CW + CW, CH)), (i * W + (W - CW) // 2, H - CH))
base.save(HERE / 'base/38_igtuk.png')

im = Image.open(HERE / 'reference_abookofcreatures.jpg').convert('RGB')
sx, sy = im.width / 985, im.height / 612          # the boxes below measured on the 985-wide copy the user sent
a = Image.new('L', im.size, 0)
px, ap = im.load(), a.load()
for y in range(im.height):
    for x in range(im.width):
        if min(px[x, y]) < 205:
            ap[x, y] = 255
for x0, y0, x1, y1 in ((815, 0, 985, 150), (755, 480, 985, 612)):     # the map inset, the size figures
    for y in range(int(y0 * sy), min(im.height, int(y1 * sy))):
        for x in range(int(x0 * sx), min(im.width, int(x1 * sx))):
            ap[x, y] = 0
a = a.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(9))
rgba = im.convert('RGBA')
rgba.putalpha(a)
c = rgba.crop(a.getbbox())
s = min(FIT[0] / c.width, FIT[1] / c.height)
sm = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
pal = list(ff.game_palette())
lab = {p: fc._lab(p) for p in pal}
out = Image.new('RGBA', (W, H))
ox, oy = (W - sm.width) // 2, GROUND + 1 - sm.height
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
o.save(HERE / 'source_idle.png')
print('sketch', o.getbbox(), sm.size)
