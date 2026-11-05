"""38 Igtuk's animated frames (idle-animate-DR, -R, -UR: its jaw opening wide and snapping shut, the boom) brought
to the bible as its approved views were. PixelLab's frames as the tool left them are kept in anim_raw/; this
reads them and rewrites idle_anim_*.png with views.py's steps: unblue() (onto its colours, back in the greys the
steps work in), flat(), its bottom row's colour black (the outline's place), tidy() sparing its eye's pale dot
(PixelLab kept it and the fur ball, animating from the stills that have them), blue(). D's frames are DR's (it has no head-on view: the user, "treat it like
the Snawfus").

    python art/enemies/pixellab/38_igtuk/anim.py
"""
from pathlib import Path
import shutil
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import views
import tidy as tidy_mod
from tidy import tidy

for v in ('DR', 'R', 'UR'):
    for i in range(1, 5):
        im = views.flat(views.unblue(Image.open(HERE / 'anim_raw' / f'idle_anim_{v}_{i}.png').convert('RGBA')))
        px = im.load()
        for x in range(im.width):                         # colour on the canvas's last row: the outline's place
            if px[x, im.height - 1][3] and px[x, im.height - 1][:3] != (0, 0, 0): px[x, im.height - 1] = (0, 0, 0, 255)
        tidy_mod.KEEP = {views.WHITE}
        im = tidy(im)
        tidy_mod.KEEP = set()
        views.blue(im).save(HERE / f'idle_anim_{v}_{i}.png')
        if v == 'DR': shutil.copy(HERE / f'idle_anim_DR_{i}.png', HERE / f'idle_anim_D_{i}.png')
    print(v, 'done')
