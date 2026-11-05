"""80 Bes Kotak with no tongue (the user, 2026-10-28: "no orange tongue"): PixelLab put an orange tongue in its
gaping mouth. The eyes are drawn in the same orange (their shade under the yellow), so only orange below the
eyes goes -- more than a pixel under the lowest yellow of that frame -- into the mouth's own dark. Every view
and animated frame, in place; the untouched frames are kept in tongue/.

    python art/enemies/pixellab/80_bes_kotak/no_tongue.py
"""
from pathlib import Path
import shutil
from PIL import Image

HERE = Path(__file__).resolve().parent
YELLOW, ORANGE, MOUTH = (0xf0, 0xbc, 0x3c), (0xfc, 0x98, 0x38), (0x22, 0x14, 0x0c)
keep = HERE / 'tongue'
keep.mkdir(exist_ok=True)
gone = 0
for f in sorted(HERE.glob('idle_anim_*.png')) + sorted(HERE.glob('idle_view_*.png')):
    if not (keep / f.name).exists():
        shutil.copy(f, keep / f.name)
    im = Image.open(keep / f.name).convert('RGBA')
    ys = [y for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3] and im.getpixel((x, y))[:3] == YELLOW]
    eye = max(ys) if ys else -1
    for y in range(eye + 2, im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] and p[:3] == ORANGE:
                im.putpixel((x, y), MOUTH + (255,))
                gone += 1
    im.save(f)
print(gone, 'tongue px gone')
