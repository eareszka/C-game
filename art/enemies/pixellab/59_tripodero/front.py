"""59 Tripodero facing the viewer (the user, 2026-10-28: "front facing and as large canvas wise as the original
sprite"). PixelLab's rotate of the side redraw (idle_frame0_side.png, after abookofcreatures.com) took the
side as its south, so its names are a quarter turn off: its "east" is the front, "south-east" the front
three-quarter left (mirrored for DR), "north" the right side, "north-east" the back three-quarter right,
"north-west" the back. Each goes onto the 54x61 canvas unscaled, centred where the old sprite stood, its feet
on the old ground line (row 58), on frame 0's eight colours and black.

    python art/enemies/pixellab/59_tripodero/front.py
"""
from pathlib import Path
import json, sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import pixellab_enemy as pe

PICK = {'D': ('east', False), 'DR': ('south-east', True), 'R': ('north', False), 'UR': ('north-east', False), 'U': ('north-west', False)}
CX, GROUND, SIZE = 27, 59, (54, 61)      # the old sprite's middle column, the row under its feet, the canvas

files = [Path(f) for f in json.loads((HERE / 'side-rotate-result.json').read_text())['files'] if f.endswith('.png')]
palette = sorted({p[:3] for p in Image.open(HERE / 'idle_frame0_side.png').convert('RGBA').get_flattened_data() if p[3]})
for v, (name, mirror) in PICK.items():
    im = Image.open(next(f for f in files if f.stem.split('-views-')[-1].rsplit('-', 1)[0] == name)).convert('RGBA')
    if mirror:
        im = ImageOps.mirror(im)
    im = im.crop(im.getbbox())
    out = Image.new('RGBA', SIZE)
    out.paste(im, (CX - im.width // 2, GROUND - im.height))
    out = pe.to_palette(out, palette)
    out.save(HERE / ('idle_frame0_clean.png' if v == 'D' else f'idle_view_{v}.png'))
    print(v, name, out.getbbox())
