"""The desert's ground: the wasteland's sparse clods, in sand (the user,
2026-10-27: "have the ground speckle pattern be the same for the desert" --
the desert takes the wasteland's few small clods, in place of its even grid of
dots and its dune swirls).

    python art/ground/sand_design.py --png

The same six cells as art/ground/wasteland_design.py, in the grass block's
roles (src/tilemap.cpp COVER_TUFTS: clump left, clump right, tuft a; tuft b,
tuft c, plain), the fill sand's f0e880 and the clods its d0c078. Writes
art/ground/sand.png, stamped at sheet cols 21-23 rows 0-1 by
gen_entrance_art.py --grounds.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wasteland_design import block

PAL = {'.': 'f0e880', 'L': 'd0c078'}

if __name__ == '__main__':
    from PIL import Image
    rows = block()
    im = Image.new('RGBA', (len(rows[0]), len(rows)))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            h = PAL[c]
            im.putpixel((x, y), (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sand.png')
    im.save(out)
    print('wrote', out, im.size)
