"""85 Nanabolele's animated frames (idle-animate-*) brought to the bible as its approved views were. PixelLab's
untouched frames are kept in anim_raw/; this reads them and rewrites idle_anim_*.png:
- palette: each pixel snapped to the game palette, the near-blacks to black, the rest folded onto the views'
  eight colours (views.py), as frame 0.
- halo: the front's gape frames grew a mint and orange ring outside the outline -- colour of the belly, teeth or
  eyes touching empty canvas is peeled away, a ring at a time.
- lights: on the side its spines blazed orange; orange is its eyes' colour only (the bible's one accent, the
  user's tiny-mark eyes), so orange outside each view's eye box is the glow green of its lights.
- eyes: in the eye box no glint (white beside orange), and each eye at most 2 px of orange; the rest skin.
- then tidy.tidy(): specks, the closed outline, interior black to 14%.

    python art/enemies/pixellab/85_nanabolele/anim.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'art/direction'))
sys.path.insert(0, str(HERE))
import fcremap
from tidy import tidy

h = lambda s: tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
KEEP = [h(c) for c in ('142e1f', '235436', '29633e', '4edc4a', 'a8f0bc', '967448', 'fc9838', 'e8e0c0')]
NEAR_BLACK = {h(c) for c in ('0c0a12', '282828', '200c0e')}
GLOW, ORANGE, MINT, WHITE, SKIN, BLACK = h('4edc4a'), h('fc9838'), h('a8f0bc'), h('e8e0c0'), h('142e1f'), (0, 0, 0)
EYES = {'D': (40, 30, 58, 40), 'DR': (64, 28, 74, 37), 'R': (70, 28, 84, 40), 'UR': None, 'U': None}   # x0 y0 x1 y1
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def clusters(px, pts):
    pts, out = set(pts), []
    while pts:
        st = [pts.pop()]; c = [st[0]]
        while st:
            x, y = st.pop()
            for dx, dy in N8:
                q = (x + dx, y + dy)
                if q in pts: pts.remove(q); st.append(q); c.append(q)
        out.append(sorted(c, key=lambda p: (p[1], p[0])))
    return out


for v, box in EYES.items():
    for i in range(1, 5):
        im = Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA')
        px, W, H = im.load(), im.width, im.height
        for y in range(H):
            for x in range(W):
                p = px[x, y]
                if p[3] < 128: px[x, y] = (0, 0, 0, 0); continue
                c = tuple(fcremap.nearest(p[:3])[:3])
                c = BLACK if c in NEAR_BLACK or c == BLACK else c if c in KEEP else min(KEEP, key=lambda k: fcremap.lab_dist(c, k))
                px[x, y] = c + (255,)
        at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
        for _ in range(3):
            ring = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] in (MINT, ORANGE, WHITE)
                    and any(not at(x + dx, y + dy)[3] for dx, dy in N4)]
            for p in ring: px[p] = (0, 0, 0, 0)
            if not ring: break
        inbox = lambda x, y: box and box[0] <= x <= box[2] and box[1] <= y <= box[3]
        orange = [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == ORANGE]
        for p in orange:
            if not inbox(*p): px[p] = GLOW + (255,)
        for y in range(H):
            for x in range(W):
                if px[x, y][3] and px[x, y][:3] == WHITE and inbox(x, y) and any(at(x + dx, y + dy)[:3] == ORANGE for dx, dy in N8):
                    px[x, y] = SKIN + (255,)
        for eye in clusters(px, [p for p in orange if inbox(*p)]):
            for p in eye[2:]: px[p] = SKIN + (255,)
        tidy(im).save(HERE / f'idle_anim_{v}_{i}.png')
    print(v, 'done')
