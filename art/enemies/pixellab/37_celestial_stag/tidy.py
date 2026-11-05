"""37 Celestial Stag's views and frames tidied to the bible (copied from 85 Nanabolele's, 2026-10-29):
- specks: PixelLab's scale texture left 57-110 lone pixels a view (the bible: no dithering, scale lattices or
  skin textures; chunky clusters). Each lone pixel takes its most common non-black neighbour colour, a few
  passes, black ones too. The teeth (single white pixels) and the eye marks are kept: they are drawn details.
- the lone pixels left after that, at edges and joined to nothing round all eight sides, take their most
  common neighbouring colour of the eight (not black, the teeth or eyes); one with none such is a tip and stays.
- outline: its glowing spines and tail tip, and parts of the back views, met the empty canvas in colour. Every
  empty pixel beside colour becomes black: the one-pixel black outline closed round everything.
- interior black: 15-17% on three views after that, over the bible's 9-14% reference: black inside the body
  with three black neighbours (then two) is a blob, not a seam, and takes the darkest grey, to 14%.
Run after views.py; rewrites the views in place. anim.py runs tidy() on every
animated frame too.

    python art/enemies/pixellab/85_nanabolele/tidy.py
"""
from pathlib import Path
from collections import Counter
from PIL import Image

HERE = Path(__file__).resolve().parent
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
BLACK = (0, 0, 0)
SHADE = (0x2b, 0x1f, 0x40)                 # its coat shade, the cave's dark purple
KEEP = set()                               # nothing lone to spare; anim.py tidies again sparing its eyes' pale dots
files = ['idle_frame0_clean.png'] + [f'idle_view_{v}.png' for v in ('DR', 'R', 'UR', 'U')]


def lone(px, W, H, at):
    """A pixel with none of its colour among its eight neighbours takes their most common colour (not black or
    KEEP); one in a black line, with no colour round it, goes black."""
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if not c[3] or c[:3] in KEEP or c[:3] == BLACK: continue
            near = [at(x + dx, y + dy) for dx, dy in N8]
            if any(n[3] and n[:3] == c[:3] for n in near): continue
            pick = Counter(n[:3] for n in near if n[3] and n[:3] != BLACK and n[:3] not in KEEP).most_common(1)
            pick = pick or Counter(n[:3] for n in near if n[3] and n[:3] != BLACK).most_common(1)   # only KEEP round it
            if pick: px[x, y] = pick[0][0] + (255,)
            elif all(not n[3] or n[:3] == BLACK for n in near): px[x, y] = BLACK + (255,)   # a lone fleck in a black line


def tidy(im):
    """One frame to the bible: specks folded, the outline closed, interior black to 14%. In place; returns it."""
    px, W, H = im.load(), im.width, im.height
    at = lambda x, y: px[x, y] if 0 <= x < W and 0 <= y < H else (0, 0, 0, 0)
    for _ in range(3):
        changed = 0
        for y in range(H):
            for x in range(W):
                c = px[x, y]
                if not c[3] or c[:3] in KEEP: continue
                near = [at(x + dx, y + dy) for dx, dy in N4]
                if any(n[3] and n[:3] == c[:3] for n in near): continue
                inside = [n[:3] for n in near if n[3]]
                if len(inside) < 3: continue                    # an edge pixel: the outline's business
                pick = Counter(n for n in inside if n != BLACK and n not in KEEP).most_common(1) or [(BLACK, 0)]
                px[x, y] = pick[0][0] + (255,); changed += 1
        if not changed: break
    lone(px, W, H, at)
    for (x, y) in [(x, y) for y in range(H) for x in range(W) if not px[x, y][3]
                   and any(at(x + dx, y + dy)[3] and at(x + dx, y + dy)[:3] != BLACK for dx, dy in N4)]:
        px[x, y] = BLACK + (255,)
    edge = lambda x, y: any(not at(x + dx, y + dy)[3] for dx, dy in N4)
    share = lambda: (sum(1 for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == BLACK and not edge(x, y))
                     / sum(1 for y in range(H) for x in range(W) if px[x, y][3]))
    for need in (3, 2):
        if share() <= 0.14: break
        for (x, y) in [(x, y) for y in range(H) for x in range(W) if px[x, y][3] and px[x, y][:3] == BLACK and not edge(x, y)
                       and sum(at(x + dx, y + dy)[:3] == BLACK for dx, dy in N4) >= need]:
            if share() <= 0.14: break
            px[x, y] = SHADE + (255,)
    lone(px, W, H, at)                     # a black blob's pixel turned SHADE alone in a line
    return im


if __name__ == '__main__':
    for f in files:
        tidy(Image.open(HERE / f).convert('RGBA')).save(HERE / f)
        print(f, 'tidied')
