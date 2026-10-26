"""63 Hidebehind's map mini: the north woods thing no one has seen -- it is always behind something, behind you --
a faceless shaggy cone with fans of hooked claws, creeping round you and in, at the player's scale, four views, two
frames (tools/minis.py).

Its battle sheet has one view, its front. Through PixelLab (art/enemies/pixellab/63_hidebehind/mini, pixellab-out/
63-mini, four generations): eight rotations of its battle front, then its front, back and side each given a creep --
sliding along low, its hem swaying, its claws curling and spreading. Its side is its three-quarter view (south-west):
the side itself is a sliver. Each mini frame is one of those on the mini's palette (minis.recolour), shrunk
(minis.shrink, a view's frames by one box so they line up), cleaned (minis.clean), its claws -- shrunk to ivory blobs -- drawn back by hand as fans of three thin hooked fingers
(claws()), one black outline round it: its claws curled, then spread. The right view is the left mirrored.
22 px tall: its battle height (61 px) at the minis' one scale, 28/79. Three of its battle colours and black: its fur
brown, its dark brown (arms, the fur's shadow), its claw ivory (claws, its two small eyes).

Its chase: the skirt (chase_speed() and chase_bend(), src/main.cpp) -- circling wide round you, then straight in:
turn to look and it is already behind you.

    python art/enemies/minis/63_hidebehind_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'M': '815423', 'D': '463422', 'C': 'fce4a0'}
CHASE = 'skirt'
HEIGHT = 22
SRC = ROOT / 'pixellab-out/63-mini/animations'
CREEPS = {'D': ('v2/creepd', (0, 3)), 'U': ('v3/creepu', (0, 3)), 'L': ('v1/creepl', (0, 3))}   # curled, spread


def tone(h, s, v):
    """Its darkest black, its pale ivories the claws, its lit browns the fur, the rest dark brown."""
    if v < 0.12: return 'K'
    if v > 0.72 and (s < 0.5 or 30 <= h <= 70): return 'C'
    return 'M' if v > 0.4 else 'D'


def line(a, b):
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
    return [(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(n + 1)]


def claws(g):
    """Its claws, which shrink to ivory blobs (mittens), drawn back by hand: each blob of ivory cleared and three
    thin fingers fanned up from its palm (the blob's bottom middle) to its top, each tip hooked a pixel outward, so the
    outline falls between them."""
    left = {p for p, c in g.items() if c == 'C'}
    out = {p: c for p, c in g.items() if c != 'C'}
    while left:
        blob, todo = set(), [left.pop()]
        while todo:
            q = todo.pop(); blob.add(q)
            for dx, dy in ff.N4:
                n = (q[0] + dx, q[1] + dy)
                if n in left: left.discard(n); todo.append(n)
        xs, ys = [x for x, y in blob], [y for x, y in blob]
        if len(blob) < 4:
            for p in blob: out[p] = 'C'
            continue
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        palm = ((x0 + x1) // 2, y1)
        for tip, hook in (((x0, y0 + 1), -1), (((x0 + x1) // 2, y0), 0), ((x1, y0 + 1), 1)):
            for p in line(palm, tip): out[p] = 'C'
            if hook: out[tip[0] + hook, tip[1] - 1] = 'C'
    return out


def view(name, picks):
    ims = [minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    out = []
    for im in ims:
        g = minis.clean(minis.shrink(im, HEIGHT, letters, box))
        out.append(ff.outline(claws({p: c for p, c in g.items() if c != 'K' or all((p[0] + dx, p[1] + dy) in g for dx, dy in ff.N4)})))
    return out


FRAMES = {v: view(*CREEPS[v]) for v in 'DUL'}
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(63, 'hidebehind', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(63, CHASE, FRAMES, PAL)
