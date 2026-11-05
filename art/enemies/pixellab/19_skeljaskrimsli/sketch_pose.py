"""19 Skeljaskrimsli in the user's third reference's pose (reference_user_pose.jpg, 2026-10-29: "have the pose of
the enemy be like this"): hunched in three-quarter view facing right, its great shelled back arched high, its
head lowered to the right, on thick bent legs. The ink drawing cut from its white ground (the title, the
signature and the grey ground wash left out), shrunk onto the 86x43 canvas, inked: the sketch whose pose
PixelLab's edit keeps (source_idle.png), with reference 5's look in the prompt and its style image
(style_look_right.png, reference 5 facing right as this does).

    python art/enemies/pixellab/19_skeljaskrimsli/sketch_pose.py
"""
from pathlib import Path
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
W, H, GROUND, FIT = 86, 43, 41, (60, 38)
im = Image.open(HERE / 'reference_user_pose.jpg').convert('L')
a = im.point(lambda v: 255 if v < 150 else 0)
ap = a.load()
for x0, y0, x1, y1 in ((190, 0, 447, 60), (330, 395, 447, 447)):   # the title, the signature
    for y in range(y0, y1):
        for x in range(x0, x1):
            ap[x, y] = 0
for y in range(380, 447):                                            # the ground wash under its feet
    for x in range(447):
        ap[x, y] = 0
a = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))
box = a.getbbox()
filled = a.crop(box).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))   # the silhouette, the gaps between its legs kept
ink = im.crop(box)
s = min(FIT[0] / filled.width, FIT[1] / filled.height)
size = (round(filled.width * s), round(filled.height * s))
mask = filled.resize(size, Image.LANCZOS).point(lambda v: 255 if v > 140 else 0)
tone = ink.resize(size, Image.LANCZOS)
out = Image.new('RGBA', (W, H))
ox, oy = (W - size[0]) // 2, GROUND - size[1]
for y in range(size[1]):
    for x in range(size[0]):
        if mask.getpixel((x, y)):
            v = tone.getpixel((x, y))
            out.putpixel((ox + x, oy + y), ((0x1e, 0x1e, 0x24) if v < 80 else (0x59, 0x59, 0x65) if v < 170 else (0xbc, 0xbe, 0xca)) + (255,))
o = out.copy()
for y in range(H):
    for x in range(W):
        if out.getpixel((x, y))[3]:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if 0 <= q[0] < W and 0 <= q[1] < H and not out.getpixel(q)[3]:
                    o.putpixel(q, (0, 0, 0, 255))
o.save(HERE / 'source_idle.png')
look = Image.open(HERE / 'style_look.png')
look.transpose(Image.FLIP_LEFT_RIGHT).save(HERE / 'style_look_right.png')
print('sketch', o.getbbox(), size)
