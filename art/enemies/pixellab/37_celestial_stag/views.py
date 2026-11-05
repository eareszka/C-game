"""37 Celestial Stag's views: a new silhouette (the user, 2026-10-30, of its old design recoloured by recolour.py:
"i like the texture but the overall design/silhouette needs to be redone from scratch, use pixellab"; of four
PixelLab concepts, concepts/, they chose 4, the spectral stag) on the colours of the reality-shard cave and its
torches (the user), restyled by PixelLab (edit try 2, the draft) and, once approved, the rotate of
it (idle-rotate-result.json).
Each placed on the 98x65 cell, feet on the bottom row, centred; folded straight onto eight game-palette colours
(nearest, Lab): the cave's purple base 664b95, shade 2b1f40 and lit lilac b69cee for its coat, stars and lit
edges, white fcfcfc, and four of the torch's pale rainbow stripes. Then flat() (36's: patches of six pixels or
fewer take the colour round them, the antlers spared); then stripes(): every antler pixel repainted as the
torch's rainbow flame is drawn (src/dungeon.cpp torch_light): slanted stripes two pixels wide cycling its pale
tones, a step along per frame; then tidy.tidy(); then the eyes stamped (FACE, Cu Sith's eye: a pale dot with
black above it and on its outer side). Writes idle_frame0_clean.png and idle_view_*.png. fold(), flat(),
stripes() and face() are anim.py's too.

    python art/enemies/pixellab/37_celestial_stag/views.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(HERE))
import fcremap
from tidy import tidy
import importlib.util
_spec = importlib.util.spec_from_file_location('cu_views', ROOT / 'art/enemies/pixellab/36_cu_sith/views.py')
cu = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cu)

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
COAT, SHADE, LILAC, WHITE = h('664b95'), h('2b1f40'), h('b69cee'), h('fcfcfc')
RAINBOW = [h(c) for c in ('ec8476', 'fae488', 'a8f0bc', '84a7e9', 'b69cee')]   # the torch's pale stripes
KEEP = [COAT, SHADE, LILAC, WHITE] + RAINBOW[:4]
ROT = ROOT / 'pixellab-out/37-celestial-stag/idle-rotate/idle-rotate/rotations/v1'
PICK = {'D': 'south-east-01', 'DR': 'east-02', 'R': None, 'UR': 'north-04', 'U': 'north-west-05'}
# By eye (the rotate took the approved left side view as its "south"): D south-east (face toward us, the most
# head-on it drew), DR east, R the approved pose mirrored (the user: it is the LEFT view), UR north, U north-west.
FLIP = {'R'}                             # the approved pose is its LEFT view (the user): R is it mirrored
W, H = 98, 65
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def fold(im):
    """Its near-blacks black; its coat's purples the cave's base (the lighter) and shade (the darker); the rest
    onto KEEP."""
    import colorsys
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            hu, sa, va = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
            if va < 0.08: px[x, y] = (0, 0, 0, 255); continue
            if 240 <= hu * 360 <= 320 and va < 0.6:          # its coat: PixelLab drew it darker than the cave's
                px[x, y] = (COAT if va >= 0.3 else SHADE) + (255,); continue   # stone, so by brightness, not nearest
            px[x, y] = min(KEEP, key=lambda k: fcremap.lab_dist(p[:3], k)) + (255,)
    return im


def antlers(im):
    """Its antler pixels: the rainbow's colours, and lilac or white touching them (the violet stripe, a white tip),
    grown till none join."""
    px, w, hh = im.load(), im.width, im.height
    hue = set(RAINBOW[:4])
    got = {(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] in hue}
    while True:
        more = {(x + dx, y + dy) for x, y in got for dx, dy in N8
                if 0 <= x + dx < w and 0 <= y + dy < hh and (x + dx, y + dy) not in got
                and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in (LILAC, WHITE)}
        if not more: return got
        got |= more


def stripes(im, f=0):
    """Every antler pixel the torch's flame: slanted stripes two pixels wide of its pale tones, `f` steps along."""
    for x, y in antlers(im):
        im.putpixel((x, y), RAINBOW[((x + y + 64) // 2 + f) % len(RAINBOW)] + (255,))
    return im


def smooth(im, passes=2):
    """Flatter (the user: "slightly more flat and fit the game's style more"): each coat pixel (base, shade, or a
    lit lilac fleck in the coat) takes the colour most of its eight coat neighbours have, so the shade sits in
    broad patches -- its far legs, under its belly -- not in streaks; lilac stays only in big patches (its tail)."""
    from collections import Counter
    px, w, hh = im.load(), im.width, im.height
    body = (COAT, SHADE)
    for _ in range(passes):
        new = {}
        for y in range(hh):
            for x in range(w):
                c = px[x, y]
                if not c[3] or c[:3] not in body + (LILAC,): continue
                n = Counter(px[x + dx, y + dy][:3] for dx, dy in N8
                            if 0 <= x + dx < w and 0 <= y + dy < hh and px[x + dx, y + dy][3] and px[x + dx, y + dy][:3] in body + (LILAC,))
                if c[:3] == LILAC and n[LILAC] >= 4: continue          # inside its tail
                top = n.most_common(1)
                if top and top[0][1] >= 5 and top[0][0] != c[:3]: new[x, y] = top[0][0]
        for p, c in new.items(): px[p] = c + (255,)
    return im


def flat(im):
    return cu.flat(smooth(im), most=10, spare=set(RAINBOW) | {WHITE})


LET = {'K': (0, 0, 0), 'c': COAT, 's': SHADE, 'l': LILAC}
FACE = {'D': (43, 29, ('KK..KK', 'Kl..lK')),     # (left, top, rows), '.' left as drawn: Cu Sith's eye, black
        'DR': (55, 28, ('KK', 'Kl')),               # above and on its outer side, the pale dot toward its snout
        'R': (62, 28, ('KK', 'Kl'))}


def face(im, v):
    if v in FACE:
        x0, y0, rows = FACE[v]
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != '.': im.putpixel((x0 + x, y0 + y), LET[c] + (255,))
    return im


def place(im):
    im = im.crop(im.getbbox())
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(im, ((W - im.width) // 2, H - im.height))
    return out


if __name__ == '__main__':
    for v, name in PICK.items():
        src = HERE / 'idle_frame0_draft.png' if name is None else next(ROT.glob(f'*views-{name}.png'))
        im = flat(fold(Image.open(src).convert('RGBA')))
        if v in FLIP: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = stripes(place(im))
        face(tidy(im), v).save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
        print(v, name)
