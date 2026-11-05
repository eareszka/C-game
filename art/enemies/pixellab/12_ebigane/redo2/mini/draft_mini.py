"""12 Ebigane's new map mini, DRAFT (art/enemies/minis/12_ebigane_mini.* stays until the user approves): the rat-bodied predator stalking, four true views (the user: "mini should be done in pixellab having u d l r"), two frames each (tools/minis.py).

Drawn by PixelLab alone (the user: "minis should use pixellab"): sprite at the mini's size and palette (pixellab-out/12-mini2, m2, 1 of 4 generations), then a stalking walk (pixellab-out/12-mini2-anim, 1 generation);
frames 0 and 3. Its rotation looked from above (the user: "up and down dont match the games way of depth and drawing"), so front and back are straight-on at ground level as the approved minis are: the front from sprite --view side --direction south (fb/front2), the back PixelLab's turn of that front (fb/t1), each given a walk (pixellab-out/12-mini2-fb, -anim); front frames 0 and 1, back 0 and 2. The right view is the left mirrored. Three colours and black: hide slate, fins peach, pale ivory. A walker: the dash chase.

    python art/enemies/pixellab/12_ebigane/redo2/mini/draft_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'S': '595965', 'P': 'f0b890', 'I': 'e8e0c0'}
CHASE = 'dash'
HEIGHT = 28
CW, CH = minis.W, minis.H
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(path, tail_from=None, trim_top=0):
    im = Image.open(path).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    if tail_from is not None:                # the tail is a thin black line in PixelLab's side frames: slate, or stripping the outline would cut it off
        for p, c in list(g.items()):
            if c == 'K' and p[0] >= tail_from: g[p] = 'S'
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    top = min(y for x, y in g)
    g = {p: c for p, c in g.items() if p[1] >= top + trim_top}   # its ears' tips, a row over the cell
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = CW // 2 - (min(xs) + max(xs)) // 2, CH - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


def logged(name):
    return [l.strip() for l in (HERE / name).read_text().splitlines() if l.strip().endswith('.png')]


LEFT = [frame(RAW[0], 32), frame(RAW[3], 32)]
RIGHT = [{(CW - 1 - x, y): c for (x, y), c in g.items()} for g in LEFT]
FRONT = [frame(logged('fb/anim_d.log')[0]), frame(logged('fb/anim_d.log')[1], trim_top=1)]
BACK = [frame(logged('fb/anim_u.log')[i]) for i in (0, 2)]
FRAMES = {'L': LEFT, 'R': RIGHT, 'D': FRONT, 'U': BACK}

if __name__ == '__main__':
    minis.HERE = HERE / 'draft'
    minis.make(12, 'ebigane', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(12, CHASE, FRAMES, PAL)
    for v, gs in FRAMES.items():
        print(v, [(max(x for x, y in g) - min(x for x, y in g) + 1, max(y for x, y in g) - min(y for x, y in g) + 1) for g in gs])
