"""40 Slide-Rock Bolter's battle sheet from its approved flop (anim/flop_N.png; the user approved it 2026-11-02): six
frames a direction at 120 ms, side-on. It is drawn facing left; the left, front and back directions (5 6 7 0 4) use that
pose and the right ones (1 2 3) mirror it. The two lone pixels the checker listed are merged into what surrounds them.
The sheet it replaces is kept here as previous_installed.png.

    python art/enemies/pixellab/40_slide_rock_bolter/install.py
"""
from pathlib import Path
from collections import Counter
import shutil
import sys
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import enemy_sheet

W, H, FRAMES = 98, 65, 6
LONE = {0: [(14, 62)], 3: [(9, 43)]}
RIGHT = {1, 2, 3}
dest = ROOT / 'assets/enemies/redraws/40_slide_rock_bolter.png'
keep = HERE / 'previous_installed.png'
if not keep.exists(): shutil.copy(dest, keep)


def frame(i):
    im = Image.open(HERE / 'anim' / f'flop_{i}.png').convert('RGBA')
    for x, y in LONE.get(i, []):
        n = Counter(im.getpixel((x + a, y + b)) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if im.getpixel((x + a, y + b))[3] and im.getpixel((x + a, y + b))[:3] != (0, 0, 0))
        im.putpixel((x, y), n.most_common(1)[0][0])
    return im


fs = [frame(i) for i in range(FRAMES)]
sheet = Image.new('RGBA', (W * 8 * FRAMES, H))
for d in range(8):
    for i, f in enumerate(fs):
        sheet.paste(ImageOps.mirror(f) if d in RIGHT else f, ((d * FRAMES + i) * W, 0))
palette = sorted('%02x%02x%02x' % c for c in {p[:3] for p in sheet.get_flattened_data() if p[3]})
enemy_sheet.install(sheet, str(dest), FRAMES, False, ms=120, palette=palette)
print('installed', dest, sheet.size, len(palette) - 1, 'colours + black')
