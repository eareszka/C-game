"""RO's free baseline: the red front draft recoloured to black-by-house-rules.

    python tools/ro_recolor.py [out.png]   (default: art/enemies/pixellab/97_ro/97_ro_recolor_baseline.png)

Black outline kept; the red-brown hide becomes a charcoal ramp, wing membrane darker than the body;
red only on the eyes, mouth and wing veins; teeth and claws stay bone. Eight colours plus black.
"""
import os, sys
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'art', 'enemies', 'pixellab', '97_ro', 'source_frame0.png')
OUT = os.path.join(ROOT, 'art', 'enemies', 'pixellab', '97_ro', '97_ro_recolor_baseline.png')


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


RAMP = {                       # red draft -> charcoal, everywhere
    '792727': '34343e', '5d1e1f': '292931', '531b1c': '1e1e24', '421618': '1e1e24',
    'b6433d': '474751',        # body highlight; on the wings it is a vein, below
    'd89830': '474751', 'f0bc3c': '595965', 'fae488': '595965',      # gold belly plates -> light charcoal
    '280e10': '792727', '7c0a1b': 'b70000',                          # mouth and tongue
    '000000': '000000', 'e8e0c0': 'e8e0c0'}
EYE_ROWS = range(17, 23)       # the yellow eyes (19-20) sit here; belly plates start at 40
WING_X = (40, 90)              # wings are outside this span of columns, above the tail
WING_BOTTOM = 50


def recolor(im):
    im = im.convert('RGBA')
    out = im.copy()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if not a:
                continue
            h = '%02x%02x%02x' % (r, g, b)
            new = RAMP[h]
            if h in ('f0bc3c', 'fae488') and y in EYE_ROWS:
                new = 'b70000'
            elif h == 'b6433d' and y < WING_BOTTOM and not WING_X[0] <= x < WING_X[1]:
                new = '792727'
            out.putpixel((x, y), rgb(new) + (255,))
    return out


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    recolor(Image.open(SOURCE)).save(out)
    print(out)
