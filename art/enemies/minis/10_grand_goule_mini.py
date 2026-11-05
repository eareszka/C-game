"""10 Grand'Goule's map mini: the gargoyle on the wing, two frames, wings down and up (tools/minis.py).

Drawn by PixelLab alone (the user: "minis should use pixellab"): sprite at the mini's size and palette (pixellab-out/10-mini2, m1, 1 of 4 generations), then a wingbeat (pixellab-out/10-mini2-anim, 1 generation);
frames 0 and 3. Front view for every direction, as its battle sprite; the back has its face taken off. Three colours and black: hide blue, wing charcoal, chest tan. It flies: mini_hover plus the swoop chase.

    python art/enemies/minis/10_grand_goule_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'art/enemies/pixellab/10_grand_goule/redo2/mini'
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'B': '375a94', 'C': '34343e', 'T': 'b2966a'}
CHASE = 'swoop'
HEIGHT = 24
HOVER = 11
CW, CH = 44, 30      # its wings need more than a standard cell: a strip of its own (minis_10.png)
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127: g[x, y] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = CW // 2 - (min(xs) + max(xs)) // 2, CH - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


def back(g):
    """Its back: the front's own body with the tan chest and face turned to hide."""
    return {p: ('B' if c == 'T' else c) for p, c in g.items()}


D = [frame(0), frame(3)]
FRAMES = {'D': D, 'U': [back(g) for g in D], 'L': D, 'R': D}

if __name__ == '__main__':
    minis.make(10, 'grand_goule', FRAMES, PAL, cap=HEIGHT, cell=(CW, CH))
    minis.chase_gif(10, CHASE, FRAMES, PAL, hover=HOVER, cell=(CW, CH))
    for g in D:
        print(max(x for x, y in g) - min(x for x, y in g) + 1, 'x', max(y for x, y in g) - min(y for x, y in g) + 1)
