"""62 Hugag's map mini: the moose-sized beast of the Lake States on jointless legs -- it can never lie down -- its
great overhanging lip, wandering at you on stiff stilt legs, at the player's scale, four views, two frames
(tools/minis.py).

Its battle sheet has one view, its side. Through PixelLab (art/enemies/pixellab/62_hugag/mini, pixellab-out/
62-mini, four generations): eight rotations of its battle side, then its front, back and left side each given a
walk -- stiff legs that never bend, swung like stilts, its body rocking, its head bobbing. Each mini frame is one of
those on the mini's palette (minis.recolour), shrunk (minis.shrink, a view's frames by one box so they line up),
cleaned (minis.clean): its body, coat, neck and head, down to its coat's hem; its legs drawn by hand under it
(stilts(): the shrink fills the gaps between them), stiff lines with no knee, swinging opposite ways;
one black outline round it all: two of its stiff strides. The right view is the left mirrored.
21 px tall: its battle height (58 px) at the minis' one scale, 28/79. Three of its battle colours and black: its
coat green, its pink (head, neck; its red lip goes to it), its tan (the legs, its coat's hem).

Its chase: the meander (chase_speed() and chase_bend(), src/main.cpp) -- it wanders the woods day and night, its
pace rising and falling, curving one way then the other as it comes.

    python art/enemies/minis/62_hugag_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'G': '2c6c44', 'P': 'ec8476', 'T': 'd7a175'}
CHASE = 'meander'
HEIGHT = 21
BASE = minis.H - 2                               # its feet's row; the outline under them
SRC = ROOT / 'pixellab-out/62-mini/animations'
WALKS = {'D': ('v2/walkd', (1, 3)), 'U': ('v3/walku', (1, 3)), 'L': ('v1/walkl', (0, 2))}   # one stride, the other


def tone(h, s, v):
    """Its darkest black, its greens the coat, its pinks and reds the head, the rest (legs, hem) tan."""
    if v < 0.2: return 'K'
    if 80 <= h <= 180 and s > 0.2: return 'G'
    if (h < 20 or h > 330) and s > 0.3: return 'P'
    return 'T'


def line(a, b):
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
    return {(round(a[0] + (b[0] - a[0]) * i / n), round(a[1] + (b[1] - a[1]) * i / n)) for i in range(n + 1)}


def stilts(g, side, stride):
    """Its body (coat, neck, head) down to its coat's hem, and four stiff legs drawn by hand under it -- the shrink
    fills the gaps between them into one block. A leg is a line of tan from the hem straight to its foot, no knee,
    only its near two show (its coat is narrow at this size): from the side its fore and hind legs swung `stride`
    px at the foot, opposite ways; from the front and back a foot lifted by turns."""
    hem = max(y for (x, y), c in g.items() if c == 'G') + 1
    body = {p: c for p, c in g.items() if c != 'K' and p[1] <= hem}
    xs = [x for (x, y), c in body.items() if c == 'G' and y >= hem - 2]   # the coat's width at its bottom
    x0, x1 = min(xs), max(xs)
    if side:                                     # its near fore and hind legs; the far two hidden behind them
        legs = [(x0 + 1, -stride, 0), (x1 - 1, stride, 0)]
    else:                                        # its two near legs, wide; its far legs hidden behind them
        c = (x0 + x1) // 2
        legs = [(c - 3, 0, max(0, stride)), (c + 3, 0, max(0, -stride))]       # a foot up, by turns
    for x, swing, lift in legs:
        for p in line((x, hem + 1), (x + swing, BASE - lift)): body.setdefault(p, 'T')
    return ff.outline(body)


def view(name, picks, side):
    ims = [minis.recolour(Image.open(SRC / f'{name}-{i:02d}.png').convert('RGBA'), tone, PAL) for i in picks]
    boxes = [im.getbbox() for im in ims]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    letters = {v: k for k, v in PAL.items() if k != 'K'}
    return [stilts(minis.clean(minis.shrink(im, HEIGHT, letters, box)), side, st) for im, st in zip(ims, (1, -1))]


FRAMES = {v: view(*WALKS[v], v == 'L') for v in 'DUL'}
FACE = {'D': [[(17, 11), (19, 11), (18, 13)], [(16, 10), (19, 10), (18, 12)]],   # by hand: its eyes, its mouth under
        'L': [[(14, 12)], [(15, 10)]]}                                      # its lip; the shrink loses them
for v, fs in FACE.items():
    for g, face in zip(FRAMES[v], fs):
        for p in face:
            assert g.get(p) == 'P', (v, p)
            g[p] = 'K'
FRAMES['R'] = [{(minis.W - 1 - x, y): c for (x, y), c in g.items()} for g in FRAMES['L']]

if __name__ == '__main__':
    minis.make(62, 'hugag', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(62, CHASE, FRAMES, PAL)
