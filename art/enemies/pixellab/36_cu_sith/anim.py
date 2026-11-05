"""36 Cu Sith's animated frames (idle-animate-*) brought to the bible as its approved views were. PixelLab's
frames as the tool left them are kept in anim_raw/; this reads them and rewrites idle_anim_*.png with views.py's
own steps: fold() (its five flat colours), flat() (no clumps), UR mirrored, tidy.tidy(), then the eyes (and the side's
muzzle) stamped where the head now is (the front's head top-left, the 3/4's and side's snout tip, in the frame
against the still's) -- after tidy, which would fold their one-pixel pale dots.

    python art/enemies/pixellab/36_cu_sith/anim.py
"""
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import views
import tidy as tidy_mod
from tidy import tidy


FLIP = {'UR'}                # animated from the unmirrored still: mirrored as views.FLIP now has it


def head(im, v):
    """Where its head is. The front: the topmost drawn row and the leftmost drawn column in the ten rows below.
    The 3/4 front and side: its snout tip, the rightmost drawn column in the twenty rows from its top, and that top row."""
    px = im.load()
    top = min(y for y in range(im.height) for x in range(im.width) if px[x, y][3])
    rows = range(top, top + (10 if v == 'D' else 20))
    xs = [x for y in rows for x in range(im.width) if px[x, y][3]]
    return (min(xs) if v == 'D' else max(xs)), top


STILL = {'D': 'idle_frame0_clean.png', 'DR': 'idle_view_DR.png', 'R': 'idle_view_R.png'}
still = {v: head(Image.open(HERE / f).convert('RGBA'), v) for v, f in STILL.items()}
for v in ('D', 'DR', 'R', 'UR', 'U'):
    for i in range(1, 5):
        im = views.flat(views.fold(Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA')))
        if v in FLIP: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im = tidy(im)
        if v in views.FACE:
            x0, y0, rows = views.FACE[v]
            if v == 'D': y0, rows = y0 + 4, rows[4:6]        # the front's eyes only: its still's speck fixes are its own
            hx, hy = head(im, v)
            saved = dict(views.FACE)
            views.FACE[v] = (x0 + hx - still[v][0], y0 + hy - still[v][1], rows)
            im = views.face(im, v)
            views.FACE.update(saved)
            tidy_mod.KEEP = {views.LET['m']}                  # again round the stamp (its outline closed), the dots spared
            im = tidy(im)
            tidy_mod.KEEP = set()
        im.save(HERE / f'idle_anim_{v}_{i}.png')
    print(v, 'done')
