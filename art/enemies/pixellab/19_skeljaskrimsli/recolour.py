"""19 Skeljaskrimsli: the pose of the user's first reference with the look of the second (the user, 2026-10-29:
"the pose from 4 but the colors/look of 5", then "pose should be 4 reference tho"). PixelLab's edit drifted
from the pose, so the cleaned side of reference 4 (idle_frame0_side.png) is kept pixel for pixel and only
recoloured, region by region: its back's plates and its tail pale grey with a darker band where their seams
ran (reference 5's banded plates); its head, belly and legs charcoal; the brown fur at its feet charcoal with
white claws at the tips; a glowing green eye on its head; its green teeth kept. Writes idle_frame0_clean.png.

    python art/enemies/pixellab/19_skeljaskrimsli/recolour.py
"""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
M, D, d, L, l, B = h('474751'), h('34343e'), h('292931'), h('848694'), h('595965'), h('463422')
GREEN = {h('a8f0bc'), h('2c6c44')}
PLATE = {M: h('bcbeca'), L: h('bcbeca'), l: h('bcbeca'), D: h('848694'), d: h('595965')}   # pale, the band, its shade
CHAR = {M: h('34343e'), L: h('34343e'), l: h('34343e'), D: h('1e1e24'), d: h('1e1e24'), B: h('34343e')}
CLAW, EYE = h('fcfcfc'), h('a8f0bc')
HEAD_X, NECK_X, FLANK_Y, TAIL_X = 16, 24, 22, 60   # head and mane left of these; below FLANK_Y the fur; the tail right of TAIL_X


def region(x, y):
    if x <= HEAD_X and y >= 20:
        return 'head'
    if x <= NECK_X and y >= 18:
        return 'body'                    # the mane round its neck
    if x >= TAIL_X and y < 30:
        return 'tail'
    return 'plates' if y < FLANK_Y else 'body'


im = Image.open(HERE / 'idle_frame0_side.png').convert('RGBA')
out = im.copy()
for y in range(im.height):
    for x in range(im.width):
        p = im.getpixel((x, y))
        if not p[3] or p[:3] == (0, 0, 0) or p[:3] in GREEN:
            continue
        r = region(x, y)
        out.putpixel((x, y), ((PLATE if r in ('plates', 'tail') else CHAR).get(p[:3], p[:3])) + (255,))
for x in range(0, im.width, 2):                 # claws: a tip at every other column of each foot's lowest fur
    for y in range(im.height - 1, 33, -1):
        p = im.getpixel((x, y))
        if p[3] and p[:3] == B:
            out.putpixel((x, y), CLAW + (255,))
            break
for e in ((9, 26), (10, 26)):                   # the glowing eye on its head, over the teeth
    out.putpixel(e, EYE + (255,))
out.save(HERE / 'idle_frame0_clean.png')
print(len({q[:3] for q in out.get_flattened_data() if q[3]}) - 1, 'colours + black', out.getbbox())
