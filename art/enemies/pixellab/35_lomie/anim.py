"""35 Lomie's animated frames (idle-animate-*) brought to the bible as its approved views were. PixelLab's
untouched frames are kept in anim_raw/; this reads them and rewrites idle_anim_*.png with views.py's own steps:
fold() (the game palette, its eight colours, the coat blue), holes() (none), eyes()
(pitch black), then tidy.tidy() (specks, the closed outline, interior black to 14%). Any of its bladder's
pale touching empty canvas outside its outline (a halo) is peeled away first.

    python art/enemies/pixellab/35_lomie/anim.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from views import fold, holes, eyes, h
from tidy import tidy

HALO = {h('f0b890'), h('d7a175')}
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
import colorsys
COAT = [h('375a94'), h('37387b'), h('34343e')]          # its coat, light to dark (views.BLUE)


def coat_shares(still):
    """The share of each coat step among its view's approved still's coat pixels."""
    n = [sum(1 for p in still.get_flattened_data() if p[3] and p[:3] == c) for c in COAT]
    return [k / max(1, sum(n)) for k in n]


def is_coat(p):
    """A blue-grey coat pixel as PixelLab drew it: cool hue or grey, not near black, not the warm browns/tan."""
    hh, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
    return v > 0.16 and (s < 0.2 or 190 <= hh * 360 <= 290)


def coated(raw, shares):
    """PixelLab shades its animated frames darker and bluer than the still it was given, so folding by nearest
    colour sends the coat to the deep blue and it flickers. Its coat pixels are ranked by brightness and given
    the still's three coat steps in the still's shares; the rest folded as usual."""
    pts = [(x, y) for y in range(raw.height) for x in range(raw.width) if raw.getpixel((x, y))[3] > 127 and is_coat(raw.getpixel((x, y)))]
    lum = lambda p: sum(w * c for w, c in zip((0.299, 0.587, 0.114), raw.getpixel(p)[:3]))
    pts.sort(key=lum, reverse=True)
    im = fold(raw.copy())
    i = 0
    for c, share in zip(COAT, shares):
        k = round(share * len(pts))
        for p in pts[i:i + k]: im.putpixel(p, c + (255,))
        i += k
    for p in pts[i:]: im.putpixel(p, COAT[-1] + (255,))
    return im


STILLS = {'D': 'idle_frame0_clean.png', 'DR': 'idle_view_DR.png', 'R': 'idle_view_R.png', 'UR': 'idle_view_UR.png',
          'U': 'idle_view_U.png'}
for v in ('D', 'DR', 'R', 'UR', 'U'):
    shares = coat_shares(Image.open(HERE / STILLS[v]).convert('RGBA'))
    for i in range(1, 5):
        im = coated(Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA'), shares)
        px, W, H = im.load(), im.width, im.height
        at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
        for _ in range(3):
            ring = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in HALO
                    and any(not at(x + dx, y + dy)[3] for dx, dy in N4)]
            for p in ring: px[p] = (0, 0, 0, 0)
            if not ring: break
        tidy(eyes(holes(im, v))).save(HERE / f'idle_anim_{v}_{i}.png')
    print(v, 'done')
