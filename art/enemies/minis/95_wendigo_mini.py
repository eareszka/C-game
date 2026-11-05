"""95 Wendigo's map mini: the bone demon of the winter at the player's scale, a step and its arms opening, two frames (tools/minis.py).

Through PixelLab (pixellab-out/95-wendigo-mini, 1 generation): the hand-drawn mini-size source art/enemies/pixellab/95_wendigo/mini/source.py given a stalking walk; frames 0 and 1 (the later ones
turned into a lanky, different creature). Like its battle sprite it is drawn from the front only: the same body every view, the back with its eyes and fangs taken off. Three colours and black:
frost, ice, crimson eyes.

Its chase: the dash (chase_speed(), src/main.cpp) -- straight at you, then a breath: it never stops hunting.

    python art/enemies/minis/95_wendigo_mini.py
"""
from pathlib import Path
import sys
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import minis, first_frame as ff

PAL = {'K': '000000', 'F': 'c6ccda', 'I': '84a7e9', 'R': 'b6433d'}
CHASE = 'dash'
HEIGHT = 24
HERE = ROOT / 'art/enemies/pixellab/95_wendigo/mini'
RAW = [l.strip() for l in (HERE / 'anim.log').read_text().splitlines() if l.strip().endswith('.png')]
RGB = {k: tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) for k, c in PAL.items()}


def frame(i):
    im = Image.open(RAW[i]).convert('RGBA')
    g = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3] > 127:
                g[x - 2, y - 8] = min(RGB, key=lambda k: sum((a - b) ** 2 for a, b in zip(RGB[k], p[:3])))
    g = {p: c for p, c in g.items() if not (c == 'K' and any((p[0] + a, p[1] + b) not in g for a, b in ff.N4))}
    xs, ys = [x for x, y in g], [y for x, y in g]
    dx, dy = minis.W // 2 - (min(xs) + max(xs)) // 2, minis.H - 2 - max(ys)
    return ff.outline({(x + dx, y + dy): c for (x, y), c in g.items()})


def back(g):
    """Its back: the front's own body with the face off (art direction: all views the same proportions)."""
    ys = [y for (x, y), c in g.items() if c == 'R']
    top, bottom = min(ys) - 1, max(ys) + 4
    out = {}
    for (x, y), c in g.items():
        face = top <= y <= bottom and c in ('R', 'K') and all(g.get((x + a, y + b)) in ('F', 'R', 'K', 'I') for a, b in ff.N4) and 13 <= x <= 27
        out[x, y] = 'F' if face else c
    return out


D = [frame(0), frame(1)]
FRAMES = {'D': D, 'U': [back(g) for g in D], 'L': D, 'R': D}

if __name__ == '__main__':
    minis.make(95, 'wendigo', FRAMES, PAL, cap=HEIGHT)
    minis.chase_gif(95, CHASE, FRAMES, PAL)
