"""35 Lomie's views, from its approved redesign (the user, 2026-10-29: "tall blue moose and sac under neck" --
concept 2's tall moose, concept 4's sac -- after its lore, abookofcreatures.com/2020/10/30/lomie: a Bohemian
forest beast drawn moosier, a sac-like bladder under its neck that it fills with water, boils as it runs and
sprays over the hunters) and the rotate of it (idle-rotate-result.json):
  D  south-west        -- head on, the bladder hanging under its chin
  DR its approved draft (idle_frame0_draft.png) -- body to the right, head toward us
  R  south-east, UR east, U north-east
Each placed on the 62x67 cell, feet on the bottom row, centred; snapped to the game palette, then folded onto
eight chosen colours (the rest to their nearest, Lab): its coat's three steps, moved onto the palette's
blue (PixelLab drew it grey; the user wanted a blue moose), its antlers' three
browns, its bladder's pale tan and shade; its near-blacks black. Its eyes PITCH BLACK (the user): no glint, a
pale pixel by an eye's black that is not part of the bladder (one of its colour round it at most) takes the
coat. Then tidy.tidy(). Writes idle_frame0_clean.png (D) and idle_view_*.png. fold(), holes() and eyes() are
anim.py's too.

    python art/enemies/pixellab/35_lomie/views.py
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

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
DRAWN = [h(c) for c in ('848694', '595965', '34343e', '583518', '8d6b4f', '967448', 'f0b890', 'd7a175')]
BLUE = {h('848694'): h('375a94'), h('595965'): h('37387b')}   # the coat onto the palette's blue (the user: a blue moose)
KEEP = [BLUE.get(c, c) for c in DRAWN]
BLACK = {h(c) for c in ('0c0a12', '14101e', '22140c', '000000')}
PALE, COAT = {h('f0b890'), h('d7a175')}, h('375a94')
ROT = ROOT / 'pixellab-out/35-lomie/idle-rotate/idle-rotate/rotations/v1'
PICK = {'D': 'south-west-07', 'DR': None, 'R': 'south-east-01', 'UR': 'east-02', 'U': 'north-east-03'}
W, H = 62, 67
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def fold(im):
    """Snapped to the game palette, its near-blacks black, the rest onto KEEP."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            c = tuple(fcremap.nearest(p[:3])[:3])
            c = (0, 0, 0) if c in BLACK else c if c in DRAWN else min(DRAWN, key=lambda k: fcremap.lab_dist(c, k))
            px[x, y] = BLUE.get(c, c) + (255,)
    return im


def holes(im, v):
    return im                            # no open mouth to fill


def eyes(im):
    """Pitch-black eyes: a pale pixel beside black with at most one pale neighbour (a glint, not the bladder)
    takes the coat."""
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] in PALE]:
        near = [at(x + dx, y + dy) for dx, dy in N8]
        if any(n[3] and n[:3] == (0, 0, 0) for n in near) and sum(n[3] and n[:3] in PALE for n in near) <= 1:
            px[x, y] = COAT + (255,)
    return im


if __name__ == '__main__':
    for v, name in PICK.items():
        im = Image.open(HERE / 'idle_frame0_draft.png' if name is None else next(ROT.glob(f'*views-{name}.png'))).convert('RGBA')
        im = fold(im)
        im = im.crop(im.getbbox())
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.paste(im, ((W - im.width) // 2, H - im.height))
        tidy(eyes(holes(out, v))).save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
        print(v, name)
