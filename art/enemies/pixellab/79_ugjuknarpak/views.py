"""79 Ugjuknarpak's views reassigned by eye. PixelLab's rotate took frame 0 -- itself a three-quarter pose, its
body turned to the right -- as its south, so its names run a step round: its south-west is the straight front,
south (frame 0) the front three-quarter, south-east the side, east the back three-quarter, north-east the back.
Each view and the animation PixelLab made from it move together; the new front gets its own (animate view=D
try=2). The three-quarter frame 0 the user approved is kept as idle_frame0_threequarter.png and stays the
palette and the reference. Run once, before animate view=D.

    python art/enemies/pixellab/79_ugjuknarpak/views.py
"""
from pathlib import Path
import json, shutil, sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'art/direction'))
import pixellab_enemy as pe

three = HERE / 'idle_frame0_threequarter.png'
if not three.exists():
    shutil.copy(HERE / 'idle_frame0_clean.png', three)
old = HERE / 'by_label'                     # PixelLab's assignment, kept
old.mkdir(exist_ok=True)
for f in HERE.glob('idle_view_*.png'):
    shutil.move(str(f), old / f.name)
for f in HERE.glob('idle_anim_*.png'):
    shutil.move(str(f), old / f.name)
MOVE = {'DR': 'D', 'R': 'DR', 'UR': 'R', 'U': 'UR'}   # new view: the old label whose view and frames it takes
for new, was in MOVE.items():
    src = three if was == 'D' else old / f'idle_view_{was}.png'
    shutil.copy(src, HERE / f'idle_view_{new}.png')
    for i in range(1, 9):
        shutil.copy(old / f'idle_anim_{was}_{i}.png', HERE / f'idle_anim_{new}_{i}.png')
# the front: south-west, onto the canvas as the other rotated views were
approved = Image.open(three).convert('RGBA')
origin = pe.roomy(approved, HERE / 'idle_rotate_input_check.png')
files = [Path(f) for f in json.loads((HERE / 'idle-rotate-result.json').read_text())['files'] if f.endswith('.png')]
sw = next(f for f in files if f.stem.split('-views-')[-1].rsplit('-', 1)[0] == 'south-west')
front = pe.to_palette(pe.fit(Image.open(sw), approved.size, origin, approved.getbbox()[3]), sorted({p[:3] for p in approved.get_flattened_data() if p[3]}))
front.save(HERE / 'idle_frame0_clean.png')
print('front', front.getbbox())
