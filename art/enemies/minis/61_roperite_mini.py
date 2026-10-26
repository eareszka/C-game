"""61 Roperite's map mini: the California runner whose snout is drawn out into a long rope it lassos its prey with,
the rattle on its tail warning it is coming, running you down flat out, at the player's scale, four views, two
frames (tools/minis.py).

Its battle sheet is already PixelLab's: its redraw's sprint cycle (art/enemies/pixellab/61_roperite/running, five
frames a view, front, back and side). Each mini frame is one of those, shrunk (minis.shrink, a view's frames by one
box so they line up), cleaned (minis.clean), one black outline round it: two of its strides. Its rope loop shrinks
to a solid blob, so its top LOOP_H rows are cut away and the loop drawn back by hand where its rope stood -- a ring
of rope a pixel wide, 6 x 8, open in the middle, its outline round it inside and out, standing on its head. The right view is its own (its battle sheet has it).
20 px tall: its battle height (57 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
tan (body, rope), its dark brown (legs), its rattle red (the rattle's orange goes to it).

Its chase: straight at you at the chase pace, never stopping -- it is dashing at all times (the user, of its
battle) -- its sprint stepping (the default in chase_speed(), src/main.cpp).

    python art/enemies/minis/61_roperite_mini.py
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'T': 'b29e5c', 'D': '463422', 'R': 'b70000'}
CHASE = 'straight'
HEIGHT = 20
LETTERS = {'b29e5c': 'T', 'd0c078': 'X', '463422': 'D', '764c20': 'D', '142e1f': 'D', 'b70000': 'R', 'f0bc3c': 'R'}
LOOP_H = 8                                       # its rope loop's rows, over its head
STRIDES = {'D': (1, 4), 'U': (1, 3), 'L': (1, 3), 'R': (1, 3)}   # battle sprint frames: one foot down, the other


def ring(x0, y0, x1, y1):
    """A ring of rope a pixel wide in the box, its middle open."""
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, max(1.5, (x1 - x0) / 2), max(1.5, (y1 - y0) / 2)
    out = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if 0.45 <= d <= 1.05: out.add((x, y))
    return out


def view(v):
    ims = [minis.battle_views(61, f)[v] for f in STRIDES[v]]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    out = []
    for im in ims:
        g = minis.shrink(im, HEIGHT, LETTERS, box)
        top = min(y for x, y in g)
        rope = [x for (x, y), c in g.items() if c == 'X' and y < top + LOOP_H]   # where its loop stands
        g = {p: ('T' if c == 'X' else c) for p, c in g.items() if c != 'K' and p[1] >= top + LOOP_H}
        g = minis.clean(g)
        cx = round(sum(rope) / len(rope)) if rope else (min(x for x, y in g) + max(x for x, y in g)) // 2
        for p in ring(cx - 3, top + 1, cx + 2, top + LOOP_H):              # 6 x 8, down onto its head
            g.setdefault(p, 'T')
        out.append(ff.outline(g))
    return out


FRAMES = {v: view(v) for v in 'DULR'}

if __name__ == '__main__':
    minis.make(61, 'roperite', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(61, CHASE, FRAMES, PAL)
