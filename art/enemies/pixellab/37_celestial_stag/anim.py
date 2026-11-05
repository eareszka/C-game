"""37 Celestial Stag's animated frames (idle-animate-*) brought to the bible as its approved views were. PixelLab's
frames as the tool left them are kept in anim_raw/; this reads them and rewrites idle_anim_*.png with views.py's
own steps: fold(), flat() (smooth, then no clumps), stripes() a step along per
frame: frame i, i steps -- the still 0, frames 1-4 -- so the five frames at 150 ms, the torches' pace, cycle the
stripes once and loop seamlessly (the user: its antlers strobing as the torches do), tidy.tidy(), then the eyes stamped where the head now is
(its top-left for the front, its snout tip for the 3/4 and side, in the frame against the still's), then tidy
again sparing the eyes' pale dots.

    python art/enemies/pixellab/37_celestial_stag/anim.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import views
import tidy as tidy_mod
from tidy import tidy


def head(im, v):
    """The front: the head's top-left -- the topmost coat row below the antlers, the leftmost drawn column in the
    eight rows from it. The 3/4 and side: the snout tip, the rightmost drawn column in the twelve rows from it."""
    px = im.load()
    ant = views.antlers(im)
    top = min(y for y in range(im.height) for x in range(im.width)
              if px[x, y][3] and (x, y) not in ant and px[x, y][:3] in (views.COAT, views.SHADE))
    xs = [x for y in range(top, top + (8 if v == 'D' else 12)) for x in range(im.width) if px[x, y][3] and (x, y) not in ant]
    return (min(xs) if v == 'D' else max(xs)), top


STILL = {'D': 'idle_frame0_clean.png', 'DR': 'idle_view_DR.png', 'R': 'idle_view_R.png'}
still = {v: head(Image.open(HERE / f).convert('RGBA'), v) for v, f in STILL.items()}
for v in ('D', 'DR', 'R', 'UR', 'U'):
    for i in range(1, 5):
        im = views.flat(views.fold(Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA')))
        im = tidy(views.stripes(im, i))
        if v in views.FACE:
            x0, y0, rows = views.FACE[v]
            hx, hy = head(im, v)
            saved = dict(views.FACE)
            views.FACE[v] = (x0 + hx - still[v][0], y0 + hy - still[v][1], rows)
            im = views.face(im, v)
            views.FACE.update(saved)
            tidy_mod.KEEP = {views.LILAC}                 # again round the stamp, the eyes' dots spared
            im = tidy(im)
            tidy_mod.KEEP = set()
        im.save(HERE / f'idle_anim_{v}_{i}.png')
    print(v, 'done')
