"""88 Amixsak's views, from its approved restyle (concept 1, the hollow hide, the user's pick, 2026-10-29) and the
rotate of it (idle-rotate-result.json), whose labels came out right this time:
  D  its approved frame 0 (idle_frame0_draft.png) -- head on, the empty hollow, the tusks
  DR south-east, R east, UR north-east, U north
Each placed on the 98x65 cell, its bottom on the bottom row, centred; snapped to the game palette, then folded
onto eight chosen colours (the rest to their nearest of those, Lab): its brown ramp (mid, dark, the light of
its back), the very dark brown of its empty hollow (not black: the bible's interior black is for seams), the
grey and dark grey of its muzzle, the pale and the shade of its tusks. The battle sprite is out of the water
(the user): no water anywhere. Its eyes then as the bible's tiny marks: no glint (a pale pixel beside the
eye's dark). Then tidy.tidy().
Writes idle_frame0_clean.png (D) and idle_view_*.png. fold(), holes() and eyes() are anim.py's too.

    python art/enemies/pixellab/88_amixsak/views.py
"""
from pathlib import Path
import sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'art/direction'))
sys.path.insert(0, str(HERE))
import fcremap
from tidy import tidy

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
DRAWN = [h(c) for c in ('8d6b4f', '463422', 'f0b890', '22140c', '595965', '34343e', 'fce4a0', 'cebe82')]
LIFT = {}
KEEP = [LIFT.get(c, c) for c in DRAWN]
RED = h('22140c')                                 # a hole is its empty hollow
JAWS = {}                                         # none found yet
EYE, WHITE, SKIN = h('22140c'), h('fce4a0'), h('8d6b4f')
ROT = ROOT / 'pixellab-out/88-amixsak/idle-rotate/idle-rotate/rotations/v1'
PICK = {'D': None, 'DR': 'south-east-01', 'R': 'east-02', 'UR': 'north-east-03', 'U': 'north-04'}
W, H = 98, 65
N8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def fold(im):
    """Snapped to the game palette, black kept, the rest onto KEEP."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
            c = tuple(fcremap.nearest(p[:3])[:3])
            c = c if c == (0, 0, 0) or c in DRAWN else min(DRAWN, key=lambda k: fcremap.lab_dist(c, k))
            px[x, y] = LIFT.get(c, c) + (255,)
    return im


def holes(im, v):
    """Empty pixels in its JAWS box the outside can't reach (4-connected) filled with its mouth red."""
    box = JAWS.get(v)
    if not box: return im
    px, w, hh = im.load(), im.width, im.height
    seen, st = set(), [(x, y) for x in range(w) for y in (0, hh - 1)] + [(x, y) for y in range(hh) for x in (0, w - 1)]
    while st:
        x, y = st.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < hh) or px[x, y][3]: continue
        seen.add((x, y)); st += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(hh):
        for x in range(w):
            if not px[x, y][3] and (x, y) not in seen and box[0] <= x <= box[2] and box[1] <= y <= box[3]: px[x, y] = RED + (255,)
    return im


def eyes(im):
    """Each eye a tiny mark: no tusk-pale glint beside the dark of an eye. (Its eyes are its hollow's dark, so
    there is no accent patch to cut to 2 px, as the Corocotta's yellow was.)"""
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    for x, y in [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == WHITE]:
        if any(at(x + dx, y + dy)[:3] == EYE for dx, dy in N8) and not any(at(x + dx, y + dy)[:3] == WHITE for dx, dy in N8):
            px[x, y] = SKIN + (255,)
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
