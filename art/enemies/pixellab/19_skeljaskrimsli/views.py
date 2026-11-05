"""19 Skeljaskrimsli's four directions (now from pose-rotate-result.json: the approved hunched pose turned; the
three-quarter itself stays DR, idle_view_DR.png). Earlier,  from PixelLab's rotate of the side redraw (idle_frame0_side.png, after the
user's reference). Its names run a quarter turn off (the side went in as its south), so picked by eye: "east"
the front, "north" the right side (the left mirrors it), "west" the back (from behind, the tail swept out).
Each onto the 86x43 canvas unscaled, centred, its feet on row 41, on frame 0's eight colours and black.

    python art/enemies/pixellab/19_skeljaskrimsli/views.py
"""
from pathlib import Path
import json, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import pixellab_enemy as pe

SHADE, BLACK = (0x29, 0x29, 0x31), (0, 0, 0)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def thin(im):
    """Interior black kept to lines, as merge.py keeps frame 0's: black inside the body with three or four black
    neighbours is a blob, not a seam, and takes the plates' dark shade (then two, if still over the bible's band)."""
    inside = lambda x, y: all(0 <= x + dx < im.width and 0 <= y + dy < im.height and im.getpixel((x + dx, y + dy))[3] for dx, dy in N4)
    drawn = lambda: [(x, y) for y in range(im.height) for x in range(im.width) if im.getpixel((x, y))[3]]
    share = lambda: sum(1 for x, y in drawn() if im.getpixel((x, y))[:3] == BLACK and inside(x, y)) / len(drawn())
    for need in (4, 3, 2):
        if share() <= 0.18:
            break
        for p in [(x, y) for x, y in drawn() if im.getpixel((x, y))[:3] == BLACK and inside(x, y)
                  and sum(im.getpixel((x + dx, y + dy))[:3] == BLACK for dx, dy in N4) >= need]:
            im.putpixel(p, SHADE + (255,))
    return im


PICK = {'D': 'west', 'R': 'south-east', 'UR': 'east', 'U': 'north-east'}   # the hunched pose (pose-rotate), by eye
ROTATE = 'pose-rotate-result.json'
SIZE, GROUND = (86, 43), 42
files = {Path(f).stem.split('-views-')[-1].rsplit('-', 1)[0].split('2-')[-1]: Path(f)
         for f in json.loads((HERE / ROTATE).read_text())['files'] if f.endswith('.png')}
palette = sorted({p[:3] for p in Image.open(HERE / 'idle_frame0_threequarter.png').convert('RGBA').get_flattened_data() if p[3]})
for v, name in PICK.items():
    im = Image.open(files[name]).convert('RGBA')
    im = im.crop(im.getbbox())
    out = Image.new('RGBA', SIZE)
    out.paste(im, ((SIZE[0] - im.width) // 2, GROUND - im.height))
    out = thin(pe.to_palette(out, palette))
    out.save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
    print(v, name, out.getbbox())
