"""87 Corocotta's views, assigned by eye from the rotate of its approved design (concept 4, the user's pick,
2026-10-29; idle-rotate-result.json). PixelLab took our side-on pose (head to the left) as its "south":
  D  east        -- head on, jaws open on its tooth
  DR north       -- its body to the right, its head turned to us
  R  north-east  -- side on, head to the right
  UR north-west  -- from behind, head away to the right
  U  west        -- straight from behind
Each placed on the 98x65 cell, feet on the bottom row, centred; snapped to the game palette, then folded onto
eight chosen colours (the rest to their nearest of those, Lab): its grey ramp, the dark of its mane, its pale
tooth, the red and pink of its mouth, the yellow of its eyes. Its grey lifted a step (PixelLab drew it near
black; the bible keeps black hide for 97 Ro alone, and its lore is grey-steel): mid grey to light, dark to mid,
the darkest kept for its mane and shadows. A hole through its jaws (the three-quarter's open mouth showed the backdrop)
is filled with its mouth red: only in each view's JAWS box, the gaps between its legs stay open. Its eyes then as the bible's tiny marks (the user,
2026-10-29): no glint beside them, each at most 2 px. Then tidy.tidy().
Writes idle_frame0_clean.png (D) and idle_view_*.png. fold(), holes() and eyes() are anim.py's too.

    python art/enemies/pixellab/87_corocotta/views.py
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
DRAWN = [h(c) for c in ('292931', '474751', '595965', '9797aa', 'e8e0c0', 'b6433d', 'ec8476', 'fae488')]
LIFT = {h('595965'): h('848694'), h('474751'): h('595965')}
KEEP = [LIFT.get(c, c) for c in DRAWN]
RED = h('b6433d')
JAWS = {'DR': (55, 20, 97, 45)}                    # x0 y0 x1 y1: where a hole is its open mouth
EYE, WHITE, SKIN = h('fae488'), h('e8e0c0'), h('292931')
ROT = ROOT / 'pixellab-out/87-corocotta/idle-rotate/idle-rotate/rotations/v1'
PICK = {'D': 'east-02', 'DR': 'north-04', 'R': 'north-east-03', 'UR': 'north-west-05', 'U': 'west-06'}
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
    """Each eye a tiny mark: no white beside the yellow, each yellow patch cut to its top 2 px."""
    px, w, hh = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < w and 0 <= y < hh else (0, 0, 0, 0)
    pts = {(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == EYE}
    for x, y in [(x, y) for y in range(hh) for x in range(w) if px[x, y][3] and px[x, y][:3] == WHITE]:
        if any(at(x + dx, y + dy)[:3] == EYE for dx, dy in N8): px[x, y] = SKIN + (255,)
    while pts:
        st = [pts.pop()]; c = [st[0]]
        while st:
            x, y = st.pop()
            for dx, dy in N8:
                q = (x + dx, y + dy)
                if q in pts: pts.remove(q); st.append(q); c.append(q)
        for p in sorted(c, key=lambda p: (p[1], p[0]))[2:]: px[p] = SKIN + (255,)
    return im


if __name__ == '__main__':
    for v, name in PICK.items():
        im = Image.open(next(ROT.glob(f'*views-{name}.png'))).convert('RGBA')
        im = fold(im)
        im = im.crop(im.getbbox())
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.paste(im, ((W - im.width) // 2, H - im.height))
        tidy(eyes(holes(out, v))).save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
        print(v, name)
