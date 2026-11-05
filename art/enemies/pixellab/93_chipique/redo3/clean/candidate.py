"""93 Chipique's tail cleanup, test frame (the user, 2026-11-03: "needs to be cleaned up using pixellab, tail seems to split oddly").
PixelLab's edit of choppy frame 4 (pixellab-out/93-redo3-clean/c4, 1 generation), unpadded, folded onto the approved frame's colours, clumps of 2 px
or fewer merged, and the mouth's blood and falling drop put back from the original frame (the edit dropped them). Writes c4_clean.png and its review.

    python art/enemies/pixellab/93_chipique/redo3/clean/candidate.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
K, RED = (0, 0, 0), (0xb6, 0x43, 0x3d)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
BASE = Image.open(HERE.parent / 'frame0.png').convert('RGBA')
PAL = sorted({p[:3] for p in BASE.get_flattened_data() if p[3] and p[:3] != K})
ORIG = Image.open(HERE.parent / 'long/c_4.png').convert('RGBA')
raw = Image.open(ROOT / 'pixellab-out/93-redo3-clean/c4/sprites/v1/c4.png').convert('RGBA').crop((1, 1, 99, 66))
W, H = raw.size
def fold(p):
    return K if max(p) < 0x1c else min(PAL, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, p)))
g = {(x, y): fold(raw.getpixel((x, y))[:3]) for y in range(H) for x in range(W) if raw.getpixel((x, y))[3] > 127}
seen, out = set(), dict(g)
for p, c in g.items():
    if p in seen: continue
    piece, todo = {p}, [p]
    while todo:
        a = todo.pop()
        for dx, dy in N4:
            q = (a[0] + dx, a[1] + dy)
            if q not in piece and g.get(q) == c: piece.add(q); todo.append(q)
    seen |= piece
    if c in (K, RED) or len(piece) > 2: continue
    n = Counter(g[q] for a in piece for q in ((a[0] + dx, a[1] + dy) for dx, dy in N4) if q in g and q not in piece and g[q] != K)
    if n:
        for a in piece: out[a] = n.most_common(1)[0][0]
reds = [(x, y) for y in range(H) for x in range(W) if ORIG.getpixel((x, y))[3] and ORIG.getpixel((x, y))[:3] == RED and x < 30]
for p in reds: out[p] = RED
for (x, y) in reds:
    for a, b in N4:
        if (x + a, y + b) not in out: out[x + a, y + b] = K
im = Image.new('RGBA', (W, H))
for p, c in out.items(): im.putpixel(p, c + (255,))
im.save(HERE / 'c4_clean.png')
print('blood px', len(reds), 'bbox', im.getbbox())
